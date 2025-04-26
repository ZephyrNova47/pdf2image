import re
import copy
import fitz
from ..utils.text_utils import (
    get_text_spans, get_text_lines, check_question_title, 
    check_end_text, check_correct_answer_text, check_reading_passage,
    check_essay_text, check_explain_text
)
from ..utils.block_utils import remove_item_in_blocks, get_json_page
from ..utils.coordinate_utils import (
    compare_coors, compare_coors_with_text, 
    check_mediabox_block, check_mediabox_height
)
from ..utils.image_utils import get_base64_title, get_base64_question
from .answer_processor import check_answer_option

def get_question_0(page):
    blocks = get_json_page(page, 0, True)
    answers_options = {}
    num_q = 1
    append_reading = False
    iteration = 1
    for block in blocks:
        # print(f"block: {iteration}")
        # for item in block:
            # if (item == "lines"):
                # print(f"    {item}")
                # for line in block[item]:
                    # print(f"        {line}")
            # else:
                # print(f"    {item}: {block[item]}")
            
        # print("-----------------")
        if num_q > 2:
            break
        # -- check lines in block --
        if "lines" in block:
            for line in block['lines']:
                text_spans = get_text_spans(line)
                # -------- check title questions ------------------------
                if check_question_title(text_spans, line):
                    if append_reading:
                        num_q -= 1
                        append_reading = False
                    
                    if check_reading_passage(text_spans):
                        append_reading = True
                    
                    num_q += 1
                    
                # --------------------- OPTION ANSWERS ---------------------------------------
                answers_options = check_answer_option(page,
                    num_q, False, line, text_spans, answers_options)

    return answers_options

def perform_traversal_questions_set(page, blocks, num_q, explain_previous, append_reading):
    """Collect information of questions"""
    # -- params question --
    questions = {}
    # -- params answer --
    answers_options = {}
    # -- params explanation --
    explains = {}

    flag_explain_in_question = False
    len_explains = len(explain_previous)
    if len_explains > 0 and f'question_{num_q - 1}' in explain_previous[len_explains - 1][1]:
        flag_explain_in_question = True
        
    page_height = page.mediabox[3]
    first_essay = False
    type_flag = 0

    for block in blocks:                    
        # --- mediabox out of rect ----
        if check_mediabox_block(block) or check_mediabox_height(block, page_height):    
            continue
        
        # -- check lines in block --
        if "lines" in block:
            for line in block['lines']:
                text_spans = get_text_spans(line)
                
                # -------Omit the line is empty -----------------------
                if text_spans.strip() == "" and line['bbox'][2] - line['bbox'][0] < 4:
                    continue
                # ---------------------- END OF PROCESSING QUESTION ---------------------------------
                if check_end_text(text_spans) or check_correct_answer_text(text_spans):
                    from .correct_answer_processor import process_stop_questions
                    data = process_stop_questions(remove_item_in_blocks(blocks, block, line, True))
                    data[0] = questions
                    data[1] = answers_options
                    if len(data[2]) > 0:
                        explains.update(data[2])
                    data[2] = explains
                    return data 
                    
                # ---------------------- QUESTION TITLE ---------------------------------
                if check_question_title(text_spans, line):
                    
                    # the reading passage is attached to the question.
                    # num_q already adds one when the reading passage is found
                    # therefore, num_q needs to be deducted by 1 if the question is found
                    if append_reading:
                        num_q -= 1
                        append_reading = False
                        
                    if check_reading_passage(text_spans):
                        append_reading = True
                    
                    # --- case Question 1: A.
                    answers_options = check_question_contain_title_answer(answers_options, text_spans, line, num_q, page)
                    
                    if f'question_{num_q}' not in questions:
                        questions[f'question_{num_q}'] = line['bbox'] + [text_spans]
                    else:
                        questions[f'question_{num_q}'] = compare_coors_with_text(questions[f'question_{num_q}'][:5], line['bbox'] + [text_spans])

                    # -- get title question --
                    if not append_reading:
                        questions[f'question_{num_q}'].append(
                            get_title_question(line, page)) 

                    num_q += 1
                    flag_explain_in_question = False                    
                    first_essay = False
                    continue

                # ---------------------- ESSAY ---------------------------------
                elif check_essay_text(text_spans) or first_essay:
                    if text_spans.isspace() :
                        continue
                    
                    # skip line with essay text
                    if check_essay_text(text_spans):
                        first_essay = True
                        type_flag = 2
                        continue 

                    first_essay = False
                    num_q += 1

                    questions[f'question_{num_q - 1}'] = line['bbox'] + [text_spans]
                    continue

                # ---------------------- EXPLAIN IN QUESTION ---------------------------------
                if check_explain_text(text_spans):
                    flag_explain_in_question = True
                    explains[f'question_{num_q - 1}'] = line['bbox'] + \
                        [text_spans]
                    continue

                # --------------------- OPTION ANSWERS ---------------------------------------
                if not append_reading and type_flag != 2:
                    answers_options = check_answer_option(page,
                        num_q, flag_explain_in_question, line, text_spans, answers_options)
                
                # --------------------- QUESTIONS ---------------------------------------
                if flag_explain_in_question == False:
                    from .explain_processor import merge_question as merge_q
                    questions = merge_q(
                        line, questions, num_q, text_spans, answers_options)
                else:
                    from .explain_processor import merge_question as merge_q
                    explains = merge_q(
                        line, explains, num_q, text_spans)
        else:
            if flag_explain_in_question == False:  
                if not explains:
                    from .explain_processor import process_line_image
                    questions = process_line_image(
                        questions, num_q, block)
                else:
                    data = process_line_image_with_answer_in_questions(
                        num_q, block, questions, explains)
                    questions = data[0]
                    explains = data[1]
            else:
                if bool(questions):
                    data = process_line_image_with_answer_in_questions(
                        num_q, block, explains, questions)
                    explains = data[0]
                    questions = data[1]
                else:
                    from .explain_processor import process_line_image
                    explains = process_line_image(
                        explains, num_q, block)
    print("questions: ", questions)
    return [questions, answers_options, explains, {}, num_q, type_flag, append_reading]

