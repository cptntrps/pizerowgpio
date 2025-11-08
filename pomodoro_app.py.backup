#!/usr/bin/python3
import sys, os, time, json
from datetime import datetime
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import logging, threading

# Load Pomodoro configuration
CONFIG_FILE = "/home/pizero2w/pizero_apps/config.json"
with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)
POMODORO_CONFIG = CONFIG.get("pomodoro", {})
logging.basicConfig(level=logging.INFO)

WORK_TIME = POMODORO_CONFIG.get("work_duration", 1500)
SHORT_BREAK = POMODORO_CONFIG.get("short_break", 300)
LONG_BREAK = POMODORO_CONFIG.get("long_break", 900)

def draw_tomato_frame1():
    """Draw excited tomato with pickaxe - frame 1"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_medium = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 20)
    
    # Tomato body (circle at x=125, y=50)
    draw.ellipse([95, 30, 155, 90], outline=0, fill=255)
    draw.ellipse([97, 32, 153, 88], outline=0, fill=0, width=2)
    
    # Leaf/stem on top
    draw.polygon([(115, 25), (125, 15), (135, 25)], outline=0, fill=0)
    
    # Happy eyes
    draw.ellipse([108, 50, 118, 60], outline=0, fill=0)
    draw.ellipse([132, 50, 142, 60], outline=0, fill=0)
    
    # Wide smile
    draw.arc([105, 55, 145, 80], 0, 180, fill=0, width=2)
    
    # Sweat drops (working hard!)
    draw.ellipse([90, 35, 95, 42], outline=0, fill=0)
    draw.ellipse([85, 45, 90, 52], outline=0, fill=0)
    draw.ellipse([80, 55, 85, 62], outline=0, fill=0)
    
    # Pickaxe (right side)
    # Handle
    draw.line([(155, 45), (180, 30)], fill=0, width=3)
    # Pick head
    draw.polygon([(175, 25), (185, 20), (190, 30), (180, 35)], outline=0, fill=0)
    
    # Arms
    draw.ellipse([90, 60, 100, 70], outline=0, fill=0)  # Left arm
    draw.ellipse([150, 45, 160, 55], outline=0, fill=0)  # Right arm (holding pick)
    
    # Legs
    draw.rectangle([115, 90, 122, 105], outline=0, fill=0)
    draw.rectangle([128, 90, 135, 105], outline=0, fill=0)
    
    # "WORK" text
    draw.text((90, 105), "WORK", font=f_medium, fill=0)
    
    # Timer icon
    draw.ellipse([50, 15, 70, 35], outline=0, width=2)
    draw.text((56, 18), "L", font=f_medium, fill=0)
    
    return img

def draw_tomato_frame2():
    """Draw focused tomato with pickaxe - frame 2"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_medium = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 20)
    
    # Tomato body
    draw.ellipse([95, 30, 155, 90], outline=0, fill=255)
    draw.ellipse([97, 32, 153, 88], outline=0, fill=0, width=2)
    
    # Leaf/stem
    draw.polygon([(115, 25), (125, 15), (135, 25)], outline=0, fill=0)
    
    # Focused eyes (smaller, determined)
    draw.line([(108, 55), (118, 55)], fill=0, width=2)
    draw.line([(132, 55), (142, 55)], fill=0, width=2)
    
    # Small smile (concentrated)
    draw.arc([110, 60, 140, 75], 0, 180, fill=0, width=2)
    
    # Sweat drops
    draw.ellipse([88, 38, 93, 45], outline=0, fill=0)
    draw.ellipse([83, 50, 88, 57], outline=0, fill=0)
    
    # Pickaxe (slightly different angle)
    draw.line([(155, 50), (175, 35)], fill=0, width=3)
    draw.polygon([(170, 30), (180, 25), (185, 35), (175, 40)], outline=0, fill=0)
    
    # Arms
    draw.ellipse([92, 58, 102, 68], outline=0, fill=0)
    draw.ellipse([150, 48, 160, 58], outline=0, fill=0)
    
    # Legs
    draw.rectangle([115, 90, 122, 105], outline=0, fill=0)
    draw.rectangle([128, 90, 135, 105], outline=0, fill=0)
    
    # "WORK" text
    draw.text((90, 105), "WORK", font=f_medium, fill=0)
    
    # Timer icon
    draw.ellipse([50, 15, 70, 35], outline=0, width=2)
    draw.text((56, 18), "L", font=f_medium, fill=0)
    
    return img

