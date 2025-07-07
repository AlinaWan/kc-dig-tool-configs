"""
Pip Reroller v1.0.0-rc.3
- Testers: Please report any issues via the Discord server before production release.
- Please PR any bug fixes or improvements to the GitHub repository.

Automates the process of rerolling pips (stat ranks) in Dig by detecting rank-colored objects
within a user-selected screen area and clicking configured UI buttons, stopping when user-defined
quality and count conditions are met.

Features:
- Interactive GUI for selecting detection area, pip rank quality, and minimum object requirements.
- Real-time preview window with bounding box overlays for detected ranks.
- Per-rank live debug count display in the GUI.
- Flexible color tolerance and object merging for robust detection under various conditions.
- Simulates mouse clicks via AutoHotkey for compatibility with games.
- Fully configurable stop conditions, supporting minimum quality, object count, and SS rank gating.
- Built with OpenCV, tkinter, pynput, ahk, and optimized win32gui for screen capture.

Some detection and selection logic adapted from iamnotbobby <https://github.com/iamnotbobby> (MIT licensed).
This script is licensed under the MIT License.

MIT License

Copyright (c) 2025 Riri <https://github.com/AlinaWan>
Copyright (c) 2025 bobby

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import tkinter as tk
from tkinter import Label, Entry, StringVar
import threading
import cv2
import numpy as np
import time
import os
import ctypes # For DPI awareness
import win32gui, win32ui, win32con # For optimized screen capture
from pynput import keyboard
from ahk import AHK

# --- DPI Awareness ---
# This should be called as early as possible in the script execution.
# DPI Awareness Constants
PROCESS_DPI_UNAWARE = 0
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2

def set_dpi_awareness():
    """
    Sets the DPI awareness for the current process to ensure consistent
    coordinate handling, especially on high-DPI displays.
    """
    if os.name == 'nt':  # Check if the OS is Windows
        try:
            # For Windows 8.1 and later, use Per-Monitor DPI Awareness
            # This allows the application to scale correctly when moved between
            # monitors with different DPI settings.
            ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
        except AttributeError:
            # Fallback for Windows versions prior to 8.1 (e.g., Windows 7, 8)
            # Use System DPI Aware, which scales based on the primary display's DPI
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e:
            print(f"Warning: Could not set DPI awareness. Error: {e}")
            print("This might lead to coordinate issues on high-DPI displays.")

# --- ScreenCapture Class ---
class ScreenCapture:
    """
    Provides optimized screen capture functionality for Windows using win32gui/win32ui.
    Manages Device Context (DC) and bitmap resources efficiently.
    """
    def __init__(self):
        self.hwnd = win32gui.GetDesktopWindow() # Handle to the desktop window
        self.hwindc = None
        self.srcdc = None
        self.memdc = None
        self.bmp = None
        self._initialized = False
        self._last_bbox = None
        self._last_width = 0
        self._last_height = 0

    def _initialize_dc(self, width, height):
        """Initializes GDI device contexts and bitmap for capturing."""
        try:
            self.hwindc = win32gui.GetWindowDC(self.hwnd) # Get DC for the entire screen
            self.srcdc = win32ui.CreateDCFromHandle(self.hwindc) # Create a DC object from the screen DC
            self.memdc = self.srcdc.CreateCompatibleDC() # Create a compatible DC in memory
            self.bmp = win32ui.CreateBitmap() # Create a bitmap object
            # Create a compatible bitmap with the specified dimensions
            self.bmp.CreateCompatibleBitmap(self.srcdc, width, height)
            self.memdc.SelectObject(self.bmp) # Select the bitmap into the memory DC
            self._initialized = True
            self._last_width = width
            self._last_height = height
        except Exception as e:
            print(f"Error initializing DC: {e}")
            self._cleanup() # Ensure cleanup on initialization failure
            return False
        return True

    def _cleanup(self):
        """Cleans up and releases GDI resources."""
        try:
            if self.memdc:
                self.memdc.DeleteDC()
                self.memdc = None
        except Exception as e: print(f"Cleanup memdc error: {e}")
        try:
            if self.srcdc:
                self.srcdc.DeleteDC()
                self.srcdc = None
        except Exception as e: print(f"Cleanup srcdc error: {e}")
        try:
            if self.hwindc:
                win32gui.ReleaseDC(self.hwnd, self.hwindc)
                self.hwindc = None
        except Exception as e: print(f"Cleanup hwindc error: {e}")
        try:
            if self.bmp:
                win32gui.DeleteObject(self.bmp.GetHandle()) # Delete the bitmap object
                self.bmp = None
        except Exception as e: print(f"Cleanup bmp error: {e}")
        self._initialized = False

    def capture(self, bbox=None):
        """
        Captures a screenshot of the specified bounding box.
        Re-initializes GDI objects only if the bounding box changes.
        Returns a BGR NumPy array.
        """
        if not bbox: return None
        left, top, right, bottom = bbox
        width, height = right - left, bottom - top
        if width <= 0 or height <= 0: return None

        # Re-initialize GDI objects if the bounding box or its dimensions change
        if (self._last_bbox != bbox or not self._initialized or
                width != self._last_width or height != self._last_height):
            self._cleanup()
            self._last_bbox = bbox # Update _last_bbox for the new region

        if not self._initialized:
            if not self._initialize_dc(width, height): return None

        try:
            # BitBlt copies the pixel data from the screen DC to the memory DC
            self.memdc.BitBlt((0, 0), (width, height), self.srcdc, (left, top), win32con.SRCCOPY)
            # Get the bitmap bits
            signedIntsArray = self.bmp.GetBitmapBits(True)
            # Convert to NumPy array and reshape to HxWx4 (BGRA)
            img = np.frombuffer(signedIntsArray, dtype='uint8').reshape((height, width, 4))
            # Convert BGRA to BGR for OpenCV compatibility
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"Capture error: {e}")
            self._cleanup() # Cleanup on error to force re-initialization next time
            return None

    def close(self):
        """Public method to explicitly close and clean up resources."""
        self._cleanup()

# --- Class ranks, order, and their colors (BGR for OpenCV, HEX for Tkinter) ---
RANKS = [
    ("F",   (182, 171, 165),  "#b6aba5"),
    ("D",   (243, 177, 149),  "#f3b195"),
    ("C",   (130, 255, 105),  "#82ff69"),
    ("B",   (255, 134, 148),  "#ff8694"),
    ("A",   (66, 201, 255),   "#42c9ff"),
    ("S",   (102, 56, 255),   "#6638ff"),
    ("SS",  (174, 130, 255),  "#ae82ff"),
]

def bgr_to_rgb_hex(bgr):
    """Converts a BGR color tuple to an RGB hex string."""
    b, g, r = bgr
    return f'#{r:02x}{g:02x}{b:02x}'

RANK_ORDER = {rank: i for i, (rank, _, _) in enumerate(RANKS)}
RANK_HEX = {rank: hexcode for rank, _, hexcode in RANKS}
RANK_TK_HEX = {rank: bgr_to_rgb_hex(bgr) for rank, bgr, _ in RANKS}

# --- ImageProcessor Thread ---
class ImageProcessor(threading.Thread):
    """
    Dedicated thread for continuously capturing screenshots, detecting pips,
    and signaling the main reroll loop to stop when conditions are met.
    """
    def __init__(self, app_ref):
        super().__init__(daemon=True) # Daemon thread exits when main program exits
        self.app = app_ref # Reference to the main app instance
        self.stop_event = threading.Event() # Event to signal this thread to stop
        self.current_rank_counts = {rank: 0 for rank, _, _ in RANKS}
        self.lock = threading.Lock() # Lock for safely accessing shared data (rank counts)
        self.screen_capturer = ScreenCapture() # Instantiate the optimized screen capturer

    def run(self):
        """Main loop for the image processing thread."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        while not self.stop_event.is_set():
            if self.app.game_area is None:
                time.sleep(0.1) # Wait if area not set by user
                continue

            try:
                # Capture screenshot using the optimized ScreenCapture class
                frame = self.screen_capturer.capture(bbox=self.app.game_area)
                if frame is None:
                    # Handle capture failure (e.g., invalid area, GDI error)
                    self.app.root.after(0, lambda: self.app.message_var.set("Screenshot capture failed. Retrying..."))
                    time.sleep(0.1) # Short delay before retrying capture
                    continue

                # Perform pip detection and classification
                detected_objs = self.app.detect_and_classify(frame)

                # Update shared rank counts safely for the GUI
                with self.lock:
                    new_counts = {rank: 0 for rank, _, _ in RANKS}
                    for obj in detected_objs:
                        new_counts[obj['rank']] += 1
                    self.current_rank_counts = new_counts
                    
                # Schedule GUI update on the main thread (Tkinter is not thread-safe)
                self.app.root.after(0, lambda: self.app.update_rank_counts_gui(detected_objs))

                # Check stop conditions based on detected pips
                min_rank_idx = RANK_ORDER[self.app.min_quality]
                filtered_objs = [obj for obj in detected_objs if RANK_ORDER[obj['rank']] >= min_rank_idx]
                ss_objs = [obj for obj in detected_objs if obj['rank'] == "SS"]

                should_stop = False
                if self.app.stop_at_ss > 0:
                    if len(filtered_objs) >= self.app.min_objects and len(ss_objs) >= self.app.stop_at_ss:
                        should_stop = True
                else:
                    if len(filtered_objs) >= self.app.min_objects:
                        should_stop = True

                # If conditions are met AND the main loop is currently running, signal it to stop
                if should_stop and self.app.running:
                    # Only log if logging is enabled and there is at least one detected object (of any rank)
                    if getattr(self.app, "enable_logging", False) and detected_objs:
                        self.app.log_event(
                            filtered_objs,
                            self.current_rank_counts.copy(),
                            {
                                "min_quality": self.app.min_quality,
                                "min_objects": self.app.min_objects,
                                "stop_at_ss": self.app.stop_at_ss,
                                "tolerance": self.app.tolerance,
                                "object_tolerance": self.app.object_tolerance,
                                "click_delay_ms": self.app.click_delay_ms,
                                "image_poll_delay_ms": self.app.image_poll_delay_ms,
                                "game_area": self.app.game_area,
                                "chisel_button_pos": self.app.chisel_button_pos,
                                "buy_button_pos": self.app.buy_button_pos,
                            },
                            decision=f"StopConditionMet: Signalling reroll thread to suspend"
                        )
                    self.app.root.after(0, lambda: self.app.message_var.set(
                        f"Min: {self.app.min_quality} x{self.app.min_objects}" +
                        (f", SS: {self.app.stop_at_ss}" if self.app.stop_at_ss > 0 else "") +
                        " met. Signalling stop."
                    ))
                    self.app.stop_running_async() # Signal the main reroll thread to stop
                    self.stop_event.set() # Also tell this image processor thread to gracefully stop
                    break # Exit this thread's loop

                # Small delay to control the image polling rate
                time.sleep(self.app.image_poll_delay_ms / 1000)

            except Exception as e:
                # Log errors and prevent tight looping on continuous errors
                self.app.root.after(0, lambda: self.app.message_var.set(f"ImageProc Error: {e}"))
                time.sleep(0.5) # Prevent tight loop on error

    def get_current_rank_counts(self):
        """Safely retrieve the latest rank counts."""
        with self.lock:
            return self.current_rank_counts.copy()

    def stop(self):
        """Signals the image processing thread to stop and cleans up resources."""
        self.stop_event.set()
        self.screen_capturer.close() # Close the screen capturer resources


