#!/usr/bin/python3
"""
Disney Magic Kingdom Wait Times for E-Paper Display (OPTIMIZED)
Shows current ride wait times with themed backgrounds
Optimized for e-paper refresh limitations
"""
import sys, os, time, json, subprocess, random, threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
imagedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'disney_images')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
import logging

# Load Disney configuration
CONFIG_FILE = "/home/pizero2w/pizero_apps/config.json"
with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)
DISNEY_CONFIG = CONFIG.get("disney", {})
logging.basicConfig(level=logging.INFO)

# Cache for background images (load once, reuse)
BACKGROUND_CACHE = {}

def fetch_wait_times():
    """Fetch Disney Magic Kingdom wait times from queue-times.com"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-m', '10', 'https://queue-times.com/parks/6/queue_times.json'],
            capture_output=True, text=True, timeout=15
        )
        
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            rides = []
            for land in data['lands']:
                land_name = land['name']
                for ride in land['rides']:
                    ride_info = {
                        'name': ride['name'],
                        'wait_time': ride.get('wait_time'),
                        'is_open': ride['is_open'],
                        'land': land_name
                    }
                    rides.append(ride_info)
            return rides
    except Exception as e:
        logging.error(f"Failed to fetch wait times: {e}")
    
    return []

def load_land_background(land_name):
    """Load and convert land background image to 1-bit (WITH CACHING)"""
    # Check cache first
    if land_name in BACKGROUND_CACHE:
        return BACKGROUND_CACHE[land_name]
    
    # Map land names to image files
    land_map = {
        'Adventureland': 'Adventureland.png',
        'Fantasyland': 'Fantasyland.png',
        'Tomorrowland': 'Tomorrowland.png',
        'Frontierland': 'Frontierland.png',
        'Main Street U.S.A.': 'Main Street U.S.A..png',
        'Liberty Square': 'Liberty Square.png'
    }
    
    try:
        image_path = os.path.join(imagedir, land_map.get(land_name, 'Adventureland.png'))
        if os.path.exists(image_path):
            img = Image.open(image_path).convert('RGBA')
            # Resize to screen
            img = img.resize((250, 122), Image.Resampling.LANCZOS)
            
            # Convert to 1-bit
            bw_img = Image.new('1', (250, 122), 255)
            pixels = img.load()
            bw_pixels = bw_img.load()
            
            for y in range(122):
                for x in range(250):
                    r, g, b, a = pixels[x, y]
                    if a < 128:
                        bw_pixels[x, y] = 255
                    else:
                        brightness = (r + g + b) / 3
                        bw_pixels[x, y] = 255 if brightness > 140 else 0
            
            # Cache the result
            BACKGROUND_CACHE[land_name] = bw_img
            logging.info(f"Cached background for {land_name}")
            return bw_img
    except Exception as e:
        logging.error(f"Failed to load background for {land_name}: {e}")
    
    # Return blank image if loading fails
    blank = Image.new('1', (250, 122), 255)
    BACKGROUND_CACHE[land_name] = blank
    return blank

def draw_ride_info(ride, scroll_offset=0):
    """Draw ride wait time with themed background (NO SCROLLING - fixed text)"""
    # Load background for the land (from cache)
    img = load_land_background(ride['land']).copy()
    draw = ImageDraw.Draw(img)
    
    # Draw semi-transparent overlay for text readability
    draw.rectangle([0, 40, 250, 82], fill=255, outline=0, width=2)
    
    # Fonts
    f_name = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 14)
    f_time = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 20)
    f_small = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 10)
    
    # Ride name - truncate if too long (NO SCROLLING)
    name = ride['name']
    bbox = draw.textbbox((0, 0), name, font=f_name)
    text_width = bbox[2] - bbox[0]
    
    # Fixed text position (no scrolling for e-ink stability)
    if text_width > 230:
        # Truncate with ellipsis
        while text_width > 230 and len(name) > 5:
            name = name[:-1]
            bbox = draw.textbbox((0, 0), name + '...', font=f_name)
            text_width = bbox[2] - bbox[0]
        name = name + '...'
        # Left align for long names
        draw.text((10, 45), name, font=f_name, fill=0)
    else:
        # Center text if it fits (fixed integer position)
        x_pos = int((250 - text_width) / 2)
        draw.text((x_pos, 45), name, font=f_name, fill=0)
    
    # Wait time or status
    if ride['is_open']:
        wait_text = f"{ride['wait_time']} min"
    else:
        wait_text = "CLOSED"
    
    bbox = draw.textbbox((0, 0), wait_text, font=f_time)
    w = bbox[2] - bbox[0]
    draw.text(((250 - w) // 2, 62), wait_text, font=f_time, fill=0)
    
    # Land name at bottom
    draw.text((5, 5), ride['land'], font=f_small, fill=0)
    draw.text((180, 110), "Touch=Exit", font=f_small, fill=0)
    
    return img

def run_disney_app(epd, gt_dev, gt_old, gt):
    """Disney wait times app (OPTIMIZED FOR E-PAPER)"""
    
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
    
    # Clear any pending touch events from menu
    gt_dev.TouchpointFlag = 0
    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0
    
    logging.info("Disney app started - fetching wait times...")
    
    # Show loading screen
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    f = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 14)
    draw.text((30, 50), "Loading Disney wait times...", font=f, fill=0)
    epd.displayPartial(epd.getbuffer(img))
    
    # Fetch wait times
    rides = fetch_wait_times()
    
    if not rides:
        logging.error("No wait times fetched")
        img = Image.new('1', (250, 122), 255)
        draw = ImageDraw.Draw(img)
        draw.text((20, 40), "Unable to fetch wait times", font=f, fill=0)
        draw.text((60, 60), "Check internet connection", font=f, fill=0)
        epd.displayPartial(epd.getbuffer(img))
        time.sleep(3)
        flag_t[0] = 0
        return
    
    logging.info(f"Fetched {len(rides)} rides")
    random.shuffle(rides)
    
    # Pre-load all backgrounds into cache
    logging.info("Pre-loading backgrounds...")
    unique_lands = set(ride['land'] for ride in rides)
    for land in unique_lands:
        load_land_background(land)
    logging.info("Backgrounds cached")
    UPDATE_INTERVAL = DISNEY_CONFIG.get("update_interval", 10)  # seconds per ride
    # Display each ride with OPTIMIZED scrolling
    ride_index = 0
    last_update = time.time()
    last_scroll = time.time()
    scroll_offset = 0
    UPDATE_INTERVAL = 10  # seconds per ride
    SCROLL_INTERVAL = 0.5  # ✅ SLOWER for e-paper (500ms instead of 150ms)
    SCROLL_STEP = 3  # ✅ Move more pixels per update (smoother perceived motion)
    
    # Check if current ride needs scrolling
    current_ride = rides[ride_index]
    f_name = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 14)
    dummy_img = Image.new('1', (1, 1), 255)
    bbox = ImageDraw.Draw(dummy_img).textbbox((0, 0), current_ride['name'], font=f_name)
    needs_scroll = (bbox[2] - bbox[0]) > 230
    
    # Initial display
    image = draw_ride_info(current_ride, scroll_offset)
    epd.displayPartial(epd.getbuffer(image))
    
    # Clear touch state again after initial display
    time.sleep(0.5)  # Give time for display to settle
    gt_dev.TouchpointFlag = 0
    
    while True:
        gt.GT_Scan(gt_dev, gt_old)
        # Check for exit signal from menu
        if hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested:
            logging.info("Exit requested by menu")
            flag_t[0] = 0
            break
        
            
        
        current_time = time.time()
        
        
        # Update to next ride
        if current_time - last_update >= UPDATE_INTERVAL:
            ride_index = (ride_index + 1) % len(rides)
            scroll_offset = 0  # Reset scroll for new ride
            current_ride = rides[ride_index]
            
            # Check if new ride needs scrolling
            bbox = ImageDraw.Draw(dummy_img).textbbox((0, 0), current_ride['name'], font=f_name)
            needs_scroll = (bbox[2] - bbox[0]) > 230
            
            # Re-fetch every 20 rides (about 3.5 minutes)
            if ride_index % 20 == 0:
                logging.info("Re-fetching wait times...")
                new_rides = fetch_wait_times()
                if new_rides:
                    rides = new_rides
                    random.shuffle(rides)
                    # Clear cache for new data
                    BACKGROUND_CACHE.clear()
                    # Re-cache backgrounds
                    unique_lands = set(ride['land'] for ride in rides)
                    for land in unique_lands:
                        load_land_background(land)
            
            image = draw_ride_info(current_ride, scroll_offset)
            epd.displayPartial(epd.getbuffer(image))
            last_update = current_time
        
        # Touch to exit
        if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
            time.sleep(0.01)
            continue
        
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            logging.info("Exiting Disney app")
            flag_t[0] = 0
            break
    
    # Clear cache on exit
    BACKGROUND_CACHE.clear()
    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0
