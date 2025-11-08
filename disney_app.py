#!/usr/bin/python3
"""
Disney Magic Kingdom Wait Times for E-Paper Display (REFACTORED)
Shows current ride wait times with themed backgrounds
Optimized for e-paper refresh limitations with shared utilities
"""
from display.components import MessageBox
from display.text import draw_centered_text, truncate_text_to_width
from display.fonts import get_font_preset
from display.touch_handler import TouchHandler, cleanup_touch_state, check_exit_requested
from shared.app_utils import ConfigLoader, setup_logging, setup_paths
from TP_lib import gt1151, epd2in13_V3
import sys
import os
import time
import json
import subprocess
import random
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Setup paths for imports
sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.realpath(__file__))),
        'python/lib'))


# Setup paths and logging
setup_paths()
logger = setup_logging('disney_app')

# Get directories
imagedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'disney_images')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')

# Cache for background images
BACKGROUND_CACHE = {}


# ============================================================================
# FETCH OPERATIONS
# ============================================================================

def fetch_wait_times():
    """Fetch Disney Magic Kingdom wait times from queue-times.com

    Returns:
        list: List of ride dictionaries with wait times and status
    """
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
            logger.info(f"Fetched {len(rides)} rides from queue-times.com")
            return rides
    except subprocess.TimeoutExpired:
        logger.error("Timeout while fetching wait times")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response: {e}")
    except Exception as e:
        logger.error(f"Failed to fetch wait times: {e}")

    return []


# ============================================================================
# IMAGE HANDLING
# ============================================================================

def load_land_background(land_name):
    """Load and convert land background image to 1-bit with caching

    Args:
        land_name: Name of the land (e.g., 'Adventureland')

    Returns:
        PIL Image: 1-bit monochrome background image
    """
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
            img = img.resize((250, 122), Image.Resampling.LANCZOS)

            # Convert to 1-bit with dithering
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

            BACKGROUND_CACHE[land_name] = bw_img
            logger.debug(f"Cached background for {land_name}")
            return bw_img
    except Exception as e:
        logger.error(f"Failed to load background for {land_name}: {e}")

    # Return blank image if loading fails
    blank = Image.new('1', (250, 122), 255)
    BACKGROUND_CACHE[land_name] = blank
    return blank


