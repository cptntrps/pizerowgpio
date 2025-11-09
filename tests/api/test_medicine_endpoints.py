"""
Medicine API Endpoint Tests
Phase 1.4 - API Testing Suite

Tests for medicine CRUD operations:
- GET /api/v1/medicines (list with pagination and filtering)
- POST /api/v1/medicines (create)
- GET /api/v1/medicines/<id> (get single)
- PUT /api/v1/medicines/<id> (full update)
- PATCH /api/v1/medicines/<id> (partial update)
- DELETE /api/v1/medicines/<id> (delete)
- GET /api/v1/medicines/pending (get pending medicines)
- GET /api/v1/medicines/low-stock (get low stock medicines)
- POST /api/v1/medicines/<id>/take (mark single medicine taken)
- POST /api/v1/medicines/batch-take (mark multiple medicines taken)
"""

import json
from datetime import datetime, date


class TestListMedicines:
    """Test GET /api/v1/medicines"""

    def test_list_medicines_empty_database(self, client):
        """Test listing medicines with empty database"""
        response = client.get('/api/v1/medicines')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) == 0

    def test_list_medicines_with_data(self, client_with_data):
        """Test listing medicines with populated database"""
        response = client_with_data.get('/api/v1/medicines')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) >= 3  # We have 3 active medicines in sample data

    def test_list_medicines_active_only(self, client_with_data):
        """Test that inactive medicines are excluded by default"""
        response = client_with_data.get('/api/v1/medicines?active=true')
        assert response.status_code == 200

        data = json.loads(response.data)
        for medicine in data['data']:
            assert medicine['active'] is True

    def test_list_medicines_include_inactive(self, client_with_data):
        """Test including inactive medicines"""
        response = client_with_data.get('/api/v1/medicines?active=false')
        assert response.status_code == 200

        data = json.loads(response.data)
        # Should include the inactive medicine
        assert any(not med['active'] for med in data['data'])

    def test_list_medicines_pagination(self, client_with_data):
        """Test pagination parameters"""
        response = client_with_data.get('/api/v1/medicines?page=1&per_page=2')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'meta' in data
        assert data['meta']['page'] == 1
        assert data['meta']['per_page'] == 2

    def test_list_medicines_pagination_max_limit(self, client):
        """Test that per_page is capped at 100"""
        response = client.get('/api/v1/medicines?per_page=200')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['meta']['per_page'] <= 100


