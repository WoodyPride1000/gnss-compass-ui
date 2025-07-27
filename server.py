
import eventlet
eventlet.monkey_patch()

from flask import Flask, send_from_directory
from flask_socketio import SocketIO
import serial
import threading
import time

app = Flask(__name__, static_url_path='', static_folder='.')
socketio = SocketIO(app, cors_allowed_origins='*')

GNSS_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

# 初期位置（東京駅）
gnss_data = {
    'lat': 35.681236,
    'lng': 139.767125,
    'alt': 0.0,
    'heading': 90.0,
    'fix': '0',
}

# ✅ NMEA → Decimal 度変換（修正済）
def convert_to_decimal(value, direction):
    if not value or len(value) < 4:
        return 0.0
    deg_len = 2 if direction in ['N', 'S'] else 3
    degrees = int(value[:deg_len])
    minutes = float(value[deg_len:])
    decimal = degrees + minutes / 60.0
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# ✅ GNSS受信スレッド
def read_gnss():
    try:
        with serial.Serial(GNSS_PORT, BAUD_RATE, timeout=1) as ser:
            while True:
                line = ser.readline().decode('ascii', errors='ignore').strip()
                if line.startswith('$GNGGA'):
                    parts = line.split(',')
                    if len(parts) > 9 and parts[6] in ['1', '2', '4']:
                        lat = convert_to_decimal(parts[2], parts[3])
                        lng = convert_to_decimal(parts[4], parts[5])
                        alt = float(parts[9])
                        gnss_data['lat'] = lat
                        gnss_data['lng'] = lng
                        gnss_data['alt'] = alt
                        gnss_data['fix'] = parts[6]
                elif line.startswith('$PVT'):  # 仮の方位角センテンス
                    try:
                        gnss_data['heading'] = float(line.split(',')[1])
                    except:
                        pass
                time.sleep(0.1)
    except Exception as e:
        print(f"[ERROR] GNSS read failed: {e}")

# ✅ 地図HTML
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ✅ クライアント接続時ログ
@socketio.on('connect')
def connect():
    print('Client connected')

# ✅ 定期的にGNSSデータ送信
def emit_gnss():
    while True:
        socketio.emit('gnss', gnss_data)
        socketio.sleep(1)

# ✅ メイン実行
if __name__ == '__main__':
    threading.Thread(target=read_gnss, daemon=True).start()
    socketio.start_background_task(emit_gnss)
    socketio.run(app, host='0.0.0.0', port=5000)
