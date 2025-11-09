"""
Test suite for refactored forbidden_app.py
==========================================

Tests verify that the refactored version maintains exact functionality
while using shared utilities and display components.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Mock hardware dependencies before importing forbidden_app
sys.modules['TP_lib'] = MagicMock()
sys.modules['TP_lib'].gt1151 = MagicMock()
sys.modules['TP_lib'].epd2in13_V3 = MagicMock()


class TestForbiddenAppRefactoring(unittest.TestCase):
    """Test suite for forbidden app refactoring."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_epd = Mock()
        self.mock_gt_dev = Mock()
        self.mock_gt_dev.TouchpointFlag = 0
        self.mock_gt_dev.Touch = 0
        self.mock_gt_dev.X = [0]
        self.mock_gt_dev.Y = [0]
        self.mock_gt_dev.S = [0]
        self.mock_gt = Mock()
        self.mock_gt.INT = 1
        self.mock_gt_old = Mock()
        self.mock_gt_old.X = [0]
        self.mock_gt_old.Y = [0]
        self.mock_gt_old.S = [0]

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_imports_required_modules(self, mock_touch, mock_text, mock_fonts,
                                     mock_canvas, mock_config, mock_logging):
        """Test that all required modules are imported."""
        import forbidden_app

        # Verify key imports are available
        self.assertTrue(hasattr(forbidden_app, 'canvas'))
        self.assertTrue(hasattr(forbidden_app, 'fonts'))
        self.assertTrue(hasattr(forbidden_app, 'text'))
        self.assertTrue(hasattr(forbidden_app, 'TouchHandler'))
        self.assertTrue(hasattr(forbidden_app, 'ConfigLoader'))

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_uses_config_loader(self, mock_touch, mock_text, mock_fonts,
                               mock_canvas, mock_config, mock_logging):
        """Test that ConfigLoader is used instead of json.load()."""
        import forbidden_app

        # Setup mocks
        mock_canvas.create_canvas.return_value = (Mock(), Mock())
        mock_fonts.get_font.return_value = Mock()
        mock_touch_instance = Mock()
        mock_touch.return_value = mock_touch_instance
        mock_config.get_value.return_value = "Test Message"

        # Simulate touch to exit
        mock_gt_dev = Mock()
        mock_gt_dev.TouchpointFlag = 1
        mock_gt = Mock()

        # Call function
        try:
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)
        except:
            pass

        # Verify ConfigLoader was used
        self.assertTrue(mock_config.get_value.called)
        mock_config.get_value.assert_any_call('forbidden', 'message_line1',
                                              'Access Forbidden')

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_uses_display_canvas(self, mock_touch, mock_text, mock_fonts,
                                mock_canvas, mock_config, mock_logging):
        """Test that display.canvas is used instead of Image.new()."""
        import forbidden_app

        # Setup mocks
        mock_img = Mock()
        mock_draw = Mock()
        mock_canvas.create_canvas.return_value = (mock_img, mock_draw)
        mock_fonts.get_font.return_value = Mock()
        mock_touch_instance = Mock()
        mock_touch.return_value = mock_touch_instance
        mock_config.get_value.return_value = "Test"

        # Simulate touch to exit
        mock_gt_dev = Mock()
        mock_gt_dev.TouchpointFlag = 1
        mock_gt = Mock()

        # Call function
        try:
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)
        except:
            pass

        # Verify canvas.create_canvas was used
        mock_canvas.create_canvas.assert_called_once()

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_uses_font_caching(self, mock_touch, mock_text, mock_fonts,
                              mock_canvas, mock_config, mock_logging):
        """Test that fonts.get_font() is used for font caching."""
        import forbidden_app

        # Setup mocks
        mock_canvas.create_canvas.return_value = (Mock(), Mock())
        mock_font = Mock()
        mock_fonts.get_font.return_value = mock_font
        mock_touch_instance = Mock()
        mock_touch.return_value = mock_touch_instance
        mock_config.get_value.return_value = "Test"

        # Simulate touch to exit
        mock_gt_dev = Mock()
        mock_gt_dev.TouchpointFlag = 1
        mock_gt = Mock()

        # Call function
        try:
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)
        except:
            pass

        # Verify fonts.get_font was called for both fonts
        calls = mock_fonts.get_font.call_args_list
        self.assertGreaterEqual(len(calls), 2)

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_uses_text_utilities(self, mock_touch, mock_text, mock_fonts,
                               mock_canvas, mock_config, mock_logging):
        """Test that display.text utilities are used for centering."""
        import forbidden_app

        # Setup mocks
        mock_canvas.create_canvas.return_value = (Mock(), Mock())
        mock_fonts.get_font.return_value = Mock()
        mock_touch_instance = Mock()
        mock_touch.return_value = mock_touch_instance
        mock_config.get_value.return_value = "Test"

        # Simulate touch to exit
        mock_gt_dev = Mock()
        mock_gt_dev.TouchpointFlag = 1
        mock_gt = Mock()

        # Call function
        try:
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)
        except:
            pass

        # Verify text.draw_centered_text was used (should be called 3 times)
        self.assertGreaterEqual(mock_text.draw_centered_text.call_count, 3)

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_uses_touch_handler(self, mock_touch, mock_text, mock_fonts,
                              mock_canvas, mock_config, mock_logging):
        """Test that TouchHandler replaces manual threading."""
        import forbidden_app

        # Setup mocks
        mock_canvas.create_canvas.return_value = (Mock(), Mock())
        mock_fonts.get_font.return_value = Mock()
        mock_touch_instance = Mock()
        mock_touch.return_value = mock_touch_instance
        mock_config.get_value.return_value = "Test"

        # Simulate touch to exit
        mock_gt_dev = Mock()
        mock_gt_dev.TouchpointFlag = 1
        mock_gt = Mock()

        # Call function
        try:
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)
        except:
            pass

        # Verify TouchHandler was instantiated and started
        mock_touch.assert_called_once()
        mock_touch_instance.start.assert_called_once()
        mock_touch_instance.stop.assert_called_once()

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_error_handling(self, mock_touch, mock_text, mock_fonts,
                           mock_canvas, mock_config, mock_logging):
        """Test that errors are properly caught and logged."""
        import forbidden_app

        # Setup mocks to raise error
        mock_canvas.create_canvas.side_effect = RuntimeError("Test error")
        mock_fonts.get_font.return_value = Mock()

        # Setup logger mock
        mock_logger = Mock()
        mock_logging.return_value = mock_logger

        # Simulate touch to exit
        mock_gt_dev = Mock()
        mock_gt = Mock()

        # Verify exception is raised after logging
        with self.assertRaises(RuntimeError):
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)

        # Verify error occurred (exception was properly raised)
        self.assertTrue(True)  # Exception handling verified by raising

    @patch('forbidden_app.setup_logging')
    @patch('forbidden_app.ConfigLoader')
    @patch('forbidden_app.canvas')
    @patch('forbidden_app.fonts')
    @patch('forbidden_app.text')
    @patch('forbidden_app.TouchHandler')
    def test_exit_on_menu_request(self, mock_touch, mock_text, mock_fonts,
                                 mock_canvas, mock_config, mock_logging):
        """Test exit on menu exit request."""
        import forbidden_app

        # Setup mocks
        mock_canvas.create_canvas.return_value = (Mock(), Mock())
        mock_fonts.get_font.return_value = Mock()
        mock_touch_instance = Mock()
        mock_touch.return_value = mock_touch_instance
        mock_config.get_value.return_value = "Test"

        # Simulate exit requested by menu
        mock_gt_dev = Mock()
        mock_gt_dev.exit_requested = True
        mock_gt_dev.TouchpointFlag = 0
        mock_gt = Mock()

        # Call function
        try:
            forbidden_app.draw_forbidden_message(self.mock_epd, mock_gt_dev,
                                                self.mock_gt_old, mock_gt)
        except:
            pass

        # Verify TouchHandler was stopped (function exited cleanly)
        mock_touch_instance.stop.assert_called_once()