# --- Main PipReroller Application Class ---
class PipRerollerApp:
    """
    Main Tkinter application for the Pip Reroller, managing GUI,
    user input, and orchestrating background threads.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Pip Reroller by Riri")
        self.root.geometry("440x520") # Increased height for new input field
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True) # Keep GUI on top

        # Configuration variables
        self.game_area = None
        self.chisel_button_pos = None
        self.buy_button_pos = None
        self.preview_active = False
        self.running = False

        self.tolerance = 10
        self.stop_at_ss = 0
        self.click_delay_ms = 50
        self.object_tolerance = 10
        self.image_poll_delay_ms = 10 # How often the image processor polls

        self.min_quality = "F"
        self.min_objects = 1
        self.game_window_title = StringVar(value="Roblox")

        # GUI state variables
        self.rank_counts = {rank: 0 for rank, _, _ in RANKS} # Updated by ImageProcessor via GUI callback
        self.status_var = StringVar(value="Status: Suspended")
        self.message_var = StringVar(value="")
        self.status_color = "#ff5555"

        # [DEBUG] Enable/disable logging
        self.enable_logging = False  # Set to True to enable logging
        self.log_buffer = []
        self.log_button = None
        self.last_detected_objs = [] # Prevent attribute errors if the reroll loop runs before detections

        # Thread management
        self.image_processor_thread = None
        self.reroll_loop_thread = None
        self.preview_thread = None
        self.stop_reroll_event = threading.Event() # Event for reroll loop to stop

        # --- GUI Elements ---
        label_fg = "#eeeeee"
        entry_bg = "#333333"
        entry_fg = "#ffffff"
        btn_bg = "#444444"
        btn_fg = "#dddddd"
        pad_y = 5

        def make_label(text):
            return tk.Label(root, text=text, fg=label_fg, bg="#222222")

        # Input fields
        frame_tol = tk.Frame(root, bg="#222222")
        frame_tol.pack(pady=(10, 0))
        tol_label = make_label("Color Tolerance:")
        tol_label.pack(in_=frame_tol, side="left")
        Tooltip(tol_label, "How close a color must be to count as a match.\nIncrease if detection is unreliable.")
        self.tolerance_entry = Entry(frame_tol, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.tolerance_entry.pack(side="left", padx=(10, 0))
        self.tolerance_entry.insert(0, str(self.tolerance))
        self.tolerance_entry.bind('<KeyRelease>', self.update_tolerance)

        frame_stop = tk.Frame(root, bg="#222222")
        frame_stop.pack(pady=(10, 0))
        ss_label = tk.Label(frame_stop, text="Minimum SS:", fg=label_fg, bg="#222222")
        ss_label.pack(side="left")
        Tooltip(ss_label, "Minimum number of SS-rank pips required to stop rerolling.")
        self.stop_at_entry = Entry(frame_stop, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.stop_at_entry.pack(side="left", padx=5)
        self.stop_at_entry.insert(0, str(self.stop_at_ss))
        self.stop_at_entry.bind('<KeyRelease>', self.update_stop_at)

        frame_delay = tk.Frame(root, bg="#222222")
        frame_delay.pack(pady=(10, 0))
        delay_label = make_label("Click Delay (ms):")
        delay_label.pack(in_=frame_delay, side="left")
        Tooltip(delay_label, "Delay in milliseconds between simulated clicks.\nIncrease if the game lags or misses clicks.")
        self.click_delay_entry = Entry(frame_delay, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.click_delay_entry.pack(side="left", padx=(10, 0))
        self.click_delay_entry.insert(0, str(self.click_delay_ms))
        self.click_delay_entry.bind('<KeyRelease>', self.update_click_delay)

        frame_poll_delay = tk.Frame(root, bg="#222222")
        frame_poll_delay.pack(pady=(10, 0))
        poll_label = make_label("Image Poll Delay (ms):")
        poll_label.pack(in_=frame_poll_delay, side="left")
        Tooltip(poll_label, "How often to check for pips (in milliseconds).\nLower values update faster but use more CPU.\nDecrease if the macro accidentally rerolls on a suspend condition.")
        self.image_poll_delay_entry = Entry(frame_poll_delay, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.image_poll_delay_entry.pack(side="left", padx=(10, 0))
        self.image_poll_delay_entry.insert(0, str(self.image_poll_delay_ms))
        self.image_poll_delay_entry.bind('<KeyRelease>', self.update_image_poll_delay)

        frame_obj_tol = tk.Frame(root, bg="#222222")
        frame_obj_tol.pack(pady=(10, 0))
        obj_tol_label = make_label("Object Tolerance (px):")
        obj_tol_label.pack(in_=frame_obj_tol, side="left")
        Tooltip(obj_tol_label, "How close detected objects must be (in pixels) to be merged as one pip.\nIncrease if pips are split into multiple boxes.")
        self.object_tolerance_entry = Entry(frame_obj_tol, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.object_tolerance_entry.pack(side="left", padx=(10, 0))
        self.object_tolerance_entry.insert(0, str(self.object_tolerance))
        self.object_tolerance_entry.bind('<KeyRelease>', self.update_object_tolerance)

        frame_minobjs = tk.Frame(root, bg="#222222")
        frame_minobjs.pack(pady=(13, 0))
        minobjs_label = Label(frame_minobjs, text="Minimum Objects:", fg=label_fg, bg="#222222")
        minobjs_label.pack(side="left")
        Tooltip(minobjs_label, "Minimum number of pips (of the selected quality or higher) required to stop rerolling.")
        self.min_objects_entry = Entry(frame_minobjs, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.min_objects_entry.pack(side="left", padx=(10,0))
        self.min_objects_entry.insert(0, str(self.min_objects))
        self.min_objects_entry.bind('<KeyRelease>', self.update_min_objects)

        # Minimum Quality row
        frame_quality = tk.Frame(root, bg="#222222")
        frame_quality.pack(pady=(20, 0))
        min_quality_label = Label(
            frame_quality,
            text="Minimum Quality",
            fg=label_fg,
            bg="#222222",
            font=("Arial", 12, "bold")
        )
        min_quality_label.pack()
        Tooltip(
            min_quality_label,
            "Select the lowest pip rank that you are willing to accept.\n"
            "Only pips of this quality or higher are considered for the stop condition."
        )

        self.quality_buttons = {}
        frame_buttons = tk.Frame(frame_quality, bg="#222222")
        frame_buttons.pack(pady=(5, 0))
        for rank, _, _ in RANKS:
            btn = tk.Button(
                frame_buttons,
                text=rank,
                width=4,
                font=("Arial", 11, "bold"),
                relief="sunken" if rank == self.min_quality else "raised",
                bg=RANK_TK_HEX[rank] if rank == self.min_quality else "#333333",
                fg="#222222" if rank == self.min_quality else "#ffffff",
                activebackground=RANK_TK_HEX[rank],
                activeforeground="#222222",
                command=lambda r=rank: self.select_quality(r),
            )
            btn.pack(side="left", padx=3)
            self.quality_buttons[rank] = btn

        # Debugging: Rank counts row
        frame_rank_counts = tk.Frame(root, bg="#222222")
        frame_rank_counts.pack(pady=(10, 0))
        # Top row: labels with rank names
        self.rank_labels = []
        for rank in RANK_TK_HEX:
            l = tk.Label(frame_rank_counts, text=rank, fg=RANK_TK_HEX[rank], bg="#222222", font=("Arial", 11, "bold"))
            l.pack(side="left", padx=7)
            self.rank_labels.append(l)
        # Bottom row: StringVars with counts per rank
        frame_rank_counts2 = tk.Frame(root, bg="#222222")
        frame_rank_counts2.pack()
        self.rank_count_vars = {}
        self.rank_count_labels = {}
        for rank in RANK_TK_HEX:
            v = StringVar(value="0")
            l = tk.Label(frame_rank_counts2, textvariable=v, fg=RANK_TK_HEX[rank], bg="#222222", font=("Arial", 11))
            l.pack(side="left", padx=7)
            self.rank_count_vars[rank] = v
            self.rank_count_labels[rank] = l

        # Action Buttons
        btn_frame = tk.Frame(root, bg="#222222")
        btn_frame.pack(pady=15)
        btn_opts = dict(bg=btn_bg, fg=btn_fg, width=18)
        tk.Button(btn_frame, text="Select Area", command=self.start_area_selection, **btn_opts).grid(row=0, column=0, padx=5, pady=pad_y)
        tk.Button(btn_frame, text="Set Chisel Button", command=self.start_chisel_button_selection, **btn_opts).grid(row=0, column=1, padx=5, pady=pad_y)
        tk.Button(btn_frame, text="Set Buy Button", command=self.start_buy_button_selection, **btn_opts).grid(row=1, column=0, padx=5, pady=pad_y)
        tk.Button(btn_frame, text="Start Preview", command=self.start_preview, **btn_opts).grid(row=1, column=1, padx=5, pady=pad_y)

        self.status_label = tk.Label(root, textvariable=self.status_var, fg=self.status_color,
                                     bg="#222222", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=(10, 0))

        self.message_label = tk.Label(root, textvariable=self.message_var,
                                      fg="#ff6666", bg="#222222", font=("Arial", 10))
        self.message_label.pack()

        hotkey_label = tk.Label(root, text="Toggle Running: F5", fg="#888888", bg="#222222", font=("Arial", 9))
        hotkey_label.pack(pady=(10, 5))

        # Keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()

        # AHK instance (default path to AutoHotkey.exe)
        self.ahk = AHK()

        # Ensure threads are cleanly stopped on app close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        if self.enable_logging:
            def log_event(self, objects, rank_counts, settings, decision):
                import datetime
                if not objects:
                    return
                now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                total_objs = len(objects)
                obj_str = "; ".join(
                    f"{o['rank']}@({o['rect'][0]},{o['rect'][1]},{o['rect'][2]},{o['rect'][3]})"
                    for o in objects
                )
                counts_str = ", ".join(f"{rank}:{rank_counts[rank]}" for rank in rank_counts)
                settings_str = ", ".join(f"{k}={v}" for k, v in settings.items())
                log_line = (
                    f"{now} | Objects Counted To Stop Condition: {total_objs} | Locations: {obj_str} | Counts: {counts_str} | "
                    f"Settings: {settings_str} | Decision: {decision}"
                )
                self.log_buffer.append(log_line)
        
            def dump_logs(self):
                import datetime
                if not self.log_buffer:
                    self.message_var.set("No logs to write.")
                    return
                filename = f"pip_reroller_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    for line in self.log_buffer:
                        f.write(line + "\n")
                self.message_var.set(f"Logs written to {filename}")
                self.log_buffer.clear()
        
            # Attach methods to the instance
            self.log_event = log_event.__get__(self)
            self.dump_logs = dump_logs.__get__(self)
        
            # Show the log button
            self.log_button = tk.Button(
                root, text="DEBUG: Dump Logs", command=self.dump_logs,
                bg="#222222", fg="#ffcc00", font=("Arial", 9, "bold")
            )
            self.log_button.place(x=5, y=5)
        else:
            self.log_event = lambda *a, **k: None

    def _on_closing(self):
        """Handles graceful shutdown of threads and resources when the app closes."""
        self.stop_running_async() # Ensure main reroll loop stops
        if self.image_processor_thread and self.image_processor_thread.is_alive():
            self.image_processor_thread.stop() # Tell image processor to stop and cleanup
            self.image_processor_thread.join(timeout=1.0) # Wait for it to finish
        self.listener.stop() # Stop keyboard listener
        self.root.destroy()

    def select_quality(self, rank):
        """Updates the selected minimum quality rank in the GUI."""
        self.min_quality = rank
        for r, btn in self.quality_buttons.items():
            if r == rank:
                btn.config(relief="sunken", bg=RANK_TK_HEX[r], fg="#222222")
            else:
                btn.config(relief="raised", bg="#333333", fg="#ffffff")

    def update_tolerance(self, event=None):
        """Updates color tolerance from GUI input."""
        try:
            val = int(self.tolerance_entry.get())
            if 0 <= val <= 255:
                self.tolerance = val
        except ValueError:
            pass

    def update_stop_at(self, event=None):
        """Updates minimum SS rank count from GUI input."""
        try:
            val = int(self.stop_at_entry.get())
            if val >= 0:
                self.stop_at_ss = val
        except ValueError:
            pass

    def update_min_objects(self, event=None):
        """Updates minimum object count from GUI input."""
        try:
            val = int(self.min_objects_entry.get())
            if val >= 1:
                self.min_objects = val
        except ValueError:
            pass

    def update_click_delay(self, event=None):
        """Updates click delay from GUI input."""
        try:
            val = int(self.click_delay_entry.get())
            if val >= 0:
                self.click_delay_ms = val
        except ValueError:
            pass

    def update_image_poll_delay(self, event=None):
        """Updates image polling delay from GUI input."""
        try:
            val = int(self.image_poll_delay_entry.get())
            if val >= 0:
                self.image_poll_delay_ms = val
        except ValueError:
            pass

    def update_object_tolerance(self, event=None):
        """Updates object merging tolerance from GUI input."""
        try:
            val = int(self.object_tolerance_entry.get())
            if val >= 0:
                self.object_tolerance = val
        except ValueError:
            pass

    def start_area_selection(self):
        """Initiates screen area selection for pip detection."""
        self.root.iconify() # Minimize main window
        self.selection_overlay = tk.Toplevel() # Create a transparent overlay window
        self.selection_overlay.attributes('-fullscreen', True, '-alpha', 0.2, '-topmost', True)
        self.selection_overlay.configure(bg='blue', cursor='crosshair')
        self.selection_rect = tk.Frame(self.selection_overlay, bg='red', highlightthickness=1,
                                     highlightbackground='white')
        self.selection_overlay.bind('<Button-1>', self.on_drag_start)
        self.selection_overlay.bind('<B1-Motion>', self.on_drag_motion)
        self.selection_overlay.bind('<ButtonRelease-1>', self.on_drag_end)

    def on_drag_start(self, event):
        """Handles the start of a drag event for area selection."""
        self.drag_start = (event.x_root, event.y_root)
        self.selection_rect.place(x=event.x, y=event.y, width=1, height=1)

    def on_drag_motion(self, event):
        """Handles mouse motion during area selection drag."""
        x1, y1 = self.drag_start
        x2, y2 = event.x_root, event.y_root
        x, y = self.selection_overlay.winfo_rootx(), self.selection_overlay.winfo_rooty()
        self.selection_rect.place(x=min(x1, x2) - x, y=min(y1, y2) - y,
                                  width=abs(x1 - x2), height=abs(y1 - y2))

    def on_drag_end(self, event):
        """Handles the end of a drag event, setting the game area."""
        x1, y1 = self.drag_start
        x2, y2 = event.x_root, event.y_root
        self.game_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.selection_overlay.destroy()
        self.root.deiconify() # Restore main window
        self.message_var.set("Game area set.")

    def start_chisel_button_selection(self):
        """Initiates selection for the 'Chisel' button position."""
        self._start_button_selection("chisel")

    def start_buy_button_selection(self):
        """Initiates selection for the 'Buy' button position."""
        self._start_button_selection("buy")

    def _start_button_selection(self, button_type):
        """Helper to create an overlay for button position selection."""
        self.root.iconify()
        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True, '-alpha', 0.3, '-topmost', True)
        overlay.configure(bg='purple' if button_type == "chisel" else 'darkgreen', cursor='crosshair')

        text = ("Click to set CHISEL BUTTON" if button_type == "chisel"
                else "Click to set BUY BUTTON")

        label = Label(overlay, text=text, font=("Arial", 20, "bold"),
                      bg=overlay['bg'], fg='white')
        label.pack(pady=100)

        overlay.bind('<Button-1>', lambda e: self.set_button_position(e, button_type, overlay))

    def set_button_position(self, event, button_type, overlay):
        """Sets the coordinates for the selected button."""
        pos = (event.x_root, event.y_root)
        if button_type == "chisel":
            self.chisel_button_pos = pos
        else:
            self.buy_button_pos = pos
        overlay.destroy()
        self.root.deiconify()
        self.message_var.set(f"{button_type.capitalize()} button set at {pos}")

    def on_key_press(self, key):
        """Handles F5 hotkey to toggle reroller on/off."""
        if key == keyboard.Key.f5:
            if not self.running:
                self.start_running_async()
            else:
                self.stop_running_async()

    def start_running_async(self):
        """
        Starts the reroller automation by validating settings, activating game window,
        and launching background threads.
        """
        # --- Input validation ---
        if self.game_area is None:
            self.message_var.set("Please select area first.")
            return
        if self.chisel_button_pos is None:
            self.message_var.set("Please set Chisel Button first.")
            return
        if self.buy_button_pos is None:
            self.message_var.set("Please set Buy Button first.")
            return
        
        # --- Activate the game window (Crucial for reliable clicks) ---
        target_title = self.game_window_title.get()
        if not target_title:
            self.message_var.set("Please enter a Game Window Title.") # This logic is here if we ever decide to extend support for bootstrappers that might not have the same window title
            return

        if not self.ahk.win_exists(target_title):
            self.message_var.set(f"Error: Game window '{target_title}' not found. Please ensure it's open.")
            return
        
        self.ahk.win_activate(target_title)
        time.sleep(0.1) # Give the OS a moment to switch focus

        self.message_var.set("Game window activated. Starting reroll.")
        self.running = True
        self.update_status(True)
        
        # Call before starting any threads
        # This avoids very rare conditions where a race condition can happen where the thread could start immediately,
        # check the stop event, and mistakenly exit if it was still set from the last run.
        # We call it here in case the reroll loop starts without clearing the event first
        self.stop_reroll_event.clear() # Clear any previous stop signal for the reroll loop

        # Start the Image Processor thread if not already running
        if self.image_processor_thread is None or not self.image_processor_thread.is_alive():
            self.image_processor_thread = ImageProcessor(self)
            self.image_processor_thread.stop_event.clear() # Clear any previous stop signal
            self.image_processor_thread.start()
        
        # Start the Reroll Loop thread if not already running
        if self.reroll_loop_thread is None or not self.reroll_loop_thread.is_alive():
            self.reroll_loop_thread = threading.Thread(target=self.reroll_loop, daemon=True)
            self.reroll_loop_thread.start()

    def stop_running_async(self):
        """Signals all active threads to stop and updates GUI status."""
        self.running = False
        self.update_status(False)
        self.stop_reroll_event.set() # Signal the reroll loop to stop
        if self.image_processor_thread and self.image_processor_thread.is_alive():
            self.image_processor_thread.stop() # Signal the image processor to stop

    def update_status(self, running):
        """Updates the status label in the GUI."""
        if running:
            self.status_var.set("Status: Running")
            self.status_label.config(fg="#55ff55")
        else:
            self.status_var.set("Status: Suspended")
            self.status_label.config(fg="#ff5555")

    def update_rank_counts_gui(self, detected_objs):
        """
        Updates the rank counts displayed in the GUI.
        This method is called safely from the ImageProcessor thread via root.after().
        """
        self.last_detected_objs = detected_objs # Store latest detected objects for logging
        # Reset counts for all ranks
        for rank in self.rank_count_vars:
            self.rank_counts[rank] = 0
        # Count detected objects by rank
        for obj in detected_objs:
            self.rank_counts[obj['rank']] += 1

        # Update Tkinter StringVars to refresh GUI labels
        for rank in self.rank_count_vars:
            self.rank_count_vars[rank].set(str(self.rank_counts[rank]))

    def start_preview(self):
        """Toggles the real-time bounding box preview window."""
        if self.game_area is None:
            self.message_var.set("Please select area first to start preview.")
            return
    
        if self.preview_active:
            self.preview_active = False
            # Do not call join() or destroyWindow here; let the thread clean up
            self.preview_thread = None
            return
    
        self.preview_active = True
        self.preview_thread = threading.Thread(target=self.preview_loop, daemon=True)
        self.preview_thread.start()

    def preview_loop(self):
        """
        Continuously captures screenshots, detects pips, and displays them
        with bounding boxes in an OpenCV window for debugging.
        """
        preview_capturer = ScreenCapture()
        cv2.namedWindow("BBox Preview", cv2.WINDOW_AUTOSIZE)
        cv2.setWindowProperty("BBox Preview", cv2.WND_PROP_TOPMOST, 1)
    
        while self.preview_active:
            if self.game_area is None:
                time.sleep(0.05)
                continue
    
            frame = preview_capturer.capture(bbox=self.game_area)
            if frame is None:
                time.sleep(0.05)
                continue
    
            detected_objs = self.detect_and_classify(frame)
            # Update GUI rank counts safely on the main thread
            self.root.after(0, lambda objs=detected_objs: self.update_rank_counts_gui(objs))
    
            debug_frame = frame.copy()
            for obj in detected_objs:
                x, y, w, h = obj['rect']
                color = obj['cv2color']
                cv2.rectangle(debug_frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(debug_frame, obj['rank'], (x+2, y+18), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
            cv2.imshow("BBox Preview", debug_frame)
            # Use a very short waitKey and check preview_active frequently
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.preview_active = False
                break
            time.sleep(0.01)  # Small sleep to reduce CPU usage
    
        cv2.destroyAllWindows()
        preview_capturer.close()

    def detect_and_classify(self, frame):
        """
        Detects and classifies pip objects within a given image frame.
        Applies color masks, morphological operations, and contour detection.
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        detected = []
        for rank, bgr, _ in RANKS:
            mask = self.rank_mask(frame, np.array(bgr), self.tolerance)
            # Apply morphological closing to connect nearby pixels and fill small gaps
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Filter contours by area to remove noise and get bounding rectangles
            rects = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 1]
            # Merge overlapping or close rectangles
            merged_rects = self.merge_rectangles(rects, self.object_tolerance)
            for rect in merged_rects:
                detected.append({
                    "rank": rank,
                    "rect": rect,
                    "cv2color": bgr
                })
        # Sort detected objects by rank order (highest rank first)
        detected.sort(key=lambda o: -RANK_ORDER[o['rank']])
        return detected

    def rank_mask(self, frame, color_bgr, tolerance):
        """
        Creates a binary mask for pixels within a certain color tolerance of a target BGR color.
        """
        # Calculate absolute difference between frame pixels and target color
        diff = np.abs(frame.astype(np.int16) - color_bgr)
        # Create mask where all color channels are within tolerance
        mask = np.all(diff <= tolerance, axis=2).astype(np.uint8) * 255
        return mask

    def merge_rectangles(self, rects, max_distance):
        """
        Merges rectangles that are close to each other, useful for combining
        fragmented detections of a single object.
        """
        merged = []
        used = [False] * len(rects)

        def rect_distance(r1, r2):
            """Calculates the Euclidean distance between the closest points of two rectangles."""
            x1, y1, w1, h1 = r1
            x2, y2, w2, h2 = r2

            # Determine horizontal distance
            left = x2 + w2 < x1
            right = x1 + w1 < x2
            dx = 0
            if right:
                dx = x2 - (x1 + w1)
            elif left:
                dx = x1 - (x2 + w2)

            # Determine vertical distance
            above = y2 + h2 < y1
            below = y1 + h1 < y2
            dy = 0
            if below:
                dy = y2 - (y1 + h1)
            elif above:
                dy = y1 - (y2 + h2)
            
            # Return hypotenuse (closest distance)
            return np.hypot(dx, dy)

        for i, r in enumerate(rects):
            if used[i]:
                continue # Skip if already merged

            x, y, w, h = r
            # Initialize merged_rect with current rectangle's bounds (min_x, min_y, max_x, max_y)
            merged_rect = [x, y, x + w, y + h]
            used[i] = True

            # Iterate through remaining rectangles to find merge candidates
            for j in range(i + 1, len(rects)):
                if used[j]:
                    continue
                dist = rect_distance(r, rects[j])
                if dist <= max_distance:
                    # If close enough, expand merged_rect to include rects[j]
                    rx, ry, rw, rh = rects[j]
                    merged_rect[0] = min(merged_rect[0], rx)
                    merged_rect[1] = min(merged_rect[1], ry)
                    merged_rect[2] = max(merged_rect[2], rx + rw)
                    merged_rect[3] = max(merged_rect[3], ry + rh)
                    used[j] = True # Mark as used

            # Add the final merged rectangle (convert back to x, y, w, h format)
            merged.append((merged_rect[0], merged_rect[1],
                           merged_rect[2] - merged_rect[0],
                           merged_rect[3] - merged_rect[1]))
        return merged

    def click_at(self, x, y):
        """Simulates a mouse click at the given screen coordinates using AHK."""
        self.ahk.mouse_move(x, y, speed=0) # Instant move
        self.ahk.click() # Left click down & up

    def reroll_loop(self):
        """
        The main automation loop that performs clicks.
        It is highly responsive to stop signals from the ImageProcessor thread.
        """
        while not self.stop_reroll_event.is_set():
            # Check if image processor has signaled a stop.
            # We wait with a short timeout to allow responsiveness.
            # If stop_reroll_event is set by ImageProcessor, this will immediately unblock.
            if self.stop_reroll_event.wait(timeout=0.01): # Wait for 10ms
                break # Exit the loop if stop is signaled

            # --- LOGGING: Only log if objects detected and logging is enabled ---
            min_rank_idx = RANK_ORDER[self.min_quality]
            detected_objs = getattr(self, "last_detected_objs", [])
            filtered_objs = [obj for obj in detected_objs if RANK_ORDER[obj["rank"]] >= min_rank_idx]
            if self.enable_logging and filtered_objs:
                self.log_event(
                    filtered_objs,
                    self.image_processor_thread.get_current_rank_counts(),
                    {
                        "min_quality": self.min_quality,
                        "min_objects": self.min_objects,
                        "stop_at_ss": self.stop_at_ss,
                        "tolerance": self.tolerance,
                        "object_tolerance": self.object_tolerance,
                        "click_delay_ms": self.click_delay_ms,
                        "image_poll_delay_ms": self.image_poll_delay_ms,
                        "game_area": self.game_area,
                        "chisel_button_pos": self.chisel_button_pos,
                        "buy_button_pos": self.buy_button_pos,
                    },
                    decision="Rolling"
                )

            # If not stopped, perform the reroll clicks
            self.click_at(*self.chisel_button_pos)
            time.sleep(self.click_delay_ms / 1000) # Delay after first click
            
            # Re-check stop condition after the first click for immediate reaction
            if self.stop_reroll_event.wait(timeout=0.01):
                break

            self.click_at(*self.buy_button_pos)
            time.sleep(self.click_delay_ms / 1000) # Delay after second click
            
            # Re-check stop condition after the second click
            if self.stop_reroll_event.wait(timeout=0.01):
                break

            # Update message using the shared rank_counts from the ImageProcessor
            current_counts = self.image_processor_thread.get_current_rank_counts()
            
            # Re-calculate filtered and SS counts for the message based on latest data
            min_rank_idx = RANK_ORDER[self.min_quality]
            filtered_count = sum(count for rank, count in current_counts.items() if RANK_ORDER[rank] >= min_rank_idx)
            ss_count = current_counts.get("SS", 0)

            # Update message on the main thread
            self.root.after(0, lambda: self.message_var.set(
                f"Detected: {filtered_count} ≥{self.min_quality}" +
                (f", {ss_count} SS" if self.stop_at_ss > 0 else "") +
                ". Rolling..."
            ))
            
            # Brief pause before the next iteration, to prevent clicking too fast
            # and allow the image processor to catch up if needed
            time.sleep(0.01) # This is a general loop delay, not a click delay

class Tooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # milliseconds
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<Motion>", self.move)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") if self.widget.winfo_class() == 'Entry' else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#4d4d4d", fg="white", relief='solid', borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=4, ipady=2)

    def hide(self, event=None):
        self.unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def move(self, event):
        if self.tipwindow:
            x = event.x_root + 10
            y = event.y_root + 10
            self.tipwindow.wm_geometry(f"+{x}+{y}")

if __name__ == '__main__':
    # --- IMPORTANT: Call DPI awareness setup BEFORE Tkinter initialization ---
    set_dpi_awareness()

    root = tk.Tk()
    app = PipRerollerApp(root)
    root.mainloop()
