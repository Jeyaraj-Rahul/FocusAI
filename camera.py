import threading
import time
from collections import deque
import platform

import cv2


class FocusMonitor:
    """Track user focus using simple rule-based signals."""

    def __init__(self):
        # Haar cascade is bundled with OpenCV and is good for a beginner-friendly demo.
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        self.lock = threading.Lock()
        self.camera = None
        self.current_frame = None
        # Remember the last time a face was clearly detected.
        self.last_face_seen_time = time.time()
        self.face_missing_started_at = None
        self.last_activity_at = time.time()
        self.tab_hidden = False
        self.tab_switch_count = 0
        self.last_tab_switch_count = 0
        self.recent_tab_switches = deque()
        self.state = "Deep Focus"
        self.focus_score = 80
        self.message = "You are fully focused right now."
        self.face_detected = False
        self.last_error = ""
        self.failed_reads = 0
        self.current_issue = "none"
        self.last_debug_print_at = 0
        self.current_score = 80
        self.score_step_up = 1
        self.score_step_down = 2
        self.score_update_interval = 0.5
        self.last_score_update_time = time.time()
        self.last_valid_frame_time = time.time()
        self.camera_fail_threshold_seconds = 3
        self.loop_iteration = 0
        self.last_loop_log_at = 0

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

        # Open the webcam once during startup using a Windows-friendly backend.
        self.camera = self._open_camera()

        # Start the detection loop in the background.
        self.worker = threading.Thread(target=self._update_loop, daemon=True)
        self.worker.start()

    def _open_camera(self):
        """Open the webcam with backend fallback for better Windows compatibility."""
        backends = []

        if platform.system() == "Windows":
            # DirectShow is often more reliable than MSMF for webcams on Windows.
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
        else:
            backends = [cv2.CAP_ANY]

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
        """Continuously read webcam frames and update focus state."""
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
                        # Ignore short camera glitches and keep the last known state.
                        if seconds_since_valid_frame < self.camera_fail_threshold_seconds:
                            self.last_error = (
                                "Temporary camera read issue. Keeping last known state."
                            )
                        else:
                            self.last_error = (
                                "Camera has failed for several seconds. Trying to reconnect."
                            )

                    # Only restart the camera after repeated failures over time.
                    if (
                        self.failed_reads >= 5
                        and seconds_since_valid_frame >= self.camera_fail_threshold_seconds
                    ):
                        self._restart_camera()
                    time.sleep(0.2)
                    continue

                self.failed_reads = 0
                self.last_valid_frame_time = time.time()

                processed_frame, face_detected = self._detect_face(frame)
                self._update_focus_state(face_detected)

                with self.lock:
                    self.current_frame = processed_frame
                    self.face_detected = face_detected
                    self.last_error = ""

                time.sleep(0.03)
            except Exception as error:
                # Keep the worker alive even if OpenCV throws unexpectedly.
                with self.lock:
                    self.last_error = f"Camera loop error: {error}"
                print(f"[FocusAI Camera Loop Error] {error}")
                self._restart_camera()
                time.sleep(0.5)

    def _detect_face(self, frame):
        """Find faces in the current frame and draw a box around them."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Improve contrast slightly so the Haar cascade works better on
        # dim or uneven webcam lighting.
        gray = cv2.equalizeHist(gray)

        # Run detection on a smaller image to improve speed and stability.
        small_gray = cv2.resize(gray, (0, 0), fx=0.75, fy=0.75)

        faces = self.face_cascade.detectMultiScale(
            small_gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(60, 60),
        )

        scaled_faces = []
        for (x, y, w, h) in faces:
            scaled_faces.append(
                (
                    int(x / 0.75),
                    int(y / 0.75),
                    int(w / 0.75),
                    int(h / 0.75),
                )
            )

        # If multiple faces are found, use the largest one as the main user.
        if scaled_faces:
            scaled_faces.sort(key=lambda box: box[2] * box[3], reverse=True)

        face_detected = len(scaled_faces) > 0
        box_color = (54, 179, 126) if face_detected else (72, 99, 255)

        if face_detected:
            x, y, w, h = scaled_faces[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
            cv2.putText(
                frame,
                "Face detected",
                (x, max(y - 10, 30)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                box_color,
                2,
            )
        else:
            cv2.putText(
                frame,
                "No face detected",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                box_color,
                2,
            )

        return frame, face_detected

    def _update_focus_state(self, face_detected):
        """Use a continuous score that moves every cycle."""
        now = time.time()

        with self.lock:
            recent_switch_count = self._get_recent_switch_count(now)

        if face_detected:
            self.last_face_seen_time = now

        face_missing_seconds = max(0, now - self.last_face_seen_time)
        previous_state = self.state
        previous_score = self.current_score

        # Update the score on a fixed time interval instead of every camera frame.
        # This keeps the behavior stable even if OpenCV reads frames very quickly.
        if now - self.last_score_update_time >= self.score_update_interval:
            if face_detected:
                self.current_score += self.score_step_up
            else:
                self.current_score -= self.score_step_down

            # Small penalty for repeated tab switching.
            if recent_switch_count > 0:
                self.current_score -= min(1, recent_switch_count // 3)

            self.last_score_update_time = now

        # Keep the score inside 0-100.
        self.current_score = max(0, min(100, self.current_score))
        self.focus_score = self.current_score

        # Derive the state from the score.
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
            next_message = "Focus is low right now. Please return your attention."
            next_issue = "no face"

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
                f"previous_score={previous_score}",
                f"tab_switch_count={recent_switch_count}",
                f"state={self.state}",
                f"seconds_without_face={face_missing_seconds:.1f}",
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
            # Include the currently active state up to the moment this summary is requested.
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
        with self.lock:
            return {
                "state": self.state,
                "score": self.focus_score,
                "message": self.message,
            }

    def get_status(self):
        """Return a serializable snapshot for the frontend."""
        now = time.time()
        with self.lock:
            face_missing_seconds = max(0, now - self.last_face_seen_time)
            idle_seconds = max(0, now - self.last_activity_at)
            recent_switch_count = self._get_recent_switch_count(now)
            return {
                "state": self.state,
                "score": self.focus_score,
                "message": self.message,
                "face_detected": self.face_detected,
                "tab_hidden": self.tab_hidden,
                "tab_switch_count": self.tab_switch_count,
                "recent_tab_switch_count": recent_switch_count,
                "seconds_without_face": round(face_missing_seconds, 1),
                "idle_seconds": round(idle_seconds, 1),
                "last_error": self.last_error,
            }

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
        """Release the webcam when the app shuts down."""
        if hasattr(self, "camera") and self.camera is not None and self.camera.isOpened():
            self.camera.release()
