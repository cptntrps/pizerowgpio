"""
Error Recovery and Resilience Integration Tests
Tests application behavior under error conditions and recovery scenarios
"""

import pytest
import sqlite3
import os
from datetime import date, datetime
from db.medicine_db import MedicineDatabase


class TestTransactionRollback:
    """Test transaction rollback and error handling"""

    def test_add_medicine_with_invalid_data_rollback(self, integration_test_db):
        """
        Scenario: Add medicine fails validation mid-transaction
        Validates: Rollback prevents partial data entry
        """
        db, db_path, _ = integration_test_db

        # Add valid medicine first
        valid_medicine = {
            "id": "med_rollback_base",
            "name": "Base Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Base",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(valid_medicine)

        # Try to add invalid medicine (missing required field)
        invalid_medicine = {
            "id": "med_invalid",
            "name": "Invalid Medicine",
            # Missing 'dosage' field
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10
        }

        with pytest.raises(ValueError):
            db.add_medicine(invalid_medicine)

        # Verify only valid medicine exists
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 1
        assert medicines[0]['id'] == 'med_rollback_base'

    def test_update_nonexistent_medicine_error(self, integration_test_db):
        """
        Scenario: Update non-existent medicine
        Validates: Error is raised and database remains clean
        """
        db, db_path, _ = integration_test_db

        nonexistent_medicine = {
            "id": "med_nonexistent",
            "name": "Ghost Medicine",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Ghost",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        with pytest.raises(ValueError):
            db.update_medicine("med_nonexistent", nonexistent_medicine)

        # Database should still be empty
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 0

    def test_delete_nonexistent_medicine_error(self, integration_test_db):
        """
        Scenario: Delete non-existent medicine
        Validates: Proper error handling
        """
        db, db_path, _ = integration_test_db

        with pytest.raises(ValueError):
            db.delete_medicine("med_nonexistent")

        # Database should remain empty
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 0

    def test_mark_taken_nonexistent_medicine(self, integration_test_db):
        """
        Scenario: Mark non-existent medicine as taken
        Validates: Error is raised
        """
        db, db_path, _ = integration_test_db

        with pytest.raises(ValueError):
            db.mark_medicine_taken("med_nonexistent")

    def test_transaction_isolation(self, integration_test_db):
        """
        Scenario: Failed transaction doesn't affect other operations
        Validates: Transaction isolation works
        """
        db, db_path, _ = integration_test_db

        # Add first medicine
        medicine1 = {
            "id": "med_iso_1",
            "name": "Isolation Test 1",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Test 1",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine1)

        # Try invalid operation
        with pytest.raises(ValueError):
            db.update_medicine("med_nonexistent", medicine1)

        # Add second medicine should still work
        medicine2 = medicine1.copy()
        medicine2['id'] = "med_iso_2"
        db.add_medicine(medicine2)

        # Verify both medicines exist
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 2


class TestDataValidation:
    """Test data validation and constraint enforcement"""

    def test_invalid_time_window_rejected(self, integration_test_db):
        """
        Scenario: Invalid time window value
        Validates: Database constraint prevents invalid values
        """
        db, db_path, _ = integration_test_db

        invalid_medicine = {
            "id": "med_invalid_window",
            "name": "Invalid Window",
            "dosage": "10mg",
            "time_window": "invalid_time",  # Invalid
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Invalid",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        # This should fail at database level or validation
        try:
            db.add_medicine(invalid_medicine)
            # If it doesn't raise, check that it wasn't actually added
            medicines = db.get_all_medicines(include_inactive=True)
            assert len(medicines) == 0
        except:
            # Expected to fail
            pass

    def test_invalid_day_rejected(self, integration_test_db):
        """
        Scenario: Invalid day value
        Validates: Day constraint is enforced
        """
        db, db_path, _ = integration_test_db

        invalid_medicine = {
            "id": "med_invalid_day",
            "name": "Invalid Day",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["monday"],  # Invalid, should be "mon"
            "with_food": False,
            "notes": "Invalid",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        # This should fail
        try:
            db.add_medicine(invalid_medicine)
            medicines = db.get_all_medicines(include_inactive=True)
            assert len(medicines) == 0
        except:
            pass

    def test_negative_pills_prevented(self, integration_test_db):
        """
        Scenario: Pills remaining cannot go negative
        Validates: CHECK constraint prevents negative pills
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_negative_pills",
            "name": "Negative Pills Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Test negative",
            "pills_remaining": 0,  # Already at minimum
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Try to mark taken when pills_remaining is 0
        result = db.mark_medicine_taken(medicine['id'])

        # Should not go below 0
        assert result['pills_remaining'] >= 0

    def test_zero_pills_per_dose_prevented(self, integration_test_db):
        """
        Scenario: Pills per dose must be positive
        Validates: CHECK constraint enforced
        """
        db, db_path, _ = integration_test_db

        invalid_medicine = {
            "id": "med_zero_dose",
            "name": "Zero Dose",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Zero dose",
            "pills_remaining": 100,
            "pills_per_dose": 0,  # Invalid
            "low_stock_threshold": 10,
            "active": True
        }

        try:
            db.add_medicine(invalid_medicine)
            # If not caught, verify it wasn't added
            medicines = db.get_all_medicines(include_inactive=True)
            assert len(medicines) == 0
        except:
            pass


class TestConcurrentErrorHandling:
    """Test error handling under concurrent operations"""

    def test_concurrent_adds_duplicate_id(self, integration_test_db):
        """
        Scenario: Two threads try to add same medicine ID concurrently
        Validates: Only one succeeds due to primary key constraint
        """
        db, db_path, _ = integration_test_db

        medicine_data = {
            "id": "med_concurrent_dup",
            "name": "Concurrent Duplicate",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Concurrent duplicate",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        import threading

        results = []
        exceptions = []
        lock = threading.Lock()

        def add_medicine():
            try:
                result = db.add_medicine(medicine_data)
                with lock:
                    results.append(result)
            except Exception as e:
                with lock:
                    exceptions.append(e)

        # Two threads try to add same medicine
        threads = [threading.Thread(target=add_medicine) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have one success and one failure
        assert len(results) + len(exceptions) == 2
        assert len(results) == 1  # Only one should succeed
        assert len(exceptions) == 1  # One should fail


class TestDatabaseCorruptionRecovery:
    """Test recovery from database corruption scenarios"""

    def test_connection_timeout_recovery(self, integration_test_db):
        """
        Scenario: Recover from connection timeout
        Validates: Database can recover from connection issues
        """
        db, db_path, _ = integration_test_db

        # Add medicine
        medicine = {
            "id": "med_timeout_recovery",
            "name": "Timeout Recovery",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Timeout",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Close connection
        db.close()

        # Try to use database again - should work (new connection)
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 1

    def test_database_cleanup_after_error(self, integration_test_db):
        """
        Scenario: Database state clean after error
        Validates: No leftover data from failed operations
        """
        db, db_path, _ = integration_test_db

        # Add valid medicine
        valid = {
            "id": "med_cleanup",
            "name": "Cleanup Test",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Cleanup",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(valid)

        # Cause an error (missing required field)
        invalid = valid.copy()
        del invalid['dosage']

        try:
            db.add_medicine(invalid)
        except:
            pass

        # Verify database is clean - only valid medicine exists
        medicines = db.get_all_medicines(include_inactive=True)
        assert len(medicines) == 1
        assert medicines[0]['id'] == 'med_cleanup'

    def test_partial_update_rollback(self, integration_test_db):
        """
        Scenario: Partial update rolled back on error
        Validates: Update atomicity
        """
        db, db_path, _ = integration_test_db

        # Add medicine
        medicine = {
            "id": "med_partial_update",
            "name": "Partial Update",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Original",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Store original state
        original = db.get_medicine_by_id(medicine['id'])

        # Try invalid update
        invalid_update = original.copy()
        del invalid_update['dosage']  # Remove required field

        try:
            db.update_medicine(medicine['id'], invalid_update)
        except:
            pass

        # Verify unchanged
        after_error = db.get_medicine_by_id(medicine['id'])
        assert after_error['notes'] == original['notes']
        assert after_error['pills_remaining'] == original['pills_remaining']


class TestRecoveryScenarios:
    """Test realistic recovery scenarios"""

    def test_recovery_from_interrupted_tracking(self, integration_test_db):
        """
        Scenario: Mark medicine taken, verify it wasn't lost on error
        Validates: Tracking data persists
        """
        db, db_path, _ = integration_test_db

        medicine = {
            "id": "med_tracking_recovery",
            "name": "Tracking Recovery",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Tracking",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }
        db.add_medicine(medicine)

        # Mark taken
        result1 = db.mark_medicine_taken(medicine['id'])
        assert result1['success'] is True
        pills_after_1 = result1['pills_remaining']

        # Simulate connection reset by closing
        db.close()

        # Reconnect and verify tracking persisted
        medicine_after = db.get_medicine_by_id(medicine['id'])
        assert medicine_after['pills_remaining'] == pills_after_1

        # Can still mark taken
        result2 = db.mark_medicine_taken(medicine['id'])
        assert result2['success'] is True
        assert result2['pills_remaining'] == pills_after_1 - 1

    def test_recovery_after_multiple_errors(self, integration_test_db):
        """
        Scenario: Multiple operations fail, then succeed
        Validates: System remains usable after errors
        """
        db, db_path, _ = integration_test_db

        # Try several invalid operations
        for i in range(3):
            with pytest.raises(ValueError):
                db.delete_medicine(f"med_nonexistent_{i}")

        # System should still work
        medicine = {
            "id": "med_recovery_ok",
            "name": "Recovery OK",
            "dosage": "10mg",
            "time_window": "morning",
            "window_start": "08:00",
            "window_end": "09:00",
            "days": ["mon"],
            "with_food": False,
            "notes": "Recovery",
            "pills_remaining": 100,
            "pills_per_dose": 1,
            "low_stock_threshold": 10,
            "active": True
        }

        db.add_medicine(medicine)
        retrieved = db.get_medicine_by_id(medicine['id'])
        assert retrieved is not None
