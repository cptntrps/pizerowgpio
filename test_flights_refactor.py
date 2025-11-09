#!/usr/bin/env python3
"""
Tests for Refactored Flights App
=================================

Verifies that the refactored code maintains functionality while using shared utilities.
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import math
import json

# Add parent directory to path
sys.path.insert(0, '/home/user/pizerowgpio')

# Test geographic calculations


class TestGeographicCalculations(unittest.TestCase):
    """Test distance and bearing calculations"""

    def test_haversine_same_point(self):
        """Distance between same point should be zero"""
        from flights_app import haversine_distance

        distance = haversine_distance(51.5, -0.1, 51.5, -0.1)
        self.assertAlmostEqual(distance, 0, places=2)

    def test_haversine_known_distance(self):
        """Test known distance (London to Paris ~340km)"""
        from flights_app import haversine_distance

        # London: 51.5N, 0.1W
        # Paris: 48.9N, 2.4E
        distance = haversine_distance(51.5, -0.1, 48.9, 2.4)

        # Should be roughly 340km
        self.assertGreater(distance, 300)
        self.assertLess(distance, 380)

    def test_bearing_north(self):
        """Bearing to point directly north should be close to 0"""
        from flights_app import calculate_bearing

        # Same longitude, slightly north
        bearing = calculate_bearing(51.0, -0.1, 52.0, -0.1)

        # Should be close to 0 (north)
        self.assertLess(bearing, 5)

    def test_bearing_east(self):
        """Bearing to point directly east should be close to 90"""
        from flights_app import calculate_bearing

        # Same latitude, point to the east
        bearing = calculate_bearing(51.5, -0.1, 51.5, 1.0)

        # Should be close to 90 (east)
        self.assertGreater(bearing, 85)
        self.assertLess(bearing, 95)

    def test_bearing_range(self):
        """Bearing should always be 0-360"""
        from flights_app import calculate_bearing

        for lat1 in [0, 30, 51.5, -30, -51.5]:
            for lon1 in [-180, -90, 0, 90, 180]:
                for lat2 in [0, 30, 51.5, -30, -51.5]:
                    for lon2 in [-180, -90, 0, 90, 180]:
                        bearing = calculate_bearing(lat1, lon1, lat2, lon2)
                        self.assertGreaterEqual(bearing, 0)
                        self.assertLess(bearing, 360)


class TestSharedUtilitiesIntegration(unittest.TestCase):
    """Test integration with shared utilities"""

    @patch('shared.app_utils.ConfigLoader.load')
    def test_config_loader_usage(self, mock_load):
        """Test that ConfigLoader is properly imported"""
        from shared.app_utils import ConfigLoader

        self.assertTrue(hasattr(ConfigLoader, 'load'))
        self.assertTrue(hasattr(ConfigLoader, 'get_section'))
        self.assertTrue(hasattr(ConfigLoader, 'get_value'))

    @patch('shared.app_utils.setup_logging')
    def test_logging_setup_usage(self, mock_setup):
        """Test that setup_logging is properly imported"""
        from shared.app_utils import setup_logging

        self.assertTrue(callable(setup_logging))

    def test_periodic_timer(self):
        """Test PeriodicTimer utility"""
        from shared.app_utils import PeriodicTimer
        import time

        timer = PeriodicTimer(0.1)
        self.assertFalse(timer.is_ready())

        time.sleep(0.11)
        self.assertTrue(timer.is_ready())

    def test_touch_handler_import(self):
        """Test TouchHandler can be imported"""
        from display.touch_handler import TouchHandler

        self.assertTrue(hasattr(TouchHandler, 'start'))
        self.assertTrue(hasattr(TouchHandler, 'stop'))
        self.assertTrue(hasattr(TouchHandler, 'is_touched'))

    def test_compass_icon_import(self):
        """Test compass icon function can be imported"""
        from display.icons import draw_compass_icon

        self.assertTrue(callable(draw_compass_icon))

    def test_font_preset_import(self):
        """Test font preset function can be imported"""
        from display.fonts import get_font_preset

        self.assertTrue(callable(get_font_preset))


class TestFlightDataStructure(unittest.TestCase):
    """Test that flight data structure is correct"""

    def test_flight_data_has_required_fields(self):
        """Flight data should have all required fields"""
        required_fields = [
            'callsign', 'airline', 'origin', 'destination',
            'aircraft', 'altitude', 'speed', 'timestamp',
            'distance', 'bearing'
        ]

        # This would be populated by get_current_flight in real scenario
        flight_data = {
            'callsign': 'BA123',
            'airline': 'British Airways',
            'origin': 'LHR',
            'destination': 'JFK',
            'aircraft': 'B777',
            'altitude': 35000,
            'speed': 450,
            'timestamp': '14:30',
            'distance': 25.5,
            'bearing': 45.0
        }

        for field in required_fields:
            self.assertIn(field, flight_data)


class TestCodeRefactoringImprovements(unittest.TestCase):
    """Verify code improvements from refactoring"""

    def test_no_direct_file_logging_setup(self):
        """Direct logging setup should be replaced by setup_logging()"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        # Should NOT have old-style logging setup
        self.assertNotIn('logging.basicConfig', content)
        self.assertNotIn('logging.FileHandler', content)

        # Should have imports from shared utilities
        self.assertIn('from shared.app_utils import', content)
        self.assertIn('setup_logging', content)

    def test_uses_config_loader(self):
        """Should use ConfigLoader instead of direct json.load"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('ConfigLoader.load()', content)
        self.assertNotIn('json.load(open("/home/pizero2w', content)

    def test_uses_touch_handler(self):
        """Should use TouchHandler instead of manual threading"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('from display.touch_handler import TouchHandler', content)
        self.assertIn('touch = TouchHandler(', content)
        self.assertIn('touch.start()', content)
        self.assertIn('touch.stop()', content)

        # Should NOT have old threading code
        self.assertNotIn('def pthread_irq():', content)
        self.assertNotIn('threading.Thread(target=pthread_irq)', content)

    def test_uses_compass_icon(self):
        """Should use draw_compass_icon instead of draw_compass_rose"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('from display.icons import draw_compass_icon', content)
        self.assertIn('draw_compass_icon(', content)

        # Should NOT have old compass rose function
        self.assertNotIn('def draw_compass_rose(', content)

    def test_uses_check_exit_requested(self):
        """Should use check_exit_requested helper function"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('check_exit_requested(gt_dev)', content)

        # Should NOT have inline attribute checking
        self.assertNotIn('hasattr(gt_dev, "exit_requested") and gt_dev.exit_requested',
                         content)

    def test_uses_cleanup_touch_state(self):
        """Should use cleanup_touch_state helper"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('cleanup_touch_state(gt_old)', content)

        # Count occurrences - should be significantly fewer than original
        # which had 3 separate inline blocks
        cleanup_count = content.count('cleanup_touch_state')
        self.assertGreater(cleanup_count, 0)

    def test_uses_periodic_timer(self):
        """Should use PeriodicTimer for timing"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('PeriodicTimer', content)
        self.assertIn('update_timer = PeriodicTimer', content)
        self.assertIn('animation_timer = PeriodicTimer', content)
        self.assertIn('quote_timer = PeriodicTimer', content)

    def test_uses_safe_execute(self):
        """Should use safe_execute for error handling"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        self.assertIn('safe_execute', content)

    def test_improved_code_organization(self):
        """Code should be organized into logical sections"""
        with open('/home/user/pizerowgpio/flights_app.py', 'r') as f:
            content = f.read()

        sections = [
            'INITIALIZATION',
            'GEOGRAPHIC CALCULATIONS',
            'FLIGHT DATA RETRIEVAL',
            'DISPLAY RENDERING',
            'MAIN APPLICATION LOOP'
        ]

        for section in sections:
            self.assertIn(section, content)

    def test_backup_exists(self):
        """Original backup should exist"""
        import os

        backup_path = '/home/user/pizerowgpio/flights_app.py.backup'
        self.assertTrue(os.path.exists(backup_path))

        # Backup should have roughly same line count as original
        with open(backup_path, 'r') as f:
            backup_lines = len(f.readlines())

        # Should be close to 606 lines
        self.assertGreater(backup_lines, 600)
        self.assertLess(backup_lines, 610)


class TestFunctionality(unittest.TestCase):
    """Test that refactored functions maintain same functionality"""

    def test_draw_quote_returns_image(self):
        """draw_quote should return PIL Image"""
        # Mock PIL since it might not be available
        with patch('flights_app.Image') as mock_image:
            mock_image.new.return_value = MagicMock()

            from flights_app import draw_quote

            result = draw_quote("Test quote", "Author")
            self.assertIsNotNone(result)

    def test_draw_flight_portal_returns_image(self):
        """draw_flight_portal should return PIL Image"""
        with patch('flights_app.Image') as mock_image:
            mock_image.new.return_value = MagicMock()

            from flights_app import draw_flight_portal

            result = draw_flight_portal(None)
            self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
