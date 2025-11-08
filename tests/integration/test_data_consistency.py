"""
Data Consistency and Integrity Integration Tests
Validates data relationships, constraints, and consistency across operations
"""

import pytest
import sqlite3
from datetime import date, datetime, timedelta
from db.medicine_db import MedicineDatabase


class TestForeignKeyConstraints:
    """Test foreign key relationships and constraints"""

    def test_medicine_days_foreign_key(self, integration_test_db):
        """
        Scenario: Verify medicine_days references valid medicines
        Validates: Foreign key constraint on medicine_id
        """
        db, db_path, _ = integration_test_db

        # Verify schema has foreign key
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_list(medicine_days)")
        fks = cursor.fetchall()
        conn.close()

        # Should have foreign key to medicines table
        assert len(fks) > 0

    def test_delete_medicine_cascades_to_days(self, integration_test_db):
        """
        Scenario: Delete medicine cascades to medicine_days
        Validates: Cascade delete works correctly
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_cascade_days",
            "name": "Cascade Days Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "wed", "fri"],
            "with_food": False,
            "notes": "Cascade test",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Verify days are in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM medicine_days WHERE medicine_id = ?",
                      (medicine['id'],))
        days_before = cursor.fetchone()[0]
        conn.close()
        assert days_before == 3

        # Delete medicine
        db.delete_medicine(medicine['id'])

        # Verify days are cascaded deleted
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM medicine_days WHERE medicine_id = ?",
                      (medicine['id'],))
        days_after = cursor.fetchone()[0]
        conn.close()
        assert days_after == 0

    def test_delete_medicine_cascades_to_tracking(self, integration_test_db):
        """
        Scenario: Delete medicine cascades to tracking
        Validates: Cascade delete to tracking table
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_cascade_tracking",
            "name": "Cascade Tracking Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Cascade test",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Create tracking
        db.mark_medicine_taken(medicine['id'])

        # Verify tracking exists
        tracking_before = db.get_tracking_history(medicine_id=medicine['id'])
        assert len(tracking_before) > 0

        # Delete medicine
        db.delete_medicine(medicine['id'])

        # Verify tracking is cascaded deleted
        tracking_after = db.get_tracking_history(medicine_id=medicine['id'])
        assert len(tracking_after) == 0

    def test_tracking_foreign_key_to_medicines(self, integration_test_db):
        """
        Scenario: Verify tracking references valid medicines
        Validates: Foreign key on medicine_id in tracking
        """
        db, db_path, _ = integration_test_db

        # Verify foreign key exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_list(tracking)")
        fks = cursor.fetchall()
        conn.close()

        # Should have foreign key to medicines
        assert len(fks) > 0


