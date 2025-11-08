#\!/usr/bin/python3
import sys, os, time, subprocess
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import logging, threading
logging.basicConfig(level=logging.INFO)

def draw_reboot_confirm(epd, gt_dev, gt_old, gt):
    """Show reboot confirmation screen"""
    
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
    
    # Show confirmation screen
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_title = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 16)
    f_button = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 12)
    
    draw.text((50, 20), "Reboot System?", font=f_title, fill=0)
    
    # Left button: Cancel (Y > 180 = physical LEFT per API contract)
    draw.rectangle([10, 70, 110, 105], outline=0, width=2)
    draw.text((35, 82), "Cancel", font=f_button, fill=0)
    
    # Right button: Reboot (Y < 70 = physical RIGHT per API contract)
    draw.rectangle([140, 70, 240, 105], outline=0, width=2)
    draw.text((165, 82), "Reboot", font=f_button, fill=0)
    
    epd.displayPartial(epd.getbuffer(img))
    
    last_touch_time = 0
    
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
            x, y = gt_dev.X[0], gt_dev.Y[0]
            
            last_touch_time = time.time()
            
            logging.info(f"Reboot screen touch: X={x} Y={y}")
            
            # API Contract: Y > 180 = Physical LEFT (Cancel)
            if y > 180:
                logging.info("Reboot cancelled")
                flag_t[0] = 0
                break
            
            # API Contract: Y < 70 = Physical RIGHT (Reboot)
            elif y < 70:
                logging.info("Rebooting system...")
                # Show "Rebooting..." message
                img = Image.new('1', (250, 122), 255)
                draw = ImageDraw.Draw(img)
                draw.text((60, 50), "Rebooting...", font=f_title, fill=0)
                epd.displayPartial(epd.getbuffer(img))
                time.sleep(1)
                
                # Execute reboot
                subprocess.run(['sudo', 'reboot'])
                flag_t[0] = 0
                break
        
    
    # Clean up
    gt_dev.TouchpointFlag = 0
    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0
