"""
TuneVault - Desktop MP3 Stripper Application
Blue / Yellow Futuristic GUI built with Tkinter.

Drop-in replacement for tunevault.py
"""

import os
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from tunevault_core import TuneVaultCore
from tunevault_db import TuneVaultDB


COLORS = {
    "bg_dark": "#020B18",       # almost black navy
    "bg_mid": "#06172E",        # deep blue panel
    "bg_card": "#081F3F",       # card blue
    "bg_card_2": "#0B2A55",     # lighter panel
    "input_bg": "#031124",      # input field
    "blue": "#1687FF",          # electric blue
    "blue_soft": "#0E4C92",     # darker blue border
    "yellow": "#FFD400",        # main yellow
    "yellow_hover": "#FFE45C",  # hover yellow
    "text_primary": "#F8FBFF",
    "text_secondary": "#A9BBD6",
    "text_muted": "#6F819E",
    "success": "#00D084",
    "warning": "#FFD400",
    "error": "#FF4D6D",
    "border": "#1461B8",
    "border_dim": "#0A315F",
}

FONT_TITLE = ("Segoe UI", 28, "bold")
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_BUTTON = ("Segoe UI", 11, "bold")


class TuneVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TuneVault -- YouTube to MP3")
        self.root.geometry("1040x720")
        self.root.minsize(850, 600)
        self.root.configure(bg=COLORS["bg_dark"])

        self.db = TuneVaultDB()
        self.core = TuneVaultCore(self.db)

        self.current_videos = []
        self.track_entries = []
        self.is_downloading = False

        self._configure_styles()
        self._check_deps()

        self.app_shell = tk.Frame(
            self.root,
            bg=COLORS["bg_dark"],
            highlightbackground=COLORS["border"],
            highlightthickness=2,
        )
        self.app_shell.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_header()
        self._build_input_section()
        self._build_notebook()
        self._build_status_bar()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------- Styling -------------------------

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background=COLORS["bg_dark"],
            borderwidth=0,
            tabmargins=[16, 5, 0, 0],
        )
        style.configure(
            "TNotebook.Tab",
            background=COLORS["bg_mid"],
            foreground=COLORS["text_secondary"],
            padding=[24, 10],
            font=("Segoe UI", 11, "bold"),
            bordercolor=COLORS["border_dim"],
            lightcolor=COLORS["border_dim"],
            darkcolor=COLORS["bg_dark"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["bg_card"])],
            foreground=[("selected", COLORS["yellow"])],
        )

        style.configure(
            "Cyber.Horizontal.TProgressbar",
            troughcolor=COLORS["input_bg"],
            background=COLORS["yellow"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["yellow_hover"],
            darkcolor=COLORS["yellow"],
            thickness=18,
        )

        style.configure(
            "Treeview",
            background=COLORS["bg_mid"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_mid"],
            bordercolor=COLORS["border"],
            rowheight=30,
            font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["bg_card_2"],
            foreground=COLORS["yellow"],
            font=FONT_BODY_BOLD,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["blue_soft"])],
            foreground=[("selected", COLORS["text_primary"])],
        )

    def _make_button(self, parent, text, command, primary=False, width=None):
        bg = COLORS["yellow"] if primary else COLORS["bg_card"]
        fg = COLORS["bg_dark"] if primary else COLORS["yellow"]
        hover_bg = COLORS["yellow_hover"] if primary else COLORS["blue_soft"]
        hover_fg = COLORS["bg_dark"] if primary else COLORS["yellow"]

        btn = tk.Button(
            parent,
            text=text,
            font=FONT_BUTTON,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=hover_fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=8,
            width=width,
            command=command,
            highlightthickness=2,
            highlightbackground=COLORS["border"],
        )
        btn.bind("<Enter>", lambda _e: btn.config(bg=hover_bg, fg=hover_fg))
        btn.bind("<Leave>", lambda _e: btn.config(bg=bg, fg=fg))
        return btn

    # ------------------------- Dependency Check -------------------------

    def _check_deps(self):
        status = self.core.get_dependency_status()
        self.deps_ok = status["yt_dlp"] and status["ffmpeg"]

        if not self.deps_ok:
            missing = []
            if not status["yt_dlp"]:
                missing.append("yt-dlp")
            if not status["ffmpeg"]:
                missing.append("ffmpeg")

            messagebox.showwarning(
                "Missing Dependencies",
                "TuneVault could not find:\n\n"
                + "\n".join(missing)
                + "\n\nInstall them or use the bundled installer build.",
            )

    # ------------------------- Header -------------------------

    def _build_header(self):
        header = tk.Frame(
            self.app_shell,
            bg=COLORS["bg_mid"],
            height=110,
            highlightbackground=COLORS["border_dim"],
            highlightthickness=1,
        )
        header.pack(fill="x", padx=8, pady=(8, 0))
        header.pack_propagate(False)

        top_line = tk.Frame(header, bg=COLORS["bg_mid"], height=20)
        top_line.pack(fill="x")

        tk.Label(
            top_line,
            text="⚡",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS["bg_mid"],
            fg=COLORS["yellow"],
        ).pack(side="left", padx=(15, 6))

        tk.Label(
            top_line,
            text="─" * 40,
            font=("Consolas", 11),
            bg=COLORS["bg_mid"],
            fg=COLORS["yellow"],
        ).pack(side="left")

        tk.Label(
            top_line,
            text="T U N E V A U L T",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS["bg_mid"],
            fg=COLORS["text_primary"],
        ).pack(side="left", padx=15)

        tk.Label(
            top_line,
            text="─" * 40,
            font=("Consolas", 11),
            bg=COLORS["bg_mid"],
            fg=COLORS["yellow"],
        ).pack(side="left")

        content = tk.Frame(header, bg=COLORS["bg_mid"])
        content.pack(fill="both", expand=True)

        title = tk.Label(
            content,
            text="TUNEVAULT",
            font=FONT_TITLE,
            bg=COLORS["bg_mid"],
            fg=COLORS["yellow"],
        )
        title.pack(side="left", padx=(24, 28), pady=(8, 15))

        subtitle = tk.Label(
            content,
            text="YouTube to MP3 Personal Music Library",
            font=("Segoe UI", 12),
            bg=COLORS["bg_mid"],
            fg=COLORS["text_secondary"],
        )
        subtitle.pack(side="left", pady=(14, 15))

        settings_btn = self._make_button(
            content,
            "OPTIONS  ⚙",
            self._open_settings,
            primary=False,
            width=12,
        )
        settings_btn.pack(side="right", padx=24, pady=(14, 18))

    # ------------------------- Input Section -------------------------

    def _build_input_section(self):
        input_panel = tk.Frame(
            self.app_shell,
            bg=COLORS["bg_mid"],
            highlightbackground=COLORS["border_dim"],
            highlightthickness=1,
        )
        input_panel.pack(fill="x", padx=8, pady=(0, 8))

        label = tk.Label(
            input_panel,
            text="🔗  Paste a YouTube URL (video or playlist):",
            font=FONT_SECTION,
            bg=COLORS["bg_mid"],
            fg=COLORS["yellow"],
        )
        label.pack(anchor="w", padx=24, pady=(16, 6))

        entry_frame = tk.Frame(input_panel, bg=COLORS["bg_mid"])
        entry_frame.pack(fill="x", padx=24, pady=(0, 18))

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            entry_frame,
            textvariable=self.url_var,
            font=("Segoe UI", 14),
            bg=COLORS["input_bg"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["yellow"],
            relief="flat",
            bd=10,
            highlightthickness=2,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["yellow"],
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self._on_fetch())

        paste_btn = self._make_button(entry_frame, "PASTE", self._paste_clipboard)
        paste_btn.pack(side="left", padx=(12, 0))

        self.fetch_btn = self._make_button(entry_frame, "⬇  FETCH", self._on_fetch, primary=True, width=10)
        self.fetch_btn.pack(side="left", padx=(12, 0))

    def _paste_clipboard(self):
        try:
            text = self.root.clipboard_get()
            self.url_var.set(text.strip())
        except tk.TclError:
            pass

    # ------------------------- Main Tabs -------------------------

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.app_shell)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        self.preview_tab = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.notebook.add(self.preview_tab, text="  ⬇ DOWNLOAD  ")

        self.library_tab = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.notebook.add(self.library_tab, text="  ♫ LIBRARY  ")

        self._build_preview_tab()
        self._build_library_tab()

    def _build_preview_tab(self):
        self.track_list_frame = tk.Frame(
            self.preview_tab,
            bg=COLORS["bg_dark"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self.track_list_frame.pack(fill="both", expand=True, pady=(0, 8))

        self.canvas = tk.Canvas(
            self.track_list_frame,
            bg=COLORS["bg_dark"],
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            self.track_list_frame,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS["bg_dark"])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.placeholder_label = tk.Label(
            self.scrollable_frame,
            text=(
                "\n\n⚡ Paste a YouTube link above and click FETCH\n"
                "to preview tracks before downloading.\n\n"
                "Supports single videos and playlists."
            ),
            font=("Segoe UI", 13),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            justify="center",
        )
        self.placeholder_label.pack(pady=90)

        self.download_all_frame = tk.Frame(self.preview_tab, bg=COLORS["bg_dark"])
        self.download_all_btn = self._make_button(
            self.download_all_frame,
            "⬇  DOWNLOAD ALL TO LIBRARY",
            self._on_download_all,
            primary=False,
            width=28,
        )
        self.download_all_btn.config(font=("Segoe UI", 13, "bold"), pady=12)
        self.download_all_btn.pack(pady=8)

        self.progress_frame = tk.Frame(self.preview_tab, bg=COLORS["bg_dark"])
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=FONT_BODY_BOLD,
            bg=COLORS["bg_dark"],
            fg=COLORS["yellow"],
        )
        self.progress_label.pack(anchor="w", padx=6)

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            style="Cyber.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(6, 8), padx=6)

    def _build_library_tab(self):
        top_bar = tk.Frame(self.library_tab, bg=COLORS["bg_dark"])
        top_bar.pack(fill="x", pady=(5, 10))

        self.lib_stats_label = tk.Label(
            top_bar,
            text="",
            font=FONT_BODY_BOLD,
            bg=COLORS["bg_dark"],
            fg=COLORS["yellow"],
        )
        self.lib_stats_label.pack(side="left")

        refresh_btn = self._make_button(top_bar, "REFRESH", self._refresh_library)
        refresh_btn.pack(side="right")

        open_folder_btn = self._make_button(top_bar, "OPEN MUSIC FOLDER", self._open_music_folder)
        open_folder_btn.pack(side="right", padx=(0, 10))

        columns = ("title", "artist", "album", "duration", "date")
        self.lib_tree = ttk.Treeview(self.library_tab, columns=columns, show="headings", height=18)
        self.lib_tree.heading("title", text="TITLE")
        self.lib_tree.heading("artist", text="ARTIST")
        self.lib_tree.heading("album", text="ALBUM")
        self.lib_tree.heading("duration", text="DURATION")
        self.lib_tree.heading("date", text="DATE ADDED")

        self.lib_tree.column("title", width=310)
        self.lib_tree.column("artist", width=170)
        self.lib_tree.column("album", width=130)
        self.lib_tree.column("duration", width=85, anchor="center")
        self.lib_tree.column("date", width=120, anchor="center")

        lib_scroll = ttk.Scrollbar(self.library_tab, orient="vertical", command=self.lib_tree.yview)
        self.lib_tree.configure(yscrollcommand=lib_scroll.set)
        self.lib_tree.pack(side="left", fill="both", expand=True)
        lib_scroll.pack(side="right", fill="y")

        self._refresh_library()

    # ------------------------- Status Bar -------------------------

    def _build_status_bar(self):
        self.status_bar = tk.Frame(
            self.app_shell,
            bg=COLORS["bg_mid"],
            height=36,
            highlightbackground=COLORS["border_dim"],
            highlightthickness=1,
        )
        self.status_bar.pack(fill="x", side="bottom", padx=8, pady=(0, 8))
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_bar,
            text="Ready",
            font=FONT_BODY_BOLD,
            bg=COLORS["bg_mid"],
            fg=COLORS["yellow"],
        )
        self.status_label.pack(side="left", padx=15)

        deps = self.core.get_dependency_status()
        dep_text = (
            f"yt-dlp: {'OK' if deps['yt_dlp'] else 'Missing'}   |   "
            f"ffmpeg: {'OK' if deps['ffmpeg'] else 'Missing'}"
        )
        dep_label = tk.Label(
            self.status_bar,
            text=dep_text,
            font=FONT_BODY,
            bg=COLORS["bg_mid"],
            fg=COLORS["text_secondary"],
        )
        dep_label.pack(side="right", padx=15)

    # ------------------------- Actions -------------------------

    def _set_status(self, msg):
        self.status_label.config(text=msg)

    def _on_fetch(self):
        url = self.url_var.get().strip()

        if not url:
            messagebox.showinfo("No URL", "Please paste a YouTube URL first.")
            return

        if not self.deps_ok:
            messagebox.showerror(
                "Missing Dependencies",
                "yt-dlp and/or ffmpeg are not installed. Cannot proceed.",
            )
            return

        self.fetch_btn.config(state="disabled", text="FETCHING...")
        self._set_status("Fetching video info...")
        self._clear_preview()

        def do_fetch():
            try:
                videos = self.core.fetch_video_info(url)
                self.root.after(0, lambda: self._display_preview(videos))
            except Exception as exc:
                self.root.after(0, lambda err=str(exc): messagebox.showerror("Fetch Error", err))
            finally:
                self.root.after(0, lambda: self.fetch_btn.config(state="normal", text="⬇  FETCH"))
                self.root.after(0, lambda: self._set_status("Ready"))

        threading.Thread(target=do_fetch, daemon=True).start()

    def _clear_preview(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.download_all_frame.pack_forget()
        self.progress_frame.pack_forget()
        self.current_videos = []
        self.track_entries = []

    def _display_preview(self, videos):
        self._clear_preview()
        self.current_videos = videos
        self.track_entries = []

        # Header row like the mockup
        header = tk.Frame(self.scrollable_frame, bg=COLORS["bg_card_2"])
        header.pack(fill="x", padx=6, pady=(6, 0))
        tk.Label(header, text="#", width=6, font=FONT_BODY_BOLD, bg=COLORS["bg_card_2"], fg=COLORS["yellow"]).pack(side="left", padx=(8, 0), pady=8)
        tk.Label(header, text="TITLE", font=FONT_BODY_BOLD, bg=COLORS["bg_card_2"], fg=COLORS["yellow"], anchor="w").pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(header, text="DURATION", width=12, font=FONT_BODY_BOLD, bg=COLORS["bg_card_2"], fg=COLORS["yellow"]).pack(side="right", padx=(0, 12), pady=8)

        for i, info in enumerate(videos):
            card = tk.Frame(
                self.scrollable_frame,
                bg=COLORS["bg_mid"],
                padx=12,
                pady=8,
                highlightbackground=COLORS["border_dim"],
                highlightthickness=1,
            )
            card.pack(fill="x", padx=6, pady=(0, 2))

            top = tk.Frame(card, bg=COLORS["bg_mid"])
            top.pack(fill="x")

            num_label = tk.Label(
                top,
                text=f"{i + 1:02d}",
                font=("Segoe UI", 14, "bold"),
                bg=COLORS["bg_mid"],
                fg=COLORS["yellow"],
                width=5,
            )
            num_label.pack(side="left")

            entry_data = {}

            title_var = tk.StringVar(value=info.title)
            title_entry = tk.Entry(
                top,
                textvariable=title_var,
                font=("Segoe UI", 14, "bold"),
                bg=COLORS["bg_mid"],
                fg=COLORS["text_primary"],
                insertbackground=COLORS["yellow"],
                relief="flat",
                bd=2,
            )
            title_entry.pack(side="left", fill="x", expand=True, padx=(10, 10))
            entry_data["title"] = title_var

            dur_label = tk.Label(
                top,
                text=info.duration_str,
                font=("Segoe UI", 14, "bold"),
                bg=COLORS["bg_mid"],
                fg=COLORS["yellow"],
                width=10,
            )
            dur_label.pack(side="right")

            meta_frame = tk.Frame(card, bg=COLORS["bg_mid"])
            meta_frame.pack(fill="x", pady=(8, 0))

            for field_name, default_val, label_text in [
                ("artist", info.artist, "Artist:"),
                ("album", info.album, "Album:"),
                ("genre", info.genre, "Genre:"),
                ("year", info.year, "Year:"),
            ]:
                lbl = tk.Label(
                    meta_frame,
                    text=label_text,
                    font=FONT_BODY_BOLD,
                    bg=COLORS["bg_mid"],
                    fg=COLORS["text_secondary"],
                )
                lbl.pack(side="left", padx=(18, 4))

                var = tk.StringVar(value=default_val)
                entry = tk.Entry(
                    meta_frame,
                    textvariable=var,
                    font=FONT_BODY_BOLD,
                    bg=COLORS["bg_mid"],
                    fg=COLORS["yellow"],
                    insertbackground=COLORS["yellow"],
                    relief="flat",
                    bd=1,
                    width=14,
                )
                entry.pack(side="left", padx=(0, 8))
                entry_data[field_name] = var

            if self.db.is_duplicate(info.video_id):
                dup_label = tk.Label(
                    meta_frame,
                    text="Downloaded  ✓",
                    font=FONT_BODY_BOLD,
                    bg=COLORS["bg_mid"],
                    fg=COLORS["yellow"],
                )
                dup_label.pack(side="right", padx=12)

            status_var = tk.StringVar(value="")
            status_label = tk.Label(
                card,
                textvariable=status_var,
                font=FONT_BODY_BOLD,
                bg=COLORS["bg_mid"],
                fg=COLORS["success"],
            )
            status_label.pack(anchor="e")

            self.track_entries.append({"info": info, "fields": entry_data, "status_var": status_var})

        self.download_all_frame.pack(fill="x", padx=5)
        self._set_status(f"Found {len(videos)} track(s). Edit metadata and click Download.")

    def _on_download_all(self):
        if self.is_downloading:
            return

        self.is_downloading = True
        self.download_all_btn.config(state="disabled", text="DOWNLOADING...")
        self.progress_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.progress_bar["value"] = 0

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

        def do_download():
            for i, info in enumerate(video_list):
                entry = self.track_entries[i]

                def progress_cb(stage, pct, msg, _entry=entry, _i=i):
                    overall = int(((_i + pct / 100) / total) * 100)
                    self.root.after(0, lambda m=msg, o=overall: self._update_progress(m, o))
                    if stage == "complete":
                        self.root.after(0, lambda e=_entry: e["status_var"].set("Downloaded  ✓"))

                try:
                    self.core.download_track(info, progress_callback=progress_cb)
                except Exception as exc:
                    self.root.after(
                        0,
                        lambda e=entry, err=str(exc): e["status_var"].set(f"Error: {err[:60]}"),
                    )

            self.root.after(0, self._download_complete)

        threading.Thread(target=do_download, daemon=True).start()

    def _update_progress(self, message, overall_pct):
        self.progress_label.config(text=message)
        self.progress_bar["value"] = overall_pct
        self._set_status(message)

    def _download_complete(self):
        self.is_downloading = False
        self.download_all_btn.config(state="normal", text="⬇  DOWNLOAD ALL TO LIBRARY")
        self.progress_label.config(text="All downloads complete!")
        self.progress_bar["value"] = 100
        self._set_status("Downloads complete.")
        self._refresh_library()
        messagebox.showinfo("Complete", "All tracks have been processed!")

    def _refresh_library(self):
        for item in self.lib_tree.get_children():
            self.lib_tree.delete(item)

        downloads = self.db.get_all_downloads()
        for row in downloads:
            date_str = row["downloaded_at"][:10] if row["downloaded_at"] else ""
            self.lib_tree.insert(
                "",
                "end",
                values=(
                    row["title"] or "--",
                    row["artist"] or "--",
                    row["album"] or "--",
                    row["duration"] or "--",
                    date_str,
                ),
            )

        stats = self.db.get_library_stats()
        size_mb = stats["total_size_bytes"] / (1024 * 1024)
        self.lib_stats_label.config(text=f"♫ {stats['total_tracks']} tracks   •   {size_mb:.1f} MB")

    def _open_music_folder(self):
        music_dir = self.db.get_setting("music_dir")
        if music_dir and os.path.isdir(music_dir):
            webbrowser.open(f"file://{os.path.abspath(music_dir)}")
        else:
            messagebox.showinfo("Folder Not Found", "Music folder has not been created yet.")

    def _open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("TuneVault Settings")
        settings_win.geometry("540x380")
        settings_win.configure(bg=COLORS["bg_dark"])
        settings_win.transient(self.root)
        settings_win.grab_set()

        tk.Label(
            settings_win,
            text="OPTIONS",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["yellow"],
        ).pack(pady=(18, 20))

        dir_frame = tk.Frame(settings_win, bg=COLORS["bg_dark"])
        dir_frame.pack(fill="x", padx=28, pady=5)

        tk.Label(
            dir_frame,
            text="Music Folder:",
            font=FONT_BODY_BOLD,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        dir_var = tk.StringVar(value=self.db.get_setting("music_dir"))
        dir_entry = tk.Entry(
            dir_frame,
            textvariable=dir_var,
            font=FONT_BODY,
            bg=COLORS["input_bg"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["yellow"],
            relief="flat",
            bd=8,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        dir_entry.pack(side="left", fill="x", expand=True, pady=(6, 0))

        def browse():
            path = filedialog.askdirectory()
            if path:
                dir_var.set(path)

        browse_btn = self._make_button(dir_frame, "BROWSE", browse)
        browse_btn.pack(side="right", padx=(8, 0), pady=(6, 0))

        br_frame = tk.Frame(settings_win, bg=COLORS["bg_dark"])
        br_frame.pack(fill="x", padx=28, pady=18)

        tk.Label(
            br_frame,
            text="Audio Quality (kbps):",
            font=FONT_BODY_BOLD,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        br_var = tk.StringVar(value=self.db.get_setting("bitrate") or "320")
        br_menu = ttk.Combobox(
            br_frame,
            textvariable=br_var,
            values=["128", "192", "256", "320"],
            state="readonly",
            width=12,
        )
        br_menu.pack(anchor="w", pady=6)

        tk.Label(
            settings_win,
            text=(
                "Legal Notice: TuneVault is for personal use only.\n"
                "Downloading copyrighted content without permission may\n"
                "violate your local laws. Use responsibly."
            ),
            font=("Segoe UI", 9),
            bg=COLORS["bg_dark"],
            fg=COLORS["yellow"],
            justify="center",
        ).pack(pady=16)

        def save_settings():
            self.db.set_setting("music_dir", dir_var.get().strip())
            self.db.set_setting("bitrate", br_var.get())
            settings_win.destroy()
            self._set_status("Settings saved.")

        save_btn = self._make_button(settings_win, "SAVE SETTINGS", save_settings, primary=True, width=18)
        save_btn.pack(pady=8)

    def _on_close(self):
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()

    try:
        if sys.platform == "win32":
            root.iconbitmap(default="")
    except Exception:
        pass

    TuneVaultApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
