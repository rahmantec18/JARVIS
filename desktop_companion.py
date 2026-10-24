"""
J.A.R.V.I.S. Desktop Floating Companion HUD
A lightweight, frameless, draggable, always-on-top Windows desktop widget.
Enables instant voice & text directives even when any application (e.g. WhatsApp) is active.

Features:
- Dual Modes:
  1. Compact Minimized Floating Icon (64x64 px glowing Arc Reactor / Mic orb)
  2. Expanded Full HUD Bar (320x76 px command console)
- Seamless Drag & Drop anywhere on screen with position persistence (hud_state.json)
- Live Voice Recognition: Click the mic/icon and speak commands ("Open WhatsApp", "Mute volume", etc.)
- Fast offline speech synthesis (pyttsx3) for spoken confirmations
- Topmost keep-alive: Stays visible over WhatsApp, Chrome, and all Windows apps
"""
import os
import sys
import re
import json
import time
import threading
import urllib.request
import urllib.error
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

try:
    import pystray
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JARVIS_Companion"


def is_start_with_windows_enabled() -> bool:
    if not HAS_WINREG:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False


def set_start_with_windows(enable: bool):
    if not HAS_WINREG:
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            script_path = str(Path(__file__).resolve())
            pythonw = str(Path(sys.executable).parent / "pythonw.exe")
            if not Path(pythonw).exists():
                pythonw = str(Path(sys.executable))
            cmd = f'"{pythonw}" "{script_path}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass

# Single-Instance Enforcement to avoid duplicate pop-up windows
_instance_mutex = None
try:
    import ctypes
    _instance_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "JarvisCompanionHUD_SingleInstance_Mutex_2026")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        print("[i] J.A.R.V.I.S. Floating Companion HUD is already active.")
        sys.exit(0)
except Exception:
    pass

# Speech Recognition & TTS
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    sr = None
    HAS_SR = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    pyttsx3 = None
    HAS_TTS = False

BACKEND_URL = "http://127.0.0.1:8000/api/chat"
DESKTOP_AGENT_URL = "http://127.0.0.1:8001/api/action"
CONFIG_FILE = Path(__file__).parent / "hud_state.json"


def speak_async(text: str):
    """Speak text asynchronously using Windows SAPI offline TTS without blocking."""
    if not HAS_TTS or not text:
        return

    def _worker():
        try:
            clean = re.sub(r'[*_`#\[\]\(\)]', '', text)
            # Take the first sentence or up to 100 chars
            clean = clean.split('\n')[0].split('. ')[0].strip()
            if not clean:
                return
            if len(clean) > 100:
                clean = clean[:100] + "..."
            engine = pyttsx3.init()
            engine.setProperty('rate', 190)
            engine.setProperty('volume', 1.0)
            engine.say(clean)
            engine.runAndWait()
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


