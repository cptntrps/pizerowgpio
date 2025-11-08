#\!/usr/bin/python3
import sys, os, time
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import logging, threading
import json
logging.basicConfig(level=logging.INFO)

def draw_forbidden_message(epd, gt_dev, gt_old, gt):
    """Show the forbidden message. Returns when user touches."""
    
    flag_t = [1]
    
    def pthread_irq():
        while flag_t[0] == 1:
            if gt.digital_read(gt.INT) == 0:
                gt_dev.Touch = 1
            else:
                gt_dev.Touch = 0
    
    t = threading.Thread(target=pthread_irq)
    t.daemon = True
    t.start()
    
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_big = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 16)
    f_small = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 11)
    
    # Message
    msg = json.load(open("/home/pizero2w/pizero_apps/config.json"))["forbidden"]["message_line1"]
    msg2 = json.load(open("/home/pizero2w/pizero_apps/config.json"))["forbidden"]["message_line2"]
    
    # Center the text
    bbox1 = draw.textbbox((0, 0), msg, font=f_big)
    w1 = bbox1[2] - bbox1[0]
    bbox2 = draw.textbbox((0, 0), msg2, font=f_big)
    w2 = bbox2[2] - bbox2[0]
    
    draw.text(((250 - w1) // 2, 35), msg, font=f_big, fill=0)
    draw.text(((250 - w2) // 2, 60), msg2, font=f_big, fill=0)
    
    draw.text((5, 110), "Touch to go back", font=f_small, fill=0)
    
    epd.displayPartial(epd.getbuffer(img))
    
    logging.info("Showing forbidden message")
    
    while True:
        gt.GT_Scan(gt_dev, gt_old)
        # Check for exit signal from menu
        if hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested:
            logging.info("Exit requested by menu")
            flag_t[0] = 0
            break
        
            logging.info("Exit requested by menu")
            flag_t[0] = 0
            break
            
        if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
            continue
        
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            logging.info("Touch detected - exiting")
            flag_t[0] = 0
            break
        
