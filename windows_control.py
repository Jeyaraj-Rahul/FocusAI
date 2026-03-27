import ctypes
import os
import platform
from ctypes import wintypes


SW_MINIMIZE = 6
BROWSER_PROCESS_NAMES = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}


def minimize_active_browser_window():
    """
    Minimize the currently active browser window on Windows.

    This minimizes the whole browser window, not just one tab.
    Returns True when a supported browser window was minimized.
    """
    if platform.system() != "Windows":
        return False

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    if not process_id.value:
        return False

    process_handle = kernel32.OpenProcess(0x1000 | 0x0400, False, process_id.value)
    if not process_handle:
        return False

    try:
        buffer_length = 260
        image_path_buffer = ctypes.create_unicode_buffer(buffer_length)
        if not psapi.GetModuleFileNameExW(process_handle, None, image_path_buffer, buffer_length):
            return False

        process_name = os.path.basename(image_path_buffer.value).lower()
        if process_name not in BROWSER_PROCESS_NAMES:
            return False

        return bool(user32.ShowWindow(hwnd, SW_MINIMIZE))
    finally:
        kernel32.CloseHandle(process_handle)
