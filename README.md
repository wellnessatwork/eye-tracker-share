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
   git clone https://github.com/wellnessatwork/eye-tracker-share
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

## Build a Standalone Executable

You can build a standalone binary (no Python installation required) using the provided `build_standalone.sh` script. This script uses [PyInstaller](https://www.pyinstaller.org/) and ensures the necessary MediaPipe model files are included.

### How to use:
1. Make sure you have `pyinstaller` installed:
   ```bash
   pip install pyinstaller
   ```
2. Run the build script:
   ```bash
   bash build_standalone.sh
   ```
3. The standalone executable will be created in the `dist/` directory. You can run it directly:
   ```bash
   ./dist/eye_blink_counter_json
   ```

> **Note:** The script is set up for a file named `eye_blink_counter_json.py`. If your main script is named differently, adjust the script or rename your file accordingly.

## Requirements
- Python 3.7+
- OpenCV
- MediaPipe
- NumPy

## License
MIT 