"""
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
import win32gui
import win32ui
import win32con # For optimized screen capture
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
    Sets the DPI awareness for the current process on Windows systems.

    This function configures the process to be DPI-aware, allowing it to scale
    properly on high-DPI displays. It attempts to use per-monitor DPI awareness
    on Windows 8.1 and later, falling back to system DPI awareness on earlier
    versions. If an error occurs, a warning message is printed and the process
    may experience display scaling issues.

    On non-Windows systems, this function does nothing.

    :raises Exception: If setting DPI awareness fails for an unexpected reason
                       (other than missing API on older Windows versions).
    :rtype: None
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
    Provides optimized screen capture functionality for Windows using `win32gui` and `win32ui`.

    This class manages low-level Windows GDI resources such as Device Contexts (DC) and bitmaps
    to enable fast and efficient screen captures. It is designed for repeated capturing operations
    with minimal overhead.

    Attributes
    ----------
    hwnd : int
        Handle to the desktop window.
    hwindc : PyHANDLE or None
        Handle to the window device context.
    srcdc : PyCDC or None
        Source device context obtained from the window DC.
    memdc : PyCDC or None
        Memory device context compatible with the source DC.
    bmp : PyCBitmap or None
        Bitmap object used for storing captured image data.
    _initialized : bool
        Indicates whether the capture resources have been initialized.
    _last_bbox : tuple or None
        Stores the bounding box of the last capture (left, top, right, bottom).
    _last_width : int
        Width of the last captured area in pixels.
    _last_height : int
        Height of the last captured area in pixels.

    :raises win32gui.error: If obtaining the desktop window handle fails.
    :rtype: None
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
        """
        Initializes GDI device contexts and bitmap for screen capturing.
    
        This method sets up the required Windows GDI resources, including the source
        device context, a compatible memory DC, and a compatible bitmap of the given
        dimensions. These resources are required for fast and direct pixel access
        during screen capture operations.
    
        If initialization fails, it cleans up any partially created resources and
        returns False.
    
        Parameters
        ----------
        width : int
            The width of the capture area in pixels.
        height : int
            The height of the capture area in pixels.
    
        Returns
        -------
        bool
            True if initialization succeeded, False otherwise.
    
        :raises Exception: If there is an unexpected error during GDI setup.
        """
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
        """
        Releases and cleans up all allocated GDI resources.
    
        This method safely disposes of the memory DC, source DC, bitmap, and
        window DC used during screen capture operations. It ensures no
        resource leaks occur, even if some of the resources are already
        released or failed to initialize.
    
        Exceptions during cleanup are caught and printed, but do not stop
        the cleanup process. After execution, the internal state is marked
        as uninitialized.
    
        :rtype: None
        """
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
        Captures a screenshot of the specified screen region.
    
        This method captures a portion of the screen defined by the given bounding box.
        It manages GDI resource re-initialization if the bounding box or its dimensions
        differ from the previous capture. The captured image is returned as a BGR NumPy
        array suitable for use with OpenCV.
    
        If `bbox` is `None`, or if width/height are invalid or capture fails,
        `None` is returned.
    
        Parameters
        ----------
        bbox : tuple[int, int, int, int], optional
            The bounding box of the region to capture in the format (left, top, right, bottom).
    
        Returns
        -------
        numpy.ndarray or None
            The captured image as a BGR NumPy array, or `None` if the capture failed.
    
        :raises Exception: If a GDI call fails unexpectedly during capture.
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
        """
        Releases all screen capture resources.
    
        Public method that explicitly cleans up all allocated GDI handles and internal
        buffers used for capturing. This should be called when the `ScreenCapture`
        instance is no longer needed to avoid leaking system resources.
    
        :rtype: None
        """
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
    """
    Converts a BGR color tuple to a hexadecimal RGB string.

    This function takes a color in BGR (Blue, Green, Red) format and returns
    the equivalent RGB hex string (e.g., `#rrggbb`) commonly used in web and
    GUI color specifications.

    Parameters
    ----------
    bgr : tuple[int, int, int]
        A tuple representing a BGR color, with each component in the range 0–255.

    Returns
    -------
    str
        A string representing the color in `#rrggbb` RGB hex format.

    :raises ValueError: If the input is not a tuple of three integers.
    """
    b, g, r = bgr
    return f'#{r:02x}{g:02x}{b:02x}'

RANK_ORDER = {rank: i for i, (rank, _, _) in enumerate(RANKS)}
RANK_HEX = {rank: hexcode for rank, _, hexcode in RANKS}
RANK_TK_HEX = {rank: bgr_to_rgb_hex(bgr) for rank, bgr, _ in RANKS}

# --- ImageProcessor Thread ---
class ImageProcessor(threading.Thread):
    """
    Thread that continuously captures screenshots, detects pips, and signals when reroll conditions are met.

    This class runs as a daemon thread to perform background image processing tasks
    independently from the main application flow. It captures screen regions, processes
    them to detect pip counts or ranks, updates shared state safely using threading locks,
    and can signal the main reroll loop to stop based on detection results.

    Attributes
    ----------
    app : object
        Reference to the main application instance, used for interaction and callbacks.
    stop_event : threading.Event
        Event used to signal this thread to stop execution gracefully.
    current_rank_counts : dict
        Dictionary mapping ranks to their current detected counts.
    lock : threading.Lock
        Lock to synchronize access to shared data like rank counts.
    screen_capturer : ScreenCapture
        Instance of the ScreenCapture class used for optimized screenshot capture.
    """
    def __init__(self, app_ref):
        """
        Initializes the ImageProcessor thread.
    
        Parameters
        ----------
        app_ref : object
            Reference to the main application instance.
    
        :rtype: None
        """
        super().__init__(daemon=True) # Daemon thread exits when main program exits
        self.app = app_ref # Reference to the main app instance
        self.stop_event = threading.Event() # Event to signal this thread to stop
        self.current_rank_counts = {rank: 0 for rank, _, _ in RANKS}
        self.lock = threading.Lock() # Lock for safely accessing shared data (rank counts)
        self.screen_capturer = ScreenCapture() # Instantiate the optimized screen capturer

    def run(self):
        """
        Main loop for continuous image capturing and pip detection.
    
        This method runs in a dedicated daemon thread and performs the following:
        - Continuously captures screenshots of the defined game area.
        - Processes the captured images to detect and classify pips.
        - Updates shared rank counts with thread-safe locking.
        - Signals the main reroll loop to stop based on configurable stop conditions.
        - Updates the GUI asynchronously using Tkinter's `after` method.
        - Logs events if logging is enabled and conditions are met.
    
        The loop respects a polling delay and handles exceptions gracefully
        by logging errors and preventing tight looping on repeated failures.
    
        The thread will stop running when `stop_event` is set or when the stop
        conditions are satisfied and the main loop is signaled to stop.
    
        :rtype: None
        """
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
                            detected_objs,
                            self.current_rank_counts.copy(),
                            {
                                "min_quality": self.app.min_quality,
                                "min_objects": self.app.min_objects,
                                "stop_at_ss": self.app.stop_at_ss,
                                "tolerance": self.app.tolerance,
                                "object_tolerance": self.app.object_tolerance,
                                "click_delay_ms": self.app.click_delay_ms,
                                "post_reroll_delay_ms": self.app.post_reroll_delay_ms,
                                "image_poll_delay_ms": self.app.image_poll_delay_ms,
                                "game_area": self.app.game_area,
                                "chisel_button_pos": self.app.chisel_button_pos,
                                "buy_button_pos": self.app.buy_button_pos,
                            },
                            decision="StopConditionMet: Signalling reroll thread to suspend"
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
        """
        Retrieve a thread-safe copy of the latest detected rank counts.
    
        This method acquires a lock to safely access the shared rank counts dictionary
        and returns a copy to avoid race conditions.
    
        Returns
        -------
        dict
            A copy of the current rank counts mapping ranks to their detected counts.
    
        :rtype: dict[str, int]
        """
        with self.lock:
            return self.current_rank_counts.copy()

    def stop(self):
        """
        Signals the image processing thread to stop and releases resources.
    
        This method sets the internal stop event, which causes the thread's
        main loop to exit gracefully. It also closes the screen capturer,
        cleaning up any allocated GDI resources.
    
        :rtype: None
        """
        self.stop_event.set()
        self.screen_capturer.close() # Close the screen capturer resources

# --- Main PipReroller Application Class ---
class PipRerollerApp:
    """
    Main Tkinter application for the Pip Reroller macro.

    This class manages the graphical user interface (GUI), user input,
    configuration settings, and background worker threads for
    continuous image processing and reroll automation.

    It handles:
    - GUI layout and input widgets for user configuration.
    - Thread-safe communication with background image processing and reroll threads.
    - Event handling for keyboard and window actions.
    - Logging of detected objects and application events (optional).

    Attributes
    ----------
    root : tkinter.Tk
        The main Tkinter root window instance.
    game_area : tuple or None
        Bounding box defining the screen region for pip detection.
    chisel_button_pos : tuple or None
        Screen coordinates of the chisel button.
    buy_button_pos : tuple or None
        Screen coordinates of the buy button.
    preview_active : bool
        Whether the preview mode is active.
    running : bool
        Whether the reroll process is currently running.
    tolerance : int
        Color tolerance used for pip detection.
    stop_at_ss : int
        Minimum number of SS-rank pips required to stop rerolling.
    click_delay_ms : int
        Delay in milliseconds between simulated clicks.
    post_reroll_delay_ms : int
        Delay in milliseconds after each reroll before next action.
    object_tolerance : int
        Pixel tolerance for merging detected objects.
    image_poll_delay_ms : int
        Interval in milliseconds between image processing polls.
    min_quality : str
        Minimum pip rank quality to accept (e.g., "F", "SS").
    min_objects : int
        Minimum number of pips of minimum quality required to stop rerolling.
    game_window_title : tkinter.StringVar
        Title of the game window to capture.
    rank_counts : dict
        Current counts of detected pips by rank, updated by background thread.
    status_var : tkinter.StringVar
        Text variable for status label in the GUI.
    message_var : tkinter.StringVar
        Text variable for message label in the GUI.
    status_color : str
        Color hex code for status label.
    enable_logging : bool
        Flag to enable or disable event logging.
    log_buffer : list
        Buffer holding log entries before dumping to file.
    log_button : tkinter.Button or None
        Button widget to manually dump logs when logging is enabled.
    last_detected_objs : list
        Cache of last detected objects to prevent attribute errors.
    image_processor_thread : threading.Thread or None
        Background thread for image processing.
    reroll_loop_thread : threading.Thread or None
        Background thread managing reroll automation.
    preview_thread : threading.Thread or None
        Background thread for preview mode.
    stop_reroll_event : threading.Event
        Event to signal stopping the reroll automation.
    listener : pynput.keyboard.Listener
        Keyboard listener for hotkey handling.
    ahk : ahk.AHK
        AutoHotkey interface for sending inputs to the game.

    Methods
    -------
    __init__(root)
        Initializes the GUI, variables, threads, and event bindings.
    """
    def __init__(self, root):
        """
        Initialize the Pip Reroller application.

        Sets up the main window, GUI components, configuration variables,
        threading constructs, and event listeners. Also initializes optional
        logging mechanisms if enabled.

        Parameters
        ----------
        root : tkinter.Tk
            The main Tkinter window instance on which the application UI is built.

        :rtype: None
        """
        self.root = root
        self.root.title("Pip Reroller by Riri")
        self.root.geometry("440x550") # Increased height for new input field
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
        self.post_reroll_delay_ms = 250
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
            """
            Create a styled Tkinter Label with predefined foreground and background colors.
        
            Parameters
            ----------
            text : str
                The text to display on the label.
        
            Returns
            -------
            tkinter.Label
                A Tkinter Label widget configured with preset colors.
            """
            return tk.Label(root, text=text, fg=label_fg, bg="#222222")

        # Input fields
        frame_delay = tk.Frame(root, bg="#222222")
        frame_delay.pack(pady=(10, 0))
        delay_label = make_label("Click Delay (ms):")
        delay_label.pack(in_=frame_delay, side="left")
        Tooltip(delay_label, "Delay in milliseconds between simulated clicks.\nIncrease if the game lags or misses clicks.")
        self.click_delay_entry = Entry(frame_delay, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.click_delay_entry.pack(side="left", padx=(10, 0))
        self.click_delay_entry.insert(0, str(self.click_delay_ms))
        self.click_delay_entry.bind('<KeyRelease>', self.update_click_delay)

        frame_reroll_delay = tk.Frame(root, bg="#222222")
        frame_reroll_delay.pack(pady=(10, 0))
        post_reroll_delay_label = make_label("Post Reroll Delay (ms):")
        post_reroll_delay_label.pack(in_=frame_reroll_delay, side="left")
        Tooltip(post_reroll_delay_label, "Delay in milliseconds between rerolls.\nIncrease if the game doesn't return charms fast enough.")
        self.post_reroll_delay_entry = Entry(frame_reroll_delay, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.post_reroll_delay_entry.pack(side="left", padx=(10, 0))
        self.post_reroll_delay_entry.insert(0, str(self.post_reroll_delay_ms))
        self.post_reroll_delay_entry.bind('<KeyRelease>', self.update_post_reroll_delay)

        frame_poll_delay = tk.Frame(root, bg="#222222")
        frame_poll_delay.pack(pady=(10, 0))
        poll_label = make_label("Image Poll Delay (ms):")
        poll_label.pack(in_=frame_poll_delay, side="left")
        Tooltip(poll_label, "How often to check for pips (in milliseconds).\nLower values update faster but use more CPU.\nDecrease if the macro accidentally rerolls on a suspend condition.")
        self.image_poll_delay_entry = Entry(frame_poll_delay, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.image_poll_delay_entry.pack(side="left", padx=(10, 0))
        self.image_poll_delay_entry.insert(0, str(self.image_poll_delay_ms))
        self.image_poll_delay_entry.bind('<KeyRelease>', self.update_image_poll_delay)

        frame_tol = tk.Frame(root, bg="#222222")
        frame_tol.pack(pady=(10, 0))
        tol_label = make_label("Color Tolerance:")
        tol_label.pack(in_=frame_tol, side="left")
        Tooltip(tol_label, "How close a color must be to count as a match.\nIncrease if detection is unreliable.")
        self.tolerance_entry = Entry(frame_tol, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.tolerance_entry.pack(side="left", padx=(10, 0))
        self.tolerance_entry.insert(0, str(self.tolerance))
        self.tolerance_entry.bind('<KeyRelease>', self.update_tolerance)

        frame_obj_tol = tk.Frame(root, bg="#222222")
        frame_obj_tol.pack(pady=(10, 0))
        obj_tol_label = make_label("Object Tolerance (px):")
        obj_tol_label.pack(in_=frame_obj_tol, side="left")
        Tooltip(obj_tol_label, "How close detected objects must be (in pixels) to be merged as one pip.\nIncrease if pips are split into multiple boxes.")
        self.object_tolerance_entry = Entry(frame_obj_tol, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.object_tolerance_entry.pack(side="left", padx=(10, 0))
        self.object_tolerance_entry.insert(0, str(self.object_tolerance))
        self.object_tolerance_entry.bind('<KeyRelease>', self.update_object_tolerance)

        frame_stop = tk.Frame(root, bg="#222222")
        frame_stop.pack(pady=(10, 0))
        ss_label = tk.Label(frame_stop, text="Minimum SS:", fg=label_fg, bg="#222222")
        ss_label.pack(side="left")
        Tooltip(ss_label, "Minimum number of SS-rank pips required to stop rerolling.")
        self.stop_at_entry = Entry(frame_stop, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.stop_at_entry.pack(side="left", padx=5)
        self.stop_at_entry.insert(0, str(self.stop_at_ss))
        self.stop_at_entry.bind('<KeyRelease>', self.update_stop_at)

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
                """
                Logs a detection event with details about detected objects, counts, settings, and decisions.
            
                Each log entry includes a timestamp in UTC, the number of detected objects,
                their ranks and screen locations, the current rank counts, relevant settings,
                and the decision made by the application. Entries are appended to the internal
                log buffer.
            
                Parameters
                ----------
                objects : list of dict
                    List of detected objects, each containing keys like 'rank' and 'rect' (bounding box).
                rank_counts : dict
                    Dictionary mapping pip ranks to their counts at the time of logging.
                settings : dict
                    Dictionary of current application settings relevant to the detection.
                decision : str
                    Description of the decision or event that triggered the log entry.
            
                :rtype: None
                """
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
                    f"{now} | Objects Detected: {total_objs} | Object Locations: {obj_str} | Counts: {counts_str} | "
                    f"Settings: {settings_str} | Decision: {decision}"
                )
                self.log_buffer.append(log_line)
        
            def dump_logs(self):
                """
                Writes all buffered log entries to a timestamped text file and clears the buffer.
            
                If no logs are present, updates the GUI message variable to indicate there are no logs to write.
                After successfully writing the logs, updates the message variable with the filename.
            
                The log file is saved in the current working directory with a name including the current date and time.
            
                :rtype: None
                """
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

            self.log_count_label = tk.Label(
                root, text="Logs ready to dump: 0", 
                bg="#222222", fg="#ffcc00", font=("Arial", 9, "bold")
            )
            self.log_count_label.place(relx=1.0, y=5, anchor='ne')  # top right
        
            def update_log_count_label():
                """
                Periodically updates the GUI label displaying the number of logs currently buffered.
            
                This function schedules itself to run every 1000 milliseconds (1 second)
                to refresh the label text, reflecting the latest count of logs waiting to be written.
            
                :rtype: None
                """
                # Update label text with current number of logs in buffer
                count = len(self.log_buffer)
                self.log_count_label.config(text=f"Logs ready to dump: {count}")
        
                # Schedule to run again after 1000 ms (1 second)
                root.after(1000, update_log_count_label)
        
            # Start the periodic update loop
            update_log_count_label()
        
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
        """
        Handle graceful shutdown when the application window is closed.
    
        This method stops background threads such as the image processor and keyboard listener,
        waits briefly for the image processor thread to finish, signals the main reroll loop to stop,
        and finally destroys the main Tkinter window.
    
        :rtype: None
        """
        self.stop_running_async() # Ensure main reroll loop stops
        if self.image_processor_thread and self.image_processor_thread.is_alive():
            self.image_processor_thread.stop() # Tell image processor to stop and cleanup
            self.image_processor_thread.join(timeout=1.0) # Wait for it to finish
        self.listener.stop() # Stop keyboard listener
        self.root.destroy()

    def select_quality(self, rank):
        """
        Update the selected minimum pip quality in the GUI.
    
        Adjusts the internal `min_quality` state and visually updates the quality selection buttons,
        highlighting the selected rank and resetting the others to default appearance.
    
        Parameters
        ----------
        rank : str
            The rank string to select as the minimum quality (e.g., "F", "SS").
    
        :rtype: None
        """
        self.min_quality = rank
        for r, btn in self.quality_buttons.items():
            if r == rank:
                btn.config(relief="sunken", bg=RANK_TK_HEX[r], fg="#222222")
            else:
                btn.config(relief="raised", bg="#333333", fg="#ffffff")

    def update_tolerance(self, event=None):
        """
        Update the color tolerance value based on user input from the GUI.
    
        Reads the value from the tolerance entry widget, validates that it is an integer between 0 and 255,
        and updates the internal `tolerance` attribute accordingly. Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            The event object from the GUI, not used in processing.
    
        :rtype: None
        """
        try:
            val = int(self.tolerance_entry.get())
            if 0 <= val <= 255:
                self.tolerance = val
        except ValueError:
            pass

    def update_stop_at(self, event=None):
        """
        Update the minimum SS-rank pip count required to stop rerolling based on GUI input.
    
        Reads the value from the stop_at entry widget, validates that it is a non-negative integer,
        and updates the internal `stop_at_ss` attribute accordingly. Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            The event object from the GUI, not used in processing.
    
        :rtype: None
        """
        try:
            val = int(self.stop_at_entry.get())
            if val >= 0:
                self.stop_at_ss = val
        except ValueError:
            pass

    def update_min_objects(self, event=None):
        """
        Update the minimum number of objects required to stop rerolling from GUI input.
    
        Reads the value from the `min_objects_entry` widget, validates that it is an integer
        greater than or equal to 1, and updates the internal `min_objects` attribute.
        Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            Event object from the GUI callback, not used.
    
        :rtype: None
        """
        try:
            val = int(self.min_objects_entry.get())
            if val >= 1:
                self.min_objects = val
        except ValueError:
            pass

    def update_click_delay(self, event=None):
        """
        Update the click delay (in milliseconds) from GUI input.
    
        Reads the value from the `click_delay_entry` widget, validates that it is a non-negative integer,
        and updates the internal `click_delay_ms` attribute.
        Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            Event object from the GUI callback, not used.
    
        :rtype: None
        """
        try:
            val = int(self.click_delay_entry.get())
            if val >= 0:
                self.click_delay_ms = val
        except ValueError:
            pass

    def update_post_reroll_delay(self, event=None):
        """
        Update the post-reroll delay (in milliseconds) from GUI input.
    
        Reads the value from the `post_reroll_delay_entry` widget, validates that it is a non-negative integer,
        and updates the internal `post_reroll_delay_ms` attribute.
        Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            Event object from the GUI callback, not used.
    
        :rtype: None
        """
        try:
            val = int(self.post_reroll_delay_entry.get())
            if val >= 0:
                self.post_reroll_delay_ms = val
        except ValueError:
            pass

    def update_image_poll_delay(self, event=None):
        """
        Update the image polling delay (in milliseconds) from GUI input.
    
        Reads the value from the `image_poll_delay_entry` widget, validates that it is a non-negative integer,
        and updates the internal `image_poll_delay_ms` attribute.
        Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            Event object from the GUI callback, not used.
    
        :rtype: None
        """
        try:
            val = int(self.image_poll_delay_entry.get())
            if val >= 0:
                self.image_poll_delay_ms = val
        except ValueError:
            pass

    def update_object_tolerance(self, event=None):
        """
        Update the object merging tolerance (in pixels) from GUI input.
    
        Reads the value from the `object_tolerance_entry` widget, validates that it is a non-negative integer,
        and updates the internal `object_tolerance` attribute.
        Invalid inputs are ignored.
    
        Parameters
        ----------
        event : tkinter.Event, optional
            Event object from the GUI callback, not used.
    
        :rtype: None
        """
        try:
            val = int(self.object_tolerance_entry.get())
            if val >= 0:
                self.object_tolerance = val
        except ValueError:
            pass

    def start_area_selection(self):
        """
        Initiate the screen area selection process for pip detection.
    
        Minimizes the main application window and creates a transparent, fullscreen overlay
        window with a crosshair cursor. This overlay captures mouse events to allow the user
        to drag and select a rectangular area of the screen for detection.
    
        :rtype: None
        """
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
        """
        Handle the beginning of a mouse drag event during area selection.
    
        Records the initial cursor position in screen coordinates and places a minimal
        selection rectangle at the drag start location.
    
        Parameters
        ----------
        event : tkinter.Event
            The mouse button press event triggering the drag start.
    
        :rtype: None
        """
        self.drag_start = (event.x_root, event.y_root)
        self.selection_rect.place(x=event.x, y=event.y, width=1, height=1)

    def on_drag_motion(self, event):
        """
        Handle mouse movement while dragging to select an area.
    
        Updates the size and position of the selection rectangle based on
        the current cursor position relative to the drag start point.
    
        Parameters
        ----------
        event : tkinter.Event
            The mouse motion event during the drag.
    
        :rtype: None
        """
        x1, y1 = self.drag_start
        x2, y2 = event.x_root, event.y_root
        x, y = self.selection_overlay.winfo_rootx(), self.selection_overlay.winfo_rooty()
        self.selection_rect.place(x=min(x1, x2) - x, y=min(y1, y2) - y,
                                  width=abs(x1 - x2), height=abs(y1 - y2))

    def on_drag_end(self, event):
        """
        Handle the end of the drag event to finalize the selected screen area.
    
        Calculates the bounding box from the drag start and end coordinates,
        stores it in `game_area`, destroys the overlay window, restores the main window,
        and updates the GUI message to confirm the selection.
    
        Parameters
        ----------
        event : tkinter.Event
            The mouse button release event signaling the end of the drag.
    
        :rtype: None
        """
        x1, y1 = self.drag_start
        x2, y2 = event.x_root, event.y_root
        self.game_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.selection_overlay.destroy()
        self.root.deiconify() # Restore main window
        self.message_var.set("Game area set.")

    def start_chisel_button_selection(self):
        """
        Initiate the selection process for the 'Chisel' button position.
    
        Minimizes the main window and launches an overlay allowing the user to
        click and set the screen coordinates for the chisel button.
    
        :rtype: None
        """
        self._start_button_selection("chisel")

    def start_buy_button_selection(self):
        """
        Initiate the selection process for the 'Buy' button position.
    
        Minimizes the main window and launches an overlay allowing the user to
        click and set the screen coordinates for the buy button.
    
        :rtype: None
        """
        self._start_button_selection("buy")

    def _start_button_selection(self, button_type):
        """
        Helper method to create a fullscreen overlay for button position selection.
    
        The overlay is semi-transparent with a crosshair cursor and prompts the user
        to click to set either the "chisel" or "buy" button position, depending on the argument.
    
        Parameters
        ----------
        button_type : str
            The type of button to select, expected values are "chisel" or "buy".
    
        :rtype: None
        """
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
        """
        Set the screen coordinates for the specified button based on user click.
    
        Stores the (x_root, y_root) screen coordinates for the given button type,
        destroys the selection overlay, restores the main window, and updates the GUI message.
    
        Parameters
        ----------
        event : tkinter.Event
            The mouse click event containing the cursor position.
        button_type : str
            The button type being set, either "chisel" or "buy".
        overlay : tkinter.Toplevel
            The overlay window used for selection, which will be destroyed.
    
        :rtype: None
        """
        pos = (event.x_root, event.y_root)
        if button_type == "chisel":
            self.chisel_button_pos = pos
        else:
            self.buy_button_pos = pos
        overlay.destroy()
        self.root.deiconify()
        self.message_var.set(f"{button_type.capitalize()} button set at {pos}")

    def on_key_press(self, key):
        """
        Handle keyboard key presses, toggling reroller on/off when F5 is pressed.
    
        If the F5 key is detected, starts the rerolling loop if it is not running,
        otherwise stops the running loop.
    
        Parameters
        ----------
        key : pynput.keyboard.Key
            The key event to handle.
    
        :rtype: None
        """
        if key == keyboard.Key.f5:
            if not self.running:
                self.start_running_async()
            else:
                self.stop_running_async()

    def start_running_async(self):
        """
        Starts the reroller automation asynchronously.
    
        Validates that required settings (game area, chisel and buy button positions)
        are set, activates the target game window, clears stop signals, and
        launches background threads for image processing and the reroll loop.
    
        If any validation fails or the game window cannot be found, sets an appropriate
        error message in the GUI and aborts starting.
    
        :rtype: None
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
        """
        Signals all active automation threads to stop and updates GUI status.
    
        Sets the internal running flag to False, updates the GUI status label,
        sets the stop event for the reroll loop thread, and signals the image
        processor thread to stop if it is active.
    
        :rtype: None
        """
        self.running = False
        self.update_status(False)
        self.stop_reroll_event.set() # Signal the reroll loop to stop
        if self.image_processor_thread and self.image_processor_thread.is_alive():
            self.image_processor_thread.stop() # Signal the image processor to stop

    def update_status(self, running):
        """
        Update the status label in the GUI.
    
        Changes the status text and color based on whether the reroller is running.
    
        :param bool running: True if running, False if suspended.
        :rtype: None
        """
        if running:
            self.status_var.set("Status: Running")
            self.status_label.config(fg="#55ff55")
        else:
            self.status_var.set("Status: Suspended")
            self.status_label.config(fg="#ff5555")

    def update_rank_counts_gui(self, detected_objs):
        """
        Update the rank count display in the GUI.
    
        Called from the ImageProcessor thread via root.after() to safely update GUI elements.
        Updates internal counts and refreshes the Tkinter StringVars to reflect detected pip counts.
    
        :param list detected_objs: List of detected pip objects with 'rank' keys.
        :rtype: None
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
        """
        Toggle the real-time bounding box preview window.
    
        Starts a background thread to capture and display pip detections live.
        If the preview is already active, stops it.
    
        :rtype: None
        """
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
        Background loop for live preview of pip detection.
    
        Continuously captures screenshots of the game area, detects pips,
        draws bounding boxes with labels, and displays them in an OpenCV window.
        Runs until preview is deactivated.
    
        :rtype: None
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
        Detect and classify pip objects within an image frame.
    
        Processes the input frame by applying color masks for each rank,
        performs morphological operations to clean the mask,
        detects contours, filters by area, merges close rectangles,
        and returns a sorted list of detected pip objects with their rank and bounding box.
    
        :param numpy.ndarray frame: The image frame to process (BGR color).
        :return: List of detected objects, each a dict with keys 'rank', 'rect', and 'cv2color'.
        :rtype: list of dict
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
        Create a binary mask of pixels within color tolerance of a target BGR color.
    
        Computes a mask where pixels in the frame are within the specified tolerance
        of the target color, across all BGR channels.
    
        :param numpy.ndarray frame: The image frame (BGR).
        :param numpy.ndarray color_bgr: Target BGR color as a NumPy array.
        :param int tolerance: Maximum allowed absolute difference per channel.
        :return: Binary mask image with 255 where pixels match, 0 elsewhere.
        :rtype: numpy.ndarray
        """
        # Calculate absolute difference between frame pixels and target color
        diff = np.abs(frame.astype(np.int16) - color_bgr)
        # Create mask where all color channels are within tolerance
        mask = np.all(diff <= tolerance, axis=2).astype(np.uint8) * 255
        return mask

    def merge_rectangles(self, rects, max_distance):
        """
        Merge rectangles that are close to each other into combined bounding boxes.
    
        Useful for merging fragmented detections of the same object by expanding bounding boxes
        that are within the specified max_distance of each other.
    
        :param list rects: List of rectangles as (x, y, w, h) tuples.
        :param float max_distance: Maximum distance between rectangles to consider merging.
        :return: List of merged rectangles as (x, y, w, h) tuples.
        :rtype: list of tuples
        """
        merged = []
        used = [False] * len(rects)

        def rect_distance(r1, r2):
            """
            Calculate the shortest Euclidean distance between the edges of two rectangles.
        
            Each rectangle is defined as (x, y, width, height). The distance is zero if the rectangles overlap
            or touch. Otherwise, it returns the straight-line distance between the closest edges.
        
            :param tuple r1: First rectangle (x, y, w, h).
            :param tuple r2: Second rectangle (x, y, w, h).
            :return: Euclidean distance between closest points of the rectangles.
            :rtype: float
            """
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
        """Simulates a mouse click at the specified screen coordinates using AutoHotkey (AHK).
    
        Moves the mouse instantly to (x, y) and performs a left-click (down and up).
        
        :param int x: The x-coordinate on the screen.
        :param int y: The y-coordinate on the screen.
        """
        self.ahk.mouse_move(x, y, speed=0) # Instant move
        self.ahk.click() # Left click down & up

    def reroll_loop(self):
        """
        Main automation loop for performing the reroll clicks with responsiveness to stop signals.
    
        This loop continuously performs the following steps until a stop event is signaled:
        - Checks for a stop event to exit early.
        - Logs detected objects if logging is enabled.
        - Clicks the 'Chisel' button and waits a configured delay.
        - Checks for stop event again to allow immediate cancellation.
        - Clicks the 'Buy' button and waits a configured delay.
        - Checks for stop event again.
        - Waits a post-reroll delay to prevent game state glitches.
        - Updates the GUI message with the current detected pip counts.
        - Waits briefly to throttle the loop and let image processing catch up.
    
        The function uses thread-safe event waits to react quickly to stop signals from other threads.
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
            if self.enable_logging and detected_objs:
                self.log_event(
                    detected_objs,
                    self.image_processor_thread.get_current_rank_counts(),
                    {
                        "min_quality": self.min_quality,
                        "min_objects": self.min_objects,
                        "stop_at_ss": self.stop_at_ss,
                        "tolerance": self.tolerance,
                        "object_tolerance": self.object_tolerance,
                        "click_delay_ms": self.click_delay_ms,
                        "post_click_delay": self.post_click_delay_ms,
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

            # Post-click safety delay
            # Prevents inventory shift issue where the charm below moves up temporarily.
            # This delay gives the game time to fully update/return the charm slot.
            time.sleep(self.post_reroll_delay_ms / 1000)

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
    """
    Creates a tooltip for a given Tkinter widget that appears after a delay
    when the mouse hovers over the widget.

    The tooltip follows the mouse cursor while it is over the widget
    and disappears when the mouse leaves.
    """
    def __init__(self, widget, text, delay=500):
        """
        Initializes the Tooltip.

        :param widget: The Tkinter widget to attach the tooltip to.
        :param text: The text to display inside the tooltip.
        :param delay: Delay in milliseconds before showing the tooltip after mouse enters the widget.
        """
        self.widget = widget
        self.text = text
        self.delay = delay  # milliseconds
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<Motion>", self.move)

    def schedule(self, event=None):
        """
        Schedule the tooltip to be shown after the specified delay.
        Cancels any previously scheduled show event.
        """
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        """
        Cancel any scheduled tooltip show event if it exists.
        """
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self, event=None):
        """
        Display the tooltip near the widget, unless it's already visible
        or there is no text to show.
        Positions the tooltip offset slightly from the widget or text insertion point.
        """
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
        """
        Hide and destroy the tooltip window, and cancel any scheduled show events.
        """
        self.unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def move(self, event):
        """
        Move the tooltip window to follow the mouse cursor,
        offset slightly from the cursor position.
        """
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
