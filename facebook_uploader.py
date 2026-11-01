import os
import requests
import json
import io
from typing import Dict, Any, Union

CONFIG_FILE = "fb_config.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def upload_video_via_token(
    video_source: Union[str, bytes],
    title: str = "",
    description: str = "",
    published: bool = True
) -> Dict[str, Any]:
    """
    Directly uploads video to Facebook via Meta Graph Video API using User/Page Token.
    Accepts video as either a disk filepath (str) OR in-memory bytes (bytes).
    Zero browser interaction. 100% Pure Token Mode.
    """
    config = get_config()
    user_token = config.get("user_access_token", "")
    target_page_id = config.get("default_page_id", "426394954503651")

    if not user_token:
        return {"success": False, "error": "Facebook Access Token not configured"}

    # Fetch page token for target
    try:
        pages_res = requests.get(
            f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}",
            timeout=15
        ).json()
        
        target_token = user_token
        target_name = "Raman Kamboj"

        if "data" in pages_res and pages_res["data"]:
            matching_page = next((p for p in pages_res["data"] if p["id"] == target_page_id), None)
            if not matching_page:
                matching_page = next((p for p in pages_res["data"] if "Raman" in p.get("name", "")), pages_res["data"][0])
            
            if matching_page:
                target_page_id = matching_page["id"]
                target_token = matching_page["access_token"]
                target_name = matching_page["name"]

        url = f"https://graph-video.facebook.com/v19.0/{target_page_id}/videos"
        payload = {
            "access_token": target_token,
            "title": title or "New Video",
            "description": description or title or "",
            "published": "true" if published else "false"
        }

        # Check if source is bytes or file path
        if isinstance(video_source, bytes):
            files = {"source": ("video.mp4", io.BytesIO(video_source), "video/mp4")}
            response = requests.post(url, data=payload, files=files, timeout=300)
        else:
            if not os.path.exists(video_source):
                return {"success": False, "error": "Video file not found"}
            with open(video_source, "rb") as video_file:
                files = {"source": video_file}
                response = requests.post(url, data=payload, files=files, timeout=300)

        res_json = response.json()

        if response.status_code == 200 and "id" in res_json:
            fb_video_id = res_json["id"]
            return {
                "success": True,
                "video_id": fb_video_id,
                "target_name": target_name,
                "url": f"https://www.facebook.com/{fb_video_id}"
            }
        else:
            err_msg = res_json.get("error", {}).get("message", "Facebook API upload error")
            return {
                "success": False,
                "error": err_msg,
                "details": res_json
            }

    except Exception as e:
        return {"success": False, "error": str(e)}
