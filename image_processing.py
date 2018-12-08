import numpy as np
import cv2

import arabic_reshaper

# install: pip install python-bidi
from bidi.algorithm import get_display

# install: pip install Pillow
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw




margins = {'top':1/30 , 'right':1/30, 'bottom':1/30 ,'left':1/30}
alpha_logo = 0.9
CAPTION_HEIGHT = 1/16
LOGO_SCALE = 1/64

def adjust_logo_size(host,watermark):
    (wH, wW) = watermark.shape[:2]
    (h, w) = host.shape[:2]
    host_area = w*h
    logo_area = host_area*LOGO_SCALE
    logo_aspectratio = wW/wH

    new_wH = np.int16(np.sqrt(logo_area/logo_aspectratio))
    new_wW = np.int16(logo_area//new_wH)
    
    proper_watermark = cv2.resize(watermark,(new_wW,new_wH), interpolation = cv2.INTER_AREA)
    return proper_watermark

def add_logo(host,watermark,logo_location):
    (wH, wW) = watermark.shape[:2]
    (h, w) = host.shape[:2]
    host = np.dstack([host, np.ones((h, w), dtype="uint8") * 255])

    # host_area = w*h
    # logo_area = host_area*scale
    # logo_aspectratio = wW/wH


    # new_wH = np.int16(np.sqrt(logo_area/logo_aspectratio))
    # new_wW = np.int16(logo_area//new_wH)
  
    
    # proper_watermark = cv2.resize(watermark,(new_wW,new_wH), interpolation = cv2.INTER_AREA)
    

    (wH, wW) = watermark.shape[:2]
    # construct an overlay that is the same size as the input
    # image, (using an extra dimension for the alpha transparency),
    # then add the watermark to the overlay in the bottom-right
    # corner
    overlay = np.zeros((h, w, 4), dtype="uint8")

    
    if logo_location=='bottom_right':
        bottom_line = np.int16(h*margins['bottom'])
        right_line =  np.int16(h*margins['right'])
        overlay[h - wH - bottom_line:h - bottom_line, w - wW - right_line:w - right_line] = watermark

    elif logo_location=='bottom_left':
        bottom_line = np.int16(h*margins['bottom'])
        left_line =  np.int16(h*margins['left'])
        overlay[h - wH - bottom_line:h - bottom_line, left_line:wW + left_line] = watermark
    
    elif logo_location=='top_left':
        top_line = np.int16(h*margins['top'])
        left_line =  np.int16(h*margins['left'])
        overlay[top_line:wH + top_line, left_line:wW + left_line] = watermark

    elif logo_location=='top_right':
        top_line = np.int16(h*margins['top'])
        right_line =  np.int16(h*margins['right'])
        overlay[top_line:wH + top_line,w - wW - right_line:w - right_line] = watermark

    elif logo_location=='best':
        pass
    
    elif logo_location=='random':
        pass

    mask = overlay[:,:,3]/255
    # cv2.imshow('sdf',proper_watermark[:,:,3])
    # cv2.waitKey(0)
    # cv2.destroyAllWindows() 
    print(np.unique(watermark[:,:,3]))
    output = host.copy()
    mask = np.dstack((mask,mask,mask,mask))
    output = output*(1-mask) +(1-alpha_logo)*output*mask + alpha_logo*overlay    
    
    
    return output


def add_caption(image,caption_text,logo_location,logo):
    h, w = image.shape[:2]
    logo_h, logo_w = logo.shape[:2]

    caption_height = np.int16(h*CAPTION_HEIGHT)
    print('caption_height : ',caption_height)
    bottom_line = np.int16(h*margins['bottom'])
    right_line =  np.int16(w*margins['right'])
    left_line =  np.int16(w*margins['left'])
    

    overlay = image.copy()

    if(logo_location == 'bottom_left'):
        cv2.rectangle(image,(logo_w + left_line ,h-bottom_line-caption_height),(w,h-bottom_line),(0,255,0),cv2.FILLED)
    elif (logo_location == 'bottom_right'):
        cv2.rectangle(image,(0,h-bottom_line-caption_height),(w-right_line-logo_w,h-bottom_line),(0,255,0),cv2.FILLED)
    else:
        cv2.rectangle(image,(0,h-bottom_line-caption_height),(w,h-bottom_line),(0,255,0),cv2.FILLED)

    opacity = 0.7
    cv2.addWeighted(overlay, opacity, image, 1 - opacity, 0, image)
   
    
    overlay = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    # use a good font!
    fontFile = "Fonts/XB Niloofar.ttf"

    # load the font and image
    font_size =  0.6684480157 * caption_height 
    font = ImageFont.truetype(fontFile, np.int(np.round(font_size)))
    # image = Image.open(imageFile)
    
    image = Image.fromarray(overlay,mode='RGB')
    # firts you must prepare your text (you dont need this for english text)
    reshaped_text = arabic_reshaper.reshape(caption_text)    # correct its shape

    bidi_text = get_display(reshaped_text)           # correct its direction
    
    size = font.getsize(bidi_text)
    
    # start drawing on image
    draw = ImageDraw.Draw(image)
    if(logo_location == 'bottom_left'):
        draw.text([w-size[0]-right_line ,h-bottom_line-(caption_height)] , bidi_text, (255,255,255), font=font)
    elif (logo_location == 'bottom_right'):
        draw.text([w-size[0]-right_line-logo_w ,h-bottom_line-(caption_height)] , bidi_text, (255,255,255), font=font)
    else:
        draw.text([w-size[0]-right_line ,h-bottom_line-(caption_height)] , bidi_text, (255,255,255), font=font)


    image = np.array(image,dtype='uint8')
    image= cv2.cvtColor(image,cv2.COLOR_RGB2BGR)
    return image


