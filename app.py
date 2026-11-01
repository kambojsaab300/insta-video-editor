import streamlit as st
import streamlit.components.v1 as components
import os
import time
import zipfile
import io
import shutil
import glob
from PIL import Image
from downloader import download_instagram_video
from processor import add_top_image_to_video, get_video_info

st.set_page_config(
    page_title="InstaForge Studio",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Responsive & Clean CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; }

    /* Compact Hero Header */
    .hero-box {
        text-align: center;
        padding: 1.2rem 0.5rem 0.8rem 0.5rem;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(45deg, #f09433, #dc2743, #bc1888);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        color: #888;
        font-size: 0.95rem;
    }

    /* Clean Card Container */
    .clean-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }

    /* Mobile Responsive Buttons & Layout */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-size: 1.05rem;
        font-weight: 700;
        background: linear-gradient(45deg, #f09433, #dc2743, #bc1888) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(220, 39, 67, 0.3);
    }
    .stButton>button:hover {
        opacity: 0.95;
    }

    /* Clear Button styling */
    .clear-btn button {
        height: 2rem !important;
        font-size: 0.82rem !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #bbb !important;
        box-shadow: none !important;
        border-radius: 8px !important;
    }
    .clear-btn button:hover {
        background: rgba(244, 67, 54, 0.15) !important;
        border-color: #f44336 !important;
        color: #ff8a80 !important;
    }

    /* Video Result Card */
    .result-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 1.2rem;
    }

    /* Mobile Specific Media Query */
    @media (max-width: 768px) {
        .hero-title { font-size: 1.6rem !important; }
        .hero-sub { font-size: 0.85rem !important; }
        .clean-card { padding: 0.9rem !important; }
        .stButton>button { height: 2.7rem !important; font-size: 0.95rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# Directories
TEMP_DIR = "temp_work"
SAVED_DIR = "saved_banners"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(SAVED_DIR, exist_ok=True)

# Browser Refresh Warning Helpers
def inject_beforeunload_warning():
    components.html("""
    <script>
    (function() {
        try {
            var p = window.parent || window.top || window;
            function warn(e) {
                var msg = "⚠️ Video processing is in progress! Please do not reload.";
                e.preventDefault(); e.returnValue = msg; return msg;
            }
            p.onbeforeunload = warn;
            p.addEventListener('beforeunload', warn, { capture: true });
        } catch(e) {}
    })();
    </script>
    """, height=0, width=0)

def remove_beforeunload_warning():
    components.html("""
    <script>
    (function() {
        try {
            var p = window.parent || window.top || window;
            p.onbeforeunload = null;
        } catch(e) {}
    })();
    </script>
    """, height=0, width=0)

# Minimal Header
st.markdown("""
<div class="hero-box">
    <div class="hero-title">⚡ InstaForge Studio</div>
    <div class="hero-sub">Instagram Reel Downloader & Top Banner Editor</div>
</div>
""", unsafe_allow_html=True)

# Initialize Session State for Links Input
if "links_text" not in st.session_state:
    st.session_state["links_text"] = ""

# 1. Links Input with 1-Click Clear Button
st.markdown('<div class="clean-card">', unsafe_allow_html=True)
header_col1, header_col2 = st.columns([2.5, 1])
with header_col1:
    st.markdown("**🔗 Instagram Links**")
with header_col2:
    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("🗑️ Clear Links", key="clear_btn"):
        st.session_state["links_text"] = ""
        st.session_state["links_area_val"] = ""
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

links_raw = st.text_area(
    "Instagram Links (Single or Multiple):",
    value=st.session_state.get("links_text", ""),
    placeholder="https://www.instagram.com/reel/Cxxxxxx/\nhttps://www.instagram.com/reel/Cyyyyyy/",
    height=95,
    key="links_area_val",
    label_visibility="collapsed",
    help="Paste one or multiple Instagram links, one link per line."
)
st.session_state["links_text"] = links_raw

links = [l.strip() for l in links_raw.splitlines() if l.strip() and "instagram.com" in l]
if links:
    st.caption(f"✨ **{len(links)} Valid Link(s) Detected**")
st.markdown('</div>', unsafe_allow_html=True)

# 2. Image Selection (Saved Banners or New Upload)
st.markdown('<div class="clean-card">', unsafe_allow_html=True)
st.markdown("**🖼️ Top Banner Image**")

saved_images = [os.path.basename(f) for f in sorted(glob.glob(os.path.join(SAVED_DIR, "*"))) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

img_source = st.radio(
    "Image Source:",
    options=["Saved Banners", "Upload New Image"],
    horizontal=True,
    label_visibility="collapsed"
)

selected_image_path = None

if img_source == "Saved Banners":
    if saved_images:
        chosen_img_name = st.selectbox("Choose a saved banner:", saved_images)
        selected_image_path = os.path.join(SAVED_DIR, chosen_img_name)
        st.image(selected_image_path, width=280)
    else:
        st.info("No saved banners found yet. Please upload a new image.")
else:
    new_img = st.file_uploader("Upload New Image:", type=["png", "jpg", "jpeg", "webp"])
    if new_img:
        clean_name = f"{int(time.time())}_{new_img.name}"
        save_path = os.path.join(SAVED_DIR, clean_name)
        with open(save_path, "wb") as f:
            f.write(new_img.getbuffer())
        selected_image_path = save_path
        st.image(selected_image_path, width=280)
st.markdown('</div>', unsafe_allow_html=True)

# 3. Extra Settings (Collapsed by Default)
with st.expander("⚙️ Advanced Layout Settings (Optional)", expanded=False):
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        mode = st.radio("Style:", ["overlay", "header"], format_func=lambda x: "🎯 Overlay on Video" if x == "overlay" else "🔝 Header (Above Video)")
        fit_mode = st.radio("Sizing:", ["fit_width", "custom_ratio"], format_func=lambda x: "Full Width (Zero Gap)" if x == "fit_width" else "Custom Height Slider")
    with col_s2:
        if fit_mode == "custom_ratio":
            height_ratio = st.slider("Banner Height %:", 10, 45, 22, 2, format="%d%%") / 100.0
        else:
            height_ratio = 0.20
        bg_color = st.selectbox("Header Color:", ["black", "white", "#1e1e1e"]) if mode == "header" else "black"
        opacity = st.slider("Opacity:", 0.2, 1.0, 1.0, 0.05)

# Session state initialization
if "results" not in st.session_state:
    st.session_state.results = []

# Action Button
start_btn = st.button("🚀 Process & Generate Videos", type="primary")

# Execution Logic
if start_btn:
    if not links:
        st.error("⚠️ Please enter at least 1 valid Instagram link!")
    elif not selected_image_path or not os.path.exists(selected_image_path):
        st.error("⚠️ Please select or upload a banner image!")
    else:
        total = len(links)
        st.session_state.results = []
        
        inject_beforeunload_warning()
        alert_placeholder = st.empty()
        alert_placeholder.warning("⚠️ Processing in progress. Please do not reload or leave this page!")

        st.markdown("---")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Real-time Video Results Placeholder
        live_container = st.container()

        try:
            for idx, link in enumerate(links, start=1):
                status_text.markdown(f"**[{idx}/{total}]** Processing: `{link[:40]}...`")
                item = {
                    "index": idx,
                    "url": link,
                    "title": f"Video #{idx}",
                    "success": False,
                    "bytes": None,
                    "error": ""
                }

                temp_dl_dir = os.path.join(TEMP_DIR, f"dl_{int(time.time())}_{idx}")
                temp_out = os.path.join(TEMP_DIR, f"out_{int(time.time())}_{idx}.mp4")

                try:
                    # 1. Download
                    dl_res = download_instagram_video(link, output_dir=temp_dl_dir)
                    if not dl_res.get("success"):
                        item["error"] = "Download failed (Post might be private)"
                    else:
                        vid_path = dl_res["filepath"]
                        item["title"] = dl_res.get("title", f"Video #{idx}")

                        # 2. Process
                        proc_res = add_top_image_to_video(
                            video_path=vid_path,
                            image_path=selected_image_path,
                            output_path=temp_out,
                            mode=mode,
                            fit_mode=fit_mode,
                            top_height_ratio=height_ratio,
                            opacity=opacity,
                            background_color=bg_color
                        )

                        if proc_res.get("success") and os.path.exists(temp_out):
                            # Read video into memory bytes
                            with open(temp_out, "rb") as vf:
                                item["bytes"] = vf.read()
                            item["success"] = True
                        else:
                            item["error"] = proc_res.get("error", "Encoding error")

                except Exception as e:
                    item["error"] = str(e)
                finally:
                    # Auto-delete temp disk files immediately - zero storage accumulation!
                    if os.path.exists(temp_out):
                        try: os.remove(temp_out)
                        except Exception: pass
                    if os.path.exists(temp_dl_dir):
                        try: shutil.rmtree(temp_dl_dir)
                        except Exception: pass

                st.session_state.results.append(item)
                progress_bar.progress(int((idx / total) * 100))

                # Render immediately in real-time
                with live_container:
                    if item["success"]:
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        st.markdown(f"**✅ Video #{idx} Ready:** {item['title'][:40]}")
                        st.video(item["bytes"])

                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.download_button(
                                label=f"⬇️ Download #{idx}",
                                data=item["bytes"],
                                file_name=f"edited_video_{idx}.mp4",
                                mime="video/mp4",
                                key=f"dl_live_{idx}"
                            )
                        with col_b2:
                            st.link_button(
                                label="🚀 Post to FB Reels",
                                url="https://www.facebook.com/reels/create/",
                                type="primary"
                            )
                        st.markdown('</div>', unsafe_allow_html=True)

            status_text.success("🎉 All videos generated successfully!")
            progress_bar.empty()
        finally:
            remove_beforeunload_warning()
            alert_placeholder.empty()

# Render Persisted Results if page reloads / button clicked
elif st.session_state.results:
    st.markdown("---")
    st.subheader("🎬 Generated Videos")

    # Zip Download if multiple
    successful = [r for r in st.session_state.results if r["success"]]
    if len(successful) > 1:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in successful:
                zf.writestr(f"video_{item['index']}.mp4", item["bytes"])
        zip_buf.seek(0)
        st.download_button(
            label=f"📦 Download All as ZIP ({len(successful)} Videos)",
            data=zip_buf.getvalue(),
            file_name=f"videos_batch_{int(time.time())}.zip",
            mime="application/zip",
            type="primary"
        )

    for item in st.session_state.results:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        if item["success"]:
            st.markdown(f"**✅ Video #{item['index']} Ready:** {item['title'][:40]}")
            st.video(item["bytes"])

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    label=f"⬇️ Download #{item['index']}",
                    data=item["bytes"],
                    file_name=f"edited_video_{item['index']}.mp4",
                    mime="video/mp4",
                    key=f"dl_pers_{item['index']}"
                )
            with c2:
                st.link_button(
                    label="🚀 Post to FB Reels",
                    url="https://www.facebook.com/reels/create/",
                    type="primary"
                )
        else:
            st.error(f"❌ #{item['index']} Failed: {item['error']}")
        st.markdown('</div>', unsafe_allow_html=True)
