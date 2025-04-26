import copy

def compare_coors(coor, coor_m):
    """Get the smallest x0, y0 and largest x1,y1 between two lists"""
    coor_new = copy.deepcopy(coor)
    # get smallest x0, y0
    coor_new[0] = min(coor[0], coor_m[0])
    coor_new[1] = min(coor[1], coor_m[1])
    # get largest x1, y1
    coor_new[2] = max(coor[2], coor_m[2])
    coor_new[3] = max(coor[3], coor_m[3])
    
    return coor_new

def compare_coors_with_text(coor, coor_m):
    """Get the smallest x0, y0 and largest x1,y1 between two lists"""
    coor_new = copy.deepcopy(coor)
    # get smallest x0, y0
    coor_new[0] = min(coor[0], coor_m[0])
    coor_new[1] = min(coor[1], coor_m[1])
    # get largest x1, y1 
    coor_new[2] = max(coor[2], coor_m[2])
    coor_new[3] = max(coor[3], coor_m[3])
    #append text
    coor_new[4] = coor[4] + coor_m[4]
    
    return coor_new

def check_mediabox_block(block):
    """Check if either block's x0 or block's y0 is negative"""
    return block["bbox"][0] < 0 or block["bbox"][1] < 0
        
def check_mediabox_height(block, page_height):
    """Check if block's height exceed page's height"""
    return block["bbox"][3] > page_height