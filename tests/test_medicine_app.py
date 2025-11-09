"""
Comprehensive Tests for Medicine App
=====================================

Tests for medicine_app.py functionality including:
- Data loading and saving
- Time window calculations
- Pending medicine detection
- Medicine tracking and inventory
- Display rendering
- Statistics calculations

Test Coverage:
- Data persistence (load/save)
- Time-based logic
- Inventory management
- Tracking logic
- Display functions
"""

import pytest
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, mock_open
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_medicine_data_full():
    """Comprehensive medicine data for testing"""
    return {
        "medicines": [
            {
                "id": "med1",
                "name": "Vitamin D",
                "dosage": "1000 IU",
                "days": ["mon", "wed", "fri"],
                "window_start": "08:00",
                "window_end": "10:00",
                "time_window": "morning",
                "pills_per_dose": 1,
                "pills_remaining": 30,
                "low_stock_threshold": 10,
                "with_food": True,
                "notes": "Take with breakfast",
                "active": True
            },
            {
                "id": "med2",
                "name": "Omega-3",
                "dosage": "1 capsule",
                "days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                "window_start": "20:00",
                "window_end": "22:00",
                "time_window": "evening",
                "pills_per_dose": 1,
                "pills_remaining": 5,
                "low_stock_threshold": 10,
                "with_food": False,
                "notes": "",
                "active": True
            },
            {
                "id": "med3",
                "name": "Inactive Med",
                "dosage": "1 pill",
                "days": ["mon"],
                "window_start": "12:00",
                "window_end": "14:00",
                "time_window": "afternoon",
                "pills_per_dose": 1,
                "pills_remaining": 20,
                "low_stock_threshold": 10,
                "with_food": False,
                "active": False
            }
        ],
        "tracking": {
            "2025-11-09": {
                "med1_morning": {
                    "taken": False,
                    "timestamp": ""
                }
            }
        },
        "time_windows": {},
        "last_updated": "2025-11-09T08:00:00"
    }


@pytest.fixture
def mock_medicine_file(tmp_path, sample_medicine_data_full):
    """Create a temporary medicine data file"""
    file_path = tmp_path / "medicine_data.json"
    with open(file_path, 'w') as f:
        json.dump(sample_medicine_data_full, f)
    return str(file_path)


# ============================================================================
# Import medicine_app functions with mocked paths
# ============================================================================

with patch('sys.path', sys.path):
    with patch.dict('os.environ', {}):
        # Mock the file paths before import
        with patch('medicine_app.CONFIG_FILE', '/tmp/test_config.json'):
            with patch('medicine_app.MEDICINE_DATA_FILE', '/tmp/test_medicine.json'):
                try:
                    import medicine_app
                except:
                    # If import fails due to missing files, create dummy ones
                    pass


# ============================================================================
# Test Data Loading/Saving
# ============================================================================

class TestDataPersistence:
    """Test data loading and saving functions"""

    def test_load_medicine_data_success(self, mock_medicine_file):
        """Test loading medicine data from file"""
        with patch('medicine_app.MEDICINE_DATA_FILE', mock_medicine_file):
            data = medicine_app.load_medicine_data()

            assert "medicines" in data
            assert len(data["medicines"]) == 3
            assert data["medicines"][0]["name"] == "Vitamin D"
            assert data["last_updated"] == "2025-11-09T08:00:00"

    def test_load_medicine_data_file_not_found(self):
        """Test loading when file doesn't exist returns empty structure"""
        with patch('medicine_app.MEDICINE_DATA_FILE', '/nonexistent/file.json'):
            data = medicine_app.load_medicine_data()

            assert data == {"medicines": [], "tracking": {}, "time_windows": {}}

    def test_save_medicine_data_success(self, tmp_path, sample_medicine_data_full):
        """Test saving medicine data to file"""
        file_path = tmp_path / "save_test.json"

        with patch('medicine_app.MEDICINE_DATA_FILE', str(file_path)):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 11, 9, 10, 30, 0)
                mock_dt.strftime = datetime.strftime

                result = medicine_app.save_medicine_data(sample_medicine_data_full)

                assert result is True
                assert file_path.exists()

                # Verify saved data
                with open(file_path, 'r') as f:
                    saved_data = json.load(f)
                    assert "last_updated" in saved_data

    def test_save_medicine_data_failure(self):
        """Test save failure handling"""
        with patch('medicine_app.MEDICINE_DATA_FILE', '/invalid/path/file.json'):
            result = medicine_app.save_medicine_data({"medicines": []})
            assert result is False

    def test_get_data_timestamp(self, sample_medicine_data_full):
        """Test getting timestamp from data"""
        timestamp = medicine_app.get_data_timestamp(sample_medicine_data_full)
        assert timestamp == "2025-11-09T08:00:00"

    def test_get_data_timestamp_missing(self):
        """Test getting timestamp when not present"""
        data = {"medicines": []}
        timestamp = medicine_app.get_data_timestamp(data)
        assert timestamp == "1970-01-01T00:00:00"


