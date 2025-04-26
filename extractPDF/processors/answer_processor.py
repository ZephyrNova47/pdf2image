import re
import fitz
import copy
from ..utils.text_utils import get_text_spans
from ..utils.coordinate_utils import compare_coors
from ..utils.image_utils import get_base64_image, format_option_response, DataBase64Image, ToDataBase64Image

def get_ascender_descender_option(answers_options):
    """Get the value of ascender, descender and flag of answer options"""
    if "question_1" not in answers_options:
        return []

    # -- compare and get ascender_descender_option --
    arr_compare = {}
    ascender_descender_option = []

    for answers_option in answers_options["question_1"]:
        item = answers_option[0]
        option_text = item[4].replace(" ", "").replace(".", "")
        if len(arr_compare) == 0:
            arr_compare[option_text] = [1, item[4], item[5], item[6], item[7]]
        else:
            if option_text in arr_compare:
                arr_compare[option_text][0] += 1
            else:
                arr_compare[option_text] = [1, item[4], item[5], item[6], item[7]]
    
    for key in arr_compare:
        if arr_compare[key][0] == 1:
            # get ascender, color, flags (boldness of text)
            ascender_descender_option = [ arr_compare[key][2], arr_compare[key][3], arr_compare[key][4] ]
            break
    
    return ascender_descender_option

def check_answer_option(page, num_q, flag_explain_in_question, line, text_spans, answers_options):
    """Check if answer's option starts at current line"""
    if flag_explain_in_question == False:
        if re.search(r"(\.)?((\s+)?[A-D]{1}(\s+)?\.(\s+)?)|^(\.)?((\s+)?[A-D]{1}(\s+)?(\.)?(\s+)?)", text_spans):
            r2 = re.compile("(\.)?((\s+)?[A-D]{1}(\s+)?(\.)?(\s+)?)")
            data = r2.findall(text_spans)
            if len(data) <= 1 or len(line["spans"]) == 1:
                for item in line["spans"]:
                    if re.search("^(\.)?((\s+)?[A-D]{1}(\s+)?(\.)?(\s+)?)$|^((\s+)?[A-D]{1}(\s+)?\.(\s+)?)|^((\s+)?[A-D]{1}(\s)(\s+)?)", item['text']):
                        if len(data) == 4:
                            if re.search(r"^[A-D\s]*$", item["text"]): #text only contains A B C D
                                answers_options = get_answers_options_without_value(answers_options, item, flag_explain_in_question, num_q, line)
                            else:
                                answers_options = get_answers_options_multiple(len(data), page, item, answers_options, flag_explain_in_question, num_q, line, text_spans)
                                break

                        answers_options = add_option_answer(
                        item['bbox'] + [item['text'], item['ascender'], item['color'], item['flags']], answers_options, num_q)
                        answers_options = get_answers_options(flag_explain_in_question, answers_options, num_q, line)
                        break
            else:
                answers_options = get_title_answer_plural(
                    line, answers_options, num_q, text_spans, page)

    # add text to answer
    if f"question_{num_q - 1}" in answers_options and len(answers_options[f"question_{num_q - 1}"]) > 0:
         # only add when option does not have text and not add next title value (exp: B C D)
        if len(answers_options[f"question_{num_q - 1}"][-1][1]) < 5 and not re.search("^[A-D](\.){0,1}$", text_spans.replace(" ", "")):
            # find number of extra option. Exp: A B C => B C are the extra options
            r2 = re.compile("\s{1,}?((\s+)?[A-D]{1}(\s+)?(\.)?(\s+)?)")  
            data = r2.findall(text_spans)

            # find option 
            r3 = re.compile("(\.)?((\s+)?[A-D]{1}(\s+)?(\.)?(\s+)?)") 
            data_1 = r3.findall(text_spans)

            len_ans = len(answers_options[f"question_{num_q - 1}"])
            if len(data) < 1 or len(data_1) == 1: # text line does not contain extra options
                if len(answers_options[f"question_{num_q - 1}"][-1][1]) < 5: # only need to add text to option the first time
                    answers_options[f"question_{num_q - 1}"][-1][1].append(text_spans)
            else:
                # case: A. 12 B.4 => A needs to be marked as "Have Text"
                for i in range(len(data)):
                    if len_ans-2-i >= 0 and len(answers_options[f"question_{num_q - 1}"][len_ans-2-i][1]) < 5:
                        answers_options[f"question_{num_q - 1}"][len_ans-2-i][1].append("Have Text")
                answers_options[f"question_{num_q - 1}"][-1][1].append(text_spans)

    return answers_options

