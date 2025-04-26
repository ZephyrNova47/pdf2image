import re
from collections import defaultdict
from ..utils.text_utils import get_text_spans
from ..utils.image_utils import get_base64_title
from ..utils.coordinate_utils import compare_coors, compare_coors_with_text

def process_explain(blocks, num_q):
    """Process explanation section"""
    questions = {}
    answers_options = {}
    explains = {}
    correct_answers = {}
    
    # Implementation details would go here
    # ...
    
    return [questions, answers_options, explains, correct_answers, num_q]

def process_explain_in_question(blocks, block, line, explains, questions):
    """Process explanation inside a question"""
    flag_explain_in_question = True
    explains[f'question_{num_q - 1}'] = line['bbox'] + [text_spans]
    return explains

def process_explain_in_correct_answer(blocks, correct_answers):
    """Process explains when there are explanation and correct answers"""
    data = process_explain(blocks, 1)
    data[3] = correct_answers
    
    return data

def process_explain_base64(explains, coor_x, doc, path_root_output=""):
    """Create image of explanation"""
    coor_explains_result = defaultdict(list)
    
    for explain in explains:
        page_num = explain[0]
        explains_dict = explain[1]
        
        for q_key, explain_data in explains_dict.items():
            if isinstance(explain_data, dict) and 'content' in explain_data:
                content = explain_data['content']
                if content:
                    # Merge coordinates
                    coor_e = content[0][:4]
                    for line in content[1:]:
                        if len(line) >= 4:
                            coor_e = compare_coors(coor_e, line[:4])
                    
                    # Add padding
                    coor_e[0] = max(0, coor_e[0] - 5)
                    coor_e[1] = max(0, coor_e[1] - 5)
                    coor_e[2] = coor_e[2] + 5
                    coor_e[3] = coor_e[3] + 5
                    
                    # Update width coordinates
                    coor_x[0] = min(coor_e[0], coor_x[0])
                    
                    # Generate explanation image
                    explain_image = get_base64_title(doc[page_num], coor_e)
                    
                    if len(explain_image) > 4:
                        coor_explains_result[q_key].append(explain_image)
            else:
                # Handle previous format
                if isinstance(explain_data, list) and len(explain_data) >= 4:
                    coor_x[0] = min(explain_data[0], coor_x[0])
                    coor = [coor_x[0], explain_data[1], explain_data[2], explain_data[3]]
                    
                    image = get_base64_title(doc[page_num], coor)
                    if len(image) > 4:
                        if q_key not in coor_explains_result:
                            coor_explains_result[q_key] = [image]
                        else:
                            coor_explains_result[q_key].append(image)
    
    return coor_explains_result

def merge_question(line, questions, num_q, text_spans, answers_options=None):
    """Merge question content with coordinates
    
    Args:
        line (dict): Line information
        questions (dict): Question information 
        num_q (int): Question number
        text_spans (str): Text content
        answers_options (dict, optional): Answer options. Defaults to None.
    
    Returns:
        dict: Updated questions dictionary
    """
    # Check if this is for current question
    question_key = f'question_{num_q - 1}'
    
    # Existing question content should use current index
    if question_key in questions:
        # Check if the line is part of the question content (not part of answer option)
        is_part_of_answer = False
        
        if answers_options is not None:
            # Check if this line overlaps with answer options
            for opt_key, opts in answers_options.items():
                if opt_key != question_key:
                    continue
                    
                for opt in opts:
                    if len(opt) >= 2 and isinstance(opt[1], list) and len(opt[1]) >= 4:
                        # Check if the line overlaps with this option
                        if (line['bbox'][1] >= opt[1][1] and line['bbox'][1] <= opt[1][3]) or \
                           (line['bbox'][3] >= opt[1][1] and line['bbox'][3] <= opt[1][3]):
                            is_part_of_answer = True
                            break
                
                if is_part_of_answer:
                    break
        
        # If not part of answer, update question content
        if not is_part_of_answer:
            # If content already exists in the dict
            if isinstance(questions[question_key], dict) and 'content' in questions[question_key]:
                questions[question_key]['content'].append(line['bbox'] + [text_spans])
            # If the questions dict only has coordinates
            elif isinstance(questions[question_key], list) and len(questions[question_key]) >= 4:
                # Convert to dict with title and content
                title = questions[question_key]
                content = [line['bbox'] + [text_spans]]
                questions[question_key] = {
                    'title': title,
                    'content': content
                }
            # Otherwise just update the coordinates
            else:
                questions[question_key] = compare_coors_with_text(
                    questions[question_key], line['bbox'] + [text_spans])
    
    return questions

def process_line_image(questions, num_q, block):
    """Process image lines in questions"""
    if f'question_{num_q - 1}' in questions:
        # If content already exists in the dict
        if isinstance(questions[f'question_{num_q - 1}'], dict) and 'content' in questions[f'question_{num_q - 1}']:
            questions[f'question_{num_q - 1}']['content'].append(block['bbox'] + ['image'])
        # If the questions dict only has coordinates
        elif isinstance(questions[f'question_{num_q - 1}'], list) and len(questions[f'question_{num_q - 1}']) >= 4:
            # Convert to dict with title and content
            title = questions[f'question_{num_q - 1}']
            content = [block['bbox'] + ['image']]
            questions[f'question_{num_q - 1}'] = {
                'title': title,
                'content': content
            }
        # Otherwise just update the coordinates
        else:
            questions[f'question_{num_q - 1}'] = compare_coors_with_text(
                questions[f'question_{num_q - 1}'], block['bbox'] + ['image'])
    
    return questions

def compare_image_outside(questions, line, text_spans):
    """Check if the image belongs to previous question"""
    key_first = list(questions.keys())[0]

    for key in questions:
        if questions[key][1] < (line['bbox'][3] + line['bbox'][1])/2 < questions[key][3] or (key_first == key and (line['bbox'][3] + line['bbox'][1])/2 < questions[key][3]):
            from ..utils.coordinate_utils import compare_coors_with_text
            questions[key] = compare_coors_with_text(
                questions[key], line['bbox'] + [text_spans])
            break

    return questions

def compare_question_outside(questions, line, text_spans, answers_options = {}):
    """Update question's coordinates to cover the coordinates of answer options when answer options belongs to the previous question"""   
    for key in questions:
        # find what question the text belongs to 
        if questions[key][1] < (line['bbox'][1] + line['bbox'][3])/2 < questions[key][3]:
            from ..utils.coordinate_utils import compare_coors_with_text, compare_coors
            questions[key] = compare_coors_with_text(questions[key], line['bbox'] + [text_spans])
            # -- case the text in answers options --
            if len(answers_options) > 0 and key in answers_options and len(answers_options[key]) > 0 and (answers_options[key][0][0][1] < line['bbox'][1] or answers_options[key][0][0][1] < line['bbox'][3]):
                len_answer = len(answers_options[key])
                arr_i = []
                for i in range(1, len_answer):
                    if answers_options[key][i][0][1] < (line['bbox'][1] + line['bbox'][3])/2 < answers_options[key][i][0][3]:
                        arr_i.append(i)
                for i in arr_i:
                    if answers_options[key][i][0][2] < line['bbox'][2]:
                        if len(answers_options[key][i]) == 2:
                            answers_options[key][i][1] = compare_coors(
                                answers_options[key][i][1], line['bbox'])
                        else:
                            answers_options[key][i].append(line['bbox'])
            break
    
    return questions