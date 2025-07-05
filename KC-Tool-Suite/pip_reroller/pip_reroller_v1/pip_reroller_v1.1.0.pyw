"""
Pip Reroller v1.1.0

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
- Built with OpenCV, tkinter, PIL, pynput, and ahk.

MIT License

Copyright (c) 2025 alina (Riri)
Copyright (c) 2025 bobby

Some detection and selection logic adapted from iamnotbobby (MIT licensed).

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
from PIL import ImageGrab
from pynput import keyboard  # for F5 listening
from ahk import AHK  # AHK for clicking

# Class ranks, order, and their colors (BGR for OpenCV, HEX for Tkinter)
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
    b, g, r = bgr
    return f'#{r:02x}{g:02x}{b:02x}'

RANK_ORDER = {rank: i for i, (rank, _, _) in enumerate(RANKS)}
RANK_HEX = {rank: hexcode for rank, _, hexcode in RANKS}
RANK_TK_HEX = {rank: bgr_to_rgb_hex(bgr) for rank, bgr, _ in RANKS}

class PipRerollerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pip Reroller by Riri")
        self.root.geometry("440x540")
        self.root.configure(bg="#222222")
        self.root.attributes("-topmost", True)

        self.game_area = None
        self.chisel_button_pos = None
        self.buy_button_pos = None
        self.preview_active = False
        self.running = False

        self.tolerance = 10
        self.stop_at_ss = 0
        self.click_delay_ms = 10
        self.object_tolerance = 10

        self.min_quality = "F"
        self.min_objects = 1

        self.rank_counts = {rank: 0 for rank, _, _ in RANKS}

        self.status_var = StringVar(value="Status: Suspended")
        self.message_var = StringVar(value="")
        self.status_color = "#ff5555"

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
        make_label("Color Tolerance:").pack(in_=frame_tol, side="left")
        self.tolerance_entry = Entry(frame_tol, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.tolerance_entry.pack(side="left", padx=(10, 0))
        self.tolerance_entry.insert(0, str(self.tolerance))
        self.tolerance_entry.bind('<KeyRelease>', self.update_tolerance)

        frame_stop = tk.Frame(root, bg="#222222")
        frame_stop.pack(pady=(10, 0))
        tk.Label(frame_stop, text="Minimum SS:", fg=label_fg, bg="#222222").pack(side="left")
        self.stop_at_entry = Entry(frame_stop, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.stop_at_entry.pack(side="left", padx=5)
        self.stop_at_entry.insert(0, str(self.stop_at_ss))
        self.stop_at_entry.bind('<KeyRelease>', self.update_stop_at)

        frame_delay = tk.Frame(root, bg="#222222")
        frame_delay.pack(pady=(10, 0))
        make_label("Delay Between Clicks (ms):").pack(in_=frame_delay, side="left")
        self.click_delay_entry = Entry(frame_delay, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.click_delay_entry.pack(side="left", padx=(10, 0))
        self.click_delay_entry.insert(0, str(self.click_delay_ms))
        self.click_delay_entry.bind('<KeyRelease>', self.update_click_delay)

        frame_obj_tol = tk.Frame(root, bg="#222222")
        frame_obj_tol.pack(pady=(10, 0))
        make_label("Object Tolerance (px):").pack(in_=frame_obj_tol, side="left")
        self.object_tolerance_entry = Entry(frame_obj_tol, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.object_tolerance_entry.pack(side="left", padx=(10, 0))
        self.object_tolerance_entry.insert(0, str(self.object_tolerance))
        self.object_tolerance_entry.bind('<KeyRelease>', self.update_object_tolerance)

        # Minimum objects input
        frame_minobjs = tk.Frame(root, bg="#222222")
        frame_minobjs.pack(pady=(13, 0))
        Label(frame_minobjs, text="Minimum Objects:", fg=label_fg, bg="#222222").pack(side="left")
        self.min_objects_entry = Entry(frame_minobjs, bg=entry_bg, fg=entry_fg, insertbackground='white', width=6)
        self.min_objects_entry.pack(side="left", padx=(10,0))
        self.min_objects_entry.insert(0, str(self.min_objects))
        self.min_objects_entry.bind('<KeyRelease>', self.update_min_objects)

        # Minimum Quality row
        frame_quality = tk.Frame(root, bg="#222222")
        frame_quality.pack(pady=(20, 0))
        Label(frame_quality, text="Minimum Quality", fg=label_fg, bg="#222222", font=("Arial", 12, "bold")).pack()

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

    def select_quality(self, rank):
        self.min_quality = rank
        for r, btn in self.quality_buttons.items():
            if r == rank:
                btn.config(relief="sunken", bg=RANK_TK_HEX[r], fg="#222222")
            else:
                btn.config(relief="raised", bg="#333333", fg="#ffffff")

    def update_tolerance(self, event=None):
        try:
            val = int(self.tolerance_entry.get())
            if 0 <= val <= 255:
                self.tolerance = val
        except ValueError:
            pass

    def update_stop_at(self, event=None):
        try:
            val = int(self.stop_at_entry.get())
            if val >= 1:
                self.stop_at_ss = val
        except ValueError:
            pass

    def update_min_objects(self, event=None):
        try:
            val = int(self.min_objects_entry.get())
            if val >= 1:
                self.min_objects = val
        except ValueError:
            pass

    def update_click_delay(self, event=None):
        try:
            val = int(self.click_delay_entry.get())
            if val >= 0:
                self.click_delay_ms = val
        except ValueError:
            pass

    def update_object_tolerance(self, event=None):
        try:
            val = int(self.object_tolerance_entry.get())
            if val >= 0:
                self.object_tolerance = val
        except ValueError:
            pass

    def start_area_selection(self):
        self.root.iconify()
        self.selection_overlay = tk.Toplevel()
        self.selection_overlay.attributes('-fullscreen', True, '-alpha', 0.2, '-topmost', True)
        self.selection_overlay.configure(bg='blue', cursor='crosshair')
        self.selection_rect = tk.Frame(self.selection_overlay, bg='red', highlightthickness=1,
                                       highlightbackground='white')
        self.selection_overlay.bind('<Button-1>', self.on_drag_start)
        self.selection_overlay.bind('<B1-Motion>', self.on_drag_motion)
        self.selection_overlay.bind('<ButtonRelease-1>', self.on_drag_end)

    def on_drag_start(self, event):
        self.drag_start = (event.x_root, event.y_root)
        self.selection_rect.place(x=event.x, y=event.y, width=1, height=1)

    def on_drag_motion(self, event):
        x1, y1 = self.drag_start
        x2, y2 = event.x_root, event.y_root
        x, y = self.selection_overlay.winfo_rootx(), self.selection_overlay.winfo_rooty()
        self.selection_rect.place(x=min(x1, x2) - x, y=min(y1, y2) - y,
                                  width=abs(x1 - x2), height=abs(y1 - y2))

    def on_drag_end(self, event):
        x1, y1 = self.drag_start
        x2, y2 = event.x_root, event.y_root
        self.game_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.selection_overlay.destroy()
        self.root.deiconify()
        self.message_var.set("Game area set.")

    def start_chisel_button_selection(self):
        self._start_button_selection("chisel")

    def start_buy_button_selection(self):
        self._start_button_selection("buy")

    def _start_button_selection(self, button_type):
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
        pos = (event.x_root, event.y_root)
        if button_type == "chisel":
            self.chisel_button_pos = pos
        else:
            self.buy_button_pos = pos
        overlay.destroy()
        self.root.deiconify()
        self.message_var.set(f"{button_type.capitalize()} button set at {pos}")

    def on_key_press(self, key):
        if key == keyboard.Key.f5:
            if not self.running:
                self.start_running()
            else:
                self.stop_running()

    def start_running(self):
        if self.game_area is None:
            self.message_var.set("Please select area first.")
            return
        if self.chisel_button_pos is None:
            self.message_var.set("Please set Chisel Button first.")
            return
        if self.buy_button_pos is None:
            self.message_var.set("Please set Buy Button first.")
            return

        self.message_var.set("")
        self.running = True
        self.update_status(True)
        threading.Thread(target=self.running_loop, daemon=True).start()

    def stop_running(self):
        self.running = False
        self.update_status(False)

    def update_status(self, running):
        if running:
            self.status_var.set("Status: Running")
            self.status_label.config(fg="#55ff55")
        else:
            self.status_var.set("Status: Suspended")
            self.status_label.config(fg="#ff5555")

    def update_rank_counts(self, detected_objs):
        # Reset
        for rank in self.rank_count_vars:
            self.rank_counts[rank] = 0
        # Count
        for obj in detected_objs:
            self.rank_counts[obj['rank']] += 1
        # Update GUI
        for rank in self.rank_count_vars:
            self.rank_count_vars[rank].set(str(self.rank_counts[rank]))

    def start_preview(self):
        if self.game_area is None:
            self.message_var.set("Please select area first.")
            return

        if self.preview_active:
            self.preview_active = False
            return

        self.preview_active = True
        threading.Thread(target=self.preview_loop, daemon=True).start()

    def preview_loop(self):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        cv2.namedWindow("BBox Preview", cv2.WINDOW_AUTOSIZE)
        cv2.setWindowProperty("BBox Preview", cv2.WND_PROP_TOPMOST, 1)

        while self.preview_active:
            if self.game_area is None:
                time.sleep(0.2)
                continue

            screenshot = ImageGrab.grab(bbox=self.game_area)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            detected_objs = self.detect_and_classify(frame)
            self.update_rank_counts(detected_objs)
            debug_frame = frame.copy()
            for obj in detected_objs:
                x, y, w, h = obj['rect']
                color = obj['cv2color']
                cv2.rectangle(debug_frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(debug_frame, obj['rank'], (x+2, y+18), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow("BBox Preview", debug_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.preview_active = False
                break

        cv2.destroyAllWindows()

    def detect_and_classify(self, frame):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        detected = []
        for rank, bgr, _ in RANKS:
            mask = self.rank_mask(frame, np.array(bgr), self.tolerance)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rects = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 1]
            merged_rects = self.merge_rectangles(rects, self.object_tolerance)
            for rect in merged_rects:
                detected.append({
                    "rank": rank,
                    "rect": rect,
                    "cv2color": bgr
                })
        # Sort by rank order (highest first)
        detected.sort(key=lambda o: -RANK_ORDER[o['rank']])
        return detected

    def rank_mask(self, frame, color_bgr, tolerance):
        # color BGR, expects numpy array
        diff = np.abs(frame.astype(np.int16) - color_bgr)
        mask = np.all(diff <= tolerance, axis=2).astype(np.uint8) * 255
        return mask

    def merge_rectangles(self, rects, max_distance):
        merged = []
        used = [False] * len(rects)

        def rect_distance(r1, r2):
            x1, y1, w1, h1 = r1
            x2, y2, w2, h2 = r2

            left = x2 + w2 < x1
            right = x1 + w1 < x2
            above = y2 + h2 < y1
            below = y1 + h1 < y2

            if right:
                dx = x2 - (x1 + w1)
            elif left:
                dx = x1 - (x2 + w2)
            else:
                dx = 0

            if below:
                dy = y2 - (y1 + h1)
            elif above:
                dy = y1 - (y2 + h2)
            else:
                dy = 0

            return np.hypot(dx, dy)

        for i, r in enumerate(rects):
            if used[i]:
                continue
            x, y, w, h = r
            merged_rect = [x, y, x + w, y + h]
            used[i] = True

            for j in range(i + 1, len(rects)):
                if used[j]:
                    continue
                dist = rect_distance(r, rects[j])
                if dist <= max_distance:
                    rx, ry, rw, rh = rects[j]
                    merged_rect[0] = min(merged_rect[0], rx)
                    merged_rect[1] = min(merged_rect[1], ry)
                    merged_rect[2] = max(merged_rect[2], rx + rw)
                    merged_rect[3] = max(merged_rect[3], ry + rh)
                    used[j] = True

            merged.append((merged_rect[0], merged_rect[1],
                           merged_rect[2] - merged_rect[0],
                           merged_rect[3] - merged_rect[1]))
        return merged

    def click_at(self, x, y):
        # Using ahk to click (move, click left down & up)
        self.ahk.mouse_move(x, y, speed=0)  # instant move
        self.ahk.click()  # left click down & up with default timing

    def running_loop(self):
        while self.running:
            screenshot = ImageGrab.grab(bbox=self.game_area)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            detected_objs = self.detect_and_classify(frame)
            self.update_rank_counts(detected_objs)
            # Apply min quality filter
            min_rank_idx = RANK_ORDER[self.min_quality]
            filtered_objs = [obj for obj in detected_objs if RANK_ORDER[obj['rank']] >= min_rank_idx]
            ss_objs = [obj for obj in detected_objs if obj['rank'] == "SS"]

            if self.stop_at_ss > 0:
                should_stop = (len(filtered_objs) >= self.min_objects and len(ss_objs) >= self.stop_at_ss)
            else:
                should_stop = (len(filtered_objs) >= self.min_objects)

            if should_stop:
                self.message_var.set(
                    f"Min: {self.min_quality} x{self.min_objects}" +
                    (f", SS: {self.stop_at_ss}" if self.stop_at_ss > 0 else "") +
                    " met. Stopping."
                )
                self.running = False
                self.update_status(False)
                break
            else:
                self.click_at(*self.chisel_button_pos)
                time.sleep(self.click_delay_ms / 1000)
                self.click_at(*self.buy_button_pos)
                time.sleep(self.click_delay_ms / 1000)
                self.message_var.set(
                    f"Detected: {len(filtered_objs)} ≥{self.min_quality}" +
                    (f", {len(ss_objs)} SS" if self.stop_at_ss > 0 else "") +
                    ". Rolling..."
                )
            time.sleep(0.1)

if __name__ == '__main__':
    root = tk.Tk()
    app = PipRerollerApp(root)
    root.mainloop()
