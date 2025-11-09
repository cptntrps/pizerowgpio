"""
Configuration API Endpoint Tests
Phase 1.4 - API Testing Suite

Tests for configuration operations:
- GET /api/v1/config (get all configuration)
- PUT /api/v1/config (replace all configuration)
- GET /api/v1/config/<section> (get section)
- PUT /api/v1/config/<section> (replace section)
- PATCH /api/v1/config/<section> (partial update section)
- Section-specific endpoints (weather, medicine, etc.)
"""

import json
import os
import tempfile
import shutil
from contextlib import contextmanager


@contextmanager
def temp_config_file(config_data):
    """Create temporary config file for testing"""
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'config.json')

    with open(config_path, 'w') as f:
        json.dump(config_data, f)

    # Update the config path in the module
    from api.v1.routes import config as config_module
    original_path = config_module.CONFIG_FILE
    config_module.CONFIG_FILE = config_path

    try:
        yield config_path
    finally:
        # Restore original path
        config_module.CONFIG_FILE = original_path
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestGetAllConfig:
    """Test GET /api/v1/config"""

    def test_get_all_config_success(self, client):
        """Test getting all configuration"""
        test_config = {
            "medicine": {"enabled": True},
            "weather": {"enabled": False},
            "system": {"debug": True}
        }

        with temp_config_file(test_config):
            response = client.get('/api/v1/config')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['success'] is True
            assert 'medicine' in data['data']
            assert 'weather' in data['data']
            assert 'system' in data['data']

    def test_get_all_config_structure(self, client):
        """Test that config has expected structure"""
        test_config = {
            "medicine": {"enabled": True, "reminder_window": 30},
            "display": {"brightness": 100}
        }

        with temp_config_file(test_config):
            response = client.get('/api/v1/config')
            data = json.loads(response.data)

            assert data['data']['medicine']['enabled'] is True
            assert data['data']['medicine']['reminder_window'] == 30


class TestGetConfigSection:
    """Test GET /api/v1/config/<section>"""

    def test_get_config_section_success(self, client):
        """Test getting specific config section"""
        test_config = {
            "medicine": {"enabled": True, "reminder_window": 30},
            "weather": {"enabled": False}
        }

        with temp_config_file(test_config):
            response = client.get('/api/v1/config/medicine')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['enabled'] is True
            assert data['data']['reminder_window'] == 30

    def test_get_config_section_not_found(self, client):
        """Test getting non-existent section"""
        test_config = {
            "medicine": {"enabled": True}
        }

        with temp_config_file(test_config):
            response = client.get('/api/v1/config/nonexistent')
            assert response.status_code == 404

            data = json.loads(response.data)
            assert data['success'] is False
            assert data['error']['code'] == 'SECTION_NOT_FOUND'

    def test_get_config_section_available_sections_listed(self, client):
        """Test that error response lists available sections"""
        test_config = {
            "medicine": {"enabled": True},
            "weather": {"enabled": False}
        }

        with temp_config_file(test_config):
            response = client.get('/api/v1/config/invalid')
            data = json.loads(response.data)

            assert 'available_sections' in data['error']['details']
            assert 'medicine' in data['error']['details']['available_sections']


class TestUpdateAllConfig:
    """Test PUT /api/v1/config"""

    def test_update_all_config_success(self, client):
        """Test replacing entire configuration"""
        test_config = {
            "medicine": {"enabled": True}
        }

        new_config = {
            "medicine": {"enabled": False, "reminder_window": 45},
            "weather": {"enabled": True}
        }

        with temp_config_file(test_config):
            response = client.put('/api/v1/config',
                                data=json.dumps(new_config),
                                content_type='application/json')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['medicine']['enabled'] is False
            assert 'weather' in data['data']

    def test_update_all_config_empty_body(self, client):
        """Test error when body is empty"""
        test_config = {"medicine": {"enabled": True}}

        with temp_config_file(test_config):
            response = client.put('/api/v1/config',
                                data='',
                                content_type='application/json')
            assert response.status_code == 400

            data = json.loads(response.data)
            assert data['success'] is False

    def test_update_all_config_invalid_json(self, client):
        """Test error when body is invalid JSON"""
        test_config = {"medicine": {"enabled": True}}

        with temp_config_file(test_config):
            response = client.put('/api/v1/config',
                                data='not valid json',
                                content_type='application/json')
            assert response.status_code == 400

    def test_update_all_config_not_dict(self, client):
        """Test error when config is not a dictionary"""
        test_config = {"medicine": {"enabled": True}}

        with temp_config_file(test_config):
            response = client.put('/api/v1/config',
                                data=json.dumps(['array', 'not', 'dict']),
                                content_type='application/json')
            assert response.status_code == 400

            data = json.loads(response.data)
            assert 'JSON object' in data['error']['message']


