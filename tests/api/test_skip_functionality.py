"""
Skip Functionality Tests
Tests for medicine skip tracking feature

Tests:
- POST /api/v1/tracking/skip (skip a medicine)
- GET /api/v1/tracking/skip-history (get skip history)
- GET /api/v1/tracking/adherence-detailed (get detailed adherence stats)
"""

import json
from datetime import datetime, date, timedelta


class TestSkipMedicine:
    """Test POST /api/v1/tracking/skip"""

    def test_skip_medicine_success(self, client_with_data):
        """Test skipping a medicine successfully"""
        skip_data = {
            'medicine_id': 'med_test_001',
            'skip_reason': 'Forgot'
        }

        response = client_with_data.post('/api/v1/tracking/skip',
                                        data=json.dumps(skip_data),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['medicine_id'] == 'med_test_001'
        assert data['data']['skip_reason'] == 'Forgot'
        assert 'skip_timestamp' in data['data']

    def test_skip_medicine_with_all_fields(self, client_with_data):
        """Test skipping with all optional fields"""
        skip_data = {
            'medicine_id': 'med_test_001',
            'time_window': 'morning',
            'skip_reason': 'Side effects',
            'skip_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'Had nausea this morning'
        }

        response = client_with_data.post('/api/v1/tracking/skip',
                                        data=json.dumps(skip_data),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['data']['skip_reason'] == 'Side effects'
        assert data['data']['time_window'] == 'morning'

    def test_skip_medicine_different_reasons(self, client_with_data):
        """Test skipping with different reasons"""
        reasons = ['Forgot', 'Side effects', 'Out of stock', 'Doctor advised', 'Other']

        for reason in reasons:
            skip_data = {
                'medicine_id': 'med_test_001',
                'skip_reason': reason
            }

            response = client_with_data.post('/api/v1/tracking/skip',
                                            data=json.dumps(skip_data),
                                            content_type='application/json')
            assert response.status_code == 201

            data = json.loads(response.data)
            assert data['data']['skip_reason'] == reason

    def test_skip_medicine_not_found(self, client):
        """Test skipping non-existent medicine"""
        skip_data = {
            'medicine_id': 'med_nonexistent_999',
            'skip_reason': 'Forgot'
        }

        response = client.post('/api/v1/tracking/skip',
                              data=json.dumps(skip_data),
                              content_type='application/json')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'RESOURCE_NOT_FOUND'

    def test_skip_medicine_missing_required_field(self, client):
        """Test skipping without required field"""
        skip_data = {
            'skip_reason': 'Forgot'
            # Missing medicine_id
        }

        response = client.post('/api/v1/tracking/skip',
                              data=json.dumps(skip_data),
                              content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_skip_medicine_invalid_reason(self, client_with_data):
        """Test skipping with invalid reason"""
        skip_data = {
            'medicine_id': 'med_test_001',
            'skip_reason': 'Invalid reason that is not in the list'
        }

        response = client_with_data.post('/api/v1/tracking/skip',
                                        data=json.dumps(skip_data),
                                        content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'VALIDATION_ERROR' in data['error']['code']

    def test_skip_medicine_invalid_time_window(self, client_with_data):
        """Test skipping with invalid time window"""
        skip_data = {
            'medicine_id': 'med_test_001',
            'time_window': 'invalid_window',
            'skip_reason': 'Forgot'
        }

        response = client_with_data.post('/api/v1/tracking/skip',
                                        data=json.dumps(skip_data),
                                        content_type='application/json')
        assert response.status_code == 400

    def test_skip_medicine_no_pill_decrement(self, client_with_data):
        """Test that skipping doesn't decrement pill count"""
        # Get initial pill count
        med_response = client_with_data.get('/api/v1/medicines/med_test_001')
        initial_pills = json.loads(med_response.data)['data']['pills_remaining']

        # Skip medicine
        skip_data = {
            'medicine_id': 'med_test_001',
            'skip_reason': 'Forgot'
        }
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps(skip_data),
                             content_type='application/json')

        # Check pill count hasn't changed
        med_response = client_with_data.get('/api/v1/medicines/med_test_001')
        final_pills = json.loads(med_response.data)['data']['pills_remaining']

        assert final_pills == initial_pills

    def test_skip_same_medicine_twice_same_day(self, client_with_data):
        """Test skipping same medicine twice on same day updates record"""
        skip_data = {
            'medicine_id': 'med_test_001',
            'skip_reason': 'Forgot'
        }

        # Skip first time
        response1 = client_with_data.post('/api/v1/tracking/skip',
                                         data=json.dumps(skip_data),
                                         content_type='application/json')
        assert response1.status_code == 201

        # Skip second time with different reason
        skip_data['skip_reason'] = 'Side effects'
        response2 = client_with_data.post('/api/v1/tracking/skip',
                                         data=json.dumps(skip_data),
                                         content_type='application/json')
        assert response2.status_code == 201

        # Should update, not duplicate
        data = json.loads(response2.data)
        assert data['data']['skip_reason'] == 'Side effects'


class TestGetSkipHistory:
    """Test GET /api/v1/tracking/skip-history"""

    def test_get_skip_history_empty(self, client_with_data):
        """Test getting skip history with no skips"""
        response = client_with_data.get('/api/v1/tracking/skip-history')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_get_skip_history_with_skips(self, client_with_data):
        """Test getting skip history after skipping medicines"""
        # Skip a medicine
        skip_data = {
            'medicine_id': 'med_test_001',
            'skip_reason': 'Forgot'
        }
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps(skip_data),
                             content_type='application/json')

        # Get skip history
        response = client_with_data.get('/api/v1/tracking/skip-history')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data['data']) > 0

        # Verify skip record has expected fields
        skip_record = data['data'][0]
        assert 'medicine_id' in skip_record
        assert 'skip_reason' in skip_record
        assert 'skip_timestamp' in skip_record
        assert 'name' in skip_record  # Medicine name joined

    def test_get_skip_history_filter_by_medicine(self, client_with_data):
        """Test filtering skip history by medicine ID"""
        # Skip two different medicines
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_001', 'skip_reason': 'Forgot'}),
                             content_type='application/json')
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_002', 'skip_reason': 'Forgot'}),
                             content_type='application/json')

        # Filter by med_test_001
        response = client_with_data.get('/api/v1/tracking/skip-history?medicine_id=med_test_001')
        data = json.loads(response.data)

        # All records should be for med_test_001
        for record in data['data']:
            assert record['medicine_id'] == 'med_test_001'

    def test_get_skip_history_date_range(self, client_with_data):
        """Test filtering skip history by date range"""
        # Skip a medicine
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_001', 'skip_reason': 'Forgot'}),
                             content_type='application/json')

        # Query with date range
        start_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')

        response = client_with_data.get(
            f'/api/v1/tracking/skip-history?start_date={start_date}&end_date={end_date}'
        )
        assert response.status_code == 200

    def test_get_skip_history_invalid_date(self, client):
        """Test error with invalid date format"""
        response = client.get('/api/v1/tracking/skip-history?start_date=invalid')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'VALIDATION_ERROR' in data['error']['code']

    def test_get_skip_history_pagination(self, client_with_data):
        """Test pagination of skip history"""
        # Skip multiple times
        for i in range(5):
            client_with_data.post('/api/v1/tracking/skip',
                                 data=json.dumps({'medicine_id': 'med_test_001', 'skip_reason': 'Forgot'}),
                                 content_type='application/json')

        response = client_with_data.get('/api/v1/tracking/skip-history?page=1&per_page=2')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'meta' in data
        assert data['meta']['per_page'] == 2


