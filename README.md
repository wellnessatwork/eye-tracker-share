# Eye Blink Counter with MediaPipe

This is a simple Python application that counts eye blinks in real-time using your webcam, [MediaPipe](https://google.github.io/mediapipe/) Face Mesh, and OpenCV.

## Features
- Real-time eye blink detection and counting
- Uses MediaPipe Face Mesh for accurate eye landmark detection
- Simple and easy to use
- **Live JSON output:** Prints the current blink count as a JSON object to the terminal on every frame

## Installation

1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd eye-tracker-share
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application with:
```bash
python eye_blink_counter.py
```

- The OpenCV window will show your webcam feed and the current blink count.
- The terminal will continuously print the blink count as a JSON object, e.g.:
  ```
  {"blink_count": 0}
  {"blink_count": 1}
  ...
  ```
- Press `ESC` in the OpenCV window to exit the application.

## Requirements
- Python 3.7+
- OpenCV
- MediaPipe
- NumPy

## License
MIT 