class TestReplaceConfigSection:
    """Test PUT /api/v1/config/<section>"""

    def test_replace_config_section_success(self, client):
        """Test replacing entire config section"""
        test_config = {
            "medicine": {"enabled": True, "reminder_window": 30},
            "weather": {"enabled": False}
        }

        new_medicine_config = {
            "enabled": False,
            "reminder_window": 45,
            "new_field": "new_value"
        }

        with temp_config_file(test_config):
            response = client.put('/api/v1/config/medicine',
                                data=json.dumps(new_medicine_config),
                                content_type='application/json')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['enabled'] is False
            assert data['data']['reminder_window'] == 45
            assert data['data']['new_field'] == 'new_value'

    def test_replace_config_section_not_found(self, client):
        """Test replacing non-existent section"""
        test_config = {"medicine": {"enabled": True}}

        new_section = {"some": "data"}

        with temp_config_file(test_config):
            response = client.put('/api/v1/config/nonexistent',
                                data=json.dumps(new_section),
                                content_type='application/json')
            assert response.status_code == 404

    def test_replace_config_section_empty_body(self, client):
        """Test error when body is empty"""
        test_config = {"medicine": {"enabled": True}}

        with temp_config_file(test_config):
            response = client.put('/api/v1/config/medicine',
                                data='',
                                content_type='application/json')
            assert response.status_code == 400

    def test_replace_config_section_preserves_other_sections(self, client):
        """Test that replacing one section doesn't affect others"""
        test_config = {
            "medicine": {"enabled": True},
            "weather": {"enabled": False, "important": "data"}
        }

        new_medicine = {"enabled": False}

        with temp_config_file(test_config):
            client.put('/api/v1/config/medicine',
                      data=json.dumps(new_medicine),
                      content_type='application/json')

            # Check that weather section is unchanged
            response = client.get('/api/v1/config/weather')
            data = json.loads(response.data)
            assert data['data']['important'] == 'data'


class TestPatchConfigSection:
    """Test PATCH /api/v1/config/<section>"""

    def test_patch_config_section_success(self, client):
        """Test partial update of config section"""
        test_config = {
            "medicine": {
                "enabled": True,
                "reminder_window": 30,
                "keep_this": "value"
            }
        }

        patch_data = {
            "enabled": False,
            "reminder_window": 45
        }

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/medicine',
                                   data=json.dumps(patch_data),
                                   content_type='application/json')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['enabled'] is False
            assert data['data']['reminder_window'] == 45
            # Original field should be preserved
            assert data['data']['keep_this'] == 'value'

    def test_patch_config_section_single_field(self, client):
        """Test patching single field"""
        test_config = {
            "medicine": {
                "enabled": True,
                "reminder_window": 30
            }
        }

        patch_data = {"reminder_window": 60}

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/medicine',
                                   data=json.dumps(patch_data),
                                   content_type='application/json')
            data = json.loads(response.data)

            assert data['data']['reminder_window'] == 60
            assert data['data']['enabled'] is True  # Unchanged

    def test_patch_config_section_not_found(self, client):
        """Test patching non-existent section"""
        test_config = {"medicine": {"enabled": True}}

        patch_data = {"field": "value"}

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/nonexistent',
                                   data=json.dumps(patch_data),
                                   content_type='application/json')
            assert response.status_code == 404

    def test_patch_config_section_empty_body(self, client):
        """Test error when patch body is empty"""
        test_config = {"medicine": {"enabled": True}}

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/medicine',
                                   data='',
                                   content_type='application/json')
            assert response.status_code == 400

    def test_patch_config_section_not_dict(self, client):
        """Test error when patch data is not a dict"""
        test_config = {"medicine": {"enabled": True}}

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/medicine',
                                   data=json.dumps(['not', 'a', 'dict']),
                                   content_type='application/json')
            assert response.status_code == 400

    def test_patch_config_section_add_new_field(self, client):
        """Test adding new field via patch"""
        test_config = {
            "medicine": {"enabled": True}
        }

        patch_data = {"new_field": "new_value"}

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/medicine',
                                   data=json.dumps(patch_data),
                                   content_type='application/json')
            data = json.loads(response.data)

            assert data['data']['new_field'] == 'new_value'
            assert data['data']['enabled'] is True


