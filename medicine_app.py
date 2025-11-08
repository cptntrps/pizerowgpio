#!/usr/bin/python3
"""
Medicine Tracker App - Refactored for SQLite
E-ink display app for tracking medicine schedule and adherence
"""

from shared.app_utils import ConfigLoader, get_font, install_signal_handlers
from db.medicine_db import MedicineDatabase
from PIL import Image, ImageDraw, ImageFont
from TP_lib import gt1151, epd2in13_V3
import sys
import os
import time
from datetime import datetime, date
import logging
import threading

# Add library paths
picdir = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))),
    'python/pic/2in13')
fontdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)

# Add project root to path for local imports
project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, project_root)


# Import our new database and utilities

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = ConfigLoader()
medicine_config = config.get_section('medicine')
UPDATE_INTERVAL = medicine_config.get('update_interval', 60)
REMINDER_WINDOW = medicine_config.get('reminder_window', 30)

# Initialize database
db = MedicineDatabase()

# Font cache (using shared utility)
FONT_DIR = fontdir


def get_pending_medicines():
    """Get list of medicines that are due now using database"""
    try:
        pending = db.get_pending_medicines(check_date=date.today(), check_time=datetime.now())
        return pending
    except Exception as e:
        logger.error(f"Failed to get pending medicines: {e}")
        return []


def mark_medicines_taken(medicines):
    """Mark a list of medicines as taken using database"""
    try:
        results = []
        for med in medicines:
            result = db.mark_medicine_taken(
                medicine_id=med['id'],
                time_window=med.get('time_window'),
                taken_date=date.today(),
                timestamp=datetime.now()
            )
            results.append(result)

            # Log low stock warnings
            if result.get('low_stock'):
                logger.warning(
                    f"Low stock alert: {med['name']} - {result['pills_remaining']} pills remaining")

        return True
    except Exception as e:
        logger.error(f"Failed to mark medicines taken: {e}")
        return False


def get_today_stats():
    """Get today's medicine statistics from database"""
    try:
        taken, total = db.get_today_stats(check_date=date.today())
        return taken, total
    except Exception as e:
        logger.error(f"Failed to get today stats: {e}")
        return 0, 0


def get_all_medicines_for_today():
    """Get all active medicines scheduled for today"""
    try:
        all_medicines = db.get_all_medicines(include_inactive=False)
        today_day = datetime.now().strftime("%a").lower()

        # Filter for today
        today_medicines = [m for m in all_medicines if today_day in m.get('days', [])]
        return today_medicines
    except Exception as e:
        logger.error(f"Failed to get medicines: {e}")
        return []


def get_tracking_for_today():
    """Get tracking data for today"""
    try:
        today_str = date.today().strftime('%Y-%m-%d')
        tracking = db.get_tracking_history(
            start_date=date.today(),
            end_date=date.today()
        )

        # Convert to dict keyed by medicine_id_timewindow
        tracking_dict = {}
        for entry in tracking:
            key = f"{entry['medicine_id']}_{entry['time_window']}"
            tracking_dict[key] = entry

        return tracking_dict
    except Exception as e:
        logger.error(f"Failed to get tracking: {e}")
        return {}


def get_data_timestamp():
    """Get the last updated timestamp from database"""
    try:
        return db.get_last_updated()
    except Exception as e:
        logger.error(f"Failed to get timestamp: {e}")
        return datetime.now().isoformat()


