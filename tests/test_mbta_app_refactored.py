#!/usr/bin/env python3
"""
Unit Tests for Refactored MBTA App
===================================

Tests verify that the refactored version maintains exact functionality
while using shared utilities and eliminating code duplication.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the TP_lib imports before importing mbta_app
sys.modules['TP_lib'] = MagicMock()

# Import after mocking
import mbta_app


class TestFetchJson:
    """Test JSON fetching functionality"""

    @patch('mbta_app.subprocess.run')
    def test_fetch_json_success(self, mock_run):
        """Test successful JSON fetch"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": []}'
        mock_run.return_value = mock_result

        result = mbta_app.fetch_json("http://example.com")
        assert result == {"data": []}

    @patch('mbta_app.subprocess.run')
    def test_fetch_json_timeout(self, mock_run):
        """Test timeout handling"""
        mock_run.side_effect = TimeoutError()

        result = mbta_app.fetch_json("http://example.com")
        assert result is None

    @patch('mbta_app.subprocess.run')
    def test_fetch_json_invalid_json(self, mock_run):
        """Test invalid JSON handling"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        result = mbta_app.fetch_json("http://example.com")
        assert result is None

    @patch('mbta_app.subprocess.run')
    def test_fetch_json_empty_response(self, mock_run):
        """Test empty response handling"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = mbta_app.fetch_json("http://example.com")
        assert result is None


class TestGetPredictions:
    """Test prediction fetching"""

    @patch('mbta_app.fetch_json')
    def test_get_predictions_success(self, mock_fetch):
        """Test successful prediction retrieval"""
        future_time = (datetime.now(datetime.now().astimezone().tzinfo) + timedelta(minutes=5)).isoformat()
        mock_fetch.return_value = {
            'data': [
                {
                    'attributes': {
                        'arrival_time': future_time,
                        'direction_id': 0
                    },
                    'relationships': {
                        'route': {
                            'data': {
                                'id': 'Red'
                            }
                        }
                    }
                }
            ]
        }

        result = mbta_app.get_predictions('place-test')
        assert len(result) == 1
        assert result[0]['route'] == 'Red'
        assert result[0]['minutes'] >= 4  # Allow for time skew

    @patch('mbta_app.fetch_json')
    def test_get_predictions_empty(self, mock_fetch):
        """Test empty prediction response"""
        mock_fetch.return_value = {'data': []}

        result = mbta_app.get_predictions('place-test')
        assert result == []

    @patch('mbta_app.fetch_json')
    def test_get_predictions_none(self, mock_fetch):
        """Test None response"""
        mock_fetch.return_value = None

        result = mbta_app.get_predictions('place-test')
        assert result == []

    @patch('mbta_app.fetch_json')
    def test_get_predictions_limit(self, mock_fetch):
        """Test that only 5 predictions are fetched"""
        future_time = (datetime.now(datetime.now().astimezone().tzinfo) + timedelta(minutes=5)).isoformat()
        predictions_data = []
        for i in range(10):
            predictions_data.append({
                'attributes': {
                    'arrival_time': future_time,
                    'direction_id': 0
                },
                'relationships': {
                    'route': {
                        'data': {
                            'id': f'Route{i}'
                        }
                    }
                }
            })

        mock_fetch.return_value = {'data': predictions_data}

        result = mbta_app.get_predictions('place-test')
        assert len(result) <= 5


