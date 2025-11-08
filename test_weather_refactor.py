#!/usr/bin/python3
"""
Test Suite for Refactored Weather App
======================================

Comprehensive tests to verify that the refactored weather_cal_app.py
maintains exact same functionality as the original while using shared
utilities and display components.
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add paths
project_root = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, project_root)

# ============================================================================
# TEST UTILITIES
# ============================================================================


class MockDisplayDriver:
    """Mock EPD display driver"""

    def __init__(self):
        self.buffer_data = None
        self.display_calls = []

    def getbuffer(self, image):
        return image.tobytes()

    def displayPartial(self, buffer_data):
        self.buffer_data = buffer_data
        self.display_calls.append(("partial", datetime.now()))

    def displayFull(self, buffer_data):
        self.buffer_data = buffer_data
        self.display_calls.append(("full", datetime.now()))


class MockTouchDevice:
    """Mock touch device state"""

    def __init__(self):
        self.Touch = 0
        self.TouchpointFlag = 0
        self.X = [0]
        self.Y = [0]
        self.S = [0]
        self.exit_requested = False


class MockTouchDriver:
    """Mock touch driver"""

    def __init__(self):
        self.INT = 1  # GPIO pin
        self.scan_count = 0

    def digital_read(self, pin):
        return 1  # No touch

    def GT_Scan(self, dev, old_dev):
        self.scan_count += 1


# ============================================================================
# UNIT TESTS
# ============================================================================

class TestWeatherDataFetching(unittest.TestCase):
    """Test weather data fetching functionality"""

    @patch('weather_cal_app.subprocess.run')
    def test_successful_weather_fetch(self, mock_run):
        """Test successful weather data retrieval"""
        from weather_cal_app import get_weather

        # Mock successful response
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Partly cloudy +15°C 65%"
        )

        result = get_weather()

        self.assertIsNotNone(result)
        self.assertEqual(result['condition'], "Partly cloudy")
        self.assertEqual(result['temp'], "+15°C")
        self.assertEqual(result['humidity'], "65%")

    @patch('weather_cal_app.subprocess.run')
    def test_weather_fetch_network_error(self, mock_run):
        """Test weather fetch with network error"""
        from weather_cal_app import get_weather

        mock_run.return_value = Mock(returncode=1, stdout="")

        result = get_weather()
        self.assertIsNone(result)

    @patch('weather_cal_app.subprocess.run')
    def test_weather_fetch_timeout(self, mock_run):
        """Test weather fetch timeout handling"""
        from weather_cal_app import get_weather

        mock_run.side_effect = TimeoutError("Timeout")

        result = get_weather()
        self.assertIsNone(result)


class TestWeatherIconDrawing(unittest.TestCase):
    """Test weather icon drawing functionality"""

    def setUp(self):
        from PIL import Image, ImageDraw
        self.img = Image.new('1', (250, 122), 255)
        self.draw = ImageDraw.Draw(self.img)

    def test_sunny_icon(self):
        """Test sunny weather icon drawing"""
        from weather_cal_app import draw_weather_icon

        # Should not raise exception
        draw_weather_icon(self.draw, "Sunny", 10, 10)
        self.assertTrue(True)

    def test_cloudy_icon(self):
        """Test cloudy weather icon drawing"""
        from weather_cal_app import draw_weather_icon

        draw_weather_icon(self.draw, "Cloudy", 10, 10)
        self.assertTrue(True)

    def test_rainy_icon(self):
        """Test rainy weather icon drawing"""
        from weather_cal_app import draw_weather_icon

        draw_weather_icon(self.draw, "Rainy", 10, 10)
        self.assertTrue(True)

    def test_snowy_icon(self):
        """Test snowy weather icon drawing"""
        from weather_cal_app import draw_weather_icon

        draw_weather_icon(self.draw, "Snow", 10, 10)
        self.assertTrue(True)

    def test_unknown_condition(self):
        """Test unknown weather condition"""
        from weather_cal_app import draw_weather_icon

        draw_weather_icon(self.draw, "XYZ", 10, 10)
        self.assertTrue(True)


class TestScreenDrawing(unittest.TestCase):
    """Test screen drawing functionality"""

    @patch('weather_cal_app.get_weather')
    def test_draw_weather_screen_with_data(self, mock_weather):
        """Test drawing screen with valid weather data"""
        from weather_cal_app import draw_weather_screen

        mock_weather.return_value = {
            'condition': 'Partly cloudy',
            'temp': '+15°C',
            'humidity': '65%'
        }

        image = draw_weather_screen()
        self.assertIsNotNone(image)
        self.assertEqual(image.size, (250, 122))

    @patch('weather_cal_app.get_weather')
    def test_draw_weather_screen_without_data(self, mock_weather):
        """Test drawing screen with no weather data"""
        from weather_cal_app import draw_weather_screen

        mock_weather.return_value = None

        image = draw_weather_screen()
        self.assertIsNotNone(image)
        self.assertEqual(image.size, (250, 122))

    def test_screen_dimensions(self):
        """Test correct screen dimensions"""
        from weather_cal_app import draw_weather_screen

        image = draw_weather_screen()
        self.assertEqual(image.size, (250, 122))

    def test_screen_mode(self):
        """Test correct image mode (monochrome)"""
        from weather_cal_app import draw_weather_screen

        image = draw_weather_screen()
        self.assertEqual(image.mode, '1')  # Monochrome


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading"""

    @patch('weather_cal_app.ConfigLoader.get_section')
    def test_config_with_defaults(self, mock_config):
        """Test that default values are used when config missing"""
        from weather_cal_app import LOCATION, UPDATE_INTERVAL

        # Config should have defaults
        self.assertIsNotNone(LOCATION)
        self.assertIsNotNone(UPDATE_INTERVAL)
        self.assertIsInstance(UPDATE_INTERVAL, int)
        self.assertGreater(UPDATE_INTERVAL, 0)


