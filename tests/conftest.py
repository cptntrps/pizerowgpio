"""
Pytest Configuration and Shared Fixtures
=========================================

Provides mocks and fixtures for testing Pi Zero 2W applications.

Mocked Hardware:
- E-ink display (epd2in13_V3, epd2in13_V4)
- Touch screen (gt1151)
- GPIO buttons (gpiozero.Button)

Fixtures:
- mock_epd: E-ink display mock
- mock_gt: Touch screen mock
- mock_button: GPIO button mock
- sample_config: Sample configuration dictionary
- temp_config_file: Temporary config file
"""

import pytest
import sys
import json
import os
from unittest.mock import MagicMock, Mock, patch
from PIL import Image, ImageDraw, ImageFont
import tempfile


# ============================================================================
# Hardware Mocking - Must happen before imports
# ============================================================================

class MockEPD:
    """Mock E-Paper Display"""
    def __init__(self):
        self.width = 250
        self.height = 122
        self.init_called = False
        self.display_calls = []
        self.sleep_called = False

    def init(self):
        self.init_called = True

    def Init(self):
        self.init_called = True

    def display(self, image):
        self.display_calls.append(image)

    def Display(self, image):
        self.display_calls.append(image)

    def sleep(self):
        self.sleep_called = True

    def Sleep(self):
        self.sleep_called = True

    def Clear(self):
        pass


class MockGT:
    """Mock Touch Screen Driver"""
    def __init__(self):
        self.init_called = False

    def GT_Init(self):
        self.init_called = True


class MockGTDev:
    """Mock Touch Screen Device State"""
    def __init__(self):
        self.Touch = 0  # 0 = no touch, 1 = touching


class MockGTOld:
    """Mock Touch Screen Coordinates"""
    def __init__(self):
        self.X = [0]
        self.Y = [0]


class MockButton:
    """Mock GPIO Button"""
    def __init__(self, pin, hold_time=2):
        self.pin = pin
        self.hold_time = hold_time
        self.when_pressed = None
        self.when_held = None

    def close(self):
        pass


# Mock hardware modules before any app imports
sys.modules['TP_lib'] = MagicMock()
sys.modules['TP_lib.epd2in13_V3'] = MagicMock()
sys.modules['TP_lib.epd2in13_V4'] = MagicMock()
sys.modules['TP_lib.gt1151'] = MagicMock()
sys.modules['gpiozero'] = MagicMock()


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def mock_epd():
    """Provides a mock E-Paper Display"""
    epd = MockEPD()
    with patch('TP_lib.epd2in13_V3.EPD', return_value=epd):
        with patch('TP_lib.epd2in13_V4.EPD', return_value=epd):
            yield epd


@pytest.fixture
def mock_gt():
    """Provides a mock Touch Screen driver"""
    gt = MockGT()
    gt_dev = MockGTDev()
    gt_old = MockGTOld()

    with patch('TP_lib.gt1151.GT_Development') as mock_dev_class:
        with patch('TP_lib.gt1151.GT_Old') as mock_old_class:
            mock_dev_class.return_value = gt_dev
            mock_old_class.return_value = gt_old
            yield {'gt': gt, 'gt_dev': gt_dev, 'gt_old': gt_old}


@pytest.fixture
def mock_button():
    """Provides a mock GPIO Button"""
    button = MockButton(pin=3)
    with patch('gpiozero.Button', return_value=button):
        yield button


