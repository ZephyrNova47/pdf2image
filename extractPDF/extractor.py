import os
import fitz
from collections import defaultdict

from .processors.question_processor import (
    perform_traversal_questions_set, get_question_0
)
from .processors.answer_processor import (
    get_ascender_descender_option, process_answer_options, extract_option_images
)
from .processors.explain_processor import (
    process_explain, process_explain_base64
)
from .processors.correct_answer_processor import (
    process_correct_answer, process_stop_questions
)
from .utils.block_utils import get_json_page
from .utils.image_utils import get_base64_image, format_option_response

def extract_pdf(file, path_root_output=""):
    """Extract information from PDF

    Args:
        file (str): link to the file
        path_root_output (str): link to the output's file

    Returns:
        dict: Dictionary with base64 images for questions, answers, and explains
    """
    # Initialize as per original code
    doc = fitz.open(file)
    n_page = doc.page_count
    num_q = 1
    questions = []
    explains = []
    correct_answers = {}
    answers_options = []
    append_reading = False
    type_flag = 0
    
    # Get question format from first page
    answers_options = get_question_0(doc[0])
    
    # Get ascender_descender_option for answer formatting
    ascender_descender_option = []
    if len(answers_options) != 0:
        ascender_descender_option = get_ascender_descender_option(answers_options) 

    # Set default type if no answers
    if len(ascender_descender_option) == 0:
        type_flag = 2

    # Free memory
    del answers_options
    
    # Process all pages
    for i_page in range(n_page):    
        blocks = get_json_page(doc[i_page], type_flag, i_page)
        if len(blocks) == 0:
            break

        # Process based on type flag
        if type_flag == 0 or type_flag == 2:  
            data = perform_traversal_questions_set(doc[i_page], blocks, num_q, explains, append_reading)
        elif type_flag == 4:
            data = process_explain(blocks, num_q)
            num_q = data[4]
            explains.append([i_page, data[2]])
        elif type_flag == 99:
            data = process_correct_answer(blocks)
        
        # Update data collections
        if type_flag != 4:
            if len(data[0]) > 0:
                if len(data[1]) > 0: 
                    questions.append([i_page, data[0], data[1]])
                else:
                    questions.append([i_page, data[0], {}])
            if len(data[2]) > 0:
                explains.append([i_page, data[2]])
            if len(data[3]) > 0:
                correct_answers = data[3]
            if len(data) > 4:
                num_q = data[4]
            if len(data) > 5:
                type_flag = data[5]
            if len(data) > 6:
                append_reading = data[6]
    
    # Process explanation images
    coor_x = [1000, 0]
    coor_explains_result = {}
    if len(explains) > 0:
        coor_explains_result = process_explain_base64(explains, coor_x, doc, path_root_output)
    
    # Remove question_0 (metadata before question 1)
    if questions and len(questions) > 0:
        if 'question_0' in questions[0][1]:
            questions[0][1].pop('question_0', None)
    
    # Process question images and answer options
    
    # Initialize result dictionaries
    questions_result = {}
    answers_result = {}
    titles_result = {}
    
    # Process questions and answers page by page
    for question_page in questions:
        page_num = question_page[0]
        questions_dict = question_page[1]
        answers_dict = question_page[2]
        
        # Process each question on this page
        for q_key, q_data in questions_dict.items():
            # Process question content
            if isinstance(q_data, dict) and 'content' in q_data:
                content = q_data['content']
                if content and len(content) > 0:
                    # Get coordinates
                    coor = content[0][:4] if len(content[0]) >= 4 else None
                    
                    # Create base64 image for question
                    if coor:
                        image_data = get_base64_image(doc[page_num], coor)
                        if image_data:
                            questions_result[q_key] = [
                                float(coor[0]), float(coor[1]), float(coor[2]), float(coor[3]),
                                image_data,
                                float(coor[0]), float(coor[1]), float(coor[2]), float(coor[3]),
                                image_data,
                                0
                            ]
            elif isinstance(q_data, list) and len(q_data) >= 4:
                # Direct coordinates format
                coor = q_data[:4]
                image_data = get_base64_image(doc[page_num], coor)
                if image_data:
                    questions_result[q_key] = [
                        float(coor[0]), float(coor[1]), float(coor[2]), float(coor[3]),
                        image_data,
                        float(coor[0]), float(coor[1]), float(coor[2]), float(coor[3]),
                        image_data,
                        0
                    ]
            
            # Process question title
            if isinstance(q_data, dict) and 'title' in q_data:
                title_coor = q_data['title']
                if title_coor and len(title_coor) >= 4:
                    image_data = get_base64_image(doc[page_num], title_coor[:4])
                    if image_data:
                        titles_result[q_key] = [
                            float(title_coor[0]), float(title_coor[1]), 
                            float(title_coor[2]), float(title_coor[3]),
                            image_data
                        ]
            
            # Process answer options for this question - new code
            if q_key in answers_dict:
                options = extract_option_images(doc[page_num], answers_dict, q_key)
                if options and options['options']:
                    answers_result[q_key] = options
    
    # Close document
    doc.close()
    
    # Return the final result
    return {
        "questions": questions_result,
        "answers": answers_result, 
        "titles": titles_result,
        "correct_options": correct_answers,
        "explains": coor_explains_result,
        "type_flag": type_flag
    }