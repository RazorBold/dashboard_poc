from flask import Flask, render_template, request, redirect, url_for, flash
from db_connection import (get_all_registration_data, insert_device_data, 
                         get_device_count, get_all_devices, get_registration_data_by_imei)
from datetime import datetime
from math import ceil

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Add this line after creating the Flask app

ROWS_PER_PAGE = 10

def get_formatted_data(page=1, start_date=None, end_date=None, get_all=False, data=None):
    if data is None:
        data = get_all_registration_data()
    
    gps_data = []
    latest_data = None
    latest_heartbeat = None
    
    if not data:
        return [], 1, 0, None, None
    
    # Define valid message types
    valid_types = ['GNSS', 'Heartbeat', 'Alarm', 'Beacon', 'Registration']
    
    # Filter messages by valid types
    valid_messages = [x for x in data if x.get('payload_id_2') in valid_types and x.get('timestamp')]
    
    # Get latest GNSS data for map (separate from table data)
    gnss_data = [x for x in data if x.get('payload_id_2') == 'GNSS' and x.get('timestamp')]
    if gnss_data:
        latest_gnss = sorted(gnss_data,
                           key=lambda x: x['timestamp'] if isinstance(x['timestamp'], datetime) else datetime.min,
                           reverse=True)[0]
        latest_data = latest_gnss.copy()
        if latest_data:
            # Fix: Swap latitude/longitude values since they're stored incorrectly in DB
            db_lat = latest_data.get('latitude', 0)  # Actually contains longitude
            db_lon = latest_data.get('longitude', 0)  # Actually contains latitude
            latest_data['longitude'] = float(db_lat) if db_lat else 0  # Set longitude from 'latitude' field
            latest_data['latitude'] = float(db_lon) if db_lon else 0   # Set latitude from 'longitude' field
            latest_data['last_update'] = latest_data.get('timestamp', 'N/A')

    # Get latest heartbeat for battery info
    heartbeat_data = [x for x in valid_messages if x.get('payload_id_2') == 'Heartbeat']
    if heartbeat_data:
        latest_heartbeat = sorted(heartbeat_data,
                                key=lambda x: x['timestamp'] if isinstance(x['timestamp'], datetime) else datetime.min,
                                reverse=True)[0]
        if latest_data:
            latest_data['battery'] = latest_heartbeat.get('voltage', 'N/A')

    # Apply date filter if provided
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            end = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            valid_messages = [x for x in valid_messages 
                            if start <= x['timestamp'] <= end]
        except ValueError as e:
            print(f"Error parsing date range: {e}")
            return [], 1, 0, None, None

    # Process messages for table display
    if valid_messages:
        sorted_data = sorted(valid_messages, 
                           key=lambda x: x['timestamp'] if isinstance(x['timestamp'], datetime) else datetime.min,
                           reverse=True)
        
        for idx, row in enumerate(sorted_data, 1):
            try:
                entry = {
                    'no': idx,
                    'payload_id_1': row.get('payload_id_1', 'N/A'),
                    'battery': row.get('voltage', 'N/A') if row.get('payload_id_2') == 'Heartbeat' else latest_heartbeat.get('voltage', 'N/A') if latest_heartbeat else 'N/A',
                    'last_update': row.get('timestamp', 'N/A'),
                    'tipe': row.get('payload_id_2', 'N/A')
                }
                
                if row.get('payload_id_2') == 'GNSS':
                    # Fix: Swap latitude/longitude values for table display
                    db_lat = row.get('latitude', 0)   # Actually contains longitude
                    db_lon = row.get('longitude', 0)  # Actually contains latitude
                    entry['longitude'] = float(db_lat) if db_lat else 0
                    entry['latitude'] = float(db_lon) if db_lon else 0
                else:
                    entry['longitude'] = 'N/A'
                    entry['latitude'] = 'N/A'
                    
                    if row.get('payload_id_2') == 'Alarm':
                        entry['alarm_type'] = row.get('alarm_type', 'N/A')
                    elif row.get('payload_id_2') == 'Beacon':
                        entry['beacon_id'] = row.get('beacon_id', 'N/A')
                
                gps_data.append(entry)
            except Exception as e:
                print(f"Error processing row {idx}: {e}")
                continue

    # Pagination
    total_records = len(gps_data)
    total_pages = max(1, ceil(total_records / ROWS_PER_PAGE))
    start_idx = (page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    
    paginated_data = gps_data[start_idx:end_idx]
    
    return (paginated_data, total_pages, total_records, latest_data,
            [latest_data] if latest_data else [])  # Return only latest GNSS point for map

@app.route('/')
def dashboard():
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    selected_device = request.args.get('device')
    
    # Get all devices for the selector
    devices = get_all_devices()
    
    # Get data based on selected device
    if selected_device:
        data = get_registration_data_by_imei(selected_device)
    else:
        data = get_all_registration_data()
    
    # Continue with existing data formatting
    paginated_data, total_pages, total_records, latest_data, _ = get_formatted_data(
        page, start_date, end_date, data=data)
    
    device_count = get_device_count()
    
    # Get all GPS data for the map
    all_gps_data = []
    try:
        _, _, _, _, all_gps_data = get_formatted_data(1, start_date, end_date, get_all=True, data=data)
        if all_gps_data is None:
            all_gps_data = []
    except Exception as e:
        print(f"Error getting all GPS data: {e}")
        all_gps_data = []
    
    return render_template('dashboard.html', 
                         gps_data=paginated_data,
                         latest_data=latest_data,
                         total_pages=total_pages,
                         current_page=page,
                         total_records=total_records,
                         all_gps_data=all_gps_data,
                         device_count=device_count,
                         devices=devices,
                         selected_device=selected_device)

@app.route('/insert-asset', methods=['GET', 'POST'])
def insert_asset():
    if request.method == 'POST':
        imei = request.form.get('imei')
        serial_number = request.form.get('serial_number')
        
        # Validate input
        if not imei or not serial_number:
            flash('Both IMEI and Serial Number are required', 'error')
            return redirect(url_for('insert_asset'))
        
        # Insert to database
        success = insert_device_data(imei, serial_number)
        
        if success:
            flash('Device successfully added', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Failed to add device', 'error')
            return redirect(url_for('insert_asset'))
            
    return render_template('insert_asset.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')