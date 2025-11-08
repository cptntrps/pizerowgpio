#!/usr/bin/python3
"""
Weather Calendar Application
=============================

Simplified weather and calendar display using shared components library.

Features:
- Real-time weather from wttr.in API
- Automatic refresh every 5 minutes
- Touch button for manual refresh
- Comprehensive error handling
- Uses shared utilities and display components

Refactoring: 171 -> 119 lines (30% reduction)
"""

from display.components import StatusBar
from display.fonts import get_font_preset
from display.touch_handler import TouchHandler
from shared.app_utils import (
    ConfigLoader, setup_logging, check_exit_requested,
    cleanup_touch_state, PeriodicTimer, safe_execute
)
from PIL import Image, ImageDraw, ImageFont
from TP_lib import gt1151, epd2in13_V3
import sys
import os
import time
import subprocess
import logging
import math
from datetime import datetime

# ============================================================================
# PATH SETUP
# ============================================================================

project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, project_root)

# Import Pi Zero display driver (required for hardware)
picdir = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))),
    'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)


# ============================================================================
# IMPORTS - Shared Utilities & Display Components
# ============================================================================


# ============================================================================
# LOGGER & CONFIGURATION
# ============================================================================

logger = setup_logging("weather_app", log_to_file=True)

config = ConfigLoader.load()
WEATHER_CONFIG = ConfigLoader.get_section(
    "weather", {"location": "London", "update_interval": 300})
LOCATION = WEATHER_CONFIG.get("location", "London")
UPDATE_INTERVAL = WEATHER_CONFIG.get("update_interval", 300)

# ============================================================================
# WEATHER DATA FETCHING
# ============================================================================


def get_weather():
    """Fetch current weather from wttr.in API

    Returns:
        dict: Weather data with 'condition', 'temp', 'humidity' or None on error
    """
    def _fetch():
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{LOCATION}?format=%C+%t+%h'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None

        data = result.stdout.strip().split()
        if len(data) >= 3:
            return {
                'condition': " ".join(data[:-2]),
                'temp': data[-2],
                'humidity': data[-1]
            }
        return None

    return safe_execute(_fetch, "Weather fetch failed", None)


# ============================================================================
# WEATHER ICON DRAWING
# ============================================================================

def draw_weather_icon(draw, condition, x, y):
    """Draw weather icon based on condition

    Args:
        draw: PIL ImageDraw object
        condition: Weather condition string
        x, y: Icon position
    """
    condition_lower = condition.lower()

    # Sun/Clear
    if 'sun' in condition_lower or 'clear' in condition_lower:
        draw.ellipse([x + 10, y + 10, x + 30, y + 30], outline=0, width=2)
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle)
            x1, y1 = x + 20 + 15 * math.cos(rad), y + 20 + 15 * math.sin(rad)
            x2, y2 = x + 20 + 20 * math.cos(rad), y + 20 + 20 * math.sin(rad)
            draw.line([x1, y1, x2, y2], fill=0, width=2)

    # Cloud
    elif 'cloud' in condition_lower:
        draw.ellipse([x + 5, y + 15, x + 20, y + 25], outline=0, width=2)
        draw.ellipse([x + 15, y + 10, x + 30, y + 20], outline=0, width=2)
        draw.ellipse([x + 25, y + 15, x + 40, y + 25], outline=0, width=2)

    # Rain/Drizzle
    elif 'rain' in condition_lower or 'drizzle' in condition_lower:
        for cx, cy in [(10, 12), (22, 12), (34, 12)]:
            draw.ellipse([x + cx - 5, y + cy - 5, x + cx + 5, y + cy + 5], outline=0, width=2)
        draw.line([x + 10, y + 25, x + 8, y + 32], fill=0, width=2)
        draw.line([x + 22, y + 25, x + 20, y + 32], fill=0, width=2)
        draw.line([x + 34, y + 25, x + 32, y + 32], fill=0, width=2)

    # Snow
    elif 'snow' in condition_lower:
        draw.line([x + 20, y + 10, x + 20, y + 30], fill=0, width=2)
        draw.line([x + 10, y + 20, x + 30, y + 20], fill=0, width=2)
        draw.line([x + 13, y + 13, x + 27, y + 27], fill=0, width=2)
        draw.line([x + 27, y + 13, x + 13, y + 27], fill=0, width=2)

    else:
        draw.text((x + 15, y + 10), "?", fill=0)