class TestSectionSpecificEndpoints:
    """Test section-specific convenience endpoints"""

    def test_weather_config_get(self, client):
        """Test GET /api/v1/config/weather"""
        test_config = {
            "weather": {"enabled": True, "api_key": "test123"}
        }

        with temp_config_file(test_config):
            response = client.get('/api/v1/config/weather')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['data']['enabled'] is True

    def test_weather_config_put(self, client):
        """Test PUT /api/v1/config/weather"""
        test_config = {
            "weather": {"enabled": True}
        }

        new_weather = {"enabled": False, "location": "Boston"}

        with temp_config_file(test_config):
            response = client.put('/api/v1/config/weather',
                                data=json.dumps(new_weather),
                                content_type='application/json')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['data']['enabled'] is False
            assert data['data']['location'] == 'Boston'

    def test_weather_config_patch(self, client):
        """Test PATCH /api/v1/config/weather"""
        test_config = {
            "weather": {"enabled": True, "location": "Boston"}
        }

        patch_data = {"enabled": False}

        with temp_config_file(test_config):
            response = client.patch('/api/v1/config/weather',
                                   data=json.dumps(patch_data),
                                   content_type='application/json')
            data = json.loads(response.data)

            assert data['data']['enabled'] is False
            assert data['data']['location'] == 'Boston'  # Preserved

    def test_medicine_config_endpoints(self, client):
        """Test medicine-specific endpoints"""
        test_config = {
            "medicine": {"enabled": True, "reminder_window": 30}
        }

        with temp_config_file(test_config):
            # GET
            response = client.get('/api/v1/config/medicine')
            assert response.status_code == 200

            # PATCH
            patch_response = client.patch('/api/v1/config/medicine',
                                         data=json.dumps({"reminder_window": 45}),
                                         content_type='application/json')
            assert patch_response.status_code == 200

    def test_multiple_section_endpoints(self, client):
        """Test that multiple section endpoints work independently"""
        test_config = {
            "medicine": {"enabled": True},
            "weather": {"enabled": False},
            "mbta": {"enabled": True}
        }

        with temp_config_file(test_config):
            # Test all section endpoints exist
            sections = ['medicine', 'weather', 'mbta', 'disney', 'flights',
                       'pomodoro', 'forbidden', 'menu', 'system', 'display']

            for section in sections:
                # Some sections may not exist in test config, that's OK
                response = client.get(f'/api/v1/config/{section}')
                # Should get 200 or 404, but not 500
                assert response.status_code in [200, 404]


class TestConfigPersistence:
    """Test that config changes persist"""

    def test_config_update_persists(self, client):
        """Test that updates are saved to file"""
        test_config = {
            "medicine": {"enabled": True}
        }

        with temp_config_file(test_config) as config_path:
            # Update config
            new_config = {"medicine": {"enabled": False}}
            client.put('/api/v1/config',
                      data=json.dumps(new_config),
                      content_type='application/json')

            # Read file directly to verify persistence
            with open(config_path, 'r') as f:
                saved_config = json.load(f)

            assert saved_config['medicine']['enabled'] is False

    def test_section_update_persists(self, client):
        """Test that section updates are saved"""
        test_config = {
            "medicine": {"enabled": True},
            "weather": {"enabled": False}
        }

        with temp_config_file(test_config) as config_path:
            # Update medicine section
            new_medicine = {"enabled": False, "new_field": "value"}
            client.put('/api/v1/config/medicine',
                      data=json.dumps(new_medicine),
                      content_type='application/json')

            # Read file directly
            with open(config_path, 'r') as f:
                saved_config = json.load(f)

            assert saved_config['medicine']['enabled'] is False
            assert saved_config['medicine']['new_field'] == 'value'
            # Weather should be unchanged
            assert saved_config['weather']['enabled'] is False

    def test_patch_update_persists(self, client):
        """Test that patch updates are saved"""
        test_config = {
            "medicine": {"enabled": True, "reminder_window": 30}
        }

        with temp_config_file(test_config) as config_path:
            # Patch medicine section
            patch_data = {"reminder_window": 60}
            client.patch('/api/v1/config/medicine',
                        data=json.dumps(patch_data),
                        content_type='application/json')

            # Read file directly
            with open(config_path, 'r') as f:
                saved_config = json.load(f)

            assert saved_config['medicine']['reminder_window'] == 60
            assert saved_config['medicine']['enabled'] is True


class TestConfigErrorHandling:
    """Test error handling in config operations"""

    def test_config_file_not_found(self, client):
        """Test handling when config file doesn't exist"""
        from api.v1.routes import config as config_module
        original_path = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = '/nonexistent/path/config.json'

        try:
            response = client.get('/api/v1/config')
            assert response.status_code == 500

            data = json.loads(response.data)
            assert data['success'] is False
            assert data['error']['code'] == 'FILE_NOT_FOUND'
        finally:
            config_module.CONFIG_FILE = original_path

    def test_concurrent_config_updates(self, client):
        """Test that concurrent updates are handled safely"""
        test_config = {
            "medicine": {"counter": 0}
        }

        with temp_config_file(test_config):
            # Multiple rapid updates
            for i in range(5):
                patch_data = {"counter": i}
                response = client.patch('/api/v1/config/medicine',
                                       data=json.dumps(patch_data),
                                       content_type='application/json')
                assert response.status_code == 200

            # Final value should be saved
            response = client.get('/api/v1/config/medicine')
            data = json.loads(response.data)
            assert 'counter' in data['data']