def check_question_contain_title_answer(answers_options, text_spans, line, num_q, page):
    """Check if questions contains answer title (for example: Question 4: A.)"""
    if re.search(r"^(\s+)?(Question)+\s+[0-9]+(\:|\.)?(\s+)?(A\.)(\s+)?", text_spans):
        bbox = page.search_for("A.", clip = fitz.Rect(line["bbox"][0],line["bbox"][1],line["bbox"][2],line["bbox"][3]))
        answers_options[f'question_{num_q}'] = [[
            [bbox[0].x0, bbox[0].y0, bbox[0].x1, bbox[0].y1, "A.", line['spans'][0]['ascender'], line['spans'][0]['color'], line['spans'][0]['flags']],
            [bbox[0].x1, line["bbox"][1], line["bbox"][2], line["bbox"][3]]
        ]]

    return answers_options

def get_title_question(line, page):
    """Return the coordinates of question's title"""
    text_spans = ''
    coor = []
    for item in line["spans"]:
        text_spans += item['text']
        if len(coor) == 0:
            coor = item['bbox']
        else:
            coor = compare_coors(coor, item['bbox'])
        if re.search(r"^(\s+)?(Câu|Cau|Bài|Question)+(\s|s\+)+[0-9]+(\:|\.)?(\s+)?$", text_spans):
            # -- True: title standard --
            coor += [text_spans]
            break
        elif re.search(r"^(\s+)?(Câu|Cau|Bài|Question)+(\s|s\+)+[0-9]+(.*)?(\:|\.)?(\s+)?", text_spans):
            coor = check_question_width(page, line, text_spans)
            coor += [text_spans]
            break
        elif re.search(r"^[0-9]+(\:|\.)?\s", text_spans.strip()):
            coor = check_question_width(page, line, text_spans)
            coor += [text_spans]
    
    return coor

def check_question_width(page, line, text_spans):
    """Get coordinator of question title when the text includes the the question title and content"""
    bbox = search_text_coor(page, line["bbox"], text_spans)
    return [bbox[0].x0, bbox[0].y0, bbox[0].x1, bbox[0].y1]

def search_text_coor(page, coor, text_spans):
    """Search the coordinator of text_spans among the given coor"""
    # find full first question title (exp: Question 1:)
    title_list = re.search(r"(Câu|Cau|Bài|Question)(\s+)?(\d+)(\s+)?(\:|\.)?", text_spans) 
    title = title_list.group(1) if title_list is not None else ""
    num_first = title_list.group(3) if title_list is not None else 1
    extra = title_list.group(5) if title_list.group(5) is not None else ""
    # the space between question title "Question" and question number"1". 
    white_space_1 = title_list.group(2) if title_list.group(2) is not None else " "
    # the space between question number "1" and extra character like ":". 
    white_space_2 = title_list.group(4) if title_list.group(4) is not None else ""
    full_title = title + white_space_1 + str(num_first) + white_space_2 + extra 
    bbox = page.search_for(full_title, clip = fitz.Rect(coor[0], coor[1], coor[2], coor[3]))
    
    return bbox

