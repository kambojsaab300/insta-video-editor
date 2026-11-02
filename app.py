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

# Global Styling: dark glass UI with Instagram-gradient accents
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"], .stMarkdown, button, input, textarea, select {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }

    :root {
        --grad: linear-gradient(120deg, #feda75 0%, #fa7e1e 22%, #d62976 50%, #962fbf 75%, #4f5bd5 100%);
        --glass: rgba(255, 255, 255, 0.035);
        --glass-border: rgba(255, 255, 255, 0.09);
        --muted: #9a9ab0;
    }

    /* Background with soft colour glows */
    .stApp {
        background:
            radial-gradient(900px 500px at 10% -10%, rgba(214, 41, 118, 0.22), transparent 60%),
            radial-gradient(800px 500px at 100% 0%, rgba(79, 91, 213, 0.20), transparent 60%),
            radial-gradient(700px 600px at 50% 110%, rgba(250, 126, 30, 0.10), transparent 60%),
            #0b0b14;
        background-attachment: fixed;
    }
    header[data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; }
    .block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 780px; }

    /* Hero */
    .hero-box { text-align: center; padding: 0.6rem 0.5rem 1.4rem; }
    .hero-logo {
        width: 64px; height: 64px; margin: 0 auto 0.9rem;
        border-radius: 20px; background: var(--grad);
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem; box-shadow: 0 10px 40px rgba(214, 41, 118, 0.45);
        animation: float 4s ease-in-out infinite;
    }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
    .hero-title {
        font-size: 2.6rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1;
        background: var(--grad); background-size: 200% auto;
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 6s linear infinite;
    }
    @keyframes shine { to { background-position: 200% center; } }
    .hero-sub { color: var(--muted); font-size: 1rem; margin-top: 0.5rem; }

    /* Section headings inside cards */
    .sec-head { display: flex; align-items: center; gap: 10px; margin-bottom: 0.15rem; }
    .sec-num {
        width: 26px; height: 26px; border-radius: 8px; flex-shrink: 0;
        background: var(--grad); color: #fff; font-weight: 800; font-size: 0.8rem;
        display: flex; align-items: center; justify-content: center;
    }
    .sec-title { font-weight: 700; font-size: 1.02rem; color: #f2f2f8; }
    .sec-desc { color: var(--muted); font-size: 0.82rem; margin: 0 0 0.4rem 36px; }

    /* Glass cards (st.container(border=True, key="card_*")) */
    [class*="st-key-card"] {
        background: var(--glass) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 18px !important;
        padding: 1.2rem 1.25rem !important;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    [class*="st-key-card"]:hover {
        border-color: rgba(214, 41, 118, 0.35) !important;
        box-shadow: 0 10px 40px rgba(214, 41, 118, 0.12);
    }
    [class*="st-key-result"] {
        background: rgba(255, 255, 255, 0.045) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 18px !important;
        padding: 1rem !important;
    }

    /* Tabs as a segmented pill control */
    .stTabs [role="tablist"] {
        gap: 6px; padding: 6px; border-radius: 16px;
        background: var(--glass); border: 1px solid var(--glass-border);
        margin-bottom: 1.2rem;
    }
    .stTabs [role="tab"] {
        flex: 1; justify-content: center; height: 46px;
        border-radius: 12px; padding: 8px 14px;
        font-weight: 700; color: var(--muted);
        transition: all 0.2s ease;
    }
    .stTabs [role="tab"]:hover { color: #fff; background: rgba(255, 255, 255, 0.05); }
    .stTabs [aria-selected="true"] {
        background: var(--grad) !important; color: #fff !important;
        box-shadow: 0 6px 20px rgba(214, 41, 118, 0.35);
    }
    .stTabs [aria-selected="true"] p { color: #fff !important; }
    .stTabs [role="tab"] { display: flex; align-items: center; cursor: pointer; border: none; }
    .stTabs [role="tablist"] { overflow: hidden !important; border-bottom: 1px solid var(--glass-border) !important; }
    .stTabs [role="tablist"]::after, .stTabs [role="tablist"]::before { display: none !important; }
    .stTabs [role="tab"] { min-width: 0; white-space: nowrap; }
    .stTabs .react-aria-SelectionIndicator { display: none !important; }

    /* Inputs */
    .stTextArea textarea, .stTextInput input,
    .stSelectbox [data-baseweb="select"] > div {
        background: rgba(0, 0, 0, 0.28) !important;
        border-radius: 12px !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #d62976 !important;
        box-shadow: 0 0 0 3px rgba(214, 41, 118, 0.2) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(0, 0, 0, 0.22); border: 1.5px dashed rgba(255, 255, 255, 0.18);
        border-radius: 14px;
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: #d62976; }

    /* Buttons */
    .stButton > button, .stDownloadButton > button, .stLinkButton > a {
        width: 100%; border-radius: 12px; font-weight: 700;
        transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }
    [data-testid="stBaseButton-primary"], [data-testid="stBaseLinkButton-primary"] {
        background: var(--grad) !important; background-size: 150% auto !important;
        border: none !important; color: #fff !important;
        box-shadow: 0 6px 22px rgba(214, 41, 118, 0.35);
    }
    .stButton [data-testid="stBaseButton-primary"] { min-height: 3.3rem; font-size: 1.05rem; margin-top: 0.4rem; }
    [data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseLinkButton-primary"]:hover {
        transform: translateY(-2px); filter: brightness(1.08);
        box-shadow: 0 10px 30px rgba(214, 41, 118, 0.5);
    }
    [data-testid="stBaseButton-secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #e4e4ee !important;
    }
    [data-testid="stBaseButton-secondary"]:hover {
        border-color: #d62976 !important; color: #fff !important;
        background: rgba(214, 41, 118, 0.12) !important;
    }
    [class*="st-key-linkbtns"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.6rem; }
    [class*="st-key-linkbtns"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
    [class*="st-key-clear"] button {
        width: 100% !important; height: 36px; min-height: 36px !important; padding: 0 10px !important;
        font-size: 0.8rem !important; font-weight: 600 !important; color: var(--muted) !important;
    }
    [class*="st-key-clear"] button:hover {
        background: rgba(244, 67, 54, 0.14) !important;
        border-color: #f44336 !important; color: #ff8a80 !important;
    }

    /* Expander */
    [data-testid="stExpander"] details {
        background: var(--glass); border: 1px solid var(--glass-border) !important;
        border-radius: 16px;
    }
    [data-testid="stExpander"] summary { font-weight: 600; }

    /* Progress bar */
    .stProgress > div > div > div > div { background: var(--grad) !important; }

    /* Radio pills */
    .stRadio [role="radiogroup"] { gap: 8px; }
    .stRadio [role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 6px 12px; border-radius: 10px; margin-right: 0;
    }
    .stRadio [role="radiogroup"] > label:has(input:checked) {
        border-color: #d62976; background: rgba(214, 41, 118, 0.12);
    }

    /* Media & alerts */
    [data-testid="stImage"] img, video { border-radius: 14px; }
    [data-testid="stAlert"] { border-radius: 14px; }
    hr { border-color: rgba(255, 255, 255, 0.08) !important; }

    .app-footer { text-align: center; color: #5d5d72; font-size: 0.78rem; margin-top: 3rem; }

    @media (max-width: 768px) {
        .block-container { padding-top: 1.2rem; }
        .hero-title { font-size: 1.85rem !important; }
        .hero-sub { font-size: 0.88rem !important; }
        .hero-logo { width: 54px; height: 54px; font-size: 1.6rem; }
        [class*="st-key-card"] { padding: 0.95rem !important; }
        .stTabs [role="tab"] { height: 42px; padding: 6px 8px; font-size: 0.85rem; }
        .stButton [data-testid="stBaseButton-primary"] { min-height: 2.9rem; font-size: 0.95rem; }
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

_paste_component = components.declare_component(
    "paste_button", path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "components", "paste_button")
)

def paste_link_button(key, text_key, area_key):
    """Reads the browser clipboard and appends it to the links text area."""
    val = _paste_component(key=key, default=None)
    if val and val.get("nonce") != st.session_state.get(f"{key}_nonce"):
        st.session_state[f"{key}_nonce"] = val.get("nonce")
        current = st.session_state.get(text_key, "").rstrip()
        pasted = val.get("text", "").strip()
        new_text = f"{current}\n{pasted}" if current else pasted
        st.session_state[text_key] = new_text
        st.session_state[area_key] = new_text

def section_header(num, title, desc=""):
    st.markdown(
        f'<div class="sec-head"><div class="sec-num">{num}</div><div class="sec-title">{title}</div></div>'
        + (f'<div class="sec-desc">{desc}</div>' if desc else ""),
        unsafe_allow_html=True
    )

# Hero Header
st.markdown("""
<div class="hero-box">
    <div class="hero-logo">⚡</div>
    <div class="hero-title">InstaForge Studio</div>
    <div class="hero-sub">Download, crop & brand your Reels and Shorts in one click</div>
</div>
""", unsafe_allow_html=True)

# TABS: Tab 1 = Instagram Studio (Existing 100%), Tab 2 = YouTube 4:5 Crop & Text Studio (New)
tab_insta, tab_yt = st.tabs(["📸 Instagram Studio", "▶️ YouTube Studio"])

# =========================================================================
# TAB 1: INSTAGRAM STUDIO (Existing functionality 100% intact)
# =========================================================================
with tab_insta:
    # Initialize Session State for Links Input
    if "links_text" not in st.session_state:
        st.session_state["links_text"] = ""

    # 1. Links Input with Paste & Clear Buttons
    with st.container(border=True, key="card_insta_links"):
        section_header(1, "🔗 Instagram Links", "Paste one or more Reel / post links, one per line")
        paste_col, clear_col = st.container(key="linkbtns_insta").columns(2)
        with paste_col:
            paste_link_button("paste_insta", "links_text", "links_area_val")
        with clear_col:
            if st.button("🗑️ Clear Links", key="clear_insta_btn"):
                st.session_state["links_text"] = ""
                st.session_state["links_area_val"] = ""
                st.rerun()

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

    # 2. Image Selection (Saved Banners or New Upload)
    with st.container(border=True, key="card_insta_banner"):
        section_header(2, "🖼️ Top Banner Image", "Pick a saved banner or upload a new one")

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
                            with st.container(border=True, key=f"result_insta_live_{idx}"):
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
            with st.container(border=True, key=f"result_insta_pers_{item['index']}"):
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

# =========================================================================
# TAB 2: YOUTUBE STUDIO (Quality / Size Selection, 4:5 Crop & Direct Download)
# =========================================================================
with tab_yt:
    if "yt_links_text" not in st.session_state:
        st.session_state["yt_links_text"] = ""

    # 1. YouTube Links Input
    with st.container(border=True, key="card_yt_links"):
        section_header(1, "▶️ YouTube Links", "Videos or Shorts, one link per line")
        yt_paste_col, yt_clear_col = st.container(key="linkbtns_yt").columns(2)
        with yt_paste_col:
            paste_link_button("paste_yt", "yt_links_text", "yt_area_val")
        with yt_clear_col:
            if st.button("🗑️ Clear Links", key="clear_yt_btn"):
                st.session_state["yt_links_text"] = ""
                st.session_state["yt_area_val"] = ""
                st.rerun()

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

    # 2. Quality / Video Size & Mode Selector (Before Generating)
    with st.container(border=True, key="card_yt_quality"):
        section_header(2, "⚙️ Size & Quality", "Choose resolution and how the video is processed")
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


    # 3. Top Text Banner Input (Only if 4:5 Crop mode is selected)
    yt_custom_text = ""
    yt_text_color = "yellow"
    yt_bg_color = "black"
    yt_banner_height = 220

    if yt_mode == "📐 Crop to 4:5 (With Top Text Banner)":
        with st.container(border=True, key="card_yt_text"):
            section_header(3, "✍️ Headline Banner", "Optional bold text shown above the cropped video")
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

    # Session state for YouTube results
    if "yt_results" not in st.session_state:
        st.session_state.yt_results = []

    # Helper function to render a card
    def render_youtube_card(item, key_prefix="live"):
        with st.container(border=True, key=f"result_yt_{key_prefix}_{item['index']}"):
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

st.markdown('<div class="app-footer">Made with ⚡ InstaForge Studio</div>', unsafe_allow_html=True)
