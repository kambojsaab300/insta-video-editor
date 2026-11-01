# 🎬 Instagram Video Downloader & Top Banner Editor (Python)

Ye project Instagram se koi bhi video / reel download karke uske top (upper) part me custom image / banner attach karta hai aur edited video generate karta hai.

---

## 🌟 Features & Possibilities (Kahan tak ban sakta hai)

| Feature | Support | Details |
|---|---|---|
| **Instagram Reels / Posts** | ✅ Yes | Public links bina login ke download hote hain |
| **Private Posts** | ⚠️ Partially | Cookies / session export ke sath possible hai |
| **Top Image Placement** | ✅ Yes | **Overlay** (video ke upar) ya **Header** (video ke upar alag se space add karke) |
| **Auto Resizing** | ✅ Yes | Image automatically video width ke hisab se scale ho jati hai |
| **Audio Preservation** | ✅ Yes | Original audio quality bilkul safe rehti hai |
| **Web UI** | ✅ Yes | Clean Streamlit interface jisme live preview & 1-click download button hai |
| **CLI / Automation** | ✅ Yes | Terminal script ke zariye batch processing bhi kar sakte ho |

---

## 🚀 Quick Start (Kaise Chalayein)

### Option 1: Web Interface (Recommended)
Terminal me run karein:
```bash
cd insta-video-editor
./run.sh
```
Ya fir:
```bash
cd insta-video-editor
./venv/bin/streamlit run app.py
```
Browser me `http://localhost:8501` open ho jayega!

### Option 2: Command Line (CLI)
```bash
cd insta-video-editor
./venv/bin/python main.py --url "https://www.instagram.com/reel/XXXXX/" --image "/path/to/image.png" --mode overlay
```

Parameters:
- `--mode overlay` : Video ke content ke upar top par image lagayega.
- `--mode header`  : Video ke upar black/custom header space banakar image lagayega (taaki video cut na ho).
- `--height-ratio` : Image kitna percent height le (e.g. `0.20` = 20%).

---

## 📁 Project Structure

```text
insta-video-editor/
├── app.py             # Streamlit Interactive Web Application
├── downloader.py      # Instagram Reel / Video Downloader (yt-dlp)
├── processor.py       # High-speed Video + Image editing (FFmpeg)
├── main.py            # CLI script for terminal usage
├── requirements.txt   # Dependencies
├── run.sh             # 1-Click Run script
├── downloads/         # Raw downloaded videos
└── outputs/           # Final edited videos
```
