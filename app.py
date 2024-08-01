from flask import Flask, render_template
from flask_sock import Sock
import mss
from PIL import Image
import base64
from io import BytesIO
import time
import json
from pynput.mouse import Button, Controller
import sys

import tkinter as tk

from threading import Thread



RECTANGLE = {'top': 200, 'left': 200, 'width': 1200, 'height': 600}

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
    print("Connected for video stream");
    ws.send('{"type": "meta", "payload": {"streamWidth": '+str(RECTANGLE['width'])+', "streamHeight": '+str(RECTANGLE['height'])+'} }')
    while True:
        frame = capture_screen_region()
        ws.send('{"type": "frame", "payload": "'+frame+'"}')
        time.sleep(1/30)
        
@sock.route('/mouse')
def mouse(ws):
    print("Connected for mouse control")
    while True:
        event = ws.receive(timeout=None)
        print(event)
        event_obj = MouseEvent.from_json(event)
        execute_mouse_event(event_obj)

THICKNESS = 10

class ResizableRectangle:
    def __init__(self, master):
        self.master = master
        self.create_windows()

    def create_windows(self):
        # Create the top, bottom, left, and right windows
        self.top = tk.Toplevel(self.master)
        self.bottom = tk.Toplevel(self.master)
        self.left = tk.Toplevel(self.master)
        self.right = tk.Toplevel(self.master)

        # Remove window decorations
        for win in [self.top, self.bottom, self.left, self.right]:
            win.overrideredirect(True)
            win.configure(bg='red')

        self.update_windows()

        # Bind mouse events for resizing
        self.top.bind('<B1-Motion>', self.resize_top)
        self.bottom.bind('<B1-Motion>', self.resize_bottom)
        self.left.bind('<B1-Motion>', self.resize_left)
        self.right.bind('<B1-Motion>', self.resize_right)

    def update_windows(self):
        width = RECTANGLE['width']
        height = RECTANGLE['height']
        top = RECTANGLE['top']
        left = RECTANGLE['left']
        
        self.top.geometry(f"{width+2*THICKNESS}x{THICKNESS}+{left-THICKNESS}+{top-THICKNESS}")
        self.bottom.geometry(f"{width+2*THICKNESS}x{THICKNESS}+{left-THICKNESS}+{top + height}")
        self.left.geometry(f"{THICKNESS}x{height}+{left-THICKNESS}+{top}")
        self.right.geometry(f"{THICKNESS}x{height}+{left + width}+{top}")

    def resize_top(self, event):
        new_height = RECTANGLE['height'] - (event.y_root - RECTANGLE['top'])
        if new_height > THICKNESS * 2:
            RECTANGLE['height'] = new_height
            RECTANGLE['top'] = event.y_root
            self.update_windows()

    def resize_bottom(self, event):
        new_height = event.y_root - RECTANGLE['top']
        if new_height > THICKNESS * 2:
            RECTANGLE['height'] = new_height
            self.update_windows()

    def resize_left(self, event):
        new_width = RECTANGLE['width'] - (event.x_root - RECTANGLE['left'])
        if new_width > THICKNESS * 2:
            RECTANGLE['width'] = new_width
            RECTANGLE['left'] = event.x_root
            self.update_windows()

    def resize_right(self, event):
        new_width = event.x_root - RECTANGLE['left']
        if new_width > THICKNESS * 2:
            RECTANGLE['width'] = new_width
            self.update_windows()

def createRectangle():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    ResizableRectangle(root)
    root.mainloop()

if __name__ == '__main__':
    print("Starting Tkinter GUI")
    t = Thread(target=createRectangle)
    t.start()
    
    print("Start server")
    app.run(host='0.0.0.0', port=5000)
