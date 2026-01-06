import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import base64
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FLASHPOINT | INTEL COMMAND",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ASSETS PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "assets", "logo.svg")

# --- INLINE SVG ICONS (The Upgrade) ---
# We define these paths here to keep the project clean without needing external files.
ICONS = {
    "signal": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>',
    "broadcast": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 18.08c-1.42-.87-2.67-2.07-3.64-3.5L3.63 12C4.38 13.06 5.34 13.93 6.45 14.5l-1.45 3.58zm12.55 0l-1.45-3.58c1.11-.57 2.06-1.44 2.82-2.5L22.64 14.58c-.97 1.43-2.22 2.63-3.64 3.5zM2 10.5C2 5.25 6.25 1 11.5 1S21 5.25 21 10.5c0 2.33-.82 4.47-2.19 6.13l-1.44-3.56c.49-.78.78-1.7.78-2.69 0-2.9-2.35-5.25-5.25-5.25S7.65 7.48 7.65 10.38c0 1 .29 1.91.78 2.69l-1.44 3.56C5.67 14.97 4.85 12.83 4.85 10.5zM11.5 8c1.38 0 2.5 1.12 2.5 2.5 0 1.05-.64 1.94-1.55 2.32l-1.9-4.72C10.66 8.04 11.07 8 11.5 8z"/></svg>',
    "map": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>',
    "chart": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>',
    "robot": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c-5.33 0-8 3.16-8 5v6c0 1.35.73 2.64 1.97 3.5H3.5v2h17v-2h-2.47C19.27 15.64 20 14.35 20 13V7c0-1.84-2.67-5-8-5zm0 2c3.51 0 5.4 1.83 5.86 3H6.14c.46-1.17 2.35-3 5.86-3zM7 11.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5S9.33 13 8.5 13 7 12.33 7 11.5zm8.5 1.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L1 21h22L12 2zm1.25 16.75h-2.5v-2.5h2.5v2.5zm0-4.5h-2.5v-6h2.5v6z"/></svg>',
    "chip": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h12v2H6V2zm0 18h12v2H6v-2zm12-4V8l4 4-4 4zm-12 0l-4-4 4-4v8zm2-6h8v4H8v-4z"/></svg>'
}

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        /* 1. GLOBAL RESET & FONT */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'JetBrains Mono', monospace;
            background-color: #0b0e11; 
            color: #e0e6ed;
        }

        /* 2. REMOVE STREAMLIT PADDING */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        
        /* 3. PANELS & CARDS */
        .cyber-card {
            background-color: rgba(21, 25, 33, 0.7);
            border: 1px solid rgba(0, 229, 255, 0.2);
            border-left: 3px solid #00e5ff;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        
        .alert-card {
            border-left: 3px solid #ffb703;
            background-color: rgba(255, 183, 3, 0.05);
            border-right: 1px solid rgba(255, 183, 3, 0.2);
        }

        /* 4. CHAT INTERFACE */
        .stChatMessage {
            background-color: #151921 !important;
            border: 1px solid #2d3748;
        }
        
        /* 5. CUSTOM BUTTONS */
        .stButton > button {
            background-color: transparent;
            color: #00e5ff;
            border: 1px solid #00e5ff;
            border-radius: 4px; 
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: rgba(0, 229, 255, 0.1);
            color: #fff;
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
        }

        /* 6. UTILITIES */
        .text-cyan { color: #00e5ff; text-shadow: 0 0 5px rgba(0, 229, 255, 0.3); }
        .text-amber { color: #ffb703; text-shadow: 0 0 5px rgba(255, 183, 3, 0.3); }
        .text-muted { color: #94a3b8; }
        
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0b0e11; }
        ::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 3px; }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def render_svg(svg_path, dim=32):
    """Renders SVG from file (Logo)"""
    try:
        if os.path.exists(svg_path):
            with open(svg_path, "r") as f:
                svg = f.read()
            b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
            return f'<img src="data:image/svg+xml;base64,{b64}" width="{dim}" height="{dim}" style="display: inline;"/>'
    except:
        return ""
    return ""

def get_icon(name, color="#00e5ff", size=24):
    """Renders Inline SVG Icon"""
    svg = ICONS.get(name, "")
    return f'<div style="display: inline-flex; align-items: center; justify-content: center; width: {size}px; height: {size}px; color: {color}; margin-right: 8px;">{svg}</div>'

def get_utc_time():
    return datetime.utcnow().strftime("%H:%M:%S UTC")

# --- TOP NAVIGATION ---
h1, h2, h3 = st.columns([2, 4, 2])

with h1:
    logo_html = render_svg(logo_path, dim=40)
    st.markdown(f"""
    <div style="display: flex; align-items: center;">
        {logo_html}
        <h2 style="margin: 0 0 0 10px; letter-spacing: 2px; color: #fff; font-size: 1.8rem;">FLASHPOINT</h2>
    </div>
    """, unsafe_allow_html=True)

with h2:
    # Replaced emojis with Chip/Alert icons in Marquee
    icon_alert = get_icon("alert", "#ffb703", 16)
    icon_sys = get_icon("chip", "#00e5ff", 16)
    
    st.markdown(f"""
    <div style="background: rgba(0, 229, 255, 0.05); border-left: 2px solid #00e5ff; padding: 10px; color: #00e5ff; font-family: 'JetBrains Mono'; font-size: 0.8rem; white-space: nowrap; overflow: hidden; display: flex; align-items: center;">
        <span style="display: inline-block; padding-left: 100%; animation: marquee 25s linear infinite;">
             REGION-4 MONITORING ACTIVE ... {icon_alert} SIGNAL INTERCEPTED AT 45.212 ... {icon_sys} NARRATIVE DIVERGENCE: STABLE ... {icon_alert} DEFCON 3 ALERT
        </span>
    </div>
    <style>
    @keyframes marquee {{ 0% {{ transform: translate(0, 0); }} 100% {{ transform: translate(-100%, 0); }} }}
    </style>
    """, unsafe_allow_html=True)

with h3:
    st.markdown(f"""
    <div style="text-align: right;">
        <span class="text-cyan">● SYSTEM ONLINE</span><br>
        <span class="text-muted" style="font-size: 0.8em;">{get_utc_time()}</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- DASHBOARD GRID ---
col_feed, col_map, col_intel = st.columns([1.2, 2.5, 1.3])

# --- 1. LIVE FEED ---
with col_feed:
    # REPLACED EMOJI 📡 -> ICON
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        {get_icon("broadcast", "#94a3b8", 28)}
        <h4 class="text-muted" style="margin: 0;">LIVE FEED</h4>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(height=600):
        feed_items = [
            {"text": "BREAKING: Large convoy of unidentified military vehicles spotted heading towards Border Region X.", "source": "Simulation", "bias": "Neutral/Raw", "url": "susuus.com", "timestamp": "12:34:56 UTC"},
            {"text": "Local residents in Border Region X report hearing heavy artillery fire. Power outages confirmed.", "source": "Simulation", "bias": "Human Intel", "url": "reddit.com" , "timestamp": "12:36:10 UTC"},
            {"text": "Defense Ministry announces 'Routine Training Exercises' near the border. Denies any aggressive intent.", "source": "Simulation", "bias": "State-Media (RU)", "url": "tass.com" , "timestamp": "12:36:30 UTC"},
            {"text": "US Satellite imagery confirms massive troop buildup. Pentagon warns of imminent incursion.", "source": "Simulation", "bias": "Western/Global", "url": "cnn.com" , "timestamp": "12:36:45 UTC"},
            {"text": "URGENT: Bridge connecting the two regions has been destroyed. Civilians trapped.", "source": "Simulation", "bias": "Neutral/Raw", "url": "telegram.com", "timestamp": "12:37:22 UTC"},
            {"text": "Foreign Ministry condemns 'Western hysteria' and provocation regarding border security measures.", "source": "Simulation", "bias": "State-Media (CN)", "url": "xinhuanet.com", "timestamp": "12:38:45 UTC"},
            {"text": "Reports of cyberattacks hitting regional hospitals and infrastructure. Communications down.", "source": "Simulation", "bias": "Human Intel", "url": "reddit.com", "timestamp": "12:39:01 UTC"},
            {"text": "UN Security Council calls for emergency meeting regarding the escalation in Region X.", "source": "Simulation", "bias": "Western/Global", "url": "reuters.com", "timestamp": "12:40:15 UTC"}
        ]
        
        for item in feed_items:
            if item['bias'] in ["State-Media (RU)", "State-Media (CN)"]:
                css_class = "cyber-card alert-card"
                tag_color = "#ffb703"
            elif item['bias'] == "Human Intel":
                css_class = "cyber-card"
                tag_color = "#94a3b8"
            else:
                css_class = "cyber-card"
                tag_color = "#00e5ff"

            st.markdown(f"""
            <div class="{css_class}">
                <div style="display: flex; justify-content: space-between; font-size: 0.75em; color: #cdd6f4;">
                    <span>[{item['timestamp']}] {item['source']}</span>
                    <span style="color: {tag_color}; font-weight: bold;">[{item['bias']}]</span>
                </div>
                <div style="margin-top: 5px; font-size: 0.9em; color: #e0e6ed;">
                    {item['text']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    b1, b2 = st.columns(2)
    b1.button("GENERATE REPORT", use_container_width=True)
    b2.button("INJECT SIMULATION", use_container_width=True)

# --- 2. TACTICAL MAP ---
with col_map:
    # REPLACED EMOJI 🗺️ -> ICON
    st.markdown(f"""
    <div style="display: flex; align-items: center;">
        {get_icon("map", "#00e5ff", 28)}
        <h4 class="text-cyan" style="margin: 0;">OPERATIONAL PICTURE</h4>
    </div>
    """, unsafe_allow_html=True)

    m = folium.Map(location=[48.3794, 31.1656], zoom_start=5, tiles="CartoDB dark_matter", control_scale=True)
    folium.CircleMarker([50.4501, 30.5234], radius=8, color="#ffb703", fill=True, fill_color="#ffb703", fill_opacity=0.7, popup="<b>Kyiv:</b> High Activity").add_to(m)
    folium.CircleMarker([55.7558, 37.6173], radius=6, color="#00e5ff", fill=True, fill_color="#00e5ff", fill_opacity=0.6, popup="<b>Moscow:</b> Official Comms").add_to(m)
    folium.Polygon(locations=[[49.0, 35.0], [48.0, 36.0], [47.0, 35.0], [48.0, 34.0]], color="#ffb703", weight=1, fill=True, fill_opacity=0.1, popup="Active Conflict Zone").add_to(m)
    
    st_folium(m, width="100%", height=550)
    
    # REPLACED EMOJI 📊 -> ICON
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-top: 15px;">
        {get_icon("chart", "#94a3b8", 24)}
        <h5 class="text-muted" style="margin: 0;">NARRATIVE DIVERGENCE</h5>
    </div>
    """, unsafe_allow_html=True)
    
    nd1, nd2 = st.columns(2)
    with nd1:
        st.markdown('<span style="color: #00e5ff;">WESTERN BLOC (65%)</span>', unsafe_allow_html=True)
        st.progress(65)
    with nd2:
        st.markdown('<span style="color: #ffb703;">EASTERN BLOC (35%)</span>', unsafe_allow_html=True)
        st.progress(35)

# --- 3. INTEL COMMANDER ---
with col_intel:
    # REPLACED EMOJI 🤖 -> ICON
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        {get_icon("robot", "#00e5ff", 28)}
        <h4 class="text-cyan" style="margin: 0;">INTEL COMMANDER</h4>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container(height=600):
        st.chat_message("assistant").write("Commander, system initialized. I am tracking 4,200 data points. Waiting for query.")
        st.chat_message("user").write("/analyze sector_4")
        st.chat_message("assistant").write("Analyzing Sector 4...\n\n**Result:** Activity Detected.\n- **Signal:** 300+ Telegram reports.\n- **Status:** Unconfirmed.\n- **Action:** Recommendation: Monitor.")
        
    st.text_input("COMMAND_LINE_INPUT >", placeholder="Type /help or query...", key="chat_input")