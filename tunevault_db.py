import sqlite3
import os
from datetime import datetime


class TuneVaultDB:

    def __init__(self, db_path="tunevault.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # ── Table Setup ──────────────────────────────────────────────

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                title TEXT,
                artist TEXT,
                album TEXT,
                genre TEXT,
                year TEXT,
                duration TEXT,
                url TEXT,
                file_path TEXT,
                file_size INTEGER DEFAULT 0,
                format TEXT DEFAULT 'mp3',
                status TEXT DEFAULT 'completed',
                downloaded_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Set default settings if they don't exist
        defaults = {
            "music_dir": os.path.join(os.path.expanduser("~"), "Music", "TuneVault"),
            "bitrate": "320",
        }
        for key, value in defaults.items():
            cursor.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value),
            )

        self.conn.commit()

    # ── Downloads ────────────────────────────────────────────────

    def add_download(self, video_id, title, url, artist="", album="",
                     genre="", year="", duration="", file_path="",
                     file_size=0, fmt="mp3"):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO downloads
                (video_id, title, url, artist, album, genre, year,
                 duration, file_path, file_size, format, downloaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_id, title, url, artist, album, genre, year,
            duration, file_path, file_size, fmt, datetime.now().isoformat()
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_downloads(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM downloads ORDER BY downloaded_at DESC')
        return cursor.fetchall()

    def is_duplicate(self, video_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM downloads WHERE video_id = ?', (video_id,))
        return cursor.fetchone() is not None

    def delete_download(self, download_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM downloads WHERE id = ?', (download_id,))
        self.conn.commit()

    # ── Library Stats ────────────────────────────────────────────

    def get_library_stats(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count, COALESCE(SUM(file_size), 0) as size FROM downloads')
        row = cursor.fetchone()
        return {
            "total_tracks": row["count"],
            "total_size_bytes": row["size"],
        }

    # ── Settings ─────────────────────────────────────────────────

    def get_setting(self, key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row["value"] if row else None

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value),
        )
        self.conn.commit()

    # ── Cleanup ──────────────────────────────────────────────────

    def close(self):
        self.conn.close()