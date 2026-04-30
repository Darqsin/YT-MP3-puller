"""
TuneVault - Blue/Yellow Mockup-Style CustomTkinter GUI
Drop-in replacement for tunevault.py.

Keeps your existing backend files:
    tunevault_core.py
    tunevault_db.py

Requires:
    customtkinter
"""

import os
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("CustomTkinter is not installed. Run: python -m pip install customtkinter")

from tunevault_core import TuneVaultCore
from tunevault_db import TuneVaultDB


# -----------------------------------------------------------------------------
# Blue / Yellow Futuristic Theme
# -----------------------------------------------------------------------------
COLORS = {
    "bg": "#020A16",
    "bg_dark": "#010713",
    "panel": "#06152B",
    "panel_2": "#082044",
    "panel_3": "#031126",
    "row": "#071B36",
    "row_alt": "#05162D",
    "blue": "#168BFF",
    "blue_soft": "#0E5CC7",
    "blue_glow": "#19A6FF",
    "yellow": "#FFD400",
    "yellow_2": "#FFB800",
    "yellow_dark": "#7A5A00",
    "white": "#F7FBFF",
    "muted": "#A8B7CC",
    "muted_2": "#71829B",
    "success": "#22E6A8",
    "error": "#FF4D6D",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def resource_path(relative_path: str) -> str:
    """Support normal Python runs and PyInstaller one-file builds."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class GlowButton(ctk.CTkButton):
    def __init__(self, master, variant="blue", **kwargs):
        if variant == "yellow":
            base = {
                "fg_color": COLORS["yellow"],
                "hover_color": COLORS["yellow_2"],
                "text_color": COLORS["bg_dark"],
                "border_color": "#FFF06A",
            }
        elif variant == "outline_yellow":
            base = {
                "fg_color": COLORS["panel_3"],
                "hover_color": COLORS["yellow_dark"],
                "text_color": COLORS["yellow"],
                "border_color": COLORS["yellow"],
            }
        else:
            base = {
                "fg_color": COLORS["panel_2"],
                "hover_color": COLORS["blue_soft"],
                "text_color": COLORS["white"],
                "border_color": COLORS["blue"],
            }
        base.update(kwargs)
        super().__init__(
            master,
            corner_radius=7,
            border_width=2,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            **base,
        )


class DecoLine(ctk.CTkCanvas):
    """Small decorative angular line strip like the mockup."""
    def __init__(self, master, height=40, **kwargs):
        super().__init__(master, height=height, highlightthickness=0, bg=COLORS["bg"], **kwargs)
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50:
            return
        y = h // 2
        # yellow angular rails
        self.create_line(20, y, w * 0.35, y, w * 0.38, 6, w * 0.62, 6, w * 0.65, y, w - 20, y,
                         fill=COLORS["yellow"], width=3)
        # blue secondary rails
        self.create_line(20, y + 7, w * 0.33, y + 7, w * 0.36, h - 6, w * 0.64, h - 6,
                         w * 0.67, y + 7, w - 20, y + 7, fill=COLORS["blue"], width=2)


class TuneVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TuneVault")
        self.geometry("1220x760")
        self.minsize(1060, 680)
        self.configure(fg_color=COLORS["bg_dark"])

        # Use custom titlebar to get much closer to the mockup.
        # The app still has minimize/maximize/close buttons inside the custom frame.
        self.overrideredirect(True)
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_maximized = False
        self._normal_geometry = None

        icon_path = resource_path("tunevault.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.db = TuneVaultDB()
        self.core = TuneVaultCore(self.db)

        self.current_videos = []
        self.track_entries = []
        self.is_downloading = False
        self.deps_ok = False

        self._build_shell()
        self._check_deps()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Window chrome
    # ------------------------------------------------------------------
    def _start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _do_move(self, event):
        if self._is_maximized:
            return
        x = self.winfo_x() + event.x - self._drag_start_x
        y = self.winfo_y() + event.y - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def _minimize(self):
        self.overrideredirect(False)
        self.iconify()
        self.after(250, lambda: self.overrideredirect(True))

    def _toggle_maximize(self):
        if self._is_maximized:
            if self._normal_geometry:
                self.geometry(self._normal_geometry)
            self._is_maximized = False
        else:
            self._normal_geometry = self.geometry()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw}x{sh}+0+0")
            self._is_maximized = True

    # ------------------------------------------------------------------
    # UI Layout
    # ------------------------------------------------------------------
    def _build_shell(self):
        self.outer = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg"],
            border_color=COLORS["blue"],
            border_width=2,
            corner_radius=14,
        )
        self.outer.pack(fill="both", expand=True, padx=4, pady=4)

        self._build_titlebar()
        self._build_header()
        self._build_url_panel()
        self._build_content_panel()
        self._build_status_area()

    def _build_titlebar(self):
        titlebar = ctk.CTkFrame(self.outer, fg_color=COLORS["panel_3"], height=48, corner_radius=12)
        titlebar.pack(fill="x", padx=8, pady=(8, 0))
        titlebar.pack_propagate(False)
        titlebar.bind("<ButtonPress-1>", self._start_move)
        titlebar.bind("<B1-Motion>", self._do_move)

        ctk.CTkLabel(
            titlebar,
            text="⚡",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(side="left", padx=(14, 12))

        DecoLine(titlebar, height=44).pack(side="left", fill="x", expand=True)

        title = ctk.CTkLabel(
            titlebar,
            text="T U N E V A U L T",
            text_color=COLORS["white"],
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
        )
        title.place(relx=0.5, rely=0.5, anchor="center")
        title.bind("<ButtonPress-1>", self._start_move)
        title.bind("<B1-Motion>", self._do_move)

        for text, cmd in [("—", self._minimize), ("□", self._toggle_maximize), ("✕", self._on_close)]:
            ctk.CTkButton(
                titlebar,
                text=text,
                width=38,
                height=32,
                corner_radius=4,
                fg_color=COLORS["panel_3"],
                hover_color=COLORS["blue_soft"] if text != "✕" else "#7A1127",
                text_color=COLORS["white"],
                command=cmd,
                font=ctk.CTkFont(size=17, weight="bold"),
            ).pack(side="right", padx=(0, 4))

    def _build_header(self):
        header = ctk.CTkFrame(
            self.outer,
            fg_color=COLORS["panel_3"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=10,
            height=108,
        )
        header.pack(fill="x", padx=16, pady=(8, 0))
        header.pack_propagate(False)

        logo_wrap = ctk.CTkFrame(header, fg_color="transparent")
        logo_wrap.pack(side="left", padx=(24, 28), pady=10)

        logo_row = ctk.CTkFrame(logo_wrap, fg_color="transparent")
        logo_row.pack()
        ctk.CTkLabel(
            logo_row,
            text="TUNE",
            text_color=COLORS["white"],
            font=ctk.CTkFont(family="Segoe UI Black", size=46, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            logo_row,
            text="VAULT",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(family="Segoe UI Black", size=46, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="YouTube to MP3 Personal Music Library",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        ).pack(side="left", pady=38)

        GlowButton(
            header,
            text="OPTIONS   ⚙",
            width=165,
            height=48,
            variant="blue",
            command=self._open_settings,
        ).pack(side="right", padx=22)

    def _build_url_panel(self):
        panel = ctk.CTkFrame(
            self.outer,
            fg_color=COLORS["panel"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=10,
        )
        panel.pack(fill="x", padx=16, pady=(8, 0))

        label_row = ctk.CTkFrame(panel, fg_color="transparent")
        label_row.pack(fill="x", padx=22, pady=(14, 4))
        ctk.CTkLabel(
            label_row,
            text="🔗",
            width=36,
            text_color=COLORS["blue_glow"],
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            label_row,
            text="Paste a YouTube URL (video or playlist):",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        ).pack(side="left")

        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(0, 18))

        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            row,
            textvariable=self.url_var,
            height=54,
            corner_radius=7,
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["blue"],
            border_width=2,
            text_color=COLORS["white"],
            placeholder_text="https://www.youtube.com/watch?v=...",
            placeholder_text_color=COLORS["muted_2"],
            font=ctk.CTkFont(family="Segoe UI", size=20),
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self._on_fetch())

        GlowButton(row, text="📋  PASTE", width=145, height=54, variant="blue", command=self._paste_clipboard).pack(side="left", padx=(16, 0))

        self.fetch_btn = GlowButton(row, text="⬇  FETCH", width=165, height=54, variant="yellow", command=self._on_fetch)
        self.fetch_btn.pack(side="left", padx=(16, 0))

    def _build_content_panel(self):
        self.content = ctk.CTkFrame(
            self.outer,
            fg_color=COLORS["panel_3"],
            border_color=COLORS["blue"],
            border_width=2,
            corner_radius=12,
        )
        self.content.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        self._build_tabs_header()
        self._build_download_area()
        self._build_library_area()
        self._show_download_tab()

    def _build_tabs_header(self):
        self.tabs = ctk.CTkFrame(self.content, fg_color="transparent", height=58)
        self.tabs.pack(fill="x", padx=14, pady=(12, 0))
        self.tabs.pack_propagate(False)

        self.download_tab_btn = GlowButton(
            self.tabs,
            text="⬇  DOWNLOAD",
            width=220,
            height=48,
            variant="outline_yellow",
            command=self._show_download_tab,
        )
        self.download_tab_btn.pack(side="left")

        self.library_tab_btn = GlowButton(
            self.tabs,
            text="♫  LIBRARY",
            width=200,
            height=48,
            variant="blue",
            command=self._show_library_tab,
        )
        self.library_tab_btn.pack(side="left", padx=(8, 0))

    def _build_download_area(self):
        self.download_area = ctk.CTkFrame(self.content, fg_color="transparent")

        header = ctk.CTkFrame(
            self.download_area,
            fg_color=COLORS["panel"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=6,
            height=48,
        )
        header.pack(fill="x", padx=14, pady=(0, 0))
        header.pack_propagate(False)

        self._table_label(header, "#", 75, COLORS["yellow"], "center").pack(side="left")
        self._table_label(header, "TITLE", 680, COLORS["yellow"], "w").pack(side="left", fill="x", expand=True)
        self._table_label(header, "DURATION", 140, COLORS["yellow"], "center").pack(side="left")
        self._table_label(header, "STATUS", 165, COLORS["yellow"], "center").pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(
            self.download_area,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["panel_2"],
            scrollbar_button_hover_color=COLORS["blue"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=8,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.placeholder_label = ctk.CTkLabel(
            self.scroll_frame,
            text="\n\nPaste a YouTube link above and click FETCH\n\nto preview tracks before downloading.",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.placeholder_label.pack(pady=110)

        btn_row = ctk.CTkFrame(self.download_area, fg_color="transparent", height=74)
        btn_row.pack(fill="x", padx=14, pady=(0, 14))
        btn_row.pack_propagate(False)

        self.download_all_btn = GlowButton(
            btn_row,
            text="⬇  DOWNLOAD ALL TO LIBRARY",
            width=440,
            height=58,
            variant="outline_yellow",
            command=self._on_download_all,
        )
        self.download_all_btn.place(relx=0.5, rely=0.5, anchor="center")
        self.download_all_btn.place_forget()

    def _build_library_area(self):
        self.library_area = ctk.CTkFrame(self.content, fg_color="transparent")

        top = ctk.CTkFrame(self.library_area, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(0, 10))

        self.lib_stats_label = ctk.CTkLabel(
            top,
            text="0 tracks - 0.0 MB",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.lib_stats_label.pack(side="left")

        GlowButton(top, text="OPEN MUSIC FOLDER", width=190, height=38, variant="blue", command=self._open_music_folder).pack(side="right", padx=(8, 0))
        GlowButton(top, text="REFRESH", width=120, height=38, variant="blue", command=self._refresh_library).pack(side="right")

        self.library_scroll = ctk.CTkScrollableFrame(
            self.library_area,
            fg_color=COLORS["bg"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=8,
        )
        self.library_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _build_status_area(self):
        status_wrap = ctk.CTkFrame(self.outer, fg_color=COLORS["bg"], corner_radius=0)
        status_wrap.pack(fill="x", padx=16, pady=(8, 14))

        self.status_label = ctk.CTkLabel(
            status_wrap,
            text="Ready",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(0, 5))

        progress_row = ctk.CTkFrame(status_wrap, fg_color="transparent")
        progress_row.pack(fill="x")

        self.progress_bar = ctk.CTkProgressBar(
            progress_row,
            height=24,
            corner_radius=7,
            fg_color=COLORS["panel_2"],
            progress_color=COLORS["yellow"],
            border_color=COLORS["blue"],
            border_width=1,
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.progress_bar.set(0)

        self.percent_label = ctk.CTkLabel(
            progress_row,
            text="0%",
            width=65,
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self.percent_label.pack(side="left", padx=(12, 0))

    def _table_label(self, master, text, width, color, anchor):
        return ctk.CTkLabel(
            master,
            text=text,
            width=width,
            anchor=anchor,
            text_color=color,
            font=ctk.CTkFont(size=16, weight="bold"),
        )

    def _show_download_tab(self):
        self.library_area.pack_forget()
        self.download_area.pack(fill="both", expand=True, padx=0, pady=0)
        self.download_tab_btn.configure(border_color=COLORS["yellow"], text_color=COLORS["yellow"])
        self.library_tab_btn.configure(border_color=COLORS["blue"], text_color=COLORS["muted"])

    def _show_library_tab(self):
        self.download_area.pack_forget()
        self.library_area.pack(fill="both", expand=True, padx=0, pady=0)
        self.download_tab_btn.configure(border_color=COLORS["blue"], text_color=COLORS["muted"])
        self.library_tab_btn.configure(border_color=COLORS["yellow"], text_color=COLORS["yellow"])
        self._refresh_library()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _check_deps(self):
        status = self.core.get_dependency_status()
        self.deps_ok = status.get("yt_dlp") and status.get("ffmpeg")
        dep_text = f"yt-dlp: {'OK' if status.get('yt_dlp') else 'Missing'} | ffmpeg: {'OK' if status.get('ffmpeg') else 'Missing'}"
        self._set_status(dep_text)
        if not self.deps_ok:
            missing = []
            if not status.get("yt_dlp"):
                missing.append("yt-dlp")
            if not status.get("ffmpeg"):
                missing.append("ffmpeg")
            messagebox.showwarning("Missing Dependencies", "Missing: " + ", ".join(missing) + "\n\nUse the packaged installer build or install dependencies.")

    def _set_status(self, message):
        if hasattr(self, "status_label"):
            self.status_label.configure(text=message)

    def _paste_clipboard(self):
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

        self.fetch_btn.configure(state="disabled", text="FETCHING...")
        self._clear_preview()
        self._set_status("Fetching video info...")
        self.progress_bar.set(0.05)
        self.percent_label.configure(text="5%")

        def worker():
            try:
                videos = self.core.fetch_video_info(url)
                self.after(0, lambda: self._display_preview(videos))
            except Exception as exc:
                self.after(0, lambda e=str(exc): messagebox.showerror("Fetch Error", e))
            finally:
                self.after(0, lambda: self.fetch_btn.configure(state="normal", text="⬇  FETCH"))
                self.after(0, lambda: self._set_status("Ready"))
                self.after(0, lambda: self.progress_bar.set(0))
                self.after(0, lambda: self.percent_label.configure(text="0%"))

        threading.Thread(target=worker, daemon=True).start()

    def _clear_preview(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.current_videos = []
        self.track_entries = []
        self.download_all_btn.place_forget()

    def _display_preview(self, videos):
        self._clear_preview()
        self.current_videos = videos
        for index, info in enumerate(videos, start=1):
            self._add_track_row(index, info)
        self.download_all_btn.place(relx=0.5, rely=0.5, anchor="center")
        self._set_status(f"Found {len(videos)} track(s). Edit metadata and click DOWNLOAD.")

    def _add_track_row(self, index, info):
        row = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=COLORS["row"] if index % 2 else COLORS["row_alt"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=7,
        )
        row.pack(fill="x", padx=8, pady=6)

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(top, text=f"{index:02d}", width=70, text_color=COLORS["yellow"], font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        fields = {}
        title_var = tk.StringVar(value=info.title)
        title_entry = ctk.CTkEntry(
            top,
            textvariable=title_var,
            height=38,
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["panel_2"],
            border_width=1,
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        fields["title"] = title_var

        ctk.CTkLabel(top, text=info.duration_str, width=140, text_color=COLORS["yellow"], font=ctk.CTkFont(size=21, weight="bold")).pack(side="left")

        is_dup = self.db.is_duplicate(info.video_id)
        status_var = tk.StringVar(value="Downloaded ✓" if is_dup else "Ready")
        ctk.CTkLabel(top, textvariable=status_var, width=165, text_color=COLORS["success"] if is_dup else COLORS["muted"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        meta = ctk.CTkFrame(row, fg_color=COLORS["panel_3"], corner_radius=6)
        meta.pack(fill="x", padx=12, pady=(0, 10))

        for key, label, val, width in [
            ("artist", "Artist", info.artist, 170),
            ("album", "Album", info.album or "Singles", 160),
            ("genre", "Genre", info.genre, 130),
            ("year", "Year", info.year, 90),
        ]:
            ctk.CTkLabel(meta, text=f"{label}:", text_color=COLORS["muted"], font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(10, 4), pady=8)
            var = tk.StringVar(value=val)
            ent = ctk.CTkEntry(
                meta,
                textvariable=var,
                width=width,
                height=30,
                fg_color=COLORS["bg_dark"],
                border_color=COLORS["panel_2"],
                text_color=COLORS["yellow"],
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            ent.pack(side="left", padx=(0, 8), pady=8)
            fields[key] = var

        self.track_entries.append({"info": info, "fields": fields, "status_var": status_var})

    def _on_download_all(self):
        if self.is_downloading or not self.track_entries:
            return

        self.is_downloading = True
        self.download_all_btn.configure(state="disabled", text="DOWNLOADING...")
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")

        for entry in self.track_entries:
            info = entry["info"]
            fields = entry["fields"]
            info.title = fields["title"].get().strip() or info.title
            info.artist = fields["artist"].get().strip() or info.artist
            info.album = fields["album"].get().strip() or info.album
            info.genre = fields["genre"].get().strip()
            info.year = fields["year"].get().strip()

        video_list = [entry["info"] for entry in self.track_entries]
        total = len(video_list)

        def worker():
            for i, info in enumerate(video_list):
                entry = self.track_entries[i]
                self.after(0, lambda e=entry: e["status_var"].set("Downloading..."))

                def progress_cb(stage, pct, msg, _i=i, _entry=entry):
                    overall = int(((_i + pct / 100) / total) * 100)
                    self.after(0, lambda m=msg, o=overall: self._update_progress(m, o))
                    if stage == "complete":
                        self.after(0, lambda e=_entry: e["status_var"].set("Downloaded ✓"))

                try:
                    self.core.download_track(info, progress_callback=progress_cb)
                except Exception as exc:
                    self.after(0, lambda e=entry, err=str(exc): e["status_var"].set(f"Error: {err[:45]}"))

            self.after(0, self._download_complete)

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, message, overall_pct):
        self._set_status(message)
        overall_pct = max(0, min(overall_pct, 100))
        self.progress_bar.set(overall_pct / 100)
        self.percent_label.configure(text=f"{overall_pct}%")

    def _download_complete(self):
        self.is_downloading = False
        self.download_all_btn.configure(state="normal", text="⬇  DOWNLOAD ALL TO LIBRARY")
        self._set_status("All downloads complete!")
        self.progress_bar.set(1)
        self.percent_label.configure(text="100%")
        self._refresh_library()
        messagebox.showinfo("Complete", "All tracks have been processed.")

    def _refresh_library(self):
        if not hasattr(self, "library_scroll"):
            return
        for widget in self.library_scroll.winfo_children():
            widget.destroy()

        downloads = self.db.get_all_downloads()
        stats = self.db.get_library_stats()
        size_mb = stats["total_size_bytes"] / (1024 * 1024)
        self.lib_stats_label.configure(text=f"{stats['total_tracks']} tracks - {size_mb:.1f} MB")

        if not downloads:
            ctk.CTkLabel(self.library_scroll, text="No downloads yet.", text_color=COLORS["muted"], font=ctk.CTkFont(size=16, weight="bold")).pack(pady=60)
            return

        for row in downloads:
            card = ctk.CTkFrame(self.library_scroll, fg_color=COLORS["row"], border_color=COLORS["blue"], border_width=1, corner_radius=8)
            card.pack(fill="x", padx=8, pady=5)
            title = row["title"] or "--"
            artist = row["artist"] or "--"
            album = row["album"] or "--"
            duration = row["duration"] or "--"
            date_str = row["downloaded_at"][:10] if row["downloaded_at"] else ""
            ctk.CTkLabel(card, text=title, anchor="w", text_color=COLORS["white"], font=ctk.CTkFont(size=15, weight="bold")).pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(card, text=f"Artist: {artist}    Album: {album}    Duration: {duration}    Added: {date_str}", anchor="w", text_color=COLORS["yellow"], font=ctk.CTkFont(size=12, weight="bold")).pack(fill="x", padx=12, pady=(0, 8))

    def _open_music_folder(self):
        music_dir = self.db.get_setting("music_dir")
        if music_dir and os.path.isdir(music_dir):
            webbrowser.open(f"file://{os.path.abspath(music_dir)}")
        else:
            messagebox.showinfo("Folder Not Found", "Music folder has not been created yet.")

    def _open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title("TuneVault Options")
        win.geometry("580x410")
        win.configure(fg_color=COLORS["bg"])
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(win, text="OPTIONS", text_color=COLORS["yellow"], font=ctk.CTkFont(size=30, weight="bold")).pack(pady=(20, 16))
        body = ctk.CTkFrame(win, fg_color=COLORS["panel"], border_color=COLORS["blue"], border_width=1)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        ctk.CTkLabel(body, text="Music Folder:", text_color=COLORS["yellow"], font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=18, pady=(18, 4))
        dir_row = ctk.CTkFrame(body, fg_color="transparent")
        dir_row.pack(fill="x", padx=18)
        dir_var = tk.StringVar(value=self.db.get_setting("music_dir") or "")
        ctk.CTkEntry(dir_row, textvariable=dir_var, height=38, fg_color=COLORS["bg"], border_color=COLORS["blue"], text_color=COLORS["white"]).pack(side="left", fill="x", expand=True)

        def browse():
            path = filedialog.askdirectory()
            if path:
                dir_var.set(path)

        GlowButton(dir_row, text="BROWSE", width=105, height=38, variant="blue", command=browse).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(body, text="Audio Quality (kbps):", text_color=COLORS["yellow"], font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=18, pady=(18, 4))
        br_var = tk.StringVar(value=self.db.get_setting("bitrate") or "320")
        ctk.CTkOptionMenu(
            body,
            values=["128", "192", "256", "320"],
            variable=br_var,
            fg_color=COLORS["panel_2"],
            button_color=COLORS["yellow"],
            button_hover_color=COLORS["yellow_2"],
            text_color=COLORS["white"],
            dropdown_fg_color=COLORS["panel"],
            dropdown_hover_color=COLORS["blue_soft"],
        ).pack(anchor="w", padx=18, pady=(0, 14))

        ctk.CTkLabel(body, text="Legal Notice: TuneVault is for personal use only. Use responsibly.", text_color=COLORS["muted"], font=ctk.CTkFont(size=12)).pack(anchor="w", padx=18, pady=(8, 16))

        def save():
            self.db.set_setting("music_dir", dir_var.get().strip())
            self.db.set_setting("bitrate", br_var.get())
            win.destroy()
            self._set_status("Settings saved.")

        GlowButton(body, text="SAVE OPTIONS", width=180, height=44, variant="yellow", command=save).pack(pady=(0, 18))

    def _on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()


if __name__ == "__main__":
    app = TuneVaultApp()
    app.mainloop()