def play_start_animation(epd):
    """Animate between frame 1 and frame 2 before starting timer"""
    logging.info("Playing start animation")
    
    for i in range(6):  # 3 cycles of animation
        if i % 2 == 0:
            img = draw_tomato_frame1()
        else:
            img = draw_tomato_frame2()
        
        epd.displayPartial(epd.getbuffer(img))
        time.sleep(0.4)

def draw_pomodoro(state, time_left, pomodoro_count):
    """Draw pomodoro timer screen
    Button control:
    - Click: Start/Pause toggle
    - Hold 2s: Exit (handled by menu)
    """
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_huge = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 48)
    f_medium = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 16)
    f_small = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 12)
    
    mins, secs = divmod(time_left, 60)
    time_text = f"{mins:02}:{secs:02}"
    
    bbox = draw.textbbox((0, 0), time_text, font=f_huge)
    w = bbox[2] - bbox[0]
    draw.text(((250 - w) // 2, 35), time_text, font=f_huge, fill=0)
    
    state_text = state
    if state == "WORK":
        state_text = f"WORK #{pomodoro_count}"
    elif state == "BREAK":
        state_text = "BREAK"
    
    bbox = draw.textbbox((0, 0), state_text, font=f_medium)
    w = bbox[2] - bbox[0]
    draw.text(((250 - w) // 2, 10), state_text, font=f_medium, fill=0)
    
    # Simplified instructions at bottom
    draw.line([(0, 100), (250, 100)], fill=0, width=1)
    draw.text((70, 105), "Click: Start/Pause", font=f_small, fill=0)
    
    return img

def run_pomodoro_app(epd, gt_dev, gt_old, gt):
    """Pomodoro timer with button controls and startup animation"""
    
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
    
    state = "READY"
    time_left = WORK_TIME
    pomodoro_count = 0
    last_update = time.time()
    prev_state = "READY"
    
    image = draw_pomodoro(state, time_left, pomodoro_count)
    epd.displayPartial(epd.getbuffer(image))
    
    logging.info("Pomodoro app started (button mode)")
    
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
            
        
        current_time = time.time()
        
        # Timer countdown logic
        if state == "WORK" or state == "BREAK":
            if current_time - last_update >= 1.0:
                time_left -= 1
                last_update = current_time
                
                if time_left <= 0:
                    # Auto-transition when timer ends
                    if state == "WORK":
                        pomodoro_count += 1
                        state = "BREAK"
                        if pomodoro_count % 4 == 0:
                            time_left = LONG_BREAK
                        else:
                            time_left = SHORT_BREAK
                    else:
                        # Break ended, return to READY
                        state = "READY"
                        time_left = WORK_TIME
                    
                    # Full refresh for state change
                    epd.init(epd.FULL_UPDATE)
                    epd.Clear(0xFF)
                    image = draw_pomodoro(state, time_left, pomodoro_count)
                    epd.displayPartBaseImage(epd.getbuffer(image))
                    epd.init(epd.PART_UPDATE)
                else:
                    # Normal timer update
                    image = draw_pomodoro(state, time_left, pomodoro_count)
                    epd.displayPartial(epd.getbuffer(image))
        
        # Check for position changes
        if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
            continue
        
        # Handle button clicks
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            
            # Any button click toggles Start/Pause
            if state == "READY":
                # Play animation when starting first time
                play_start_animation(epd)
                
                # Full refresh before starting timer
                epd.init(epd.FULL_UPDATE)
                epd.Clear(0xFF)
                
                state = "WORK"
                pomodoro_count = 1
                time_left = WORK_TIME
                last_update = current_time
                
                image = draw_pomodoro(state, time_left, pomodoro_count)
                epd.displayPartBaseImage(epd.getbuffer(image))
                epd.init(epd.PART_UPDATE)
                
                logging.info("Started work session with animation")
            
            elif state == "PAUSED":
                # Resume from pause
                state = prev_state
                last_update = current_time
                logging.info("Resumed from pause")
                image = draw_pomodoro(state, time_left, pomodoro_count)
                epd.displayPartial(epd.getbuffer(image))
            
            elif state in ["WORK", "BREAK"]:
                # Pause active timer
                prev_state = state
                state = "PAUSED"
                logging.info(f"Paused {prev_state}")
                image = draw_pomodoro(state, time_left, pomodoro_count)
                epd.displayPartial(epd.getbuffer(image))
    
    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0