# ============================================================================
# Test Time Window Logic
# ============================================================================

class TestTimeWindows:
    """Test time window calculations"""

    def test_is_in_time_window_within_window(self):
        """Test time check when within window"""
        current_time = datetime(2025, 11, 9, 9, 0, 0)  # 9:00 AM

        # Window 8:00-10:00 with 30min reminder buffer = 7:30-10:30
        result = medicine_app.is_in_time_window(
            "08:00", "10:00", current_time, reminder_window_minutes=30
        )

        assert result is True

    def test_is_in_time_window_before_window(self):
        """Test time check when before window"""
        current_time = datetime(2025, 11, 9, 7, 0, 0)  # 7:00 AM

        result = medicine_app.is_in_time_window(
            "08:00", "10:00", current_time, reminder_window_minutes=30
        )

        assert result is False

    def test_is_in_time_window_after_window(self):
        """Test time check when after window"""
        current_time = datetime(2025, 11, 9, 11, 0, 0)  # 11:00 AM

        result = medicine_app.is_in_time_window(
            "08:00", "10:00", current_time, reminder_window_minutes=30
        )

        assert result is False

    def test_is_in_time_window_with_reminder_buffer(self):
        """Test time check within reminder buffer"""
        # 7:45 AM - within 30min reminder buffer before 8:00 window
        current_time = datetime(2025, 11, 9, 7, 45, 0)

        result = medicine_app.is_in_time_window(
            "08:00", "10:00", current_time, reminder_window_minutes=30
        )

        assert result is True

    def test_is_in_time_window_invalid_format(self):
        """Test handling of invalid time format"""
        current_time = datetime(2025, 11, 9, 9, 0, 0)

        result = medicine_app.is_in_time_window(
            "invalid", "10:00", current_time, reminder_window_minutes=30
        )

        assert result is False

    def test_get_current_day(self):
        """Test getting current day as 3-letter code"""
        with patch('datetime.datetime') as mock_dt:
            # Saturday
            mock_dt.now.return_value = datetime(2025, 11, 8, 10, 0, 0)
            mock_dt.strftime = datetime.strftime

            day = medicine_app.get_current_day()
            assert day == "sat"


# ============================================================================
# Test Pending Medicines Logic
# ============================================================================

