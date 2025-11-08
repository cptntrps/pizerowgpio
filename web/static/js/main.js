/* Pi Zero 2W Dashboard - Main JavaScript */

/* ============================================
   INITIALIZATION
   ============================================ */

// Load config on page load
window.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    initMedicineForm();
});

/* ============================================
   NAVIGATION FUNCTIONS
   ============================================ */

/**
 * Show specific content section and update active state
 * @param {string} section - Section ID to show
 */
function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));

    // Remove active state from all menu items
    document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active'));

    // Show selected section
    document.getElementById(section).classList.add('active');

    // Set active state on clicked menu item
    event.target.classList.add('active');

    // Load medicine data when medicine section is shown
    if (section === 'medicine') {
        loadMedicineDataAndDisplay();
    }
}

/**
 * Toggle submenu visibility
 * @param {string} id - Submenu ID prefix
 */
function toggleSubmenu(id) {
    const submenu = document.getElementById(id + '-submenu');
    submenu.style.display = submenu.style.display === 'none' ? 'block' : 'none';
}

/* ============================================
   UI UTILITY FUNCTIONS
   ============================================ */

/**
 * Show status message
 * @param {string} formId - Form ID prefix
 * @param {boolean} success - Success state
 * @param {string} message - Message to display
 */
function showStatus(formId, success, message) {
    const status = document.getElementById(formId + '-status');
    status.className = 'status-message ' + (success ? 'success' : 'error');
    status.textContent = message;
    status.style.display = 'block';
    setTimeout(() => status.style.display = 'none', 3000);
}

/* ============================================
   FORM SUBMISSION HANDLERS
   ============================================ */

// Weather Form
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('weather-form').addEventListener('submit', e => {
        e.preventDefault();
        saveConfig('weather', {
            location: document.getElementById('weather-location').value,
            units: document.getElementById('weather-units').value,
            update_interval: parseInt(document.getElementById('weather-interval').value),
            display_format: document.getElementById('weather-format').value
        })
        .then(data => showStatus('weather', data.success, data.message))
        .catch(err => showStatus('weather', false, 'Error: ' + err));
    });
});

// MBTA Form
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('mbta-form').addEventListener('submit', e => {
        e.preventDefault();
        saveConfig('mbta', {
            home_station_id: document.getElementById('mbta-home-id').value,
            home_station_name: document.getElementById('mbta-home-name').value,
            work_station_id: document.getElementById('mbta-work-id').value,
            work_station_name: document.getElementById('mbta-work-name').value,
            update_interval: parseInt(document.getElementById('mbta-interval').value),
            morning_start: document.getElementById('mbta-morning-start').value,
            morning_end: document.getElementById('mbta-morning-end').value,
            evening_start: document.getElementById('mbta-evening-start').value,
            evening_end: document.getElementById('mbta-evening-end').value
        })
        .then(data => showStatus('mbta', data.success, data.message))
        .catch(err => showStatus('mbta', false, 'Error: ' + err));
    });
});

// Disney Form
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('disney-form').addEventListener('submit', e => {
        e.preventDefault();
        saveConfig('disney', {
            park_id: parseInt(document.getElementById('disney-park').value),
            update_interval: parseInt(document.getElementById('disney-interval').value),
            data_refresh_rides: parseInt(document.getElementById('disney-refresh').value),
            sort_by: document.getElementById('disney-sort').value
        })
        .then(data => showStatus('disney', data.success, data.message))
        .catch(err => showStatus('disney', false, 'Error: ' + err));
    });
});

// Flights Form
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('flights-form').addEventListener('submit', e => {
        e.preventDefault();
        saveConfig('flights', {
            lat: document.getElementById('flights-lat').value,
            lon: document.getElementById('flights-lon').value,
            altitude: parseInt(document.getElementById('flights-alt').value)
        })
        .then(data => showStatus('flights', data.success, data.message))
        .catch(err => showStatus('flights', false, 'Error: ' + err));
    });
});

// Pomodoro Form
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('pomodoro-form').addEventListener('submit', e => {
        e.preventDefault();
        saveConfig('pomodoro', {
            work_duration: parseInt(document.getElementById('pomodoro-work').value),
            short_break: parseInt(document.getElementById('pomodoro-short').value),
            long_break: parseInt(document.getElementById('pomodoro-long').value),
            sessions_until_long_break: parseInt(document.getElementById('pomodoro-sessions').value)
        })
        .then(data => showStatus('pomodoro', data.success, data.message))
        .catch(err => showStatus('pomodoro', false, 'Error: ' + err));
    });
});

// Forbidden Form
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('forbidden-form').addEventListener('submit', e => {
        e.preventDefault();
        saveConfig('forbidden', {
            message: document.getElementById('forbidden-message').value
        })
        .then(data => showStatus('forbidden', data.success, data.message))
        .catch(err => showStatus('forbidden', false, 'Error: ' + err));
    });
});
