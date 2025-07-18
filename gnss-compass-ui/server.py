from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import threading, time

app = Flask(__name__, static_url_path='', static_folder='.')
socketio = SocketIO(app, cors_allowed_origins='*')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)