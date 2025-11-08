/* Pi Zero 2W Dashboard - API Client */

/* ============================================
   CONFIGURATION API
   ============================================ */

/**
 * Load configuration from server
 * @returns {Promise<Object>} Configuration object
 */
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Populate Weather fields
        document.getElementById('weather-location').value = config.weather?.location || '';
        document.getElementById('weather-units').value = config.weather?.units || 'metric';
        document.getElementById('weather-interval').value = config.weather?.update_interval || 300;
        document.getElementById('weather-format').value = config.weather?.display_format || 'detailed';

        // Populate MBTA fields
        document.getElementById('mbta-home-id').value = config.mbta?.home_station_id || '';
        document.getElementById('mbta-home-name').value = config.mbta?.home_station_name || '';
        document.getElementById('mbta-work-id').value = config.mbta?.work_station_id || '';
        document.getElementById('mbta-work-name').value = config.mbta?.work_station_name || '';
        document.getElementById('mbta-interval').value = config.mbta?.update_interval || 30;
        document.getElementById('mbta-morning-start').value = config.mbta?.morning_start || '06:00';
        document.getElementById('mbta-morning-end').value = config.mbta?.morning_end || '12:00';
        document.getElementById('mbta-evening-start').value = config.mbta?.evening_start || '15:00';
        document.getElementById('mbta-evening-end').value = config.mbta?.evening_end || '21:00';

        // Populate Disney fields
        document.getElementById('disney-park').value = config.disney?.park_id || 6;
        document.getElementById('disney-interval').value = config.disney?.update_interval || 10;
        document.getElementById('disney-refresh').value = config.disney?.data_refresh_rides || 20;
        document.getElementById('disney-sort').value = config.disney?.sort_by || 'wait_time';

        // Populate Flights fields
        document.getElementById('flights-lat').value = config.flights?.lat || '';
        document.getElementById('flights-lon').value = config.flights?.lon || '';
        document.getElementById('flights-alt').value = config.flights?.altitude || '';

        // Populate Pomodoro fields
        document.getElementById('pomodoro-work').value = config.pomodoro?.work_duration || 1500;
        document.getElementById('pomodoro-short').value = config.pomodoro?.short_break || 300;
        document.getElementById('pomodoro-long').value = config.pomodoro?.long_break || 900;
        document.getElementById('pomodoro-sessions').value = config.pomodoro?.sessions_until_long_break || 4;

        // Populate Forbidden fields
        document.getElementById('forbidden-message').value = config.forbidden?.message || '';
    } catch (err) {
        console.error('Failed to load config:', err);
    }
}

/**
 * Save configuration section
 * @param {string} section - Configuration section name
 * @param {Object} data - Configuration data
 * @returns {Promise<Object>} Response object
 */
async function saveConfig(section, data) {
    const response = await fetch(`/api/config/${section}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    return response.json();
}

/* ============================================
   MEDICINE API
   ============================================ */

/**
 * Load medicine data from server
 * @returns {Promise<Object>} Medicine data object
 */
async function loadMedicineData() {
    const response = await fetch('/api/medicine/data');
    return response.json();
}

/**
 * Add new medicine
 * @param {Object} medicineData - Medicine object
 * @returns {Promise<Object>} Response object
 */
async function addMedicine(medicineData) {
    const response = await fetch('/api/medicine/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(medicineData)
    });
    return response.json();
}

/**
 * Update existing medicine
 * @param {Object} medicineData - Medicine object with id
 * @returns {Promise<Object>} Response object
 */
async function updateMedicine(medicineData) {
    const response = await fetch('/api/medicine/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(medicineData)
    });
    return response.json();
}

/**
 * Delete medicine by ID
 * @param {string} medId - Medicine ID
 * @returns {Promise<Object>} Response object
 */
async function deleteMedicineById(medId) {
    const response = await fetch(`/api/medicine/delete/${medId}`, {
        method: 'DELETE'
    });
    return response.json();
}
