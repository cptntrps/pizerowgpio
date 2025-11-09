#\!/usr/bin/python3
import sys, os, time, json, subprocess, math, random
from datetime import datetime
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

from TP_lib import gt1151, epd2in13_V3
from PIL import Image, ImageDraw, ImageFont
import logging, threading

try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/home/pizero2w/pizero_apps/flights_app.log'),
            logging.StreamHandler()
        ]
    )
except:
    logging.basicConfig(level=logging.INFO)

CONFIG = json.load(open("/home/pizero2w/pizero_apps/config.json"))
LAT = CONFIG["flights"]["latitude"]
LON = CONFIG["flights"]["longitude"]
RADIUS_KM = CONFIG["flights"]["radius_km"]

CACHE_FILE = "/tmp/flights_cache.json"

# Calculate bounds box from lat/lon and radius
lat_offset = RADIUS_KM / 111.0
lon_offset = RADIUS_KM / (111.0 * abs(math.cos(math.radians(LAT))))

LAMIN = LAT - lat_offset
LAMAX = LAT + lat_offset  
LOMIN = LON - lon_offset
LOMAX = LON + lon_offset

# FR24 bounds format: north,south,EAST,WEST (not west,east!)
BOUNDS_BOX = f"{LAMAX},{LAMIN},{LOMIN},{LOMAX}"

FLIGHT_SEARCH_URL = f"https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds={BOUNDS_BOX}&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=0&maxage=14400&gliders=0&stats=0&ems=1"

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2 in degrees"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    x = math.sin(dlon_rad) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

