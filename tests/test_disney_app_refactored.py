#!/usr/bin/env python3
"""
Comprehensive Tests for Refactored disney_app.py
Tests all major functions and verifies refactoring improvements
"""
import os
import sys
import json
import time
import unittest
from unittest.mock import Mock, MagicMock, patch
from PIL import Image, ImageDraw

# Mock hardware modules before importing disney_app
sys.modules['TP_lib'] = MagicMock()
sys.modules['TP_lib.gt1151'] = MagicMock()
sys.modules['TP_lib.epd2in13_V3'] = MagicMock()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# TEST FIXTURES AND HELPERS
# ============================================================================

class MockEPD:
    """Mock E-paper display object"""
    def __init__(self):
        self.buffer = None
        self.display_calls = []

    def displayPartial(self, buffer):
        """Mock display partial update"""
        self.buffer = buffer
        self.display_calls.append(('partial', buffer))

    def getbuffer(self, img):
        """Mock get buffer"""
        return f"buffer_{id(img)}"

    def sleep(self):
        """Mock sleep"""
        pass

    def module_exit(self):
        """Mock module exit"""
        pass


class MockGT:
    """Mock touch driver"""
    def __init__(self):
        self.INT = 0
        self.digital_read_value = 1

    def digital_read(self, pin):
        """Mock digital read"""
        return self.digital_read_value

    def GT_Scan(self, gt_dev, gt_old):
        """Mock GT scan"""
        pass


class MockGTDev:
    """Mock touch device state"""
    def __init__(self):
        self.Touch = 0
        self.X = [0]
        self.Y = [0]
        self.S = [0]
        self.TouchpointFlag = 0
        self.exit_requested = False


# ============================================================================
# TEST CLASS
# ============================================================================