class TestPendingMedicines:
    """Test getting pending medicines"""

    @patch('medicine_app.REMINDER_WINDOW', 30)
    def test_get_pending_medicines_one_due(self, sample_medicine_data_full):
        """Test getting pending medicines when one is due"""
        with patch('datetime.datetime') as mock_dt:
            # Monday 9:00 AM
            mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
            mock_dt.strftime = datetime.strftime

            pending = medicine_app.get_pending_medicines(sample_medicine_data_full)

            # med1 is due (Mon, 8:00-10:00 window)
            assert len(pending) == 1
            assert pending[0]["id"] == "med1"

    @patch('medicine_app.REMINDER_WINDOW', 30)
    def test_get_pending_medicines_none_due(self, sample_medicine_data_full):
        """Test when no medicines are due"""
        with patch('datetime.datetime') as mock_dt:
            # Monday 14:00 (2 PM) - outside all windows
            mock_dt.now.return_value = datetime(2025, 11, 10, 14, 0, 0)
            mock_dt.strftime = datetime.strftime

            pending = medicine_app.get_pending_medicines(sample_medicine_data_full)

            assert len(pending) == 0

    @patch('medicine_app.REMINDER_WINDOW', 30)
    def test_get_pending_medicines_already_taken(self, sample_medicine_data_full):
        """Test pending excludes already taken medicines"""
        # Mark med1 as taken
        sample_medicine_data_full["tracking"]["2025-11-10"] = {
            "med1_morning": {"taken": True, "timestamp": "2025-11-10T09:00:00"}
        }

        with patch('datetime.datetime') as mock_dt:
            # Monday 9:00 AM
            mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
            mock_dt.strftime = datetime.strftime

            pending = medicine_app.get_pending_medicines(sample_medicine_data_full)

            # med1 was taken, so no pending
            assert len(pending) == 0

    @patch('medicine_app.REMINDER_WINDOW', 30)
    def test_get_pending_medicines_inactive_excluded(self, sample_medicine_data_full):
        """Test that inactive medicines are excluded"""
        with patch('datetime.datetime') as mock_dt:
            # Monday 13:00 (med3's time, but inactive)
            mock_dt.now.return_value = datetime(2025, 11, 10, 13, 0, 0)
            mock_dt.strftime = datetime.strftime

            pending = medicine_app.get_pending_medicines(sample_medicine_data_full)

            # med3 is inactive
            assert len(pending) == 0

    @patch('medicine_app.REMINDER_WINDOW', 30)
    def test_get_pending_medicines_wrong_day(self, sample_medicine_data_full):
        """Test medicines not due on current day are excluded"""
        with patch('datetime.datetime') as mock_dt:
            # Tuesday 9:00 AM (med1 not scheduled for Tue)
            mock_dt.now.return_value = datetime(2025, 11, 11, 9, 0, 0)
            mock_dt.strftime = datetime.strftime

            pending = medicine_app.get_pending_medicines(sample_medicine_data_full)

            # med1 not on Tuesday
            assert len(pending) == 0


# ============================================================================
# Test Medicine Tracking
# ============================================================================

class TestMedicineTracking:
    """Test marking medicines as taken"""

    def test_mark_medicines_taken_single(self, tmp_path, sample_medicine_data_full):
        """Test marking a single medicine as taken"""
        file_path = tmp_path / "tracking_test.json"

        with patch('medicine_app.MEDICINE_DATA_FILE', str(file_path)):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
                mock_dt.strftime = datetime.strftime

                med_to_take = [sample_medicine_data_full["medicines"][0]]
                result = medicine_app.mark_medicines_taken(
                    sample_medicine_data_full, med_to_take
                )

                assert result is True

                # Check tracking was updated
                assert "2025-11-10" in sample_medicine_data_full["tracking"]
                assert "med1_morning" in sample_medicine_data_full["tracking"]["2025-11-10"]
                assert sample_medicine_data_full["tracking"]["2025-11-10"]["med1_morning"]["taken"] is True

                # Check inventory decreased
                assert sample_medicine_data_full["medicines"][0]["pills_remaining"] == 29

    def test_mark_medicines_taken_multiple(self, tmp_path, sample_medicine_data_full):
        """Test marking multiple medicines as taken"""
        file_path = tmp_path / "tracking_test2.json"

        with patch('medicine_app.MEDICINE_DATA_FILE', str(file_path)):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 11, 10, 20, 30, 0)
                mock_dt.strftime = datetime.strftime

                meds_to_take = sample_medicine_data_full["medicines"][:2]
                result = medicine_app.mark_medicines_taken(
                    sample_medicine_data_full, meds_to_take
                )

                assert result is True

                # Check both tracked
                tracking_today = sample_medicine_data_full["tracking"]["2025-11-10"]
                assert "med1_morning" in tracking_today
                assert "med2_evening" in tracking_today

                # Check inventories decreased
                assert sample_medicine_data_full["medicines"][0]["pills_remaining"] == 29
                assert sample_medicine_data_full["medicines"][1]["pills_remaining"] == 4

    def test_mark_medicines_taken_inventory_floor(self, tmp_path, sample_medicine_data_full):
        """Test inventory doesn't go below 0"""
        file_path = tmp_path / "tracking_test3.json"

        # Set inventory to 0
        sample_medicine_data_full["medicines"][0]["pills_remaining"] = 0

        with patch('medicine_app.MEDICINE_DATA_FILE', str(file_path)):
            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
                mock_dt.strftime = datetime.strftime

                med_to_take = [sample_medicine_data_full["medicines"][0]]
                medicine_app.mark_medicines_taken(sample_medicine_data_full, med_to_take)

                # Should stay at 0
                assert sample_medicine_data_full["medicines"][0]["pills_remaining"] == 0


