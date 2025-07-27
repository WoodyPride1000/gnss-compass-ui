import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO

import serial
import threading
import time

app = Flask(__name__, static_url_path='', static_folder='.')
socketio = SocketIO(app, cors_allowed_origins='*')

GNSS_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

gnss_data = {
    'lat': 35.681236,
    'lng': 139.767125,
    'alt': 0.0,
    'heading': 90.0,
    'fix': '0',
}

def read_gnss():
    try:
        with serial.Serial(GNSS_PORT, BAUD_RATE, timeout=1) as ser:
            while True:
                line = ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$GNGGA'):
                    parts = line.split(',')
                    if len(parts) > 9 and parts[6] in ['1', '2', '4']:
                        gnss_data['lat'] = convert_to_decimal(parts[2], parts[3])
                        gnss_data['lng'] = convert_to_decimal(parts[4], parts[5])
                        gnss_data['alt'] = float(parts[9])
                        gnss_data['fix'] = parts[6]
                elif line.startswith('$PVT'):
                    # 仮想例: ヘディング値が別プロトコルで来ると仮定
                    gnss_data['heading'] = float(line.split(',')[1])
                time.sleep(0.1)
    except Exception as e:
        print(f"[ERROR] GNSS read failed: {e}")

#def convert_to_decimal(value, direction):
#    if not value or len(value) < 4:
#        return 0.0
#    degrees = int(value[:2])
#    minutes = float(value[2:])
#    decimal = degrees + minutes / 60.0
#    if direction in ['S', 'W']:
#        decimal *= -1
#    return decimal

def convert_to_decimal(value, direction):
    if not value or len(value) < 4:
        return 0.0
    dot = value.find('.')
    degrees_len = dot - 2
    degrees = int(value[:degrees_len])
    minutes = float(value[degrees_len:])
    decimal = degrees + minutes / 60.0
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@socketio.on('connect')
def connect():
    print('Client connected')

#def emit_gnss():
#    while True:
#        socketio.emit('gnss', gnss_data)
#        socketio.sleep(1)

def emit_gnss():
    while True:
        # heading が欠損している場合は 0.0 を補完
        if 'heading' not in gnss_data:
            gnss_data['heading'] = 0.0
        socketio.emit('gnss', gnss_data)
        socketio.sleep(1)

if __name__ == '__main__':
    threading.Thread(target=read_gnss, daemon=True).start()
    socketio.start_background_task(emit_gnss)
    socketio.run(app, host='0.0.0.0', port=5000)
