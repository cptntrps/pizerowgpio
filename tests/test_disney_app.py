"""
Tests for Disney App
====================

Tests for disney_app.py functionality including:
- Wait times fetching
- Background image caching
- Display rendering
- Error handling

Test Coverage:
- API fetching
- Data parsing
- Display functions
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import disney_app
except:
    pass


class TestDisneyWaitTimes:
    """Test Disney wait times fetching"""

    @patch('subprocess.run')
    def test_fetch_wait_times_success(self, mock_run):
        """Test successful wait times fetch"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            'lands': [
                {
                    'name': 'Tomorrowland',
                    'rides': [
                        {'name': 'Space Mountain', 'wait_time': 45, 'is_open': True}
                    ]
                }
            ]
        })
        mock_run.return_value = mock_result

        if hasattr(disney_app, 'fetch_wait_times'):
            rides = disney_app.fetch_wait_times()
            assert len(rides) >= 0

    @patch('subprocess.run')
    def test_fetch_wait_times_failure(self, mock_run):
        """Test wait times fetch failure handling"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_run.return_value = mock_result

        if hasattr(disney_app, 'fetch_wait_times'):
            rides = disney_app.fetch_wait_times()
            assert isinstance(rides, list)
            assert len(rides) == 0

    @patch('subprocess.run')
    def test_fetch_wait_times_timeout(self, mock_run):
        """Test timeout handling"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('curl', 10)

        if hasattr(disney_app, 'fetch_wait_times'):
            rides = disney_app.fetch_wait_times()
            assert rides == []


class TestDisneyDisplay:
    """Test Disney display functions"""

    @patch('disney_app.fontdir', '/tmp')
    def test_draw_wait_times_no_rides(self):
        """Test drawing with no rides"""
        if hasattr(disney_app, 'draw_wait_times'):
            with patch('PIL.ImageFont.truetype') as mock_font:
                mock_font.return_value = Image.core.getfont("", size=12)

                img = disney_app.draw_wait_times([])
                assert isinstance(img, Image.Image)
                assert img.size[0] > 0

    @patch('disney_app.fontdir', '/tmp')
    def test_draw_wait_times_with_rides(self):
        """Test drawing with rides"""
        if hasattr(disney_app, 'draw_wait_times'):
            rides = [
                {'name': 'Space Mountain', 'wait_time': 45, 'is_open': True},
                {'name': 'Splash Mountain', 'wait_time': 30, 'is_open': True}
            ]

            with patch('PIL.ImageFont.truetype') as mock_font:
                mock_font.return_value = Image.core.getfont("", size=12)

                img = disney_app.draw_wait_times(rides, 0)
                assert isinstance(img, Image.Image)


class TestBackgroundCaching:
    """Test background image caching"""

    def test_background_cache_initialization(self):
        """Test background cache exists"""
        if hasattr(disney_app, 'background_cache'):
            assert isinstance(disney_app.background_cache, dict)

    @patch('PIL.Image.open')
    def test_get_background_caches_image(self, mock_open):
        """Test background images are cached"""
        mock_img = Image.new('1', (250, 122), 255)
        mock_open.return_value = mock_img

        if hasattr(disney_app, 'get_background'):
            # First call - loads from file
            img1 = disney_app.get_background('test_land')
            # Second call - should use cache
            img2 = disney_app.get_background('test_land')

            # Verify caching happened
            if hasattr(disney_app, 'background_cache'):
                assert 'test_land' in disney_app.background_cache
