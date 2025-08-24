import time
import json
from typing import List, Tuple, Optional, Any

import cv2
import mediapipe as mp
import numpy as np

# Eye landmark indices for left and right eyes (MediaPipe Face Mesh)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

mp_face_mesh = mp.solutions.face_mesh


# --- Utilities -------------------------------------------------------------
def euclidean_dist(pt1: Tuple[int, int], pt2: Tuple[int, int]) -> float:
    return float(np.linalg.norm(np.array(pt1) - np.array(pt2)))


def eye_aspect_ratio(eye_landmarks: List[Tuple[int, int]]) -> float:
    """Compute eye aspect ratio (EAR) for a list of 6 eye landmark (x,y) points."""
    if len(eye_landmarks) < 6:
        raise ValueError("eye_landmarks must contain 6 points")
    A = euclidean_dist(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_dist(eye_landmarks[2], eye_landmarks[4])
    C = euclidean_dist(eye_landmarks[0], eye_landmarks[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)


def landmarks_to_eye_points(landmarks: Any, indices: List[int], frame_width: int, frame_height: int):
    return [
        (int(landmarks[i].x * frame_width), int(landmarks[i].y * frame_height))
        for i in indices
    ]


# --- PyQt compatibility (signals/worker) -----------------------------------
try:
    from PyQt5.QtCore import QObject, pyqtSignal
except Exception:
    # fallback shims so module can be imported in non-GUI environments
    class QObject:
        def __init__(self, *args, **kwargs):
            pass

    def pyqtSignal(*_args, **_kwargs):  # type: ignore
        return None


class BlinkCounterWorker(QObject):
    # class-level signals (will be None if pyqtSignal is not available)
    blink_count_updated = pyqtSignal(int) if callable(pyqtSignal) else None
    frame_ready = pyqtSignal(object) if callable(pyqtSignal) else None  # emits numpy BGR frame
    finished = pyqtSignal() if callable(pyqtSignal) else None

    def __init__(self,
                 cam_index: int = 0,
                 ear_threshold: float = 0.21,
                 consec_frames: int = 2,
                 window_name: str = "Eye Blink Counter"):
        super().__init__()
        self.cam_index = cam_index
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        self.window_name = window_name
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        """Main loop: read frames, detect face landmarks, compute EAR and count blinks.
        Emits blink_count_updated and frame_ready (if available). Emits finished on exit.
        """
        cap = cv2.VideoCapture(self.cam_index)
        blink_count = 0
        frame_counter = 0

        self._running = True
        try:
            with mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            ) as face_mesh:
                while self._running:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    h, w = frame.shape[:2]
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(rgb)

                    ear = None
                    left_eye = []
                    right_eye = []
                    if results and getattr(results, "multi_face_landmarks", None):
                        for face_landmarks in results.multi_face_landmarks:
                            try:
                                left_eye = landmarks_to_eye_points(face_landmarks.landmark, LEFT_EYE, w, h)
                                right_eye = landmarks_to_eye_points(face_landmarks.landmark, RIGHT_EYE, w, h)
                                left_ear = eye_aspect_ratio(left_eye)
                                right_ear = eye_aspect_ratio(right_eye)
                                ear = (left_ear + right_ear) / 2.0
                            except Exception:
                                ear = None

                            if ear is not None and ear < self.ear_threshold:
                                frame_counter += 1
                            else:
                                if frame_counter >= self.consec_frames:
                                    blink_count += 1
                                    try:
                                        if getattr(self, "blink_count_updated", None) is not None:
                                            self.blink_count_updated.emit(blink_count)  # type: ignore
                                    except Exception:
                                        pass
                                frame_counter = 0

                            # draw markers for debug / visualization
                            try:
                                for pt in (left_eye + right_eye) if ear is not None else []:
                                    cv2.circle(frame, pt, 2, (0, 255, 0), -1)
                            except Exception:
                                pass

                    # emit frame to UI (main thread should convert/display)
                    try:
                        if getattr(self, "frame_ready", None) is not None:
                            self.frame_ready.emit(frame.copy())  # type: ignore
                    except Exception:
                        pass

                    # small sleep to reduce CPU in tight loops
                    time.sleep(0.01)
        finally:
            try:
                cap.release()
            except Exception:
                pass
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            self._running = False
            try:
                if getattr(self, "finished", None) is not None:
                    self.finished.emit()  # type: ignore
            except Exception:
                pass


# --- Factory / public API --------------------------------------------------
def count_blinks(cam_index: int = 0,
                 ear_threshold: float = 0.21,
                 consec_frames: int = 2,
                 window_name: str = "Eye Blink Counter") -> BlinkCounterWorker:
    """Return a BlinkCounterWorker instance configured for the given parameters."""
    return BlinkCounterWorker(cam_index=cam_index,
                              ear_threshold=ear_threshold,
                              consec_frames=consec_frames,
                              window_name=window_name)


# --- CLI fallback for manual testing --------------------------------------
def _run_cli_once(cam_index: int = 0) -> None:
    """Run blink counter in-process and print JSON updates to stdout (for manual testing)."""
    cap = cv2.VideoCapture(cam_index)
    blink_count = 0
    frame_counter = 0
    EAR_THRESH = 0.21
    CONSEC_FRAMES = 2
    window_name = "Eye Blink Counter (CLI)"

    try:
        with mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as face_mesh:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                h, w = frame.shape[:2]
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)

                if results and getattr(results, "multi_face_landmarks", None):
                    for face_landmarks in results.multi_face_landmarks:
                        try:
                            left_eye = landmarks_to_eye_points(face_landmarks.landmark, LEFT_EYE, w, h)
                            right_eye = landmarks_to_eye_points(face_landmarks.landmark, RIGHT_EYE, w, h)
                            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
                        except Exception:
                            ear = None

                        if ear is not None and ear < EAR_THRESH:
                            frame_counter += 1
                        else:
                            if frame_counter >= CONSEC_FRAMES:
                                blink_count += 1
                                print(json.dumps({"blink_count": blink_count}), flush=True)
                            frame_counter = 0

                # show frame if possible
                try:
                    cv2.imshow(window_name, frame)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
                except Exception:
                    pass
    finally:
        try:
            cap.release()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        print(json.dumps({"blink_count": blink_count}), flush=True)


if __name__ == "__main__":
    _run_cli_once()