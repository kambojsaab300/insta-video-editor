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

def create_text_banner(
    text: str,
    output_path: str,
    width: int = 1080,
    height: int = 220,
    bg_color: str = "black",
    text_color: str = "white",
    font_size: int = 50
) -> str:
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    img = Image.new("RGBA", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    font = None
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "Arial.ttf"
    ]
    for fc in font_candidates:
        if os.path.exists(fc):
            try:
                font = ImageFont.truetype(fc, font_size)
                break
            except Exception:
                pass

    if not font:
        try:
            font = ImageFont.load_default(size=font_size)
        except Exception:
            font = ImageFont.load_default()

    lines = textwrap.wrap(text, width=32)
    line_height = int(font_size * 1.3)
    total_text_height = len(lines) * line_height
    start_y = max(10, (height - total_text_height) // 2)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = max(10, (width - line_w) // 2)
        y = start_y + (i * line_height)
        draw.text((x, y), line, fill=text_color, font=font)

    img.save(output_path, "PNG")
    return output_path

def process_youtube_to_4_5(
    video_path: str,
    output_path: str,
    target_width: int = 1080,
    target_height: int = 1350,
    text: str = "",
    text_bg: str = "black",
    text_color: str = "white",
    banner_height: int = 220
) -> Dict[str, Any]:
    """
    Crops any YouTube video to 4:5 aspect ratio with chosen resolution (e.g. 1080x1350, 720x900)
    and overlays optional top text banner.
    """
    ffmpeg_exe = get_ffmpeg_path()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Scale factor relative to 1080 width
    scale_factor = target_width / 1080.0
    effective_banner_height = max(60, int(banner_height * scale_factor))
    effective_font_size = max(18, int(50 * scale_factor))
    
    # 4:5 center-crop filter, scaled to target_width:target_height
    crop_base = rf"crop=w=min(iw\,ih*4/5):h=min(ih\,iw*5/4):x=(in_w-out_w)/2:y=(in_h-out_h)/2,scale={target_width}:{target_height}"

    if text and text.strip():
        banner_temp = output_path + "_banner.png"
        create_text_banner(
            text=text.strip(),
            output_path=banner_temp,
            width=target_width,
            height=effective_banner_height,
            bg_color=text_bg,
            text_color=text_color,
            font_size=effective_font_size
        )
        
        filter_complex = (
            f"[0:v]{crop_base}[vid];"
            f"[1:v]scale={target_width}:{effective_banner_height}[banner];"
            f"[vid][banner]overlay=0:0:shortest=1[outv]"
        )
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", video_path,
            "-loop", "1",
            "-i", banner_temp,
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
    else:
        banner_temp = None
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", video_path,
            "-vf", crop_base,
            "-map", "0:v",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if banner_temp and os.path.exists(banner_temp):
        try: os.remove(banner_temp)
        except Exception: pass

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
        "height": target_height
    }

