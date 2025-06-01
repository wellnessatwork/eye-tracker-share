#!/bin/bash

# Build the standalone binary for eye_blink_counter_json.py with mediapipe model files
pyinstaller --onefile \
  --add-data "$(python -c 'import mediapipe, os; print(os.path.dirname(mediapipe.__file__) + "/modules")'):mediapipe/modules" \
  eye_blink_counter_json.py 