def check_answer_without_value(answer):
    """Check if answer option has content"""
    count = 0
    r2 = re.compile("[A-D](\.)?(\s+)")

    for option in answer:        
        # check title contains multiple question titles: text A B C
        if len(answer) < 4 and len(option[1]) > 4 and len(r2.findall(option[0][4])) >= 2:
            return True

        if len(option[1]) <= 4: # answers without content
            count += 1

    return count >= 2

def get_answers_options_without_value(answers_options, item, flag_explain_in_question, num_q, line):
    """Process answer option when option has no value"""
    answers_options = add_option_answer(
                [item["bbox"][0], item["bbox"][1], item["bbox"][2], item["bbox"][1]] + [item["text"], item['ascender'], item['color'], item['flags']], answers_options, num_q) 
    answers_options = get_answers_options(flag_explain_in_question, answers_options, num_q, line)
    
    return answers_options         

def get_answers_options_multiple(len_options, page, item, answers_options, flag_explain_in_question, num_q, line, text_spans):
    """Process answer option when options are on the same span's text"""
    options = ["A.", "B.", "C.", "D."]

    for i in range(len_options):
        bbox = page.search_for(options[i], clip = fitz.Rect(item["bbox"][0], item["bbox"][1], item["bbox"][2], item["bbox"][3]))
        if len(bbox) > 0:
            answers_options = add_option_answer(
                [bbox[0].x0, bbox[0].y0, bbox[0].x1, bbox[0].y1] + [options[i], item['ascender'], item['color'], item['flags']], answers_options, num_q)                
            answers_options = get_answers_options(flag_explain_in_question, answers_options, num_q, line)
    return answers_options 

def get_title_answer_plural(line, answers_options, num_q, text_spans, page):
    """Process answers option when options are in multiple span"""
    for item in line["spans"]:
        if re.search("^(\.)?((\s+)?[A-D]{1}(\s+)?(\.)?(\s+)?)$|^((\s+)?[A-D]{1}(\s+)?\.(\s+)?)", item['text']):
            # -- True: title standard --
            span = item['bbox'] + [item['text'],
                                   item['ascender'], item['color'], item['flags']]
            answers_options = add_option_answer(span, answers_options, num_q)
        else:
            answers_options = get_answers_options(
                False, answers_options, num_q, {'bbox': item['bbox']})
        
    return answers_options

def add_option_answer(span, answers_options, num_q):
    """Add option coordinates to list answers_options"""
    # -- add option answers --
    data_op = [span, [span[0], span[1], span[2], span[3]]]
    if f'question_{num_q - 1}' in answers_options:
        answers_options[f'question_{num_q - 1}'].append(data_op)
    else:
        answers_options[f'question_{num_q - 1}'] = [data_op]

    return answers_options

def get_answers_options(flag_explain_in_question, answers_options, num_q, line):
    """Add coordinates of answer's value"""
    if f'question_{num_q - 1}' in answers_options and flag_explain_in_question == False:
        if line['bbox'][3] > answers_options[f'question_{num_q - 1}'][-1][0][1]:
            if len(answers_options[f'question_{num_q - 1}'][-1]) == 2:
                answers_options[f'question_{num_q - 1}'][-1][1] = compare_coors(
                    answers_options[f'question_{num_q - 1}'][-1][1], line['bbox'])
            else:
                answers_options[f'question_{num_q - 1}'][-1].append(
                    line['bbox'])
    
    return answers_options