@pytest.fixture
def sample_config():
    """Provides a sample configuration dictionary"""
    return {
        "weather": {
            "location": "Boston",
            "units": "metric",
            "update_interval": 300
        },
        "medicine": {
            "data_file": "/tmp/medicine_data.json",
            "update_interval": 60,
            "reminder_window": 30,
            "alert_upcoming_minutes": 15,
            "rotate_interval": 3
        },
        "disney": {
            "park_id": 6,
            "park_name": "Magic Kingdom",
            "update_interval": 10,
            "data_refresh_rides": 20,
            "sort_by": "wait_time",
            "show_closed": False,
            "favorite_rides": []
        },
        "flights": {
            "latitude": 40.716389,
            "longitude": -73.954167,
            "radius_km": 15,
            "update_interval": 15,
            "min_altitude": 0,
            "max_altitude": 10000,
            "show_details": True
        },
        "forbidden": {
            "message": "Custom message here"
        },
        "menu": {
            "apps": [
                {"id": "medicine", "name": "Medicine", "enabled": True, "order": 1},
                {"id": "disney", "name": "Disney", "enabled": True, "order": 2},
                {"id": "flights", "name": "Flights", "enabled": True, "order": 3},
                {"id": "reboot", "name": "Reboot", "enabled": True, "order": 4}
            ],
            "button_hold_time": 2.0,
            "scroll_speed": 0.5
        },
        "system": {
            "timezone": "America/New_York",
            "display_brightness": 100
        },
        "display": {
            "rotation": 0,
            "invert_colors": False,
            "refresh_mode": "auto"
        }
    }


@pytest.fixture
def sample_medicine_data():
    """Provides sample medicine data"""
    return {
        "medicines": [
            {
                "id": "med1",
                "name": "Vitamin D",
                "dosage": "1000 IU",
                "schedule": {
                    "time": "08:00",
                    "days": ["mon", "wed", "fri"]
                },
                "inventory": {
                    "current_count": 30,
                    "alert_threshold": 10
                },
                "with_food": True
            },
            {
                "id": "med2",
                "name": "Omega-3",
                "dosage": "1 capsule",
                "schedule": {
                    "time": "20:00",
                    "days": ["daily"]
                },
                "inventory": {
                    "current_count": 5,
                    "alert_threshold": 10
                },
                "with_food": False
            }
        ],
        "tracking": {},
        "time_windows": {}
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Creates a temporary config file"""
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(sample_config, f, indent=2)
    return str(config_file)


@pytest.fixture
def temp_medicine_file(sample_medicine_data, tmp_path):
    """Creates a temporary medicine data file"""
    med_file = tmp_path / "medicine_data.json"
    with open(med_file, 'w') as f:
        json.dump(sample_medicine_data, f, indent=2)
    return str(med_file)


@pytest.fixture
def mock_subprocess_success():
    """Mocks subprocess.run for successful command execution"""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"success": true}'
        mock_result.stderr = ''
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_subprocess_failure():
    """Mocks subprocess.run for failed command execution"""
    with patch('subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ''
        mock_result.stderr = 'Command failed'
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def mock_datetime():
    """Mocks datetime for consistent testing"""
    from datetime import datetime
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 11, 9, 10, 30, 0)
        mock_dt.strptime = datetime.strptime
        mock_dt.fromisoformat = datetime.fromisoformat
        yield mock_dt


@pytest.fixture(autouse=True)
def mock_fonts():
    """Auto-mock fonts to prevent file not found errors"""
    default_font = ImageFont.load_default()

    def mock_truetype(*args, **kwargs):
        return default_font

    with patch('PIL.ImageFont.truetype', side_effect=mock_truetype):
        yield


@pytest.fixture
def flask_client():
    """Provides Flask test client for web_config.py"""
    # This will be implemented in test_web_config.py
    # as it requires importing web_config.py
    pass


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_image(width=250, height=122, mode='1'):
    """Creates a test image"""
    return Image.new(mode, (width, height), 255)


def simulate_touch(gt_dev, gt_old, x, y, duration=0.1):
    """Simulates a touch event"""
    import time
    gt_dev.Touch = 1
    gt_old.X = [x]
    gt_old.Y = [y]
    time.sleep(duration)
    gt_dev.Touch = 0


def simulate_button_press(button):
    """Simulates a button press"""
    if button.when_pressed:
        button.when_pressed()


def simulate_button_hold(button):
    """Simulates a button hold"""
    if button.when_held:
        button.when_held()