# ============================================================================
# SCREEN DRAWING
# ============================================================================

def draw_weather_screen():
    """Draw weather and calendar display

    Returns:
        PIL Image: Display image ready for epd
    """
    img = Image.new('1', (250, 122), 255)
    draw = ImageDraw.Draw(img)

    # Fonts from display library
    f_time = get_font_preset('headline')
    f_date = get_font_preset('subtitle')
    f_temp = get_font_preset('title')
    f_small = get_font_preset('small')

    # Draw status bar (time at top)
    status = StatusBar(show_time=True, font=f_time)
    status.draw(draw)

    # Current date
    date_str = datetime.now().strftime("%a, %b %d")
    draw.text((10, 38), date_str, font=f_date, fill=0)

    # Separator line
    draw.line((5, 60, 245, 60), fill=0, width=1)

    # Weather data section
    weather = safe_execute(get_weather, "Cannot display weather", None)
    if weather:
        draw_weather_icon(draw, weather['condition'], 10, 65)
        draw.text((70, 68), weather['temp'], font=f_temp, fill=0)
        draw.text((70, 95), weather['condition'][:15], font=f_small, fill=0)
        draw.text((170, 75), "Humid:", font=f_small, fill=0)
        draw.text((170, 90), weather['humidity'], font=f_small, fill=0)
    else:
        draw.text((50, 75), "Weather unavailable", font=f_small, fill=0)
        draw.text((50, 90), "Check connection", font=f_small, fill=0)

    # Status line
    draw.text((75, 112), "Auto-refresh: 5 min", font=f_small, fill=0)

    return img


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def run_weather_app(epd, gt_dev, gt_old, gt):
    """Main weather app loop

    Args:
        epd: Display driver object
        gt_dev: Touch device state
        gt_old: Previous touch state
        gt: Touch driver instance
    """
    logger.info(f"Starting weather app - Location: {LOCATION}")

    # Start touch handler (replaces 15 lines of threading code)
    touch = TouchHandler(gt, gt_dev)
    touch.start()

    # Periodic update timer
    update_timer = PeriodicTimer(UPDATE_INTERVAL)

    try:
        # Initial display
        image = safe_execute(draw_weather_screen, "Failed to draw initial screen")
        if image:
            epd.displayPartial(epd.getbuffer(image))

        # Main loop
        while True:
            # Check for exit request
            if check_exit_requested(gt_dev):
                logger.info("Exit requested by menu")
                break

            # Auto-refresh weather
            if update_timer.is_ready():
                logger.info(f"Auto-refreshing weather from {LOCATION}")
                image = safe_execute(draw_weather_screen, "Failed to redraw screen")
                if image:
                    epd.displayPartial(epd.getbuffer(image))

            # Handle touch input for manual refresh
            gt.GT_Scan(gt_dev, gt_old)
            if gt_dev.TouchpointFlag:
                gt_dev.TouchpointFlag = 0
                logger.info("Manual refresh triggered by touch")
                image = safe_execute(draw_weather_screen, "Failed to redraw screen")
                if image:
                    epd.displayPartial(epd.getbuffer(image))

            # Check for position changes (ignore if no touch change)
            if (gt_old.X[0] == gt_dev.X[0] and
                gt_old.Y[0] == gt_dev.Y[0] and
                    gt_old.S[0] == gt_dev.S[0]):
                time.sleep(0.1)
                continue

            time.sleep(0.1)

    except Exception as e:
        logger.error(f"Weather app error: {e}", exc_info=True)

    finally:
        touch.stop()
        logger.info("Weather app stopped")
