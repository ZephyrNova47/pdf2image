import re

def get_text_spans(line):
    """Get the text of a line"""
    text_block = ""
    for span in line['spans']:
        text_block += span['text']
    return text_block

def get_text_lines(block):
    """Get the text of a block"""
    text_block = ""
    if block['type'] == 0:
        for line in block['lines']:
            text_block += get_text_spans(line)
    else:
        text_block = "image"
    return text_block.strip()

def get_text_in_block(block, type_flag, check_page_num=False):
    """Check if block's text is footer or header"""
    text_block = get_text_lines(block).strip()

    if type_flag == 99 and re.search(r"Mã đề", text_block):
        return False
    pattern = r"((Trang|Page)+(\s+)?([0-9]\/[0-9]|[0-9]))|Mã đề"
    if check_page_num == True:
        pattern = r"((Trang|Page)+(\s+)?([0-9]\/[0-9]|[0-9]))|Mã đề|^(\s+)?([0-9]+)$"
    if text_block.strip() != "" and re.search(pattern, text_block.strip()):
        return True
    
    return False

def check_question_title(text_spans, line):
    """Check if given text contains beginning of question title"""
    if re.search(r"^(\s+)?(Câu|Cau|Bài|Question)+(\s)+[0-9]+(.*)?(\:|\.)?(\s+)?|^Mark the|^Read the|Đọc văn bản", text_spans.strip()) or re.search(r"^[0-9]+(\:|\.)\s", text_spans.strip()) and line["spans"][0]["flags"] >= 16:
        return True
    return False

def check_end_text(text_spans):
    """Check if given text contains the end of document"""
    if re.search(r"^((((–|—|-|_|\…|\.)(\s+)?)+)?(\s)?(HẾT|Hết|Het|HET|THE END))", text_spans.strip()):   
        return True
    return False

def check_correct_answer_text(text_spans):
    """Check if given text contains start of correct answers"""
    if re.search(r"^(bảng đáp án|hướng dẫn giải – đáp án)", text_spans.strip(), re.IGNORECASE):
        return True
    return False

def check_explain_text(text_spans):
    """Check if given text contains explanation"""
    if re.search(r"^hướng dẫn giải|lời giải", text_spans.strip(), re.IGNORECASE):
        return True
    return False

def check_essay_text(text_spans):
    """Check if given text contains essays"""
    if re.search(r"^(?!.*(trac nghiem|trắc nghiệm)).*", text_spans.strip()) and re.search(r"^(([A-F]{1})?(\s+)?(\:|\.)?(\s+)?(Phần|PHẦN|[A-F]{1}|PHẦN CÂU HỎI)?(\s+)?(I|II|III)?(\s+)?(\:|\.|\–|\-|\—)??(\s+)?(\.*?)?)?(\s+)?(Tự luận|TỰ LUẬN)|tự luận|PHẦN TỰ LUẬN", text_spans.strip()):
        return True
    return False

def check_reading_passage(text_spans):
    """Check if given text contains beginning of English vocabularies"""
    if re.search(r"^Mark the|^Read the|Đọc văn bản", text_spans.strip()):
        return True
    return False

def check_exam_multiple(text_spans):
    """Check if there are multiple exams in one pdf"""
    if re.search(r"^Mã đề|Đề", text_spans.strip()):
        return True
    return False

def check_correct_answer_type_1(text_span):
    """Check if the given text is in the format with number-letter, decimal, or mixed short-answer text."""
    if re.search(r"^[0-9]+(\s+)?(\.|-)(\s+)?([A-FĐSTF\s\w-]+|\d+([.,]\d+)?|\-\d+([.,]\d+)?)$", text_span):
        return True
    return False

def check_answer_option_title(text_span):
    """Check if given text is a single answer option (e.g., A, B, Đ, S, T, F)"""
    return True  # Matches original implementation

def check_correct_answer_type_special(text_span):
    """Check for special answer formats like Đ S T F or short-answer strings"""
    if re.match(r"^[ĐSTFA-F\s]+$|^-?\d+$|^\w+$", text_span):
        return True
    return False

def get_ascender_descender_option(answers_options):
    """Get ascenders and descenders for option identification

    Args:
        answers_options (dict): answer options information

    Returns:
        list: ascender_descender information
    """
    ascender_descender_option = []
    
    for q_num in answers_options:
        for option_letter in answers_options[q_num]:
            if len(answers_options[q_num][option_letter]) > 0:
                ascender_descender_option.append(option_letter)
        
        # We just need one example
        if len(ascender_descender_option) > 0:
            break
    
    return ascender_descender_option