def draw_ride_info(ride):
    """Draw ride wait time with themed background

    Args:
        ride: Ride dictionary with name, wait_time, is_open, land

    Returns:
        PIL Image: Ride info display
    """
    # Load background for the land
    img = load_land_background(ride['land']).copy()
    draw = ImageDraw.Draw(img)

    # Draw semi-transparent overlay for text readability
    draw.rectangle([0, 40, 250, 82], fill=255, outline=0, width=2)

    # Get fonts
    f_name = get_font_preset('subtitle')
    f_time = get_font_preset('display')
    f_small = get_font_preset('small')

    # Ride name - truncate if too long
    name = ride['name']
    dummy_img = Image.new('1', (1, 1), 255)
    bbox = ImageDraw.Draw(dummy_img).textbbox((0, 0), name, font=f_name)
    text_width = bbox[2] - bbox[0]

    if text_width > 230:
        # Truncate with ellipsis
        name = truncate_text_to_width(draw, name, 230, f_name, suffix='...')
        draw.text((10, 45), name, font=f_name, fill=0)
    else:
        # Center text if it fits
        x_pos = (250 - text_width) // 2
        draw.text((x_pos, 45), name, font=f_name, fill=0)

    # Wait time or status
    wait_text = f"{ride['wait_time']} min" if ride['is_open'] else "CLOSED"
    bbox = ImageDraw.Draw(dummy_img).textbbox((0, 0), wait_text, font=f_time)
    w = bbox[2] - bbox[0]
    draw.text(((250 - w) // 2, 62), wait_text, font=f_time, fill=0)

    # Land name at bottom
    draw.text((5, 5), ride['land'], font=f_small, fill=0)
    draw.text((180, 110), "Touch=Exit", font=f_small, fill=0)

    return img


# ============================================================================
# DISPLAY OPERATIONS
# ============================================================================

def show_loading_screen(epd):
    """Show loading message on display

    Args:
        epd: Display driver object
    """
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    f = get_font_preset('body')
    draw.text((30, 50), "Loading Disney wait times...", font=f, fill=0)
    epd.displayPartial(epd.getbuffer(img))


def show_error_screen(epd, message):
    """Show error message on display

    Args:
        epd: Display driver object
        message: Error message to display
    """
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)
    f = get_font_preset('body')

    draw.text((20, 40), "Unable to fetch wait times", font=f, fill=0)
    draw.text((60, 60), message, font=f, fill=0)
    epd.displayPartial(epd.getbuffer(img))


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def run_disney_app(epd, gt_dev, gt_old, gt):
    """Disney wait times app (REFACTORED)

    Args:
        epd: E-paper display driver
        gt_dev: Touch device state
        gt_old: Previous touch state
        gt: Touch driver interface
    """
    # Use TouchHandler for cleaner thread management
    touch = TouchHandler(gt, gt_dev)
    touch.start()

    try:
        # Clear any pending touch events
        cleanup_touch_state(gt_old)

        logger.info("Disney app started - fetching wait times...")

        # Show loading screen
        show_loading_screen(epd)

        # Fetch wait times
        rides = fetch_wait_times()

        if not rides:
            logger.error("No wait times fetched")
            show_error_screen(epd, "Check internet connection")
            time.sleep(3)
            return

        logger.info(f"Displaying {len(rides)} rides")
        random.shuffle(rides)

        # Pre-cache backgrounds for all lands
        logger.debug("Pre-loading backgrounds...")
        unique_lands = set(ride['land'] for ride in rides)
        for land in unique_lands:
            load_land_background(land)

        # Configuration
        disney_config = ConfigLoader.get_section('disney', {})
        update_interval = disney_config.get('update_interval', 10)
        scroll_interval = 0.5
        scroll_step = 3

        # Display loop
        ride_index = 0
        last_update = time.time()

        # Check if current ride needs scrolling
        f_name = get_font_preset('subtitle')
        dummy_img = Image.new('1', (1, 1), 255)
        bbox = ImageDraw.Draw(dummy_img).textbbox((0, 0), rides[ride_index]['name'], font=f_name)
        needs_scroll = (bbox[2] - bbox[0]) > 230

        # Initial display
        image = draw_ride_info(rides[ride_index])
        epd.displayPartial(epd.getbuffer(image))

        # Wait for display to settle
        time.sleep(0.5)
        cleanup_touch_state(gt_old)

        while touch.is_running():
            # Check for exit signal
            if check_exit_requested(gt_dev) or touch.is_touched():
                logger.info("Exiting Disney app")
                break

            current_time = time.time()

            # Update to next ride
            if current_time - last_update >= update_interval:
                ride_index = (ride_index + 1) % len(rides)
                current_ride = rides[ride_index]

                # Check if new ride needs scrolling
                bbox = ImageDraw.Draw(dummy_img).textbbox(
                    (0, 0), current_ride['name'], font=f_name)
                needs_scroll = (bbox[2] - bbox[0]) > 230

                # Re-fetch every 20 rides
                if ride_index % 20 == 0:
                    logger.debug("Re-fetching wait times...")
                    new_rides = fetch_wait_times()
                    if new_rides:
                        rides = new_rides
                        random.shuffle(rides)
                        BACKGROUND_CACHE.clear()
                        unique_lands = set(ride['land'] for ride in rides)
                        for land in unique_lands:
                            load_land_background(land)

                image = draw_ride_info(current_ride)
                epd.displayPartial(epd.getbuffer(image))
                last_update = current_time

            # Small sleep to avoid busy waiting
            time.sleep(0.01)

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        show_error_screen(epd, f"Error: {str(e)[:30]}")
        time.sleep(3)

    finally:
        # Cleanup
        BACKGROUND_CACHE.clear()
        cleanup_touch_state(gt_old)
        touch.stop()
        logger.info("Disney app cleanup complete")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        # Initialize display
        epd = epd2in13_V3.EPD()
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)
        epd.init(epd.PART_UPDATE)

        # Initialize touch
        gt = gt1151.gt1151()
        gt_dev = gt1151.gt1151_dev()
        gt_old = gt1151.gt1151_dev()

        # Run application
        run_disney_app(epd, gt_dev, gt_old, gt)

        # Cleanup display
        epd.sleep()
        epd.module_exit()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
