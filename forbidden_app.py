#!/usr/bin/python3
"""Forbidden App - Shows locked message with shared utilities."""

from shared.app_utils import setup_logging, ConfigLoader
from display.touch_handler import TouchHandler, check_exit_requested
from display import canvas, fonts, text
from TP_lib import gt1151, epd2in13_V3
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python/lib'))


logger = setup_logging("forbidden_app")


def draw_forbidden_message(epd, gt_dev, gt_old, gt):
    """Show the forbidden message. Returns when user touches."""
    try:
        # Load configuration
        msg1 = ConfigLoader.get_value('forbidden', 'message_line1', 'Access Forbidden')
        msg2 = ConfigLoader.get_value('forbidden', 'message_line2', 'Touch to continue')

        # Create canvas
        img, draw = canvas.create_canvas()
        font_big = fonts.get_font('Roboto-Bold', 16)
        font_small = fonts.get_font('Roboto-Regular', 11)

        # Draw centered messages
        text.draw_centered_text(draw, msg1, y=35, font=font_big, color=0)
        text.draw_centered_text(draw, msg2, y=60, font=font_big, color=0)
        text.draw_centered_text(draw, "Touch to go back", y=110, font=font_small, color=0)

        # Display
        epd.displayPartial(epd.getbuffer(img))
        logger.info("Showing forbidden message")

        # Start touch detection
        touch = TouchHandler(gt, gt_dev)
        touch.start()

        try:
            while True:
                if check_exit_requested(gt_dev):
                    logger.info("Exit requested by menu")
                    break

                gt.GT_Scan(gt_dev, gt_old)

                if gt_dev.TouchpointFlag:
                    gt_dev.TouchpointFlag = 0
                    logger.info("Touch detected - exiting")
                    break

                time.sleep(0.1)
        finally:
            touch.stop()

    except Exception as e:
        logger.error(f"Error displaying forbidden message: {e}")
        raise
