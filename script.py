import cv2
import mediapipe as mp
import numpy as np
import json

# Initialize MediaPipe Face Mesh and drawing utils
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Eye landmark indices for left and right eyes (from MediaPipe Face Mesh)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def euclidean_dist(pt1, pt2):
    return np.linalg.norm(np.array(pt1) - np.array(pt2))

def eye_aspect_ratio(eye_landmarks):
    # Compute the eye aspect ratio (EAR)
    A = euclidean_dist(eye_landmarks[1], eye_landmarks[5])
    B = euclidean_dist(eye_landmarks[2], eye_landmarks[4])
    C = euclidean_dist(eye_landmarks[0], eye_landmarks[3])
    ear = (A + B) / (2.0 * C)
    return ear

def main():
    cap = cv2.VideoCapture(0)
    blink_count = 0
    blink_state = False
    EAR_THRESH = 0.21  # Threshold for blink detection
    CONSEC_FRAMES = 2  # Frames required to confirm a blink
    frame_counter = 0

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
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)

                if results.multi_face_landmarks:
                    h, w, _ = frame.shape
                    for face_landmarks in results.multi_face_landmarks:
                        # Get eye landmarks
                        left_eye = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in LEFT_EYE]
                        right_eye = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in RIGHT_EYE]
                        # Draw eyes
                        for pt in left_eye + right_eye:
                            cv2.circle(frame, pt, 2, (0,255,0), -1)
                        # Calculate EAR
                        left_ear = eye_aspect_ratio(left_eye)
                        right_ear = eye_aspect_ratio(right_eye)
                        ear = (left_ear + right_ear) / 2.0
                        # Blink detection logic
                        if ear < EAR_THRESH:
                            frame_counter += 1
                        else:
                            if frame_counter >= CONSEC_FRAMES:
                                blink_count += 1
                            frame_counter = 0
                        # Display blink count
                        cv2.putText(frame, f'Blinks: {blink_count}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                # Print blink count as JSON on every frame
                print(json.dumps({"blink_count": blink_count}), flush=True)
                cv2.imshow('Eye Blink Counter', frame)
                if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
                    break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main() 