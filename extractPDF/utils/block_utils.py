import json
from .text_utils import get_text_lines, get_text_in_block

def get_json_page(page, type_flag, flag_first_page=False):
    """Get page's jason after deleting header and footer"""
    blocks = page.get_text("json")
    blocks_json = json.loads(blocks)
    block_main = get_block_main(blocks_json['blocks'], type_flag, flag_first_page)
    
    return block_main

def get_block_main(blocks, type_flag, flag_first_page):
    """Delete header and footer"""
    if len(blocks) < 3:
        return []
    
    if get_text_in_block(blocks[0], type_flag, True) == True:
        del blocks[0]
    elif len(blocks) > 1 and get_text_in_block(blocks[1], type_flag) == True:
        del blocks[0:2]
    elif len(blocks) > 2 and get_text_in_block(blocks[2], type_flag) == True:
        del blocks[0:3]
    elif get_text_in_block(blocks[len(blocks) - 1], type_flag, True):
        del blocks[-1:]
    
    if len(blocks) > 0 and (get_text_lines(blocks[0]).strip() == "" or (flag_first_page == True and blocks[0]['type'] == 1)):
        del blocks[0]
    
    return blocks

def remove_item_in_blocks(blocks, block, line, keep_line=False):
    """Remove previous blocks starting from given block"""
    # -- delete previous block --
    index = blocks.index(block)
    del blocks[:index]
    # -- delete line used --
    if keep_line == False and len(blocks) > 0 and 'lines' in blocks[0] and blocks[0]['lines']:
        index = blocks[0]['lines'].index(line)
        del blocks[0]['lines'][:index+1]
        if len(blocks[0]['lines']) == 0 or get_text_lines(blocks[0]) == "":
            del blocks[0]
    
    return blocks