"""
TuneVault - Desktop MP3 Scraper Application
Main GUI built with Tkinter.
"""

import os
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

from tunevault_core import TuneVaultCore
from tunevault_db import TuneVaultDB


# Color Theme
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_mid": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b81",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#e74c3c",
    "input_bg": "#1c2541",
    "border": "#2a2a4a",
}


class TuneVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TuneVault -- YouTube to MP3")
        self.root.geometry("900x700")
        self.root.minsize(750, 550)
        self.root.configure(bg=COLORS["bg_dark"])

        # Initialize backend
        self.db = TuneVaultDB()
        self.core = TuneVaultCore(self.db)

        # State
        self.current_videos = []
        self.track_entries = []
        self.is_downloading = False

        # Check dependencies
        self._check_deps()

        # Build UI
        self._build_header()
        self._build_input_section()
        self._build_notebook()
        self._build_status_bar()

        # Protocol for clean exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _check_deps(self):
        status = self.core.get_dependency_status()
        self.deps_ok = status["yt_dlp"] and status["ffmpeg"]

        if not self.deps_ok:
            missing = []
            if not status["yt_dlp"]:
                missing.append("yt-dlp (pip install yt-dlp)")
            if not status["ffmpeg"]:
                missing.append("ffmpeg (https://ffmpeg.org/download.html)")

            messagebox.showwarning(
                "Missing Dependencies",
                "The following tools are required but not found:\n\n"
                + "\n".join(missing)
                + "\n\nPlease install them and restart TuneVault.",
            )

    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["bg_mid"], height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="TuneVault",
            font=("Helvetica", 22, "bold"),
            bg=COLORS["bg_mid"],
            fg=COLORS["accent"],
        )
        title_label.pack(side="left", padx=20, pady=10)

        subtitle = tk.Label(
            header,
            text="YouTube to MP3 Personal Music Library",
            font=("Helvetica", 10),
            bg=COLORS["bg_mid"],
            fg=COLORS["text_secondary"],
        )
        subtitle.pack(side="left", pady=10)

        settings_btn = tk.Button(
            header,
            text="Settings",
            font=("Helvetica", 10),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            relief="flat",
            cursor="hand2",
            command=self._open_settings,
        )
        settings_btn.pack(side="right", padx=20, pady=15)

    def _build_input_section(self):
        input_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        input_frame.pack(fill="x", padx=20, pady=(15, 5))

        label = tk.Label(
            input_frame,
            text="Paste a YouTube URL (video or playlist):",
            font=("Helvetica", 11),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        label.pack(anchor="w")

        entry_frame = tk.Frame(input_frame, bg=COLORS["bg_dark"])
        entry_frame.pack(fill="x", pady=(5, 0))

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            entry_frame,
            textvariable=self.url_var,
            font=("Helvetica", 13),
            bg=COLORS["input_bg"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat",
            bd=8,
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self._on_fetch())

        paste_btn = tk.Button(
            entry_frame,
            text="Paste",
            font=("Helvetica", 10),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            relief="flat",
            cursor="hand2",
            padx=12,
            command=self._paste_clipboard,
        )
        paste_btn.pack(side="left", padx=(5, 0))

        self.fetch_btn = tk.Button(
            entry_frame,
            text="Fetch",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["accent"],
            fg=COLORS["text_primary"],
            relief="flat",
            cursor="hand2",
            padx=18,
            command=self._on_fetch,
        )
        self.fetch_btn.pack(side="left", padx=(5, 0))

    def _paste_clipboard(self):
        try:
            text = self.root.clipboard_get()
            self.url_var.set(text.strip())
        except tk.TclError:
            pass

    def _build_notebook(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLORS["bg_dark"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=COLORS["bg_mid"],
            foreground=COLORS["text_secondary"],
            padding=[15, 8],
            font=("Helvetica", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["bg_card"])],
            foreground=[("selected", COLORS["text_primary"])],
        )

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self.preview_tab = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.notebook.add(self.preview_tab, text=" Download ")

        self.library_tab = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.notebook.add(self.library_tab, text=" Library ")

        self._build_preview_tab()
        self._build_library_tab()

    def _build_preview_tab(self):
        self.track_list_frame = tk.Frame(self.preview_tab, bg=COLORS["bg_dark"])
        self.track_list_frame.pack(fill="both", expand=True, pady=5)

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
                "\n\nPaste a YouTube link above and click Fetch\n"
                "to preview tracks before downloading.\n\n"
                "Supports single videos and playlists."
            ),
            font=("Helvetica", 12),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            justify="center",
        )
        self.placeholder_label.pack(pady=80)

        self.download_all_frame = tk.Frame(self.preview_tab, bg=COLORS["bg_dark"])
        self.download_all_btn = tk.Button(
            self.download_all_frame,
            text="Download All to Library",
            font=("Helvetica", 12, "bold"),
            bg=COLORS["success"],
            fg=COLORS["text_primary"],
            relief="flat",
            cursor="hand2",
            padx=25,
            pady=8,
            command=self._on_download_all,
        )
        self.download_all_btn.pack(pady=10)

        self.progress_frame = tk.Frame(self.preview_tab, bg=COLORS["bg_dark"])
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Helvetica", 10),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.progress_label.pack(anchor="w")

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            length=400,
        )
        self.progress_bar.pack(fill="x", pady=(3, 8))

    def _build_library_tab(self):
        top_bar = tk.Frame(self.library_tab, bg=COLORS["bg_dark"])
        top_bar.pack(fill="x", pady=(5, 10))

        self.lib_stats_label = tk.Label(
            top_bar,
            text="",
            font=("Helvetica", 10),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.lib_stats_label.pack(side="left")

        refresh_btn = tk.Button(
            top_bar,
            text="Refresh",
            font=("Helvetica", 9),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            relief="flat",
            cursor="hand2",
            command=self._refresh_library,
        )
        refresh_btn.pack(side="right")

        open_folder_btn = tk.Button(
            top_bar,
            text="Open Music Folder",
            font=("Helvetica", 9),
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            relief="flat",
            cursor="hand2",
            command=self._open_music_folder,
        )
        open_folder_btn.pack(side="right", padx=(0, 10))

        columns = ("title", "artist", "album", "duration", "date")
        self.lib_tree = ttk.Treeview(
            self.library_tab,
            columns=columns,
            show="headings",
            height=18,
        )
        self.lib_tree.heading("title", text="Title")
        self.lib_tree.heading("artist", text="Artist")
        self.lib_tree.heading("album", text="Album")
        self.lib_tree.heading("duration", text="Duration")
        self.lib_tree.heading("date", text="Date Added")

        self.lib_tree.column("title", width=250)
        self.lib_tree.column("artist", width=150)
        self.lib_tree.column("album", width=120)
        self.lib_tree.column("duration", width=70, anchor="center")
        self.lib_tree.column("date", width=100, anchor="center")

        style = ttk.Style()
        style.configure(
            "Treeview",
            background=COLORS["bg_mid"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_mid"],
            font=("Helvetica", 10),
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            font=("Helvetica", 10, "bold"),
        )

        lib_scroll = ttk.Scrollbar(
            self.library_tab,
            orient="vertical",
            command=self.lib_tree.yview,
        )
        self.lib_tree.configure(yscrollcommand=lib_scroll.set)
        self.lib_tree.pack(side="left", fill="both", expand=True)
        lib_scroll.pack(side="right", fill="y")

        self._refresh_library()

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg=COLORS["bg_mid"], height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_bar,
            text="Ready",
            font=("Helvetica", 9),
            bg=COLORS["bg_mid"],
            fg=COLORS["text_secondary"],
        )
        self.status_label.pack(side="left", padx=15)

        deps = self.core.get_dependency_status()
        dep_text = (
            f"yt-dlp: {'OK' if deps['yt_dlp'] else 'Missing'} | "
            f"ffmpeg: {'OK' if deps['ffmpeg'] else 'Missing'}"
        )
        dep_label = tk.Label(
            self.status_bar,
            text=dep_text,
            font=("Helvetica", 9),
            bg=COLORS["bg_mid"],
            fg=COLORS["text_secondary"],
        )
        dep_label.pack(side="right", padx=15)

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

        self.fetch_btn.config(state="disabled", text="Fetching...")
        self._set_status("Fetching video info...")
        self._clear_preview()

        def do_fetch():
            try:
                videos = self.core.fetch_video_info(url)
                self.root.after(0, lambda: self._display_preview(videos))
            except Exception as exc:
                self.root.after(
                    0,
                    lambda err=str(exc): messagebox.showerror("Fetch Error", err),
                )
            finally:
                self.root.after(
                    0,
                    lambda: self.fetch_btn.config(state="normal", text="Fetch"),
                )
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

        for i, info in enumerate(videos):
            card = tk.Frame(
                self.scrollable_frame,
                bg=COLORS["bg_card"],
                padx=12,
                pady=8,
                highlightbackground=COLORS["border"],
                highlightthickness=1,
            )
            card.pack(fill="x", padx=5, pady=3)

            header = tk.Frame(card, bg=COLORS["bg_card"])
            header.pack(fill="x")

            num_label = tk.Label(
                header,
                text=f"#{i + 1}",
                font=("Helvetica", 10, "bold"),
                bg=COLORS["bg_card"],
                fg=COLORS["accent"],
                width=4,
            )
            num_label.pack(side="left")

            entry_data = {}

            title_var = tk.StringVar(value=info.title)
            title_entry = tk.Entry(
                header,
                textvariable=title_var,
                font=("Helvetica", 11, "bold"),
                bg=COLORS["input_bg"],
                fg=COLORS["text_primary"],
                insertbackground=COLORS["text_primary"],
                relief="flat",
                bd=3,
            )
            title_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            entry_data["title"] = title_var

            dur_label = tk.Label(
                header,
                text=info.duration_str,
                font=("Helvetica", 10),
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"],
            )
            dur_label.pack(side="right")

            meta_frame = tk.Frame(card, bg=COLORS["bg_card"])
            meta_frame.pack(fill="x", pady=(4, 0))

            for field_name, default_val, label_text in [
                ("artist", info.artist, "Artist:"),
                ("album", info.album, "Album:"),
                ("genre", info.genre, "Genre:"),
                ("year", info.year, "Year:"),
            ]:
                lbl = tk.Label(
                    meta_frame,
                    text=label_text,
                    font=("Helvetica", 9),
                    bg=COLORS["bg_card"],
                    fg=COLORS["text_secondary"],
                )
                lbl.pack(side="left", padx=(8, 2))

                var = tk.StringVar(value=default_val)
                entry = tk.Entry(
                    meta_frame,
                    textvariable=var,
                    font=("Helvetica", 9),
                    bg=COLORS["input_bg"],
                    fg=COLORS["text_primary"],
                    insertbackground=COLORS["text_primary"],
                    relief="flat",
                    bd=2,
                    width=14,
                )
                entry.pack(side="left", padx=(0, 4))
                entry_data[field_name] = var

            if self.db.is_duplicate(info.video_id):
                dup_label = tk.Label(
                    meta_frame,
                    text="Already downloaded",
                    font=("Helvetica", 9),
                    bg=COLORS["bg_card"],
                    fg=COLORS["warning"],
                )
                dup_label.pack(side="right", padx=5)

            status_var = tk.StringVar(value="")
            status_label = tk.Label(
                card,
                textvariable=status_var,
                font=("Helvetica", 9),
                bg=COLORS["bg_card"],
                fg=COLORS["success"],
            )
            status_label.pack(anchor="e")

            self.track_entries.append(
                {
                    "info": info,
                    "fields": entry_data,
                    "status_var": status_var,
                }
            )

        self.download_all_frame.pack(fill="x", padx=5)
        self._set_status(f"Found {len(videos)} track(s). Edit metadata and click Download.")

    def _on_download_all(self):
        if self.is_downloading:
            return

        self.is_downloading = True
        self.download_all_btn.config(state="disabled", text="Downloading...")
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
                    self.root.after(
                        0,
                        lambda m=msg, o=overall: self._update_progress(m, o),
                    )
                    if stage == "complete":
                        self.root.after(
                            0,
                            lambda e=_entry: e["status_var"].set("Downloaded"),
                        )

                try:
                    self.core.download_track(info, progress_callback=progress_cb)
                except Exception as exc:
                    self.root.after(
                        0,
                        lambda e=entry, err=str(exc): e["status_var"].set(
                            f"Error: {err[:60]}"
                        ),
                    )

            self.root.after(0, self._download_complete)

        threading.Thread(target=do_download, daemon=True).start()

    def _update_progress(self, message, overall_pct):
        self.progress_label.config(text=message)
        self.progress_bar["value"] = overall_pct
        self._set_status(message)

    def _download_complete(self):
        self.is_downloading = False
        self.download_all_btn.config(state="normal", text="Download All to Library")
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
        self.lib_stats_label.config(
            text=f"{stats['total_tracks']} tracks - {size_mb:.1f} MB"
        )

    def _open_music_folder(self):
        music_dir = self.db.get_setting("music_dir")
        if music_dir and os.path.isdir(music_dir):
            webbrowser.open(f"file://{os.path.abspath(music_dir)}")
        else:
            messagebox.showinfo(
                "Folder Not Found",
                "Music folder has not been created yet.",
            )

    def _open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("TuneVault Settings")
        settings_win.geometry("500x350")
        settings_win.configure(bg=COLORS["bg_dark"])
        settings_win.transient(self.root)
        settings_win.grab_set()

        tk.Label(
            settings_win,
            text="Settings",
            font=("Helvetica", 16, "bold"),
            bg=COLORS["bg_dark"],
            fg=COLORS["accent"],
        ).pack(pady=(15, 20))

        dir_frame = tk.Frame(settings_win, bg=COLORS["bg_dark"])
        dir_frame.pack(fill="x", padx=25, pady=5)

        tk.Label(
            dir_frame,
            text="Music Folder:",
            font=("Helvetica", 10),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        dir_var = tk.StringVar(value=self.db.get_setting("music_dir"))
        dir_entry = tk.Entry(
            dir_frame,
            textvariable=dir_var,
            font=("Helvetica", 10),
            bg=COLORS["input_bg"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat",
            bd=5,
        )
        dir_entry.pack(side="left", fill="x", expand=True)

        def browse():
            path = filedialog.askdirectory()
            if path:
                dir_var.set(path)

        tk.Button(
            dir_frame,
            text="Browse",
            command=browse,
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            relief="flat",
        ).pack(side="right", padx=(5, 0))

        br_frame = tk.Frame(settings_win, bg=COLORS["bg_dark"])
        br_frame.pack(fill="x", padx=25, pady=15)

        tk.Label(
            br_frame,
            text="Audio Quality (kbps):",
            font=("Helvetica", 10),
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        br_var = tk.StringVar(value=self.db.get_setting("bitrate") or "320")
        br_menu = ttk.Combobox(
            br_frame,
            textvariable=br_var,
            values=["128", "192", "256", "320"],
            state="readonly",
            width=10,
        )
        br_menu.pack(anchor="w", pady=5)

        tk.Label(
            settings_win,
            text=(
                "Legal Notice: TuneVault is for personal use only.\n"
                "Downloading copyrighted content without permission may\n"
                "violate your local laws. Use responsibly."
            ),
            font=("Helvetica", 9),
            bg=COLORS["bg_dark"],
            fg=COLORS["warning"],
            justify="center",
        ).pack(pady=20)

        def save_settings():
            self.db.set_setting("music_dir", dir_var.get().strip())
            self.db.set_setting("bitrate", br_var.get())
            settings_win.destroy()
            self._set_status("Settings saved.")

        tk.Button(
            settings_win,
            text="Save Settings",
            font=("Helvetica", 11, "bold"),
            bg=COLORS["success"],
            fg=COLORS["text_primary"],
            relief="flat",
            padx=20,
            pady=6,
            command=save_settings,
        ).pack(pady=10)

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
