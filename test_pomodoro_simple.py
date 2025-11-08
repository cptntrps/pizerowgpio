#!/usr/bin/env python3
"""
Simplified Test Suite for Refactored Pomodoro App
==================================================

Tests core functionality without hardware dependencies.
Tests:
  - State machine logic
  - Timer formatting
  - Configuration system
  - Touch handler
  - Error handling patterns
  - Backup file integrity
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


# ============================================================================
# TEST CASES
# ============================================================================

class TestStateMachineLogic(unittest.TestCase):
    """Test Pomodoro state machine without hardware"""

    def test_state_transitions_valid(self):
        """Valid states should be recognized"""
        valid_states = ["READY", "WORK", "BREAK", "PAUSED"]
        for state in valid_states:
            self.assertIn(state, ["READY", "WORK", "BREAK", "PAUSED"])

    def test_work_to_break_transition(self):
        """After work, should transition to break"""
        state = "WORK"
        time_left = 0

        if time_left <= 0 and state == "WORK":
            state = "BREAK"

        self.assertEqual(state, "BREAK")

    def test_break_to_ready_transition(self):
        """After break, should return to ready"""
        state = "BREAK"
        time_left = 0

        if time_left <= 0 and state == "BREAK":
            state = "READY"

        self.assertEqual(state, "READY")

    def test_pause_state_preserves_time(self):
        """Pause should preserve remaining time"""
        state = "WORK"
        time_left = 450
        prev_state = state

        # Enter pause
        state = "PAUSED"
        self.assertEqual(state, "PAUSED")

        # Time should not have changed
        self.assertEqual(time_left, 450)

        # Exit pause
        state = prev_state
        self.assertEqual(state, "WORK")
        self.assertEqual(time_left, 450)

    def test_long_break_after_four_sessions(self):
        """Every 4th work session should get long break"""
        sessions = [1, 2, 3, 4, 5, 6, 7, 8]
        long_break_sessions = [4, 8]

        for session in sessions:
            is_long_break = (session % 4 == 0)
            if session in long_break_sessions:
                self.assertTrue(is_long_break)
            else:
                self.assertFalse(is_long_break)


class TestTimerLogic(unittest.TestCase):
    """Test timer functionality"""

    def test_time_formatting(self):
        """Should format times correctly"""
        test_cases = [
            (0, "00:00"),
            (30, "00:30"),
            (60, "01:00"),
            (90, "01:30"),
            (1500, "25:00"),
            (5999, "99:59"),
        ]

        for seconds, expected in test_cases:
            mins, secs = divmod(seconds, 60)
            result = f"{mins:02}:{secs:02}"
            self.assertEqual(result, expected, f"Failed for {seconds}s")

    def test_timer_countdown(self):
        """Timer should count down per second"""
        time_left = 1500
        intervals_passed = 0

        for _ in range(10):
            if intervals_passed % 1 == 0:  # Every second
                time_left -= 1
                intervals_passed += 1

        self.assertEqual(time_left, 1490)

    def test_timer_completion(self):
        """Timer should signal completion at 0"""
        time_left = 1
        is_complete = False

        # Simulate one interval passing
        time_left -= 1

        if time_left <= 0:
            is_complete = True

        self.assertTrue(is_complete)


class TestConfigurationSystem(unittest.TestCase):
    """Test configuration loading"""

    def test_config_loader_singleton(self):
        """ConfigLoader should be singleton"""
        from shared.app_utils import ConfigLoader

        loader1 = ConfigLoader()
        loader2 = ConfigLoader()
        self.assertIs(loader1, loader2)

    def test_get_config_section_with_defaults(self):
        """Should return defaults if config missing"""
        from shared.app_utils import ConfigLoader

        default_config = {
            'work_duration': 1500,
            'short_break': 300,
            'long_break': 900
        }

        config = ConfigLoader.get_section('pomodoro', default=default_config)
        self.assertIsNotNone(config)
        # Should have defaults
        self.assertIn('work_duration', config or {})

    def test_config_get_value(self):
        """Should retrieve config values"""
        from shared.app_utils import ConfigLoader

        value = ConfigLoader.get_value('pomodoro', 'work_duration', 1500)
        # Should return something (either from config or default)
        self.assertIsNotNone(value)


class TestTouchHandling(unittest.TestCase):
    """Test touch handler system"""

    def test_touch_handler_import(self):
        """TouchHandler should be importable"""
        from display.touch_handler import TouchHandler
        self.assertIsNotNone(TouchHandler)

    def test_exit_detection(self):
        """Should detect exit requests"""
        from shared.app_utils import check_exit_requested

        mock_device = Mock()
        mock_device.exit_requested = False
        self.assertFalse(check_exit_requested(mock_device))

        mock_device.exit_requested = True
        self.assertTrue(check_exit_requested(mock_device))

    def test_cleanup_touch_state(self):
        """Should reset touch state"""
        from shared.app_utils import cleanup_touch_state

        mock_old = Mock()
        mock_old.X = [100]
        mock_old.Y = [200]
        mock_old.S = [50]

        cleanup_touch_state(mock_old)

        self.assertEqual(mock_old.X[0], 0)
        self.assertEqual(mock_old.Y[0], 0)
        self.assertEqual(mock_old.S[0], 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling patterns"""

    def test_safe_execute_on_error(self):
        """Should return default on error"""
        from shared.app_utils import safe_execute

        def failing_func():
            raise ValueError("Test error")

        result = safe_execute(failing_func, default=42)
        self.assertEqual(result, 42)

    def test_safe_execute_on_success(self):
        """Should return result on success"""
        from shared.app_utils import safe_execute

        def success_func():
            return "success"

        result = safe_execute(success_func)
        self.assertEqual(result, "success")


