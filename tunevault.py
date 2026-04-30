"""
TuneVault - CustomTkinter Blue/Yellow Futuristic GUI
Drop-in replacement for tunevault.py.

Requires:
    pip install customtkinter

Uses existing:
    tunevault_core.py
    tunevault_db.py
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
    raise SystemExit(
        "CustomTkinter is not installed. Run: python -m pip install customtkinter"
    )

from tunevault_core import TuneVaultCore
from tunevault_db import TuneVaultDB


# -----------------------------
# Futuristic Blue / Yellow Theme
# -----------------------------
COLORS = {
    "bg": "#020B1A",
    "bg_2": "#06152B",
    "panel": "#071D3A",
    "panel_2": "#0A274D",
    "panel_3": "#031126",
    "blue": "#168BFF",
    "blue_2": "#0057D8",
    "yellow": "#FFD400",
    "yellow_2": "#FFB800",
    "white": "#F8FBFF",
    "muted": "#A8B7CC",
    "muted_2": "#70829C",
    "border": "#0E6BFF",
    "success": "#20E3A2",
    "error": "#FF4D6D",
}


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class GlowButton(ctk.CTkButton):
    """Small helper button with consistent hover behavior."""

    def __init__(self, master, variant="blue", **kwargs):
        if variant == "yellow":
            colors = {
                "fg_color": COLORS["yellow"],
                "hover_color": COLORS["yellow_2"],
                "text_color": "#06152B",
                "border_color": COLORS["yellow"],
            }
        else:
            colors = {
                "fg_color": COLORS["panel_2"],
                "hover_color": COLORS["blue_2"],
                "text_color": COLORS["white"],
                "border_color": COLORS["blue"],
            }
        colors.update(kwargs)
        super().__init__(
            master,
            corner_radius=8,
            border_width=2,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            **colors,
        )


class TuneVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TuneVault")
        self.geometry("1120x760")
        self.minsize(980, 680)
        self.configure(fg_color=COLORS["bg"])

        # Backend
        self.db = TuneVaultDB()
        self.core = TuneVaultCore(self.db)

        # State
        self.current_videos = []
        self.track_entries = []
        self.is_downloading = False
        self.deps_ok = False

        self._build_shell()
        self._check_deps()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -----------------------------
    # UI Layout
    # -----------------------------
    def _build_shell(self):
        self.outer = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg"],
            border_color=COLORS["blue"],
            border_width=2,
            corner_radius=14,
        )
        self.outer.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_top_bar()
        self._build_header()
        self._build_url_panel()
        self._build_tabs()
        self._build_status_area()

    def _build_top_bar(self):
        top = ctk.CTkFrame(self.outer, fg_color=COLORS["bg"], height=42, corner_radius=12)
        top.pack(fill="x", padx=12, pady=(8, 0))
        top.pack_propagate(False)

        ctk.CTkLabel(
            top,
            text="⚡",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=(8, 12))

        ctk.CTkFrame(top, fg_color=COLORS["yellow"], height=3, width=330).pack(
            side="left", padx=6
        )
        ctk.CTkLabel(
            top,
            text="T U N E V A U L T",
            text_color=COLORS["white"],
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
        ).pack(side="left", padx=16)
        ctk.CTkFrame(top, fg_color=COLORS["yellow"], height=3, width=330).pack(
            side="left", padx=6, fill="x", expand=True
        )

    def _build_header(self):
        header = ctk.CTkFrame(
            self.outer,
            fg_color=COLORS["panel_3"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=10,
            height=88,
        )
        header.pack(fill="x", padx=18, pady=(8, 0))
        header.pack_propagate(False)

        logo = ctk.CTkLabel(
            header,
            text="TUNEVAULT",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(family="Segoe UI Black", size=44, weight="bold"),
        )
        logo.pack(side="left", padx=(24, 28), pady=8)

        ctk.CTkLabel(
            header,
            text="YouTube to MP3 Personal Music Library",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
        ).pack(side="left", pady=28)

        GlowButton(
            header,
            text="OPTIONS  ⚙",
            width=145,
            height=42,
            variant="blue",
            command=self._open_settings,
        ).pack(side="right", padx=20)

    def _build_url_panel(self):
        panel = ctk.CTkFrame(
            self.outer,
            fg_color=COLORS["panel"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=10,
        )
        panel.pack(fill="x", padx=18, pady=(8, 0))

        ctk.CTkLabel(
            panel,
            text="Paste a YouTube URL (video or playlist):",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
        ).pack(anchor="w", padx=22, pady=(16, 6))

        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(0, 18))

        self.url_var = tk.StringVar()
        self.url_entry = ctk.CTkEntry(
            row,
            textvariable=self.url_var,
            height=48,
            corner_radius=8,
            fg_color=COLORS["bg"],
            border_color=COLORS["blue"],
            border_width=2,
            text_color=COLORS["white"],
            placeholder_text="https://www.youtube.com/watch?v=...",
            placeholder_text_color=COLORS["muted_2"],
            font=ctk.CTkFont(family="Segoe UI", size=18),
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self._on_fetch())

        GlowButton(
            row,
            text="PASTE",
            width=120,
            height=48,
            variant="blue",
            command=self._paste_clipboard,
        ).pack(side="left", padx=(14, 0))

        self.fetch_btn = GlowButton(
            row,
            text="⬇  FETCH",
            width=145,
            height=48,
            variant="yellow",
            command=self._on_fetch,
        )
        self.fetch_btn.pack(side="left", padx=(14, 0))

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self.outer,
            fg_color=COLORS["panel_3"],
            segmented_button_fg_color=COLORS["panel_2"],
            segmented_button_selected_color=COLORS["yellow"],
            segmented_button_selected_hover_color=COLORS["yellow_2"],
            segmented_button_unselected_color=COLORS["panel_2"],
            segmented_button_unselected_hover_color=COLORS["blue_2"],
            text_color=COLORS["white"],
            border_color=COLORS["blue"],
            border_width=2,
            corner_radius=10,
        )
        self.tabview.pack(fill="both", expand=True, padx=18, pady=(10, 0))

        self.download_tab = self.tabview.add("⬇  DOWNLOAD")
        self.library_tab = self.tabview.add("♫  LIBRARY")
        self.download_tab.configure(fg_color=COLORS["panel_3"])
        self.library_tab.configure(fg_color=COLORS["panel_3"])

        self._build_download_tab()
        self._build_library_tab()

    def _build_download_tab(self):
        header = ctk.CTkFrame(
            self.download_tab,
            fg_color=COLORS["panel"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=8,
            height=42,
        )
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)

        for text, width, anchor in [
            ("#", 70, "center"),
            ("TITLE", 620, "w"),
            ("DURATION", 130, "center"),
            ("STATUS", 160, "center"),
        ]:
            ctk.CTkLabel(
                header,
                text=text,
                width=width,
                anchor=anchor,
                text_color=COLORS["yellow"],
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(side="left", padx=4)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self.download_tab,
            fg_color=COLORS["bg"],
            scrollbar_button_color=COLORS["panel_2"],
            scrollbar_button_hover_color=COLORS["blue"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=8,
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.placeholder_label = ctk.CTkLabel(
            self.scroll_frame,
            text="\n\nPaste a YouTube link above and click FETCH\n\nto preview tracks before downloading.",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self.placeholder_label.pack(pady=100)

        self.download_all_btn = GlowButton(
            self.download_tab,
            text="⬇  DOWNLOAD ALL TO LIBRARY",
            width=420,
            height=58,
            variant="blue",
            command=self._on_download_all,
        )
        self.download_all_btn.pack(pady=(0, 18))
        self.download_all_btn.pack_forget()

    def _build_library_tab(self):
        top = ctk.CTkFrame(self.library_tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=10)

        self.lib_stats_label = ctk.CTkLabel(
            top,
            text="0 tracks - 0.0 MB",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.lib_stats_label.pack(side="left")

        GlowButton(
            top,
            text="OPEN MUSIC FOLDER",
            width=170,
            height=36,
            variant="blue",
            command=self._open_music_folder,
        ).pack(side="right", padx=(8, 0))

        GlowButton(
            top,
            text="REFRESH",
            width=110,
            height=36,
            variant="blue",
            command=self._refresh_library,
        ).pack(side="right")

        self.library_scroll = ctk.CTkScrollableFrame(
            self.library_tab,
            fg_color=COLORS["bg"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=8,
        )
        self.library_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._refresh_library()

    def _build_status_area(self):
        status_wrap = ctk.CTkFrame(self.outer, fg_color=COLORS["bg"], corner_radius=0)
        status_wrap.pack(fill="x", padx=18, pady=(8, 14))

        self.status_label = ctk.CTkLabel(
            status_wrap,
            text="Ready",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(0, 4))

        progress_row = ctk.CTkFrame(status_wrap, fg_color="transparent")
        progress_row.pack(fill="x")

        self.progress_bar = ctk.CTkProgressBar(
            progress_row,
            height=22,
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
            width=58,
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.percent_label.pack(side="left", padx=(10, 0))

    # -----------------------------
    # Actions
    # -----------------------------
    def _check_deps(self):
        status = self.core.get_dependency_status()
        self.deps_ok = status.get("yt_dlp") and status.get("ffmpeg")
        dep_text = (
            f"yt-dlp: {'OK' if status.get('yt_dlp') else 'Missing'} | "
            f"ffmpeg: {'OK' if status.get('ffmpeg') else 'Missing'}"
        )
        self._set_status(dep_text)

        if not self.deps_ok:
            missing = []
            if not status.get("yt_dlp"):
                missing.append("yt-dlp")
            if not status.get("ffmpeg"):
                missing.append("ffmpeg")
            messagebox.showwarning(
                "Missing Dependencies",
                "Missing: " + ", ".join(missing) + "\n\nInstall them or use the packaged installer build.",
            )

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
        self.download_all_btn.pack_forget()

    def _display_preview(self, videos):
        self._clear_preview()
        self.current_videos = videos

        for index, info in enumerate(videos, start=1):
            self._add_track_row(index, info)

        self.download_all_btn.pack(pady=(0, 18))
        self._set_status(f"Found {len(videos)} track(s). Edit metadata and click DOWNLOAD.")

    def _add_track_row(self, index, info):
        row = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=COLORS["panel"],
            border_color=COLORS["blue"],
            border_width=1,
            corner_radius=8,
        )
        row.pack(fill="x", padx=8, pady=6)

        top = ctk.CTkFrame(row, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            top,
            text=f"{index:02d}",
            width=70,
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        fields = {}
        title_var = tk.StringVar(value=info.title)
        title_entry = ctk.CTkEntry(
            top,
            textvariable=title_var,
            height=38,
            fg_color=COLORS["bg"],
            border_color=COLORS["panel_2"],
            text_color=COLORS["white"],
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        fields["title"] = title_var

        ctk.CTkLabel(
            top,
            text=info.duration_str,
            width=120,
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        status_var = tk.StringVar(value="Already downloaded" if self.db.is_duplicate(info.video_id) else "Ready")
        ctk.CTkLabel(
            top,
            textvariable=status_var,
            width=160,
            text_color=COLORS["success"] if self.db.is_duplicate(info.video_id) else COLORS["muted"],
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        meta = ctk.CTkFrame(row, fg_color=COLORS["panel_3"], corner_radius=6)
        meta.pack(fill="x", padx=12, pady=(0, 10))

        for key, label, val, width in [
            ("artist", "Artist", info.artist, 160),
            ("album", "Album", info.album or "Singles", 150),
            ("genre", "Genre", info.genre, 120),
            ("year", "Year", info.year, 80),
        ]:
            ctk.CTkLabel(
                meta,
                text=f"{label}:",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left", padx=(10, 4), pady=8)

            var = tk.StringVar(value=val)
            ent = ctk.CTkEntry(
                meta,
                textvariable=var,
                width=width,
                height=30,
                fg_color=COLORS["bg"],
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
        value = max(0, min(overall_pct, 100)) / 100
        self.progress_bar.set(value)
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
            ctk.CTkLabel(
                self.library_scroll,
                text="No downloads yet.",
                text_color=COLORS["muted"],
                font=ctk.CTkFont(size=16, weight="bold"),
            ).pack(pady=60)
            return

        for row in downloads:
            card = ctk.CTkFrame(
                self.library_scroll,
                fg_color=COLORS["panel"],
                border_color=COLORS["blue"],
                border_width=1,
                corner_radius=8,
            )
            card.pack(fill="x", padx=8, pady=5)

            title = row["title"] or "--"
            artist = row["artist"] or "--"
            album = row["album"] or "--"
            duration = row["duration"] or "--"
            date_str = row["downloaded_at"][:10] if row["downloaded_at"] else ""

            ctk.CTkLabel(
                card,
                text=title,
                anchor="w",
                text_color=COLORS["white"],
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(fill="x", padx=12, pady=(8, 2))

            ctk.CTkLabel(
                card,
                text=f"Artist: {artist}    Album: {album}    Duration: {duration}    Added: {date_str}",
                anchor="w",
                text_color=COLORS["yellow"],
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(fill="x", padx=12, pady=(0, 8))

    def _open_music_folder(self):
        music_dir = self.db.get_setting("music_dir")
        if music_dir and os.path.isdir(music_dir):
            webbrowser.open(f"file://{os.path.abspath(music_dir)}")
        else:
            messagebox.showinfo("Folder Not Found", "Music folder has not been created yet.")

    def _open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title("TuneVault Options")
        win.geometry("560x390")
        win.configure(fg_color=COLORS["bg"])
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(
            win,
            text="OPTIONS",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(20, 16))

        body = ctk.CTkFrame(win, fg_color=COLORS["panel"], border_color=COLORS["blue"], border_width=1)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        ctk.CTkLabel(
            body,
            text="Music Folder:",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 4))

        dir_row = ctk.CTkFrame(body, fg_color="transparent")
        dir_row.pack(fill="x", padx=18)
        dir_var = tk.StringVar(value=self.db.get_setting("music_dir") or "")
        ctk.CTkEntry(
            dir_row,
            textvariable=dir_var,
            height=38,
            fg_color=COLORS["bg"],
            border_color=COLORS["blue"],
            text_color=COLORS["white"],
        ).pack(side="left", fill="x", expand=True)

        def browse():
            path = filedialog.askdirectory()
            if path:
                dir_var.set(path)

        GlowButton(dir_row, text="BROWSE", width=100, height=38, variant="blue", command=browse).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            body,
            text="Audio Quality (kbps):",
            text_color=COLORS["yellow"],
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 4))

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
            dropdown_hover_color=COLORS["blue_2"],
        ).pack(anchor="w", padx=18, pady=(0, 14))

        ctk.CTkLabel(
            body,
            text="Legal Notice: TuneVault is for personal use only. Use responsibly.",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=18, pady=(8, 16))

        def save():
            self.db.set_setting("music_dir", dir_var.get().strip())
            self.db.set_setting("bitrate", br_var.get())
            win.destroy()
            self._set_status("Settings saved.")

        GlowButton(body, text="SAVE OPTIONS", width=170, height=42, variant="yellow", command=save).pack(pady=(0, 18))

    def _on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()


if __name__ == "__main__":
    app = TuneVaultApp()
    app.mainloop()
