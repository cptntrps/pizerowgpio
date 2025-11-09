"""
Tracking API Endpoint Tests
Phase 1.4 - API Testing Suite

Tests for tracking operations:
- GET /api/v1/medicines/<id>/tracking (get medicine tracking history)
- POST /api/v1/medicines/<id>/tracking (mark medicine taken)
- GET /api/v1/tracking (get all tracking history)
- POST /api/v1/tracking (batch mark medicines taken)
- GET /api/v1/tracking/today (get today's statistics)
- GET /api/v1/tracking/stats (get adherence statistics)
"""

import json
from datetime import datetime, date, timedelta


class TestGetMedicineTracking:
    """Test GET /api/v1/medicines/<id>/tracking"""

    def test_get_medicine_tracking_empty(self, client_with_data):
        """Test getting tracking history with no records"""
        response = client_with_data.get('/api/v1/medicines/med_test_001/tracking')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) == 0

    def test_get_medicine_tracking_with_records(self, client_with_data):
        """Test getting tracking history after marking taken"""
        # First mark medicine as taken
        client_with_data.post('/api/v1/medicines/med_test_001/tracking',
                             data=json.dumps({}),
                             content_type='application/json')

        # Now get tracking history
        response = client_with_data.get('/api/v1/medicines/med_test_001/tracking')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) > 0

    def test_get_medicine_tracking_not_found(self, client):
        """Test getting tracking for non-existent medicine"""
        response = client.get('/api/v1/medicines/nonexistent_id/tracking')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'RESOURCE_NOT_FOUND'

    def test_get_medicine_tracking_with_date_range(self, client_with_data):
        """Test getting tracking history with date filtering"""
        start_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')

        response = client_with_data.get(
            f'/api/v1/medicines/med_test_001/tracking?start_date={start_date}&end_date={end_date}'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_medicine_tracking_invalid_date_format(self, client_with_data):
        """Test error with invalid date format"""
        response = client_with_data.get(
            '/api/v1/medicines/med_test_001/tracking?start_date=invalid-date'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_get_medicine_tracking_pagination(self, client_with_data):
        """Test pagination of tracking history"""
        # Mark medicine taken multiple times
        for _ in range(5):
            client_with_data.post('/api/v1/medicines/med_test_001/tracking',
                                 data=json.dumps({}),
                                 content_type='application/json')

        response = client_with_data.get(
            '/api/v1/medicines/med_test_001/tracking?page=1&per_page=2'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'meta' in data
        assert data['meta']['page'] == 1
        assert data['meta']['per_page'] == 2


class TestMarkSpecificMedicineTaken:
    """Test POST /api/v1/medicines/<id>/tracking"""

    def test_mark_specific_medicine_taken_success(self, client_with_data):
        """Test marking specific medicine as taken via tracking endpoint"""
        response = client_with_data.post('/api/v1/medicines/med_test_001/tracking',
                                        data=json.dumps({}),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['medicine_id'] == 'med_test_001'
        assert 'pills_remaining' in data['data']

    def test_mark_specific_medicine_taken_custom_timestamp(self, client_with_data):
        """Test marking with custom timestamp"""
        custom_data = {
            'timestamp': '2025-11-08T08:30:00'
        }

        response = client_with_data.post('/api/v1/medicines/med_test_001/tracking',
                                        data=json.dumps(custom_data),
                                        content_type='application/json')
        assert response.status_code == 201

        data = json.loads(response.data)
        assert '2025-11-08T08:30:00' in data['data']['taken_at']

    def test_mark_specific_medicine_taken_not_found(self, client):
        """Test marking non-existent medicine"""
        response = client.post('/api/v1/medicines/nonexistent_id/tracking',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 404


class TestGetAllTracking:
    """Test GET /api/v1/tracking"""

    def test_get_all_tracking_empty(self, client_with_data):
        """Test getting all tracking with no records"""
        response = client_with_data.get('/api/v1/tracking')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_get_all_tracking_with_records(self, client_with_data):
        """Test getting all tracking after marking medicines taken"""
        # Mark multiple medicines taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')
        client_with_data.post('/api/v1/medicines/med_test_002/take',
                             data=json.dumps({}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data['data']) >= 2

    def test_get_all_tracking_filter_by_medicine(self, client_with_data):
        """Test filtering tracking by medicine ID"""
        # Mark medicines taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')
        client_with_data.post('/api/v1/medicines/med_test_002/take',
                             data=json.dumps({}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking?medicine_id=med_test_001')
        assert response.status_code == 200

        data = json.loads(response.data)
        for record in data['data']:
            assert record['medicine_id'] == 'med_test_001'

    def test_get_all_tracking_date_range(self, client_with_data):
        """Test filtering tracking by date range"""
        start_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')

        response = client_with_data.get(
            f'/api/v1/tracking?start_date={start_date}&end_date={end_date}'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_all_tracking_invalid_date(self, client):
        """Test error with invalid date format"""
        response = client.get('/api/v1/tracking?start_date=invalid')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False

    def test_get_all_tracking_pagination(self, client_with_data):
        """Test pagination of all tracking"""
        response = client_with_data.get('/api/v1/tracking?page=1&per_page=5')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'meta' in data
        assert data['meta']['per_page'] == 5


class TestBatchMarkMedicinesTaken:
    """Test POST /api/v1/tracking"""

    def test_batch_mark_taken_success(self, client_with_data):
        """Test batch marking medicines as taken"""
        batch_data = {
            'medicine_ids': ['med_test_001', 'med_test_002']
        }

        response = client_with_data.post('/api/v1/tracking',
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

        response = client_with_data.post('/api/v1/tracking',
                                        data=json.dumps(batch_data),
                                        content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert '2025-11-08T08:30:00' in data['data']['timestamp']

    def test_batch_mark_taken_missing_field(self, client):
        """Test batch marking without required field"""
        response = client.post('/api/v1/tracking',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'medicine_ids' in data['error']['message']

    def test_batch_mark_taken_empty_list(self, client):
        """Test batch marking with empty medicine list"""
        batch_data = {
            'medicine_ids': []
        }

        response = client.post('/api/v1/tracking',
                             data=json.dumps(batch_data),
                             content_type='application/json')
        assert response.status_code == 400

    def test_batch_mark_taken_invalid_type(self, client):
        """Test batch marking with invalid medicine_ids type"""
        batch_data = {
            'medicine_ids': 'not_a_list'
        }

        response = client.post('/api/v1/tracking',
                             data=json.dumps(batch_data),
                             content_type='application/json')
        assert response.status_code == 400

    def test_batch_mark_taken_partial_failures(self, client_with_data):
        """Test batch marking with some invalid medicine IDs"""
        batch_data = {
            'medicine_ids': ['med_test_001', 'invalid_id', 'med_test_002']
        }

        response = client_with_data.post('/api/v1/tracking',
                                        data=json.dumps(batch_data),
                                        content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        # Should have successful marks
        assert len(data['data']['marked']) >= 2
        # May have errors
        if 'errors' in data['data']:
            assert len(data['data']['errors']) >= 1

    def test_batch_mark_taken_metadata(self, client_with_data):
        """Test that batch operation includes metadata"""
        batch_data = {
            'medicine_ids': ['med_test_001', 'med_test_002']
        }

        response = client_with_data.post('/api/v1/tracking',
                                        data=json.dumps(batch_data),
                                        content_type='application/json')
        data = json.loads(response.data)

        assert 'meta' in data
        assert 'count' in data['meta']
        assert data['meta']['count'] == 2


class TestGetTodayStats:
    """Test GET /api/v1/tracking/today"""

    def test_get_today_stats_no_data(self, client_with_data):
        """Test getting today's stats with no tracking data"""
        response = client_with_data.get('/api/v1/tracking/today')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total_medicines' in data['data']
        assert 'medicines_taken' in data['data']
        assert 'medicines_pending' in data['data']
        assert 'adherence_rate' in data['data']

    def test_get_today_stats_with_data(self, client_with_data):
        """Test getting today's stats after marking medicines taken"""
        # Mark one medicine as taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking/today')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['data']['medicines_taken'] >= 1
        assert data['data']['total_medicines'] >= 1

    def test_get_today_stats_adherence_rate(self, client_with_data):
        """Test that adherence rate is calculated correctly"""
        response = client_with_data.get('/api/v1/tracking/today')
        data = json.loads(response.data)

        # Adherence rate should be between 0 and 1
        assert 0 <= data['data']['adherence_rate'] <= 1

    def test_get_today_stats_custom_date(self, client_with_data):
        """Test getting stats for specific date"""
        check_date = date.today().strftime('%Y-%m-%d')
        response = client_with_data.get(f'/api/v1/tracking/today?date={check_date}')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['data']['date'] == check_date

    def test_get_today_stats_invalid_date(self, client):
        """Test error with invalid date format"""
        response = client.get('/api/v1/tracking/today?date=invalid-date')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False

    def test_get_today_stats_low_stock_count(self, client_with_data):
        """Test that low stock count is included"""
        response = client_with_data.get('/api/v1/tracking/today')
        data = json.loads(response.data)

        assert 'low_stock_count' in data['data']
        # med_test_003 has low stock
        assert data['data']['low_stock_count'] >= 1


class TestGetAdherenceStats:
    """Test GET /api/v1/tracking/stats"""

    def test_get_adherence_stats_default_period(self, client_with_data):
        """Test getting adherence stats with default period (7 days)"""
        response = client_with_data.get('/api/v1/tracking/stats')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'period' in data['data']
        assert 'overall' in data['data']
        assert 'daily' in data['data']

    def test_get_adherence_stats_period_info(self, client_with_data):
        """Test that period information is correct"""
        response = client_with_data.get('/api/v1/tracking/stats')
        data = json.loads(response.data)

        period = data['data']['period']
        assert 'start_date' in period
        assert 'end_date' in period
        assert 'days' in period

    def test_get_adherence_stats_overall_metrics(self, client_with_data):
        """Test overall adherence metrics"""
        response = client_with_data.get('/api/v1/tracking/stats')
        data = json.loads(response.data)

        overall = data['data']['overall']
        assert 'total_records' in overall
        assert 'taken_records' in overall
        assert 'adherence_rate' in overall
        assert 0 <= overall['adherence_rate'] <= 1

    def test_get_adherence_stats_daily_breakdown(self, client_with_data):
        """Test daily breakdown of adherence"""
        response = client_with_data.get('/api/v1/tracking/stats')
        data = json.loads(response.data)

        daily = data['data']['daily']
        assert isinstance(daily, list)

        # Each daily entry should have required fields
        for day_data in daily:
            assert 'date' in day_data
            assert 'total' in day_data
            assert 'taken' in day_data
            assert 'adherence_rate' in day_data

    def test_get_adherence_stats_custom_date_range(self, client_with_data):
        """Test getting stats for custom date range"""
        start_date = (date.today() - timedelta(days=14)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')

        response = client_with_data.get(
            f'/api/v1/tracking/stats?start_date={start_date}&end_date={end_date}'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['data']['period']['start_date'] == start_date
        assert data['data']['period']['end_date'] == end_date

    def test_get_adherence_stats_filter_by_medicine(self, client_with_data):
        """Test filtering stats by specific medicine"""
        response = client_with_data.get('/api/v1/tracking/stats?medicine_id=med_test_001')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_adherence_stats_invalid_date_format(self, client):
        """Test error with invalid date format"""
        response = client.get('/api/v1/tracking/stats?start_date=invalid')
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_get_adherence_stats_with_tracking_data(self, client_with_data):
        """Test stats calculation with actual tracking data"""
        # Mark some medicines taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')
        client_with_data.post('/api/v1/medicines/med_test_002/take',
                             data=json.dumps({}),
                             content_type='application/json')

        response = client_with_data.get('/api/v1/tracking/stats')
        data = json.loads(response.data)

        # Should have some tracking records
        assert data['data']['overall']['taken_records'] >= 2


class TestTrackingEdgeCases:
    """Test edge cases in tracking operations"""

    def test_mark_same_medicine_twice_same_day(self, client_with_data):
        """Test marking same medicine taken twice on same day"""
        # Mark first time
        response1 = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                         data=json.dumps({}),
                                         content_type='application/json')
        assert response1.status_code == 201

        # Mark second time (should update, not create duplicate)
        response2 = client_with_data.post('/api/v1/medicines/med_test_001/take',
                                         data=json.dumps({}),
                                         content_type='application/json')
        assert response2.status_code == 201

    def test_tracking_persistence_across_requests(self, client_with_data):
        """Test that tracking data persists across requests"""
        # Mark medicine taken
        client_with_data.post('/api/v1/medicines/med_test_001/take',
                             data=json.dumps({}),
                             content_type='application/json')

        # Verify it appears in tracking history
        response = client_with_data.get('/api/v1/medicines/med_test_001/tracking')
        data = json.loads(response.data)
        assert len(data['data']) > 0

        # Verify it appears in today's stats
        stats_response = client_with_data.get('/api/v1/tracking/today')
        stats_data = json.loads(stats_response.data)
        assert stats_data['data']['medicines_taken'] >= 1

    def test_tracking_with_zero_pills_remaining(self, client_with_data):
        """Test tracking when medicine runs out of pills"""
        # Get a medicine and mark it taken multiple times to deplete stock
        # med_test_003 starts with only 5 pills
        for _ in range(10):  # Mark more times than available pills
            client_with_data.post('/api/v1/medicines/med_test_003/take',
                                 data=json.dumps({}),
                                 content_type='application/json')

        # Should still work, just show 0 pills remaining
        response = client_with_data.get('/api/v1/medicines/med_test_003')
        data = json.loads(response.data)
        assert data['data']['pills_remaining'] == 0
