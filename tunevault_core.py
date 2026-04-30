import os
import re
import json
import subprocess
import tempfile
import shutil

import imageio_ffmpeg
from yt_dlp import YoutubeDL


class VideoInfo:
    """Holds metadata for a single video."""

    def __init__(self, video_id="", title="", url="", artist="",
                 album="", genre="", year="", duration=0):
        self.video_id = video_id
        self.title = title
        self.url = url
        self.artist = artist
        self.album = album
        self.genre = genre
        self.year = year
        self.duration = duration

    @property
    def duration_str(self):
        if not self.duration:
            return "0:00"
        mins = int(self.duration) // 60
        secs = int(self.duration) % 60
        return f"{mins}:{secs:02d}"


def safe_filename(value):
    value = value or "Unknown"
    value = re.sub(r'[\\/*?:"<>|]', "_", value).strip(". ")
    return value or "Unknown"


class TuneVaultCore:
    """
    Backend engine for TuneVault.

    This version is designed for a bundled Windows app:
    - yt-dlp is used as a Python library, not a PATH command.
    - ffmpeg is supplied by imageio-ffmpeg, not system PATH.
    """

    def __init__(self, db):
        self.db = db
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    def get_dependency_status(self):
        return {
            "yt_dlp": True,
            "ffmpeg": bool(self.ffmpeg_path and os.path.exists(self.ffmpeg_path)),
        }

    def fetch_video_info(self, url):
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }

        with YoutubeDL(opts) as ydl:
            data = ydl.extract_info(url, download=False)

        entries = data.get("entries") if isinstance(data, dict) else None
        if not entries:
            entries = [data]

        videos = []
        for item in entries:
            if not item:
                continue

            upload_date = item.get("upload_date", "") or ""
            year_val = str(item.get("release_year") or "")
            if not year_val and len(upload_date) >= 4:
                year_val = upload_date[:4]

            video_url = item.get("webpage_url") or item.get("url") or url
            if item.get("id") and not str(video_url).startswith("http"):
                video_url = f"https://www.youtube.com/watch?v={item.get('id')}"

            videos.append(VideoInfo(
                video_id=item.get("id", ""),
                title=item.get("title", "Unknown"),
                url=video_url,
                artist=item.get("artist") or item.get("uploader") or "Unknown Artist",
                album=item.get("album") or "Singles",
                genre=item.get("genre") or "",
                year=year_val,
                duration=item.get("duration", 0) or 0,
            ))

        if not videos:
            raise RuntimeError("No videos found at that URL.")

        return videos

    def download_track(self, info, progress_callback=None):
        music_dir = self.db.get_setting("music_dir")
        bitrate = self.db.get_setting("bitrate") or "320"

        if not music_dir:
            music_dir = os.path.join(os.path.expanduser("~"), "Music", "TuneVault")

        dest_dir = music_dir
        os.makedirs(dest_dir, exist_ok=True)

        title = safe_filename(info.title or "Unknown Track")
        output_template = os.path.join(dest_dir, f"{title}.%(ext)s")
        final_path = os.path.join(dest_dir, f"{title}.mp3")

        def hook(d):
            if not progress_callback:
                return
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                pct = int((downloaded / total) * 70) if total else 20
                progress_callback("downloading", min(max(pct, 10), 75), f"Downloading: {info.title}")
            elif status == "finished":
                progress_callback("converting", 80, f"Converting to MP3: {info.title}")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "ffmpeg_location": self.ffmpeg_path,
            "progress_hooks": [hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(bitrate),
                },
                {"key": "FFmpegMetadata"},
            ],
        }

        if progress_callback:
            progress_callback("starting", 5, f"Starting: {info.title}")

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([info.url])

        file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

        self.db.add_download(
            video_id=info.video_id,
            title=info.title,
            url=info.url,
            artist=info.artist,
            album=info.album,
            genre=info.genre,
            year=info.year,
            duration=info.duration_str,
            file_path=final_path,
            file_size=file_size,
        )

        if progress_callback:
            progress_callback("complete", 100, f"Complete: {info.title}")

        return final_path