def process_line_image_with_answer_in_questions(num_q, block, object_1, object_2):
    """Find what question the image belongs to"""
    question_key = f'question_{num_q - 1}'
    
    # Check if the question exists in object_1
    if question_key in object_1:
        # Check if the value is a list/array with at least 4 elements
        if (isinstance(object_1[question_key], list) and len(object_1[question_key]) > 3 and 
            isinstance(object_1[question_key][3], (int, float))):
            if block['bbox'][3] >= object_1[question_key][3]:
                from ..utils.coordinate_utils import compare_coors_with_text
                object_1[question_key] = compare_coors_with_text(
                    object_1[question_key], block['bbox'] + ['image'])
                return [object_1, object_2]
        # Check if the value is a dict with 'content' that has coordinates
        elif isinstance(object_1[question_key], dict) and 'content' in object_1[question_key]:
            content = object_1[question_key]['content']
            if content and isinstance(content[0], list) and len(content[0]) > 3:
                if block['bbox'][3] >= content[0][3]:
                    content.append(block['bbox'] + ['image'])
                    return [object_1, object_2]
    
    # If we reach here, process as an image outside two objects
    return compare_image_outside_two_object(object_1, object_2, block, 'image')

def compare_image_outside_two_object(object_1, object_2, line, text_spans):
    """Find what question the image belongs to when image belongs between two questions"""
    key_1 = get_object_match_image(object_1, line)
    key_2 = get_object_match_image(object_2, line)
    if key_1 != "" and key_2 != "":
        if object_1[key_1][3] < object_2[key_2][3]:
            from ..utils.coordinate_utils import compare_coors_with_text
            object_1[key_1] = compare_coors_with_text(
                object_1[key_1], line['bbox'] + [text_spans])
        else:
            from ..utils.coordinate_utils import compare_coors_with_text
            object_2[key_2] = compare_coors_with_text(
                object_2[key_2], line['bbox'] + [text_spans])
    elif key_1 != "":
        from ..utils.coordinate_utils import compare_coors_with_text
        object_1[key_1] = compare_coors_with_text(
            object_1[key_1], line['bbox'] + [text_spans])
    elif key_2 != "":
        from ..utils.coordinate_utils import compare_coors_with_text
        object_2[key_2] = compare_coors_with_text(
            object_2[key_2], line['bbox'] + [text_spans])

    return [object_1, object_2]

def get_object_match_image(obj, line):
    """Return which question the line belongs to"""
    if not obj:
        return ""
        
    keys = list(obj.keys())
    if not keys:
        return ""
        
    key_first = keys[0]
    
    for key in obj:
        value = obj[key]
        
        # Skip if the value doesn't have proper coordinates
        if not isinstance(value, list) or len(value) < 4:
            if isinstance(value, dict) and 'content' in value:
                # Try to use content coordinates
                content = value['content']
                if content and isinstance(content[0], list) and len(content[0]) >= 4:
                    y1 = content[0][1]
                    y3 = content[0][3]
                    if y1 < (line['bbox'][3] + line['bbox'][1])/2 < y3:
                        return key
            continue
            
        # Check if the line's center is between the top and bottom of the question
        if value[1] < (line['bbox'][3] + line['bbox'][1])/2 < value[3]:
            return key
        # Special case for the first question
        elif key == key_first and (line['bbox'][3] + line['bbox'][1])/2 < value[3]:
            return key

    return ""


import re
import copy
from ..utils.text_utils import (
    get_text_spans, check_question_title, check_reading_passage
)
from ..utils.block_utils import remove_item_in_blocks
from ..utils.coordinate_utils import (
    compare_coors, compare_coors_with_text, 
    check_mediabox_block, check_mediabox_height
)
from ..utils.image_utils import get_base64_title, get_base64_question



