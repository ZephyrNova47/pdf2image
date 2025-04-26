import re
from ..utils.text_utils import (
    get_text_spans, get_text_lines, check_end_text, 
    check_correct_answer_text, check_explain_text,
    check_question_title, check_correct_answer_type_1,
    check_answer_option_title, check_correct_answer_type_special
)
from ..utils.block_utils import remove_item_in_blocks

def process_correct_answer(blocks):
    """Process correct answers

    Args:
        blocks (list): list of page's blocks

    Returns:
        list: list containing returning type, correct answers, and question's number
    """
    text_spans = get_text_lines(blocks[0])
    if check_correct_answer_text(text_spans):
        del blocks[0]

    # Check each block for correct answers
    for block in blocks:
        if "lines" in block:
            text_spans = get_text_lines(block)

            from ..utils.text_utils import check_exam_multiple
            if check_exam_multiple(text_spans):
                return [{}, {}, {}, {}]
            
            if text_spans == "":
                continue
            
            # Check if it's an explanation block
            if check_explain_text(text_spans):
                from ..processors.explain_processor import process_explain
                return process_explain(blocks, 1)

            # Process the first two lines to determine answer type
            if len(block['lines']) >= 2:
                text_span_1 = block['lines'][0]['spans'][0]['text'].strip()
                text_span_2 = block['lines'][1]['spans'][0]['text'].strip()
                # Check various answer formats
                if check_correct_answer_type_1(text_span_1):
                    return get_correct_answer_type_1(blocks)
                elif check_answer_option_title(text_span_2):
                    return get_correct_answer_type_2(blocks)
                elif check_correct_answer_type_special(text_span_1) or check_correct_answer_type_special(text_span_2):
                    return get_correct_answer_type(blocks)
            break
        else:
            del blocks[blocks.index(block)]
    
    return [{}, {}, {}, {}, -1, 99]

def process_stop_questions(blocks):
    """Process data when the end of document is found

    Args:
        blocks (list): list of page's blocks

    Returns:
        list: list containing returning type, questions and question's number 
    """
    if not blocks:
        return [{}, {}, {}, {}, 1, 99]
        
    text_spans = get_text_lines(blocks[0])
    if check_end_text(text_spans):
        del blocks[0]
        
    for block in blocks:
        # -- check lines in block --
        if "lines" in block:
            for line in block['lines']:
                text_spans = get_text_spans(line)
                if check_correct_answer_text(text_spans.strip()):
                    data_answer = process_correct_answer(
                        remove_item_in_blocks(blocks, block, line))
                    return data_answer
                elif check_explain_text(text_spans):
                    from ..processors.explain_processor import process_explain
                    return process_explain(remove_item_in_blocks(blocks, block, line), 1)
                else:
                    if len(block['lines']) == 1:
                        continue
                    text_span_1 = block['lines'][0]['spans'][0]['text'].strip()
                    text_span_2 = block['lines'][1]['spans'][0]['text'].strip()
                    if re.search(r"^[0-9]+(\s+)?(\:|\.)(\s+)?[A-F]{1}$", text_span_1):
                        return get_correct_answer_type_1(blocks)
                    elif re.search(r"^[A-F]{1}$", text_span_2):
                        return get_correct_answer_type_2(blocks)
                    elif re.search(r"^[A-F]{1}$", text_span_1) or re.search(r"^[A-F]{1}$", text_span_2):
                        return get_correct_answer_type(blocks)
    
    return [{}, {}, {}, {}, 1, 99]

def process_explain_in_correct_answer(blocks, correct_answers):
    """Process explains when there are explanation and correct answers 

    Args:
        blocks (list): list of page's blocks

    Returns:
        list: list containing return type, coordinates of explains and number of questions
    """
    from ..processors.explain_processor import process_explain
    data = process_explain(blocks, 1)
    data[3] = correct_answers
    
    return data

def get_correct_answer_type_1(blocks):
    """Process correct answers when one span includes both question number and answer type.

    Args:
        blocks (list): list of page's blocks
    
    Returns:
        list: list of return type, correct answers, and question number
    """
    correct_answers = {}
    for block in blocks:
        # Check lines in block
        if "lines" in block:
            for line in block['lines']:
                text_spans = get_text_spans(line).strip()

                # Check for valid answer format
                if check_correct_answer_type_1(text_spans):
                    # Match only the first instance of a period or dash after the question number
                    match = re.match(r"^(\d+)(\s*[-.]?\s*)(.+)$", text_spans)
                    if match:
                        question_number = match.group(1).strip()
                        answer_text = match.group(3).strip()
                        
                        # Add answer to the correct question number
                        correct_answers[f'question_{question_number}'] = answer_text
                
                elif check_explain_text(text_spans):
                    return process_explain_in_correct_answer(remove_item_in_blocks(blocks, block, line, True), correct_answers)
                
                elif check_question_title(text_spans, line):
                    return process_explain_in_correct_answer(remove_item_in_blocks(blocks, block, line, True), correct_answers)

    return [{}, {}, {}, correct_answers, -1, 99]

def get_correct_answer_type_2(blocks):
    """Process correct answers when one span includes the number and the next span includes the letter

    Args:
        blocks (list): list of page's blocks
    Returns:
        list: list of return type, correct answers and question number
    """
    correct_answers = {}
    num_correct = None 

    for block in blocks:
        # Check lines in block
        if "lines" in block:
            for line in block['lines']:
                for span in line['spans']:
                    text_span = span['text'].strip()  # Strip whitespace

                    # Check if text_span is a question number format like "1." or "3."
                    if re.match(r"^\d+\.$", text_span):
                        # Extract only the number part, removing the trailing dot
                        num_correct = text_span[:-1]
                    # Save the correct answer if num_correct exists and text_span is valid
                    elif num_correct and text_span not in ['', None]:
                        correct_answers[f'question_{num_correct}'] = text_span
                        num_correct = None  # Reset for the next question
                    # Additional conditions for explanation text or question titles
                    elif check_answer_option_title(text_span):
                        if num_correct:
                            correct_answers[f'question_{num_correct}'] = text_span
                    elif check_explain_text(text_span):
                        return process_explain_in_correct_answer(remove_item_in_blocks(blocks, block, line), correct_answers)
                    elif check_question_title(text_span, line):
                        return process_explain_in_correct_answer(remove_item_in_blocks(blocks, block, line, True), correct_answers)

    # Remove any "question_None" entry from the dictionary
    correct_answers.pop('question_None', None)

    return [{}, {}, {}, correct_answers, -1, 99]

def get_correct_answer_type(blocks):
    """Check what type of correct answers is

    Args:
        blocks (list): list of page's blocks

    Returns:
        list: list containing returning type, correct answers and question's number
    """
    correct_answers = {}
    num_title = 1
    
    for block in blocks:
        # -- check lines in block --
        if "lines" in block:
            for line in block['lines']:
                for span in line['spans']:
                    text_span = span['text'].strip()
                    if re.search(r"^[A-F]{1}$", text_span):
                        correct_answers[f'question_{num_title}'] = text_span
                        num_title +=1
                    elif check_explain_text(text_span):
                        return process_explain_in_correct_answer(remove_item_in_blocks(blocks, block, line), correct_answers)
                    elif check_question_title(text_span, line):
                        return process_explain_in_correct_answer(blocks, correct_answers)
                          
    return [{}, {}, {}, correct_answers, -1, 99]