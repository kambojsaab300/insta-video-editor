import os
import re
import shutil
from typing import Optional, Dict, Any
import yt_dlp
import imageio_ffmpeg

# Ensure ffmpeg binary is always on PATH for yt-dlp
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{ffmpeg_dir}:{os.environ.get('PATH', '')}"

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_instagram_video(url: str, output_dir: str = "downloads") -> Dict[str, Any]:
    """
    Downloads an Instagram video/reel using yt-dlp.
    Returns a dict with 'status', 'filepath', 'title', 'duration', etc.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Template for output
    outtmpl = os.path.join(output_dir, "%(id)s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg_exe,
        'quiet': False,
        'no_warnings': False,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info:
            # Playlist or multi-item post
            info = info['entries'][0]
            
        video_id = info.get('id', 'video')
        ext = info.get('ext', 'mp4')
        filepath = os.path.join(output_dir, f"{video_id}.{ext}")
        
        # Verify file existence or fallback to downloaded filename
        if not os.path.exists(filepath):
            # Check if any file with video_id exists
            for f in os.listdir(output_dir):
                if f.startswith(video_id):
                    filepath = os.path.join(output_dir, f)
                    break

        return {
            'success': True,
            'filepath': filepath,
            'id': video_id,
            'title': info.get('title', 'Instagram Video'),
            'duration': info.get('duration', 0),
            'width': info.get('width'),
            'height': info.get('height')
        }

def _js_runtimes() -> Dict[str, Dict]:
    """yt-dlp only enables deno by default; register any runtime that is installed."""
    runtimes = {}
    for name in ("deno", "node", "bun"):
        path = shutil.which(name)
        if path:
            runtimes[name] = {"path": path}
    return runtimes

def download_youtube_video(url: str, output_dir: str = "downloads", quality: str = "1080p") -> Dict[str, Any]:
    """
    Downloads a YouTube video or Short using yt-dlp with specific quality/resolution.
    Tries the default web clients first (full quality, needs a JS runtime), then falls
    back to mobile/TV clients if YouTube blocks the request.
    Returns dict with filepath, title, id, width, height, etc.
    """
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "yt_%(id)s.%(ext)s")

    height_map = {
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360
    }

    # Prefer H.264 (avc1) so ffmpeg processing and phone playback work everywhere
    h = height_map.get(quality)
    hf = f"[height<={h}]" if h else ""
    fmt = (
        f"bestvideo{hf}[vcodec^=avc1]+bestaudio[ext=m4a]/"
        f"bestvideo{hf}[ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo{hf}+bestaudio/best{hf}/best"
    )

    client_strategies = [
        None,                      # yt-dlp defaults (best quality)
        ['tv', 'web_safari'],
        ['android', 'ios'],
        ['mweb', 'web_embedded'],
    ]
    js_runtimes = _js_runtimes()

    last_error = ""
    for clients in client_strategies:
        ydl_opts = {
            'format': fmt,
            'outtmpl': outtmpl,
            'merge_output_format': 'mp4',
            'ffmpeg_location': ffmpeg_exe,
            'quiet': False,
            'no_warnings': True,
            'noprogress': True,
            'retries': 3,
        }
        if js_runtimes:
            ydl_opts['js_runtimes'] = js_runtimes
        if clients:
            ydl_opts['extractor_args'] = {'youtube': {'player_client': clients}}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:
                    info = info['entries'][0]

                video_id = info.get('id', 'yt_video')
                ext = info.get('ext', 'mp4')
                filepath = os.path.join(output_dir, f"yt_{video_id}.{ext}")

                if not os.path.exists(filepath):
                    for f in os.listdir(output_dir):
                        if f.startswith(f"yt_{video_id}") and not f.endswith(".part"):
                            filepath = os.path.join(output_dir, f)
                            break

                if os.path.exists(filepath):
                    return {
                        'success': True,
                        'filepath': filepath,
                        'id': video_id,
                        'title': info.get('title', 'YouTube Video'),
                        'duration': info.get('duration', 0),
                        'width': info.get('width'),
                        'height': info.get('height')
                    }
        except Exception as e:
            last_error = str(e)
            continue

    if "not a bot" in last_error or "Sign in" in last_error:
        return {
            'success': False,
            'error': "YouTube blocked this server (\"Sign in to confirm you're not a bot\"). Try again later or run the app locally."
        }
    return {
        'success': False,
        'error': f"Failed to download ({last_error})"
    }