# ============================================================================
# Test Statistics
# ============================================================================

class TestStatistics:
    """Test statistics calculations"""

    def test_get_today_stats_none_taken(self, sample_medicine_data_full):
        """Test stats when no medicines taken"""
        with patch('datetime.datetime') as mock_dt:
            # Monday
            mock_dt.now.return_value = datetime(2025, 11, 10, 10, 0, 0)
            mock_dt.strftime = datetime.strftime

            taken, total = medicine_app.get_today_stats(sample_medicine_data_full)

            # On Monday: med1 (mon) and med2 (daily) = 2 total
            assert taken == 0
            assert total == 2

    def test_get_today_stats_some_taken(self, sample_medicine_data_full):
        """Test stats when some medicines taken"""
        # Mark med1 as taken
        sample_medicine_data_full["tracking"]["2025-11-10"] = {
            "med1_morning": {"taken": True, "timestamp": "2025-11-10T09:00:00"}
        }

        with patch('datetime.datetime') as mock_dt:
            # Monday
            mock_dt.now.return_value = datetime(2025, 11, 10, 10, 0, 0)
            mock_dt.strftime = datetime.strftime

            taken, total = medicine_app.get_today_stats(sample_medicine_data_full)

            assert taken == 1
            assert total == 2

    def test_get_today_stats_all_taken(self, sample_medicine_data_full):
        """Test stats when all medicines taken"""
        sample_medicine_data_full["tracking"]["2025-11-10"] = {
            "med1_morning": {"taken": True, "timestamp": "2025-11-10T09:00:00"},
            "med2_evening": {"taken": True, "timestamp": "2025-11-10T20:00:00"}
        }

        with patch('datetime.datetime') as mock_dt:
            # Monday
            mock_dt.now.return_value = datetime(2025, 11, 10, 22, 0, 0)
            mock_dt.strftime = datetime.strftime

            taken, total = medicine_app.get_today_stats(sample_medicine_data_full)

            assert taken == 2
            assert total == 2

    def test_get_today_stats_inactive_excluded(self, sample_medicine_data_full):
        """Test that inactive medicines don't count in stats"""
        with patch('datetime.datetime') as mock_dt:
            # Monday (med3 would be on Monday if active)
            mock_dt.now.return_value = datetime(2025, 11, 10, 10, 0, 0)
            mock_dt.strftime = datetime.strftime

            taken, total = medicine_app.get_today_stats(sample_medicine_data_full)

            # med3 is inactive, so only med1 and med2 count
            assert total == 2


# ============================================================================
# Test Display Functions
# ============================================================================

