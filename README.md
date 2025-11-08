# Pi Zero 2W Application Suite

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-brightgreen.svg)](https://www.python.org/)
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208-lightblue.svg)](https://pep8.org/)

A comprehensive, modular application suite for Raspberry Pi Zero 2W with e-ink display integration. Features weather, transit, Disney wait times, flight tracking, productivity tools, and medicine management.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Applications](#applications)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Pi Zero 2W Application Suite is a production-ready system for managing multiple applications on a Raspberry Pi Zero 2W with a Waveshare 2.13" e-ink display. The system provides:

- **Real-time information display** on a low-power e-ink screen
- **Web-based configuration interface** for easy settings management
- **Modular architecture** for easy extension with new applications
- **Persistent data storage** using SQLite and JSON
- **RESTful API** for programmatic access to all features

**Current Version:** 2.3
**Last Updated:** November 8, 2025
**Device:** Raspberry Pi Zero 2W with Waveshare 2.13" V4 e-ink display

## Features

### Core Capabilities

- ✅ **8+ Integrated Applications** - Weather, transit, flights, Disney, Pomodoro, medicine tracking, and more
- ✅ **E-ink Display Support** - Optimized for Waveshare 2.13" V4 display with partial/full refresh modes
- ✅ **RESTful API** - Complete REST API for all functionality with Flask
- ✅ **Web Configuration** - Browser-based UI for managing settings and data
- ✅ **SQLite Database** - Modern database backend with migration support
- ✅ **Component System** - Reusable display components for consistent UI
- ✅ **GPIO Integration** - Button handling and hardware control
- ✅ **Configuration Management** - JSON-based configuration with validation
- ✅ **Logging & Monitoring** - Comprehensive logging and error tracking
- ✅ **Test Suite** - Unit, integration, and performance tests

### Applications

| App | Purpose | Status |
|-----|---------|--------|
| **Weather** | Current weather & calendar display | ✅ Stable |
| **MBTA** | Boston transit real-time predictions | ✅ Stable |
| **Disney** | Theme park wait times | ✅ Stable |
| **Flights** | ADS-B aircraft tracking | ✅ Stable |
| **Pomodoro** | Productivity timer | ✅ Stable |
| **Medicine** | Reminder & inventory management | ✅ Stable |
| **Forbidden** | Custom message display | ✅ Stable |
| **Reboot** | System reboot utility | ✅ Stable |

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                       │
├──────────────────────┬──────────────────────────────────┤
│   Pi Zero Display    │         Web Browser              │
│   (250x122 e-ink)    │    (Port 5000)                   │
└──────────────────────┴──────────────────────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│              Application Layer                           │
├──────────────────────────────────────────────────────────┤
│  [Weather] [MBTA] [Disney] [Flights] [Pomodoro]         │
│  [Medicine] [Forbidden] [Reboot] [Menu]                 │
└──────────────────────────────────────────────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│          Display & API Layer                            │
├──────────────────────────────────────────────────────────┤
│  [Display Components] [REST API v1] [Web Config]        │
└──────────────────────────────────────────────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│          Data & Hardware Layer                          │
├──────────────────────────────────────────────────────────┤
│  [SQLite DB] [JSON Config] [GPIO Control] [e-ink Driver]│
└──────────────────────────────────────────────────────────┘
```

### Directory Structure

```
pizerowgpio/
├── api/                          # REST API implementation
│   ├── __init__.py
│   ├── config.py
│   ├── security.py
│   └── v1/                       # API v1 endpoints
│       ├── __init__.py
│       ├── medicine.py
│       ├── config.py
│       └── health.py
├── display/                      # Display components & rendering
│   ├── __init__.py
│   ├── canvas.py                 # Canvas management
│   ├── components.py             # UI components
│   ├── fonts.py                  # Font definitions
│   ├── icons.py                  # Icon utilities
│   ├── layouts.py                # Layout templates
│   ├── shapes.py                 # Shape drawing
│   ├── text.py                   # Text rendering
│   └── touch_handler.py          # Touch input handling
├── web/                          # Web UI assets
│   ├── static/                   # CSS, JS, images
│   ├── templates/                # HTML templates
│   └── app.py                    # Flask application
├── config/                       # Configuration files
│   ├── config.json               # Application settings
│   └── example.json              # Example configuration
├── db/                           # Database files
│   └── medicine.db               # SQLite database
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── performance/              # Performance tests
│   └── conftest.py               # Pytest configuration
├── scripts/                      # Utility scripts
├── docs/                         # Documentation
├── systemd/                      # Systemd service files
├── .github/                      # GitHub metadata
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE/
├── app files                     # Individual app modules
│   ├── medicine_app.py
│   ├── weather_cal_app.py
│   ├── mbta_app.py
│   └── ...
├── run_api.py                    # API server entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
├── README.md                     # This file
├── CONTRIBUTING.md               # Contribution guidelines
└── CHANGELOG.md                  # Version history
```

## Hardware Requirements

### Required Hardware

| Component | Specification | Purpose |
|-----------|---------------|---------|
| **Microcomputer** | Raspberry Pi Zero 2W | Main processor (1GHz ARMv8, 512MB RAM) |
| **Display** | Waveshare 2.13" V4 e-ink | Primary output (250×122 px, SPI) |
| **Input** | Push button | Menu navigation (GPIO 3) |
| **Power** | USB micro | 5V input or HAT connector |
| **Storage** | microSD card (8GB+) | OS and data storage |

### Optional Hardware

- WiFi dongle (if not using Pi Zero 2W W variant)
- Hat/Shield for display connector
- Case for protection

### GPIO Configuration

| Pin | Function | Purpose |
|-----|----------|---------|
| GPIO 3 | Button Input | Menu navigation & app control |
| SPI Clock | Display | e-ink SPI communication |
| SPI MOSI | Display | Data transmission to display |
| SPI CS | Display | Chip select for display |
| GPIO 17 | Display | e-ink reset/busy signals |

## Installation

### Prerequisites

- Raspberry Pi OS (Debian-based)
- Python 3.7 or higher
- pip package manager
- git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pizerowgpio.git
   cd pizerowgpio
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   nano .env
   ```

5. **Initialize database**
   ```bash
   python3 -m scripts.init_db
   ```

6. **Run the API server**
   ```bash
   python3 run_api.py
   ```

   Access web UI at: `http://localhost:5000`

### Systemd Installation (Production)

1. **Copy service file**
   ```bash
   sudo cp systemd/pizero-api.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

2. **Enable and start**
   ```bash
   sudo systemctl enable pizero-api
   sudo systemctl start pizero-api
   ```

3. **Check status**
   ```bash
   sudo systemctl status pizero-api
   sudo journalctl -u pizero-api -f
   ```

## Configuration

### Environment Variables (.env)

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secure-key-here

# Database
PIZERO_MEDICINE_DB=/home/user/pizerowgpio/db/medicine.db
CONFIG_FILE=/home/user/pizerowgpio/config/config.json

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/pizero/application.log

# External Services
WEATHER_API_KEY=your-api-key
FLIGHTS_API_KEY=your-api-key
DISNEY_API_KEY=your-api-key
MBTA_API_KEY=your-api-key
```

### config.json Structure

Main configuration file located at `config/config.json`:

```json
{
  "weather": {
    "location": "Rio de Janeiro",
    "units": "metric",
    "update_interval": 300
  },
  "mbta": {
    "home_station_id": "place-davis",
    "work_station_id": "place-pktrm",
    "update_interval": 30
  },
  "medicine": {
    "data_file": "/path/to/medicine.db",
    "update_interval": 60,
    "reminder_window": 30
  },
  "display": {
    "rotation": 0,
    "refresh_mode": "auto"
  },
  "menu": {
    "apps": [
      {"id": "weather", "name": "Weather", "enabled": true, "order": 1}
    ]
  }
}
```

See [Configuration Guide](./docs/CONFIGURATION.md) for complete options.

## Applications

### 1. Medicine Tracker (medicine_app.py)

Real-time medicine reminder and inventory tracking system.

**Features:**
- Time-window based reminders (Morning/Afternoon/Evening/Night)
- Automatic pill count tracking
- Low-stock alerts
- Daily tracking with timestamps
- Support for multiple medicines per time window

**Configuration:**
```json
{
  "medicine": {
    "update_interval": 60,
    "reminder_window": 30,
    "alert_upcoming_minutes": 15
  }
}
```

[Medicine Documentation](./docs/MEDICINE.md)

### 2. Weather & Calendar (weather_cal_app.py)

Current weather, time, and date display with auto-refresh.

**Features:**
- Real-time weather data
- Current time and date
- Temperature and humidity
- Weather icons

[Weather Documentation](./docs/WEATHER.md)

### 3. MBTA Transit (mbta_app.py)

Boston area real-time transit predictions.

**Features:**
- Next 3 train arrivals
- Time-based route switching
- Delay information
- 30-second refresh

[MBTA Documentation](./docs/MBTA.md)

### 4. Disney Wait Times (disney_app.py)

Real-time Disney theme park wait times.

**Features:**
- Rotating ride display
- Wait times in minutes
- Operating status
- Sortable by time or name

[Disney Documentation](./docs/DISNEY.md)

### 5. Flight Tracker (flights_app.py)

Live aircraft tracking using ADS-B data.

**Features:**
- Overhead flight detection
- Altitude and heading
- Airline information
- Configurable radius

[Flights Documentation](./docs/FLIGHTS.md)

### 6. Pomodoro Timer (pomodoro_app.py)

Productivity timer with work/break cycles.

**Features:**
- 25-minute work sessions
- 5-minute short breaks
- 15-minute long breaks
- Session counter
- Animated display

[Pomodoro Documentation](./docs/POMODORO.md)

### 7. Custom Message (forbidden_app.py)

Display custom user-defined messages.

### 8. System Reboot (reboot_app.py)

Safe system reboot with countdown confirmation.

## API Documentation

### REST Endpoints

#### Base URL
```
http://localhost:5000/api/v1
```

#### Medicine Endpoints

**GET /medicine**
- Get all medicines
- Response: Array of medicine objects

**POST /medicine**
- Add new medicine
- Body: Medicine object
- Response: Created medicine with ID

**PUT /medicine/{id}**
- Update existing medicine
- Body: Updated medicine object
- Response: Updated medicine

**DELETE /medicine/{id}**
- Delete medicine
- Response: Success confirmation

**GET /medicine/reminders**
- Get pending reminders
- Response: Array of due medicines

**POST /medicine/{id}/taken**
- Mark medicine as taken
- Body: { timestamp: ISO8601 }
- Response: Updated tracking

#### Configuration Endpoints

**GET /config**
- Get system configuration
- Response: Config object

**PUT /config/{section}**
- Update configuration section
- Body: Section configuration
- Response: Updated configuration

#### Health Endpoints

**GET /health**
- System health check
- Response: Health status object

**GET /status**
- Detailed status report
- Response: Status information

### Authentication

Currently uses secret key validation. Future versions will support JWT tokens.

### Rate Limiting

API is rate-limited to 100 requests per hour by default. Configure via `API_RATE_LIMIT` in `.env`.

### Response Format

All responses follow this format:

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed",
  "timestamp": "2025-11-08T10:30:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "timestamp": "2025-11-08T10:30:00Z"
}
```

## Development

### Setting Up Development Environment

1. **Clone and setup**
   ```bash
   git clone <repo>
   cd pizerowgpio
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Initialize pre-commit hooks**
   ```bash
   pre-commit install
   ```

