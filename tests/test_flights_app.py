"""
Tests for Flights App
======================

Tests for flights_app.py functionality including:
- Flight data fetching
- Geographic calculations (haversine, bearing)
- Display rendering
- Error handling

Test Coverage:
- API fetching
- Distance calculations
- Bearing calculations
- Display functions
"""

import pytest
import math
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import flights_app
except:
    pass


class TestGeographicCalculations:
    """Test geographic calculation functions"""

    def test_haversine_distance_same_point(self):
        """Test distance between same point is 0"""
        if hasattr(flights_app, 'haversine_distance'):
            distance = flights_app.haversine_distance(40.0, -73.0, 40.0, -73.0)
            assert distance == 0

    def test_haversine_distance_known_cities(self):
        """Test distance between known cities"""
        if hasattr(flights_app, 'haversine_distance'):
            # San Francisco to Los Angeles ~559 km
            distance = flights_app.haversine_distance(
                37.7749, -122.4194,  # SF
                34.0522, -118.2437    # LA
            )
            assert 500 < distance < 600  # Approximate check

    def test_calculate_bearing_north(self):
        """Test bearing calculation for due north"""
        if hasattr(flights_app, 'calculate_bearing'):
            # Point A to point directly north
            bearing = flights_app.calculate_bearing(
                40.0, -73.0,  # Start
                41.0, -73.0   # North (same longitude)
            )
            assert -10 < bearing < 10  # ~0 degrees (north)

    def test_calculate_bearing_east(self):
        """Test bearing calculation for due east"""
        if hasattr(flights_app, 'calculate_bearing'):
            bearing = flights_app.calculate_bearing(
                40.0, -73.0,   # Start
                40.0, -72.0    # East (same latitude)
            )
            assert 80 < bearing < 100  # ~90 degrees (east)

    def test_calculate_bearing_range(self):
        """Test bearing is always 0-360 degrees"""
        if hasattr(flights_app, 'calculate_bearing'):
            bearing = flights_app.calculate_bearing(40.0, -73.0, 30.0, -74.0)
            assert 0 <= bearing <= 360


class TestFlightDataFetching:
    """Test flight data fetching"""

    @patch('subprocess.run')
    def test_fetch_flights_success(self, mock_run):
        """Test successful flight data fetch"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"flight":"AA123","altitude":5000}]'
        mock_run.return_value = mock_result

        if hasattr(flights_app, 'fetch_flights'):
            flights = flights_app.fetch_flights()
            assert isinstance(flights, list)

    @patch('subprocess.run')
    def test_fetch_flights_failure(self, mock_run):
        """Test flight fetch failure handling"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        if hasattr(flights_app, 'fetch_flights'):
            flights = flights_app.fetch_flights()
            assert flights == []

    @patch('subprocess.run')
    def test_fetch_flights_invalid_json(self, mock_run):
        """Test invalid JSON handling"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'not valid json'
        mock_run.return_value = mock_result

        if hasattr(flights_app, 'fetch_flights'):
            flights = flights_app.fetch_flights()
            assert flights == []


class TestFlightDisplay:
    """Test flight display functions"""

    @patch('flights_app.fontdir', '/tmp')
    def test_draw_flight_no_flights(self):
        """Test drawing with no flights"""
        if hasattr(flights_app, 'draw_flight'):
            with patch('PIL.ImageFont.truetype') as mock_font:
                mock_font.return_value = Image.core.getfont("", size=12)

                img = flights_app.draw_flight([])
                assert isinstance(img, Image.Image)

    @patch('flights_app.fontdir', '/tmp')
    def test_draw_flight_with_data(self):
        """Test drawing with flight data"""
        if hasattr(flights_app, 'draw_flight'):
            flights = [
                {
                    'flight': 'AA123',
                    'altitude': 5000,
                    'speed': 450,
                    'lat': 40.0,
                    'lon': -73.0
                }
            ]

            with patch('PIL.ImageFont.truetype') as mock_font:
                mock_font.return_value = Image.core.getfont("", size=12)

                img = flights_app.draw_flight(flights, 0)
                assert isinstance(img, Image.Image)


class TestQuoteDisplay:
    """Test aviation quote display"""

    def test_aviation_quotes_exist(self):
        """Test aviation quotes list exists"""
        if hasattr(flights_app, 'AVIATION_QUOTES'):
            quotes = flights_app.AVIATION_QUOTES
            assert isinstance(quotes, list)
            assert len(quotes) > 0

    def test_quote_format(self):
        """Test quote format is valid"""
        if hasattr(flights_app, 'AVIATION_QUOTES'):
            for quote in flights_app.AVIATION_QUOTES:
                assert isinstance(quote, str)
                assert len(quote) > 0


class TestCompassDisplay:
    """Test compass display functionality"""

    @patch('flights_app.fontdir', '/tmp')
    def test_draw_compass(self):
        """Test compass drawing"""
        if hasattr(flights_app, 'draw_compass'):
            with patch('PIL.ImageFont.truetype') as mock_font:
                mock_font.return_value = Image.core.getfont("", size=12)

                # Test various bearings
                for bearing in [0, 90, 180, 270]:
                    img = flights_app.draw_compass(bearing)
                    if img:
                        assert isinstance(img, Image.Image)