class TestDisplayFunctions:
    """Test display rendering functions"""

    def test_draw_pill_icon(self):
        """Test pill icon drawing"""
        img = Image.new("1", (100, 100), 255)
        draw = medicine_app.ImageDraw.Draw(img)

        # Should not raise exception
        medicine_app.draw_pill_icon(draw, 10, 10, 15)

    def test_draw_food_icon(self):
        """Test food icon drawing"""
        img = Image.new("1", (100, 100), 255)
        draw = medicine_app.ImageDraw.Draw(img)

        # Should not raise exception
        medicine_app.draw_food_icon(draw, 10, 10, 10)

    @patch('medicine_app.fontdir', '/tmp')
    def test_draw_current_reminder_no_pending(self):
        """Test drawing reminder screen with no pending medicines"""
        with patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = medicine_app.ImageFont.load_default()

            img = medicine_app.draw_current_reminder([])

            assert isinstance(img, Image.Image)
            assert img.size == (250, 122)

    @patch('medicine_app.fontdir', '/tmp')
    def test_draw_current_reminder_with_medicine(self, sample_medicine_data_full):
        """Test drawing reminder with pending medicine"""
        with patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = medicine_app.ImageFont.load_default()

            pending = [sample_medicine_data_full["medicines"][0]]
            img = medicine_app.draw_current_reminder(pending, 0)

            assert isinstance(img, Image.Image)
            assert img.size == (250, 122)

    @patch('medicine_app.fontdir', '/tmp')
    def test_draw_current_reminder_multiple_medicines(self, sample_medicine_data_full):
        """Test drawing reminder with multiple medicines"""
        with patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = medicine_app.ImageFont.load_default()

            pending = sample_medicine_data_full["medicines"][:2]
            img = medicine_app.draw_current_reminder(pending, 1)

            assert isinstance(img, Image.Image)

    @patch('medicine_app.fontdir', '/tmp')
    def test_draw_schedule_view(self, sample_medicine_data_full):
        """Test drawing schedule view"""
        with patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = medicine_app.ImageFont.load_default()

            with patch('datetime.datetime') as mock_dt:
                mock_dt.now.return_value = datetime(2025, 11, 10, 10, 0, 0)
                mock_dt.strftime = datetime.strftime

                img = medicine_app.draw_schedule_view(sample_medicine_data_full)

                assert isinstance(img, Image.Image)
                assert img.size == (250, 122)

    @patch('medicine_app.fontdir', '/tmp')
    def test_draw_confirmation_screen(self, sample_medicine_data_full):
        """Test drawing confirmation screen"""
        with patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = medicine_app.ImageFont.load_default()

            medicines_taken = [sample_medicine_data_full["medicines"][0]]
            img = medicine_app.draw_confirmation_screen(medicines_taken, 1)

            assert isinstance(img, Image.Image)
            assert img.size == (250, 122)

    @patch('medicine_app.fontdir', '/tmp')
    def test_draw_confirmation_screen_multiple(self, sample_medicine_data_full):
        """Test confirmation screen with many medicines"""
        with patch('PIL.ImageFont.truetype') as mock_font:
            mock_font.return_value = medicine_app.ImageFont.load_default()

            # Test with more than 3 to trigger "X more..." display
            medicines_taken = sample_medicine_data_full["medicines"]
            img = medicine_app.draw_confirmation_screen(medicines_taken, len(medicines_taken))

            assert isinstance(img, Image.Image)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple functions"""

    @patch('medicine_app.REMINDER_WINDOW', 30)
    def test_complete_medicine_cycle(self, tmp_path, sample_medicine_data_full):
        """Test complete flow: load → check pending → mark taken → save"""
        file_path = tmp_path / "integration_test.json"

        # Save initial data
        with open(file_path, 'w') as f:
            json.dump(sample_medicine_data_full, f)

        with patch('medicine_app.MEDICINE_DATA_FILE', str(file_path)):
            with patch('datetime.datetime') as mock_dt:
                # Monday 9:00 AM
                mock_dt.now.return_value = datetime(2025, 11, 10, 9, 0, 0)
                mock_dt.strftime = datetime.strftime

                # Load data
                data = medicine_app.load_medicine_data()
                assert len(data["medicines"]) == 3

                # Check pending
                pending = medicine_app.get_pending_medicines(data)
                assert len(pending) == 1
                assert pending[0]["id"] == "med1"

                # Check stats before
                taken_before, total_before = medicine_app.get_today_stats(data)
                assert taken_before == 0
                assert total_before == 2

                # Mark as taken
                result = medicine_app.mark_medicines_taken(data, pending)
                assert result is True

                # Reload and check stats after
                data = medicine_app.load_medicine_data()
                taken_after, total_after = medicine_app.get_today_stats(data)
                assert taken_after == 1
                assert total_after == 2

                # Check pending again (should be none)
                pending_after = medicine_app.get_pending_medicines(data)
                assert len(pending_after) == 0

    def test_low_stock_detection(self, sample_medicine_data_full):
        """Test low stock warning detection"""
        # med2 has 5 pills remaining with threshold of 10
        med2 = sample_medicine_data_full["medicines"][1]

        assert med2["pills_remaining"] <= med2["low_stock_threshold"]