def process_answer_options(page, answers_dict):
    """Process answer options into base64 images with API format
    
    Args:
        page (fitz.Page): PDF page
        answers_dict (dict): Dictionary of answer options coordinates
        
    Returns:
        dict: Dictionary with options formatted for API response
    """
    result = {}
    
    for question_key, options in answers_dict.items():
        result[question_key] = {"options": []}
        
        # Handle options as list (common format in the data)
        if isinstance(options, list):
            for option in options:
                # Skip if not valid coordinates
                if not isinstance(option, list) or len(option) < 4:
                    continue
                    
                # Get base64 image
                coor = option[:4]
                image_data = get_base64_image(page, coor)
                if not image_data:
                    continue
                    
                # Format the response structure
                formatted_option = format_option_response(coor, image_data)
                if formatted_option:
                    result[question_key]["options"].append(formatted_option)
        
        # Handle options as dictionary (alternative format)
        elif isinstance(options, dict):
            for option_key, option_coords in options.items():
                # Skip if not valid coordinates
                if not option_coords or len(option_coords) < 4:
                    continue
                    
                # Get base64 image
                image_data = get_base64_image(page, option_coords)
                if not image_data:
                    continue
                    
                # Format the response structure
                formatted_option = format_option_response(option_coords, image_data)
                if formatted_option:
                    result[question_key]["options"].append(formatted_option)
    
    return result

def extract_option_images(page, answers_dict, question_key):
    """Extract and format option images for a specific question
    
    Args:
        page (fitz.Page): PDF page
        answers_dict (dict): Answer data for all questions
        question_key (str): The question key to process (e.g., 'question_1')
        
    Returns:
        dict: Options formatted as {'options': [[x1,y1,x2,y2,base64,x1,y1,x2,y2,base64,0], ...]}
    """
    if not answers_dict or question_key not in answers_dict:
        return {'options': []}
    
    options = []
    answer_options = answers_dict[question_key]
    
    # Handle different structures of answer options
    if isinstance(answer_options, list):
        # Process list format (most common)
        for option in answer_options:
            # Each option typically has title coordinates [0] and content coordinates [1]
            if len(option) < 2:
                continue
                
            title_coords = option[0]
            content_coords = option[1]
            
            # Skip if invalid coordinates
            if not title_coords or len(title_coords) < 4 or not content_coords or len(content_coords) < 4:
                continue
            
            # Extract coordinates
            title_x1, title_y1, title_x2, title_y2 = title_coords[:4]
            content_x1, content_y1, content_x2, content_y2 = content_coords[:4]
            
            # Generate base64 images
            title_image = get_base64_image(page, [title_x1, title_y1, title_x2, title_y2])
            content_image = get_base64_image(page, [content_x1, content_y1, content_x2, content_y2])
            
            # Format according to expected output
            if title_image and content_image:
                formatted_option = [
                    float(title_x1), float(title_y1), float(title_x2), float(title_y2), 
                    title_image,
                    float(content_x1), float(content_y1), float(content_x2), float(content_y2),
                    content_image, 
                    0
                ]
                options.append(formatted_option)
    
    elif isinstance(answer_options, dict):
        # Handle dictionary format (less common)
        for option_key, option_coords in answer_options.items():
            if not option_coords or len(option_coords) < 4:
                continue
                
            # Generate base64 image
            image = get_base64_image(page, option_coords[:4])
            
            if image:
                # For dictionary format, we use the same coordinates for both parts
                formatted_option = [
                    float(option_coords[0]), float(option_coords[1]), 
                    float(option_coords[2]), float(option_coords[3]),
                    image,
                    float(option_coords[0]), float(option_coords[1]), 
                    float(option_coords[2]), float(option_coords[3]),
                    image, 
                    0
                ]
                options.append(formatted_option)
    
    return {'options': options}

def get_base64_image(page, coors):
    """Get base64 image for coordinates
    
    Args:
        page (fitz.Page): PDF page
        coors (list): Coordinates [x1,y1,x2,y2]
        
    Returns:
        str: base64 encoded image
    """
    import fitz
    
    if not coors or len(coors) < 4:
        return ""
        
    try:
        # Check coordinates are within page mediabox
        coors[2] = min(float(coors[2]), page.mediabox[2])
        coors[3] = min(float(coors[3]), page.mediabox[3])

        # Create rectangle for cropping
        crop_box = fitz.Rect(coors[0], coors[1], coors[2], coors[3])
        
        # Skip if invalid rectangle
        if crop_box.is_empty or crop_box.is_infinite:
            return ""
            
        # Crop and render the image
        page.set_cropbox(crop_box)
        scale = 1.5  # zoom factor
        zoom_x = scale
        zoom_y = scale
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to base64
        data = ToDataBase64Image(pix)
        pix = None
        return data
    except Exception as e:
        print(f"Error generating base64 image: {e}")
        return ""