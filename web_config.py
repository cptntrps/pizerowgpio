#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

# Configure Flask app with custom template and static folders
app = Flask(__name__,
            template_folder='web/templates',
            static_folder='web/static')
CONFIG_FILE = "/home/pizero2w/pizero_apps/config.json"

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/<section>', methods=['POST'])
def update_config(section):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        data = request.get_json()
        config[section] = data

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        return jsonify({"success": True, "message": f"{section.title()} settings saved successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

# Medicine API endpoints
MEDICINE_DATA_FILE = "/home/pizero2w/pizero_apps/medicine_data.json"

@app.route('/api/medicine/data', methods=['GET'])
def get_medicine_data():
    try:
        with open(MEDICINE_DATA_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"medicines": [], "tracking": {}, "time_windows": {}}), 200

@app.route('/api/medicine/add', methods=['POST'])
def add_medicine():
    try:
        with open(MEDICINE_DATA_FILE, 'r') as f:
            data = json.load(f)

        new_med = request.get_json()

        if 'medicines' not in data:
            data['medicines'] = []

        data['medicines'].append(new_med)

        # Add timestamp for push refresh
        data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        with open(MEDICINE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True, "message": "Medicine added successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/medicine/update', methods=['POST'])
def update_medicine():
    try:
        with open(MEDICINE_DATA_FILE, 'r') as f:
            data = json.load(f)

        updated_med = request.get_json()

        if 'medicines' not in data:
            data['medicines'] = []

        # Find and update the medicine
        found = False
        for i, med in enumerate(data['medicines']):
            if med['id'] == updated_med['id']:
                data['medicines'][i] = updated_med
                found = True
                break

        if not found:
            return jsonify({"success": False, "message": "Medicine not found"}), 404

        # Add timestamp for push refresh
        data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        with open(MEDICINE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True, "message": "Medicine updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/medicine/delete/<med_id>', methods=['DELETE'])
def delete_medicine(med_id):
    try:
        with open(MEDICINE_DATA_FILE, 'r') as f:
            data = json.load(f)

        if 'medicines' not in data:
            data['medicines'] = []

        # Filter out the medicine to delete
        original_length = len(data['medicines'])
        data['medicines'] = [m for m in data['medicines'] if m['id'] != med_id]

        if len(data['medicines']) == original_length:
            return jsonify({"success": False, "message": "Medicine not found"}), 404

        # Add timestamp for push refresh
        data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        with open(MEDICINE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        return jsonify({"success": True, "message": "Medicine deleted successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/medicine/mark-taken', methods=['POST'])
def mark_medicine_taken():
    """
    Mark medicine(s) as taken

    Request body:
    {
        "medicine_ids": ["med_001", "med_002"],  // Array of medicine IDs
        "timestamp": "2025-11-07T08:30:00"       // Optional, defaults to now
    }

    OR for single medicine:
    {
        "medicine_id": "med_001",
        "timestamp": "2025-11-07T08:30:00"
    }
    """
    try:
        from datetime import datetime

        with open(MEDICINE_DATA_FILE, 'r') as f:
            data = json.load(f)

        request_data = request.get_json()

        # Support both single and multiple medicines
        medicine_ids = []
        if 'medicine_ids' in request_data:
            medicine_ids = request_data['medicine_ids']
        elif 'medicine_id' in request_data:
            medicine_ids = [request_data['medicine_id']]
        else:
            return jsonify({"success": False, "message": "No medicine_id or medicine_ids provided"}), 400

        # Get timestamp (use provided or current time)
        if 'timestamp' in request_data:
            timestamp = request_data['timestamp']
            # Parse to validate format
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return jsonify({"success": False, "message": "Invalid timestamp format. Use ISO 8601 (e.g., 2025-11-07T08:30:00)"}), 400
        else:
            dt = datetime.now()
            timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S")

        today = dt.strftime("%Y-%m-%d")

        # Initialize tracking for today if needed
        if 'tracking' not in data:
            data['tracking'] = {}
        if today not in data['tracking']:
            data['tracking'][today] = {}

        # Track which medicines were found and marked
        marked_medicines = []
        not_found = []

        for med_id in medicine_ids:
            # Find the medicine
            medicine = None
            for med in data.get('medicines', []):
                if med['id'] == med_id:
                    medicine = med
                    break

            if not medicine:
                not_found.append(med_id)
                continue

            # Mark as taken
            time_window = medicine.get('time_window', 'morning')
            tracking_key = f"{med_id}_{time_window}"

            data['tracking'][today][tracking_key] = {
                "taken": True,
                "timestamp": timestamp
            }

            # Decrement pill count
            pills_per_dose = medicine.get('pills_per_dose', 1)
            current_count = medicine.get('pills_remaining', 0)
            new_count = max(0, current_count - pills_per_dose)

            # Update pill count in the medicine list
            for i, med in enumerate(data['medicines']):
                if med['id'] == med_id:
                    data['medicines'][i]['pills_remaining'] = new_count
                    break

            marked_medicines.append({
                "id": med_id,
                "name": medicine['name'],
                "pills_remaining": new_count,
                "low_stock": new_count <= medicine.get('low_stock_threshold', 10)
            })

        # Add timestamp for push refresh
        data['last_updated'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Save updated data
        with open(MEDICINE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        # Build response message
        if len(marked_medicines) == 0:
            return jsonify({
                "success": False,
                "message": "No medicines found",
                "not_found": not_found
            }), 404

        response = {
            "success": True,
            "message": f"Marked {len(marked_medicines)} medicine(s) as taken",
            "marked": marked_medicines,
            "timestamp": timestamp
        }

        if not_found:
            response["not_found"] = not_found
            response["message"] += f" ({len(not_found)} not found)"

        return jsonify(response)

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/api/medicine/pending', methods=['GET'])
def get_pending_medicines():
    """
    Get medicines that are due now (within time window)

    Optional query params:
    - date: YYYY-MM-DD (defaults to today)
    - time: HH:MM (defaults to current time)
    """
    try:
        from datetime import datetime

        with open(MEDICINE_DATA_FILE, 'r') as f:
            data = json.load(f)

        # Get date and time from query params or use current
        date_str = request.args.get('date')
        time_str = request.args.get('time')

        if date_str and time_str:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        else:
            dt = datetime.now()

        today = dt.strftime("%Y-%m-%d")
        current_day = dt.strftime("%a").lower()
        current_hour = dt.hour
        current_minute = dt.minute
        current_mins = current_hour * 60 + current_minute

        # Reminder window in minutes
        reminder_window = 30

        pending = []

        for med in data.get('medicines', []):
            if not med.get('active', True):
                continue

            # Check if today is a scheduled day
            if current_day not in med.get('days', []):
                continue

            # Check if in time window
            window_start = med.get('window_start', '00:00')
            window_end = med.get('window_end', '23:59')

            start_h, start_m = map(int, window_start.split(':'))
            end_h, end_m = map(int, window_end.split(':'))

            start_mins = start_h * 60 + start_m - reminder_window
            end_mins = end_h * 60 + end_m + reminder_window

            if not (start_mins <= current_mins <= end_mins):
                continue

            # Check if already taken today
            tracking_key = f"{med['id']}_{med['time_window']}"
            if today in data.get('tracking', {}):
                if tracking_key in data['tracking'][today]:
                    if data['tracking'][today][tracking_key].get('taken', False):
                        continue

            pending.append({
                "id": med['id'],
                "name": med['name'],
                "dosage": med['dosage'],
                "time_window": med['time_window'],
                "with_food": med.get('with_food', False),
                "notes": med.get('notes', ''),
                "pills_remaining": med.get('pills_remaining', 0),
                "low_stock": med.get('pills_remaining', 0) <= med.get('low_stock_threshold', 10)
            })

        return jsonify({
            "success": True,
            "count": len(pending),
            "medicines": pending,
            "checked_at": dt.strftime("%Y-%m-%dT%H:%M:%S")
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
