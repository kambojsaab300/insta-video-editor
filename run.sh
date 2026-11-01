#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

mkdir -p ~/.streamlit
cat <<EOF > ~/.streamlit/credentials.toml
[general]
email = ""
EOF

# Ensure ffmpeg binary is linked in venv/bin
./venv/bin/python3 -c "
import imageio_ffmpeg, os
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
venv_ffmpeg = os.path.abspath('venv/bin/ffmpeg')
if not os.path.exists(venv_ffmpeg):
    os.symlink(ffmpeg_path, venv_ffmpeg)
"

export PATH="$(pwd)/venv/bin:$PATH"

echo "🚀 Starting Instagram Video Editor Web UI..."
./venv/bin/streamlit run app.py --server.headless true --browser.gatherUsageStats false
