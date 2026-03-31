import ctypes
import os
import platform
import threading
import time
from ctypes import wintypes


BROWSER_PROCESS_NAMES = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}


class WebsiteUsageTracker:
    """Track active browser tab usage in memory using the foreground window title."""

    def __init__(self):
        self.lock = threading.Lock()
        self.time_spent = {}
        self.category = {}
        self.current_site = None
        self.last_tick_at = time.time()
        self.is_windows = platform.system() == "Windows"
        self.loop_iteration = 0
        self.last_loop_log_at = 0

        # Start a lightweight background loop that samples the active browser tab once per second.
        self.worker = threading.Thread(target=self._tracking_loop, daemon=True)
        self.worker.start()

    def _tracking_loop(self):
        """Check the active browser tab every second and add time to the matching site."""
        while True:
            try:
                now = time.time()
                self.loop_iteration += 1

                if now - self.last_loop_log_at >= 5:
                    print(f"[FocusAI Usage Loop] running iteration={self.loop_iteration}")
                    self.last_loop_log_at = now

                active_site = self._get_active_site_name()

                with self.lock:
                    elapsed = max(0, int(now - self.last_tick_at))

                    # Add the elapsed whole seconds to the previously active site.
                    if self.current_site and elapsed > 0:
                        self.time_spent[self.current_site] = (
                            self.time_spent.get(self.current_site, 0) + elapsed
                        )

                    self.current_site = active_site
                    self.last_tick_at = now

                    if active_site and active_site not in self.category:
                        self.category[active_site] = self._classify_site(active_site)

                time.sleep(1)
            except Exception as error:
                print(f"[FocusAI Usage Loop Error] {error}")
                time.sleep(1)

    def _get_active_site_name(self):
        """
        Read the active window title and convert it into a simple site name.

        This is Windows-only. On other systems it returns None.
        """
        if not self.is_windows:
            return None

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if not process_id.value:
            return None

        process_handle = kernel32.OpenProcess(0x1000 | 0x0400, False, process_id.value)
        if not process_handle:
            return None

        try:
            image_path_buffer = ctypes.create_unicode_buffer(260)
            if not psapi.GetModuleFileNameExW(process_handle, None, image_path_buffer, 260):
                return None

            process_name = os.path.basename(image_path_buffer.value).lower()
            if process_name not in BROWSER_PROCESS_NAMES:
                return None

            title_length = user32.GetWindowTextLengthW(hwnd)
            if title_length <= 0:
                return None

            title_buffer = ctypes.create_unicode_buffer(title_length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)
            return self._normalize_site_name(title_buffer.value)
        finally:
            kernel32.CloseHandle(process_handle)

    def _normalize_site_name(self, window_title):
        """Extract a readable site label from a browser tab title."""
        if not window_title:
            return None

        lower_title = window_title.lower()

        # Use explicit site labels for common websites so the output stays clean.
        known_sites = {
            "youtube": "youtube.com",
            "instagram": "instagram.com",
            "leetcode": "leetcode.com",
            "github": "github.com",
            "docs": "docs",
            "documentation": "docs",
        }

        for keyword, site_name in known_sites.items():
            if keyword in lower_title:
                return site_name

        # Browser titles often end with the browser name. Remove that suffix first.
        cleaned_title = window_title
        suffixes = [
            " - Google Chrome",
            " - Microsoft Edge",
            " - Mozilla Firefox",
            " - Brave",
            " - Opera",
        ]

        for suffix in suffixes:
            if cleaned_title.endswith(suffix):
                cleaned_title = cleaned_title[: -len(suffix)]
                break

        # Use the remaining tab title as the key for unknown or neutral sites.
        cleaned_title = cleaned_title.strip()
        return cleaned_title[:80] if cleaned_title else None

    def _classify_site(self, site_name):
        """Assign a simple category using keyword-based rules."""
        lower_site = site_name.lower()

        productive_keywords = ("leetcode", "github", "docs")
        distracting_keywords = ("youtube", "instagram")

        if any(keyword in lower_site for keyword in productive_keywords):
            return "Productive"
        if any(keyword in lower_site for keyword in distracting_keywords):
            return "Distracting"
        return "Neutral"

    def get_usage_summary(self):
        """Return the current in-memory website usage summary."""
        now = time.time()

        with self.lock:
            snapshot_time_spent = dict(self.time_spent)

            # Include time spent on the currently active site up to this exact request.
            if self.current_site:
                live_elapsed = max(0, int(now - self.last_tick_at))
                snapshot_time_spent[self.current_site] = (
                    snapshot_time_spent.get(self.current_site, 0) + live_elapsed
                )

            sites = sorted(snapshot_time_spent.keys())
            category = {
                site: self.category.get(site, self._classify_site(site))
                for site in sites
            }

            return {
                "sites": sites,
                "time_spent": snapshot_time_spent,
                "category": category,
            }

    def get_current_site_info(self):
        """Return the current active site and its category."""
        with self.lock:
            if not self.current_site:
                return {
                    "site": None,
                    "category": "Neutral",
                }

            return {
                "site": self.current_site,
                "category": self.category.get(
                    self.current_site,
                    self._classify_site(self.current_site),
                ),
            }
