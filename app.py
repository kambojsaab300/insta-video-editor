import streamlit as st
import streamlit.components.v1 as components
import os
import time
import zipfile
import io
import shutil
import glob
from PIL import Image
from downloader import download_instagram_video, download_youtube_video
from processor import add_top_image_to_video, get_video_info, process_youtube_to_4_5

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
        padding: 1.2rem 0.5rem 0.6rem 0.5rem;
        margin-bottom: 0.8rem;
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

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
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
    <div class="hero-sub">Video Downloader, Aspect Ratio Cropper & Banner Studio</div>
</div>
""", unsafe_allow_html=True)

# TABS: Tab 1 = Instagram Studio (Existing 100%), Tab 2 = YouTube 4:5 Crop & Text Studio (New)
tab_insta, tab_yt = st.tabs(["📸 Instagram Studio", "▶️ YouTube Studio (4:5 Crop & Text)"])

# =========================================================================
# TAB 1: INSTAGRAM STUDIO (Existing functionality 100% intact)
# =========================================================================
with tab_insta:
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
        if st.button("🗑️ Clear Links", key="clear_insta_btn"):
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
        label_visibility="collapsed",
        key="insta_img_source"
    )

    selected_image_path = None

    if img_source == "Saved Banners":
        if saved_images:
            chosen_img_name = st.selectbox("Choose a saved banner:", saved_images, key="insta_saved_picker")
            selected_image_path = os.path.join(SAVED_DIR, chosen_img_name)
            st.image(selected_image_path, width=280)
        else:
            st.info("No saved banners found yet. Please upload a new image.")
    else:
        new_img = st.file_uploader("Upload New Image:", type=["png", "jpg", "jpeg", "webp"], key="insta_new_uploader")
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
            mode = st.radio("Style:", ["overlay", "header"], format_func=lambda x: "🎯 Overlay on Video" if x == "overlay" else "🔝 Header (Above Video)", key="insta_mode")
            fit_mode = st.radio("Sizing:", ["fit_width", "custom_ratio"], format_func=lambda x: "Full Width (Zero Gap)" if x == "fit_width" else "Custom Height Slider", key="insta_fit_mode")
        with col_s2:
            if fit_mode == "custom_ratio":
                height_ratio = st.slider("Banner Height %:", 10, 45, 22, 2, format="%d%%", key="insta_height_ratio") / 100.0
            else:
                height_ratio = 0.20
            bg_color = st.selectbox("Header Color:", ["black", "white", "#1e1e1e"], key="insta_bg_col") if mode == "header" else "black"
            opacity = st.slider("Opacity:", 0.2, 1.0, 1.0, 0.05, key="insta_opacity")

    # Session state initialization for Instagram results
    if "results" not in st.session_state:
        st.session_state.results = []

    # Action Button
    start_btn = st.button("🚀 Process & Generate Instagram Videos", type="primary", key="insta_start_btn")

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
                                with open(temp_out, "rb") as vf:
                                    item["bytes"] = vf.read()
                                item["success"] = True
                            else:
                                item["error"] = proc_res.get("error", "Encoding error")

                    except Exception as e:
                        item["error"] = str(e)
                    finally:
                        if os.path.exists(temp_out):
                            try: os.remove(temp_out)
                            except Exception: pass
                        if os.path.exists(temp_dl_dir):
                            try: shutil.rmtree(temp_dl_dir)
                            except Exception: pass

                    st.session_state.results.append(item)
                    progress_bar.progress(int((idx / total) * 100))

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
                                    type="primary",
                                    key=f"fb_link_live_{idx}"
                                )
                            st.markdown('</div>', unsafe_allow_html=True)

                status_text.success("🎉 All videos generated successfully!")
                progress_bar.empty()
            finally:
                remove_beforeunload_warning()
                alert_placeholder.empty()

    # Render Persisted Instagram Results
    elif st.session_state.results:
        st.markdown("---")
        st.subheader("🎬 Generated Videos")

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
                type="primary",
                key="insta_zip_btn"
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
                        type="primary",
                        key=f"fb_link_pers_{item['index']}"
                    )
            else:
                st.error(f"❌ #{item['index']} Failed: {item['error']}")
            st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# TAB 2: YOUTUBE STUDIO (Quality / Size Selection, 4:5 Crop & Direct Download)
# =========================================================================
with tab_yt:
    if "yt_links_text" not in st.session_state:
        st.session_state["yt_links_text"] = ""

    # 1. YouTube Links Input
    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    yt_hcol1, yt_hcol2 = st.columns([2.5, 1])
    with yt_hcol1:
        st.markdown("**▶️ YouTube Video / Shorts Links**")
    with yt_hcol2:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Clear Links", key="clear_yt_btn"):
            st.session_state["yt_links_text"] = ""
            st.session_state["yt_area_val"] = ""
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    yt_links_raw = st.text_area(
        "YouTube Links:",
        value=st.session_state.get("yt_links_text", ""),
        placeholder="https://www.youtube.com/watch?v=xxxxxx\nhttps://youtube.com/shorts/yyyyyy",
        height=95,
        key="yt_area_val",
        label_visibility="collapsed",
        help="Paste YouTube Video or Shorts links, one per line."
    )
    st.session_state["yt_links_text"] = yt_links_raw

    yt_links = [l.strip() for l in yt_links_raw.splitlines() if l.strip() and ("youtube.com" in l or "youtu.be" in l)]
    if yt_links:
        st.caption(f"✨ **{len(yt_links)} Valid YouTube Link(s) Detected**")
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Quality / Video Size & Mode Selector (Before Generating)
    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.markdown("**⚙️ Video Size & Quality Settings**")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        yt_quality_choice = st.selectbox(
            "Select Video Resolution / Size:",
            options=[
                "1080p (Full HD - High Quality, 1080x1350)",
                "720p (HD - Balanced, 720x900)",
                "480p (SD - Fast / Smaller Size, 480x600)",
                "360p (Low - Lightweight, 360x450)",
                "Best Available (Original Source Quality)"
            ],
            index=0,
            help="Choose the video resolution before download and processing."
        )
    with q_col2:
        yt_mode = st.radio(
            "Processing Mode:",
            options=[
                "📐 Crop to 4:5 (With Top Text Banner)",
                "📥 Direct Download (Original Video, No Crop)"
            ],
            index=0,
            help="Choose between 4:5 aspect ratio cropping or direct original video download."
        )

    # Parse Quality
    if "1080p" in yt_quality_choice:
        yt_quality = "1080p"
        target_w, target_h = 1080, 1350
    elif "720p" in yt_quality_choice:
        yt_quality = "720p"
        target_w, target_h = 720, 900
    elif "480p" in yt_quality_choice:
        yt_quality = "480p"
        target_w, target_h = 480, 600
    elif "360p" in yt_quality_choice:
        yt_quality = "360p"
        target_w, target_h = 360, 450
    else:
        yt_quality = "best"
        target_w, target_h = 1080, 1350

    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Top Text Banner Input (Only if 4:5 Crop mode is selected)
    yt_custom_text = ""
    yt_text_color = "yellow"
    yt_bg_color = "black"
    yt_banner_height = 220

    if yt_mode == "📐 Crop to 4:5 (With Top Text Banner)":
        st.markdown('<div class="clean-card">', unsafe_allow_html=True)
        st.markdown("**✍️ Top Headline / Text Banner (Optional)**")
        yt_custom_text = st.text_input(
            "Top Text to Overlay:",
            placeholder="e.g. WAIT FOR THE END! 😂 | INSANE MOMENT 🔥",
            help="This text will be rendered as a bold top header on the 4:5 cropped video."
        )

        with st.expander("🎨 Text Banner Styling (Colors & Height)", expanded=False):
            yt_scol1, yt_scol2 = st.columns(2)
            with yt_scol1:
                yt_text_color = st.selectbox("Text Color:", ["yellow", "white", "#00ffff", "#ff3b30"], index=0)
                yt_bg_color = st.selectbox("Banner Background:", ["black", "#121212", "white", "#b71c1c"], index=0)
            with yt_scol2:
                yt_banner_height = st.slider("Banner Height (px):", 140, 320, 220, 20)
                st.caption(f"Output size: {target_w}x{target_h} (4:5 Aspect Ratio)")
        st.markdown('</div>', unsafe_allow_html=True)

    # Session state for YouTube results
    if "yt_results" not in st.session_state:
        st.session_state.yt_results = []

    # Helper function to render a card
    def render_youtube_card(item, key_prefix="live"):
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        idx = item["index"]
        if item["success"]:
            st.markdown(f"**✅ Video #{idx} Ready ({item['quality']}):** {item['title'][:45]}")
            play_bytes = item.get("cropped_bytes") or item.get("orig_bytes")
            if play_bytes:
                st.video(play_bytes)

            if item.get("cropped_bytes") and item.get("orig_bytes"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label=f"⬇️ 4:5 Video ({item['quality']})",
                        data=item["cropped_bytes"],
                        file_name=f"yt_4_5_{idx}_{item['quality']}.mp4",
                        mime="video/mp4",
                        key=f"dl_crop_{key_prefix}_{idx}"
                    )
                with col2:
                    st.download_button(
                        label=f"📥 Original Video ({item['quality']})",
                        data=item["orig_bytes"],
                        file_name=f"yt_original_{idx}_{item['quality']}.mp4",
                        mime="video/mp4",
                        key=f"dl_orig_{key_prefix}_{idx}"
                    )
                with col3:
                    st.link_button(
                        label="🚀 Post to FB Reels",
                        url="https://www.facebook.com/reels/create/",
                        type="primary",
                        key=f"fb_yt_{key_prefix}_{idx}"
                    )
            else:
                dl_data = item.get("cropped_bytes") or item.get("orig_bytes")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label=f"⬇️ Download Video ({item['quality']})",
                        data=dl_data,
                        file_name=f"yt_video_{idx}_{item['quality']}.mp4",
                        mime="video/mp4",
                        key=f"dl_single_{key_prefix}_{idx}"
                    )
                with col2:
                    st.link_button(
                        label="🚀 Post to FB Reels",
                        url="https://www.facebook.com/reels/create/",
                        type="primary",
                        key=f"fb_yt_{key_prefix}_{idx}"
                    )
        else:
            st.error(f"❌ #{idx} Failed: {item['error']}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Action Button
    if "Direct Download" in yt_mode:
        btn_label = f"⬇️ Download YouTube Video(s) [{yt_quality}]"
    else:
        btn_label = f"🚀 Crop to 4:5 ({target_w}x{target_h}) & Generate [{yt_quality}]"

    yt_start_btn = st.button(btn_label, type="primary", key="yt_start_btn")

    if yt_start_btn:
        if not yt_links:
            st.error("⚠️ Please enter at least 1 valid YouTube link!")
        else:
            yt_total = len(yt_links)
            st.session_state.yt_results = []

            inject_beforeunload_warning()
            yt_alert = st.empty()
            yt_alert.warning("⚠️ Processing in progress. Please do not reload or leave this page!")

            st.markdown("---")
            yt_progress = st.progress(0)
            yt_status = st.empty()

            yt_live_container = st.container()

            try:
                for idx, ylink in enumerate(yt_links, start=1):
                    mode_desc = "Downloading Original" if "Direct Download" in yt_mode else f"Cropping to 4:5 ({target_w}x{target_h})"
                    yt_status.markdown(f"**[{idx}/{yt_total}]** {mode_desc}: `{ylink[:40]}...`")
                    item = {
                        "index": idx,
                        "url": ylink,
                        "title": f"YouTube #{idx}",
                        "success": False,
                        "cropped_bytes": None,
                        "orig_bytes": None,
                        "mode": yt_mode,
                        "quality": yt_quality,
                        "error": ""
                    }

                    temp_dl_dir = os.path.join(TEMP_DIR, f"yt_dl_{int(time.time())}_{idx}")
                    temp_out = os.path.join(TEMP_DIR, f"yt_out_{int(time.time())}_{idx}.mp4")

                    try:
                        # 1. Download YouTube video with requested quality
                        dl_res = download_youtube_video(ylink, output_dir=temp_dl_dir, quality=yt_quality)
                        if not dl_res.get("success"):
                            item["error"] = dl_res.get("error", "YouTube download failed (Video might be private or restricted)")
                        else:
                            vid_path = dl_res["filepath"]
                            item["title"] = dl_res.get("title", f"YouTube #{idx}")

                            # Read original downloaded bytes
                            with open(vid_path, "rb") as ovf:
                                item["orig_bytes"] = ovf.read()

                            if "Direct Download" in yt_mode:
                                item["success"] = True
                            else:
                                # 2. Crop to 4:5 and overlay text banner
                                proc_res = process_youtube_to_4_5(
                                    video_path=vid_path,
                                    output_path=temp_out,
                                    target_width=target_w,
                                    target_height=target_h,
                                    text=yt_custom_text,
                                    text_bg=yt_bg_color,
                                    text_color=yt_text_color,
                                    banner_height=yt_banner_height
                                )

                                if proc_res.get("success") and os.path.exists(temp_out):
                                    with open(temp_out, "rb") as vf:
                                        item["cropped_bytes"] = vf.read()
                                    item["success"] = True
                                else:
                                    item["error"] = proc_res.get("error", "Cropping/encoding error")

                    except Exception as e:
                        item["error"] = str(e)
                    finally:
                        if os.path.exists(temp_out):
                            try: os.remove(temp_out)
                            except Exception: pass
                        if os.path.exists(temp_dl_dir):
                            try: shutil.rmtree(temp_dl_dir)
                            except Exception: pass

                    st.session_state.yt_results.append(item)
                    yt_progress.progress(int((idx / yt_total) * 100))

                    with yt_live_container:
                        render_youtube_card(item, key_prefix="live")

                yt_status.success("🎉 Processing completed successfully!")
                yt_progress.empty()
            finally:
                remove_beforeunload_warning()
                yt_alert.empty()

    # Render Persisted YouTube Results
    elif st.session_state.yt_results:
        st.markdown("---")
        st.subheader("🎬 Generated Videos")

        successful_yt = [r for r in st.session_state.yt_results if r["success"]]
        if len(successful_yt) > 1:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for item in successful_yt:
                    data = item.get("cropped_bytes") or item.get("orig_bytes")
                    if data:
                        zf.writestr(f"youtube_video_{item['index']}_{item['quality']}.mp4", data)
            zip_buf.seek(0)
            st.download_button(
                label=f"📦 Download All as ZIP ({len(successful_yt)} Videos)",
                data=zip_buf.getvalue(),
                file_name=f"youtube_batch_{int(time.time())}.zip",
                mime="application/zip",
                type="primary",
                key="yt_zip_btn"
            )

        for item in st.session_state.yt_results:
            render_youtube_card(item, key_prefix="persisted")