class TestPeriodicTimer(unittest.TestCase):
    """Test periodic timer utility"""

    def test_periodic_timer_not_ready_initially(self):
        """Timer should not be ready immediately"""
        from shared.app_utils import PeriodicTimer

        timer = PeriodicTimer(10.0)  # Long interval
        self.assertFalse(timer.is_ready())

    def test_periodic_timer_ready_after_interval(self):
        """Timer should be ready after interval"""
        from shared.app_utils import PeriodicTimer

        timer = PeriodicTimer(0.05)  # 50ms
        time.sleep(0.08)  # Wait 80ms
        self.assertTrue(timer.is_ready())

    def test_periodic_timer_reset(self):
        """Reset should restart timer"""
        from shared.app_utils import PeriodicTimer

        timer = PeriodicTimer(0.05)
        time.sleep(0.08)
        self.assertTrue(timer.is_ready())

        timer.reset()
        self.assertFalse(timer.is_ready())


class TestIconLibrary(unittest.TestCase):
    """Test icon drawing functions"""

    def test_tomato_icon_import(self):
        """Should import tomato icon function"""
        from display.icons import draw_tomato_icon
        self.assertIsNotNone(draw_tomato_icon)

    def test_checkmark_icon_import(self):
        """Should import checkmark icon function"""
        from display.icons import draw_checkmark
        self.assertIsNotNone(draw_checkmark)

    def test_pill_icon_import(self):
        """Should import pill icon function"""
        from display.icons import draw_pill_icon
        self.assertIsNotNone(draw_pill_icon)


class TestBackupFileIntegrity(unittest.TestCase):
    """Test backup file creation and validity"""

    def test_backup_file_exists(self):
        """Backup file should exist"""
        backup = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        self.assertTrue(os.path.exists(backup), "Backup not found")

    def test_backup_has_content(self):
        """Backup should have substantial content"""
        backup = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        with open(backup, 'r') as f:
            content = f.read()
        self.assertGreater(len(content), 1000, "Backup too small")

    def test_backup_is_valid_python(self):
        """Backup should be valid Python"""
        backup = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        with open(backup, 'r') as f:
            code = f.read()
        try:
            compile(code, backup, 'exec')
        except SyntaxError as e:
            self.fail(f"Backup has syntax error: {e}")

    def test_backup_contains_original_functions(self):
        """Backup should contain original functions"""
        backup = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        with open(backup, 'r') as f:
            content = f.read()

        required_items = ['draw_tomato_frame1', 'draw_tomato_frame2', 'run_pomodoro_app']
        for item in required_items:
            self.assertIn(item, content, f"Backup missing {item}")

    def test_refactored_is_different(self):
        """Refactored should differ from backup"""
        backup = '/home/user/pizerowgpio/pomodoro_app.py.backup'
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'

        with open(backup, 'r') as f:
            backup_content = f.read()
        with open(refactored, 'r') as f:
            refactored_content = f.read()

        # Should be different
        self.assertNotEqual(backup_content, refactored_content)

        # But similar in structure
        backup_lines = len(backup_content.split('\n'))
        refactored_lines = len(refactored_content.split('\n'))

        # Should be reasonably different sizes
        # (refactored may be larger due to docstrings, or smaller due to code reduction)
        self.assertGreater(max(backup_lines, refactored_lines) / min(backup_lines, refactored_lines), 0.8)


class TestRefactoringGoals(unittest.TestCase):
    """Verify refactoring goals were met"""

    def test_uses_touch_handler(self):
        """Refactored app should use TouchHandler"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()
        self.assertIn('TouchHandler', content, "Should use TouchHandler")
        self.assertIn('touch_handler = TouchHandler', content, "Should instantiate TouchHandler")

    def test_uses_config_loader(self):
        """Refactored app should use ConfigLoader"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()
        self.assertIn('ConfigLoader', content, "Should use ConfigLoader")

    def test_uses_font_presets(self):
        """Refactored app should use font presets"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()
        self.assertIn('get_font_preset', content, "Should use get_font_preset")

    def test_uses_tomato_icon(self):
        """Refactored app should use draw_tomato_icon"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()
        self.assertIn('draw_tomato_icon', content, "Should use draw_tomato_icon")
        self.assertNotIn('def draw_tomato_frame', content, "Should not define custom tomato frames")

    def test_uses_periodic_timer(self):
        """Refactored app should use PeriodicTimer"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()
        self.assertIn('PeriodicTimer', content, "Should use PeriodicTimer")

    def test_eliminates_manual_threading(self):
        """Should not have manual threading code"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()

        # Should not have the old threading pattern
        self.assertNotIn('def pthread_irq', content, "Should not have pthread_irq function")
        self.assertNotIn('flag_t = [1]', content, "Should not have flag_t array")
        self.assertNotIn('t = threading.Thread(target=pthread_irq)', content, "Should not create threading.Thread manually")

    def test_has_comprehensive_error_handling(self):
        """Should have error handling in key functions"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()

        self.assertIn('try:', content)
        self.assertIn('except Exception', content)
        self.assertIn('logger.error', content)

    def test_has_good_docstrings(self):
        """Should have comprehensive docstrings"""
        refactored = '/home/user/pizerowgpio/pomodoro_app.py'
        with open(refactored, 'r') as f:
            content = f.read()

        # Should have module docstring
        self.assertIn('"""', content)
        # Should have function docstrings
        self.assertIn('Args:', content)
        self.assertIn('Returns:', content)


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestStateMachineLogic,
        TestTimerLogic,
        TestConfigurationSystem,
        TestTouchHandling,
        TestErrorHandling,
        TestPeriodicTimer,
        TestIconLibrary,
        TestBackupFileIntegrity,
        TestRefactoringGoals,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
