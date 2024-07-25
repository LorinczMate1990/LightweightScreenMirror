from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_sock import Sock
import eventlet
import mss
from PIL import Image
import base64
from io import BytesIO
import time
import threading


app = Flask(__name__)
sock = Sock(app)

# Define the rectangle region (left, top, width, height)
RECTANGLE = {'top': 100, 'left': 100, 'width': 700, 'height': 500}

def capture_screen_region():
    with mss.mss() as sct:
        img = sct.grab(RECTANGLE)
        img_pil = Image.frombytes('RGB', img.size, img.rgb)
        buffered = BytesIO()
        img_pil.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

@app.route('/')
def index():
    return render_template('index.html')
        
@sock.route('/video')
def video(ws):
    print("Connected for video stream")
    while True:
        frame = capture_screen_region()
        ws.send(frame)
        time.sleep(1/30)
        
@sock.route('/mouse')
def mouse(ws):
    print("Connected for mouse control")
    while True:
        event = ws.receive(timeout=None)
        print("event: ", event)

if __name__ == '__main__':
    print("Ok")
    app.run(host='0.0.0.0', port=5000)
