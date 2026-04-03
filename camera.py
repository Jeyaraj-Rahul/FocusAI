import platform
import threading
import time
from collections import deque

import cv2
import mediapipe as mp

try:
    # Most MediaPipe builds expose Face Mesh from the top-level `solutions` package.
    MP_FACE_MESH = mp.solutions.face_mesh
except AttributeError:
    try:
        # Some installs expose the same module only from `mediapipe.python.solutions`.
        from mediapipe.python.solutions import face_mesh as MP_FACE_MESH
    except Exception:
        MP_FACE_MESH = None


class FocusMonitor:
    """Track focus using MediaPipe face mesh, gaze direction, and eye closure."""

    def __init__(self):
        # Prefer MediaPipe for richer tracking, but fall back to OpenCV face
        # detection so the app can still run if Face Mesh is unavailable.
        self.mp_face_mesh = MP_FACE_MESH
        self.using_mediapipe = self.mp_face_mesh is not None
        self.face_mesh = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        if self.using_mediapipe:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )

        # Re-entrant lock avoids deadlocks when status helpers call each other.
        self.lock = threading.RLock()
        self.camera = None
        self.current_frame = None

        self.last_face_seen_time = time.time()
        self.last_activity_at = time.time()
        self.last_look_at_screen_time = time.time()
        self.looking_away_started_at = None
        self.eyes_closed_started_at = None

        self.tab_hidden = False
        self.tab_switch_count = 0
        self.last_tab_switch_count = 0
        self.recent_tab_switches = deque()

        self.state = "Deep Focus"
        self.focus_score = 80
        self.current_score = 80.0
        self.message = "Face detected and focus is steady."
        self.current_issue = "none"

        self.face_detected = False
        self.looking_away = False
        self.eyes_closed = False
        self.last_error = ""
        self.startup_warning = ""

        self.failed_reads = 0
        self.last_valid_frame_time = time.time()
        self.camera_fail_threshold_seconds = 3

        # Recover slowly, but drop faster when distraction signals are present.
        self.score_step_up = 0.6
        self.score_step_down = 3.0
        self.score_update_interval = 0.5
        self.last_score_update_time = time.time()
        self.look_away_threshold_seconds = 4
        self.eyes_closed_threshold_seconds = 3
        self.look_away_penalty = 1.5
        self.eyes_closed_penalty = 3.0
        self.tab_switch_penalty = 0.6

        self.loop_iteration = 0
        self.last_loop_log_at = 0
        self.last_debug_print_at = 0

        # Session tracking stays in memory for the current app run only.
        self.session_started_at = time.time()
        self.last_state_changed_at = self.session_started_at
        self.time_in_states = {
            "Deep Focus": 0.0,
            "Mild Distraction": 0.0,
            "High Distraction": 0.0,
            "Fatigue": 0.0,
        }
        self.high_distraction_count = 0
        self.issue_counts = {
            "tab switching": 0,
            "no face": 0,
            "idle": 0,
        }

        if not self.using_mediapipe:
            self.startup_warning = (
                "MediaPipe Face Mesh is unavailable. Using basic OpenCV face detection."
            )
            self.last_error = self.startup_warning

        self.camera = self._open_camera()
        self.worker = threading.Thread(target=self._update_loop, daemon=True)
        self.worker.start()

    def _open_camera(self):
        """Open the webcam with backend fallback for better Windows compatibility."""
        backends = [cv2.CAP_ANY]
        if platform.system() == "Windows":
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]

        for backend in backends:
            camera = cv2.VideoCapture(0, backend)
            if camera.isOpened():
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return camera
            camera.release()

        return cv2.VideoCapture()

    def _restart_camera(self):
        """Try to recover the webcam if frame reads keep failing."""
        if self.camera is not None and self.camera.isOpened():
            self.camera.release()

        time.sleep(0.3)
        self.camera = self._open_camera()
        self.failed_reads = 0

    def _update_loop(self):
        """Continuously read webcam frames and update focus signals in the background."""
        while True:
            try:
                now = time.time()
                self.loop_iteration += 1

                if now - self.last_loop_log_at >= 5:
                    print(f"[FocusAI Camera Loop] running iteration={self.loop_iteration}")
                    self.last_loop_log_at = now

                if self.camera is None or not self.camera.isOpened():
                    with self.lock:
                        self.last_error = (
                            "Unable to access webcam. Close other camera apps and check permissions."
                        )
                    self._restart_camera()
                    time.sleep(1)
                    continue

                success, frame = self.camera.read()
                if not success:
                    self.failed_reads += 1
                    seconds_since_valid_frame = time.time() - self.last_valid_frame_time
                    print("Camera fail count:", self.failed_reads)

                    with self.lock:
                        if seconds_since_valid_frame < self.camera_fail_threshold_seconds:
                            self.last_error = "Temporary camera read issue. Keeping last known state."
                        else:
                            self.last_error = "Camera has failed for several seconds. Trying to reconnect."

                    if (
                        self.failed_reads >= 5
                        and seconds_since_valid_frame >= self.camera_fail_threshold_seconds
                    ):
                        self._restart_camera()
                    time.sleep(0.2)
                    continue

                self.failed_reads = 0
                self.last_valid_frame_time = time.time()

                processed_frame, detection = self._detect_face_and_eyes(frame)
                self._update_focus_state(detection)

                with self.lock:
                    self.current_frame = processed_frame
                    self.face_detected = detection["face_detected"]
                    self.looking_away = detection["looking_away"]
                    self.eyes_closed = detection["eyes_closed"]
                    self.last_error = self.startup_warning

                time.sleep(0.03)
            except Exception as error:
                with self.lock:
                    self.last_error = f"Camera loop error: {error}"
                print(f"[FocusAI Camera Loop Error] {error}")
                self._restart_camera()
                time.sleep(0.5)

    def _to_pixel(self, landmark, width, height):
        """Convert a normalized MediaPipe landmark into image coordinates."""
        return int(landmark.x * width), int(landmark.y * height)

    def _distance(self, point_a, point_b):
        """Return Euclidean distance between two 2D points."""
        return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5

    def _calculate_eye_aspect_ratio(self, landmarks, eye_points, width, height):
        """Compute a simple eye aspect ratio to estimate whether the eye is closed."""
        left_corner = self._to_pixel(landmarks[eye_points[0]], width, height)
        right_corner = self._to_pixel(landmarks[eye_points[1]], width, height)
        top_upper = self._to_pixel(landmarks[eye_points[2]], width, height)
        top_lower = self._to_pixel(landmarks[eye_points[3]], width, height)
        bottom_upper = self._to_pixel(landmarks[eye_points[4]], width, height)
        bottom_lower = self._to_pixel(landmarks[eye_points[5]], width, height)

        vertical_1 = self._distance(top_upper, bottom_upper)
        vertical_2 = self._distance(top_lower, bottom_lower)
        horizontal = max(1.0, self._distance(left_corner, right_corner))
        return (vertical_1 + vertical_2) / (2.0 * horizontal)

    def _detect_face_and_eyes(self, frame):
        """Detect the face, estimate gaze direction, and detect closed eyes."""
        if not self.using_mediapipe or self.face_mesh is None:
            return self._detect_face_with_opencv(frame)

        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        detection = {
            "face_detected": False,
            "looking_away": False,
            "eyes_closed": False,
        }

        if not results.multi_face_landmarks:
            cv2.putText(
                frame,
                "No face detected",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (72, 99, 255),
                2,
            )
            return frame, detection

        face_landmarks = results.multi_face_landmarks[0].landmark
        detection["face_detected"] = True

        xs = [landmark.x for landmark in face_landmarks]
        ys = [landmark.y for landmark in face_landmarks]
        x1 = max(0, int(min(xs) * width))
        y1 = max(0, int(min(ys) * height))
        x2 = min(width, int(max(xs) * width))
        y2 = min(height, int(max(ys) * height))

        # Use nose position inside the face width as a simple "looking away" estimate.
        left_face = face_landmarks[234]
        right_face = face_landmarks[454]
        nose_tip = face_landmarks[1]
        face_width = max(0.001, right_face.x - left_face.x)
        horizontal_ratio = (nose_tip.x - left_face.x) / face_width
        # Use a wider center zone so normal head movement is still treated as on-screen.
        detection["looking_away"] = horizontal_ratio < 0.25 or horizontal_ratio > 0.75

        left_eye_points = [33, 133, 160, 158, 153, 144]
        right_eye_points = [362, 263, 387, 385, 380, 373]
        left_ear = self._calculate_eye_aspect_ratio(face_landmarks, left_eye_points, width, height)
        right_ear = self._calculate_eye_aspect_ratio(face_landmarks, right_eye_points, width, height)
        average_ear = (left_ear + right_ear) / 2.0
        detection["eyes_closed"] = average_ear < 0.20

        box_color = (54, 179, 126)
        if detection["looking_away"]:
            box_color = (0, 215, 255)
        if detection["eyes_closed"]:
            box_color = (72, 99, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        cv2.putText(
            frame,
            "Face detected",
            (x1, max(y1 - 10, 30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            box_color,
            2,
        )

        if detection["looking_away"]:
            cv2.putText(
                frame,
                "Looking away",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 215, 255),
                2,
            )

        if detection["eyes_closed"]:
            cv2.putText(
                frame,
                "Eyes closed",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (72, 99, 255),
                2,
            )

        return frame, detection

    def _detect_face_with_opencv(self, frame):
        """Fallback face detector used when MediaPipe is unavailable."""
        detection = {
            "face_detected": False,
            "looking_away": False,
            "eyes_closed": False,
        }

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80),
        )

        if len(faces) == 0:
            cv2.putText(
                frame,
                "No face detected (OpenCV fallback)",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (72, 99, 255),
                2,
            )
            return frame, detection

        x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
        detection["face_detected"] = True

        cv2.rectangle(frame, (x, y), (x + w, y + h), (54, 179, 126), 2)
        cv2.putText(
            frame,
            "Face detected (OpenCV fallback)",
            (x, max(y - 10, 30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (54, 179, 126),
            2,
        )
        return frame, detection

    def _update_focus_state(self, detection):
        """Use MediaPipe face mesh signals to determine focus or distraction."""
        now = time.time()
        with self.lock:
            recent_switch_count = self._get_recent_switch_count(now)

        face_detected = detection["face_detected"]
        looking_away = detection["looking_away"] if self.using_mediapipe else False
        eyes_closed = detection["eyes_closed"] if self.using_mediapipe else False

        if face_detected:
            self.last_face_seen_time = now

        # Track how long the user has been looking away.
        if face_detected and not looking_away:
            self.last_look_at_screen_time = now
            self.looking_away_started_at = None
        elif face_detected and self.looking_away_started_at is None:
            self.looking_away_started_at = now

        looking_away_seconds = max(0, now - self.last_look_at_screen_time)
        looking_away_too_long = (
            self.using_mediapipe
            and looking_away_seconds > self.look_away_threshold_seconds
        )

        # Track how long the eyes have stayed closed.
        if eyes_closed:
            if self.eyes_closed_started_at is None:
                self.eyes_closed_started_at = now
        else:
            self.eyes_closed_started_at = None

        eyes_closed_seconds = 0
        if self.eyes_closed_started_at is not None:
            eyes_closed_seconds = now - self.eyes_closed_started_at
        eyes_closed_too_long = (
            self.using_mediapipe
            and eyes_closed_seconds > self.eyes_closed_threshold_seconds
        )

        face_missing_seconds = max(0, now - self.last_face_seen_time)
        previous_state = self.state
        previous_score = self.current_score

        # Update the score on a fixed interval so the changes stay smooth.
        if now - self.last_score_update_time >= self.score_update_interval:
            if face_detected and not looking_away_too_long and not eyes_closed_too_long:
                # Recover more slowly near the top so the score does not stay pinned at 100.
                if self.current_score < 70:
                    self.current_score += self.score_step_up
                elif self.current_score < 90:
                    self.current_score += self.score_step_up * 0.7
                else:
                    self.current_score += self.score_step_up * 0.25
            else:
                self.current_score -= self.score_step_down

            if self.tab_hidden:
                # Actively being away from the page should hurt more than old switch history.
                self.current_score -= self.tab_switch_penalty
            elif recent_switch_count >= 6:
                self.current_score -= self.tab_switch_penalty * 0.5
            elif recent_switch_count >= 3:
                self.current_score -= self.tab_switch_penalty * 0.2

            if looking_away_too_long:
                self.current_score -= self.look_away_penalty
            if eyes_closed_too_long:
                self.current_score -= self.eyes_closed_penalty

            self.last_score_update_time = now

        self.current_score = max(0.0, min(100.0, self.current_score))
        self.focus_score = int(round(self.current_score))

        if self.current_score >= 80:
            next_state = "Deep Focus"
            next_message = "Face detected and focus is steady."
            next_issue = "none"
        elif self.current_score >= 50:
            next_state = "Mild Distraction"
            next_message = "Focus is slipping a little. Stay on task."
            next_issue = "tab switching" if recent_switch_count > 0 else "none"
        else:
            next_state = "High Distraction"
            if not face_detected:
                next_message = "Face not detected. Please return to the frame."
                next_issue = "no face"
            elif eyes_closed_too_long:
                next_message = "Eyes closed for too long. You may be drowsy."
                next_issue = "idle"
            elif not self.using_mediapipe:
                next_message = "Focus score is low. Stay on the task and remain visible."
                next_issue = "tab switching" if recent_switch_count > 0 else "none"
            else:
                next_message = "Looking away from the screen too often."
                next_issue = "idle"

        self._record_state_time(now)
        self.state = next_state
        self.message = next_message
        self.current_issue = next_issue

        if self.state == "High Distraction" and previous_state != "High Distraction":
            self.high_distraction_count += 1
            if self.current_issue in self.issue_counts:
                self.issue_counts[self.current_issue] += 1
        elif self.state == "Mild Distraction" and previous_state != "Mild Distraction":
            self.issue_counts["tab switching"] += 1

        if now - self.last_debug_print_at >= 1:
            print(
                "[FocusAI Debug]",
                f"score={self.focus_score}",
                f"face_detected={face_detected}",
                f"looking_away={looking_away}",
                f"eyes_closed={eyes_closed}",
                f"using_mediapipe={self.using_mediapipe}",
                f"previous_score={previous_score}",
                f"tab_switch_count={recent_switch_count}",
                f"state={self.state}",
                f"looking_away_seconds={looking_away_seconds:.1f}",
                f"eyes_closed_seconds={eyes_closed_seconds:.1f}",
            )
            self.last_debug_print_at = now

    def update_tab_hidden(self, is_hidden, tab_switch_count=None):
        """Store browser tab visibility and the latest switch count."""
        with self.lock:
            self.tab_hidden = is_hidden
            if tab_switch_count is not None:
                if tab_switch_count > self.last_tab_switch_count:
                    increase = tab_switch_count - self.last_tab_switch_count
                    now = time.time()
                    for _ in range(increase):
                        self.recent_tab_switches.append(now)
                self.tab_switch_count = tab_switch_count
                self.last_tab_switch_count = tab_switch_count

    def update_activity(self):
        """Record that the user interacted with the page recently."""
        with self.lock:
            self.last_activity_at = time.time()

    def _get_recent_switch_count(self, now=None):
        """Count tab switches that happened in the last 60 seconds."""
        if now is None:
            now = time.time()

        while self.recent_tab_switches and now - self.recent_tab_switches[0] > 60:
            self.recent_tab_switches.popleft()

        return len(self.recent_tab_switches)

    def _record_state_time(self, now):
        """Add elapsed seconds to the currently active state."""
        elapsed = max(0, now - self.last_state_changed_at)
        if self.state in self.time_in_states:
            self.time_in_states[self.state] += elapsed
        self.last_state_changed_at = now

    def _format_duration(self, seconds):
        """Convert raw seconds into a simple HH:MM:SS string."""
        total_seconds = int(max(0, seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_session_summary(self):
        """Return a simple in-memory session summary."""
        now = time.time()
        with self.lock:
            state_totals = self.time_in_states.copy()
            if self.state in state_totals:
                state_totals[self.state] += max(0, now - self.last_state_changed_at)

            total_time = max(0, now - self.session_started_at)
            deep_focus_time = state_totals["Deep Focus"]
            focus_percentage = (deep_focus_time / total_time * 100) if total_time > 0 else 0

            main_issue = max(self.issue_counts, key=self.issue_counts.get)
            if self.issue_counts[main_issue] == 0:
                main_issue = "none"

            return {
                "total_time": self._format_duration(total_time),
                "focus_percentage": f"{focus_percentage:.1f}%",
                "deep_focus_time": self._format_duration(deep_focus_time),
                "mild_distraction_time": self._format_duration(
                    state_totals["Mild Distraction"]
                ),
                "high_distraction_time": self._format_duration(
                    state_totals["High Distraction"]
                ),
                "fatigue_time": self._format_duration(state_totals["Fatigue"]),
                "distraction_count": str(self.high_distraction_count),
                "main_issue": main_issue,
            }

    def get_face_detected_status(self):
        """Return the simple backend payload for the dashboard."""
        return self.get_face_detected_status_with_site()

    def _build_status_payload(self, site_name=None, site_category="Neutral"):
        """Build the public status payload, including website-based score penalties."""
        with self.lock:
            score = self.focus_score
            base_message = self.message
            looking_away = self.looking_away
            eyes_closed = self.eyes_closed

        if site_category == "Distracting":
            score = max(0, score - 30)
        elif site_category == "Productive":
            score = min(100, score + 2)

        if score >= 80:
            state = "Deep Focus"
        elif score >= 50:
            state = "Mild Distraction"
        else:
            state = "High Distraction"

        if self.using_mediapipe and eyes_closed:
            message = "Eyes appear closed. Stay alert."
        elif self.using_mediapipe and looking_away:
            message = "Looking away from the screen."
        elif site_category == "Distracting" and site_name:
            message = f"Distracting site detected: {site_name}. Focus score reduced."
        elif site_category == "Productive" and site_name:
            message = f"Productive site detected: {site_name}. Keep going."
        else:
            message = base_message

        return {
            "state": state,
            "score": score,
            "message": message,
            "active_site": site_name,
            "active_site_category": site_category,
        }

    def get_face_detected_status_with_site(self, site_name=None, site_category="Neutral"):
        """Return the lightweight status payload used by the dashboard."""
        return self._build_status_payload(site_name, site_category)

    def get_status(self):
        """Return a serializable snapshot for the frontend."""
        return self.get_status_with_site()

    def get_status_with_site(self, site_name=None, site_category="Neutral"):
        """Return a serializable snapshot for the frontend."""
        now = time.time()
        with self.lock:
            face_missing_seconds = max(0, now - self.last_face_seen_time)
            idle_seconds = max(0, now - self.last_activity_at)
            recent_switch_count = self._get_recent_switch_count(now)
            looking_away_seconds = max(0, now - self.last_look_at_screen_time)
            eyes_closed_seconds = 0
            if self.eyes_closed_started_at is not None:
                eyes_closed_seconds = now - self.eyes_closed_started_at

            payload = self._build_status_payload(site_name, site_category)
            payload.update(
                {
                    "face_detected": self.face_detected,
                    "looking_away": self.looking_away,
                    "eyes_closed": self.eyes_closed,
                    "tab_hidden": self.tab_hidden,
                    "tab_switch_count": self.tab_switch_count,
                    "recent_tab_switch_count": recent_switch_count,
                    "seconds_without_face": round(face_missing_seconds, 1),
                    "idle_seconds": round(idle_seconds, 1),
                    "looking_away_seconds": round(looking_away_seconds, 1),
                    "eyes_closed_seconds": round(eyes_closed_seconds, 1),
                    "last_error": self.last_error,
                }
            )
            return payload

    def generate_frames(self):
        """Yield JPEG frames continuously for Flask streaming."""
        while True:
            try:
                with self.lock:
                    frame = None if self.current_frame is None else self.current_frame.copy()

                if frame is None:
                    time.sleep(0.1)
                    continue

                success, buffer = cv2.imencode(".jpg", frame)
                if not success:
                    time.sleep(0.05)
                    continue

                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            except Exception as error:
                print(f"[FocusAI Frame Stream Error] {error}")
                time.sleep(0.2)

    def __del__(self):
        """Release resources when the app shuts down."""
        if hasattr(self, "camera") and self.camera is not None and self.camera.isOpened():
            self.camera.release()
        if hasattr(self, "face_mesh") and self.face_mesh is not None:
            self.face_mesh.close()
