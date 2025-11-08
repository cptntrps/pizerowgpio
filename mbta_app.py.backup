#!/usr/bin/python3
"""
MBTA App for E-Paper Display
Mode 1: Commute Dashboard (home/work stations with next trains)
Mode 2: System Status Monitor (all lines status)
Touch right side = cycle modes, Touch left side = exit
"""
import sys, os, time, json, subprocess, threading
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
import logging

# Load configuration
CONFIG_FILE = "/home/pizero2w/pizero_apps/config.json"
with open(CONFIG_FILE, "r") as f:
    CONFIG = json.load(f)
MBTA_CONFIG = CONFIG.get("mbta", {})
logging.basicConfig(level=logging.INFO)

MBTA_API = "https://api-v3.mbta.com"

def fetch_json(url):
    """Fetch JSON from URL using curl"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-m', '10', url],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
    except Exception as e:
        logging.error(f"Fetch error: {e}")
    return None

def get_predictions(stop_id):
    """Get next train predictions for a stop"""
    url = f"{MBTA_API}/predictions?filter[stop]={stop_id}&sort=arrival_time&include=route,trip"
    data = fetch_json(url)
    
    predictions = []
    if data and 'data' in data:
        for pred in data['data'][:5]:
            attrs = pred.get('attributes', {})
            arrival = attrs.get('arrival_time') or attrs.get('departure_time')
            
            if arrival:
                try:
                    arrival_dt = datetime.fromisoformat(arrival.replace('Z', '+00:00'))
                    now = datetime.now(arrival_dt.tzinfo)
                    minutes = int((arrival_dt - now).total_seconds() / 60)
                    
                    route_id = pred.get('relationships', {}).get('route', {}).get('data', {}).get('id', '')
                    direction = attrs.get('direction_id', 0)
                    
                    predictions.append({
                        'route': route_id,
                        'minutes': minutes if minutes > 0 else 0,
                        'direction': direction
                    })
                except Exception as e:
                    logging.error(f"Parse error: {e}")
    
    return predictions

def get_system_alerts():
    """Get alerts for all subway lines"""
    url = f"{MBTA_API}/alerts?filter[route_type]=0,1"
    data = fetch_json(url)
    
    alerts = {}
    if data and 'data' in data:
        for alert in data['data']:
            attrs = alert.get('attributes', {})
            effect = attrs.get('effect', '')
            
            if effect in ['SUSPENSION', 'DELAY', 'DETOUR']:
                informed = alert.get('relationships', {}).get('informed_entity', {}).get('data', [])
                for entity in informed:
                    route_id = entity.get('route')
                    if route_id in ['Red', 'Orange', 'Blue', 'Green-B', 'Green-C', 'Green-D', 'Green-E']:
                        if route_id not in alerts:
                            alerts[route_id] = effect
    
    return alerts

def draw_commute_dashboard(home_station, work_station, home_name, work_name):
    """Draw commute dashboard with next trains"""
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_title = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 16)
    f_normal = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 12)
    f_small = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 10)
    
    draw.text((5, 2), "MBTA Commute", font=f_title, fill=0)
    draw.line([(0, 22), (250, 22)], fill=0, width=1)
    
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        active_station = home_station
        active_name = home_name
        label = "Morning Commute"
    elif 12 <= hour < 20:
        active_station = work_station
        active_name = work_name
        label = "Evening Commute"
    else:
        active_station = home_station
        active_name = home_name
        label = "Late Night"
    
    draw.text((5, 28), f"{label} - {active_name}", font=f_normal, fill=0)
    
    predictions = get_predictions(active_station)
    
    y = 48
    if predictions:
        for pred in predictions[:4]:
            route = pred['route']
            minutes = pred['minutes']
            
            if minutes == 0:
                time_str = "Arriving"
            elif minutes == 1:
                time_str = "1 min"
            else:
                time_str = f"{minutes} min"
            
            route_display = route.replace('-', ' ')
            draw.text((10, y), f"{route_display}: {time_str}", font=f_normal, fill=0)
            y += 16
    else:
        draw.text((10, 55), "No upcoming trains", font=f_normal, fill=0)
    
    draw.text((5, 110), "L=Exit  R=Status", font=f_small, fill=0)
    
    return img

def draw_system_status():
    """Draw system-wide status for all lines"""
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_title = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Bold.ttf'), 16)
    f_normal = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 11)
    f_small = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 10)
    
    draw.text((5, 2), "MBTA System Status", font=f_title, fill=0)
    draw.line([(0, 22), (250, 22)], fill=0, width=1)
    
    alerts = get_system_alerts()
    
    lines = [
        ('Red', 'Red Line'),
        ('Orange', 'Orange Line'),
        ('Blue', 'Blue Line'),
        ('Green-B', 'Green B'),
        ('Green-C', 'Green C'),
        ('Green-D', 'Green D')
    ]
    
    y = 28
    for line_id, line_name in lines:
        if line_id in alerts:
            effect = alerts[line_id]
            if effect == 'SUSPENSION':
                status = "⊗ SUSPENDED"
            elif effect == 'DELAY':
                status = "⚠ DELAYS"
            else:
                status = "⚠ ALERT"
        else:
            status = "✓ Normal"
        
        draw.text((10, y), f"{line_name}:", font=f_normal, fill=0)
        draw.text((125, y), status, font=f_normal, fill=0)
        y += 15
    
    draw.text((5, 110), "L=Exit  R=Commute", font=f_small, fill=0)
    
    return img

def run_mbta_app(epd, gt_dev, gt_old, gt):
    """MBTA app with two modes"""
    
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
    # Load MBTA configuration from config.json
    HOME_STATION = MBTA_CONFIG.get("home_station_id", "place-davis")
    HOME_NAME = MBTA_CONFIG.get("home_station_name", "Davis Square")
    WORK_STATION = MBTA_CONFIG.get("work_station_id", "place-pktrm")
    WORK_NAME = MBTA_CONFIG.get("work_station_name", "Park Street")
    UPDATE_INTERVAL = MBTA_CONFIG.get("update_interval", 30)
    
    mode = 0
    last_update = 0
    
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    f = ImageFont.truetype(os.path.join(fontdir, 'Roboto-Regular.ttf'), 12)
    draw.text((40, 50), "Loading MBTA data...", font=f, fill=0)
    epd.displayPartial(epd.getbuffer(img))
    
    time.sleep(0.5)
    gt_dev.TouchpointFlag = 0
    
    logging.info("MBTA app started")
    
    while True:
        time.sleep(0.01)
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
        
        if current_time - last_update >= UPDATE_INTERVAL or last_update == 0:
            logging.info(f"Updating display - mode {mode}")
            
            if mode == 0:
                image = draw_commute_dashboard(HOME_STATION, WORK_STATION, HOME_NAME, WORK_NAME)
            else:
                image = draw_system_status()
            
            epd.displayPartial(epd.getbuffer(image))
            last_update = current_time
        
        if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
            continue
        
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            # Single click: cycle between Commute (0) and Status (1) modes
            mode = 1 - mode
            logging.info(f"Button click - switched to mode {mode} ({'Status' if mode else 'Commute'})")
            last_update = 0  # Force immediate refresh
    
    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0