### Code Style

This project follows PEP 8 style guidelines.

- **Linting:** `pylint` or `flake8`
- **Formatting:** `black` (line length: 100)
- **Type Checking:** `mypy`

**Run linters:**
```bash
black .
flake8
mypy .
```

### Project Structure Guidelines

- **Apps:** Each app in root directory (e.g., `medicine_app.py`)
- **Display:** Reusable components in `display/`
- **API:** Endpoint handlers in `api/v1/`
- **Tests:** Mirror source structure in `tests/`
- **Docs:** Feature documentation in `docs/`

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_medicine_app.py

# With coverage
pytest --cov=. --cov-report=html

# Integration tests only
pytest tests/integration/

# Performance tests
pytest tests/performance/
```

### Test Structure

```
tests/
├── unit/                   # Unit tests (isolated functionality)
├── integration/            # Integration tests (component interactions)
├── performance/            # Performance benchmarks
└── conftest.py            # Shared fixtures and configuration
```

### Writing Tests

```python
import pytest
from display.components import Component

@pytest.fixture
def component():
    return Component()

def test_component_initialization(component):
    assert component is not None
    assert component.size == (250, 122)

@pytest.mark.parametrize("width,height", [
    (250, 122),
    (200, 100),
])
def test_various_sizes(width, height):
    comp = Component(width, height)
    assert comp.size == (width, height)