def process_question_and_answers(questions, doc, coor_x, ascender_descender_option):
    """Process questions, titles, and answers to create base64 images
    
    Args:
        questions (list): List of questions by page
        doc (fitz.Document): PDF document
        coor_x (list): Width coordinates for adjustment
        ascender_descender_option (list): Format options for answers
        
    Returns:
        list: Lists of questions, answers, and titles with base64 images
    """
    questions_result = {}
    answers_result = {}
    titles_result = {}
    
    # Process each page of questions
    for question_page in questions:
        page_num = question_page[0]
        questions_dict = question_page[1]
        answers_dict = question_page[2] if len(question_page) > 2 else {}
        
        # Process each question
        for q_key, q_data in questions_dict.items():
            # Skip if not a proper question structure
            if not isinstance(q_data, dict):
                continue
                
            # Process question title
            if 'title' in q_data and q_data['title']:
                coor_title = process_title_coordinates(q_data['title'])
                if coor_title:
                    title_image = get_base64_title(doc[page_num], coor_title)
                    if len(title_image) > 4 and title_image[4].startswith('data:image/png;base64,'):
                        titles_result[q_key] = title_image
            
            # Process question content
            if 'content' in q_data and q_data['content']:
                # Parse the question number
                q_num = 0
                if q_key.startswith('question_'):
                    try:
                        q_num = int(q_key.split('_')[1])
                    except (IndexError, ValueError):
                        pass
                
                # Get answer options coordinates
                coor_answer_cover = []
                answer_key = f'question_{q_num}'
                if answer_key in answers_dict:
                    coor_answer_cover = get_answer_coordinates(answers_dict[answer_key])
                
                # Process content coordinates
                coor_q = process_content_coordinates(q_data['content'])
                if coor_q and len(coor_q) >= 4:
                    # Update width coordinates
                    coor_x[0] = min(coor_q[0], coor_x[0])
                    coor_x[1] = max(coor_q[2], coor_x[1])
                    
                    # Get title coordinates for masking
                    data_title = []
                    if q_key in titles_result:
                        data_title = titles_result[q_key][:4]
                    
                    # Generate question image
                    question_image = get_base64_question(
                        doc[page_num], coor_q, coor_answer_cover, data_title)
                    
                    if len(question_image) > 4 and isinstance(question_image[4], str) and question_image[4].startswith('data:image/png;base64,'):
                        questions_result[q_key] = question_image
            
            # Process answer options
            if q_key.startswith('question_'):
                q_num = int(q_key.split('_')[1])
                if q_num in answers_dict:
                    answer_images = process_answer_images(
                        doc[page_num], answers_dict[q_num], ascender_descender_option)
                    if answer_images:
                        answers_result[q_key] = answer_images
    
    return [questions_result, answers_result, titles_result]

def process_title_coordinates(titles):
    """Process and merge coordinates for question title"""
    if not titles:
        return []
        
    coor_title = titles[0][:4]
    
    for title in titles[1:]:
        if len(title) >= 4:  # Ensure the item has coordinates
            coor_title = compare_coors(coor_title, title[:4])
    
    # Add padding
    coor_title[0] = max(0, coor_title[0] - 5)
    coor_title[1] = max(0, coor_title[1] - 5)
    coor_title[2] = coor_title[2] + 5
    coor_title[3] = coor_title[3] + 5
    
    return coor_title

def process_content_coordinates(content):
    """Process and merge coordinates for question content"""
    if not content:
        return []
    
    coor_q = content[0][:4] + [""]
    
    for line in content[1:]:
        if len(line) >= 4:  # Ensure the item has coordinates
            line_with_text = line[:4] + [line[4] if len(line) > 4 else ""]
            coor_q = compare_coors_with_text(coor_q, line_with_text)
    
    # Add padding
    coor_q[0] = max(0, coor_q[0] - 5)
    coor_q[1] = max(0, coor_q[1] - 5)
    coor_q[2] = coor_q[2] + 5
    coor_q[3] = coor_q[3] + 5
    
    return coor_q

def get_answer_coordinates(answer_options):
    """Get combined coordinates for all answer options"""
    coor_answer = []
    
    # Handle different answer option formats
    if isinstance(answer_options, dict):
        for option_key, options in answer_options.items():
            for option in options:
                if len(option) >= 4:
                    if not coor_answer:
                        coor_answer = option[:4]
                    else:
                        coor_answer = compare_coors(coor_answer, option[:4])
    elif isinstance(answer_options, list):
        for option in answer_options:
            if len(option) >= 4:
                if not coor_answer:
                    coor_answer = option[:4]
                else:
                    coor_answer = compare_coors(coor_answer, option[:4])
    
    return coor_answer

def process_answer_images(page, answer_options, ascender_descender_option):
    """Create images for answer options"""
    result = {}
    
    # Handle different answer option formats
    if isinstance(answer_options, dict):
        for option_key, options in answer_options.items():
            for option in options:
                if len(option) >= 4:
                    coor = option[:4]
                    # Add padding
                    coor[0] = max(0, coor[0] - 5)
                    coor[1] = max(0, coor[1] - 5)
                    coor[2] = coor[2] + 5
                    coor[3] = coor[3] + 5
                    
                    image = get_base64_title(page, coor)
                    
                    # Ensure we get valid image data
                    if len(image) > 4 and image[4].startswith('data:image/png;base64,'):
                        if option_key not in result:
                            result[option_key] = []
                        result[option_key].append(image)
    elif isinstance(answer_options, list):
        for i, option in enumerate(answer_options):
            if len(option) >= 4:
                coor = option[:4]
                # Add padding
                coor[0] = max(0, coor[0] - 5)
                coor[1] = max(0, coor[1] - 5)
                coor[2] = coor[2] + 5
                coor[3] = coor[3] + 5
                
                image = get_base64_title(page, coor)
                
                # Ensure we get valid image data
                if len(image) > 4 and image[4].startswith('data:image/png;base64,'):
                    option_key = f'option_{i}'
                    if option_key not in result:
                        result[option_key] = []
                    result[option_key].append(image)
    
    return result