def get_flight_search():
    """Search for closest commercial flight in area"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", "10", FLIGHT_SEARCH_URL],
            capture_output=True, text=True, timeout=12
        )
        
        if result.returncode != 0:
            return None, None, None
        
        data = json.loads(result.stdout)
        
        commercial_flights = []
        
        for flight_id, flight_info in data.items():
            if flight_id not in ["version", "full_count"]:
                if len(flight_info) > 13:
                    flight_lat = flight_info[1]
                    flight_lon = flight_info[2]
                    callsign = flight_info[13]
                    
                    if not callsign or callsign.strip() == "":
                        continue
                    
                    distance = haversine_distance(LAT, LON, flight_lat, flight_lon)
                    
                    if distance <= RADIUS_KM:
                        bearing = calculate_bearing(LAT, LON, flight_lat, flight_lon)
                        commercial_flights.append({
                            "id": flight_id,
                            "distance": distance,
                            "bearing": bearing,
                            "callsign": callsign
                        })
        
        if not commercial_flights:
            logging.info("No commercial flights within radius")
            return None, None, None
        
        commercial_flights.sort(key=lambda x: x["distance"])
        
        chosen = commercial_flights[0]
        logging.info(f"Found flight {chosen['callsign']} (ID: {chosen['id']}) at {chosen['distance']:.1f}km, bearing {chosen['bearing']:.0f}°")
        return chosen["id"], chosen["distance"], chosen["bearing"]
        
    except Exception as e:
        logging.warning(f"Search error: {e}")
        return None, None, None

def get_flight_details(flight_id):
    """Get detailed flight info from FR24"""
    try:
        url = f"https://data-live.flightradar24.com/clickhandler/?flight={flight_id}"
        
        result = subprocess.run(
            ["curl", "-s", "-m", "10", url],
            capture_output=True, text=True, timeout=12
        )
        
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        identification = data.get("identification", {})
        flight_number = identification.get("number", {})
        if flight_number:
            flight_number = flight_number.get("default", "")
        else:
            flight_number = ""
        
        callsign = identification.get("callsign", "")
        if callsign == "Blocked":
            callsign = ""
        
        aircraft = data.get("aircraft", {})
        aircraft_model = aircraft.get("model", {})
        aircraft_code = aircraft_model.get("code", "?") if aircraft_model else "?"
        
        airline = data.get("airline", {})
        airline_name = airline.get("name", "") if airline else ""
        
        airport = data.get("airport", {})
        origin = airport.get("origin") if airport else None
        destination = airport.get("destination") if airport else None
        
        origin_code = "?"
        dest_code = "?"
        origin_name = ""
        dest_name = ""
        
        if origin:
            origin_iata = origin.get("code", {})
            origin_code = origin_iata.get("iata", "?") if origin_iata else "?"
            origin_name = origin.get("name", "").replace(" Airport", "")
        
        if destination:
            dest_iata = destination.get("code", {})
            dest_code = dest_iata.get("iata", "?") if dest_iata else "?"
            dest_name = destination.get("name", "").replace(" Airport", "")
        
        trail = data.get("trail", [])
        altitude = 0
        speed = 0
        if trail and len(trail) > 0:
            altitude = int(trail[0].get("alt", 0))
            speed = int(trail[0].get("spd", 0))
        
        flight_data = {
            "callsign": flight_number or callsign or flight_id[-4:].upper(),
            "airline": airline_name,
            "origin": origin_code,
            "destination": dest_code,
            "origin_name": origin_name,
            "dest_name": dest_name,
            "aircraft": aircraft_code,
            "altitude": altitude,
            "speed": speed,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        
        logging.info(f"Flight: {flight_data['callsign']} from {origin_code} to {dest_code} on {aircraft_code}")
        
        return flight_data
        
    except Exception as e:
        logging.warning(f"Details error: {e}")
        return None

def get_current_flight():
    """Get current overhead flight with full details"""
    flight_id, distance, bearing = get_flight_search()
    
    if not flight_id:
        logging.info("No flights found")
        return None
    
    flight_data = get_flight_details(flight_id)
    
    if flight_data:
        flight_data["distance"] = distance
        flight_data["bearing"] = bearing
        
        with open(CACHE_FILE, "w") as f:
            json.dump(flight_data, f)
    
    return flight_data

AVIATION_QUOTES = [
    ("Flying is learning how to\nthrow yourself at the\nground and miss.", "Douglas Adams"),
    ("There are old pilots and\nbold pilots, but no old,\nbold pilots.", "Aviation Adage"),
    ("Every takeoff is optional.\nEvery landing is mandatory.", "Aviation Adage"),
    ("A good landing is one\nfrom which you can walk\naway.", "Aviation Adage"),
    ("The probability of\nsurvival is inversely\nproportional to the\nangle of arrival.", "Neil Armstrong"),
    ("Aviate, Navigate,\nCommunicate.", "Pilot's Mantra"),
    ("If you push the stick\nforward, the houses\nget bigger.", "Aviation Adage"),
    ("The propeller is just a\nbig fan to keep the\npilot cool.", "Aviation Humor"),
    ("Helicopters don't fly.\nThey beat the air into\nsubmission.", "Aviation Humor"),
    ("Gravity is not just a\ngood idea. It's the law.", "Aviation Adage"),
    ("Learn from the mistakes\nof others. You won't\nlive long enough.", "Aviation Adage"),
    ("A superior pilot uses\nsuperior judgment to\navoid situations.", "Frank Borman"),
    ("The only time you have\ntoo much fuel is when\nyou're on fire.", "Aviation Adage"),
]

def draw_quote(quote_text, author):
    """Draw aviation quote full screen"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_quote = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 16)
    f_author = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 14)
    
    draw.text((10, 15), quote_text, font=f_quote, fill=0)
    draw.text((10, 100), f"— {author}", font=f_author, fill=0)
    
    return img

