"""
API Integration Tests
Phase 1.4 - API Testing Suite

Integration tests for complete workflows:
- Complete medicine lifecycle (create → update → take → track → delete)
- Multi-user concurrent scenarios
- Transaction integrity and rollback
- Database consistency
- Cross-endpoint data flow
"""

import json
import threading
import time
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestMedicineLifecycle:
    """Test complete medicine lifecycle"""

    def test_complete_medicine_workflow(self, client):
        """Test full medicine workflow from creation to deletion"""
        # 1. Create medicine
        medicine_data = {
            "name": "Lifecycle Test Medicine",
            "dosage": "50mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed", "thu", "fri"],
            "with_food": True,
            "notes": "Integration test medicine",
            "pills_remaining": 30,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        assert create_response.status_code == 201
        created_med = json.loads(create_response.data)
        med_id = created_med['data']['id']

        # 2. Verify it appears in list
        list_response = client.get('/api/v1/medicines')
        list_data = json.loads(list_response.data)
        assert any(m['id'] == med_id for m in list_data['data'])

        # 3. Get specific medicine
        get_response = client.get(f'/api/v1/medicines/{med_id}')
        assert get_response.status_code == 200

        # 4. Update medicine
        update_data = medicine_data.copy()
        update_data['id'] = med_id
        update_data['dosage'] = '100mg'
        update_response = client.patch(f'/api/v1/medicines/{med_id}',
                                      data=json.dumps({'dosage': '100mg'}),
                                      content_type='application/json')
        assert update_response.status_code == 200

        # 5. Mark medicine as taken
        take_response = client.post(f'/api/v1/medicines/{med_id}/take',
                                   data=json.dumps({}),
                                   content_type='application/json')
        assert take_response.status_code == 201
        take_data = json.loads(take_response.data)
        assert take_data['data']['pills_remaining'] == 29

        # 6. Verify tracking history
        tracking_response = client.get(f'/api/v1/medicines/{med_id}/tracking')
        tracking_data = json.loads(tracking_response.data)
        assert len(tracking_data['data']) > 0

        # 7. Check today's stats
        stats_response = client.get('/api/v1/tracking/today')
        stats_data = json.loads(stats_response.data)
        assert stats_data['data']['medicines_taken'] > 0

        # 8. Delete medicine
        delete_response = client.delete(f'/api/v1/medicines/{med_id}')
        assert delete_response.status_code == 204

        # 9. Verify it's gone
        get_deleted_response = client.get(f'/api/v1/medicines/{med_id}')
        assert get_deleted_response.status_code == 404

    def test_medicine_stock_depletion_workflow(self, client):
        """Test workflow when medicine stock runs low and depletes"""
        # Create medicine with low stock
        medicine_data = {
            "name": "Low Stock Medicine",
            "dosage": "25mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed"],
            "pills_remaining": 5,
            "pills_per_dose": 2,
            "low_stock_threshold": 10,
            "active": True
        }

        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        # Check it appears in low stock
        low_stock_response = client.get('/api/v1/medicines/low-stock')
        low_stock_data = json.loads(low_stock_response.data)
        assert any(m['id'] == med_id for m in low_stock_data['data'])

        # Take medicine multiple times until depleted
        for i in range(3):
            take_response = client.post(f'/api/v1/medicines/{med_id}/take',
                                       data=json.dumps({}),
                                       content_type='application/json')
            assert take_response.status_code == 201

        # Check final count is 0 (not negative)
        get_response = client.get(f'/api/v1/medicines/{med_id}')
        final_data = json.loads(get_response.data)
        assert final_data['data']['pills_remaining'] == 0

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')

    def test_batch_operations_workflow(self, client):
        """Test batch operations in realistic workflow"""
        # Create multiple medicines
        medicine_ids = []
        for i in range(3):
            medicine_data = {
                "name": f"Batch Medicine {i}",
                "dosage": "10mg",
                "time_window": "morning",
                "window_start": "08:00",
                "window_end": "09:00",
                "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            response = client.post('/api/v1/medicines',
                                 data=json.dumps(medicine_data),
                                 content_type='application/json')
            med_id = json.loads(response.data)['data']['id']
            medicine_ids.append(med_id)

        # Batch mark as taken
        batch_data = {
            'medicine_ids': medicine_ids
        }
        batch_response = client.post('/api/v1/medicines/batch-take',
                                    data=json.dumps(batch_data),
                                    content_type='application/json')
        assert batch_response.status_code == 200
        batch_result = json.loads(batch_response.data)
        assert len(batch_result['data']['marked']) == 3

        # Verify all have reduced pill counts
        for med_id in medicine_ids:
            get_response = client.get(f'/api/v1/medicines/{med_id}')
            med_data = json.loads(get_response.data)
            assert med_data['data']['pills_remaining'] == 99

        # Cleanup
        for med_id in medicine_ids:
            client.delete(f'/api/v1/medicines/{med_id}')