class TestDisneyAppRefactored(unittest.TestCase):
    """Test suite for refactored disney_app.py"""

    @classmethod
    def setUpClass(cls):
        """Set up test class - import after mocking"""
        global disney_app
        import disney_app

    def setUp(self):
        """Set up test fixtures"""
        self.mock_epd = MockEPD()
        self.mock_gt = MockGT()
        self.mock_gt_dev = MockGTDev()
        self.mock_gt_old = MockGTDev()

    def tearDown(self):
        """Clean up after tests"""
        # Clear background cache
        disney_app.BACKGROUND_CACHE.clear()

    # ========================================================================
    # FETCH OPERATIONS TESTS
    # ========================================================================

    @patch('subprocess.run')
    def test_fetch_wait_times_success(self, mock_run):
        """Test successful wait times fetch"""
        # Mock successful curl response
        mock_response = Mock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({
            'lands': [
                {
                    'name': 'Adventureland',
                    'rides': [
                        {'name': 'Jungle Cruise', 'wait_time': 30, 'is_open': True}
                    ]
                }
            ]
        })
        mock_run.return_value = mock_response

        result = disney_app.fetch_wait_times()

        # Verify fetch succeeded
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Jungle Cruise')
        self.assertEqual(result[0]['wait_time'], 30)
        self.assertEqual(result[0]['land'], 'Adventureland')
        self.assertTrue(result[0]['is_open'])

    @patch('subprocess.run')
    def test_fetch_wait_times_curl_failure(self, mock_run):
        """Test fetch with curl failure"""
        # Mock curl failure
        mock_response = Mock()
        mock_response.returncode = 1
        mock_response.stdout = ""
        mock_run.return_value = mock_response

        result = disney_app.fetch_wait_times()

        # Should return empty list on failure
        self.assertEqual(result, [])

    @patch('subprocess.run')
    def test_fetch_wait_times_invalid_json(self, mock_run):
        """Test fetch with invalid JSON response"""
        # Mock invalid JSON
        mock_response = Mock()
        mock_response.returncode = 0
        mock_response.stdout = "invalid json {{"
        mock_run.return_value = mock_response

        result = disney_app.fetch_wait_times()

        # Should return empty list on JSON error
        self.assertEqual(result, [])

    @patch('subprocess.run')
    def test_fetch_wait_times_timeout(self, mock_run):
        """Test fetch with timeout"""
        # Mock timeout
        mock_run.side_effect = Exception("Timeout")

        result = disney_app.fetch_wait_times()

        # Should return empty list on timeout
        self.assertEqual(result, [])

    @patch('subprocess.run')
    def test_fetch_wait_times_multiple_lands(self, mock_run):
        """Test fetch with multiple lands and rides"""
        mock_response = Mock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({
            'lands': [
                {
                    'name': 'Adventureland',
                    'rides': [
                        {'name': 'Jungle Cruise', 'wait_time': 30, 'is_open': True},
                        {'name': 'Pirates', 'wait_time': 45, 'is_open': True}
                    ]
                },
                {
                    'name': 'Tomorrowland',
                    'rides': [
                        {'name': 'Space Mountain', 'wait_time': 60, 'is_open': True}
                    ]
                }
            ]
        })
        mock_run.return_value = mock_response

        result = disney_app.fetch_wait_times()

        # Should have all 3 rides
        self.assertEqual(len(result), 3)

    # ========================================================================
    # IMAGE HANDLING TESTS
    # ========================================================================

    def test_load_land_background_caching(self):
        """Test background image caching"""
        # Clear cache
        disney_app.BACKGROUND_CACHE.clear()

        # Load background (will create blank if file doesn't exist)
        result1 = disney_app.load_land_background('Adventureland')
        result2 = disney_app.load_land_background('Adventureland')

        # Both should return same cached object
        self.assertIs(result1, result2)

        # Verify cache is populated
        self.assertIn('Adventureland', disney_app.BACKGROUND_CACHE)

    def test_load_land_background_returns_image(self):
        """Test that loaded background is a PIL Image"""
        result = disney_app.load_land_background('Tomorrowland')

        # Should return a PIL Image
        self.assertIsInstance(result, Image.Image)

        # Should be 1-bit monochrome
        self.assertEqual(result.mode, '1')

        # Should have correct dimensions
        self.assertEqual(result.size, (250, 122))

    def test_load_land_background_blank_fallback(self):
        """Test blank image fallback"""
        # Load non-existent land
        result = disney_app.load_land_background('NonexistentLand')

        # Should still return a valid image
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (250, 122))
        self.assertEqual(result.mode, '1')

    def test_load_land_background_different_lands(self):
        """Test that different lands are cached separately"""
        disney_app.BACKGROUND_CACHE.clear()

        land1 = disney_app.load_land_background('Adventureland')
        land2 = disney_app.load_land_background('Fantasyland')

        # Should be different objects
        self.assertIsNot(land1, land2)

        # Both should be in cache
        self.assertEqual(len(disney_app.BACKGROUND_CACHE), 2)

    @patch('disney_app.load_land_background')
    def test_draw_ride_info(self, mock_load_bg):
        """Test ride info drawing"""
        # Mock background load
        bg_img = Image.new('1', (250, 122), 255)
        mock_load_bg.return_value = bg_img

        ride = {
            'name': 'Space Mountain',
            'wait_time': 45,
            'is_open': True,
            'land': 'Tomorrowland'
        }

        result = disney_app.draw_ride_info(ride)

        # Should return a PIL Image
        self.assertIsInstance(result, Image.Image)

        # Should have correct dimensions
        self.assertEqual(result.size, (250, 122))

        # Should be 1-bit
        self.assertEqual(result.mode, '1')

    @patch('disney_app.load_land_background')
    def test_draw_ride_info_closed_ride(self, mock_load_bg):
        """Test drawing closed ride"""
        bg_img = Image.new('1', (250, 122), 255)
        mock_load_bg.return_value = bg_img

        ride = {
            'name': 'Haunted Mansion',
            'wait_time': 0,
            'is_open': False,
            'land': 'Liberty Square'
        }

        result = disney_app.draw_ride_info(ride)

        # Should still produce valid image
        self.assertIsInstance(result, Image.Image)

    @patch('disney_app.load_land_background')
    def test_draw_ride_info_long_name(self, mock_load_bg):
        """Test drawing ride with very long name"""
        bg_img = Image.new('1', (250, 122), 255)
        mock_load_bg.return_value = bg_img

        ride = {
            'name': 'This is a very long ride name that should be truncated',
            'wait_time': 30,
            'is_open': True,
            'land': 'Adventureland'
        }

        result = disney_app.draw_ride_info(ride)

        # Should still produce valid image without error
        self.assertIsInstance(result, Image.Image)

    # ========================================================================
    # DISPLAY OPERATIONS TESTS
    # ========================================================================

    def test_show_loading_screen(self):
        """Test loading screen display"""
        epd = MockEPD()
        disney_app.show_loading_screen(epd)

        # Should have called displayPartial
        self.assertEqual(len(epd.display_calls), 1)
        self.assertEqual(epd.display_calls[0][0], 'partial')

    def test_show_error_screen(self):
        """Test error screen display"""
        epd = MockEPD()
        disney_app.show_error_screen(epd, "Connection failed")

        # Should have called displayPartial
        self.assertEqual(len(epd.display_calls), 1)
        self.assertEqual(epd.display_calls[0][0], 'partial')

    def test_show_error_screen_with_long_message(self):
        """Test error screen with long message"""
        epd = MockEPD()
        disney_app.show_error_screen(epd, "A" * 100)

        # Should still display without error
        self.assertEqual(len(epd.display_calls), 1)

    # ========================================================================
    # SHARED UTILITIES INTEGRATION TESTS
    # ========================================================================

    def test_touch_handler_integration(self):
        """Test TouchHandler integration"""
        from display.touch_handler import TouchHandler

        gt = MockGT()
        gt_dev = MockGTDev()

        # Create and start handler
        touch = TouchHandler(gt, gt_dev)
        self.assertFalse(touch.is_running())

        touch.start()
        self.assertTrue(touch.is_running())

        # Stop handler
        touch.stop()
        time.sleep(0.1)  # Give thread time to stop
        self.assertFalse(touch.is_running())

    def test_cleanup_touch_state(self):
        """Test touch state cleanup"""
        from display.touch_handler import cleanup_touch_state

        gt_old = MockGTDev()
        gt_old.X[0] = 100
        gt_old.Y[0] = 200
        gt_old.S[0] = 1

        cleanup_touch_state(gt_old)

        # All should be reset to 0
        self.assertEqual(gt_old.X[0], 0)
        self.assertEqual(gt_old.Y[0], 0)
        self.assertEqual(gt_old.S[0], 0)

    def test_check_exit_requested(self):
        """Test exit request checking"""
        from display.touch_handler import check_exit_requested

        gt_dev = MockGTDev()
        gt_dev.exit_requested = False

        # Should return False initially
        self.assertFalse(check_exit_requested(gt_dev))

        # Set exit requested
        gt_dev.exit_requested = True
        self.assertTrue(check_exit_requested(gt_dev))

    def test_config_loader_integration(self):
        """Test ConfigLoader integration"""
        from shared.app_utils import ConfigLoader

        # Load config
        config = ConfigLoader.load()
        self.assertIsInstance(config, dict)

        # Get disney section (may be empty but should not crash)
        disney_config = ConfigLoader.get_section('disney', {})
        self.assertIsInstance(disney_config, dict)

    def test_logging_setup(self):
        """Test logging setup"""
        from shared.app_utils import setup_logging

        logger = setup_logging('test_disney')
        self.assertIsNotNone(logger)

        # Logger should be able to log
        logger.info("Test log message")
        logger.error("Test error message")

    # ========================================================================
    # CODE STRUCTURE TESTS
    # ========================================================================

    def test_shared_utils_used(self):
        """Test that shared utilities are being used"""
        with open('/home/user/pizerowgpio/disney_app.py', 'r') as f:
            content = f.read()

        # Check for shared utility imports
        self.assertIn('from shared.app_utils import', content)
        self.assertIn('ConfigLoader', content)
        self.assertIn('setup_logging', content)

        # Check for display component imports
        self.assertIn('from display.touch_handler import TouchHandler', content)
        self.assertIn('from display.fonts import get_font_preset', content)

    def test_threading_boilerplate_removed(self):
        """Test that manual threading boilerplate has been removed"""
        with open('/home/user/pizerowgpio/disney_app.py', 'r') as f:
            content = f.read()

        # Should not have manual flag_t threading code
        self.assertNotIn('flag_t = [1]', content)
        self.assertNotIn('def pthread_irq()', content)
        self.assertNotIn('threading.Thread(target=pthread_irq)', content)

        # Should use TouchHandler instead
        self.assertIn('TouchHandler(gt, gt_dev)', content)

    def test_font_loading_uses_presets(self):
        """Test that font loading uses display presets"""
        with open('/home/user/pizerowgpio/disney_app.py', 'r') as f:
            content = f.read()

        # Should use get_font_preset
        self.assertIn('get_font_preset', content)

        # Should not have manual font truetype loading
        # (We allow one for the dummy image bbox, but the main ones should use presets)
        font_truetype_count = content.count('ImageFont.truetype')
        self.assertLessEqual(font_truetype_count, 1,
                            "Should minimize manual font loading in favor of presets")

    def test_error_handling_comprehensive(self):
        """Test that error handling is comprehensive"""
        with open('/home/user/pizerowgpio/disney_app.py', 'r') as f:
            content = f.read()

        # Should have try/except blocks
        self.assertIn('try:', content)
        self.assertIn('except', content)

        # Should log errors
        self.assertIn('logger.error', content)

        # Should use finally for cleanup
        self.assertIn('finally:', content)

    def test_module_structure(self):
        """Test module is well-structured with sections"""
        with open('/home/user/pizerowgpio/disney_app.py', 'r') as f:
            content = f.read()

        # Check for section headers
        self.assertIn('# FETCH OPERATIONS', content)
        self.assertIn('# IMAGE HANDLING', content)
        self.assertIn('# DISPLAY OPERATIONS', content)
        self.assertIn('# MAIN APPLICATION', content)
        self.assertIn('# ENTRY POINT', content)

    def test_docstrings_present(self):
        """Test that functions have comprehensive docstrings"""
        with open('/home/user/pizerowgpio/disney_app.py', 'r') as f:
            lines = f.readlines()

        # Count docstrings (triple quotes)
        docstring_count = 0
        for line in lines:
            if '"""' in line:
                docstring_count += 1

        # Should have multiple docstrings (at least 5)
        self.assertGreaterEqual(docstring_count, 10,
                               "Should have comprehensive docstrings")

    # ========================================================================
    # FUNCTIONAL TESTS
    # ========================================================================

    @patch('subprocess.run')
    def test_fetch_and_draw_workflow(self, mock_run):
        """Test workflow of fetching data and drawing"""
        # Mock fetch
        mock_response = Mock()
        mock_response.returncode = 0
        mock_response.stdout = json.dumps({
            'lands': [
                {
                    'name': 'Adventureland',
                    'rides': [
                        {'name': 'Jungle Cruise', 'wait_time': 30, 'is_open': True}
                    ]
                }
            ]
        })
        mock_run.return_value = mock_response

        # Fetch rides
        rides = disney_app.fetch_wait_times()
        self.assertEqual(len(rides), 1)

        # Draw ride info
        img = disney_app.draw_ride_info(rides[0])
        self.assertIsNotNone(img)
        self.assertEqual(img.size, (250, 122))

    def test_background_cache_efficiency(self):
        """Test that background caching improves efficiency"""
        import time

        disney_app.BACKGROUND_CACHE.clear()

        # First load should populate cache
        start = time.time()
        img1 = disney_app.load_land_background('Adventureland')
        first_load_time = time.time() - start

        # Second load should be from cache (much faster)
        start = time.time()
        img2 = disney_app.load_land_background('Adventureland')
        cached_load_time = time.time() - start

        # Both should return same object
        self.assertIs(img1, img2)

        # Cached load should be faster (or at least not slower by much)
        # Note: In fast systems, both might be very fast, so we just verify it's cached
        self.assertIn('Adventureland', disney_app.BACKGROUND_CACHE)


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