```

## Troubleshooting

### Common Issues

#### 1. GPIO Busy Error
**Symptom:** "GPIO busy" when starting menu
**Solution:**
```bash
pkill -9 python3
sleep 2
python3 run_api.py
```

#### 2. Web Server Not Accessible
**Symptom:** Cannot connect to port 5000
**Diagnosis:**
```bash
# Check if running
ps aux | grep run_api.py

# Check port
netstat -tulpn | grep 5000

# Check logs
tail -f /var/log/pizero/application.log
```

#### 3. Database Locked
**Symptom:** "Database is locked" errors
**Solution:**
```bash
# Restart service
sudo systemctl restart pizero-api

# Or kill and restart
pkill -f run_api.py
sleep 1
python3 run_api.py
```

#### 4. Display Not Updating
**Symptom:** E-ink display frozen or not refreshing
**Solution:**
```bash
# Check SPI interface
ls -l /dev/spidev*

# Verify display driver
python3 -c "from display.canvas import Canvas; c = Canvas(); print(c.size)"

# Force refresh
sudo systemctl restart pizero-api
```

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=DEBUG
FLASK_DEBUG=True

# Or via command line
export LOG_LEVEL=DEBUG
python3 run_api.py
```

### Logs

Log files location:
- Application: `/var/log/pizero/application.log`
- Systemd: `journalctl -u pizero-api -f`
- API access: `/var/log/pizero/api.log`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

**Quick Summary:**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test
4. Commit with clear messages
5. Push and create a Pull Request

## License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file for details.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history and release notes.

## Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/pizerowgpio/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/pizerowgpio/discussions)
- **Documentation:** [/docs](./docs/)

## Acknowledgments

- Waveshare for excellent e-ink display drivers
- Flask community for the web framework
- Raspberry Pi Foundation for the incredible hardware

---

**Version:** 2.3
**Last Updated:** November 8, 2025
**Maintainer:** Claude Code Assistant
