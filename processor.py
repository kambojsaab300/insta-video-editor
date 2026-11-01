import os
import subprocess
import re
from typing import Tuple, Dict, Any, Optional
import imageio_ffmpeg
from PIL import Image

def get_ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_video_info(video_path: str) -> Dict[str, Any]:
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [ffmpeg_exe, "-i", video_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    
    # Extract dimensions
    dim_match = re.search(r'Stream.*Video.*,\s*(\d+)x(\d+)', result.stderr)
    width, height = (1080, 1920)
    if dim_match:
        width = int(dim_match.group(1))
        height = int(dim_match.group(2))
        
    # Extract duration
    dur_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', result.stderr)
    duration = 0.0
    if dur_match:
        hours = int(dur_match.group(1))
        mins = int(dur_match.group(2))
        secs = float(dur_match.group(3))
        duration = hours * 3600 + mins * 60 + secs

    return {
        "width": width,
        "height": height,
        "duration": duration,
        "stderr": result.stderr
    }

def add_top_image_to_video(
    video_path: str,
    image_path: str,
    output_path: str,
    mode: str = "overlay", # 'overlay' or 'header'
    fit_mode: str = "fit_width", # 'fit_width' (zero top gap) or 'custom_ratio'
    top_height_ratio: float = 0.20,
    opacity: float = 1.0,
    background_color: str = "black"
) -> Dict[str, Any]:
    """
    Overlays or stacks an image onto the top part of the video with ZERO top space/padding.
    
    Modes:
    - 'overlay': Image overlays directly on top edge (y=0) of the video.
    - 'header': Canvas expands upwards, placing the image exactly at top (y=0) above video.
    """
    ffmpeg_exe = get_ffmpeg_path()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    info = get_video_info(video_path)
    vw, vh = info["width"], info["height"]
    
    # Read original image dimensions
    with Image.open(image_path) as img:
        img_w, img_h = img.size

    # Calculate target dimensions
    target_width = vw
    target_width = target_width if target_width % 2 == 0 else target_width - 1

    if fit_mode == "fit_width":
        # Proportional height based on video width - zero distortion, zero top space
        target_height = int(img_h * (target_width / img_w))
    else:
        # Custom height ratio
        target_height = int(vh * top_height_ratio)

    target_height = target_height if target_height % 2 == 0 else target_height + 1

    if mode == "header":
        # Header style: Canvas expanded at top by target_height
        total_height = vh + target_height
        total_height = total_height if total_height % 2 == 0 else total_height + 1
        
        # Notice: y=0 alignment (top aligned, NO (oh-ih)/2 padding)
        filter_complex = (
            f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:0:{background_color},"
            f"format=rgba,colorchannelmixer=aa={opacity}[top_img];"
            f"[0:v]pad={vw}:{total_height}:0:{target_height}:{background_color}[base];"
            f"[base][top_img]overlay=0:0:shortest=1[outv]"
        )
    else:
        # Overlay directly on top of video at y=0 (NO space from top)
        if fit_mode == "fit_width":
            filter_complex = (
                f"[1:v]scale={target_width}:{target_height},"
                f"format=rgba,colorchannelmixer=aa={opacity}[top_img];"
                f"[0:v][top_img]overlay=0:0:shortest=1[outv]"
            )
        else:
            # Custom height ratio but strictly top-aligned at y=0
            filter_complex = (
                f"[1:v]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
                f"pad={target_width}:{target_height}:(ow-iw)/2:0:color=0x00000000,"
                f"format=rgba,colorchannelmixer=aa={opacity}[top_img];"
                f"[0:v][top_img]overlay=0:0:shortest=1[outv]"
            )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-loop", "1",
        "-i", image_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        return {
            "success": False,
            "error": process.stderr,
            "command": " ".join(cmd)
        }

    return {
        "success": True,
        "output_path": output_path,
        "width": target_width,
        "height": vh if mode == "overlay" else (vh + target_height)
    }