class JarvisCompanionHUD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. Companion")
        self.root.overrideredirect(True)  # Frameless
        self.root.attributes("-topmost", True)  # Always on top

        # Windows Transparent Color Support
        self.transparent_color = "#010101"
        try:
            self.root.wm_attributes("-transparentcolor", self.transparent_color)
        except Exception:
            self.transparent_color = "#050b14"

        self.root.configure(bg=self.transparent_color)

        # State Variables
        self.mode = "mini"  # "mini" or "expanded"
        self.is_listening = False
        self.state = "idle"  # "idle", "listening", "processing", "success", "error"
        self.pulse_phase = 0
        self.pulse_timer = None
        self.reset_timer = None
        self.bubble_window = None
        self.bubble_hide_timer = None
        self.is_hovered = False
        self._mini_photo = None

        # Drag tracking
        self._drag_data = {"x": 0, "y": 0, "win_x": 0, "win_y": 0, "moved": False}

        # Speech Recognizer instance
        self.recognizer = sr.Recognizer() if HAS_SR else None
        if self.recognizer:
            self.recognizer.energy_threshold = 280
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8

        # Load Saved Position & Mode
        self._load_state()

        # Build UI Components
        self._build_mini_ui()
        self._build_expanded_ui()

        # Initial Mode Setup
        if self.mode == "mini":
            self._show_mini_mode()
        else:
            self._show_expanded_mode()

        # Initialize System Tray
        self._init_system_tray()

        # Keepalive for Topmost persistence
        self._ensure_topmost()

    # -------------------------------------------------------------
    # State & Config Persistence
    # -------------------------------------------------------------
    def _load_state(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        default_x = screen_w - 90
        default_y = screen_h - 180

        self.saved_x = default_x
        self.saved_y = default_y
        self.mode = "mini"

        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.saved_x = max(10, min(screen_w - 80, data.get("x", default_x)))
                self.saved_y = max(10, min(screen_h - 80, data.get("y", default_y)))
                self.mode = data.get("mode", "mini")
            except Exception:
                pass

    def _save_state(self):
        try:
            data = {
                "mode": self.mode,
                "x": self.root.winfo_x(),
                "y": self.root.winfo_y()
            }
            CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _ensure_topmost(self):
        try:
            self.root.attributes("-topmost", True)
            self.root.lift()
        except Exception:
            pass
        self.root.after(1800, self._ensure_topmost)

    def _init_system_tray(self):
        """Initialize background Windows System Tray icon with menu controls."""
        if not HAS_PYSTRAY:
            return

        def _create_tray_image():
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((4, 4, 60, 60), outline=(0, 240, 255, 255), width=3)
            draw.ellipse((14, 14, 50, 50), outline=(56, 189, 248, 200), width=2)
            draw.ellipse((22, 22, 42, 42), fill=(0, 240, 255, 255))
            return img

        def _on_toggle_tray(icon, item):
            self.root.after(0, self._toggle_show_hide_tray)

        def _on_toggle_voice(icon, item):
            self.root.after(0, self.toggle_listening)

        def _on_open_browser(icon, item):
            import webbrowser
            webbrowser.open("http://127.0.0.1:8000")

        def _on_toggle_startup(icon, item):
            current = is_start_with_windows_enabled()
            set_start_with_windows(not current)

        def _on_exit(icon, item):
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.stop()
            self.root.after(0, self.root.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("Show / Hide J.A.R.V.I.S.", _on_toggle_tray, default=True),
            pystray.MenuItem("Toggle Voice Listening", _on_toggle_voice),
            pystray.MenuItem("Open Web Command Center", _on_open_browser),
            pystray.MenuItem("Start with Windows", _on_toggle_startup, checked=lambda item: is_start_with_windows_enabled()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit J.A.R.V.I.S.", _on_exit)
        )

        try:
            self.tray_icon = pystray.Icon("JARVIS", _create_tray_image(), "J.A.R.V.I.S. Desktop Assistant", menu)
            self.tray_icon.run_detached()
        except Exception as e:
            print(f"[!] System tray init exception: {e}")

    def _toggle_show_hide_tray(self):
        """Toggle HUD window visibility between desktop topmost and system tray."""
        try:
            if self.root.state() == "withdrawn" or not self.root.winfo_viewable():
                self.root.deiconify()
                self.root.lift()
                self.root.attributes("-topmost", True)
            else:
                self.root.withdraw()
        except Exception:
            self.root.deiconify()

    # -------------------------------------------------------------
    # UI Building: Minimized Mode (Floating Circular Voice Icon)
    # -------------------------------------------------------------
    def _build_mini_ui(self):
        self.mini_size = 72
        self.mini_canvas = tk.Canvas(
            self.root,
            width=self.mini_size,
            height=self.mini_size,
            bg=self.transparent_color,
            highlightthickness=0,
            cursor="hand2"
        )

        # Mouse Bindings for Drag & Click Detection
        self.mini_canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.mini_canvas.bind("<B1-Motion>", self._on_mouse_motion)
        self.mini_canvas.bind("<ButtonRelease-1>", self._on_mini_release)
        self.mini_canvas.bind("<Double-Button-1>", lambda e: self.toggle_mode())
        self.mini_canvas.bind("<Button-3>", self._show_context_menu)
        self.mini_canvas.bind("<Enter>", self._on_mini_enter)
        self.mini_canvas.bind("<Leave>", self._on_mini_leave)

        self._render_mini_icon()

    def _generate_smooth_icon(self, state: str, phase: int, is_hovered: bool) -> Image.Image:
        """
        Render a 4x supersampled, antialiased high-tech voice command microphone emblem.
        Downsampled with Lanczos resampling for pristine, razor-sharp, smooth pixels.
        """
        scale = 4
        size = self.mini_size
        ss = size * scale
        cx, cy = ss // 2, ss // 2

        img = Image.new("RGBA", (ss, ss), (1, 1, 1, 0))
        draw = ImageDraw.Draw(img)

        # State Palette
        if state == "listening":
            neon = (16, 185, 129)       # Emerald Green
            neon_glow = (52, 211, 153)
            core_bg = (2, 44, 34)
        elif state == "processing":
            neon = (56, 189, 248)       # Sky Blue
            neon_glow = (125, 211, 252)
            core_bg = (8, 47, 73)
        elif state == "success":
            neon = (16, 185, 129)       # Emerald Green
            neon_glow = (52, 211, 153)
            core_bg = (2, 44, 34)
        elif state == "error":
            neon = (239, 68, 68)        # Crimson Red
            neon_glow = (248, 113, 113)
            core_bg = (69, 10, 10)
        else:  # idle
            neon = (0, 240, 255)        # Jarvis Electric Cyan
            neon_glow = (103, 232, 249)
            core_bg = (5, 15, 28)

        # Ambient Glow Halo
        r_halo = (ss // 2) - scale * 1
        halo_alpha = 50 if is_hovered else 25
        draw.ellipse([cx - r_halo, cy - r_halo, cx + r_halo, cy + r_halo],
                     fill=(*neon, halo_alpha), outline=(*neon, 60), width=scale)

        # Main Titanium Outer Bezel & Body
        r = (ss // 2) - scale * 3
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=(*core_bg, 250), outline=(*neon, 240), width=scale * 2)

        # Inner Cyber Track Ring
        r_in = r - scale * 4
        draw.ellipse([cx - r_in, cy - r_in, cx + r_in, cy + r_in],
                     outline=(*neon_glow, 110), width=scale)

        # High-Tech Radial Tick Marks (Stark Arc Reactor style)
        num_ticks = 12
        for i in range(num_ticks):
            angle = (i * 360 / num_ticks) + (phase * 15 if state == "processing" else 0)
            rad = math.radians(angle)
            t_r1 = r - scale * 2
            t_r2 = r - scale * (4 if i % 3 == 0 else 3)
            x1 = cx + t_r1 * math.cos(rad)
            y1 = cy + t_r1 * math.sin(rad)
            x2 = cx + t_r2 * math.cos(rad)
            y2 = cy + t_r2 * math.sin(rad)
            draw.line([x1, y1, x2, y2], fill=(*neon_glow, 170 if i % 3 == 0 else 90), width=scale)

        if state == "success":
            # Crisp antialiased checkmark
            pts = [
                (cx - scale * 8, cy),
                (cx - scale * 2, cy + scale * 6),
                (cx + scale * 9, cy - scale * 6)
            ]
            draw.line(pts, fill=(*neon_glow, 255), width=scale * 3, joint="curve")
        elif state == "error":
            # Crisp antialiased error alert
            d = scale * 6
            draw.line([cx - d, cy - d, cx + d, cy + d], fill=(*neon_glow, 255), width=scale * 3)
            draw.line([cx + d, cy - d, cx - d, cy + d], fill=(*neon_glow, 255), width=scale * 3)
        else:
            # Voice Command Microphone Emblem
            mw = scale * 5
            mh = scale * 13
            m_top = cy - scale * 10
            m_bot = m_top + mh

            # Mic capsule
            draw.rounded_rectangle([cx - mw, m_top, cx + mw, m_bot], radius=mw,
                                   fill=(*neon_glow, 255), outline=(*neon, 255), width=scale)

            # Acoustic grille horizontal line slits
            for slit_y in [m_top + scale * 4, m_top + scale * 7, m_top + scale * 10]:
                draw.line([cx - mw + scale * 1.5, slit_y, cx + mw - scale * 1.5, slit_y],
                          fill=(*core_bg, 220), width=scale)

            # U-shaped cradle holder
            cradle_r = mw + scale * 4
            cradle_top = cy - scale * 4
            cradle_bot = m_bot + scale * 3
            draw.arc([cx - cradle_r, cradle_top - scale * 3, cx + cradle_r, cradle_bot],
                     start=0, end=180, fill=(*neon, 255), width=scale * 2)

            # Stem & Base Pedestal
            draw.line([cx, cradle_bot, cx, cradle_bot + scale * 5], fill=(*neon, 255), width=scale * 2)
            draw.line([cx - scale * 6, cradle_bot + scale * 5, cx + scale * 6, cradle_bot + scale * 5],
                      fill=(*neon, 255), width=scale * 2)

            # Acoustic Soundwave Radiation (Active Equalizer Waves when listening)
            if state == "listening":
                wave_offsets = [scale * 13, scale * 18]
                for idx, wr in enumerate(wave_offsets):
                    w_alpha = int(255 * (0.9 - idx * 0.35 + (phase % 3) * 0.1))
                    w_alpha = max(60, min(255, w_alpha))
                    # Left wave
                    draw.arc([cx - wr - scale * 2, cy - wr, cx - scale * 4, cy + wr],
                             start=130, end=230, fill=(*neon_glow, w_alpha), width=scale * 2)
                    # Right wave
                    draw.arc([cx + scale * 4, cy - wr, cx + wr + scale * 2, cy + wr],
                             start=310, end=50, fill=(*neon_glow, w_alpha), width=scale * 2)

        # Micro Controls: Expand (top-right) & Close (top-left)
        if is_hovered:
            # Micro expand arrow (top right)
            draw.polygon([
                (cx + r - scale * 4, cy - r + scale * 2),
                (cx + r - scale * 2, cy - r + scale * 2),
                (cx + r - scale * 2, cy - r + scale * 4)
            ], fill=(56, 189, 248, 220))
            draw.line([(cx + r - scale * 2, cy - r + scale * 2), (cx + r - scale * 5, cy - r + scale * 5)],
                      fill=(56, 189, 248, 220), width=scale)
            # Micro close X (top left)
            draw.line([(cx - r + scale * 2, cy - r + scale * 2), (cx - r + scale * 5, cy - r + scale * 5)],
                      fill=(148, 163, 184, 200), width=scale)
            draw.line([(cx - r + scale * 5, cy - r + scale * 2), (cx - r + scale * 2, cy - r + scale * 5)],
                      fill=(148, 163, 184, 200), width=scale)

        # Supersampled Lanczos Resampling for Pristine Smooth Pixels
        final = img.resize((size, size), Image.Resampling.LANCZOS)
        bg = Image.new("RGB", (size, size), (1, 1, 1))
        bg.paste(final, (0, 0), final)
        return bg

    def _render_mini_icon(self):
        """Draw smooth-pixel Voice HUD Icon on Canvas."""
        self.mini_canvas.delete("all")
        bg_img = self._generate_smooth_icon(self.state, self.pulse_phase, self.is_hovered)
        self._mini_photo = ImageTk.PhotoImage(bg_img)
        self.mini_canvas.create_image(
            self.mini_size // 2,
            self.mini_size // 2,
            image=self._mini_photo
        )

    def _start_pulsing(self):
        if self.pulse_timer:
            self.root.after_cancel(self.pulse_timer)
        self._pulse_step()

    def _pulse_step(self):
        if self.state not in ["listening", "processing"]:
            self.pulse_phase = 0
            self._render_mini_icon()
            return

        self.pulse_phase = (self.pulse_phase + 1) % 6
        self._render_mini_icon()
        self.pulse_timer = self.root.after(140, self._pulse_step)

    # -------------------------------------------------------------
    # UI Building: Expanded Mode (Full Floating HUD Bar)
    # -------------------------------------------------------------
    def _build_expanded_ui(self):
        self.exp_w = 320
        self.exp_h = 76
        self.expanded_frame = tk.Frame(self.root, bg="#050b14", bd=0)

        # Outer Neon Border
        border = tk.Frame(self.expanded_frame, bg="#00f0ff", bd=1)
        border.pack(fill="both", expand=True)

        inner = tk.Frame(border, bg="#050b14", bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Top Header Bar (Draggable)
        top_bar = tk.Frame(inner, bg="#071322", height=22)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)

        top_bar.bind("<ButtonPress-1>", self._on_mouse_down)
        top_bar.bind("<B1-Motion>", self._on_mouse_motion)
        top_bar.bind("<ButtonRelease-1>", self._on_mouse_up)

        self.title_lbl = tk.Label(
            top_bar,
            text="⚡ J.A.R.V.I.S. // COMPANION HUD",
            font=("Segoe UI", 8, "bold"),
            fg="#00f0ff",
            bg="#071322",
            anchor="w"
        )
        self.title_lbl.pack(side="left", padx=8)
        self.title_lbl.bind("<ButtonPress-1>", self._on_mouse_down)
        self.title_lbl.bind("<B1-Motion>", self._on_mouse_motion)
        self.title_lbl.bind("<ButtonRelease-1>", self._on_mouse_up)

        # Window Controls: Minimize & Close
        btn_close = tk.Label(top_bar, text="✕", font=("Segoe UI", 8), fg="#94a3b8", bg="#071322", cursor="hand2", padx=6)
        btn_close.pack(side="right")
        btn_close.bind("<Button-1>", lambda e: self.root.destroy())

        btn_min = tk.Label(top_bar, text="—", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#071322", cursor="hand2", padx=6)
        btn_min.pack(side="right")
        btn_min.bind("<Button-1>", lambda e: self.toggle_mode())

        # Bottom Command & Controls Area
        bottom_box = tk.Frame(inner, bg="#050b14")
        bottom_box.pack(fill="both", expand=True, padx=8, pady=6)

        # Arc Reactor Core Status Button
        self.exp_core_btn = tk.Button(
            bottom_box,
            text="●",
            font=("Consolas", 16, "bold"),
            fg="#00f0ff",
            bg="#031b26",
            activebackground="#00f0ff",
            activeforeground="#000000",
            relief="flat",
            bd=0,
            cursor="hand2",
            width=2,
            command=self._on_core_click
        )
        self.exp_core_btn.pack(side="left", padx=(0, 6))

        # Dedicated Mic Button
        self.exp_mic_btn = tk.Button(
            bottom_box,
            text="🎙",
            font=("Segoe UI", 12),
            fg="#00f0ff",
            bg="#082f49",
            activebackground="#10b981",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            cursor="hand2",
            width=2,
            command=self.toggle_listening
        )
        self.exp_mic_btn.pack(side="left", padx=(0, 6))

        # Text Input Box
        self.entry = tk.Entry(
            bottom_box,
            font=("Segoe UI", 9),
            bg="#0a1526",
            fg="#e0f2fe",
            insertbackground="#00f0ff",
            relief="flat",
            bd=2
        )
        self.entry.pack(side="left", fill="both", expand=True, pady=2)
        self.entry.insert(0, "Awaiting directive or voice...")
        self.entry.bind("<FocusIn>", lambda e: self.entry.delete(0, "end") if self.entry.get() == "Awaiting directive or voice..." else None)
        self.entry.bind("<Return>", lambda e: self._submit_command(self.entry.get()))

        # Send Button
        self.exp_send_btn = tk.Button(
            bottom_box,
            text="➔",
            font=("Segoe UI", 9, "bold"),
            fg="#00f0ff",
            bg="#031b26",
            activebackground="#00f0ff",
            activeforeground="#000000",
            relief="flat",
            bd=0,
            cursor="hand2",
            width=2,
            command=lambda: self._submit_command(self.entry.get())
        )
        self.exp_send_btn.pack(side="right", padx=(6, 0))

    # -------------------------------------------------------------
    # Mode Switching Mechanics
    # -------------------------------------------------------------
    def _show_mini_mode(self):
        self.mode = "mini"
        self.expanded_frame.pack_forget()
        self.root.geometry(f"{self.mini_size}x{self.mini_size}+{self.saved_x}+{self.saved_y}")
        self.mini_canvas.pack(fill="both", expand=True)
        self._render_mini_icon()
        self._save_state()

    def _show_expanded_mode(self):
        self.mode = "expanded"
        self.mini_canvas.pack_forget()
        self._hide_bubble()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        exp_x = max(10, min(screen_w - self.exp_w - 20, self.saved_x - (self.exp_w - self.mini_size)))
        exp_y = max(10, min(screen_h - self.exp_h - 40, self.saved_y))

        self.root.geometry(f"{self.exp_w}x{self.exp_h}+{exp_x}+{exp_y}")
        self.expanded_frame.pack(fill="both", expand=True)
        self._save_state()

    def toggle_mode(self):
        """Toggle between Minimized Floating Icon and Expanded HUD Console."""
        if self.mode == "mini":
            self.saved_x = self.root.winfo_x()
            self.saved_y = self.root.winfo_y()
            self._show_expanded_mode()
        else:
            self.saved_x = self.root.winfo_x() + (self.exp_w - self.mini_size)
            self.saved_y = self.root.winfo_y()
            self._show_mini_mode()
            self.show_bubble("Minimized. Tap icon to speak, double-tap to expand.", duration_ms=2500)

    # -------------------------------------------------------------
    # Mouse & Drag Mechanics
    # -------------------------------------------------------------
    def _on_mouse_down(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self._drag_data["win_x"] = self.root.winfo_x()
        self._drag_data["win_y"] = self.root.winfo_y()
        self._drag_data["moved"] = False

    def _on_mouse_motion(self, event):
        dx = event.x_root - self._drag_data["x"]
        dy = event.y_root - self._drag_data["y"]

        if abs(dx) > 3 or abs(dy) > 3:
            self._drag_data["moved"] = True

        new_x = self._drag_data["win_x"] + dx
        new_y = self._drag_data["win_y"] + dy

        # Keep on screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w = self.mini_size if self.mode == "mini" else self.exp_w
        h = self.mini_size if self.mode == "mini" else self.exp_h

        clamped_x = max(0, min(screen_w - w, new_x))
        clamped_y = max(0, min(screen_h - h, new_y))

        self.root.geometry(f"+{clamped_x}+{clamped_y}")

        # Move floating bubble alongside icon if open
        if self.bubble_window and self.bubble_window.winfo_exists():
            self._position_bubble()

    def _on_mouse_up(self, event):
        self.saved_x = self.root.winfo_x()
        self.saved_y = self.root.winfo_y()
        self._save_state()

    def _on_mini_release(self, event):
        """Handle single-click vs drag on mini icon."""
        if self._drag_data["moved"]:
            self._on_mouse_up(event)
            return

        click_x = event.x
        click_y = event.y

        # Check if clicked on expand micro badge (top-right)
        if click_x >= self.mini_size - 22 and click_y <= 22:
            self.toggle_mode()
            return

        # Check if clicked on close micro badge (top-left)
        if click_x <= 22 and click_y <= 22:
            self.root.destroy()
            return

        # Core circle clicked -> Toggle Voice Input!
        self.toggle_listening()

    def _on_mini_enter(self, event):
        self.is_hovered = True
        self._render_mini_icon()
        if self.state == "idle":
            self.show_bubble("J.A.R.V.I.S. Voice HUD • Tap to speak • Drag to move", duration_ms=2500)

    def _on_mini_leave(self, event):
        self.is_hovered = False
        self._render_mini_icon()
        if self.state == "idle":
            self._hide_bubble()

    # -------------------------------------------------------------
    # Context Menu
    # -------------------------------------------------------------
    def _show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#071322", fg="#e0f2fe", activebackground="#0284c7", activeforeground="#ffffff")
        menu.add_command(label="🎙 Speak Directive (Mic)", command=self.toggle_listening)
        menu.add_command(label="⤢ Expand to Full HUD" if self.mode == "mini" else "— Minimize to Floating Icon", command=self.toggle_mode)
        menu.add_separator()
        menu.add_command(label="📱 Open WhatsApp", command=lambda: self._submit_command("open whatsapp"))
        menu.add_command(label="🌐 Open Google Chrome", command=lambda: self._submit_command("open chrome"))
        menu.add_command(label="🔊 Mute / Unmute Audio", command=lambda: self._submit_command("mute audio"))
        menu.add_command(label="📸 Take Screenshot", command=lambda: self._submit_command("take screenshot"))
        menu.add_command(label="🕒 System Time", command=lambda: self._submit_command("what time is it"))
        menu.add_separator()
        menu.add_command(label="🔄 Reset Position to Corner", command=self._reset_position)
        menu.add_command(label="✕ Close J.A.R.V.I.S.", command=self.root.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def _reset_position(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.saved_x = screen_w - 90
        self.saved_y = screen_h - 180
        self.root.geometry(f"+{self.saved_x}+{self.saved_y}")
        self._save_state()

    # -------------------------------------------------------------
    # Floating Speech Bubble / Tooltip
    # -------------------------------------------------------------
    def show_bubble(self, message: str, duration_ms: int = 3500):
        """Display an always-on-top high-tech floating speech pill beside the icon."""
        if not message:
            return

        if self.bubble_hide_timer:
            self.root.after_cancel(self.bubble_hide_timer)
            self.bubble_hide_timer = None

        if not self.bubble_window or not self.bubble_window.winfo_exists():
            self.bubble_window = tk.Toplevel(self.root)
            self.bubble_window.overrideredirect(True)
            self.bubble_window.attributes("-topmost", True)
            self.bubble_window.configure(bg="#00f0ff")

            self.bubble_inner = tk.Frame(self.bubble_window, bg="#050b14")
            self.bubble_inner.pack(fill="both", expand=True, padx=1, pady=1)

            self.bubble_label = tk.Label(
                self.bubble_inner,
                text="",
                font=("Segoe UI", 9, "bold"),
                fg="#e0f2fe",
                bg="#050b14",
                padx=8,
                pady=4,
                wraplength=220,
                justify="left"
            )
            self.bubble_label.pack()

        # Update text
        clean = message.strip()
        if len(clean) > 80:
            clean = clean[:80] + "..."
        self.bubble_label.config(text=clean)

        self._position_bubble()

        if duration_ms > 0:
            self.bubble_hide_timer = self.root.after(duration_ms, self._hide_bubble)

    def _position_bubble(self):
        if not self.bubble_window or not self.bubble_window.winfo_exists():
            return

        self.bubble_window.update_idletasks()
        bw = self.bubble_window.winfo_reqwidth()
        bh = self.bubble_window.winfo_reqheight()

        x = self.root.winfo_x()
        y = self.root.winfo_y()

        # Position above or to the left of the mini icon
        bx = x - bw - 8
        if bx < 10:
            bx = x + (self.mini_size if self.mode == "mini" else self.exp_w) + 8

        by = y + 10
        screen_h = self.root.winfo_screenheight()
        if by + bh > screen_h - 40:
            by = screen_h - bh - 40

        self.bubble_window.geometry(f"+{bx}+{by}")
        self.bubble_window.lift()

    def _hide_bubble(self):
        if self.bubble_window and self.bubble_window.winfo_exists():
            self.bubble_window.destroy()
            self.bubble_window = None

    # -------------------------------------------------------------
    # Voice Input Engine (speech_recognition)
    # -------------------------------------------------------------
    def toggle_listening(self):
        """Toggle microphone listening state."""
        if self.is_listening:
            self.is_listening = False
            self.state = "idle"
            self._render_mini_icon()
            self.show_bubble("Microphone disengaged.", duration_ms=1500)
            return

        if not HAS_SR:
            self.show_bubble("Speech recognition library not available.", duration_ms=3000)
            return

        self.is_listening = True
        self.state = "listening"
        self._start_pulsing()

        if self.mode == "expanded":
            self.title_lbl.config(text="🎙 LISTENING... SPEAK DIRECTIVE", fg="#10b981")
            self.exp_mic_btn.config(bg="#10b981", fg="#050b14")

        self.show_bubble("🎙 Listening... Speak your command now", duration_ms=0)
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        """Microphone capture thread."""
        transcript = ""
        error_msg = ""

        try:
            with sr.Microphone() as source:
                # Fast noise calibration
                self.recognizer.adjust_for_ambient_noise(source, duration=0.25)
                # Listen with timeout
                audio = self.recognizer.listen(source, timeout=6.0, phrase_time_limit=10.0)

            # Recognize speech via Google Speech Recognition
            transcript = self.recognizer.recognize_google(audio)

        except sr.WaitTimeoutError:
            error_msg = "No speech detected."
        except sr.UnknownValueError:
            error_msg = "Could not understand audio."
        except sr.RequestError:
            error_msg = "Speech recognition network timeout."
        except Exception as e:
            error_msg = f"Audio capture error: {str(e)[:30]}"

        # Transition back to main thread
        self.root.after(0, lambda: self._on_voice_finished(transcript, error_msg))

    def _on_voice_finished(self, transcript: str, error_msg: str):
        self.is_listening = False

        if transcript:
            clean_cmd = transcript.strip()
            self.show_bubble(f'🎙 Heard: "{clean_cmd}"', duration_ms=3000)
            if self.mode == "expanded":
                self.entry.delete(0, "end")
                self.entry.insert(0, clean_cmd)
                self.title_lbl.config(text=f'HEARD: "{clean_cmd[:25]}"', fg="#38bdf8")
            self._submit_command(clean_cmd)
        else:
            self.state = "error"
            self._render_mini_icon()
            self.show_bubble(error_msg or "Voice canceled.", duration_ms=2500)
            if self.mode == "expanded":
                self.title_lbl.config(text=f"VOICE: {error_msg[:25]}", fg="#ef4444")
                self.exp_mic_btn.config(bg="#082f49", fg="#00f0ff")
            self.root.after(2500, self._reset_state)

    # -------------------------------------------------------------
    # Directive Dispatch & Execution
    # -------------------------------------------------------------
    def _on_core_click(self):
        cmd = self.entry.get().strip()
        if not cmd or cmd == "Awaiting directive or voice...":
            cmd = "open whatsapp"
            self.entry.delete(0, "end")
            self.entry.insert(0, cmd)
        self._submit_command(cmd)

    def _submit_command(self, cmd_text: str):
        cmd = cmd_text.strip()
        if not cmd or cmd == "Awaiting directive or voice...":
            return

        self.state = "processing"
        self._start_pulsing()

        if self.mode == "expanded":
            self.title_lbl.config(text=f"DISPATCHING: {cmd[:25]}...", fg="#38bdf8")
            self.exp_core_btn.config(fg="#38bdf8")
        else:
            self.show_bubble(f'⚡ Dispatching: "{cmd[:30]}"...', duration_ms=0)

        def _send_thread():
            try:
                payload = json.dumps({"message": cmd}).encode("utf-8")
                req = urllib.request.Request(
                    BACKEND_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=9) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    msg = data.get("message", "Directive executed.")
                    self.root.after(0, lambda: self._on_success(msg))
            except Exception as e:
                # If backend is offline, try direct desktop agent fallback for common commands
                self._fallback_desktop_action(cmd, str(e))

        threading.Thread(target=_send_thread, daemon=True).start()

    def _fallback_desktop_action(self, cmd: str, orig_err: str):
        """Fallback to desktop agent directly if backend core is offline or starting."""
        clean = cmd.strip()
        lower = clean.lower()
        action = None
        params = {}

        if any(w in lower for w in ["mute", "unmute", "volume up", "volume down"]):
            action = "control_volume"
            params = {"action": "mute" if "mute" in lower else "up" if "up" in lower else "down"}
        elif "screenshot" in lower or "screen capture" in lower:
            action = "take_screenshot"
            params = {}
        elif lower.startswith("delete ") or lower.startswith("remove ") or lower.startswith("erase ") or lower.startswith("empty "):
            target = re.sub(r'^(delete|remove|erase|clear|empty)\s+(?:the\s+)?(?:file\s+|folder\s+|directory\s+)?', '', clean, flags=re.IGNORECASE).strip()
            action = "delete_item"
            params = {"target": target}
        elif lower.startswith("close ") or lower.startswith("kill ") or lower.startswith("terminate "):
            target = re.sub(r'^(close|kill|terminate|exit)\s+(?:the\s+)?(?:app\s+|process\s+)?', '', clean, flags=re.IGNORECASE).strip()
            action = "kill_process"
            params = {"target": target}
        elif "spotify" in lower or (lower.startswith("play ") and "youtube" not in lower):
            song_q = re.sub(r'^(?:open\s+spotify\s+(?:and\s+)?|spotify\s+)?(?:play|listen to|stream)\s+', '', clean, flags=re.IGNORECASE)
            song_q = re.sub(r'\s+on\s+spotify$', '', song_q, flags=re.IGNORECASE).strip()
            action = "play_spotify"
            params = {"query": song_q}
        elif "youtube" in lower and any(w in lower for w in ["play", "watch", "search"]):
            yt_q = re.sub(r'^(?:open\s+youtube\s+(?:and\s+)?|youtube\s+)?(?:play|watch|search(?:\s+for)?)\s+', '', clean, flags=re.IGNORECASE)
            yt_q = re.sub(r'\s+on\s+youtube$', '', yt_q, flags=re.IGNORECASE).strip()
            action = "open_url"
            params = {"url": f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_q)}"}
        elif lower.startswith("open ") or lower.startswith("launch ") or lower.startswith("start ") or lower.startswith("run "):
            target = re.sub(r'^(open|launch|start|run|fire up)\s+', '', clean, flags=re.IGNORECASE).strip()
            action = "launch_custom_app"
            params = {"target": target}
        elif any(w in lower for w in ["send ", "text ", "message "]) and "to " in lower:
            # WhatsApp direct message
            m_wa = re.search(r'(?:send|text|message)\s+(?:a\s+)?(?:message\s+)?to\s+(.+?)\s+(?:saying|that|with)\s+(.+)$', clean, re.IGNORECASE)
            if not m_wa:
                m_wa = re.search(r'(?:send|text|message)\s+(.+?)\s+to\s+(.+)$', clean, re.IGNORECASE)
                if m_wa:
                    raw_msg, wa_c = m_wa.group(1).strip(), m_wa.group(2).strip()
                    wa_m = re.sub(r'\s+message$', '', raw_msg, flags=re.IGNORECASE).strip() or "Hi"
                else:
                    wa_c, wa_m = "", "Hi"
            else:
                wa_c, wa_m = m_wa.group(1).strip(), m_wa.group(2).strip()

            wa_c = re.sub(r'\s+on\s+whatsapp$', '', wa_c, flags=re.IGNORECASE).strip()
            action = "send_whatsapp"
            params = {"contact": wa_c, "text": wa_m}
        elif "whatsapp" in lower:
            action = "launch_app"
            params = {"app_id": "whatsapp"}
        elif "chrome" in lower:
            action = "launch_app"
            params = {"app_id": "chrome"}

        if action:
            try:
                payload = json.dumps({"action": action, "parameters": params}).encode("utf-8")
                req = urllib.request.Request(
                    DESKTOP_AGENT_URL,
                    data=payload,
                    headers={"Content-Type": "application/json", "Authorization": "Bearer jarvis_desktop_secure_pairing_token_2026"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    msg = data.get("message", "Executed via Desktop Agent.")
                    self.root.after(0, lambda: self._on_success(msg))
                    return
            except Exception:
                pass

        self.root.after(0, lambda: self._on_error("Backend offline. Start J.A.R.V.I.S."))

    def _on_success(self, response_msg: str):
        self.state = "success"
        self._render_mini_icon()

        clean_resp = response_msg.replace("*", "").replace("`", "").strip()
        clean_resp = re.sub(r'[\U00010000-\U0010ffff]', '', clean_resp).strip()
        disp_resp = clean_resp[:45] + "..." if len(clean_resp) > 45 else clean_resp

        if self.mode == "expanded":
            self.title_lbl.config(text=f"DONE: {disp_resp}", fg="#10b981")
            self.exp_core_btn.config(fg="#10b981")
            self.exp_mic_btn.config(bg="#082f49", fg="#00f0ff")
            self.entry.delete(0, "end")
            self.entry.insert(0, "Awaiting directive or voice...")
        else:
            self.show_bubble(f"✓ {disp_resp}", duration_ms=4000)

        # Spoken Audio Confirmation via pyttsx3
        speak_async(clean_resp)

        if self.reset_timer:
            self.root.after_cancel(self.reset_timer)
        self.reset_timer = self.root.after(3500, self._reset_state)

    def _on_error(self, err_msg: str):
        self.state = "error"
        self._render_mini_icon()

        if self.mode == "expanded":
            self.title_lbl.config(text=f"ERR: {err_msg[:28]}", fg="#ef4444")
            self.exp_core_btn.config(fg="#ef4444")
            self.exp_mic_btn.config(bg="#082f49", fg="#00f0ff")
        else:
            self.show_bubble(f"✕ {err_msg}", duration_ms=3500)

        if self.reset_timer:
            self.root.after_cancel(self.reset_timer)
        self.reset_timer = self.root.after(3500, self._reset_state)

    def _reset_state(self):
        self.state = "idle"
        self._render_mini_icon()

        if self.mode == "expanded":
            self.title_lbl.config(text="⚡ J.A.R.V.I.S. // COMPANION HUD", fg="#00f0ff")
            self.exp_core_btn.config(fg="#00f0ff")
            self.exp_mic_btn.config(bg="#082f49", fg="#00f0ff")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = JarvisCompanionHUD()
    app.run()
