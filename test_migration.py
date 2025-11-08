#!/usr/bin/env python3
"""
Test script to verify migration and new database functionality
Run this before deploying to ensure everything works
"""

from datetime import datetime, date
from shared.validation import validate_medicine
from shared.app_utils import ConfigLoader
from db.medicine_db import MedicineDatabase
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_database_connection():
    """Test 1: Database connection"""
    print("\n" + "=" * 70)
    print("TEST 1: Database Connection")
    print("=" * 70)

    try:
        db = MedicineDatabase(db_path='/home/user/pizerowgpio/medicine.db')
        print("✓ Database connection successful")
        print(f"  Last updated: {db.get_last_updated()}")
        return db
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def test_get_medicines(db):
    """Test 2: Get all medicines"""
    print("\n" + "=" * 70)
    print("TEST 2: Get All Medicines")
    print("=" * 70)

    try:
        medicines = db.get_all_medicines()
        print(f"✓ Found {len(medicines)} medicines")

        for med in medicines:
            pills = med['pills_remaining']
            threshold = med['low_stock_threshold']
            status = "🔴 LOW" if pills <= threshold else "✓"
            print(f"  {status} {med['name']} ({med['dosage']}): {pills} pills")

        return True
    except Exception as e:
        print(f"❌ Failed to get medicines: {e}")
        return False


def test_pending_medicines(db):
    """Test 3: Get pending medicines"""
    print("\n" + "=" * 70)
    print("TEST 3: Get Pending Medicines")
    print("=" * 70)

    try:
        now = datetime.now()
        pending = db.get_pending_medicines(check_date=date.today(), check_time=now)
        print(f"✓ Found {len(pending)} pending medicines at {now.strftime('%H:%M')}")

        for med in pending:
            window = med['time_window']
            print(f"  • {med['name']} ({med['dosage']}) - {window}")

        return True
    except Exception as e:
        print(f"❌ Failed to get pending medicines: {e}")
        return False


def test_adherence_stats(db):
    """Test 4: Get today's stats"""
    print("\n" + "=" * 70)
    print("TEST 4: Today's Adherence Statistics")
    print("=" * 70)

    try:
        taken, total = db.get_today_stats()
        if total > 0:
            percentage = int((taken / total) * 100)
            print(f"✓ Today's adherence: {taken}/{total} medicines taken ({percentage}%)")
        else:
            print("  No medicines scheduled for today")

        return True
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        return False


def test_low_stock(db):
    """Test 5: Low stock check"""
    print("\n" + "=" * 70)
    print("TEST 5: Low Stock Medicines")
    print("=" * 70)

    try:
        low_stock = db.get_low_stock_medicines()
        if low_stock:
            print(f"🔴 {len(low_stock)} medicine(s) at or below low stock threshold:")
            for med in low_stock:
                print(f"  • {med['name']}: {med['pills_remaining']} pills " +
                      f"(threshold: {med['low_stock_threshold']}, " +
                      f"~{med['days_remaining']:.1f} days remaining)")
        else:
            print("✓ No medicines at low stock")

        return True
    except Exception as e:
        print(f"❌ Failed to check low stock: {e}")
        return False


def test_config_loader():
    """Test 6: Config loading"""
    print("\n" + "=" * 70)
    print("TEST 6: Configuration Loading")
    print("=" * 70)

    try:
        config = ConfigLoader()
        med_config = config.get_section('medicine')
        print(f"✓ Config loaded successfully")
        print(f"  Update interval: {med_config.get('update_interval', 'N/A')}s")
        print(f"  Reminder window: {med_config.get('reminder_window', 'N/A')} minutes")

        return True
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False


def test_validation():
    """Test 7: Input validation"""
    print("\n" + "=" * 70)
    print("TEST 7: Input Validation")
    print("=" * 70)

    # Valid medicine
    valid_medicine = {
        'id': 'med_1234567890',
        'name': 'Test Medicine',
        'dosage': '100mg',
        'time_window': 'morning',
        'window_start': '08:00',
        'window_end': '10:00',
        'days': ['mon', 'wed', 'fri'],
        'with_food': True,
        'notes': 'Test notes',
        'pills_remaining': 30,
        'pills_per_dose': 1,
        'low_stock_threshold': 10,
        'active': True
    }

    try:
        validated = validate_medicine(valid_medicine)
        print("✓ Valid medicine passed validation")
    except Exception as e:
        print(f"❌ Valid medicine failed validation: {e}")
        return False

    # Invalid medicine (should fail)
    invalid_medicine = {
        'id': 'invalid_id',  # Wrong format
        'name': 'Test',
        'dosage': '100mg',
        'time_window': 'invalid',  # Invalid window
    }

    try:
        validate_medicine(invalid_medicine)
        print("❌ Invalid medicine passed validation (should have failed)")
        return False
    except Exception as e:
        print(f"✓ Invalid medicine correctly rejected: {e}")
        return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  Pi Zero 2W Medicine Tracker - System Test Suite")
    print("=" * 70)

    results = []

    # Test 1: Database connection
    db = test_database_connection()
    if not db:
        print("\n❌ CRITICAL: Database connection failed. Cannot continue.")
        sys.exit(1)

    results.append(("Database Connection", True))

    # Test 2: Get medicines
    results.append(("Get Medicines", test_get_medicines(db)))

    # Test 3: Pending medicines
    results.append(("Pending Medicines", test_pending_medicines(db)))

    # Test 4: Adherence stats
    results.append(("Adherence Stats", test_adherence_stats(db)))

    # Test 5: Low stock
    results.append(("Low Stock Check", test_low_stock(db)))

    # Test 6: Config loader
    results.append(("Config Loader", test_config_loader()))

    # Test 7: Validation
    results.append(("Input Validation", test_validation()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "=" * 70)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\n✨ System is ready for deployment!")
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        print("\n⚠️  Please fix failing tests before deployment")
        sys.exit(1)


if __name__ == '__main__':
    main()