def draw_compass_rose(draw, cx, cy, radius, bearing):
    """Draw compass rose rotated so 310° points up"""
    user_heading = 310
    rotation_offset = user_heading
    
    # Outer ellipse
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], outline=0, width=2)
    
    # Define fonts
    f_compass_cardinal = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 11)
    f_compass_inter = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 9)
    
    # Add cardinal directions (N, E, S, W)
    cardinal_directions = [
        (0, "N"), (90, "E"), (180, "S"), (270, "W")
    ]
    
    for angle, label in cardinal_directions:
        rotated_angle = angle - rotation_offset
        angle_rad = math.radians(rotated_angle - 90)
        
        # Line for the rose
        x_inner = cx + int((radius - 10) * math.cos(angle_rad))
        y_inner = cy + int((radius - 10) * math.sin(angle_rad))
        x_outer = cx + int(radius * math.cos(angle_rad))
        y_outer = cy + int(radius * math.sin(angle_rad))
        draw.line([(x_inner, y_inner), (x_outer, y_outer)], fill=0, width=2)
        
        # Text label (centered better)
        x_text = cx + int((radius - 18) * math.cos(angle_rad))
        y_text = cy + int((radius - 18) * math.sin(angle_rad))
        draw.text((x_text-3, y_text-5), label, font=f_compass_cardinal, fill=0)

    # Add intercardinal directions (NW, NE, SW, SE)
    inter_directions = [
        (45, "NE"), (135, "SE"), (225, "SW"), (315, "NW")
    ]
    
    for angle, label in inter_directions:
        rotated_angle = angle - rotation_offset
        angle_rad = math.radians(rotated_angle - 90)
        
        # Shorter line for the rose
        x_inner = cx + int((radius - 6) * math.cos(angle_rad))
        y_inner = cy + int((radius - 6) * math.sin(angle_rad))
        x_outer = cx + int(radius * math.cos(angle_rad))
        y_outer = cy + int(radius * math.sin(angle_rad))
        draw.line([(x_inner, y_inner), (x_outer, y_outer)], fill=0, width=1)
        
        # Text label (centered better)
        x_text = cx + int((radius - 16) * math.cos(angle_rad))
        y_text = cy + int((radius - 16) * math.sin(angle_rad))
        draw.text((x_text-5, y_text-4), label, font=f_compass_inter, fill=0)

    # Inner circle
    inner_radius = 8
    draw.ellipse([cx-inner_radius, cy-inner_radius, cx+inner_radius, cy+inner_radius], outline=0, fill=0)

    # Bearing Arrow
    rotated_bearing = bearing - rotation_offset
    bearing_rad = math.radians(rotated_bearing - 90)
    arrow_len = radius - 12
    ax = cx + int(arrow_len * math.cos(bearing_rad))
    ay = cy + int(arrow_len * math.sin(bearing_rad))
    
    # Arrow shaft from inner circle edge
    shaft_start_x = cx + int(inner_radius * math.cos(bearing_rad))
    shaft_start_y = cy + int(inner_radius * math.sin(bearing_rad))
    draw.line([(shaft_start_x, shaft_start_y), (ax, ay)], fill=0, width=2)
    
    # Arrowhead
    tip_angle1 = bearing_rad + math.radians(150)
    tip_angle2 = bearing_rad - math.radians(150)
    tx1 = ax + int(7 * math.cos(tip_angle1))
    ty1 = ay + int(7 * math.sin(tip_angle1))
    tx2 = ax + int(7 * math.cos(tip_angle2))
    ty2 = ay + int(7 * math.sin(tip_angle2))
    
    draw.polygon([(ax, ay), (tx1, ty1), (tx2, ty2)], outline=0, fill=0)

