#!/usr/bin/env python3
from backend.app import app
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # print("Starting Flask server...")
    # threading.Thread(target=open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
