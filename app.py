from flask import Flask, render_template
from flask_sock import Sock
import mss
from PIL import Image
import base64
from io import BytesIO
import time
import json
from pynput.mouse import Button, Controller

RECTANGLE = {'top': 100, 'left': 100, 'width': 700, 'height': 500}

class MouseEvent:
    def __init__(self, x, y, event, width, height):
        self.x = x
        self.y = y
        self.event = event
        self.width = width
        self.height = height

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(data['x'], data['y'], data['event'], data['width'], data['height'])

mouse_controller = Controller()

def map_to_rectangle(mouseX, mouseY, maxMouseX, maxMouseY, goalArea):
    goalX = goalArea['left'] + (mouseX / maxMouseX) * goalArea['width']
    goalY = goalArea['top'] + (mouseY / maxMouseY) * goalArea['height']
    return (int(goalX), int(goalY))

def execute_mouse_event(event_obj):
    mapped_x, mapped_y = map_to_rectangle(event_obj.x, event_obj.y, event_obj.width, event_obj.height, RECTANGLE)
    
    if event_obj.event == 'move':
        print(f"Mouse move to ({mapped_x}, {mapped_y})")
        mouse_controller.position = (mapped_x, mapped_y)
    elif event_obj.event == 'down':
        print(f"Mouse down at ({mapped_x}, {mapped_y})")
        mouse_controller.position = (mapped_x, mapped_y)
        mouse_controller.press(Button.left)
    elif event_obj.event == 'up':
        print(f"Mouse up at ({mapped_x}, {mapped_y})")
        mouse_controller.position = (mapped_x, mapped_y)
        mouse_controller.release(Button.left)

app = Flask(__name__)
sock = Sock(app)

# Define the rectangle region (left, top, width, height)

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
        event_obj = MouseEvent.from_json(event)
        execute_mouse_event(event_obj)

if __name__ == '__main__':
    print("Ok")
    app.run(host='0.0.0.0', port=5000)