def draw_flight_portal(flight_data, animation_frame=0):
    """Split screen: info left, compass right"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)
    
    f_large = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 24)
    f_medium = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 14)
    f_medium_bold = ImageFont.truetype(os.path.join(fontdir, "Roboto-Bold.ttf"), 14)
    f_small = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 10)
    
    if not flight_data:
        draw.text((30, 50), "No flights overhead", font=f_medium, fill=0)
        draw.text((170, 110), "Touch=Exit", font=f_small, fill=0)
        return img
    
    # --- UI Layout ---
    draw.line([(125, 0), (125, 122)], fill=0, width=1)
    
    # --- Right Panel (Compass) ---
    draw_compass_rose(draw, 187, 61, 45, flight_data.get("bearing", 0))
    draw.text((135, 5), f"Live {flight_data['timestamp']}", font=f_small, fill=0)
    draw.text((135, 110), "Touch=Exit", font=f_small, fill=0)
    
    # --- Left Panel (Info) ---
    draw.text((5, 5), flight_data["callsign"], font=f_large, fill=0)
    
    # --- NEW: 2-Frame Animation Cycle ---
    cycle = animation_frame % 2
    
    if cycle == 0:
        # Frame 0: Flight Info
        route = f"{flight_data['origin']}->{flight_data['destination']}"
        draw.text((5, 35), route, font=f_medium, fill=0)
        
        airline = flight_data.get("airline", "")
        if airline and len(airline) > 12:
            airline = airline[:12]
        draw.text((5, 55), airline or flight_data['aircraft'], font=f_medium, fill=0)
    
    else:
        # Frame 1: Flight Data
        if flight_data["altitude"] > 0:
            draw.text((5, 35), f"Alt: {flight_data['altitude']:,} ft", font=f_medium, fill=0)
        else:
            draw.text((5, 35), flight_data['aircraft'], font=f_medium, fill=0)
            
        if flight_data["speed"] > 0:
            draw.text((5, 55), f"Speed: {flight_data['speed']} kts", font=f_medium, fill=0)
        else:
            draw.text((5, 55), "On Ground", font=f_medium, fill=0)

    # --- NEW: Moved Distance & Bearing (Bold for prominence) ---
    draw.text((5, 85), f"Dist: {flight_data.get('distance', 0):.1f} km", font=f_medium_bold, fill=0)
    draw.text((5, 105), f"Bear: {flight_data.get('bearing', 0):.0f}°", font=f_medium_bold, fill=0)
    
    return img

def run_flights_app(epd, gt_dev, gt_old, gt):
    """Flights display using proper FR24 API"""
    
    try:
        _run_flights_app_impl(epd, gt_dev, gt_old, gt)
    except Exception as e:
        logging.error(f"Flights app crashed: {e}", exc_info=True)
        img = Image.new("1", (250, 122), 255)
        draw = ImageDraw.Draw(img)
        f = ImageFont.truetype(os.path.join(fontdir, "Roboto-Regular.ttf"), 12)
        draw.text((10, 50), f"Error: {str(e)[:30]}", font=f, fill=0)
        epd.displayPartial(epd.getbuffer(img))
        time.sleep(5)

def _run_flights_app_impl(epd, gt_dev, gt_old, gt):
    """Internal implementation"""
    
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
    
    last_update = time.time()
    last_animation_cycle = time.time()
    last_quote_time = time.time()
    animation_frame = 0
    quote_index = 0
    
    UPDATE_INTERVAL = 30
    ANIMATION_CYCLE_INTERVAL = 10
    QUOTE_INTERVAL = 300
    
    random.seed(time.time())
    quote_index = random.randint(0, len(AVIATION_QUOTES) - 1)
    quote_text, author = AVIATION_QUOTES[quote_index]
    quote_img = draw_quote(quote_text, author)
    epd.displayPartial(epd.getbuffer(quote_img))
    
    quote_start = time.time()
    flight_data = None
    
    while time.time() - quote_start < 10:
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
            time.sleep(0.1)
            continue
        
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            logging.info("Exiting during quote display")
            flag_t[0] = 0
            gt_old.X[0] = 0
            gt_old.Y[0] = 0
            gt_old.S[0] = 0
            return
        
        time.sleep(0.1)
    
    flight_data = get_current_flight()
    
    if not flight_data:
        logging.info("No flights - starting quote cycle mode (every 30 min)")
        
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)
        quote_text, author = AVIATION_QUOTES[quote_index]
        quote_img = draw_quote(quote_text, author)
        epd.displayPartBaseImage(epd.getbuffer(quote_img))
        epd.init(epd.PART_UPDATE)
        logging.info(f"Showing quote {quote_index}: {author}")
        
        last_quote_time = time.time()
        quote_index = (quote_index + 1) % len(AVIATION_QUOTES)
        
        while True:
            gt.GT_Scan(gt_dev, gt_old)
            # Check for exit signal from menu
            if hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested:
                logging.info("Exit requested by menu")
                flag_t[0] = 0
                break
            
            
            current_time = time.time()
            
            if current_time - last_quote_time > 1800:
                logging.info(f"30 min elapsed, showing next quote {quote_index}")
                epd.init(epd.FULL_UPDATE)
                epd.Clear(0xFF)
                
                quote_text, author = AVIATION_QUOTES[quote_index]
                quote_img = draw_quote(quote_text, author)
                epd.displayPartBaseImage(epd.getbuffer(quote_img))
                epd.init(epd.PART_UPDATE)
                
                quote_index = (quote_index + 1) % len(AVIATION_QUOTES)
                last_quote_time = current_time
                
                logging.info("Checking for flights...")
                flight_data = get_current_flight()
                if flight_data:
                    logging.info(f"Flight found: {flight_data.get('callsign')}, exiting quote mode")
                    break
                else:
                    logging.info("Still no flights, continuing quote cycle")
            
            if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
                time.sleep(0.1)
                continue
            
            if gt_dev.TouchpointFlag:
                gt_dev.TouchpointFlag = 0
                logging.info("Exiting quotes mode")
                flag_t[0] = 0
                gt_old.X[0] = 0
                gt_old.Y[0] = 0
                gt_old.S[0] = 0
                return
            
            time.sleep(0.1)
        
        if not flight_data:
            gt_old.X[0] = 0
            gt_old.Y[0] = 0
            gt_old.S[0] = 0
            return
    
    image = draw_flight_portal(flight_data, animation_frame)
    epd.displayPartial(epd.getbuffer(image))
    
    quote_index = (quote_index + 1) % len(AVIATION_QUOTES)
    
    last_update = time.time()
    last_animation_cycle = time.time()
    last_quote_time = time.time()
    
    logging.info("Flights app started")
    
    while True:
        gt.GT_Scan(gt_dev, gt_old)
        # Check for exit signal from menu
        if hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested:
            logging.info("Exit requested by menu")
            flag_t[0] = 0
            break
        
        
        current_time = time.time()
        
        if current_time - last_quote_time > QUOTE_INTERVAL:
            logging.info(f"Showing quote {quote_index}")
            
            epd.init(epd.FULL_UPDATE)
            epd.Clear(0xFF)
            
            quote_text, author = AVIATION_QUOTES[quote_index]
            quote_img = draw_quote(quote_text, author)
            epd.displayPartBaseImage(epd.getbuffer(quote_img))
            epd.init(epd.PART_UPDATE)
            time.sleep(10)
            
            flight_data = get_current_flight()
            if flight_data:
                image = draw_flight_portal(flight_data, 0)
                epd.displayPartial(epd.getbuffer(image))
            
            quote_index = (quote_index + 1) % len(AVIATION_QUOTES)
            last_quote_time = current_time
            last_update = current_time
            last_animation_cycle = current_time
            animation_frame = 0
        
        elif current_time - last_update > UPDATE_INTERVAL:
            logging.info("Checking for new flight")
            new_flight = get_current_flight()
            
            if new_flight:
                flight_data = new_flight
                animation_frame = 0
                image = draw_flight_portal(flight_data, animation_frame)
                epd.displayPartial(epd.getbuffer(image))
            
            last_update = current_time
            last_animation_cycle = current_time
        
        elif current_time - last_animation_cycle > ANIMATION_CYCLE_INTERVAL:
            animation_frame += 1
            image = draw_flight_portal(flight_data, animation_frame)
            epd.displayPartial(epd.getbuffer(image))
            last_animation_cycle = current_time
        
        if gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and gt_old.S[0] == gt_dev.S[0]:
            time.sleep(0.01)
            continue
        
        if gt_dev.TouchpointFlag:
            gt_dev.TouchpointFlag = 0
            logging.info("Exiting flights app")
            flag_t[0] = 0
            break
    
    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0