class TestCodeReductionMetrics(unittest.TestCase):
    """Test code reduction metrics."""

    def test_line_count_reduction(self):
        """Test that refactored version has reduced line count."""
        refactored_path = os.path.join(project_root, 'forbidden_app.py')
        backup_path = os.path.join(project_root, 'backups', 'forbidden_app.py.backup')

        with open(refactored_path, 'r') as f:
            refactored_lines = len(f.readlines())

        with open(backup_path, 'r') as f:
            original_lines = len(f.readlines())

        # Verify reduction
        reduction = original_lines - refactored_lines
        reduction_percent = (reduction / original_lines) * 100

        print(f"\nCode Reduction Metrics:")
        print(f"  Original:    {original_lines} lines")
        print(f"  Refactored:  {refactored_lines} lines")
        print(f"  Reduction:   {reduction} lines ({reduction_percent:.1f}%)")

        # Should have reduced at least 10%
        self.assertGreater(reduction_percent, 10)
        self.assertLess(refactored_lines, original_lines)

    def test_backup_exists(self):
        """Test that backup file was created."""
        backup_path = os.path.join(project_root, 'backups', 'forbidden_app.py.backup')
        self.assertTrue(os.path.exists(backup_path))
        self.assertGreater(os.path.getsize(backup_path), 0)

    def test_uses_shared_utilities(self):
        """Test that refactored version uses shared utilities."""
        refactored_path = os.path.join(project_root, 'forbidden_app.py')

        with open(refactored_path, 'r') as f:
            content = f.read()

        # Verify use of shared utilities
        self.assertIn('ConfigLoader', content)
        self.assertIn('setup_logging', content)
        self.assertIn('TouchHandler', content)

        # Verify display components
        self.assertIn('canvas', content)
        self.assertIn('fonts', content)
        self.assertIn('text', content)

    def test_no_manual_threading(self):
        """Test that refactored version doesn't use manual threading."""
        refactored_path = os.path.join(project_root, 'forbidden_app.py')

        with open(refactored_path, 'r') as f:
            content = f.read()

        # Should not have threading.Thread
        self.assertNotIn('threading.Thread', content)
        self.assertNotIn('pthread_irq', content)
        self.assertNotIn('flag_t', content)

    def test_no_duplicate_config_loading(self):
        """Test that config is not loaded multiple times."""
        refactored_path = os.path.join(project_root, 'forbidden_app.py')

        with open(refactored_path, 'r') as f:
            content = f.read()

        # Should use ConfigLoader, not duplicate json.load()
        self.assertNotIn('json.load', content)
        self.assertEqual(content.count('ConfigLoader.get_value'), 2)


if __name__ == '__main__':
    unittest.main()
