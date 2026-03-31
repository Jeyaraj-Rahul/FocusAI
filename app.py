import os

from flask import Flask, Response, jsonify, render_template, request

from camera import FocusMonitor
from usage_tracker import WebsiteUsageTracker


app = Flask(__name__)

# Create the monitor only in the active Flask process.
monitor = None
usage_tracker = None


def get_monitor():
    """Create the camera monitor lazily so the webcam is opened only once."""
    global monitor
    if monitor is None:
        monitor = FocusMonitor()
    return monitor


def get_usage_tracker():
    """Create the website usage tracker lazily so it runs once per app."""
    global usage_tracker
    if usage_tracker is None:
        usage_tracker = WebsiteUsageTracker()
    return usage_tracker


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    """Stream webcam frames to the browser as an MJPEG feed."""
    return Response(
        get_monitor().generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/api/status")
def get_status():
    """Return the latest focus data for the dashboard."""
    site_info = get_usage_tracker().get_current_site_info()
    return jsonify(
        get_monitor().get_status_with_site(
            site_name=site_info["site"],
            site_category=site_info["category"],
        )
    )


@app.route("/status")
def face_status():
    """Return whether a face is currently detected."""
    site_info = get_usage_tracker().get_current_site_info()
    return jsonify(
        get_monitor().get_face_detected_status_with_site(
            site_name=site_info["site"],
            site_category=site_info["category"],
        )
    )


@app.route("/api/tab-activity", methods=["POST"])
def update_tab_activity():
    """Receive browser tab visibility updates from the frontend."""
    payload = request.get_json(silent=True) or {}
    is_hidden = bool(payload.get("is_hidden", False))
    tab_switch_count = int(payload.get("tab_switch_count", 0))
    monitor = get_monitor()
    monitor.update_tab_hidden(is_hidden, tab_switch_count)
    if not is_hidden:
        monitor.update_activity()

    return jsonify(
        {
            "success": True,
            "tab_hidden": is_hidden,
            "tab_switch_count": tab_switch_count,
        }
    )


@app.route("/api/activity", methods=["POST"])
def update_activity():
    """Receive lightweight user activity pings from the frontend."""
    get_monitor().update_activity()
    return jsonify({"success": True})


@app.route("/api/session-summary")
def session_summary():
    """Return the current in-memory session analytics."""
    return jsonify(get_monitor().get_session_summary())


@app.route("/usage")
def usage_summary():
    """Return simple in-memory website usage tracking data."""
    return jsonify(get_usage_tracker().get_usage_summary())


if __name__ == "__main__":
    # Start background workers before serving requests so the APIs stay fast.
    get_monitor()
    get_usage_tracker()

    # debug=True is useful for beginners while building locally.
    app.run(debug=True, use_reloader=False)
