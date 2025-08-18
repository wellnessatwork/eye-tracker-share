import sys
import os
# Ensure project root is on sys.path so top-level `APIs` package can be imported when running this file directly.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import threading
import psutil
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt

from UI.blink_actions import attach_blink_actions

from APIs.eye_blink_counter import count_blinks

class LaptopDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laptop Dashboard")
        self.setGeometry(100, 100, 400, 350)
        self.initUI()
        self.blink_worker = None
        self.blink_thread = None

        # Attach blink-related helper functions to this instance
        attach_blink_actions(self)

    def initUI(self):
        layout = QVBoxLayout()
        self.info_label = QLabel(self.get_system_info())
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        # Blink Counter UI
        self.blink_label = QLabel("Blinks: 0")
        self.blink_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.blink_label)
        self.blink_btn = QPushButton("Start Eye Blink Counter")
        self.blink_btn.clicked.connect(self.toggle_blink_counter)
        layout.addWidget(self.blink_btn)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def get_system_info(self):
        uname = psutil.Process().as_dict(attrs=['username'])
        return f"User: {uname['username']}\nPlatform: {sys.platform}\nPython: {sys.version.split()[0]}"

    def toggle_blink_counter(self):
        if self.blink_worker is None:
            self.blink_worker = count_blinks()
            self.blink_worker.blink_count_updated.connect(self.update_blink_count)
            self.blink_worker.finished.connect(self.blink_counter_stopped)
            self.blink_thread = threading.Thread(target=self.blink_worker.run)
            self.blink_thread.start()
            self.blink_btn.setText("Stop Eye Blink Counter")
        else:
            self.blink_worker.stop()
            self.blink_btn.setText("Start Eye Blink Counter")

    def update_blink_count(self, count):
        self.blink_label.setText(f"Blinks: {count}")

    def blink_counter_stopped(self):
        self.blink_worker = None
        self.blink_thread = None
        self.blink_btn.setText("Start Eye Blink Counter")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LaptopDashboard()
    window.show()
    sys.exit(app.exec_())
