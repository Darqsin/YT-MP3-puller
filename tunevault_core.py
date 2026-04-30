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
    value = re.sub(r"\s+", " ", value).strip()
    return value or "Unknown"


JUNK_BRACKET_RE = re.compile(
    r"\s*[\(\[]\s*[^\)\]]*"
    r"(?:official|music\s*video|lyric|lyrics|video|audio|hd|4k|upgrade|visualizer|remaster|remastered|explicit|clean|hq)"
    r"[^\)\]]*[\)\]]\s*",
    re.IGNORECASE,
)

JUNK_TEXT_RE = re.compile(
    r"\s*[-|:]?\s*"
    r"(?:official\s*)?(?:music\s*)?(?:lyric|lyrics|video|audio|visualizer)"
    r"(?:\s*video)?\s*$",
    re.IGNORECASE,
)


def _norm_name(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def clean_youtube_title(raw_title, fallback_artist=""):
    """
    Clean YouTube-style titles and return (artist, track_title).

    Handles both:
        Artist - Song
        Song - Artist

    Example:
        Numb (Official Music Video) [4K UPGRADE] – Linkin Park
        -> (Linkin Park, Numb)
    """
    title = raw_title or "Unknown Track"
    title = title.replace("–", "-").replace("—", "-").replace("−", "-")
    title = JUNK_BRACKET_RE.sub(" ", title)
    title = re.sub(r"\s+", " ", title).strip(" -|:.")
    title = JUNK_TEXT_RE.sub("", title).strip(" -|:.")

    fallback_artist = (fallback_artist or "").strip()
    if _norm_name(fallback_artist) in {"", "unknown", "unknownartist", "variousartists"}:
        fallback_artist = ""

    parts = [p.strip(" -|:.") for p in re.split(r"\s+-\s+", title) if p.strip(" -|:.")]

    artist = fallback_artist
    track = title

    if len(parts) >= 2:
        left = parts[0]
        right = parts[-1]
        left_norm = _norm_name(left)
        right_norm = _norm_name(right)
        fallback_norm = _norm_name(fallback_artist)

        if fallback_norm and right_norm == fallback_norm:
            artist = right
            track = " - ".join(parts[:-1]).strip()
        elif fallback_norm and left_norm == fallback_norm:
            artist = left
            track = " - ".join(parts[1:]).strip()
        elif fallback_norm and right_norm in fallback_norm:
            artist = fallback_artist
            track = " - ".join(parts[:-1]).strip()
        elif fallback_norm and left_norm in fallback_norm:
            artist = fallback_artist
            track = " - ".join(parts[1:]).strip()
        else:
            # Common YouTube pattern when official artist channel uploads as "Song - Artist".
            # Keep the likely artist first in the saved filename.
            if len(right.split()) <= max(3, len(left.split())):
                artist = right
                track = " - ".join(parts[:-1]).strip()
            else:
                artist = left
                track = " - ".join(parts[1:]).strip()

    track = JUNK_BRACKET_RE.sub(" ", track)
    track = JUNK_TEXT_RE.sub("", track)
    track = re.sub(r"\s+", " ", track).strip(" -|:.") or "Unknown Track"
    artist = re.sub(r"\s+", " ", artist).strip(" -|:.")

    return artist, track


def make_track_filename(artist, title):
    artist = safe_filename(artist) if artist else ""
    title = safe_filename(title or "Unknown Track")
    if artist and _norm_name(artist) not in {"unknown", "unknownartist"}:
        return f"{artist} - {title}"
    return title


def unique_output_base(dest_dir, base_name):
    """Return a filename base that will not overwrite an existing MP3."""
    candidate = base_name
    counter = 2
    while os.path.exists(os.path.join(dest_dir, f"{candidate}.mp3")):
        candidate = f"{base_name} ({counter})"
        counter += 1
    return candidate


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

            raw_title = item.get("title", "Unknown")
            raw_artist = item.get("artist") or item.get("creator") or item.get("uploader") or ""
            clean_artist, clean_title = clean_youtube_title(raw_title, raw_artist)

            videos.append(VideoInfo(
                video_id=item.get("id", ""),
                title=clean_title,
                url=video_url,
                artist=clean_artist or raw_artist or "Unknown Artist",
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

        clean_artist, clean_title = clean_youtube_title(info.title or "Unknown Track", info.artist)
        info.artist = clean_artist or info.artist or "Unknown Artist"
        info.title = clean_title or info.title or "Unknown Track"

        base_name = make_track_filename(info.artist, info.title)
        base_name = unique_output_base(dest_dir, base_name)
        output_template = os.path.join(dest_dir, f"{base_name}.%(ext)s")
        final_path = os.path.join(dest_dir, f"{base_name}.mp3")

        def hook(d):
            if not progress_callback:
                return
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                pct = int((downloaded / total) * 70) if total else 20
                progress_callback("downloading", min(max(pct, 10), 75), f"Downloading: {info.artist} - {info.title}")
            elif status == "finished":
                progress_callback("converting", 80, f"Converting to MP3: {info.artist} - {info.title}")

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
            progress_callback("starting", 5, f"Starting: {info.artist} - {info.title}")

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
            progress_callback("complete", 100, f"Complete: {info.artist} - {info.title}")

        return final_path