class TestGetAdherenceDetailed:
    """Test GET /api/v1/tracking/adherence-detailed"""

    def test_get_adherence_detailed_default(self, client_with_data):
        """Test getting detailed adherence with default period"""
        response = client_with_data.get('/api/v1/tracking/adherence-detailed')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'taken' in data['data']
        assert 'skipped' in data['data']
        assert 'missed' in data['data']
        assert 'total' in data['data']
        assert 'adherence_rate' in data['data']
        assert 'skip_rate' in data['data']

    def test_get_adherence_detailed_with_data(self, client_with_data):
        """Test detailed adherence after tracking activities"""
        # Mark one taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')

        # Skip one
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_002', 'skip_reason': 'Forgot'}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking/adherence-detailed')
        data = json.loads(response.data)

        assert data['data']['taken'] >= 1
        assert data['data']['skipped'] >= 1
        assert data['data']['total'] >= 2

    def test_get_adherence_detailed_rates(self, client_with_data):
        """Test adherence and skip rate calculations"""
        response = client_with_data.get('/api/v1/tracking/adherence-detailed')
        data = json.loads(response.data)

        # Rates should be percentages between 0 and 100
        assert 0 <= data['data']['adherence_rate'] <= 100
        assert 0 <= data['data']['skip_rate'] <= 100

    def test_get_adherence_detailed_custom_date_range(self, client_with_data):
        """Test detailed adherence with custom date range"""
        start_date = (date.today() - timedelta(days=14)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')

        response = client_with_data.get(
            f'/api/v1/tracking/adherence-detailed?start_date={start_date}&end_date={end_date}'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_adherence_detailed_invalid_date(self, client):
        """Test error with invalid date format"""
        response = client.get('/api/v1/tracking/adherence-detailed?start_date=invalid')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'VALIDATION_ERROR' in data['error']['code']

    def test_get_adherence_detailed_empty(self, client_with_data):
        """Test detailed adherence with no tracking data"""
        # Use future date range with no data
        start_date = (date.today() + timedelta(days=100)).strftime('%Y-%m-%d')
        end_date = (date.today() + timedelta(days=130)).strftime('%Y-%m-%d')

        response = client_with_data.get(
            f'/api/v1/tracking/adherence-detailed?start_date={start_date}&end_date={end_date}'
        )
        data = json.loads(response.data)

        assert data['data']['total'] == 0
        assert data['data']['taken'] == 0
        assert data['data']['skipped'] == 0


class TestTodayStatsWithSkip:
    """Test GET /api/v1/tracking/today with skip support"""

    def test_today_stats_includes_skipped(self, client_with_data):
        """Test that today's stats include skipped count"""
        response = client_with_data.get('/api/v1/tracking/today')
        data = json.loads(response.data)

        assert 'medicines_skipped' in data['data']
        assert isinstance(data['data']['medicines_skipped'], int)

    def test_today_stats_after_skip(self, client_with_data):
        """Test today's stats after skipping a medicine"""
        # Skip a medicine
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_001', 'skip_reason': 'Forgot'}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking/today')
        data = json.loads(response.data)

        assert data['data']['medicines_skipped'] >= 1

    def test_today_stats_pending_calculation(self, client_with_data):
        """Test that pending medicines excludes both taken and skipped"""
        # Mark one taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')

        # Skip one
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_002', 'skip_reason': 'Forgot'}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking/today')
        data = json.loads(response.data)

        # Pending should be total - taken - skipped
        expected_pending = (data['data']['total_medicines'] -
                          data['data']['medicines_taken'] -
                          data['data']['medicines_skipped'])

        assert data['data']['medicines_pending'] == expected_pending