def draw_pill_icon(draw, x, y, size=10):
    """Draw a simple pill icon"""
    # Capsule shape
    draw.ellipse([x, y, x + size, y + size], outline=0, width=2)
    draw.line([x + size // 4, y, x + size // 4, y + size], fill=0, width=1)


def draw_food_icon(draw, x, y, size=8):
    """Draw a simple fork/knife icon for 'with food'"""
    # Fork
    draw.line([x, y, x, y + size], fill=0, width=1)
    draw.line([x - 1, y, x - 1, y + size // 2], fill=0, width=1)
    draw.line([x + 1, y, x + 1, y + size // 2], fill=0, width=1)


def draw_current_reminder(pending_meds, current_index=0):
    """Draw current medicine reminder (rotate through if multiple)"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)

    f_title = get_font('Roboto-Bold', 12)
    f_med = get_font('Roboto-Bold', 16)
    f_dose = get_font('Roboto-Regular', 12)
    f_small = get_font('Roboto-Regular', 10)

    # Title bar
    now = datetime.now().strftime("%H:%M")
    draw.text((5, 2), "TIME TO TAKE MEDICINE", font=f_title, fill=0)
    draw.text((200, 2), now, font=f_title, fill=0)
    draw.line([(0, 18), (250, 18)], fill=0, width=1)

    if not pending_meds:
        # No pending medicines
        draw.text((40, 50), "All caught up!", font=f_med, fill=0)
        draw.text((60, 70), "No medicines due now", font=f_small, fill=0)
    else:
        # Show current medicine (rotate through)
        med = pending_meds[current_index % len(pending_meds)]

        y_pos = 30

        # Pill icon
        draw_pill_icon(draw, 10, y_pos + 5, 15)

        # Medicine name
        draw.text((35, y_pos), med["name"], font=f_med, fill=0)

        # Dosage
        draw.text((35, y_pos + 20), med["dosage"], font=f_dose, fill=0)

        # With food indicator
        if med.get("with_food", False):
            draw_food_icon(draw, 10, y_pos + 25, 10)
            draw.text((25, y_pos + 22), "with food", font=f_small, fill=0)

        # Pills remaining and low stock warning
        pills_remaining = med.get("pills_remaining", 0)
        low_threshold = med.get("low_stock_threshold", 10)

        y_info = y_pos + 40
        if med.get("notes"):
            notes_text = med["notes"][:25]  # Truncate if too long
            draw.text((10, y_info), notes_text, font=f_small, fill=0)
            y_info += 12

        # Show pill count
        pill_text = f"Pills left: {pills_remaining}"
        if pills_remaining <= low_threshold:
            pill_text += " - REORDER!"
        draw.text((10, y_info), pill_text, font=f_small, fill=0)

        # If multiple, show count
        if len(pending_meds) > 1:
            count_text = f"({current_index + 1}/{len(pending_meds)})"
            draw.text((200, y_pos + 40), count_text, font=f_small, fill=0)

    # Bottom instructions
    draw.line([(0, 100), (250, 100)], fill=0, width=1)
    if pending_meds:
        if len(pending_meds) > 1:
            instruction = "Tap: Next | Double-tap: Take | Hold: Exit"
        else:
            instruction = "Double-tap: Mark taken | Hold: Exit"
    else:
        instruction = "Hold 2s: Exit"
    draw.text((10, 106), instruction, font=f_small, fill=0)

    return img


def draw_schedule_view():
    """Draw today's full schedule"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)

    f_title = get_font('Roboto-Bold', 12)
    f_item = get_font('Roboto-Regular', 11)
    f_small = get_font('Roboto-Regular', 9)

    today = datetime.now().strftime("%b %d")
    current_day = datetime.now().strftime("%a").lower()

    # Title
    draw.text((5, 2), f"Today's Medicines - {today}", font=f_title, fill=0)
    draw.line([(0, 16), (250, 16)], fill=0, width=1)

    # Get medicines and tracking for today
    medicines = get_all_medicines_for_today()
    tracking = get_tracking_for_today()

    # Group medicines by time window
    windows = {}
    for med in medicines:
        window = med.get("time_window", "morning")
        if window not in windows:
            windows[window] = []
        windows[window].append(med)

    # Draw schedule
    y_pos = 20

    for window in ["morning", "afternoon", "evening", "night"]:
        if window not in windows:
            continue

        meds = windows[window]
        window_text = window.capitalize()

        # Window header
        draw.text((5, y_pos), window_text, font=f_item, fill=0)
        y_pos += 14

        for med in meds:
            # Check if taken
            tracking_key = f"{med['id']}_{window}"
            taken = tracking_key in tracking and tracking[tracking_key].get('taken', False)

            # Checkbox
            checkbox = "[✓]" if taken else "[ ]"
            med_text = f"{checkbox} {med['name']} ({med['dosage']})"
            draw.text((15, y_pos), med_text, font=f_small, fill=0)
            y_pos += 11

    # Stats at bottom
    taken, total = get_today_stats()
    if total > 0:
        percentage = int((taken / total) * 100)
        draw.line([(0, 95), (250, 95)], fill=0, width=1)
        stats_text = f"Progress: {taken}/{total} taken ({percentage}%)"
        draw.text((40, 100), stats_text, font=f_small, fill=0)
        draw.text((30, 110), "Tap: Refresh | Hold: Exit", font=f_small, fill=0)

    return img


def draw_confirmation_screen(medicines_taken, count):
    """Draw confirmation screen after marking medicines taken"""
    img = Image.new("1", (250, 122), 255)
    draw = ImageDraw.Draw(img)

    f_big = get_font('Roboto-Bold', 20)
    f_medium = get_font('Roboto-Regular', 12)
    f_small = get_font('Roboto-Regular', 10)

    # Big checkmark
    draw.text((90, 15), "✓", font=f_big, fill=0)

    # Confirmation text
    draw.text((60, 45), "Marked as Taken!", font=f_medium, fill=0)

    # List medicines
    y_pos = 65
    for i, med in enumerate(medicines_taken[:3]):  # Show max 3
        med_text = f"• {med['name']} ({med['dosage']})"
        draw.text((30, y_pos), med_text, font=f_small, fill=0)
        y_pos += 12

    if count > 3:
        draw.text((50, y_pos), f"+ {count - 3} more...", font=f_small, fill=0)

    # Timestamp
    now = datetime.now().strftime("%H:%M")
    draw.text((80, 105), f"Taken at {now}", font=f_small, fill=0)

    return img


def run_medicine_app(epd, gt_dev, gt_old, gt):
    """Medicine tracking app with button controls"""

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
    rotation_index = 0
    view_mode = "reminder"  # "reminder" or "schedule"
    last_timestamp_check = 0
    TIMESTAMP_CHECK_INTERVAL = 5  # Check for external changes every 5 seconds

    # Click tracking for double-click detection
    last_click_time = 0
    DOUBLE_CLICK_TIME = 0.5  # 500ms for double click

    # Initial display
    last_known_timestamp = get_data_timestamp()
    pending = get_pending_medicines()

    if pending:
        image = draw_current_reminder(pending, rotation_index)
    else:
        image = draw_schedule_view()
        view_mode = "schedule"

    epd.displayPartial(epd.getbuffer(image))
    last_update = time.time()

    logger.info("Medicine app started")

    while True:
        current_time = time.time()

        # Check for external data changes (push refresh)
        if current_time - last_timestamp_check > TIMESTAMP_CHECK_INTERVAL:
            current_timestamp = get_data_timestamp()

            if current_timestamp != last_known_timestamp:
                logger.info(
                    f"Data changed externally (timestamp: {current_timestamp}), refreshing display")
                last_known_timestamp = current_timestamp
                pending = get_pending_medicines()
                rotation_index = 0

                if pending and view_mode == "reminder":
                    image = draw_current_reminder(pending, rotation_index)
                else:
                    image = draw_schedule_view()
                    if not pending:
                        view_mode = "schedule"

                epd.displayPartial(epd.getbuffer(image))
                last_update = current_time

            last_timestamp_check = current_time

        # Auto-refresh data periodically
        if current_time - last_update > UPDATE_INTERVAL:
            logger.info("Auto-refreshing medicine data")
            pending = get_pending_medicines()

            if pending and view_mode == "reminder":
                image = draw_current_reminder(pending, rotation_index)
            else:
                image = draw_schedule_view()
                view_mode = "schedule"

            epd.displayPartial(epd.getbuffer(image))
            last_update = current_time

        # NO AUTO-ROTATION - user controls cycling manually

        gt.GT_Scan(gt_dev, gt_old)

        # Check for exit signal from menu
        if hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested:
            logger.info("Exit requested by menu")
            flag_t[0] = 0
            break

        # Handle button clicks (menu system sets TouchpointFlag)
        # Note: No position check needed for GPIO-only (no touchscreen)
        if gt_dev.TouchpointFlag:
            logger.info("Button clicked - processing")
            gt_dev.TouchpointFlag = 0

            current_click_time = time.time()

            # Check if this is a double click
            if current_click_time - last_click_time < DOUBLE_CLICK_TIME:
                # Double click detected - mark selected medicine as taken
                logger.info("Double click - marking selected medicine as taken")
                last_click_time = 0  # Reset to prevent triple-click

                pending = get_pending_medicines()

                if pending and len(pending) > 0:
                    # Mark only the currently selected medicine
                    selected_med = [pending[rotation_index % len(pending)]]
                    logger.info(f"Marking {selected_med[0]['name']} as taken")

                    if mark_medicines_taken(selected_med):
                        # Show confirmation screen
                        epd.init(epd.FULL_UPDATE)
                        epd.Clear(0xFF)

                        image = draw_confirmation_screen(selected_med, 1)
                        epd.displayPartBaseImage(epd.getbuffer(image))
                        epd.init(epd.PART_UPDATE)

                        time.sleep(2)  # Show confirmation for 2 seconds

                        # Refresh display
                        last_known_timestamp = get_data_timestamp()
                        pending = get_pending_medicines()
                        rotation_index = 0

                        if pending:
                            image = draw_current_reminder(pending, rotation_index)
                            view_mode = "reminder"
                        else:
                            image = draw_schedule_view()
                            view_mode = "schedule"

                        epd.displayPartial(epd.getbuffer(image))
                        last_update = current_time
            else:
                # Single click - cycle to next medicine
                last_click_time = current_click_time

                pending = get_pending_medicines()

                if pending and len(pending) > 1:
                    rotation_index = (rotation_index + 1) % len(pending)
                    logger.info(
                        f"Single click - cycling to medicine {rotation_index + 1}/{len(pending)}")
                    image = draw_current_reminder(pending, rotation_index)
                    epd.displayPartial(epd.getbuffer(image))
                elif pending and len(pending) == 1:
                    logger.info("Single click - only one medicine, just refresh")
                    image = draw_current_reminder(pending, 0)
                    epd.displayPartial(epd.getbuffer(image))
                else:
                    logger.info("Single click - no pending medicines, show schedule")
                    image = draw_schedule_view()
                    epd.displayPartial(epd.getbuffer(image))

        time.sleep(0.1)

    gt_old.X[0] = 0
    gt_old.Y[0] = 0
    gt_old.S[0] = 0


# Signal handler for graceful shutdown
def cleanup():
    """Cleanup database connection on exit"""
    logger.info("Cleaning up medicine app...")
    try:
        db.close()
    except BaseException:
        pass


# Install signal handlers
install_signal_handlers(cleanup)
