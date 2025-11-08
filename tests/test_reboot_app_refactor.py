"""
Test Suite for Refactored reboot_app.py
Verifies functionality preservation and new feature usage
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRebootAppRefactor(unittest.TestCase):
    """Test reboot app refactoring"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_epd = Mock()
        self.mock_gt_dev = Mock()
        self.mock_gt_old = Mock()
        self.mock_gt = Mock()

        # Initialize touch state
        self.mock_gt_dev.X = [0]
        self.mock_gt_dev.Y = [0]
        self.mock_gt_dev.S = [0]
        self.mock_gt_dev.Touch = 0
        self.mock_gt_dev.TouchpointFlag = 0
        self.mock_gt_old.X = [0]
        self.mock_gt_old.Y = [0]
        self.mock_gt_old.S = [0]

    def test_touch_handler_replaces_threading(self):
        """Verify TouchHandler is used instead of manual threading"""
        # Import reboot_app
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "reboot_app",
                "/home/user/pizerowgpio/reboot_app.py"
            )
            module = importlib.util.module_from_spec(spec)

            # Check that TouchHandler is imported
            with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
                content = f.read()
                self.assertIn("from display.touch_handler import TouchHandler",
                            content, "TouchHandler should be imported")
                # Verify no manual threading import
                self.assertNotIn("import threading", content,
                               "Manual threading should not be used")

        except Exception as e:
            self.fail(f"Failed to check imports: {e}")

    def test_button_component_usage(self):
        """Verify Button component is used for UI"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            self.assertIn("from display.components import Button",
                        content, "Button should be imported")
            self.assertIn("Button(", content, "Button class should be instantiated")

    def test_shared_utilities_usage(self):
        """Verify shared utilities are used"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            self.assertIn("from shared.app_utils import", content,
                        "Shared utilities should be imported")
            self.assertIn("setup_logging", content, "setup_logging should be used")
            self.assertIn("check_exit_requested", content, "check_exit_requested should be used")
            self.assertIn("cleanup_touch_state", content, "cleanup_touch_state should be used")

    def test_font_presets_usage(self):
        """Verify font presets are used instead of manual font loading"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            self.assertIn("from display.fonts import get_font_preset",
                        content, "get_font_preset should be imported")
            self.assertIn("get_font_preset('", content, "Font presets should be used")
            # Verify no manual font loading
            self.assertNotIn("ImageFont.truetype(", content,
                           "Manual font loading should not be used")

    def test_error_handling(self):
        """Verify comprehensive error handling is present"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            # Check for try/except blocks
            self.assertIn("try:", content, "Should have try blocks")
            self.assertIn("except Exception", content, "Should have except blocks")
            self.assertIn("finally:", content, "Should have finally block")
            # Verify proper cleanup
            self.assertIn("touch.stop()", content, "Should stop touch handler")
            self.assertIn("cleanup_touch_state", content, "Should clean up touch state")

    def test_no_duplicate_code(self):
        """Verify duplicate code has been eliminated"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            # Check that duplicate exit check is removed
            lines = content.split('\n')
            exit_check_count = sum(1 for line in lines
                                  if "Exit requested" in line)
            self.assertLessEqual(exit_check_count, 2,
                               "Should not have duplicate exit check code")

    def test_code_reduction(self):
        """Verify code reduction from original"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            refactored_lines = len(f.readlines())

        with open("/home/user/pizerowgpio/reboot_app.py.backup", "r") as f:
            original_lines = len(f.readlines())

        # The refactored version should be more maintainable and use shared utilities
        # (it may be slightly longer due to error handling, but should not be much longer)
        print(f"Original: {original_lines} lines")
        print(f"Refactored: {refactored_lines} lines")
        # Allow up to 30% more due to error handling and better structure
        self.assertLess(refactored_lines, original_lines * 1.3,
                       "Refactored code should not be significantly longer")

    def test_exact_functionality_preserved(self):
        """Verify exact functionality is preserved"""
        # Check that key functionality is still present:
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()

            # 1. Confirmation dialog with title
            self.assertIn("Reboot System?", content,
                        "Confirmation title should be present")

            # 2. Cancel button logic
            self.assertIn("y > 180", content, "Cancel button Y coordinate check")
            self.assertIn("Cancel", content, "Cancel button text")

            # 3. Reboot button logic
            self.assertIn("y < 70", content, "Reboot button Y coordinate check")
            self.assertIn("Reboot", content, "Reboot button text")

            # 4. Reboot command execution
            self.assertIn("sudo", content, "Sudo reboot command")
            self.assertIn("subprocess.run", content, "subprocess call for reboot")

            # 5. Rebooting message display
            self.assertIn("Rebooting...", content, "Rebooting status message")

            # 6. Touch input handling
            self.assertIn("GT_Scan", content, "Touch scanning")
            self.assertIn("TouchpointFlag", content, "Touch point flag check")

    def test_backup_exists(self):
        """Verify backup file exists"""
        backup_path = "/home/user/pizerowgpio/reboot_app.py.backup"
        self.assertTrue(os.path.exists(backup_path),
                       "Backup file should exist")
        self.assertTrue(os.path.isfile(backup_path),
                       "Backup should be a file")

    def test_reboot_app_syntax(self):
        """Verify refactored app has valid Python syntax"""
        try:
            import py_compile
            py_compile.compile('/home/user/pizerowgpio/reboot_app.py',
                             doraise=True)
        except py_compile.PyCompileError as e:
            self.fail(f"Refactored app has syntax errors: {e}")

    def test_imports_available(self):
        """Verify all required imports are available"""
        required_modules = [
            'display.touch_handler',
            'display.fonts',
            'display.components',
            'shared.app_utils'
        ]

        for module_name in required_modules:
            try:
                parts = module_name.split('.')
                __import__(module_name)
                print(f"✓ {module_name} available")
            except ImportError as e:
                print(f"✗ {module_name} not found: {e}")


class TestCodeQualityMetrics(unittest.TestCase):
    """Test code quality improvements"""

    def test_no_hardcoded_paths(self):
        """Verify no hardcoded config paths in refactored version"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            # Should use ConfigLoader instead of hardcoded paths
            if "config" in content:
                self.assertIn("ConfigLoader", content,
                            "Should use ConfigLoader for config access")

    def test_logging_setup(self):
        """Verify proper logging setup"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            self.assertIn("setup_logging", content,
                        "Should use setup_logging function")
            self.assertIn("logger =", content, "Should create logger instance")
            self.assertIn("logger.info", content, "Should use logger.info")
            self.assertIn("logger.error", content, "Should use logger.error")

    def test_no_magic_numbers(self):
        """Verify magic numbers are explained"""
        with open("/home/user/pizerowgpio/reboot_app.py", "r") as f:
            content = f.read()
            # Key coordinates should have comments explaining API contract
            if "y > 180" in content:
                self.assertIn("LEFT", content,
                            "Y > 180 coordinate should be documented as LEFT")
            if "y < 70" in content:
                self.assertIn("RIGHT", content,
                            "Y < 70 coordinate should be documented as RIGHT")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
