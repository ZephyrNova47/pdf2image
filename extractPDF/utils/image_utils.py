import base64
import fitz

def DataBase64Image(base64Data):
    """Format base64 data as image"""
    if isinstance(base64Data, bytes):
        base64Data = base64Data.decode('utf-8')
    dataBase64 = f'data:image/png;base64,{base64Data}'
    dataBase64 = dataBase64.replace(
        "data:image/png;base64,b'", "data:image/png;base64,").replace("'", "")
    return dataBase64

def ToDataBase64Image(fitz_pix):
    """Convert fitz pixmap to base64 string"""
    base64Data = base64.b64encode(fitz_pix.pil_tobytes("png"))
    return DataBase64Image(base64Data)

def get_base64_title(page, coors):
    """Get coordinates and base64 image for titles"""
    data = ''
    # Check coordinates are within page mediabox
    coors[2] = min(coors[2], page.mediabox[2])
    coors[3] = min(coors[3], page.mediabox[3])

    crop_box = fitz.Rect(coors[0], coors[1], coors[2], coors[3])
    if not crop_box.is_empty and not crop_box.is_infinite:
        page.set_cropbox(crop_box)
        
        scale = 1.5
        zoom_x = scale  # horizontal zoom
        zoom_y = scale  # vertical zoom
        mat = fitz.Matrix(zoom_x, zoom_y)  # zoom factor 1.5 in each dimension
        pix = page.get_pixmap(matrix=mat) 

        data = ToDataBase64Image(pix)
        pix = None

    return coors + [data]

def get_base64_question(page, coors, coor_answer_cover=None, data_title=None):
    """Get base64 image of question, setting answers and question's title to white"""
    if coor_answer_cover is None:
        coor_answer_cover = []
    if data_title is None:
        data_title = []
        
    data = ''
    # Guarantee coordinates are within page mediabox
    coors[2] = min(coors[2], page.mediabox[2])
    coors[3] = min(coors[3], page.mediabox[3])

    crop_box = fitz.Rect(coors[0], coors[1], coors[2], coors[3])
    if not crop_box.is_empty and not crop_box.is_infinite:
        page.set_cropbox(crop_box)

        scale = 1.5
        zoom_x = scale  # horizontal zoom
        zoom_y = scale  # vertical zoom
        mat = fitz.Matrix(zoom_x, zoom_y)  
        pix = page.get_pixmap(matrix=mat)

        # Case question 1: A. - Delete all question
        if len(coor_answer_cover) > 0 and coor_answer_cover[1] == coors[1]:
            pix = delete_white_coor_section(pix, coors, scale)

        # Set question title to white
        if data_title:
            pix = delete_white_coor(pix, data_title, coors, scale)
        
        data = ToDataBase64Image(pix)
        pix = None
    
    # Ensure we have a properly formatted result
    result = coors.copy()
    if len(result) <= 4 or not isinstance(result[4], str):
        # Add or replace the image data at index 4
        if len(result) > 4:
            result[4] = data
        else:
            result.append(data)
    
    # Remove any extra elements beyond the image data
    if len(result) > 5:
        del result[5:]
    
    return result

def delete_white_coor_section(pix, coor, scale):
    """Set color of given coordinates to white"""
    if coor:
        pix.set_rect(
            fitz.Rect(
                0,
                0,
                coor[2]*scale,
                coor[3]*scale
            ),
            (255, 255, 255)
        )
    return pix
    
def delete_white_coor(pix, coor, coor_main, scale):
    """Set color of outer part that was not included in inner part to white"""
    if len(coor) >= 3 and len(coor_main) >= 1:
        pix.set_rect(
            fitz.Rect(
                (coor[0]*scale - coor_main[0]*scale),
                (coor[1]*scale - coor_main[1]*scale),
                (coor[2]*scale - coor_main[0]*scale),
                (coor[3]*scale - coor_main[1]*scale)
            ),
            (255, 255, 255)
        )
    return pix

def get_base64_image(page, coor):
    """Get base64 image for coordinates
    
    Args:
        page (fitz.Page): PDF page
        coor (list): Coordinates [x1,y1,x2,y2]
        
    Returns:
        str: base64 encoded image
    """
    if not coor or len(coor) < 4:
        return ""
        
    try:
        # Check coordinates are within page mediabox
        coor[2] = min(float(coor[2]), page.mediabox[2])
        coor[3] = min(float(coor[3]), page.mediabox[3])

        # Create rectangle for cropping
        crop_box = fitz.Rect(coor[0], coor[1], coor[2], coor[3])
        
        # Skip if invalid rectangle
        if crop_box.is_empty or crop_box.is_infinite:
            return ""
            
        # Crop and render the image
        page.set_cropbox(crop_box)
        scale = 1.5  # zoom factor
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to base64
        img_bytes = pix.tobytes("png")
        base64_data = base64.b64encode(img_bytes).decode('utf-8')
        data = f'data:image/png;base64,{base64_data}'
        
        return data
    except Exception as e:
        print(f"Error generating base64 image: {e}")
        return ""

def format_option_response(coordinates, image_data):
    """Format option coordinates and image data in API response format
    
    Args:
        coordinates (list): [x1,y1,x2,y2] coordinates
        image_data (str): base64 image data
        
    Returns:
        list: Formatted response [x1,y1,x2,y2,base64,x1,y1,x2,y2,base64,0]
    """
    if not coordinates or len(coordinates) < 4 or not image_data:
        return []
        
    try:
        # Format as [x1,y1,x2,y2,base64,x1,y1,x2,y2,base64,0]
        return [
            float(coordinates[0]), float(coordinates[1]), 
            float(coordinates[2]), float(coordinates[3]), 
            image_data,
            float(coordinates[0]), float(coordinates[1]), 
            float(coordinates[2]), float(coordinates[3]),
            image_data,
            0
        ]
    except Exception as e:
        print(f"Error formatting option response: {e}")
        return []