class TestSkipEdgeCases:
    """Test edge cases in skip functionality"""

    def test_skip_then_mark_taken(self, client_with_data):
        """Test marking taken after skipping (should update to taken)"""
        # First skip
        client_with_data.post('/api/v1/tracking/skip',
                             data=json.dumps({'medicine_id': 'med_test_001', 'skip_reason': 'Forgot'}),
                             content_type='application/json')

        # Then mark as taken
        response = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                        data=json.dumps({}),
                                        content_type='application/json')
        assert response.status_code == 201

    def test_mark_taken_then_skip(self, client_with_data):
        """Test skipping after marking taken (should update to skipped)"""
        # First mark taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')

        # Then skip
        response = client_with_data.post('/api/v1/tracking/skip',
                                        data=json.dumps({'medicine_id': 'med_test_001', 'skip_reason': 'Forgot'}),
                                        content_type='application/json')
        assert response.status_code == 201

    def test_skip_without_reason(self, client_with_data):
        """Test skipping without providing a reason (should be optional)"""
        skip_data = {
            'medicine_id': 'med_test_001'
            # No skip_reason
        }

        response = client_with_data.post('/api/v1/tracking/skip',
                                        data=json.dumps(skip_data),
                                        content_type='application/json')
        # Should succeed - reason is optional
        assert response.status_code == 201

    def test_skip_empty_body(self, client):
        """Test skipping with empty request body"""
        response = client.post('/api/v1/tracking/skip',
                              data=json.dumps({}),
                              content_type='application/json')
        assert response.status_code == 400

    def test_skip_no_body(self, client):
        """Test skipping with no request body"""
        response = client.post('/api/v1/tracking/skip',
                              content_type='application/json')
        assert response.status_code == 400
