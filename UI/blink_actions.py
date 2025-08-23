"""Blink counter UI helpers moved out of the main window.
This module attaches helper callables to a window instance so the UI can
call or connect to them as if they were methods on the window.

It intentionally keeps the same attribute names used in the window code:
- toggle_blink_counter
- update_blink_count
- blink_counter_stopped

These are attached via attach_blink_actions(window).
"""
import threading
from typing import Any
import time
import datetime

from APIs.eye_blink_counter import count_blinks


def attach_blink_actions(window: Any) -> None:
    """Attach blink-related callables to the provided window instance.

    The attached callables match the original method names used in the
    `LaptopDashboard` class so existing connections (signals/slots) keep working.
    """
    def update_blink_count(count: int) -> None:
        # update label text
        try:
            window.blink_label.setText(f"Blinks: {count}")
        except Exception:
            # be defensive if UI not ready
            pass

        # If a database and a current_user_id are present on the window, insert a blink event.
        try:
            db = getattr(window, 'db', None)
            user_id = getattr(window, 'current_user_id', None)
            if db is not None and user_id is not None:
                ts = datetime.datetime.utcnow().isoformat()
                epoch_ms = int(time.time() * 1000)
                # Insert a blink event; use event_type 'blink_count' and no duration by default
                try:
                    db.insert_blink_event(user_id=user_id, session_id=None, event_ts=ts, event_epoch_ms=epoch_ms,
                                           duration_ms=None, event_type='blink_count', ear=None,
                                           source=getattr(window, 'blink_source', None), metadata=None)
                except Exception:
                    # don't let DB errors break the UI
                    pass
        except Exception:
            pass

    def blink_counter_stopped() -> None:
        window.blink_worker = None
        window.blink_thread = None
        try:
            window.blink_btn.setText("Start Eye Blink Counter")
        except Exception:
            pass

    def toggle_blink_counter() -> None:
        # start/stop a worker provided by APIs.eye_blink_counter
        if getattr(window, "blink_worker", None) is None:
            # count_blinks() is expected to return a worker-like object with
            # signals `blink_count_updated` and `finished`, and methods `run` and `stop`.
            window.blink_worker = count_blinks()
            # Connect signals if the worker provides them
            try:
                window.blink_worker.blink_count_updated.connect(window.update_blink_count)
            except Exception:
                pass
            try:
                window.blink_worker.finished.connect(window.blink_counter_stopped)
            except Exception:
                pass
            # Start worker in a background thread if it exposes a run() method
            if hasattr(window.blink_worker, "run"):
                window.blink_thread = threading.Thread(target=window.blink_worker.run, daemon=True)
                window.blink_thread.start()
            # update button text
            try:
                window.blink_btn.setText("Stop Eye Blink Counter")
            except Exception:
                pass
        else:
            # Stop the worker if possible
            try:
                window.blink_worker.stop()
            except Exception:
                pass
            try:
                window.blink_btn.setText("Start Eye Blink Counter")
            except Exception:
                pass

    # Attach to window
    window.update_blink_count = update_blink_count
    window.blink_counter_stopped = blink_counter_stopped
    window.toggle_blink_counter = toggle_blink_counter
