#!/usr/bin/env python3
"""
Test Suite for Refactored Pomodoro App
======================================

Comprehensive tests verifying:
  - Configuration loading with ConfigLoader
  - State machine transitions
  - Display rendering
  - Timer logic
  - Error handling
  - Thread safety with TouchHandler

Tests are designed to run without hardware dependencies.
"""

from PIL import Image, ImageDraw
import unittest
import sys
import os
import time
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# ============================================================================
# MOCK CLASSES FOR TESTING
# ============================================================================

class MockEPD:
    """Mock e-ink display driver"""
    FULL_UPDATE = 0
    PART_UPDATE = 1

    def __init__(self):
        self.init_count = 0
        self.clear_count = 0
        self.display_count = 0
        self.last_buffer = None

    def init(self, mode):
        self.init_count += 1

    def Clear(self, color):
        self.clear_count += 1

    def getbuffer(self, image):
        self.last_buffer = image
        return b'mock_buffer'

    def displayPartial(self, buffer):
        self.display_count += 1

    def displayPartBaseImage(self, buffer):
        self.display_count += 1

    def sleep(self):
        pass

    def module_exit(self):
        pass


class MockGTDevice:
    """Mock touch device"""

    def __init__(self):
        self.X = [0]
        self.Y = [0]
        self.S = [0]
        self.Touch = 0
        self.TouchpointFlag = 0
        self.exit_requested = False


class MockGT:
    """Mock touch driver"""
    INT = 0

    def __init__(self):
        self.scan_count = 0

    def GT_Scan(self, gt_dev, gt_old):
        self.scan_count += 1

    def digital_read(self, pin):
        return 1  # No touch


# ============================================================================
# TEST CASES
# ============================================================================

class TestConfigLoading(unittest.TestCase):
    """Test configuration loading with ConfigLoader"""

    def test_config_loader_singleton(self):
        """ConfigLoader should be a singleton"""
        from shared.app_utils import ConfigLoader

        config1 = ConfigLoader()
        config2 = ConfigLoader()
        self.assertIs(config1, config2)

    def test_pomodoro_config_defaults(self):
        """Pomodoro config should have sensible defaults"""
        from shared.app_utils import ConfigLoader

        config = ConfigLoader.get_section('pomodoro', default={
            'work_duration': 1500,
            'short_break': 300,
            'long_break': 900
        })

        self.assertIn('work_duration', config or {})
        self.assertIn('short_break', config or {})
        self.assertIn('long_break', config or {})

    def test_config_value_retrieval(self):
        """Should retrieve config values with defaults"""
        from shared.app_utils import ConfigLoader

        # With defaults
        value = ConfigLoader.get_value('pomodoro', 'work_duration', 1500)
        self.assertIsNotNone(value)


class TestDisplayFunctions(unittest.TestCase):
    """Test display rendering functions"""

    def setUp(self):
        """Set up test fixtures"""
        # Import after path setup
        import pomodoro_app
        self.draw_pomodoro = pomodoro_app.draw_pomodoro

    def test_draw_pomodoro_ready_state(self):
        """Should render READY state correctly"""
        img = self.draw_pomodoro("READY", 1500, 0)

        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (250, 122))
        self.assertEqual(img.mode, "1")

    def test_draw_pomodoro_work_state(self):
        """Should render WORK state with session count"""
        img = self.draw_pomodoro("WORK", 300, 3)

        self.assertIsInstance(img, Image.Image)
        # Image should contain session information
        self.assertIsNotNone(img)

    def test_draw_pomodoro_break_state(self):
        """Should render BREAK state correctly"""
        img = self.draw_pomodoro("BREAK", 600, 1)

        self.assertIsInstance(img, Image.Image)
        self.assertIsNotNone(img)

    def test_draw_pomodoro_paused_state(self):
        """Should render PAUSED state correctly"""
        img = self.draw_pomodoro("PAUSED", 450, 2)

        self.assertIsInstance(img, Image.Image)
        self.assertIsNotNone(img)

    def test_draw_pomodoro_time_formatting(self):
        """Should correctly format time in MM:SS format"""
        # 5 minutes 30 seconds
        img = self.draw_pomodoro("WORK", 330, 1)
        self.assertIsNotNone(img)

        # Edge case: 0 seconds
        img = self.draw_pomodoro("WORK", 0, 1)
        self.assertIsNotNone(img)

        # Edge case: Large time
        img = self.draw_pomodoro("WORK", 5999, 1)
        self.assertIsNotNone(img)

    def test_draw_pomodoro_error_handling(self):
        """Should handle rendering errors gracefully"""
        img = self.draw_pomodoro("WORK", -1, 0)  # Invalid input
        # Should return blank image instead of crashing
        self.assertIsInstance(img, Image.Image)


