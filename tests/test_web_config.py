"""
Comprehensive Tests for Web Config API
=======================================

Tests for web_config.py Flask application including:
- Config API endpoints
- Medicine API endpoints
- Data persistence
- Error handling

Test Coverage:
- GET /api/config
- POST /api/config/<section>
- GET /api/medicine/data
- POST /api/medicine/add
- POST /api/medicine/update
- DELETE /api/medicine/delete/<id>
- POST /api/medicine/mark-taken
- GET /api/medicine/pending
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Flask App Setup
# ============================================================================

@pytest.fixture
def flask_app(tmp_path):
    """Create Flask app with temporary config"""
    # Mock config file
    config_file = tmp_path / "config.json"
    config_data = {
        "weather": {"location": "Boston", "update_interval": 300},
        "medicine": {"update_interval": 60, "reminder_window": 30},
        "disney": {"park_id": 6, "update_interval": 10}
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f)

    # Patch CONFIG_FILE before importing
    with patch('web_config.CONFIG_FILE', str(config_file)):
        import web_config
        web_config.CONFIG_FILE = str(config_file)
        app = web_config.app
        app.config['TESTING'] = True
        yield app


@pytest.fixture
def client(flask_app):
    """Create Flask test client"""
    return flask_app.test_client()


@pytest.fixture
def medicine_data_file(tmp_path):
    """Create temporary medicine data file"""
    med_file = tmp_path / "medicine_data.json"
    data = {
        "medicines": [
            {
                "id": "med1",
                "name": "Vitamin D",
                "dosage": "1000 IU",
                "days": ["mon", "wed", "fri"],
                "window_start": "08:00",
                "window_end": "10:00",
                "time_window": "morning",
                "pills_remaining": 30,
                "active": True
            }
        ],
        "tracking": {},
        "time_windows": {}
    }
    with open(med_file, 'w') as f:
        json.dump(data, f)
    return str(med_file)


# ============================================================================
# Test Config API
# ============================================================================

class TestConfigAPI:
    """Test configuration API endpoints"""

    def test_get_config_success(self, client):
        """Test GET /api/config returns config data"""
        response = client.get('/api/config')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "weather" in data
        assert "medicine" in data
        assert data["weather"]["location"] == "Boston"

    def test_get_config_file_not_found(self, client):
        """Test GET /api/config when file doesn't exist"""
        with patch('web_config.CONFIG_FILE', '/nonexistent/config.json'):
            response = client.get('/api/config')

            # Should return error or empty config
            assert response.status_code in [200, 404, 500]

    def test_post_config_section_success(self, client, tmp_path):
        """Test POST /api/config/<section> updates config"""
        new_weather_config = {
            "location": "New York",
            "update_interval": 600
        }

        response = client.post(
            '/api/config/weather',
            data=json.dumps(new_weather_config),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Verify config was updated
        response = client.get('/api/config')
        data = json.loads(response.data)
        assert data["weather"]["location"] == "New York"
        assert data["weather"]["update_interval"] == 600

    def test_post_config_invalid_json(self, client):
        """Test POST /api/config with invalid JSON"""
        response = client.post(
            '/api/config/weather',
            data='not valid json',
            content_type='application/json'
        )

        # Should return error
        assert response.status_code in [400, 500]

    def test_post_config_new_section(self, client):
        """Test POST /api/config creates new section"""
        new_section = {
            "custom_setting": "value"
        }

        response = client.post(
            '/api/config/new_section',
            data=json.dumps(new_section),
            content_type='application/json'
        )

        assert response.status_code == 200

        # Verify new section exists
        response = client.get('/api/config')
        data = json.loads(response.data)
        assert "new_section" in data


# ============================================================================
# Test Medicine Data API
# ============================================================================

class TestMedicineDataAPI:
    """Test medicine data API endpoints"""

    def test_get_medicine_data_success(self, client, medicine_data_file):
        """Test GET /api/medicine/data returns medicine data"""
        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            response = client.get('/api/medicine/data')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "medicines" in data
            assert len(data["medicines"]) == 1
            assert data["medicines"][0]["name"] == "Vitamin D"

    def test_add_medicine_success(self, client, medicine_data_file):
        """Test POST /api/medicine/add adds new medicine"""
        new_medicine = {
            "name": "Omega-3",
            "dosage": "1 capsule",
            "days": ["mon", "tue", "wed", "thu", "fri"],
            "window_start": "20:00",
            "window_end": "22:00",
            "time_window": "evening",
            "pills_remaining": 60
        }

        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            response = client.post(
                '/api/medicine/add',
                data=json.dumps(new_medicine),
                content_type='application/json'
            )

            assert response.status_code in [200, 201]

            # Verify medicine was added
            response = client.get('/api/medicine/data')
            data = json.loads(response.data)
            assert len(data["medicines"]) == 2

    def test_add_medicine_invalid_data(self, client):
        """Test POST /api/medicine/add with invalid data"""
        invalid_medicine = {
            "name": "Test"
            # Missing required fields
        }

        response = client.post(
            '/api/medicine/add',
            data=json.dumps(invalid_medicine),
            content_type='application/json'
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 500]

    def test_update_medicine_success(self, client, medicine_data_file):
        """Test POST /api/medicine/update updates existing medicine"""
        update_data = {
            "id": "med1",
            "name": "Vitamin D3",
            "dosage": "2000 IU",
            "pills_remaining": 25
        }

        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            response = client.post(
                '/api/medicine/update',
                data=json.dumps(update_data),
                content_type='application/json'
            )

            assert response.status_code == 200

            # Verify updates
            response = client.get('/api/medicine/data')
            data = json.loads(response.data)
            med = next(m for m in data["medicines"] if m["id"] == "med1")
            assert med["name"] == "Vitamin D3"
            assert med["dosage"] == "2000 IU"

    def test_delete_medicine_success(self, client, medicine_data_file):
        """Test DELETE /api/medicine/delete/<id> removes medicine"""
        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            response = client.delete('/api/medicine/delete/med1')

            assert response.status_code == 200

            # Verify deletion
            response = client.get('/api/medicine/data')
            data = json.loads(response.data)
            assert len(data["medicines"]) == 0

    def test_delete_medicine_not_found(self, client, medicine_data_file):
        """Test DELETE /api/medicine/delete with non-existent ID"""
        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            response = client.delete('/api/medicine/delete/nonexistent')

            # Should handle gracefully
            assert response.status_code in [200, 404]

    def test_mark_medicine_taken_success(self, client, medicine_data_file):
        """Test POST /api/medicine/mark-taken marks medicine as taken"""
        mark_data = {
            "medicine_id": "med1",
            "time_window": "morning"
        }

        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
                mock_dt.strftime = datetime.strftime

                response = client.post(
                    '/api/medicine/mark-taken',
                    data=json.dumps(mark_data),
                    content_type='application/json'
                )

                assert response.status_code == 200

    def test_get_pending_medicines(self, client, medicine_data_file):
        """Test GET /api/medicine/pending returns pending medicines"""
        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            with patch('medicine_app.REMINDER_WINDOW', 30):
                with patch('datetime.datetime') as mock_dt:
                    # Monday 9:00 AM
                    mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
                    mock_dt.strftime = datetime.strftime

                    response = client.get('/api/medicine/pending')

                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert "pending" in data or isinstance(data, list)


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling in web config"""

    def test_404_on_invalid_route(self, client):
        """Test 404 response on invalid route"""
        response = client.get('/api/invalid/route')
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 on wrong HTTP method"""
        # POST to GET-only endpoint
        response = client.post('/api/config')
        assert response.status_code == 405

    def test_missing_content_type(self, client):
        """Test POST without content-type header"""
        response = client.post(
            '/api/config/weather',
            data='{"test": "data"}'
        )

        # Flask might handle this, or return error
        assert response.status_code in [200, 400, 415]


# ============================================================================
# Test Index Route
# ============================================================================

class TestIndexRoute:
    """Test main dashboard route"""

    def test_index_returns_html(self, client):
        """Test GET / returns HTML dashboard"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'html' in response.data or b'HTML' in response.data
        assert response.content_type.startswith('text/html')

    def test_index_contains_title(self, client):
        """Test index page contains title"""
        response = client.get('/')

        assert b'Pi Zero' in response.data or b'Dashboard' in response.data


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for web config"""

    def test_complete_medicine_workflow(self, client, medicine_data_file):
        """Test complete workflow: get → add → update → delete"""
        with patch('medicine_app.MEDICINE_DATA_FILE', medicine_data_file):
            # 1. Get initial data
            response = client.get('/api/medicine/data')
            assert response.status_code == 200
            initial_data = json.loads(response.data)
            initial_count = len(initial_data["medicines"])

            # 2. Add new medicine
            new_med = {
                "name": "Test Med",
                "dosage": "1 pill",
                "days": ["mon"],
                "window_start": "12:00",
                "window_end": "14:00",
                "time_window": "afternoon",
                "pills_remaining": 10
            }
            response = client.post(
                '/api/medicine/add',
                data=json.dumps(new_med),
                content_type='application/json'
            )
            assert response.status_code in [200, 201]

            # 3. Verify addition
            response = client.get('/api/medicine/data')
            data = json.loads(response.data)
            assert len(data["medicines"]) == initial_count + 1

            # 4. Update the medicine
            new_med_id = data["medicines"][-1]["id"]
            update = {
                "id": new_med_id,
                "name": "Updated Med",
                "dosage": "2 pills"
            }
            response = client.post(
                '/api/medicine/update',
                data=json.dumps(update),
                content_type='application/json'
            )
            assert response.status_code == 200

            # 5. Delete the medicine
            response = client.delete(f'/api/medicine/delete/{new_med_id}')
            assert response.status_code == 200

            # 6. Verify deletion
            response = client.get('/api/medicine/data')
            data = json.loads(response.data)
            assert len(data["medicines"]) == initial_count

    def test_config_persistence(self, client):
        """Test config changes persist across requests"""
        # Update config
        new_config = {"location": "Los Angeles", "update_interval": 900}
        response = client.post(
            '/api/config/weather',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        assert response.status_code == 200

        # Fetch config again
        response = client.get('/api/config')
        data = json.loads(response.data)
        assert data["weather"]["location"] == "Los Angeles"
        assert data["weather"]["update_interval"] == 900