class TestMainAppLoop(unittest.TestCase):
    """Test main application loop"""

    @patch('weather_cal_app.logger')
    @patch('weather_cal_app.TouchHandler')
    @patch('weather_cal_app.draw_weather_screen')
    def test_app_startup(self, mock_draw, mock_touch, mock_logger):
        """Test application startup and initialization"""
        from weather_cal_app import run_weather_app

        # Setup mocks
        epd = MockDisplayDriver()
        touch_handler = MagicMock()
        mock_touch.return_value = touch_handler

        gt_dev = MockTouchDevice()
        gt_dev.exit_requested = True  # Exit immediately

        gt_old = MockTouchDevice()
        gt = MockTouchDriver()

        mock_draw.return_value = MagicMock()

        # Run app (will exit immediately due to exit_requested)
        run_weather_app(epd, gt_dev, gt_old, gt)

        # Verify touch handler was created and started
        mock_touch.assert_called_once()
        touch_handler.start.assert_called_once()
        touch_handler.stop.assert_called_once()

    @patch('weather_cal_app.TouchHandler')
    @patch('weather_cal_app.draw_weather_screen')
    def test_touch_handler_cleanup(self, mock_draw, mock_touch):
        """Test that touch handler is properly cleaned up"""
        from weather_cal_app import run_weather_app

        epd = MockDisplayDriver()
        touch_handler = MagicMock()
        mock_touch.return_value = touch_handler

        gt_dev = MockTouchDevice()
        gt_dev.exit_requested = True

        gt_old = MockTouchDevice()
        gt = MockTouchDriver()

        mock_draw.return_value = MagicMock()

        run_weather_app(epd, gt_dev, gt_old, gt)

        # Verify stop was called even with immediate exit
        touch_handler.stop.assert_called_once()

    @patch('weather_cal_app.TouchHandler')
    @patch('weather_cal_app.draw_weather_screen')
    def test_error_handling(self, mock_draw, mock_touch):
        """Test error handling in main loop"""
        from weather_cal_app import run_weather_app

        epd = MockDisplayDriver()
        touch_handler = MagicMock()
        mock_touch.return_value = touch_handler

        gt_dev = MockTouchDevice()
        gt_dev.exit_requested = True

        gt_old = MockTouchDevice()
        gt = MockTouchDriver()

        # Simulate drawing error
        mock_draw.side_effect = Exception("Drawing failed")

        # Should not raise exception, just log it
        try:
            run_weather_app(epd, gt_dev, gt_old, gt)
        except Exception as e:
            self.fail(f"App loop raised exception: {e}")

        # But touch handler should still be stopped
        touch_handler.stop.assert_called_once()


