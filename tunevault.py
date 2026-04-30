import customtkinter as ctk
import tkinter as tk

ctk.set_appearance_mode("dark")

COLORS = {
    "bg_main": "#0A192F",
    "bg_card": "#112240",
    "accent": "#FFD166",
    "accent_hover": "#FFE8A3",
    "text_main": "#E6F1FF",
    "text_dim": "#8892B0",
    "border": "#1F4068"
}

class TuneVaultApp:

    def __init__(self, root):
        self.root = root
        self.root.title("TuneVault")
        self.root.geometry("1000x650")
        self.root.configure(fg_color=COLORS["bg_main"])

        self.build_ui()

    def build_ui(self):
        self.build_header()
        self.build_input()
        self.build_tabs()
        self.build_table()
        self.build_download_button()
        self.build_progress()

    # ───────────────────────── HEADER ─────────────────────────

    def build_header(self):
        frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg_card"], corner_radius=10)
        frame.pack(fill="x", padx=10, pady=10)

        title = ctk.CTkLabel(
            frame,
            text="TUNEVAULT",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS["accent"]
        )
        title.pack(side="left", padx=20, pady=10)

        subtitle = ctk.CTkLabel(
            frame,
            text="YouTube to MP3 Personal Music Library",
            text_color=COLORS["text_dim"]
        )
        subtitle.pack(side="left", padx=10)

        btn = ctk.CTkButton(
            frame,
            text="OPTIONS",
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["accent"],
            text_color=COLORS["accent"],
            hover_color=COLORS["accent"]
        )
        btn.pack(side="right", padx=20)

    # ───────────────────────── INPUT ─────────────────────────

    def build_input(self):
        frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg_card"])
        frame.pack(fill="x", padx=10, pady=5)

        label = ctk.CTkLabel(
            frame,
            text="Paste a YouTube URL (video or playlist):",
            text_color=COLORS["accent"]
        )
        label.pack(anchor="w", padx=15, pady=5)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=5)

        self.entry = ctk.CTkEntry(inner, height=40)
        self.entry.pack(side="left", fill="x", expand=True, padx=5)

        paste_btn = ctk.CTkButton(inner, text="PASTE")
        paste_btn.pack(side="left", padx=5)

        fetch_btn = ctk.CTkButton(
            inner,
            text="FETCH",
            fg_color=COLORS["accent"],
            text_color="#000",
            hover_color=COLORS["accent_hover"]
        )
        fetch_btn.pack(side="left", padx=5)

    # ───────────────────────── TABS ─────────────────────────

    def build_tabs(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)

        self.download_tab = ctk.CTkButton(
            frame,
            text="DOWNLOAD",
            fg_color=COLORS["bg_card"],
            border_width=2,
            border_color=COLORS["accent"],
            text_color=COLORS["accent"]
        )
        self.download_tab.pack(side="left", padx=5)

        self.library_tab = ctk.CTkButton(
            frame,
            text="LIBRARY",
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text_dim"]
        )
        self.library_tab.pack(side="left", padx=5)

    # ───────────────────────── TABLE ─────────────────────────

    def build_table(self):
        frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg_card"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header, text="#", width=50).pack(side="left")
        ctk.CTkLabel(header, text="TITLE").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="DURATION").pack(side="right", padx=10)

        # Example row (this will be dynamic later)
        row = ctk.CTkFrame(frame, fg_color="#0F223D", corner_radius=8)
        row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(row, text="01", width=50).pack(side="left", padx=5)

        ctk.CTkLabel(
            row,
            text="Bon Jovi - Livin’ On A Prayer",
            text_color=COLORS["text_main"]
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            row,
            text="4:09",
            text_color=COLORS["accent"]
        ).pack(side="right", padx=10)

        details = ctk.CTkLabel(
            frame,
            text="Artist: Bon Jovi     Album: Singles     Year: 2009     Downloaded ✓",
            text_color=COLORS["text_dim"]
        )
        details.pack(anchor="w", padx=20)

    # ───────────────────────── DOWNLOAD BUTTON ─────────────────────────

    def build_download_button(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.pack(pady=10)

        btn = ctk.CTkButton(
            frame,
            text="⬇ DOWNLOAD ALL TO LIBRARY",
            height=50,
            width=350,
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["accent"],
            text_color=COLORS["accent"],
            hover_color=COLORS["accent"]
        )
        btn.pack()

    # ───────────────────────── PROGRESS ─────────────────────────

    def build_progress(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=10)

        label = ctk.CTkLabel(
            frame,
            text="All downloads complete!",
            text_color=COLORS["accent"]
        )
        label.pack(anchor="w", padx=10)

        self.progress = ctk.CTkProgressBar(
            frame,
            progress_color=COLORS["accent"]
        )
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(1.0)


if __name__ == "__main__":
    root = ctk.CTk()
    app = TuneVaultApp(root)
    root.mainloop()
