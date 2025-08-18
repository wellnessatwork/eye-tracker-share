import sys
import os
# Ensure project root is on sys.path so top-level `APIs` package can be imported when running this file directly.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from APIs.database import DatabaseHandler
import APIs.system_monitor as sm
from UI.db_actions import add_sample_users,update_user_prompt,delete_user_prompt, show_users
from UI.blink_actions import attach_blink_actions

import threading
import psutil

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt SQLite + System Monitor + Blink Counter")
        self.resize(600, 500)

        self.db = DatabaseHandler()
        self.blink_worker = None
        self.blink_thread = None

        # Build UI
        self.init_ui()

        # Attach blink-related helper functions to this instance
        attach_blink_actions(self)

        # Timer to update system stats every 1s
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system_stats)
        self.timer.start(1000)

    def init_ui(self):
        container = QWidget()
        layout = QVBoxLayout()

        # System / user info (from laptopdashboard)
        self.info_label = QLabel(self.get_system_info())
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # Output for DB actions
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # DB action buttons
        btn_add = QPushButton("Add Users")
        btn_add.clicked.connect(lambda: add_sample_users(self.db, self.output))
        btn_show = QPushButton("Show Users")
        btn_show.clicked.connect(lambda: show_users(self.db, self.output))
        btn_del = QPushButton("Delete Users")
        btn_del.clicked.connect(lambda: delete_user_prompt(self.db, self.output))
        btn_update = QPushButton("Update Users")
        btn_update.clicked.connect(lambda: update_user_prompt(self.db, self.output))
        # Place the DB action buttons on the same row
        button_row = QHBoxLayout()
        button_row.addWidget(btn_add)
        button_row.addWidget(btn_show)
        button_row.addWidget(btn_del)
        button_row.addWidget(btn_update)
        layout.addLayout(button_row)

        # Blink Counter UI (from laptopdashboard)
        self.blink_label = QLabel("Blinks: 0")
        self.blink_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.blink_label)

        self.blink_btn = QPushButton("Start Eye Blink Counter")
        # Defer lookup of the toggle function (it is attached after init via attach_blink_actions)
        self.blink_btn.clicked.connect(lambda: getattr(self, 'toggle_blink_counter', lambda: None)())
        layout.addWidget(self.blink_btn)

        # System metrics
        self.cpu_label = QLabel("CPU Usage: -- %")
        self.mem_label = QLabel("Memory Usage: -- MB")
        self.power_label = QLabel("Power: --")
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.mem_label)
        layout.addWidget(self.power_label)

        container.setLayout(layout)
        self.setCentralWidget(container)

    def get_system_info(self):
        try:
            uname = psutil.Process().as_dict(attrs=['username'])
            user = uname.get('username') if isinstance(uname, dict) else str(uname)
        except Exception:
            user = 'unknown'
        return f"User: {user}\nPlatform: {sys.platform}\nPython: {sys.version.split()[0]}"

    # Note: toggle_blink_counter, update_blink_count, blink_counter_stopped will be attached
    # to the instance by UI/blink_actions.attach_blink_actions(self) in __init__.

    def update_system_stats(self):
        try:
            cpu = sm.get_cpu_usage()
            mem = sm.get_memory_usage()
            power = sm.get_power_usage()
            self.cpu_label.setText(f"CPU Usage: {cpu:.1f} %")
            self.mem_label.setText(f"Memory Usage: {mem:.1f} MB")
            self.power_label.setText(f"Power: {power}")
        except Exception:
            # keep previous values on failure
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
