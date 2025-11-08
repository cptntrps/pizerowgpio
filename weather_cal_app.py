#!/usr/bin/python3
import sys, os, time, subprocess
from datetime import datetime, timedelta
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import logging, threading
logging.basicConfig(level=logging.INFO)

import json
import sys
sys.path.append('/home/pizero2w/pizero_apps')
CONFIG = json.load(open("/home/pizero2w/pizero_apps/config.json")); LOCATION = CONFIG["weather"]["location"]; UPDATE_INTERVAL = CONFIG["weather"].get("update_interval", 300)

def get_weather():
    try:
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{LOCATION}?format=%C+%t+%h'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            data = result.stdout.strip().split()
            if len(data) >= 3:
                condition = " ".join(data[:-2])
                temp = data[-2]
                humidity = data[-1]
                return {'condition': condition, 'temp': temp, 'humidity': humidity}
    except:
        pass
    return None

def draw_weather_icon(draw, condition, x, y):
    condition_lower = condition.lower()
    
    if 'sun' in condition_lower or 'clear' in condition_lower:
        draw.ellipse([x+10, y+10, x+30, y+30], outline=0, width=2)
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            import math
            rad = math.radians(angle)
            x1 = x + 20 + 15 * math.cos(rad)
            y1 = y + 20 + 15 * math.sin(rad)
            x2 = x + 20 + 20 * math.cos(rad)
            y2 = y + 20 + 20 * math.sin(rad)
            draw.line([x1, y1, x2, y2], fill=0, width=2)
    
    elif 'cloud' in condition_lower:
        draw.ellipse([x+5, y+15, x+20, y+25], outline=0, width=2)
        draw.ellipse([x+15, y+10, x+30, y+20], outline=0, width=2)
        draw.ellipse([x+25, y+15, x+40, y+25], outline=0, width=2)
    
    elif 'rain' in condition_lower or 'drizzle' in condition_lower:
        draw.ellipse([x+5, y+10, x+20, y+20], outline=0, width=2)
        draw.ellipse([x+15, y+5, x+30, y+15], outline=0, width=2)
        draw.ellipse([x+25, y+10, x+40, y+20], outline=0, width=2)
        draw.line([x+10, y+25, x+8, y+32], fill=0, width=2)
        draw.line([x+22, y+25, x+20, y+32], fill=0, width=2)
        draw.line([x+34, y+25, x+32, y+32], fill=0, width=2)
    
    elif 'snow' in condition_lower:
        draw.line([x+20, y+10, x+20, y+30], fill=0, width=2)
        draw.line([x+10, y+20, x+30, y+20], fill=0, width=2)
        draw.line([x+13, y+13, x+27, y+27], fill=0, width=2)
        draw.line([x+27, y+13, x+13, y+27], fill=0, width=2)
    else:
        draw.text((x+15, y+10), "?", fill=0)

def draw_weather_screen():
    """Draw today's weather only (simplified for button control)"""
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_time = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 28)
    f_date = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 14)
    f_temp = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 20)
    f_small = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 10)
    
    target_date = datetime.now()
    
    # Current time
    time_str = target_date.strftime("%H:%M")
    draw.text((10, 5), time_str, font=f_time, fill=0)
    
    # Date
    date_str = target_date.strftime("%a, %b %d")
    draw.text((10, 38), date_str, font=f_date, fill=0)
    
    # Separator line
    draw.line((5, 60, 245, 60), fill=0, width=1)
    
    # Weather data
    weather = get_weather()
    if weather:
        draw_weather_icon(draw, weather['condition'], 10, 65)
        temp_text = weather['temp']
        draw.text((70, 68), temp_text, font=f_temp, fill=0)
        condition_short = weather['condition'][:15]
        draw.text((70, 95), condition_short, font=f_small, fill=0)
        draw.text((170, 75), f"Humid:", font=f_small, fill=0)
        draw.text((170, 90), weather['humidity'], font=f_small, fill=0)
    else:
        draw.text((50, 75), "Weather unavailable", font=f_small, fill=0)
        draw.text((50, 90), "Check connection", font=f_small, fill=0)
    
    # Simplified status text
    draw.text((75, 112), "Auto-refresh: 5 min", font=f_small, fill=0)
    
    return img

def run_weather_app(epd, gt_dev, gt_old, gt):
    """Weather app with button control - view-only with auto-refresh"""
    flag_t = [1]
    
    def pthread_irq():
        while flag_t[0] == 1:
            if gt.digital_read(gt.INT) == 0:
                gt_dev.Touch = 1
            else:
                gt_dev.Touch = 0
            time.sleep(0.01)
    
    t = threading.Thread(target=pthread_irq)
    t.daemon = True
    t.start()
    
    last_update = 0
    
    # Initial display
    image = draw_weather_screen()
    epd.displayPartial(epd.getbuffer(image))
    last_update = time.time()
    logging.info("Weather app started (button mode - view only)")
    
    while True:
        # Auto-refresh every 5 minutes
        if time.time() - last_update > UPDATE_INTERVAL:
            logging.info("Auto-refreshing weather")
            image = draw_weather_screen()
            epd.displayPartial(epd.getbuffer(image))
            last_update = time.time()
        
        gt.GT_Scan(gt_dev, gt_old)
        # Check for exit signal from menu
        if hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested:
            logging.info("Exit requested by menu")
            flag_t[0] = 0
            break
        
            logging.info("Exit requested by menu")
            flag_t[0] = 0
            break
            
        
        # Check for position changes
        if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
            time.sleep(0.1)
            continue
        
        # Optional: allow button click to manually refresh
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            logging.info("Manual refresh via button")
            image = draw_weather_screen()
            epd.displayPartial(epd.getbuffer(image))
            last_update = time.time()
        
        time.sleep(0.1)
