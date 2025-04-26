from flask import Flask, request, jsonify
from extractPDF import extractor as ExtractPDF
import os
import secrets
from functools import wraps

# Add python-dotenv to load environment variables
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    env_loaded = True
except ImportError:
    env_loaded = False
    print("python-dotenv not installed. Falling back to config file.")

app = Flask(__name__)

# Default API key (used if not in env or config)
DEFAULT_API_KEY = "truc"

# Try to get API key from environment first
API_KEY = os.environ.get('API_KEY')

# If not in environment, try config file
if not API_KEY:
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.py')
    if not os.path.exists(CONFIG_FILE):
        # Create config file with default key
        API_KEY = DEFAULT_API_KEY
        with open(CONFIG_FILE, 'w') as f:
            f.write(f"API_KEY = '{API_KEY}'\n")
        print(f"Created config file with API key: {API_KEY}")
    else:
        # Import the existing API key
        try:
            from config import API_KEY
        except (ImportError, AttributeError):
            API_KEY = DEFAULT_API_KEY
            print(f"Failed to load API key from config, using default: {DEFAULT_API_KEY}")

def require_api_key(view_function):
    """Decorator to require API key in request headers"""
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        # Check if API key is in headers
        provided_key = request.headers.get('X-API-Key')
        
        # Option to also check query parameters
        if not provided_key:
            provided_key = request.args.get('api_key')
            
        if provided_key and provided_key == API_KEY:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized. Valid API key required."}), 401
    return decorated_function

@app.route('/extract', methods=['POST'])
@require_api_key
def extract_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

        # Extract data from the PDF
        data = ExtractPDF.extract_pdf(file_path, "")
        
        # Prepare response
        response = {
            "questions": data.get("questions", {}),
            "answers": data.get("answers", {}),
            "titles": data.get("titles", {}),
            "correct_options": data.get("correct_options", {}),
            "explains": data.get("explains", {}),
            "type_flag": data.get("type_flag", 0)
        }

        return jsonify(response)

    return jsonify({"error": "Invalid file format"}), 400

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    # Add a secret key for session security
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Get debug mode from environment
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    print(f"API is secured with key: {API_KEY}")
    print("Use this key in your requests with header: X-API-Key")
    print(f"Starting server on port {port} (debug: {debug})")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