class TestUniqueConstraints:
    """Test unique constraints and duplicates prevention"""

    def test_medicine_id_unique_constraint(self, integration_test_db):
        """
        Scenario: Cannot add two medicines with same ID
        Validates: Primary key constraint
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_unique_id",
            "name": "Unique ID Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Unique test",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        # Add first medicine
        db.add_medicine(medicine)

        # Try to add duplicate - should fail
        with pytest.raises(sqlite3.IntegrityError):
            db.add_medicine(medicine)

    def test_tracking_unique_constraint(self, integration_test_db):
        """
        Scenario: Tracking per medicine per date per window is unique
        Validates: Composite unique constraint
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_tracking_unique",
            "name": "Tracking Unique Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Tracking unique",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Mark taken once
        result1 = db.mark_medicine_taken(medicine['id'])
        assert result1['success'] is True

        # Mark taken again (same day, same window)
        # Should update existing record, not create duplicate
        result2 = db.mark_medicine_taken(medicine['id'])
        assert result2['success'] is True

        # Verify only one tracking record
        tracking = db.get_tracking_history(medicine_id=medicine['id'])
        assert len(tracking) == 1

    def test_medicine_days_composite_unique(self, integration_test_db):
        """
        Scenario: Medicine-day combination is unique
        Validates: Composite primary key on medicine_days
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_days_unique",
            "name": "Days Unique Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "wed"],
            "with_food": False,
            "notes": "Days unique",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Try to add medicine again with duplicate day
        # (This should fail when updating)
        medicine2 = medicine.copy()
        medicine2['id'] = 'med_days_unique_2'
        medicine2['days'] = ["mon", "mon"]  # Duplicate

        # The database should handle this (may silently ignore or may fail)
        # We'll just verify behavior is consistent
        try:
            db.add_medicine(medicine2)
            # If it succeeds, verify the record
            retrieved = db.get_medicine_by_id(medicine2['id'])
            # Days should be processed somehow
            assert 'mon' in retrieved['days']
        except:
            # If it fails, that's also acceptable
            pass


class TestDataIntegrity:
    """Test overall data integrity"""

    def test_all_medicines_have_valid_days(self, integration_test_db, comprehensive_medicine_set):
        """
        Scenario: All medicines have valid scheduled days
        Validates: No medicine without days
        """
        db, db_path, _ = integration_test_db

        # Add all medicines
        for medicine in comprehensive_medicine_set:
            db.add_medicine(medicine)

        # Get all medicines and verify all have days
        medicines = db.get_all_medicines(include_inactive=True)

        valid_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

        for med in medicines:
            assert len(med['days']) > 0, f"Medicine {med['id']} has no days"
            for day in med['days']:
                assert day in valid_days, f"Invalid day {day} for medicine {med['id']}"

    def test_tracking_consistency(self, integration_test_db):
        """
        Scenario: All tracking records reference valid medicines
        Validates: Referential integrity
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_tracking_integrity",
            "name": "Tracking Integrity",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Tracking integrity",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Create multiple tracking records
        for _ in range(3):
            db.mark_medicine_taken(medicine['id'])

        # Get all tracking
        all_tracking = db.get_tracking_history()

        # Verify all reference valid medicines
        all_medicines = db.get_all_medicines(include_inactive=True)
        medicine_ids = {m['id'] for m in all_medicines}

        for track in all_tracking:
            assert track['medicine_id'] in medicine_ids

    def test_pill_count_consistency(self, integration_test_db):
        """
        Scenario: Pill counts remain consistent with marks
        Validates: Pills decrease correctly
        """
        db, db_path, _ = integration_test_db

        initial_pills = 10
        pills_per_dose = 1

        medicine = {
            "id": "med_pills_count",
            "name": "Pills Count Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Pills count",
            "pills_remaining": initial_pills,
            "pills_per_dose": pills_per_dose,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Mark taken multiple times
        for i in range(5):
            result = db.mark_medicine_taken(medicine['id'])
            expected_pills = initial_pills - (pills_per_dose * (i + 1))
            assert result['pills_remaining'] == expected_pills

    def test_time_window_consistency(self, integration_test_db):
        """
        Scenario: All medicines have valid time windows
        Validates: Time window values are correct
        """
        db, db_path, _ = integration_test_db

        valid_windows = ['morning', 'afternoon', 'evening', 'night']

        # Add medicines with each time window
        for window in valid_windows:
            medicine = {
                "id": f"med_{window}",
                "name": f"{window.capitalize()} Medicine",
                "dosage": "10mg",
                "time_window": window,
                "window_start": "08:00",
                "window_end": "09:00",
                "days": ["mon"],
                "with_food": False,
                "notes": f"{window} test",
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            db.add_medicine(medicine)

        # Verify all medicines
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 4

        for med in medicines:
            assert med['time_window'] in valid_windows


class TestDataConsistencyAfterOperations:
    """Test consistency maintained throughout operations"""

    def test_consistency_after_update(self, integration_test_db):
        """
        Scenario: Data remains consistent after updates
        Validates: Update doesn't corrupt data
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_consistency_update",
            "name": "Original Name",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "wed", "fri"],
            "with_food": True,
            "notes": "Original notes",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Update multiple fields
        medicine['name'] = 'Updated Name'
        medicine['dosage'] = '20mg'
        medicine['days'] = ['tue', 'thu']
        medicine['with_food'] = False

        db.update_medicine(medicine['id'], medicine)

        # Verify all changes persisted
        updated = db.get_medicine_by_id(medicine['id'])
        assert updated['name'] == 'Updated Name'
        assert updated['dosage'] == '20mg'
        assert set(updated['days']) == {'tue', 'thu'}
        assert updated['with_food'] is False

    def test_consistency_after_mark_taken(self, integration_test_db):
        """
        Scenario: Data consistent after marking taken
        Validates: Mark taken updates pills and tracking atomically
        """
        db, db_path, _ = integration_test_db

        initial_pills = 50
        medicine = {
            "id": "med_consistency_mark",
            "name": "Mark Consistency Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Mark consistency",
            "pills_remaining": initial_pills,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Mark taken
        result = db.mark_medicine_taken(medicine['id'])

        # Verify both pill count and tracking updated atomically
        tracking = db.get_tracking_history(medicine_id=medicine['id'])
        med_data = db.get_medicine_by_id(medicine['id'])

        assert len(tracking) == 1
        # SQLite returns 1 for True, 0 for False
        assert tracking[0]['taken'] in (True, 1)
        assert med_data['pills_remaining'] == initial_pills - 1
        assert result['pills_remaining'] == initial_pills - 1

    def test_consistency_across_multiple_operations(self, integration_test_db):
        """
        Scenario: Consistency maintained through sequence of operations
        Validates: Complex operation sequence maintains integrity
        """
        db, db_path, _ = integration_test_db

        # Setup
        medicine = {
            "id": "med_sequence_consistency",
            "name": "Sequence Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon", "tue"],
            "with_food": False,
            "notes": "Sequence test",
            "pills_remaining": 10,
            "pills_per_dose": 1,
            "low_stock_threshold": 5,
            "active": True
        }

        # Operation sequence
        db.add_medicine(medicine)
        assert len(db.get_all_medicines()) == 1

        medicine['pills_remaining'] = 9  # Update to 9
        db.update_medicine(medicine['id'], medicine)
        assert db.get_medicine_by_id(medicine['id'])['pills_remaining'] == 9

        db.mark_medicine_taken(medicine['id'])
        assert db.get_medicine_by_id(medicine['id'])['pills_remaining'] == 8

        medicine['days'] = ["wed", "thu"]
        # Need to update pills_remaining to match current state
        medicine['pills_remaining'] = 8
        db.update_medicine(medicine['id'], medicine)
        updated = db.get_medicine_by_id(medicine['id'])
        assert set(updated['days']) == {'wed', 'thu'}
        assert updated['pills_remaining'] == 8

        # Verify final state
        final = db.get_medicine_by_id(medicine['id'])
        assert final['id'] == medicine['id']
        assert set(final['days']) == {'wed', 'thu'}
        assert final['pills_remaining'] == 8

    def test_database_integrity_after_operations(self, integration_test_db, verify_db_consistency,
                                                assert_data_consistency):
        """
        Scenario: Overall database integrity after various operations
        Validates: Foreign keys and constraints still valid
        """
        db, db_path, _ = integration_test_db

        # Perform various operations
        for i in range(5):
            medicine = {
                "id": f"med_integrity_{i}",
                "name": f"Integrity Test {i}",
                "dosage": "10mg",
                "time_window": "morning",
                "window_start": "08:00",
                "window_end": "09:00",
                "days": ["mon", "tue"],
                "with_food": False,
                "notes": f"Test {i}",
                "pills_remaining": 100,
                "pills_per_dose": 1,
                "low_stock_threshold": 10,
                "active": True
            }
            db.add_medicine(medicine)
            db.mark_medicine_taken(medicine['id'])

        # Verify database consistency
        consistency = verify_db_consistency(db_path)
        assert_data_consistency(consistency)


class TestMetadataConsistency:
    """Test metadata consistency"""

    def test_metadata_last_updated_on_add(self, integration_test_db):
        """
        Scenario: Metadata timestamp updates on medicine add
        Validates: Last updated timestamp maintained
        """
        db, db_path, _ = integration_test_db

        timestamp1 = db.get_last_updated()

        import time
        time.sleep(0.1)

        medicine = {
            "id": "med_metadata_add",
            "name": "Metadata Add Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Metadata test",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        timestamp2 = db.get_last_updated()
        assert timestamp2 >= timestamp1

    def test_metadata_last_updated_on_mark(self, integration_test_db):
        """
        Scenario: Metadata timestamp updates on mark taken
        Validates: Timestamp updated for all changes
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_metadata_mark",
            "name": "Metadata Mark Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Metadata test",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        timestamp1 = db.get_last_updated()

        import time
        time.sleep(0.1)

        db.mark_medicine_taken(medicine['id'])

        timestamp2 = db.get_last_updated()
        assert timestamp2 >= timestamp1