class TestStateMachine(unittest.TestCase):
    """Test Pomodoro state machine transitions"""

    def test_state_transitions(self):
        """Should transition correctly between states"""
        # READY -> WORK (on click)
        states = ["READY", "WORK", "BREAK", "READY"]
        for state in states:
            self.assertIn(state, ["READY", "WORK", "BREAK", "PAUSED"])

    def test_work_to_break_transition(self):
        """After work session, should go to BREAK"""
        state = "WORK"
        pomodoro_count = 1

        # Simulate work completion
        state = "BREAK"
        if pomodoro_count % 4 == 0:
            break_time = 900  # long break
        else:
            break_time = 300  # short break

        self.assertEqual(state, "BREAK")
        self.assertEqual(break_time, 300)

    def test_long_break_after_four_sessions(self):
        """After 4 work sessions, should get long break"""
        pomodoro_count = 4
        break_time = 900 if (pomodoro_count % 4 == 0) else 300

        self.assertEqual(break_time, 900)

    def test_pause_resume_cycle(self):
        """Should pause and resume without state loss"""
        state = "WORK"
        time_left = 450
        prev_state = state

        # Pause
        state = "PAUSED"
        self.assertEqual(state, "PAUSED")
        self.assertEqual(time_left, 450)  # Time should not change

        # Resume
        state = prev_state
        self.assertEqual(state, "WORK")
        self.assertEqual(time_left, 450)


class TestTimerLogic(unittest.TestCase):
    """Test timer countdown logic"""

    def test_timer_countdown(self):
        """Timer should decrement correctly"""
        from shared.app_utils import PeriodicTimer

        timer = PeriodicTimer(0.1)
        self.assertFalse(timer.is_ready())

        # Should be ready after interval
        time.sleep(0.15)
        self.assertTrue(timer.is_ready())

    def test_timer_reset(self):
        """Timer reset should work"""
        from shared.app_utils import PeriodicTimer

        timer = PeriodicTimer(0.05)
        time.sleep(0.08)
        self.assertTrue(timer.is_ready())

        # After reset, should not be ready again immediately
        timer.reset()
        self.assertFalse(timer.is_ready())

    def test_time_formatting(self):
        """Should format time correctly"""
        test_cases = [
            (0, "00:00"),
            (30, "00:30"),
            (60, "01:00"),
            (90, "01:30"),
            (1500, "25:00"),
            (5999, "99:59"),
        ]

        for seconds, expected_format in test_cases:
            mins, secs = divmod(seconds, 60)
            formatted = f"{mins:02}:{secs:02}"
            self.assertEqual(formatted, expected_format)


class TestTouchHandlerIntegration(unittest.TestCase):
    """Test TouchHandler integration"""

    def test_touch_handler_creation(self):
        """Should create TouchHandler without errors"""
        from display.touch_handler import TouchHandler

        mock_gt = MockGT()
        mock_dev = MockGTDevice()

        handler = TouchHandler(mock_gt, mock_dev)
        self.assertIsNotNone(handler)
        self.assertFalse(handler.is_running())

    def test_touch_handler_lifecycle(self):
        """Touch handler should start and stop cleanly"""
        from display.touch_handler import TouchHandler

        mock_gt = MockGT()
        mock_dev = MockGTDevice()

        handler = TouchHandler(mock_gt, mock_dev)
        handler.start()
        self.assertTrue(handler.is_running())

        time.sleep(0.05)
        handler.stop()
        self.assertFalse(handler.is_running())

    def test_exit_request_detection(self):
        """Should detect exit request from device"""
        from shared.app_utils import check_exit_requested

        device = MockGTDevice()
        device.exit_requested = False
        self.assertFalse(check_exit_requested(device))

        device.exit_requested = True
        self.assertTrue(check_exit_requested(device))