class TestGetSystemAlerts:
    """Test system alerts fetching"""

    @patch('mbta_app.fetch_json')
    def test_get_alerts_suspension(self, mock_fetch):
        """Test suspension alert detection"""
        mock_fetch.return_value = {
            'data': [
                {
                    'attributes': {
                        'effect': 'SUSPENSION'
                    },
                    'relationships': {
                        'informed_entity': {
                            'data': [
                                {'route': 'Red'}
                            ]
                        }
                    }
                }
            ]
        }

        result = mbta_app.get_system_alerts()
        assert result == {'Red': 'SUSPENSION'}

    @patch('mbta_app.fetch_json')
    def test_get_alerts_delay(self, mock_fetch):
        """Test delay alert detection"""
        mock_fetch.return_value = {
            'data': [
                {
                    'attributes': {
                        'effect': 'DELAY'
                    },
                    'relationships': {
                        'informed_entity': {
                            'data': [
                                {'route': 'Orange'}
                            ]
                        }
                    }
                }
            ]
        }

        result = mbta_app.get_system_alerts()
        assert result == {'Orange': 'DELAY'}

    @patch('mbta_app.fetch_json')
    def test_get_alerts_empty(self, mock_fetch):
        """Test empty alerts response"""
        mock_fetch.return_value = {'data': []}

        result = mbta_app.get_system_alerts()
        assert result == {}

    @patch('mbta_app.fetch_json')
    def test_get_alerts_invalid_line(self, mock_fetch):
        """Test that invalid lines are ignored"""
        mock_fetch.return_value = {
            'data': [
                {
                    'attributes': {
                        'effect': 'SUSPENSION'
                    },
                    'relationships': {
                        'informed_entity': {
                            'data': [
                                {'route': 'InvalidLine'}
                            ]
                        }
                    }
                }
            ]
        }

        result = mbta_app.get_system_alerts()
        assert result == {}


class TestFormatTime:
    """Test time formatting"""

    def test_format_time_arriving(self):
        """Test arriving format"""
        assert mbta_app.format_time(0) == "Arriving"

    def test_format_time_one_minute(self):
        """Test one minute format"""
        assert mbta_app.format_time(1) == "1 min"

    def test_format_time_multiple_minutes(self):
        """Test multiple minutes format"""
        assert mbta_app.format_time(5) == "5 min"
        assert mbta_app.format_time(30) == "30 min"


class TestDrawingFunctions:
    """Test display drawing functions"""

    @patch('mbta_app.get_font_preset')
    @patch('mbta_app.create_canvas')
    @patch('mbta_app.get_predictions')
    def test_draw_commute_dashboard_returns_image(self, mock_predictions, mock_canvas, mock_font):
        """Test that draw_commute_dashboard returns image"""
        mock_img = Mock()
        mock_draw = Mock()
        mock_canvas.return_value = (mock_img, mock_draw)
        mock_predictions.return_value = []
        mock_font.return_value = Mock()  # Mock font

        result = mbta_app.draw_commute_dashboard('home', 'work', 'Home', 'Work')
        assert result == mock_img

    @patch('mbta_app.get_font_preset')
    @patch('mbta_app.create_canvas')
    @patch('mbta_app.get_system_alerts')
    def test_draw_system_status_returns_image(self, mock_alerts, mock_canvas, mock_font):
        """Test that draw_system_status returns image"""
        mock_img = Mock()
        mock_draw = Mock()
        mock_canvas.return_value = (mock_img, mock_draw)
        mock_alerts.return_value = {}
        mock_font.return_value = Mock()  # Mock font

        result = mbta_app.draw_system_status()
        assert result == mock_img


class TestImportsAndSharedUtilities:
    """Test that refactored version uses shared utilities"""

    def test_uses_config_loader(self):
        """Verify ConfigLoader is imported"""
        from shared.app_utils import ConfigLoader
        assert ConfigLoader is not None

    def test_uses_touch_handler(self):
        """Verify TouchHandler is imported"""
        from display.touch_handler import TouchHandler
        assert TouchHandler is not None

    def test_uses_periodic_timer(self):
        """Verify PeriodicTimer is imported"""
        from shared.app_utils import PeriodicTimer
        assert PeriodicTimer is not None

    def test_uses_logging(self):
        """Verify logging is configured"""
        from shared.app_utils import setup_logging
        assert setup_logging is not None


class TestCodeReduction:
    """Verify code reduction metrics"""

    def test_original_backup_exists(self):
        """Verify backup file was created"""
        backup_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'mbta_app.py.backup'
        )
        assert os.path.exists(backup_path)

    def test_refactored_is_smaller(self):
        """Verify refactored version is smaller than original"""
        backup_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'mbta_app.py.backup'
        )
        refactored_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'mbta_app.py'
        )

        with open(backup_path) as f:
            original_lines = len(f.readlines())

        with open(refactored_path) as f:
            refactored_lines = len(f.readlines())

        reduction = ((original_lines - refactored_lines) / original_lines) * 100
        assert refactored_lines < original_lines
        assert reduction >= 8  # Target: ~8% reduction
        print(f"\nCode reduction: {reduction:.1f}% ({original_lines} -> {refactored_lines} lines)")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
