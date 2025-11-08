#!/usr/bin/python3
"""
Reboot Application - Refactored
Provides system reboot confirmation dialog with touch-enabled buttons.
Uses shared utilities and display components to eliminate code duplication.
"""

from display.components import Button
from display.fonts import get_font_preset
from display.touch_handler import TouchHandler
from shared.app_utils import setup_logging, check_exit_requested, cleanup_touch_state
from PIL import Image, ImageDraw
from TP_lib import gt1151, epd2in13_V3
import sys
import os
import time
import subprocess
import logging

# Path setup
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'python/lib')
sys.path.append(libdir)


logger = setup_logging('reboot_app', log_to_file=True)


def draw_reboot_confirm(epd, gt_dev, gt_old, gt):
    """Show reboot confirmation screen with Cancel/Reboot buttons"""
    logger.info("Showing reboot confirmation screen")

    try:
        # Start touch handler
        touch = TouchHandler(gt, gt_dev)
        touch.start()

        # Define buttons
        cancel_btn = Button("Cancel", 10, 70, 100, 30, get_font_preset('body'))
        reboot_btn = Button("Reboot", 140, 70, 100, 30, get_font_preset('body'))

        # Draw confirmation screen
        img = Image.new('1', (250, 122), 255)
        draw = ImageDraw.Draw(img)
        draw.text((50, 20), "Reboot System?", font=get_font_preset('title'), fill=0)
        cancel_btn.draw(draw)
        reboot_btn.draw(draw)
        epd.displayPartial(epd.getbuffer(img))

        # Handle user input
        last_touch_time = time.time()
        while touch.is_running():
            if check_exit_requested(gt_dev):
                logger.info("Exit requested")
                break

            gt.GT_Scan(gt_dev, gt_old)

            if (gt_old.X[0] == gt_dev.X[0] and gt_old.Y[0] == gt_dev.Y[0] and
                    gt_old.S[0] == gt_dev.S[0]):
                time.sleep(0.01)
                continue

            if gt_dev.TouchpointFlag:
                gt_dev.TouchpointFlag = 0
                current_time = time.time()

                if current_time - last_touch_time < 0.3:
                    continue

                last_touch_time = current_time
                x, y = gt_dev.X[0], gt_dev.Y[0]
                logger.info(f"Touch: X={x} Y={y}")

                # API Contract: Y > 180 = LEFT (Cancel), Y < 70 = RIGHT (Reboot)
                if y > 180:
                    logger.info("Cancel")
                    break
                elif y < 70:
                    logger.info("Rebooting...")
                    img = Image.new('1', (250, 122), 255)
                    draw = ImageDraw.Draw(img)
                    draw.text((60, 50), "Rebooting...", font=get_font_preset('title'), fill=0)
                    epd.displayPartial(epd.getbuffer(img))
                    time.sleep(1)

                    result = subprocess.run(['sudo', 'reboot'], capture_output=True, timeout=5)
                    if result.returncode != 0:
                        logger.error(f"Reboot failed: {result.stderr.decode()}")
                    break

            time.sleep(0.01)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise RuntimeError(f"Reboot confirmation failed: {e}") from e

    finally:
        touch.stop()
        cleanup_touch_state(gt_old)


if __name__ == '__main__':
    try:
        epd = epd2in13_V3.EPD()
        epd.init(epd.FULL_UPDATE)
        epd.Clear(0xFF)
        epd.init(epd.PART_UPDATE)

        gt = gt1151.GT1151()
        gt_dev = gt1151.GT_State()
        gt_old = gt1151.GT_State()

        logger.info("Reboot app started")
        draw_reboot_confirm(epd, gt_dev, gt_old, gt)
        logger.info("Reboot app completed")

    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        try:
            epd.sleep()
            epd.module_exit()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
