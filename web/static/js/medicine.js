/* Pi Zero 2W Dashboard - Medicine Tracker */

/* ============================================
   MEDICINE DATA & STATE
   ============================================ */
let medicineData = {medicines: [], tracking: {}, time_windows: {}};

/* ============================================
   MEDICINE UI FUNCTIONS
   ============================================ */

/**
 * Load medicine data from server and display
 */
function loadMedicineDataAndDisplay() {
    loadMedicineData()
        .then(data => {
            medicineData = data;
            displayMedicineList();
        })
        .catch(err => console.error('Failed to load medicine data:', err));
}

/**
 * Display medicine list in the UI
 */
function displayMedicineList() {
    const listEl = document.getElementById('medicine-list');
    if (!medicineData.medicines || medicineData.medicines.length === 0) {
        listEl.innerHTML = '<p style="color: #6b7280;">No medicines added yet. Click "Add New Medicine" to get started.</p>';
        return;
    }

    let html = '';
    medicineData.medicines.forEach(med => {
        const daysText = med.days.map(d => d.charAt(0).toUpperCase() + d.slice(1)).join(', ');
        const windowText = med.time_window.charAt(0).toUpperCase() + med.time_window.slice(1);
        const foodText = med.with_food ? 'Yes' : 'No';

        const pillsRemaining = med.pills_remaining || 0;
        const lowThreshold = med.low_stock_threshold || 10;
        const isLowStock = pillsRemaining <= lowThreshold;
        const stockColor = isLowStock ? '#ef4444' : '#374151';
        const stockWarning = isLowStock ? ' ⚠️ REORDER SOON!' : '';
        const borderColor = isLowStock ? '#ef4444' : '#e5e7eb';

        html += `
            <div style="border: 2px solid ${borderColor}; border-radius: 6px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 4px;">${med.name}</h3>
                        <p style="color: #6b7280; font-size: 13px; margin-bottom: 8px;">${med.dosage}</p>
                        <p style="font-size: 12px; color: #374151;">
                            <strong>Time:</strong> ${windowText} (${med.window_start}-${med.window_end})<br>
                            <strong>Days:</strong> ${daysText}<br>
                            <strong>With food:</strong> ${foodText}<br>
                            <strong style="color: ${stockColor};">Pills remaining:</strong> <span style="color: ${stockColor}; font-weight: 600;">${pillsRemaining}${stockWarning}</span><br>
                            <strong>Pills per dose:</strong> ${med.pills_per_dose || 1}
                            ${med.notes ? '<br><strong>Notes:</strong> ' + med.notes : ''}
                        </p>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="editMedicine('${med.id}')" class="save-btn" style="padding: 6px 12px; font-size: 12px;">Edit</button>
                        <button onclick="deleteMedicine('${med.id}')" class="save-btn" style="padding: 6px 12px; font-size: 12px; background: #ef4444;">Delete</button>
                    </div>
                </div>
            </div>
        `;
    });
    listEl.innerHTML = html;
}

/**
 * Show the add medicine form
 */
function showAddMedicineForm() {
    document.getElementById('medicine-form-card').style.display = 'block';
    document.getElementById('medicine-form-title').textContent = 'Add Medicine';
    document.getElementById('medicine-form').reset();
    document.getElementById('medicine-id').value = '';
    // Check all day checkboxes by default
    document.querySelectorAll('input[name="day"]').forEach(cb => cb.checked = true);
}

/**
 * Cancel medicine form and hide it
 */
function cancelMedicineForm() {
    document.getElementById('medicine-form-card').style.display = 'none';
    document.getElementById('medicine-form').reset();
}

/**
 * Edit existing medicine
 * @param {string} medId - Medicine ID
 */
function editMedicine(medId) {
    const med = medicineData.medicines.find(m => m.id === medId);
    if (!med) return;

    document.getElementById('medicine-form-card').style.display = 'block';
    document.getElementById('medicine-form-title').textContent = 'Edit Medicine';
    document.getElementById('medicine-id').value = med.id;
    document.getElementById('medicine-name').value = med.name;
    document.getElementById('medicine-dosage').value = med.dosage;
    document.getElementById('medicine-window').value = med.time_window;
    document.getElementById('medicine-food').value = med.with_food.toString();
    document.getElementById('medicine-notes').value = med.notes || '';
    document.getElementById('medicine-pills-remaining').value = med.pills_remaining || 0;
    document.getElementById('medicine-pills-per-dose').value = med.pills_per_dose || 1;
    document.getElementById('medicine-low-threshold').value = med.low_stock_threshold || 10;

    // Set day checkboxes
    document.querySelectorAll('input[name="day"]').forEach(cb => {
        cb.checked = med.days.includes(cb.value);
    });
}

/**
 * Delete medicine with confirmation
 * @param {string} medId - Medicine ID
 */
function deleteMedicine(medId) {
    if (!confirm('Are you sure you want to delete this medicine?')) return;

    deleteMedicineById(medId)
        .then(data => {
            if (data.success) {
                loadMedicineDataAndDisplay();
                showStatus('medicine-form', true, 'Medicine deleted successfully');
            } else {
                showStatus('medicine-form', false, data.message);
            }
        })
        .catch(err => showStatus('medicine-form', false, 'Error: ' + err));
}

/* ============================================
   MEDICINE FORM INITIALIZATION
   ============================================ */

/**
 * Initialize medicine form submission handler
 */
function initMedicineForm() {
    document.getElementById('medicine-form').addEventListener('submit', e => {
        e.preventDefault();

        const days = Array.from(document.querySelectorAll('input[name="day"]:checked')).map(cb => cb.value);
        const medId = document.getElementById('medicine-id').value;

        const medicineFormData = {
            id: medId || 'med_' + Date.now(),
            name: document.getElementById('medicine-name').value,
            dosage: document.getElementById('medicine-dosage').value,
            time_window: document.getElementById('medicine-window').value,
            with_food: document.getElementById('medicine-food').value === 'true',
            days: days,
            notes: document.getElementById('medicine-notes').value,
            pills_remaining: parseInt(document.getElementById('medicine-pills-remaining').value) || 0,
            pills_per_dose: parseInt(document.getElementById('medicine-pills-per-dose').value) || 1,
            low_stock_threshold: parseInt(document.getElementById('medicine-low-threshold').value) || 10,
            active: true
        };

        // Get window times from selection
        const windows = {
            morning: {start: '06:00', end: '12:00'},
            afternoon: {start: '12:00', end: '18:00'},
            evening: {start: '18:00', end: '22:00'},
            night: {start: '22:00', end: '23:59'}
        };
        medicineFormData.window_start = windows[medicineFormData.time_window].start;
        medicineFormData.window_end = windows[medicineFormData.time_window].end;

        const apiCall = medId ? updateMedicine(medicineFormData) : addMedicine(medicineFormData);

        apiCall
            .then(data => {
                if (data.success) {
                    cancelMedicineForm();
                    loadMedicineDataAndDisplay();
                    showStatus('medicine-form', true, data.message);
                } else {
                    showStatus('medicine-form', false, data.message);
                }
            })
            .catch(err => showStatus('medicine-form', false, 'Error: ' + err));
    });
}
