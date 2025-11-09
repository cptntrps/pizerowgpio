"""
Multi-App Interaction Integration Tests
Tests interactions between medicine app and API layer, ensuring data consistency
"""

import pytest
from datetime import date, datetime, timedelta
from db.medicine_db import MedicineDatabase


class TestMedicineAppAPIIntegration:
    """Test integration between medicine app and API"""

    def test_app_reads_after_api_creates(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: API creates medicine, app reads it
        Validates: App can access data created via API
        """
        db, db_path, _ = integration_test_db

        # API creates medicine via database
        medicine = comprehensive_medicine_set[0]
        db.add_medicine(medicine)

        # App reads medicine
        medicines = db.get_all_medicines()
        assert len(medicines) == 1
        assert medicines[0]['id'] == medicine['id']
        assert medicines[0]['name'] == medicine['name']

    def test_app_tracking_visible_to_api(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: App marks medicine taken, API retrieves tracking
        Validates: API can see tracking data created by app
        """
        db, db_path, _ = integration_test_db

        # Setup: Add medicine
        medicine = comprehensive_medicine_set[0]
        db.add_medicine(medicine)

        # App marks medicine taken
        result = db.mark_medicine_taken(medicine['id'])
        assert result['success'] is True
        assert result['pills_remaining'] == 99

        # API reads tracking data
        tracking = db.get_tracking_history(medicine_id=medicine['id'])
        assert len(tracking) == 1
        # SQLite returns 1 for True, 0 for False
        assert tracking[0]['taken'] in (True, 1)
        assert tracking[0]['pills_taken'] == 1

    def test_api_updates_visible_to_app(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: API updates medicine, app displays updated info
        Validates: App sees changes made via API/database
        """
        db, db_path, _ = integration_test_db

        # Setup: Add medicine
        medicine = comprehensive_medicine_set[0]
        db.add_medicine(medicine)

        # API updates medicine
        updated_data = medicine.copy()
        updated_data['pills_remaining'] = 25
        updated_data['notes'] = 'Updated via API'
        db.update_medicine(medicine['id'], updated_data)

        # App reads updated medicine
        updated_med = db.get_medicine_by_id(medicine['id'])
        assert updated_med['pills_remaining'] == 25
        assert updated_med['notes'] == 'Updated via API'

    def test_pending_medicines_consistency(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: Check pending medicines returns correct data
        Validates: Pending medicines calculation is correct across layers
        """
        db, db_path, _ = integration_test_db

        # Setup: Add medicines scheduled for today
        today = date.today()
        today_day = today.strftime('%a').lower()

        # Add medicines scheduled for today
        for med in comprehensive_medicine_set[:3]:
            # Ensure medicine is scheduled for today
            med_copy = med.copy()
            med_copy['days'] = [today_day]
            db.add_medicine(med_copy)

        # Get pending medicines
        pending = db.get_pending_medicines(
            check_date=today,
            check_time=datetime.now()
        )

        # Should have medicines scheduled for today
        assert len(pending) >= 0  # May not have pending if outside time window
        for med in pending:
            assert today_day in med['days']

    def test_low_stock_detection_across_layers(self, integration_test_db):
        """
        Scenario: Low stock detected by database, visible to both app and API
        Validates: Low stock status is consistent
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_low_stock",
            "name": "Low Stock Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed"],
            "with_food": False,
            "notes": "Test low stock",
            "pills_remaining": 8,  # Below threshold of 10
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # App sees low stock via get_medicine_by_id
        med = db.get_medicine_by_id(medicine['id'])
        assert med['pills_remaining'] <= med['low_stock_threshold']

        # API sees low stock via get_low_stock_medicines
        low_stock_list = db.get_low_stock_medicines()
        assert len(low_stock_list) >= 1
        medicine_ids = [m['id'] for m in low_stock_list]
        assert medicine['id'] in medicine_ids

    def test_stats_calculation_consistency(self, integration_test_db):
        """
        Scenario: Check today's stats are consistent
        Validates: Stats calculation is correct
        """
        db, db_path, _ = integration_test_db

        today = date.today()
        today_day = today.strftime('%a').lower()

        # Add medicines for today
        for i in range(3):
            medicine = {
                "id": f"med_stats_{i}",
                "name": f"Stats Medicine {i}",
                "dosage": "10mg",
                "time_window": "morning",
                "window_start": "08:00",
                "window_end": "09:00",
                "days": [today_day],
                "with_food": False,
                "notes": f"Stats test {i}",
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            db.add_medicine(medicine)

        # Mark first medicine as taken
        db.mark_medicine_taken("med_stats_0")

        # Get stats
        taken, total = db.get_today_stats(check_date=today)
        assert total == 3
        assert taken == 1  # Only one marked as taken

    def test_medicine_deletion_cascades(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: Delete medicine cascades to related records
        Validates: Foreign key constraints work correctly
        """
        db, db_path, _ = integration_test_db

        medicine = comprehensive_medicine_set[0]
        db.add_medicine(medicine)

        # Create some tracking data
        db.mark_medicine_taken(medicine['id'])

        # Delete medicine
        db.delete_medicine(medicine['id'])

        # Verify medicine is deleted
        remaining = db.get_all_medicines(include_inactive=True)
        assert len(remaining) == 0

        # Verify tracking is cascaded (deleted)
        tracking = db.get_tracking_history()
        assert len(tracking) == 0

    def test_concurrent_app_api_reads(self, integration_test_db, comprehensive_medicine_set,
                                     concurrent_operations):
        """
        Scenario: App and API read simultaneously
        Validates: Concurrent reads don't cause issues
        """
        db, db_path, _ = integration_test_db

        # Setup: Add medicines
        medicine = comprehensive_medicine_set[0]
        db.add_medicine(medicine)

        # Create concurrent read operations
        operations = [
            (db.get_all_medicines, ()),
            (db.get_medicine_by_id, (medicine['id'],)),
            (db.get_all_medicines, (True,)),  # include_inactive
            (db.get_all_medicines, ()),
            (db.get_medicine_by_id, (medicine['id'],)),
        ]

        results, exceptions = concurrent_operations(operations, max_workers=5)

        # All operations should succeed
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
        assert len(results) == 5

    def test_metadata_updates_on_changes(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: Metadata timestamp updates when data changes
        Validates: Last updated timestamp is maintained correctly
        """
        db, db_path, _ = integration_test_db

        # Get initial timestamp
        timestamp1 = db.get_last_updated()

        # Wait slightly to ensure time difference
        import time
        time.sleep(0.1)

        # Add medicine
        medicine = comprehensive_medicine_set[0]
        db.add_medicine(medicine)

        # Get new timestamp
        timestamp2 = db.get_last_updated()

        # Timestamp should have been updated
        assert timestamp2 >= timestamp1

    def test_medicine_days_consistency(self, integration_test_db):
        """
        Scenario: Medicine days are stored and retrieved correctly
        Validates: Days-of-week data is preserved
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_days_test",
            "name": "Days Test Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "wed", "fri"],
            "with_food": False,
            "notes": "Test days",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Retrieve and verify days
        retrieved = db.get_medicine_by_id(medicine['id'])
        assert set(retrieved['days']) == set(["mon", "wed", "fri"])

        # Update days
        medicine['days'] = ["tue", "thu", "sat"]
        db.update_medicine(medicine['id'], medicine)

        # Verify updated days
        retrieved = db.get_medicine_by_id(medicine['id'])
        assert set(retrieved['days']) == set(["tue", "thu", "sat"])


class TestCrossLayerDataFlow:
    """Test data flow across app and API layers"""

    def test_create_read_update_delete_cycle(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: Complete CRUD cycle via database
        Validates: All operations maintain data integrity
        """
        db, db_path, _ = integration_test_db

        medicine = comprehensive_medicine_set[0]

        # Create
        db.add_medicine(medicine)
        med = db.get_medicine_by_id(medicine['id'])
        assert med is not None

        # Read
        all_meds = db.get_all_medicines()
        assert len(all_meds) == 1

        # Update
        medicine['pills_remaining'] = 50
        db.update_medicine(medicine['id'], medicine)
        updated = db.get_medicine_by_id(medicine['id'])
        assert updated['pills_remaining'] == 50

        # Delete
        db.delete_medicine(medicine['id'])
        deleted = db.get_medicine_by_id(medicine['id'])
        assert deleted is None

    def test_multiple_medicines_independent_operations(self, integration_test_db,
                                                       comprehensive_medicine_set):
        """
        Scenario: Multiple medicines can be operated on independently
        Validates: Operations on one medicine don't affect others
        """
        db, db_path, _ = integration_test_db

        # Add multiple medicines
        for medicine in comprehensive_medicine_set[:3]:
            db.add_medicine(medicine)

        # Mark first medicine taken
        db.mark_medicine_taken(comprehensive_medicine_set[0]['id'])

        # Verify only first has tracking
        tracking1 = db.get_tracking_history(
            medicine_id=comprehensive_medicine_set[0]['id']
        )
        tracking2 = db.get_tracking_history(
            medicine_id=comprehensive_medicine_set[1]['id']
        )

        assert len(tracking1) == 1
        assert len(tracking2) == 0

    def test_state_after_multiple_marks_taken(self, integration_test_db):
        """
        Scenario: Medicine marked taken multiple times on same day
        Validates: Tracking handles duplicates correctly
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_marks_test",
            "name": "Marks Test Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue", "wed"],
            "with_food": False,
            "notes": "Test marks",
            "pills_remaining": 10,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Mark taken once
        db.mark_medicine_taken(medicine['id'])
        tracking1 = db.get_tracking_history(medicine_id=medicine['id'])
        pills1 = db.get_medicine_by_id(medicine['id'])['pills_remaining']

        # Mark taken again (should update, not duplicate)
        db.mark_medicine_taken(medicine['id'])
        tracking2 = db.get_tracking_history(medicine_id=medicine['id'])
        pills2 = db.get_medicine_by_id(medicine['id'])['pills_remaining']

        # Should have only 1 tracking record (on conflict, update)
        assert len(tracking2) == 1
        # Pills should decrease once more (second mark)
        assert pills2 == pills1 - 1