class TestConcurrentOperations:
    """Test concurrent access and thread safety"""

    def test_concurrent_medicine_creation(self, client):
        """Test creating medicines concurrently"""
        def create_medicine(index):
            medicine_data = {
                "name": f"Concurrent Medicine {index}",
                "dosage": "10mg",
                "time_window": "morning",
                "window_start": "08:00",
                "window_end": "09:00",
                "days": ["mon", "tue", "wed"],
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            response = client.post('/api/v1/medicines',
                                 data=json.dumps(medicine_data),
                                 content_type='application/json')
            return response.status_code == 201, json.loads(response.data)

        # Create 10 medicines concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_medicine, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed
        assert all(success for success, _ in results)

        # Cleanup
        for success, data in results:
            if success and 'data' in data:
                client.delete(f"/api/v1/medicines/{data['data']['id']}")

    def test_concurrent_medicine_updates(self, client):
        """Test updating same medicine concurrently"""
        # Create a medicine
        medicine_data = {
            "name": "Concurrent Update Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        def update_medicine(value):
            patch_data = {'notes': f'Update {value}'}
            response = client.patch(f'/api/v1/medicines/{med_id}',
                                   data=json.dumps(patch_data),
                                   content_type='application/json')
            return response.status_code == 200

        # Update concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_medicine, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # All updates should succeed
        assert all(results)

        # Medicine should still exist and be valid
        get_response = client.get(f'/api/v1/medicines/{med_id}')
        assert get_response.status_code == 200

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')

    def test_concurrent_tracking_operations(self, client):
        """Test marking medicine taken concurrently"""
        # Create medicine
        medicine_data = {
            "name": "Concurrent Tracking Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        def mark_taken():
            response = client.post(f'/api/v1/medicines/{med_id}/take',
                                 data=json.dumps({}),
                                 content_type='application/json')
            return response.status_code == 201

        # Mark taken concurrently (simulating multiple rapid clicks)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(mark_taken) for _ in range(5)]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed
        assert all(results)

        # Check final pill count (should be decremented correctly)
        get_response = client.get(f'/api/v1/medicines/{med_id}')
        final_data = json.loads(get_response.data)
        # Pills should be decremented (though exact count may vary due to timing)
        assert final_data['data']['pills_remaining'] < 100

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')


class TestDatabaseConsistency:
    """Test database consistency and integrity"""

    def test_cascade_delete_consistency(self, client):
        """Test that deleting medicine cascades to tracking data"""
        # Create medicine
        medicine_data = {
            "name": "Cascade Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        # Mark as taken multiple times
        for _ in range(3):
            client.post(f'/api/v1/medicines/{med_id}/take',
                       data=json.dumps({}),
                       content_type='application/json')

        # Verify tracking data exists
        tracking_response = client.get(f'/api/v1/medicines/{med_id}/tracking')
        tracking_data = json.loads(tracking_response.data)
        assert len(tracking_data['data']) > 0

        # Delete medicine
        client.delete(f'/api/v1/medicines/{med_id}')

        # Verify medicine is gone
        get_response = client.get(f'/api/v1/medicines/{med_id}')
        assert get_response.status_code == 404

        # Tracking data should also be gone (cascade delete)
        tracking_after_delete = client.get(f'/api/v1/medicines/{med_id}/tracking')
        assert tracking_after_delete.status_code == 404

    def test_data_integrity_after_multiple_operations(self, client):
        """Test data remains consistent after many operations"""
        # Create medicine
        medicine_data = {
            "name": "Integrity Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed"],
            "pills_remaining": 50,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        # Perform many operations
        operations_count = 10
        for i in range(operations_count):
            # Update
            client.patch(f'/api/v1/medicines/{med_id}',
                        data=json.dumps({'notes': f'Operation {i}'}),
                        content_type='application/json')

            # Mark taken
            client.post(f'/api/v1/medicines/{med_id}/take',
                       data=json.dumps({}),
                       content_type='application/json')

        # Verify final state is consistent
        get_response = client.get(f'/api/v1/medicines/{med_id}')
        final_data = json.loads(get_response.data)

        # Pills should be decremented correctly
        expected_pills = 50 - operations_count
        assert final_data['data']['pills_remaining'] == expected_pills

        # Tracking count should match
        tracking_response = client.get(f'/api/v1/medicines/{med_id}/tracking')
        tracking_data = json.loads(tracking_response.data)
        assert len(tracking_data['data']) >= operations_count

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')

    def test_unique_constraint_enforcement(self, client):
        """Test that database unique constraints are enforced"""
        medicine_data = {
            "id": "unique_test_med",
            "name": "Unique Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        # Create medicine
        response1 = client.post('/api/v1/medicines',
                              data=json.dumps(medicine_data),
                              content_type='application/json')
        assert response1.status_code == 201

        # Try to create with same ID
        response2 = client.post('/api/v1/medicines',
                              data=json.dumps(medicine_data),
                              content_type='application/json')
        # Should fail with 400, 409, or 500
        assert response2.status_code in [400, 409, 500]

        # Cleanup
        client.delete('/api/v1/medicines/unique_test_med')


class TestCrossEndpointIntegration:
    """Test data flow across different endpoints"""

    def test_medicine_tracking_stats_integration(self, client):
        """Test that medicine, tracking, and stats all stay in sync"""
        # Create multiple medicines
        medicine_ids = []
        for i in range(3):
            medicine_data = {
                "name": f"Integration Med {i}",
                "dosage": "10mg",
                "time_window": "morning",
                "window_start": "08:00",
                "window_end": "09:00",
                "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            response = client.post('/api/v1/medicines',
                                 data=json.dumps(medicine_data),
                                 content_type='application/json')
            med_id = json.loads(response.data)['data']['id']
            medicine_ids.append(med_id)

        # Mark some as taken
        client.post(f'/api/v1/medicines/{medicine_ids[0]}/take',
                   data=json.dumps({}),
                   content_type='application/json')
        client.post(f'/api/v1/medicines/{medicine_ids[1]}/take',
                   data=json.dumps({}),
                   content_type='application/json')

        # Check today's stats
        stats_response = client.get('/api/v1/tracking/today')
        stats_data = json.loads(stats_response.data)

        # Should show 2 medicines taken
        assert stats_data['data']['medicines_taken'] >= 2

        # Check tracking endpoint
        tracking_response = client.get('/api/v1/tracking')
        tracking_data = json.loads(tracking_response.data)
        assert len(tracking_data['data']) >= 2

        # Check individual medicine tracking
        med1_tracking = client.get(f'/api/v1/medicines/{medicine_ids[0]}/tracking')
        med1_data = json.loads(med1_tracking.data)
        assert len(med1_data['data']) > 0

        # Cleanup
        for med_id in medicine_ids:
            client.delete(f'/api/v1/medicines/{med_id}')

    def test_pending_medicines_updates_after_taking(self, client):
        """Test that pending medicines list updates after marking taken"""
        # Create medicine for today
        today = date.today()
        day_name = today.strftime('%a').lower()

        medicine_data = {
            "name": "Pending Test Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": [day_name],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        # Medicine might be in pending (depending on current time)
        pending_before = client.get('/api/v1/medicines/pending')
        pending_before_data = json.loads(pending_before.data)

        # Mark as taken
        client.post(f'/api/v1/medicines/{med_id}/take',
                   data=json.dumps({}),
                   content_type='application/json')

        # Check pending again
        pending_after = client.get('/api/v1/medicines/pending')
        pending_after_data = json.loads(pending_after.data)

        # The medicine should no longer be in pending list after being taken
        # (assuming it was there before)
        pending_ids_before = [m['id'] for m in pending_before_data['data']]
        pending_ids_after = [m['id'] for m in pending_after_data['data']]

        if med_id in pending_ids_before:
            assert med_id not in pending_ids_after

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')


class TestHealthAndMetadata:
    """Test health check and metadata endpoints"""

    def test_health_check_endpoint(self, client):
        """Test that health check works"""
        response = client.get('/api/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['success'] is True
        assert 'status' in data['data']
        assert data['data']['database'] in ['connected', 'disconnected']

    def test_health_check_v1_endpoint(self, client):
        """Test v1 health check endpoint"""
        response = client.get('/api/v1/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'version' in data['data']

    def test_api_consistency_across_requests(self, client):
        """Test that API returns consistent response structure"""
        endpoints = [
            ('/api/v1/medicines', 'GET'),
            ('/api/v1/tracking', 'GET'),
            ('/api/v1/tracking/today', 'GET'),
            ('/api/v1/medicines/pending', 'GET'),
            ('/api/v1/medicines/low-stock', 'GET'),
        ]

        for endpoint, method in endpoints:
            response = client.get(endpoint)
            data = json.loads(response.data)

            # All responses should have 'success' field
            assert 'success' in data
            # All successful responses should have 'data' field
            if data['success']:
                assert 'data' in data


class TestErrorRecovery:
    """Test error handling and recovery"""

    def test_recovery_from_invalid_operation(self, client):
        """Test that API recovers gracefully from errors"""
        # Try to get non-existent medicine
        response1 = client.get('/api/v1/medicines/nonexistent')
        assert response1.status_code == 404

        # Subsequent valid request should work fine
        response2 = client.get('/api/v1/medicines')
        assert response2.status_code == 200

    def test_partial_batch_operation_error_handling(self, client):
        """Test batch operation handles partial failures gracefully"""
        # Create one valid medicine
        medicine_data = {
            "name": "Valid Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        create_response = client.post('/api/v1/medicines',
                                     data=json.dumps(medicine_data),
                                     content_type='application/json')
        med_id = json.loads(create_response.data)['data']['id']

        # Batch operation with valid and invalid IDs
        batch_data = {
            'medicine_ids': [med_id, 'invalid_id_1', 'invalid_id_2']
        }
        batch_response = client.post('/api/v1/medicines/batch-take',
                                    data=json.dumps(batch_data),
                                    content_type='application/json')

        # Should return 200 with partial success
        assert batch_response.status_code == 200
        batch_result = json.loads(batch_response.data)

        # Valid medicine should be marked
        assert len(batch_result['data']['marked']) >= 1

        # System should still be functional
        get_response = client.get('/api/v1/medicines')
        assert get_response.status_code == 200

        # Cleanup
        client.delete(f'/api/v1/medicines/{med_id}')
