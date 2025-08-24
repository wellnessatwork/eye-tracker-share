import sys
import os
# Ensure project root is on sys.path so top-level `APIs` package can be imported when running this file directly.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit
from PyQt5.QtWidgets import QHBoxLayout, QTabWidget, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from APIs.database import DatabaseHandler
import APIs.system_monitor as sm
from UI.db_actions import add_sample_users, update_user_prompt, delete_user_prompt, show_users, process_output_commands
from UI.blink_actions import attach_blink_actions

import threading
import psutil

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaW Tracker")
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
        # Create tab widget
        tabs = QTabWidget()

        # --- Tracker tab (system info, blink counter, system metrics) ---
        tracker_widget = QWidget()
        tracker_layout = QVBoxLayout()

        self.info_label = QLabel(self.get_system_info())
        self.info_label.setAlignment(Qt.AlignCenter)
        tracker_layout.addWidget(self.info_label)

        # Blink Counter UI
        self.blink_label = QLabel("Blinks: 0")
        self.blink_label.setAlignment(Qt.AlignCenter)
        tracker_layout.addWidget(self.blink_label)

        # preview area for camera frames
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(320, 240)
        self.preview_label.setStyleSheet("background: #000;")
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setAlignment(Qt.AlignCenter)
        tracker_layout.addWidget(self.preview_label, stretch=1)

        self.blink_btn = QPushButton("Start Eye Blink Counter")
        # Defer lookup of the toggle function (it is attached after init via attach_blink_actions)
        self.blink_btn.clicked.connect(lambda: getattr(self, 'toggle_blink_counter', lambda: None)())
        tracker_layout.addWidget(self.blink_btn)

        # System metrics
        self.cpu_label = QLabel("CPU Usage: -- %")
        self.mem_label = QLabel("Memory Usage: -- MB")
        self.power_label = QLabel("Power: --")
        tracker_layout.addWidget(self.cpu_label)
        tracker_layout.addWidget(self.mem_label)
        tracker_layout.addWidget(self.power_label)

        tracker_widget.setLayout(tracker_layout)

        # --- Admin tab (DB actions) ---
        admin_widget = QWidget()
        admin_layout = QVBoxLayout()

        # Output for DB actions
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        admin_layout.addWidget(self.output)

        # DB action buttons row
        btn_add = QPushButton("Add Users")
        btn_add.clicked.connect(lambda: add_sample_users(self.db, self.output))
        btn_show = QPushButton("Show Users")
        btn_show.clicked.connect(lambda: show_users(self.db, self.output))
        btn_del = QPushButton("Delete Users")
        btn_del.clicked.connect(lambda: delete_user_prompt(self.db, self.output))
        btn_update = QPushButton("Update Users")
        btn_update.clicked.connect(lambda: update_user_prompt(self.db, self.output))
        # new: show blink events button
        btn_show_blinks = QPushButton("Show Blinks")
        btn_show_blinks.clicked.connect(lambda: self.show_blink_events())

        button_row = QHBoxLayout()
        button_row.addWidget(btn_add)
        button_row.addWidget(btn_show)
        button_row.addWidget(btn_del)
        button_row.addWidget(btn_update)
        button_row.addWidget(btn_show_blinks)
        admin_layout.addLayout(button_row)

        # Command processing button (processes commands typed into the output area)
        # Input for single commands (update/delete)
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command, e.g. update:2:Charlie:28  or  delete:3")
        admin_layout.addWidget(self.command_input)

        btn_process = QPushButton("Process Command")

        def _process_single_command():
            cmd = self.command_input.text().strip()
            if not cmd:
                return
            # append into output so the existing processor can find and process it
            self.output.append(cmd)
            process_output_commands(self.db, self.output)
            self.command_input.clear()

        btn_process.clicked.connect(_process_single_command)
        admin_layout.addWidget(btn_process)

        admin_widget.setLayout(admin_layout)

        # Add tabs to the QTabWidget
        tabs.addTab(tracker_widget, "Tracker")
        tabs.addTab(admin_widget, "Admin")

        # Set the tab widget as central
        self.setCentralWidget(tabs)

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

    def show_blink_events(self, user_id: int = None, limit: int = 200) -> None:
        """Query blink_events and write formatted rows to the admin output widget."""
        try:
            rows = self.db.get_blink_events(user_id=user_id, limit=limit)
        except Exception as e:
            self.output.append(f"Error querying blink events: {e}")
            return

        if not rows:
            self.output.append("No blink events found.")
            return

        self.output.append(f"Showing up to {limit} blink events (most recent first):")
        for r in rows:
            # r is: id, user_id, session_id, event_ts, event_epoch_ms, duration_ms, event_type, ear, source, metadata
            event_id, uid, session_id, event_ts, epoch_ms, duration_ms, event_type, ear, source, metadata = r
            parts = [
                f"id={event_id}",
                f"user_id={uid}",
                f"session={session_id or '-'}",
                f"ts={event_ts}",
                f"epoch_ms={epoch_ms}",
                f"duration_ms={duration_ms if duration_ms is not None else '-'}",
                f"type={event_type or '-'}",
                f"ear={ear if ear is not None else '-'}",
                f"src={source or '-'}",
            ]
            if metadata:
                parts.append(f"meta={metadata}")
            self.output.append(" | ".join(parts))
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
