"""Blink counter UI helpers moved out of the main window.
This module attaches helper callables to a window instance so the UI can
call or connect to them as if they were methods on the window.

It intentionally keeps the same attribute names used in the window code:
- toggle_blink_counter
- update_blink_count
- blink_counter_stopped

These are attached via attach_blink_actions(window).
"""
from typing import Any
import traceback

# Qt imports
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtGui import QImage, QPixmap

# numpy / cv2 for image conversion
import cv2
import numpy as np

# worker factory
try:
    from APIs.eye_blink_counter import count_blinks
except Exception:
    count_blinks = None  # defensive: main will fail earlier if worker missing


def attach_blink_actions(window: Any) -> None:
    """Attach blink-control helpers and UI callbacks to the window instance."""

    def update_preview(frame: np.ndarray) -> None:
        """Receive a BGR numpy frame from the worker and show it in preview_label."""
        try:
            if not hasattr(window, "preview_label") or window.preview_label is None:
                return
            # defensive: ensure frame is a numpy array with 3 channels
            if frame is None:
                return
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            except Exception:
                # if frame already RGB or conversion fails, try to coerce
                rgb = frame
            h, w = rgb.shape[:2]
            ch = 3 if rgb.ndim == 3 else 1
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg).scaled(window.preview_label.size(), Qt.KeepAspectRatio)
            window.preview_label.setPixmap(pix)
        except Exception:
            # swallow exceptions to avoid thread signal errors
            try:
                traceback.print_exc()
            except Exception:
                pass

    def update_blink_count(count: int) -> None:
        try:
            if hasattr(window, "blink_label") and window.blink_label:
                window.blink_label.setText(f"Blinks: {count}")
        except Exception:
            pass

    def blink_counter_stopped() -> None:
        """Called when worker finished or when stop requested."""
        try:
            if hasattr(window, "blink_btn") and window.blink_btn:
                window.blink_btn.setText("Start Eye Blink Counter")
        except Exception:
            pass

        # stop & clean up QThread/worker references
        try:
            th = getattr(window, "blink_thread", None)
            if th is not None:
                try:
                    th.quit()
                    th.wait(1000)
                except Exception:
                    pass
        finally:
            window.blink_worker = None
            window.blink_thread = None

    def toggle_blink_counter() -> None:
        """Start or stop the blink worker in a QThread and connect signals."""
        # If no worker is running -> start
        if getattr(window, "blink_worker", None) is None:
            if count_blinks is None:
                # cannot start worker
                try:
                    if hasattr(window, "output"):
                        window.output.append("Blink worker factory not available (count_blinks).")
                except Exception:
                    pass
                return

            # create worker and thread
            try:
                worker = count_blinks()
            except Exception as e:
                try:
                    if hasattr(window, "output"):
                        window.output.append(f"Failed to create blink worker: {e}")
                except Exception:
                    pass
                return

            thread = QThread()
            # move worker into thread (worker must be a QObject for this to work)
            try:
                worker.moveToThread(thread)
            except Exception:
                # if worker is not QObject, we'll run it in the thread using a wrapper
                pass

            # connect signals if present
            try:
                if getattr(worker, "frame_ready", None) is not None:
                    worker.frame_ready.connect(update_preview)
            except Exception:
                pass
            try:
                if getattr(worker, "blink_count_updated", None) is not None:
                    worker.blink_count_updated.connect(update_blink_count)
            except Exception:
                pass
            try:
                if getattr(worker, "finished", None) is not None:
                    worker.finished.connect(blink_counter_stopped)
            except Exception:
                pass

            # start the worker.run when thread starts
            try:
                thread.started.connect(worker.run)
            except Exception:
                # fallback: start a thread that calls run directly
                def _run_wrapper():
                    try:
                        worker.run()
                    finally:
                        # ensure finished/cleanup executed in main thread via signal if available
                        try:
                            if getattr(worker, "finished", None) is not None:
                                worker.finished.emit()  # type: ignore
                        except Exception:
                            pass

                thread.run = _run_wrapper  # type: ignore

            # store refs and start
            window.blink_worker = worker
            window.blink_thread = thread
            thread.start()

            try:
                if hasattr(window, "blink_btn") and window.blink_btn:
                    window.blink_btn.setText("Stop Eye Blink Counter")
            except Exception:
                pass
        else:
            # stop running worker
            try:
                if getattr(window.blink_worker, "stop", None) is not None:
                    window.blink_worker.stop()
            except Exception:
                pass
            # let finished signal / blink_counter_stopped handle the rest
            try:
                if hasattr(window, "blink_btn") and window.blink_btn:
                    window.blink_btn.setText("Start Eye Blink Counter")
            except Exception:
                pass

    # Attach functions to the window instance for later use
    window.toggle_blink_counter = toggle_blink_counter
    window.update_blink_count = update_blink_count
    window.blink_counter_stopped = blink_counter_stopped
    window.update_preview = update_preview