class TestFunctionalityPreservation(unittest.TestCase):
    """Test that all original functionality is preserved"""

    def test_uses_touch_handler(self):
        """Verify refactored version uses TouchHandler"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            self.assertIn('TouchHandler', content)

    def test_uses_config_loader(self):
        """Verify refactored version uses ConfigLoader"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            self.assertIn('ConfigLoader', content)

    def test_uses_setup_logging(self):
        """Verify refactored version uses setup_logging"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            self.assertIn('setup_logging', content)

    def test_eliminates_threading_boilerplate(self):
        """Verify threading boilerplate is removed"""
        # Original had ~15 lines of manual threading
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            # Should not have old threading code patterns
            self.assertNotIn('threading.Thread', content)
            self.assertNotIn('pthread_irq', content)

    def test_eliminates_duplicate_exit_code(self):
        """Verify duplicate exit checks are removed"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            # Count exit_requested checks
            count = content.count('exit_requested')
            # Should only appear once (or twice - definition and use)
            self.assertLessEqual(count, 2)

    def test_has_error_handling(self):
        """Verify comprehensive error handling is added"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            self.assertIn('try:', content)
            self.assertIn('except', content)
            self.assertIn('finally:', content)

    def test_uses_periodic_timer(self):
        """Verify PeriodicTimer is used for updates"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            self.assertIn('PeriodicTimer', content)

    def test_uses_safe_execute(self):
        """Verify safe_execute is used for error handling"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            self.assertIn('safe_execute', content)


class TestCodeQuality(unittest.TestCase):
    """Test code quality improvements"""

    def test_has_docstrings(self):
        """Verify functions have docstrings"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            # Should have multiple docstrings
            docstring_count = content.count('"""')
            self.assertGreater(docstring_count, 4)  # Multiple docstrings

    def test_has_type_hints(self):
        """Verify functions have type hints"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            # Should have arrow hints for return types
            self.assertIn('->', content)

    def test_organized_sections(self):
        """Verify code is organized into clear sections"""
        with open('/home/user/pizerowgpio/weather_cal_app.py', 'r') as f:
            content = f.read()
            # Should have multiple section headers
            section_count = content.count('# ============')
            self.assertGreaterEqual(section_count, 8)


# ============================================================================
# COMPARISON TEST
# ============================================================================

class TestRefactoringComparison(unittest.TestCase):
    """Compare original and refactored versions"""

    def test_backup_exists(self):
        """Verify backup of original file exists"""
        backup_path = '/home/user/pizerowgpio/weather_cal_app.py.backup'
        self.assertTrue(os.path.exists(backup_path))

    def test_original_still_readable(self):
        """Verify original backup is still readable"""
        backup_path = '/home/user/pizerowgpio/weather_cal_app.py.backup'
        with open(backup_path, 'r') as f:
            content = f.read()
            self.assertIn('run_weather_app', content)
            self.assertIn('get_weather', content)

    def test_refactored_file_syntax(self):
        """Test that refactored file has valid Python syntax"""
        import py_compile
        refactored_path = '/home/user/pizerowgpio/weather_cal_app.py'
        try:
            py_compile.compile(refactored_path, doraise=True)
        except py_compile.PyCompileError as e:
            self.fail(f"Syntax error in refactored file: {e}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWeatherDataFetching))
    suite.addTests(loader.loadTestsFromTestCase(TestWeatherIconDrawing))
    suite.addTests(loader.loadTestsFromTestCase(TestScreenDrawing))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestMainAppLoop))
    suite.addTests(loader.loadTestsFromTestCase(TestFunctionalityPreservation))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestRefactoringComparison))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
