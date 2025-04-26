import requests

# API endpoint
url = 'http://127.0.0.1:5000/extract'

# API key (must match the one in the server)
api_key = 'truc'  

# Headers with API key
headers = {
    'X-API-Key': api_key
}

# PDF file to process
files = {'file': open('/home/trucddx/thide/AI/PdfToImage/uploads/Math Test-1.pdf', 'rb')}

# Send the request
response = requests.post(url, headers=headers, files=files)

# Check if authentication was successful
if response.status_code == 401:
    print("Authentication failed: Invalid API key")
elif response.status_code == 200:
    # Print just the first part to avoid overwhelming output
    print("Authentication successful!")
    print("Response contains:")
    
    data = response.json()
    question_count = len(data.get("questions", {}))
    answer_count = len(data.get("answers", {}))
    title_count = len(data.get("titles", {}))
    explain_count = len(data.get("explains", {}))
    
    print(f"- {question_count} questions")
    print(f"- {answer_count} answer sets")
    print(f"- {title_count} titles")
    print(f"- {explain_count} explanations")
    
    # Print one example if available
    if question_count > 0:
        first_q = next(iter(data["questions"]))
        print(f"\nExample question data structure for {first_q}:")
        print(f"- Type: {type(data['questions'][first_q])}")
        print(f"- Length: {len(data['questions'][first_q])}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