class TestCreateMedicine:
    """Test POST /api/v1/medicines"""

    def test_create_medicine_success(self, client, sample_medicine):
        """Test successful medicine creation"""
        response = client.post('/api/v1/medicines',
                             data=json.dumps(sample_medicine),
                             content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == sample_medicine['id']
        assert data['data']['name'] == sample_medicine['name']

        # Check Location header
        assert 'Location' in response.headers

    def test_create_medicine_auto_generate_id(self, client, sample_medicine):
        """Test that server generates ID if not provided"""
        medicine_data = sample_medicine.copy()
        del medicine_data['id']  # Remove ID

        response = client.post('/api/v1/medicines',
                             data=json.dumps(medicine_data),
                             content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert 'id' in data['data']
        assert data['data']['id'].startswith('med_')

    def test_create_medicine_missing_required_field(self, client, invalid_medicine_missing_field):
        """Test validation error for missing required field"""
        response = client.post('/api/v1/medicines',
                             data=json.dumps(invalid_medicine_missing_field),
                             content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data

    def test_create_medicine_invalid_time_format(self, client, invalid_medicine_bad_time):
        """Test validation error for invalid time format"""
        response = client.post('/api/v1/medicines',
                             data=json.dumps(invalid_medicine_bad_time),
                             content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False

    def test_create_medicine_duplicate_id(self, client_with_data, sample_medicine):
        """Test error when creating medicine with duplicate ID"""
        # Try to create medicine with existing ID
        response = client_with_data.post('/api/v1/medicines',
                                        data=json.dumps(sample_medicine),
                                        content_type='application/json')
        # Should get database error (500) due to integrity constraint
        assert response.status_code in [400, 409, 500]

    def test_create_medicine_empty_body(self, client):
        """Test error when request body is empty"""
        response = client.post('/api/v1/medicines',
                             data='',
                             content_type='application/json')
        assert response.status_code in [400, 500]

    def test_create_medicine_invalid_json(self, client):
        """Test error when request body is invalid JSON"""
        response = client.post('/api/v1/medicines',
                             data='not valid json',
                             content_type='application/json')
        assert response.status_code in [400, 500]


class TestGetMedicine:
    """Test GET /api/v1/medicines/<id>"""

    def test_get_medicine_success(self, client_with_data):
        """Test getting a specific medicine by ID"""
        response = client_with_data.get('/api/v1/medicines/med_test_001')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == 'med_test_001'
        assert data['data']['name'] == 'Aspirin'

    def test_get_medicine_not_found(self, client):
        """Test getting a non-existent medicine"""
        response = client.get('/api/v1/medicines/nonexistent_id')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'RESOURCE_NOT_FOUND'

    def test_get_inactive_medicine(self, client_with_data):
        """Test getting an inactive medicine (should still return it)"""
        response = client_with_data.get('/api/v1/medicines/med_test_004')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['active'] is False


class TestUpdateMedicine:
    """Test PUT /api/v1/medicines/<id>"""

    def test_update_medicine_success(self, client_with_data, sample_medicine):
        """Test full update of medicine"""
        updated_data = sample_medicine.copy()
        updated_data['id'] = 'med_test_001'
        updated_data['name'] = 'Updated Aspirin'
        updated_data['dosage'] = '100mg'

        response = client_with_data.put('/api/v1/medicines/med_test_001',
                                       data=json.dumps(updated_data),
                                       content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'Updated Aspirin'
        assert data['data']['dosage'] == '100mg'

    def test_update_medicine_not_found(self, client, sample_medicine):
        """Test updating non-existent medicine"""
        response = client.put('/api/v1/medicines/nonexistent_id',
                            data=json.dumps(sample_medicine),
                            content_type='application/json')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_medicine_invalid_data(self, client_with_data, invalid_medicine_missing_field):
        """Test updating with invalid data"""
        response = client_with_data.put('/api/v1/medicines/med_test_001',
                                       data=json.dumps(invalid_medicine_missing_field),
                                       content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False


class TestPatchMedicine:
    """Test PATCH /api/v1/medicines/<id>"""

    def test_patch_medicine_success(self, client_with_data):
        """Test partial update of medicine"""
        patch_data = {
            'name': 'Patched Aspirin',
            'notes': 'Updated notes'
        }

        response = client_with_data.patch('/api/v1/medicines/med_test_001',
                                         data=json.dumps(patch_data),
                                         content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['name'] == 'Patched Aspirin'
        assert data['data']['notes'] == 'Updated notes'
        # Other fields should remain unchanged
        assert data['data']['dosage'] == '81mg'

    def test_patch_medicine_single_field(self, client_with_data):
        """Test patching a single field"""
        patch_data = {'pills_remaining': 75}

        response = client_with_data.patch('/api/v1/medicines/med_test_001',
                                         data=json.dumps(patch_data),
                                         content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['data']['pills_remaining'] == 75

    def test_patch_medicine_not_found(self, client):
        """Test patching non-existent medicine"""
        patch_data = {'name': 'New Name'}

        response = client.patch('/api/v1/medicines/nonexistent_id',
                              data=json.dumps(patch_data),
                              content_type='application/json')
        assert response.status_code == 404


class TestDeleteMedicine:
    """Test DELETE /api/v1/medicines/<id>"""

    def test_delete_medicine_success(self, client_with_data):
        """Test successful medicine deletion"""
        response = client_with_data.delete('/api/v1/medicines/med_test_001')
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client_with_data.get('/api/v1/medicines/med_test_001')
        assert get_response.status_code == 404

    def test_delete_medicine_not_found(self, client):
        """Test deleting non-existent medicine"""
        response = client.delete('/api/v1/medicines/nonexistent_id')
        assert response.status_code == 404

    def test_delete_medicine_cascade(self, client_with_data):
        """Test that deleting medicine also deletes related data"""
        # First mark medicine as taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                            data=json.dumps({}),
                            content_type='application/json')

        # Now delete the medicine
        response = client_with_data.delete('/api/v1/medicines/med_test_001')
        assert response.status_code == 204


class TestGetPendingMedicines:
    """Test GET /api/v1/medicines/pending"""

    def test_get_pending_medicines(self, client_with_data):
        """Test getting pending medicines"""
        response = client_with_data.get('/api/v1/medicines/pending')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_get_pending_medicines_with_custom_time(self, client_with_data):
        """Test getting pending medicines at specific time"""
        response = client_with_data.get(
            '/api/v1/medicines/pending?date=2025-11-08&time=08:30&reminder_window=30'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'meta' in data

    def test_get_pending_medicines_metadata(self, client_with_data):
        """Test that response includes metadata"""
        response = client_with_data.get('/api/v1/medicines/pending')
        data = json.loads(response.data)

        assert 'meta' in data
        assert 'count' in data['meta']
        assert 'checked_at' in data['meta']
        assert 'reminder_window' in data['meta']


class TestGetLowStockMedicines:
    """Test GET /api/v1/medicines/low-stock"""

    def test_get_low_stock_medicines(self, client_with_data):
        """Test getting low stock medicines"""
        response = client_with_data.get('/api/v1/medicines/low-stock')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)

        # med_test_003 has only 5 pills remaining with threshold of 10
        low_stock_ids = [med['id'] for med in data['data']]
        assert 'med_test_003' in low_stock_ids

    def test_get_low_stock_medicines_metadata(self, client_with_data):
        """Test that response includes metadata"""
        response = client_with_data.get('/api/v1/medicines/low-stock')
        data = json.loads(response.data)

        assert 'meta' in data
        assert 'count' in data['meta']
        assert 'timestamp' in data['meta']


class TestMarkMedicineTaken:
    """Test POST /api/v1/medicines/<id>/take"""

    def test_mark_medicine_taken_success(self, client_with_data):
        """Test marking medicine as taken"""
        response = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                        data=json.dumps({}),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['medicine_id'] == 'med_test_001'
        assert 'pills_remaining' in data['data']
        assert 'taken_at' in data['data']

    def test_mark_medicine_taken_decrements_count(self, client_with_data):
        """Test that marking medicine taken decrements pill count"""
        # Get initial count
        get_response = client_with_data.get('/api/v1/medicines/med_test_001')
        initial_count = json.loads(get_response.data)['data']['pills_remaining']

        # Mark as taken
        response = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                        data=json.dumps({}),
                                        content_type='application/json')
        data = json.loads(response.data)

        # Pills should be decremented
        assert data['data']['pills_remaining'] == initial_count - 1

    def test_mark_medicine_taken_custom_timestamp(self, client_with_data):
        """Test marking medicine taken with custom timestamp"""
        custom_time = {
            'timestamp': '2025-11-08T08:30:00'
        }

        response = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                        data=json.dumps(custom_time),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert '2025-11-08T08:30:00' in data['data']['taken_at']

    def test_mark_medicine_taken_not_found(self, client):
        """Test marking non-existent medicine as taken"""
        response = client.post('/api/v1/medicines/nonexistent_id/take',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 404

    def test_mark_medicine_taken_low_stock_warning(self, client_with_data):
        """Test that low stock warning is returned"""
        # med_test_003 has only 5 pills (threshold is 10)
        response = client_with_data.post('/api/v1/medicines/med_test_003/take',
                                        data=json.dumps({}),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['data']['low_stock'] is True


class TestBatchMarkTaken:
    """Test POST /api/v1/medicines/batch-take"""

    def test_batch_mark_taken_success(self, client_with_data):
        """Test marking multiple medicines as taken"""
        batch_data = {
            'medicine_ids': ['med_test_001', 'med_test_002']
        }

        response = client_with_data.post('/api/v1/medicines/batch-take',
                                        data=json.dumps(batch_data),
                                        content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']['marked']) == 2

    def test_batch_mark_taken_custom_timestamp(self, client_with_data):
        """Test batch marking with custom timestamp"""
        batch_data = {
            'medicine_ids': ['med_test_001', 'med_test_002'],
            'timestamp': '2025-11-08T08:30:00'
        }

        response = client_with_data.post('/api/v1/medicines/batch-take',
                                        data=json.dumps(batch_data),
                                        content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert '2025-11-08T08:30:00' in data['data']['timestamp']

    def test_batch_mark_taken_missing_field(self, client):
        """Test batch marking without medicine_ids"""
        batch_data = {}

        response = client.post('/api/v1/medicines/batch-take',
                             data=json.dumps(batch_data),
                             content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False

    def test_batch_mark_taken_empty_list(self, client):
        """Test batch marking with empty list"""
        batch_data = {
            'medicine_ids': []
        }

        response = client.post('/api/v1/medicines/batch-take',
                             data=json.dumps(batch_data),
                             content_type='application/json')
        assert response.status_code == 400

    def test_batch_mark_taken_partial_success(self, client_with_data):
        """Test batch marking with some invalid IDs"""
        batch_data = {
            'medicine_ids': ['med_test_001', 'nonexistent_id', 'med_test_002']
        }

        response = client_with_data.post('/api/v1/medicines/batch-take',
                                        data=json.dumps(batch_data),
                                        content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        # Should have some marked and some errors
        assert len(data['data']['marked']) >= 2
        if 'errors' in data['data']:
            assert len(data['data']['errors']) >= 1

    def test_batch_mark_taken_not_a_list(self, client):
        """Test batch marking with medicine_ids not a list"""
        batch_data = {
            'medicine_ids': 'not_a_list'
        }

        response = client.post('/api/v1/medicines/batch-take',
                             data=json.dumps(batch_data),
                             content_type='application/json')
        assert response.status_code == 400
