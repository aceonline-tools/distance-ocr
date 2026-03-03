#!/usr/bin/env python3
"""OCR number under mouse cursor and copy to clipboard.

Works on macOS and Windows.
Hotkeys work globally (even when window is not focused on Windows).

Dependencies:
  macOS:   pip install pyobjc-framework-Quartz pyobjc-framework-Vision
  Windows: pip install mss Pillow winocr keyboard
"""

import logging
import os
import platform
import re
import subprocess
import sys
import time
import traceback

SYSTEM = platform.system()

# === Error logging to file next to the executable ===

executable_directory = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
error_log_path = os.path.join(executable_directory, "error.log")

logging.basicConfig(
    filename=error_log_path,
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)

def _unhandled_exception_handler(exception_type, exception_value, exception_traceback):
    logging.error(
        "".join(traceback.format_exception(exception_type, exception_value, exception_traceback))
    )

sys.excepthook = _unhandled_exception_handler


# === Platform: Screen capture + OCR ===

if SYSTEM == "Darwin":
    import Quartz
    import objc

    objc.loadBundle(
        "Vision",
        bundle_path="/System/Library/Frameworks/Vision.framework",
        module_globals=globals(),
    )
    _VNRecognizeTextRequest = objc.lookUpClass("VNRecognizeTextRequest")
    _VNImageRequestHandler = objc.lookUpClass("VNImageRequestHandler")

    def get_mouse_position():
        mouse_location = Quartz.NSEvent.mouseLocation()
        display_height = Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID())
        return int(mouse_location.x), int(display_height - mouse_location.y)

    def capture_and_ocr():
        screen_x, screen_y = get_mouse_position()
        capture_rect = Quartz.CGRectMake(screen_x - 50, screen_y + 25, 100, 100)
        image = Quartz.CGWindowListCreateImage(
            capture_rect,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault,
        )
        if image is None:
            return ""

        request = _VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(1)
        request.setUsesLanguageCorrection_(False)
        handler = _VNImageRequestHandler.alloc().initWithCGImage_options_(image, None)
        success = handler.performRequests_error_([request], None)
        if not success:
            return ""

        results = request.results()
        if not results:
            return ""

        recognized_lines = []
        for observation in results:
            candidate = observation.topCandidates_(1)
            if candidate:
                recognized_lines.append(candidate[0].string())
        return "\n".join(recognized_lines)

elif SYSTEM == "Windows":
    import asyncio
    import ctypes
    import ctypes.wintypes
    import io

    import mss
    from PIL import Image
    from winocr import recognize_pil

    def get_mouse_position():
        point = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    async def _run_ocr(pil_image):
        return await recognize_pil(pil_image, "en")

    def capture_and_ocr():
        screen_x, screen_y = get_mouse_position()
        region = {
            "left": screen_x - 100,
            "top": screen_y,
            "width": 200,
            "height": 200,
        }
        with mss.mss() as sct:
            screenshot = sct.grab(region)
        pil_image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        result = asyncio.run(_run_ocr(pil_image))
        recognized_lines = [line.text for line in result.lines if line.text]
        return "\n".join(recognized_lines)

else:
    sys.exit(f"Unsupported platform: {SYSTEM}")


# === Platform: Clipboard ===

def copy_to_clipboard(text):
    if SYSTEM == "Darwin":
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-8"))
    elif SYSTEM == "Windows":
        process = subprocess.Popen(["clip.exe"], stdin=subprocess.PIPE)
        process.communicate(text.encode("utf-16le"))


# === Platform: Keypress ===

if SYSTEM == "Darwin":
    import termios
    import tty

    def wait_for_key():
        original_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)

elif SYSTEM == "Windows":
    import queue

    import keyboard

    _global_key_queue = queue.Queue()

    keyboard.add_hotkey("-", lambda: _global_key_queue.put("c"))
    keyboard.add_hotkey("ctrl+shift+q", lambda: _global_key_queue.put("q"))

    def wait_for_key():
        return _global_key_queue.get()


# === Main ===



def do_capture():
    try:
        start = time.perf_counter()
        recognized_text = capture_and_ocr()
        numbers_only = re.sub(r"[^\d.]", "", recognized_text)
        elapsed = (time.perf_counter() - start) * 1000
        if numbers_only:
            copy_to_clipboard(numbers_only)
            print(f"Copied: {numbers_only} ({elapsed:.0f}ms)")
        else:
            copy_to_clipboard("9999")
            print(f"No text detected. ({elapsed:.0f}ms)")
    except Exception:
        logging.error(traceback.format_exc())
        print("Error during capture. See error.log for details.")


def main():
    if SYSTEM == "Windows":
        print("Ready. Press Ctrl+Shift+C to capture, Ctrl+Shift+Q to quit.")
    else:
        print("Ready. Press 'c' to capture, 'q' to quit.")
    try:
        while True:
            key = wait_for_key()
            if key == "c":
                do_capture()
            elif key == "q":
                break
    except KeyboardInterrupt:
        pass
    print("\nStopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.error(traceback.format_exc())
        print("Fatal error. See error.log for details.")
        input("Press Enter to exit...")
