import os
import json
import time
import sys
import traceback

def test_pdf_extraction(file_path, output_dir):
    """Test the PDF extraction functionality and display results"""
    try:
        print("Loading necessary modules...")
        # Import only after setting up the directory structure
        from extractPDF import extract_pdf
        
        print(f"Starting extraction of: {file_path}")
        start_time = time.time()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Run extraction
        result = extract_pdf(file_path, output_dir)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Analyze results
        print(result.keys())
        num_questions = len(result["questions"])
        num_answers = len(result["answers"])
        # num_titles = len(result["title"])
        num_correct_options = len(result["correct_options"])
        num_explanations = len(result["explains"])
        
        # Count valid images
        valid_questions = count_valid_images(result["questions"])
        valid_answers = count_valid_answer_images(result["answers"])
        # valid_titles = count_valid_images(result["titles"])
        valid_explanations = count_valid_explanation_images(result["explains"])
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"EXTRACTION RESULTS SUMMARY:")
        print("=" * 50)
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Type flag: {result['type_flag']}")
        print(f"Questions extracted: {num_questions} (valid images: {valid_questions})")
        print(f"Answer options extracted: {num_answers} (valid images: {valid_answers})")
        # print(f"Titles extracted: {num_titles} (valid images: {valid_titles})")
        print(f"Correct options identified: {len(result['correct_options'])}")
        print(f"Explanations extracted: {num_explanations} (valid images: {valid_explanations})")
        
        # Save minimal result data for verification (without base64 images)
        result_data = {
            "type_flag": result["type_flag"],
            "question_keys": list(result["questions"].keys()),
            "answer_keys": list(result["answers"].keys()),
            # "title_keys": list(result["titles"].keys()),
            "correct_options": result["correct_options"],
            "explanation_keys": list(result["explains"].keys()),
            "valid_images": {
                "questions": valid_questions,
                "answers": valid_answers,
                # "titles": valid_titles,
                "explanations": valid_explanations
            }
        }
        
        # Export the result data
        result_file = os.path.join(output_dir, "extraction_results.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
            
        print(f"\nDetailed results saved to: {result_file}")
        
        # Save example images if available
        save_example_images(result, output_dir)
        
        print("=" * 50)
        return True
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        traceback.print_exc()
        return False

def count_valid_images(images_dict):
    """Count valid base64 images in the dictionary"""
    count = 0
    for key, value in images_dict.items():
        if isinstance(value, list) and len(value) > 4 and isinstance(value[4], str) and value[4].startswith('data:image/png;base64,'):
            count += 1
        elif isinstance(value, dict) and 'base64' in value and value['base64'].startswith('data:image/png;base64,'):
            count += 1
    return count

def count_valid_answer_images(answers_dict):
    """Count valid base64 images in answers dictionary"""
    count = 0
    for question_key, options in answers_dict.items():
        for option_key, images in options.items():
            for image in images:
                if isinstance(image, list) and len(image) > 4 and isinstance(image[4], str) and image[4].startswith('data:image/png;base64,'):
                    count += 1
    return count

def count_valid_explanation_images(explains_dict):
    """Count valid base64 images in explanations dictionary"""
    count = 0
    for question_key, explanations in explains_dict.items():
        for explanation in explanations:
            if isinstance(explanation, list) and len(explanation) > 4 and isinstance(explanation[4], str) and explanation[4].startswith('data:image/png;base64,'):
                count += 1
    return count

def save_example_images(result, output_dir):
    """Save example images as HTML files for verification"""
    try:
        # Create examples directory
        examples_dir = os.path.join(output_dir, "examples")
        os.makedirs(examples_dir, exist_ok=True)
        
        # Save question example
        if result["questions"]:
            q_key = next(iter(result["questions"].keys()))
            q_data = result["questions"][q_key]
            if isinstance(q_data, list) and len(q_data) > 4 and isinstance(q_data[4], str) and q_data[4].startswith('data:image/png;base64,'):
                save_html_example(examples_dir, f"question_{q_key}.html", "Question Example", q_data[4])
        
        # Save title example
        # if result["titles"]:
        #     t_key = next(iter(result["titles"].keys()))
        #     t_data = result["titles"][t_key]
        #     if isinstance(t_data, list) and len(t_data) > 4 and isinstance(t_data[4], str) and t_data[4].startswith('data:image/png;base64,'):
        #         save_html_example(examples_dir, f"title_{t_key}.html", "Title Example", t_data[4])
        
        # Save explanation example
        if result["explains"]:
            e_key = next(iter(result["explains"].keys()))
            e_data = result["explains"][e_key]
            if e_data and isinstance(e_data[0], list) and len(e_data[0]) > 4 and isinstance(e_data[0][4], str) and e_data[0][4].startswith('data:image/png;base64,'):
                save_html_example(examples_dir, f"explanation_{e_key}.html", "Explanation Example", e_data[0][4])
        
        # Save answer option example
        if result["answers"]:
            a_key = next(iter(result["answers"].keys()))
            a_options = result["answers"][a_key]
            if a_options:
                o_key = next(iter(a_options.keys()))
                o_data = a_options[o_key]
                if o_data and isinstance(o_data[0], list) and len(o_data[0]) > 4 and isinstance(o_data[0][4], str) and o_data[0][4].startswith('data:image/png;base64,'):
                    save_html_example(examples_dir, f"option_{a_key}_{o_key}.html", "Answer Option Example", o_data[0][4])
        
        print(f"Example images saved to: {examples_dir}")
    except Exception as e:
        print(f"Error saving example images: {e}")

def save_html_example(output_dir, filename, title, base64_img):
    """Save base64 image as HTML file"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #333; }}
            .image-container {{ border: 1px solid #ddd; padding: 10px; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="image-container">
            <img src="{base64_img}" alt="{title}" />
        </div>
    </body>
    </html>
    """
    
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    # Define paths
    pdf_file = "/home/trucddx/thide/AI/PdfToImage/uploads/3.De_GHK2_Toan10_CamThuy1.pdf"
    output_path = "/home/trucddx/thide/AI/PdfToImage/output"
    
    # Run test
    success = test_pdf_extraction(pdf_file, output_path)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)