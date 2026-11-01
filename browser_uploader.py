import os
import time
import subprocess
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.abspath("fb_browser_profile")
FB_REELS_URL = "https://www.facebook.com/reels/create/"

def upload_to_main_facebook_account(video_bytes_or_path, caption: str = ""):
    """
    Directly opens https://www.facebook.com/reels/create/ and reveals the video in Finder
    ready for 1-click upload to the user's main Facebook profile.
    """
    temp_dir = os.path.abspath("temp_work")
    os.makedirs(temp_dir, exist_ok=True)
    
    if isinstance(video_bytes_or_path, bytes):
        abs_video_path = os.path.join(temp_dir, f"reel_{int(time.time())}.mp4")
        with open(abs_video_path, "wb") as f:
            f.write(video_bytes_or_path)
    else:
        abs_video_path = os.path.abspath(video_bytes_or_path)

    if not os.path.exists(abs_video_path):
        return {"success": False, "error": "Video file ready nahi hai."}

    os.makedirs(USER_DATA_DIR, exist_ok=True)

    try:
        # 1. Reveal video in macOS Finder (highlights the exact file)
        subprocess.run(["open", "-R", abs_video_path])
        
        # 2. Open https://www.facebook.com/reels/create/ in default browser
        subprocess.run(["open", FB_REELS_URL])

        return {
            "success": True,
            "url": FB_REELS_URL,
            "message": "✅ Facebook Reels Creator open ho gaya hai aur video Finder me select hai! Bas drag & drop karke share karein."
        }
    except Exception as e:
        subprocess.run(["open", FB_REELS_URL])
        return {
            "success": True,
            "url": FB_REELS_URL,
            "message": f"Facebook Reels Creator open ho gaya hai: {FB_REELS_URL}"
        }
