"""
TuneVault - Tkinter mockup-style GUI
Drop-in replacement for tunevault.py.

Keeps your existing backend files:
    tunevault_core.py
    tunevault_db.py

This version uses the cleaner GUI structure from the provided mockup code,
but keeps the real TuneVault fetch / queue / download / settings behavior.
"""

from __future__ import annotations

import ctypes
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont
import webbrowser

from tunevault_core import TuneVaultCore
from tunevault_db import TuneVaultDB


# ── Color palette from mockup ─────────────────────────────────────────────────
BG_DARK = "#050d1a"
BG_PANEL = "#091428"
BG_WIDGET = "#0a1a30"
BG_ROW = "#0d1f38"
BORDER = "#1a3a5c"
BORDER_BRIGHT = "#168BFF"
ACCENT_BLUE = "#1e4d80"
GOLD = "#ffd400"
GOLD_DIM = "#c8920f"
TEXT_WHITE = "#e8f0fe"
TEXT_MUTED = "#7a9abf"
SUCCESS = "#22E6A8"
ERROR = "#FF4D6D"
PROGRESS_BG = "#0d1f38"
SCROLLBAR_BG = "#0d1f38"
SCROLLBAR_FG = "#1e4d80"


# Optional bundled fonts.
# Later, add these TTF files beside the EXE in a fonts folder and include them in Inno/PyInstaller.
# The app will use them automatically. If they are missing, it falls back to Windows fonts.
BUNDLED_FONT_FILES = [
    "fonts/Geist-Regular.ttf",
    "fonts/Geist-SemiBold.ttf",
    "fonts/Geist-Bold.ttf",
    "fonts/Orbitron-Regular.ttf",
    "fonts/Orbitron-SemiBold.ttf",
    "fonts/Orbitron-Bold.ttf",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def resource_path(relative_path: str) -> str:
    """Support normal Python runs and PyInstaller one-file builds."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def find_icon_path() -> str:
    candidates = [
        "tunevault.ico",
        "TuneVault.ico",
        "tunevault (1).ico",
        "app.ico",
    ]
    for name in candidates:
        path = resource_path(name)
        if os.path.exists(path):
            return path
    return resource_path("tunevault.ico")


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TuneVault.Desktop.App")
    except Exception:
        pass


def clean_track_title(title: str) -> str:
    """Clean common YouTube labels while preserving Artist - Song order."""
    if not title:
        return "Unknown Track"

    value = str(title).strip()
    value = value.replace("–", "-").replace("—", "-")

    # Remove bracketed video-quality / official-video labels anywhere in title.
    junk_inside_brackets = [
        r"official\s+music\s+video",
        r"official\s+hd\s+music\s+video",
        r"official\s+lyric\s+video",
        r"official\s+lyrics?\s+video",
        r"official\s+video",
        r"official\s+audio",
        r"music\s+video",
        r"lyric\s+video",
        r"lyrics?",
        r"audio",
        r"4k\s+upgrade",
        r"4k\s+upgraded",
        r"hd",
    ]
    pattern = "|".join(junk_inside_brackets)
    value = re.sub(rf"\s*[\(\[]\s*(?:{pattern})\s*[\)\]]\s*", " ", value, flags=re.I)

    # Remove loose trailing labels.
    loose = [
        r"official\s+music\s+video",
        r"official\s+hd\s+music\s+video",
        r"official\s+lyric\s+video",
        r"official\s+video",
        r"official\s+audio",
        r"music\s+video",
        r"lyric\s+video",
        r"4k\s+upgrade",
        r"hd",
    ]
    for item in loose:
        value = re.sub(rf"\s*-?\s*{item}\s*$", "", value, flags=re.I)

    value = re.sub(r"\s+", " ", value).strip(" -_\t\r\n")
    return value or str(title).strip() or "Unknown Track"


def maybe_flip_song_artist(title: str, artist: str) -> str:
    """If YouTube title is Song - Artist, convert to Artist - Song."""
    title = clean_track_title(title)
    artist = (artist or "").strip()
    if not artist or artist.lower() == "unknown artist":
        return title

    normalized = title.replace("–", "-").replace("—", "-")
    parts = [p.strip() for p in normalized.split("-") if p.strip()]
    if len(parts) >= 2 and parts[-1].lower() == artist.lower():
        song = " - ".join(parts[:-1]).strip()
        return f"{artist} - {song}" if song else artist
    if not normalized.lower().startswith(artist.lower() + " -"):
        return f"{artist} - {title}"
    return title




def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _blend(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    a = _hex_to_rgb(c1)
    b = _hex_to_rgb(c2)
    return _rgb_to_hex(tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))


def _gradient_line(canvas, points, colors, width=3, steps=90):
    """Draw a segmented line with a soft left-to-right color fade."""
    if len(points) < 4:
        return
    pts = list(zip(points[0::2], points[1::2]))
    if len(pts) < 2:
        return

    # Build small linear interpolation points across each segment.
    expanded = []
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        seg_steps = max(2, steps // max(1, len(pts) - 1))
        for j in range(seg_steps):
            t = j / seg_steps
            expanded.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    expanded.append(pts[-1])

    n = max(1, len(expanded) - 1)
    for i in range(n):
        t = i / n
        # Multi-stop gradient.
        if len(colors) == 2:
            color = _blend(colors[0], colors[1], t)
        else:
            scaled = t * (len(colors) - 1)
            idx = min(int(scaled), len(colors) - 2)
            local_t = scaled - idx
            color = _blend(colors[idx], colors[idx + 1], local_t)
        x1, y1 = expanded[i]
        x2, y2 = expanded[i + 1]
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width, capstyle="round", joinstyle="round")


def _rounded_gradient_rect(canvas, x1, y1, x2, y2, r, left_color, mid_color, right_color, outline=None, width=1):
    """Paint a horizontal gradient clipped to a rounded-rect silhouette."""
    x1, y1, x2, y2, r = int(x1), int(y1), int(x2), int(y2), int(r)
    total = max(1, x2 - x1)
    for x in range(x1, x2 + 1):
        t = (x - x1) / total
        if t < 0.5:
            color = _blend(left_color, mid_color, t * 2)
        else:
            color = _blend(mid_color, right_color, (t - 0.5) * 2)

        # Rounded vertical clipping.
        top = y1
        bottom = y2
        if x < x1 + r:
            dx = (x1 + r) - x
            dy = int((max(0, r * r - dx * dx)) ** 0.5)
            top = y1 + r - dy
            bottom = y2 - r + dy
        elif x > x2 - r:
            dx = x - (x2 - r)
            dy = int((max(0, r * r - dx * dx)) ** 0.5)
            top = y1 + r - dy
            bottom = y2 - r + dy

        canvas.create_line(x, top, x, bottom, fill=color)

    if outline:
        _rounded_rect(canvas, x1, y1, x2, y2, r, fill="", outline=outline, width=width)


# ── Rounded canvas controls ───────────────────────────────────────────────────
def _rounded_rect(canvas, x1, y1, x2, y2, r=10, **kwargs):
    """Draw a rounded rectangle on a Tk canvas."""
    points = [
        x1 + r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedButton(tk.Canvas):
    """Rounded blue/yellow TuneVault button."""
    def __init__(self, parent, text, command=None, width=140, height=44,
                 kind="outline", font=None):
        self.kind = kind
        self.command = command
        self.text = text
        self._state = "normal"
        self.normal_bg = BG_WIDGET
        self.hover_bg = ACCENT_BLUE
        self.border = BORDER_BRIGHT
        self.text_color = TEXT_WHITE
        self.glow = ""

        if kind == "gold":
            self.normal_bg = GOLD
            self.hover_bg = GOLD_DIM
            self.border = "#fff06a"
            self.text_color = BG_DARK
            self.glow = "#6f5c00"
        elif kind == "outline_gold":
            self.normal_bg = BG_WIDGET
            self.hover_bg = "#10233d"
            self.border = GOLD
            self.text_color = GOLD
            self.glow = "#4e4300"

        super().__init__(parent, width=width, height=height, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.font = font or ("Bahnschrift SemiBold", 11, "bold")
        self._is_hover = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)
        self.draw()

    def draw(self):
        self.delete("all")
        w = int(self.cget("width"))
        h = int(self.cget("height"))
        fill = self.hover_bg if self._is_hover and self._state != "disabled" else self.normal_bg
        text_color = self.text_color if self._state != "disabled" else TEXT_MUTED

        # Simulated neon glow. Tk does not support real blur/alpha on widgets,
        # so this uses layered rounded outlines for a soft blue/gold halo.
        if self.kind == "gold":
            glow_colors = ["#5f5000", "#8a7200", "#c9a800"]
            inner_line = "#fff06a"
        elif self.kind == "outline_gold":
            glow_colors = ["#332b00", "#5f5000", "#9f8600"]
            inner_line = "#fff06a"
        else:
            glow_colors = ["#06284f", "#0b4f95", "#168BFF"]
            inner_line = "#2a7dcc"

        _rounded_rect(self, 0, 0, w, h, 13, fill="", outline=glow_colors[0], width=2)
        _rounded_rect(self, 2, 2, w - 2, h - 2, 12, fill="", outline=glow_colors[1], width=2)
        if self._is_hover and self._state != "disabled":
            _rounded_rect(self, 4, 4, w - 4, h - 4, 11, fill="", outline=glow_colors[2], width=2)

        # Button face: horizontal gradient fade so it has the brighter center
        # seen in the original mockup instead of a flat Tk fill.
        if self.kind == "gold":
            left_face = "#f2a900" if not self._is_hover else "#d89300"
            mid_face = "#ffe45c" if not self._is_hover else "#ffd22d"
            right_face = "#ffbd00" if not self._is_hover else "#e39b00"
        elif self.kind == "outline_gold":
            left_face = "#08172c" if not self._is_hover else "#11233c"
            mid_face = "#102844" if not self._is_hover else "#1b3658"
            right_face = "#071528" if not self._is_hover else "#10233d"
        else:
            left_face = "#071528" if not self._is_hover else "#12335d"
            mid_face = "#12345a" if not self._is_hover else "#1f5792"
            right_face = "#071528" if not self._is_hover else "#102b4e"

        _rounded_gradient_rect(self, 5, 5, w - 5, h - 5, 9, left_face, mid_face, right_face, outline=self.border, width=2)
        _rounded_rect(self, 9, 9, w - 9, h - 9, 6, fill="", outline=inner_line, width=1)
        # Small top highlight for a glossy beveled look.
        self.create_line(15, 12, w - 15, 12, fill="#ffffff" if self.kind == "gold" else "#2a7dcc", width=1)
        self.create_text(w / 2, h / 2, text=self.text, fill=text_color, font=self.font)

    def _on_enter(self, _event=None):
        self._is_hover = True
        self.draw()

    def _on_leave(self, _event=None):
        self._is_hover = False
        self.draw()

    def _on_click(self, _event=None):
        if self._state != "disabled" and self.command:
            self.command()

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "state" in kwargs:
            self._state = kwargs.pop("state")
        if kwargs:
            super().config(**kwargs)
        self.draw()

    configure = config


class TuneVaultApp(tk.Tk):
    def __init__(self):
        super().__init__()

        set_windows_app_id()

        self.title("TuneVault")
        self.geometry("1280x760")
        self.minsize(1060, 680)
        self.configure(bg=BG_PANEL)
        self.resizable(True, True)

        self.db = TuneVaultDB()
        self.core = TuneVaultCore(self.db)

        self.current_videos = []
        self.track_entries = []
        self.is_downloading = False
        self.deps_ok = False
        self.active_tab = "queue"

        self._build_fonts()
        self._build_styles()
        self._set_icon()
        self._build_ui()
        self._check_deps()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── fonts ────────────────────────────────────────────────────────────────
    def _register_bundled_fonts(self):
        """Register private bundled fonts on Windows without installing them system-wide."""
        self._registered_font_paths = []
        if sys.platform != "win32":
            return

        FR_PRIVATE = 0x10
        for rel_path in BUNDLED_FONT_FILES:
            font_path = resource_path(rel_path)
            if not os.path.exists(font_path):
                continue
            try:
                added = ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
                if added:
                    self._registered_font_paths.append(font_path)
            except Exception:
                pass

    def _pick_font_family(self, preferred, fallback="Segoe UI"):
        available = set(tkfont.families(self))
        for family in preferred:
            if family in available:
                return family
        return fallback

    def _build_fonts(self):
        # Preview today with Windows-safe fallback fonts.
        # Later, if Geist/Orbitron TTF files are bundled in ./fonts, the app switches automatically.
        self._register_bundled_fonts()

        ui = self._pick_font_family([
            "Geist",
            "Geist Sans",
            "Bahnschrift SemiBold",
            "Bahnschrift",
            "Segoe UI Semibold",
            "Segoe UI",
        ])
        strip = self._pick_font_family([
            "Orbitron",
            "Bahnschrift SemiBold",
            "Bahnschrift",
            "Segoe UI Semibold",
            "Segoe UI",
        ])
        logo = self._pick_font_family([
            "Arial Black",
            "Impact",
            "Bahnschrift SemiBold",
            "Segoe UI Black",
        ], fallback="Arial")

        self.ui_family = ui
        self.strip_family = strip
        self.logo_family = logo

        self.font_title_tune = tkfont.Font(family=logo, size=34, weight="bold")
        self.font_title_vault = tkfont.Font(family=logo, size=34, weight="bold")
        self.font_strip = tkfont.Font(family=strip, size=13, weight="bold")
        self.font_strip_title = tkfont.Font(family=strip, size=15, weight="bold")
        self.font_subtitle = tkfont.Font(family=ui, size=12, weight="bold")
        self.font_label = tkfont.Font(family=ui, size=11, weight="bold")
        self.font_btn = tkfont.Font(family=ui, size=11, weight="bold")
        self.font_tab = tkfont.Font(family=ui, size=12, weight="bold")
        self.font_col_hdr = tkfont.Font(family=ui, size=11, weight="bold")
        self.font_track_num = tkfont.Font(family=ui, size=15, weight="bold")
        self.font_track_title = tkfont.Font(family=ui, size=14, weight="bold")
        self.font_track_dur = tkfont.Font(family=ui, size=15, weight="bold")
        self.font_meta = tkfont.Font(family=ui, size=10, weight="bold")
        self.font_progress = tkfont.Font(family=ui, size=11, weight="bold")
        self.font_options_btn = tkfont.Font(family=ui, size=10, weight="bold")
        self.font_dl_btn = tkfont.Font(family=ui, size=13, weight="bold")

    # ── ttk styles ───────────────────────────────────────────────────────────
    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Custom.Vertical.TScrollbar",
            troughcolor=SCROLLBAR_BG,
            background=SCROLLBAR_FG,
            arrowcolor=GOLD,
            borderwidth=0,
            relief="flat",
        )
        style.map("Custom.Vertical.TScrollbar", background=[("active", GOLD_DIM)])
        style.configure(
            "Gold.Horizontal.TProgressbar",
            troughcolor=PROGRESS_BG,
            background=GOLD,
            borderwidth=0,
            relief="flat",
            thickness=24,
        )

    def _set_icon(self):
        icon_path = find_icon_path()
        if not os.path.exists(icon_path):
            return
        try:
            self.iconbitmap(icon_path)
        except Exception:
            pass

    # ── master layout ────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self, bg=BORDER_BRIGHT, padx=2, pady=2)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg=BG_PANEL)
        inner.pack(fill="both", expand=True)

        self._build_title_strip(inner)
        self._build_header(inner)
        self._build_url_row(inner)
        self._build_main_area(inner)
        self._build_footer(inner)

    def _build_title_strip(self, parent):
        self.title_canvas = tk.Canvas(parent, bg=BG_DARK, height=56, bd=0, highlightthickness=0)
        self.title_canvas.pack(fill="x", padx=8, pady=(8, 0))
        self.title_canvas.bind("<Configure>", self._draw_title_strip)

    def _draw_title_strip(self, event=None):
        c = self.title_canvas
        c.delete("all")
        w = max(c.winfo_width(), 900)
        h = 56

        # Left dark cap with lightning icon, like the mockup.
        _rounded_rect(c, 0, 2, 50, h - 4, 8, fill="#06152B", outline="")
        c.create_text(25, 28, text="⚡", fill=GOLD, font=("Segoe UI Symbol", 20, "bold"))

        # Subtle angled dark plating behind the rails.
        c.create_polygon(52, 4, 250, 4, 230, 20, 70, 20, 58, 34, 52, 34,
                         fill="#071326", outline="#0c233d")
        c.create_polygon(w - 52, 4, w - 250, 4, w - 230, 20, w - 70, 20, w - 58, 34, w - 52, 34,
                         fill="#071326", outline="#0c233d")

        # Central wrapped badge around TUNEVAULT.
        cx = w / 2
        badge_w = min(360, max(280, w * 0.25))
        left = cx - badge_w / 2
        right = cx + badge_w / 2
        top = 7
        mid_y = 27
        low_y = 42

        # Outer blue wrap around the title with simulated glow.
        c.create_line(left - 24, mid_y, left, top, right, top, right + 24, mid_y,
                      fill="#06284f", width=6)
        c.create_line(left - 23, mid_y, left, top, right, top, right + 23, mid_y,
                      fill="#0b4f95", width=4)
        c.create_line(left - 22, mid_y, left, top, right, top, right + 22, mid_y,
                      fill=BORDER_BRIGHT, width=2)
        c.create_line(left, low_y, right, low_y, fill="#0b4f95", width=3)
        c.create_line(left, low_y, right, low_y, fill=BORDER_BRIGHT, width=1)

        # Gold rails flowing into the title wrap with warm glow behind them.
        c.create_line(65, 30, left - 95, 30, left - 65, 18, left - 22, 18,
                      fill="#5f5000", width=7)
        c.create_line(right + 22, 18, right + 65, 18, right + 95, 30, w - 110, 30,
                      fill="#5f5000", width=7)
        c.create_line(65, 30, left - 95, 30, left - 65, 18, left - 22, 18,
                      fill="#9f8600", width=5)
        c.create_line(right + 22, 18, right + 65, 18, right + 95, 30, w - 110, 30,
                      fill="#9f8600", width=5)
        c.create_line(65, 30, left - 95, 30, left - 65, 18, left - 22, 18,
                      fill=GOLD, width=3)
        c.create_line(right + 22, 18, right + 65, 18, right + 95, 30, w - 110, 30,
                      fill=GOLD, width=3)

        # Blue secondary rails under the gold line.
        c.create_line(65, 38, left - 105, 38, left - 72, low_y, left, low_y,
                      fill="#0b4f95", width=3)
        c.create_line(right, low_y, right + 72, low_y, right + 105, 38, w - 110, 38,
                      fill="#0b4f95", width=3)
        c.create_line(65, 38, left - 105, 38, left - 72, low_y, left, low_y,
                      fill=BORDER_BRIGHT, width=1)
        c.create_line(right, low_y, right + 72, low_y, right + 105, 38, w - 110, 38,
                      fill=BORDER_BRIGHT, width=1)

        # Center title with sharper tech font.
        c.create_text(cx, 26, text="T U N E V A U L T", fill=TEXT_WHITE,
                      font=self.font_strip_title)

    def _build_header(self, parent):
        hdr_border = tk.Frame(parent, bg=BORDER_BRIGHT, padx=1, pady=1)
        hdr_border.pack(fill="x", padx=14, pady=(8, 0))

        hdr = tk.Frame(hdr_border, bg=BG_PANEL, height=92)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        brand = tk.Frame(hdr, bg=BG_PANEL)
        brand.pack(side="left", padx=(18, 0), pady=10)

        # Wider logo canvas prevents the subtitle from overlapping TUNEVAULT.
        logo_canvas = tk.Canvas(brand, bg=BG_PANEL, bd=0, highlightthickness=0, height=70, width=348)
        logo_canvas.pack(side="left")
        logo_canvas.create_text(0, 36, text="TUNE", fill=TEXT_WHITE, font=self.font_title_tune, anchor="w")
        logo_canvas.create_text(144, 36, text="VAULT", fill=GOLD, font=self.font_title_vault, anchor="w")

        # Moved back to the right, but still kept tighter than the older wide gap.
        sub = tk.Label(
            brand,
            text="YouTube to MP3 Personal Music Library",
            bg=BG_PANEL,
            fg=TEXT_MUTED,
            font=self.font_subtitle,
        )
        sub.pack(side="left", padx=(8, 0), pady=(10, 0))

        opt = self._button(hdr, "OPTIONS  ⚙", command=self._open_settings, kind="outline_gold", width=150, height=50)
        opt.pack(side="right", padx=18, pady=20)

    def _build_url_row(self, parent):
        container_border = tk.Frame(parent, bg=BORDER_BRIGHT, padx=1, pady=1)
        container_border.pack(fill="x", padx=14, pady=(8, 0))

        container = tk.Frame(container_border, bg=BG_PANEL)
        container.pack(fill="x")

        lbl_row = tk.Frame(container, bg=BG_PANEL)
        lbl_row.pack(fill="x", padx=18, pady=(12, 4))
        tk.Label(lbl_row, text="🔗", bg=BG_PANEL, fg=BORDER_BRIGHT, font=("Arial", 13, "bold")).pack(side="left")
        tk.Label(lbl_row, text="  Paste a YouTube URL (video or playlist):", bg=BG_PANEL,
                 fg=GOLD, font=self.font_label).pack(side="left")

        inp_row = tk.Frame(container, bg=BG_PANEL)
        inp_row.pack(fill="x", padx=18, pady=(0, 14))

        row_h = 50
        entry_border = tk.Frame(inp_row, bg=BORDER_BRIGHT, padx=2, pady=2, height=row_h)
        entry_border.pack(side="left", fill="x", expand=True)
        entry_border.pack_propagate(False)

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            entry_border,
            textvariable=self.url_var,
            bg=BG_DARK,
            fg=TEXT_WHITE,
            insertbackground=TEXT_WHITE,
            font=tkfont.Font(family=self.ui_family, size=14),
            relief="flat",
            bd=8,
        )
        self.url_entry.pack(fill="both", expand=True)
        self.url_entry.bind("<Return>", lambda _e: self._on_fetch())

        # Same visual size as OPTIONS. Fixed rail width prevents disappearing buttons.
        btn_rail = tk.Frame(inp_row, bg=BG_PANEL, width=308, height=row_h)
        btn_rail.pack(side="left", padx=(12, 0))
        btn_rail.pack_propagate(False)

        self.paste_btn = self._button(btn_rail, "📋  PASTE", command=self._paste_url, kind="outline", width=150, height=50)
        self.paste_btn.pack(side="left", padx=(0, 8), pady=0)

        self.fetch_btn = self._button(btn_rail, "⬇  FETCH", command=self._on_fetch, kind="gold", width=150, height=50)
        self.fetch_btn.pack(side="left", pady=0)

    def _build_main_area(self, parent):
        outer = tk.Frame(parent, bg=BORDER_BRIGHT, padx=2, pady=2)
        outer.pack(fill="both", expand=True, padx=14, pady=(8, 0))

        self.main_inner = tk.Frame(outer, bg=BG_WIDGET)
        self.main_inner.pack(fill="both", expand=True)

        self._build_tabs(self.main_inner)
        self._build_queue_area(self.main_inner)
        self._build_library_area(self.main_inner)
        self._show_queue_tab()

    def _build_tabs(self, parent):
        self.tab_frame = tk.Frame(parent, bg=BG_WIDGET)
        self.tab_frame.pack(fill="x", padx=8, pady=(8, 0))

        self.queue_tab = self._make_tab(self.tab_frame, "☰  QUEUE", active=True, cmd=self._show_queue_tab)
        self.queue_tab.pack(side="left")

        self.library_tab = self._make_tab(self.tab_frame, "♪  LIBRARY", active=False, cmd=self._show_library_tab)
        self.library_tab.pack(side="left", padx=(4, 0))

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=8)

    def _make_tab(self, parent, text, active, cmd):
        frame = tk.Frame(parent, bg=BG_WIDGET)
        btn = tk.Button(frame, text=text, bg=BG_WIDGET, fg=GOLD if active else TEXT_MUTED,
                        font=self.font_tab, relief="flat", bd=0,
                        activebackground=BG_WIDGET, activeforeground=GOLD,
                        cursor="hand2", padx=34, pady=11, command=cmd)
        btn.pack()
        underline = tk.Frame(frame, bg=GOLD if active else BG_WIDGET, height=3)
        underline.pack(fill="x")
        frame._btn = btn
        frame._underline = underline
        return frame

    def _set_tab_state(self, selected: str):
        for name, frame in [("queue", self.queue_tab), ("library", self.library_tab)]:
            active = name == selected
            frame._btn.config(fg=GOLD if active else TEXT_MUTED)
            frame._underline.config(bg=GOLD if active else BG_WIDGET)
        self.active_tab = selected

    def _build_queue_area(self, parent):
        self.queue_area = tk.Frame(parent, bg=BG_WIDGET)

        hdr = tk.Frame(self.queue_area, bg=BG_ROW, height=38)
        hdr.pack(fill="x", padx=8, pady=(0, 0))
        hdr.pack_propagate(False)
        tk.Label(hdr, text="#", bg=BG_ROW, fg=GOLD, font=self.font_col_hdr, width=6).pack(side="left", padx=(8, 0))
        tk.Label(hdr, text="TITLE", bg=BG_ROW, fg=GOLD, font=self.font_col_hdr, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Label(hdr, text="DURATION", bg=BG_ROW, fg=GOLD, font=self.font_col_hdr, width=14).pack(side="left")
        tk.Label(hdr, text="STATUS", bg=BG_ROW, fg=GOLD, font=self.font_col_hdr, width=16).pack(side="left", padx=(0, 10))

        scroll_frame = tk.Frame(self.queue_area, bg=BG_WIDGET)
        scroll_frame.pack(fill="both", expand=True, padx=8, pady=(0, 0))

        self.track_canvas = tk.Canvas(scroll_frame, bg=BG_WIDGET, bd=0, highlightthickness=0)
        self.track_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", style="Custom.Vertical.TScrollbar", command=self.track_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.track_canvas.configure(yscrollcommand=scrollbar.set)

        self.track_inner = tk.Frame(self.track_canvas, bg=BG_WIDGET)
        self.canvas_window = self.track_canvas.create_window((0, 0), window=self.track_inner, anchor="nw")
        self.track_inner.bind("<Configure>", lambda _e: self.track_canvas.configure(scrollregion=self.track_canvas.bbox("all")))
        self.track_canvas.bind("<Configure>", lambda e: self.track_canvas.itemconfig(self.canvas_window, width=e.width))
        self.track_canvas.bind("<MouseWheel>", self._on_mousewheel)

        self.placeholder = tk.Label(self.track_inner,
                                    text="\n\nPaste a YouTube link above and click FETCH\n\nto add tracks to your download queue.",
                                    bg=BG_WIDGET, fg=TEXT_MUTED, font=tkfont.Font(family=self.ui_family, size=14, weight="bold"))
        self.placeholder.pack(pady=90)

        btn_frame = tk.Frame(self.queue_area, bg=BG_WIDGET, pady=14)
        btn_frame.pack(fill="x")
        self.download_all_btn = self._button(btn_frame, "⬇  DOWNLOAD ALL TO LIBRARY", command=self._on_download_all,
                                             kind="outline_gold", width=320)
        self.download_all_btn.pack()
        self.download_all_btn.pack_forget()

    def _build_library_area(self, parent):
        self.library_area = tk.Frame(parent, bg=BG_WIDGET)

        top = tk.Frame(self.library_area, bg=BG_WIDGET)
        top.pack(fill="x", padx=12, pady=(10, 8))

        self.lib_stats_label = tk.Label(top, text="0 tracks - 0.0 MB", bg=BG_WIDGET, fg=GOLD, font=self.font_label)
        self.lib_stats_label.pack(side="left")

        self._button(top, "OPEN MUSIC FOLDER", command=self._open_music_folder, kind="outline", width=160).pack(side="right", padx=(8, 0))
        self._button(top, "REFRESH", command=self._refresh_library, kind="outline", width=100).pack(side="right")

        scroll_frame = tk.Frame(self.library_area, bg=BG_WIDGET)
        scroll_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.library_canvas = tk.Canvas(scroll_frame, bg=BG_WIDGET, bd=0, highlightthickness=0)
        self.library_canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", style="Custom.Vertical.TScrollbar", command=self.library_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.library_canvas.configure(yscrollcommand=scrollbar.set)
        self.library_inner = tk.Frame(self.library_canvas, bg=BG_WIDGET)
        self.library_window = self.library_canvas.create_window((0, 0), window=self.library_inner, anchor="nw")
        self.library_inner.bind("<Configure>", lambda _e: self.library_canvas.configure(scrollregion=self.library_canvas.bbox("all")))
        self.library_canvas.bind("<Configure>", lambda e: self.library_canvas.itemconfig(self.library_window, width=e.width))

    def _build_footer(self, parent):
        footer = tk.Frame(parent, bg=BG_PANEL, pady=9)
        footer.pack(fill="x", padx=14)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(footer, textvariable=self.status_var, bg=BG_PANEL, fg=GOLD, font=self.font_progress).pack(anchor="w", pady=(0, 4))

        prog_row = tk.Frame(footer, bg=BG_PANEL)
        prog_row.pack(fill="x")

        trough = tk.Frame(prog_row, bg=BORDER_BRIGHT, padx=2, pady=2)
        trough.pack(side="left", fill="x", expand=True)

        self.progress_var = tk.DoubleVar(value=0)
        progress = ttk.Progressbar(trough, orient="horizontal", mode="determinate", variable=self.progress_var,
                                   style="Gold.Horizontal.TProgressbar", maximum=100)
        progress.pack(fill="x")

        self.pct_var = tk.StringVar(value="0%")
        tk.Label(prog_row, textvariable=self.pct_var, bg=BG_PANEL, fg=GOLD,
                 font=tkfont.Font(family=self.ui_family, size=12, weight="bold"), width=6).pack(side="right", padx=(8, 0))

    # ── controls/helpers ─────────────────────────────────────────────────────
    def _button(self, parent, text, command=None, kind="outline", width=120, height=None):
        if height is None:
            height = 46
            if kind == "outline_gold":
                height = 54
            elif kind == "gold":
                height = 46
        return RoundedButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            kind=kind,
            font=self.font_btn if kind != "outline_gold" else self.font_dl_btn,
        )

    def _bind_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda _e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda _e: widget.config(bg=normal_bg))

    def _on_mousewheel(self, event):
        self.track_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _show_queue_tab(self):
        self.library_area.pack_forget()
        self.queue_area.pack(fill="both", expand=True)
        self._set_tab_state("queue")

    def _show_library_tab(self):
        self.queue_area.pack_forget()
        self.library_area.pack(fill="both", expand=True)
        self._set_tab_state("library")
        self._refresh_library()

    # ── app actions ──────────────────────────────────────────────────────────
    def _check_deps(self):
        try:
            status = self.core.get_dependency_status()
            self.deps_ok = bool(status.get("yt_dlp") and status.get("ffmpeg"))
            self._set_status(f"yt-dlp: {'OK' if status.get('yt_dlp') else 'Missing'} | ffmpeg: {'OK' if status.get('ffmpeg') else 'Missing'}", 0)
            if not self.deps_ok:
                missing = []
                if not status.get("yt_dlp"):
                    missing.append("yt-dlp")
                if not status.get("ffmpeg"):
                    missing.append("ffmpeg")
                messagebox.showwarning("Missing Dependencies", "Missing: " + ", ".join(missing) + "\n\nUse the packaged installer build or install dependencies.")
        except Exception as exc:
            self.deps_ok = False
            self._set_status(f"Dependency check failed: {exc}", 0)

    def _set_status(self, message: str, pct: int | None = None):
        self.status_var.set(message)
        if pct is not None:
            pct = max(0, min(int(pct), 100))
            self.progress_var.set(pct)
            self.pct_var.set(f"{pct}%")

    def _paste_url(self):
        try:
            self.url_var.set(self.clipboard_get().strip())
        except tk.TclError:
            pass

    def _on_fetch(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showinfo("No URL", "Paste a YouTube URL first.")
            return
        if not self.deps_ok:
            messagebox.showerror("Missing Dependencies", "yt-dlp and/or ffmpeg are missing.")
            return

        self.fetch_btn.config(state="disabled", text="FETCHING...")
        self._set_status("Fetching video info and adding to queue...", 5)

        def worker():
            try:
                videos = self.core.fetch_video_info(url)
                self.after(0, lambda: self._display_preview(videos))
            except Exception as exc:
                self.after(0, lambda e=str(exc): messagebox.showerror("Fetch Error", e))
                self.after(0, lambda: self._set_status("Fetch failed.", 0))
            finally:
                self.after(0, lambda: self.fetch_btn.config(state="normal", text="⬇  FETCH"))
                self.after(0, lambda: self._set_status(self.status_var.get(), 0 if not self.track_entries else None))

        threading.Thread(target=worker, daemon=True).start()

    def _display_preview(self, videos):
        if self.placeholder and self.placeholder.winfo_exists():
            self.placeholder.destroy()

        queued_ids = {entry["info"].video_id for entry in self.track_entries}
        added = 0
        skipped = 0

        for info in videos:
            if info.video_id and info.video_id in queued_ids:
                skipped += 1
                continue
            info.title = maybe_flip_song_artist(info.title, info.artist)
            self.current_videos.append(info)
            self._add_track_row(len(self.track_entries) + 1, info)
            if info.video_id:
                queued_ids.add(info.video_id)
            added += 1

        if self.track_entries:
            self.download_all_btn.pack()

        if skipped:
            self._set_status(f"Added {added} track(s). Skipped {skipped} duplicate(s). Queue total: {len(self.track_entries)}.", 0)
        else:
            self._set_status(f"Added {added} track(s). Queue total: {len(self.track_entries)}. Edit metadata, then download all.", 0)

    def _add_track_row(self, index, info):
        row_border = tk.Frame(self.track_inner, bg=BORDER_BRIGHT, padx=1, pady=1)
        row_border.pack(fill="x", padx=8, pady=(8, 0))

        row = tk.Frame(row_border, bg=BG_ROW)
        row.pack(fill="x")

        main_line = tk.Frame(row, bg=BG_ROW)
        main_line.pack(fill="x", padx=8, pady=(8, 4))

        tk.Label(main_line, text=f"{index:02d}", bg=BG_ROW, fg=GOLD, font=self.font_track_num,
                 width=5, anchor="center").pack(side="left")

        fields = {}
        title_var = tk.StringVar(value=info.title)
        title_entry = tk.Entry(main_line, textvariable=title_var, bg=BG_DARK, fg=TEXT_WHITE,
                               insertbackground=TEXT_WHITE, font=self.font_track_title, relief="flat", bd=5)
        title_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        fields["title"] = title_var

        tk.Label(main_line, text=info.duration_str, bg=BG_ROW, fg=GOLD, font=self.font_track_dur,
                 width=10).pack(side="left")

        is_dup = self.db.is_duplicate(info.video_id) if info.video_id else False
        status_var = tk.StringVar(value="Downloaded ✓" if is_dup else "Ready")
        status_lbl = tk.Label(main_line, textvariable=status_var, bg=BG_ROW,
                              fg=SUCCESS if is_dup else TEXT_MUTED, font=self.font_meta, width=16)
        status_lbl.pack(side="left", padx=(4, 0))

        meta = tk.Frame(row, bg=BG_WIDGET)
        meta.pack(fill="x", padx=8, pady=(0, 8))
        tk.Label(meta, text="", bg=BG_WIDGET, width=6).pack(side="left")

        for key, label, val, width in [
            ("artist", "Artist", info.artist, 18),
            ("album", "Album", info.album or "Singles", 18),
            ("genre", "Genre", info.genre, 14),
            ("year", "Year", info.year, 9),
        ]:
            tk.Label(meta, text=f"{label}:", bg=BG_WIDGET, fg=TEXT_MUTED, font=self.font_meta).pack(side="left", padx=(0, 3))
            var = tk.StringVar(value=val)
            ent = tk.Entry(meta, textvariable=var, bg=BG_DARK, fg=GOLD, insertbackground=TEXT_WHITE,
                           relief="flat", bd=3, width=width, font=self.font_meta)
            ent.pack(side="left", padx=(0, 12), pady=6)
            fields[key] = var

        self.track_entries.append({"info": info, "fields": fields, "status_var": status_var, "status_lbl": status_lbl})

    def _on_download_all(self):
        if self.is_downloading or not self.track_entries:
            return

        self.is_downloading = True
        try:
            self.download_all_btn.config(state="disabled", text="DOWNLOADING...")
        except Exception:
            pass
        self._set_status("Starting downloads...", 0)

        for entry in self.track_entries:
            info = entry["info"]
            fields = entry["fields"]
            info.title = clean_track_title(fields["title"].get().strip() or info.title)
            info.artist = fields["artist"].get().strip() or info.artist
            info.album = fields["album"].get().strip() or info.album
            info.genre = fields["genre"].get().strip()
            info.year = fields["year"].get().strip()

        video_list = [entry["info"] for entry in self.track_entries]
        total = max(len(video_list), 1)

        def worker():
            for i, info in enumerate(video_list):
                entry = self.track_entries[i]
                self.after(0, lambda e=entry: e["status_var"].set("Downloading..."))
                self.after(0, lambda e=entry: e["status_lbl"].config(fg=GOLD))

                def progress_cb(stage, pct, msg, _i=i, _entry=entry):
                    overall = int(((_i + pct / 100) / total) * 100)
                    self.after(0, lambda m=msg, o=overall: self._set_status(m, o))
                    if stage == "complete":
                        self.after(0, lambda e=_entry: e["status_var"].set("Downloaded ✓"))
                        self.after(0, lambda e=_entry: e["status_lbl"].config(fg=SUCCESS))

                try:
                    self.core.download_track(info, progress_callback=progress_cb)
                except Exception as exc:
                    self.after(0, lambda e=entry, err=str(exc): e["status_var"].set(f"Error: {err[:35]}"))
                    self.after(0, lambda e=entry: e["status_lbl"].config(fg=ERROR))

            self.after(0, self._download_complete)

        threading.Thread(target=worker, daemon=True).start()

    def _download_complete(self):
        self.is_downloading = False
        try:
            self.download_all_btn.config(state="normal", text="⬇  DOWNLOAD ALL TO LIBRARY")
        except Exception:
            pass
        self._set_status("All downloads complete!", 100)
        self._refresh_library()
        messagebox.showinfo("Complete", "All tracks have been processed.")

    def _refresh_library(self):
        if not hasattr(self, "library_inner"):
            return
        for widget in self.library_inner.winfo_children():
            widget.destroy()

        try:
            downloads = self.db.get_all_downloads()
            stats = self.db.get_library_stats()
        except Exception:
            downloads = []
            stats = {"total_tracks": 0, "total_size_bytes": 0}

        size_mb = stats.get("total_size_bytes", 0) / (1024 * 1024)
        self.lib_stats_label.config(text=f"{stats.get('total_tracks', 0)} tracks - {size_mb:.1f} MB")

        if not downloads:
            tk.Label(self.library_inner, text="No downloads yet.", bg=BG_WIDGET, fg=TEXT_MUTED,
                     font=tkfont.Font(family=self.ui_family, size=14, weight="bold")).pack(pady=60)
            return

        for row in downloads:
            card_border = tk.Frame(self.library_inner, bg=BORDER_BRIGHT, padx=1, pady=1)
            card_border.pack(fill="x", padx=8, pady=5)
            card = tk.Frame(card_border, bg=BG_ROW)
            card.pack(fill="x")
            title = row["title"] or "--"
            artist = row["artist"] or "--"
            album = row["album"] or "--"
            duration = row["duration"] or "--"
            date_str = row["downloaded_at"][:10] if row["downloaded_at"] else ""
            tk.Label(card, text=title, anchor="w", bg=BG_ROW, fg=TEXT_WHITE,
                     font=tkfont.Font(family=self.ui_family, size=12, weight="bold")).pack(fill="x", padx=10, pady=(7, 1))
            tk.Label(card, text=f"Artist: {artist}    Album: {album}    Duration: {duration}    Added: {date_str}",
                     anchor="w", bg=BG_ROW, fg=GOLD, font=tkfont.Font(family=self.ui_family, size=10, weight="bold")).pack(fill="x", padx=10, pady=(0, 7))

    def _open_music_folder(self):
        music_dir = self.db.get_setting("music_dir")
        if music_dir and os.path.isdir(music_dir):
            webbrowser.open(f"file://{os.path.abspath(music_dir)}")
        else:
            messagebox.showinfo("Folder Not Found", "Music folder has not been created yet.")

    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("TuneVault Options")
        win.geometry("580x360")
        win.configure(bg=BG_PANEL)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="OPTIONS", bg=BG_PANEL, fg=GOLD, font=tkfont.Font(family=self.strip_family, size=24, weight="bold")).pack(pady=(18, 14))
        body_border = tk.Frame(win, bg=BORDER_BRIGHT, padx=1, pady=1)
        body_border.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        body = tk.Frame(body_border, bg=BG_WIDGET)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Music Folder:", bg=BG_WIDGET, fg=GOLD, font=self.font_label).pack(anchor="w", padx=16, pady=(16, 4))
        dir_row = tk.Frame(body, bg=BG_WIDGET)
        dir_row.pack(fill="x", padx=16)
        dir_var = tk.StringVar(value=self.db.get_setting("music_dir") or "")
        entry_border = tk.Frame(dir_row, bg=BORDER_BRIGHT, padx=1, pady=1)
        entry_border.pack(side="left", fill="x", expand=True)
        tk.Entry(entry_border, textvariable=dir_var, bg=BG_DARK, fg=TEXT_WHITE, insertbackground=TEXT_WHITE,
                 relief="flat", bd=6).pack(fill="x")

        def browse():
            path = filedialog.askdirectory()
            if path:
                dir_var.set(path)

        self._button(dir_row, "BROWSE", command=browse, kind="outline", width=95).pack(side="left", padx=(8, 0))

        tk.Label(body, text="Audio Quality (kbps):", bg=BG_WIDGET, fg=GOLD, font=self.font_label).pack(anchor="w", padx=16, pady=(16, 4))
        br_var = tk.StringVar(value=self.db.get_setting("bitrate") or "320")
        option = tk.OptionMenu(body, br_var, "128", "192", "256", "320")
        option.config(bg=BG_DARK, fg=TEXT_WHITE, activebackground=ACCENT_BLUE, activeforeground=TEXT_WHITE,
                      highlightbackground=BORDER_BRIGHT, relief="flat")
        option["menu"].config(bg=BG_DARK, fg=TEXT_WHITE)
        option.pack(anchor="w", padx=16)

        tk.Label(body, text="Legal Notice: TuneVault is for personal use only. Use responsibly.",
                 bg=BG_WIDGET, fg=TEXT_MUTED, font=tkfont.Font(family=self.ui_family, size=9)).pack(anchor="w", padx=16, pady=(16, 12))

        def save():
            self.db.set_setting("music_dir", dir_var.get().strip())
            self.db.set_setting("bitrate", br_var.get())
            win.destroy()
            self._set_status("Settings saved.", None)

        self._button(body, "SAVE OPTIONS", command=save, kind="gold", width=150).pack(pady=(0, 16))

    def _on_close(self):
        try:
            self.db.close()
        finally:
            if sys.platform == "win32":
                try:
                    FR_PRIVATE = 0x10
                    for font_path in getattr(self, "_registered_font_paths", []):
                        ctypes.windll.gdi32.RemoveFontResourceExW(font_path, FR_PRIVATE, 0)
                except Exception:
                    pass
            self.destroy()


if __name__ == "__main__":
    app = TuneVaultApp()
    app.mainloop()