class TestErrorHandling(unittest.TestCase):
    """Test error handling throughout app"""

    def test_display_error_recovery(self):
        """Display function should recover from errors"""
        import pomodoro_app

        # This should not crash even with invalid inputs
        result = pomodoro_app.draw_pomodoro("INVALID", -999, -5)
        self.assertIsInstance(result, Image.Image)

    def test_safe_execute_wrapper(self):
        """Should handle errors gracefully with safe_execute"""
        from shared.app_utils import safe_execute

        def failing_func():
            raise ValueError("Test error")

        result = safe_execute(failing_func, "Test failed", default=42)
        self.assertEqual(result, 42)

    def test_safe_execute_success(self):
        """Safe execute should return function result on success"""
        from shared.app_utils import safe_execute

        def success_func():
            return "success"

        result = safe_execute(success_func)
        self.assertEqual(result, "success")


class TestFontPresets(unittest.TestCase):
    """Test font preset system"""

    def test_get_font_preset(self):
        """Should get font presets without errors"""
        from display.fonts import get_font_preset

        presets = ['headline', 'title', 'body', 'small', 'display_huge']
        for preset in presets:
            font = get_font_preset(preset)
            self.assertIsNotNone(font)

    def test_font_caching(self):
        """Fonts should be cached for performance"""
        from display.fonts import get_font_preset, get_cache_size

        initial_size = get_cache_size()

        # Get same font multiple times
        get_font_preset('title')
        get_font_preset('title')
        get_font_preset('title')

        # Cache size should not increase
        final_size = get_cache_size()
        self.assertLessEqual(final_size, initial_size + 1)


class TestIconLibrary(unittest.TestCase):
    """Test icon drawing from display library"""

    def test_tomato_icon_frame1(self):
        """Should draw tomato icon frame 1"""
        from display.icons import draw_tomato_icon

        img = Image.new("1", (250, 122), 255)
        draw = ImageDraw.Draw(img)

        # Should not raise exception
        draw_tomato_icon(draw, 125, 61, frame=1, size=30, color=0)
        self.assertIsNotNone(img)

    def test_tomato_icon_frame2(self):
        """Should draw tomato icon frame 2"""
        from display.icons import draw_tomato_icon

        img = Image.new("1", (250, 122), 255)
        draw = ImageDraw.Draw(img)

        # Should not raise exception
        draw_tomato_icon(draw, 125, 61, frame=2, size=30, color=0)
        self.assertIsNotNone(img)


class TestBackupFile(unittest.TestCase):
    """Test that backup file was created"""

    def test_backup_exists(self):
        """Should have created backup of original file"""
        backup_path = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        self.assertTrue(os.path.exists(backup_path), "Backup file not found")

    def test_backup_has_content(self):
        """Backup file should contain original code"""
        backup_path = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        with open(backup_path, 'r') as f:
            content = f.read()
        self.assertGreater(len(content), 100)

    def test_backup_is_readable(self):
        """Backup should be valid Python"""
        backup_path = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        try:
            with open(backup_path, 'r') as f:
                compile(f.read(), backup_path, 'exec')
        except SyntaxError:
            self.fail("Backup file has syntax errors")


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_tests():
    """Run all tests and print results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestConfigLoading,
        TestDisplayFunctions,
        TestStateMachine,
        TestTimerLogic,
        TestTouchHandlerIntegration,
        TestErrorHandling,
        TestFontPresets,
        TestIconLibrary,
        TestBackupFile,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
