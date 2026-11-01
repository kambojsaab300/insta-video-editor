#!/usr/bin/env python3
import argparse
import sys
import os
import time
from downloader import download_instagram_video
from processor import add_top_image_to_video

def main():
    parser = argparse.ArgumentParser(description="Instagram Video Downloader & Top Image Editor (Batch Supported)")
    parser.add_argument("--url", "-u", nargs="+", help="One or more Instagram Reel / Post URLs")
    parser.add_argument("--file", "-F", help="Path to text file containing Instagram URLs (one per line)")
    parser.add_argument("--image", "-i", required=True, help="Path to image for top overlay/header")
    parser.add_argument("--mode", "-m", choices=["overlay", "header"], default="overlay", 
                        help="'overlay' to place directly on video, 'header' to stack above video")
    parser.add_argument("--fit-mode", "-f", choices=["fit_width", "custom_ratio"], default="fit_width",
                        help="'fit_width' for zero top gap / edge-to-edge, 'custom_ratio' for custom height")
    parser.add_argument("--height-ratio", "-hr", type=float, default=0.20, 
                        help="Height ratio of top image relative to video (default: 0.20 i.e. 20%)")
    parser.add_argument("--bg", default="black", help="Background color for header mode (default: black)")
    parser.add_argument("--out-dir", "-o", default="outputs", help="Output directory (default: outputs)")

    args = parser.parse_args()

    # Collect URLs
    urls = []
    if args.url:
        urls.extend(args.url)
    if args.file and os.path.exists(args.file):
        with open(args.file, "r") as f:
            for line in f:
                clean = line.strip()
                if clean and "instagram.com" in clean:
                    urls.append(clean)

    if not urls:
        print("❌ Error: Kam se kam ek Instagram URL provide karein (--url ya --file).")
        sys.exit(1)

    if not os.path.exists(args.image):
        print(f"❌ Error: Image file nahi mili: {args.image}")
        sys.exit(1)

    os.makedirs(args.out_dir, exist_ok=True)
    total = len(urls)
    print(f"\n🚀 Total {total} Instagram video(s) process hone ke liye ready hain.\n")

    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{total}] 📥 Downloading: {url}")
        try:
            download_res = download_instagram_video(url, output_dir="downloads")
            video_path = download_res["filepath"]
            video_id = download_res["id"]
            print(f"    ✅ Downloaded: {video_path}")

            print(f"    🎨 Applying top banner ({args.mode} mode, {args.fit_mode})...")
            out_filename = f"final_{video_id}_{int(time.time())}.mp4"
            out_path = os.path.join(args.out_dir, out_filename)

            process_res = add_top_image_to_video(
                video_path=video_path,
                image_path=args.image,
                output_path=out_path,
                mode=args.mode,
                fit_mode=args.fit_mode,
                top_height_ratio=args.height_ratio,
                background_color=args.bg
            )

            if process_res.get("success"):
                print(f"    🎉 Success: {out_path}\n")
            else:
                print(f"    ❌ Processing error: {process_res.get('error')}\n")

        except Exception as e:
            print(f"    ❌ Error: {e}\n")

    print(f"✨ All finished! Saved in '{args.out_dir}/' folder.")

if __name__ == "__main__":
    main()
