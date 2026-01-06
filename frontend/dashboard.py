import streamlit as st
import pandas as pd 
import folium 
from streamlit_folium import st_folium
import time
import base64
import os
# page configration 
st.set_page_config(
    page_title="FLASHPOINT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "assets", "logo.svg")

# --- SVG LOADER FUNCTION ---
# This helper function reads the SVG code so Streamlit renders it perfectly
def render_svg(svg_path, width=200):
    try:
        with open(svg_path, "r") as f:
            svg_content = f.read()
        # Encode to base64 to ensure it displays correctly regardless of browser
        b64 = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")
        html = f'<img src="data:image/svg+xml;base64,{b64}" width="{width}"/>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:
        # Fallback if file is missing
        st.error(f"Logo missing: {svg_path}")
# Custom CSS 
st.markdown("""
    <style>
        /* Hide Streamlit Header/Footer */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Main Background */
        .stApp {
            background-color: #050505;
        }
        
        /* Card Styling (Glassmorphism) */
        div.css-1r6slb0.e1tzin5v2 {
            background-color: #111;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 5px;
        }

        /* Neon Text Effects */
        .neon-text {
            color: #00ff41;
            text-shadow: 0 0 5px #00ff41;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
        }
        
        .alert-text {
            color: #ff003c;
            text-shadow: 0 0 5px #ff003c;
            font-weight: bold;
        }
        
        /* Custom Borders for Columns */
        [data-testid="column"] {
            border-right: 1px solid #333;
            padding-right: 15px;
        }
    </style>
""", unsafe_allow_html=True)


# sidebar
with st.sidebar:
    render_svg(logo_path, width=200)

    st.markdown("### ⚙️ Settings")
    st.toggle("Live Feed",value=True)
    st.toggle("Notifications",value=True)
    st.markdown("---")
    st.markdown("Status: **🟢 ONLINE**")

# --- HEADER ---
# Adjusted ratios: [1.8, 3.2, 1] to give a bit more room for the logo+title
col_head1, col_head2, col_head3 = st.columns([1.8, 3.2, 1])

with col_head1:
    # Split this column: 1 part for Logo, 3 parts for Name
    c1, c2 = st.columns([1, 4])
    
    with c1:
        # Render the SVG Logo (Icon)
        render_svg(logo_path, width=50)
        
    with c2:
        # Render the Title Text with custom styling to align it vertically
        st.markdown("""
            <h2 style='
                margin: 0; 
                padding-top: 5px; 
                color: #fafafa; 
                font-family: sans-serif; 
                letter-spacing: 2px;
            '>FLASHPOINT</h2>
        """, unsafe_allow_html=True)

with col_head2:
    st.info("🔴 LIVE: MONITORING 4 SOURCES [TELEGRAM, REDDIT, TASS, REUTERS]... DETECTING ANOMALIES IN SECTOR 4...")

with col_head3:
    st.markdown("<h3 class='alert-text' style='text-align: center; border: 2px solid red; border-radius: 5px;'>DEFCON 3</h3>", unsafe_allow_html=True)

st.markdown("---")


# Main dashboard
col1,col2,col3=st.columns([2,5,3])
with col1:
    st.markdown("### 📡 INCOMING STREAM")

    # buttons
    f1,f2=st.columns(2)
    f1.button("ALL",use_container_width=True)
    f2.button("CONFLICT",use_container_width=True,type="primary")

    # mock data 
    news_items = [
        {"source": "TELEGRAM", "author": "@insider_paper", "time": "12:45", "text": "🚨 Breaking: Tanks moving near Border X. Visual confirmation pending.", "sentiment": "negative"},
        {"source": "REDDIT", "author": "r/conflictnews", "time": "12:42", "text": "Video shows smoke rising in Region Y. Locals claim drill gone wrong.", "sentiment": "neutral"},
        {"source": "TASS", "author": "State Media", "time": "12:40", "text": "Kremlin announces unscheduled military drill in western district.", "sentiment": "positive"},
        {"source": "REUTERS", "author": "Wire", "time": "12:35", "text": "Oil prices spike as tensions rise in Eastern Europe.", "sentiment": "negative"},
    ]
    # Scrollabel container for feed 
    with st.container(height=500):
        for item in news_items:
            border_color = "#ff003c" if item['sentiment'] == "negative" else "#00ff41"
            st.markdown(f"""
            <div style="border-left: 3px solid {border_color}; padding-left: 10px; margin-bottom: 15px; background-color: #1a1a1a;">
                <small style="color: #888;">{item['time']} | <b>{item['source']}</b></small><br>
                <span style="color: #fff;">{item['text']}</span>
            </div>
            """, unsafe_allow_html=True)
# map 
with col2:
    st.markdown("### 🗺️ TACTICAL MAP")

    m=folium.Map(location=[48.3794,31.1656],zoom_start=5,tiles="CartoDB dark_matter")

    folium.Marker(
        [50.4501, 30.5234], 
        popup="<b>Kyiv</b><br>Air Raid Siren", 
        icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
    ).add_to(m)

    folium.Marker(
        [55.7558, 37.6173], 
        popup="<b>Moscow</b><br>Official Statement", 
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    # Rendor map
    st_folium(m,width="100%",height=500)
 
# AI assitant 
with col3:
    st.markdown("### 🤖 INTEL ANALYST")
    
    with st.container(height=420):
        st.chat_message("assistant").write("System initialized. Monitoring narrative divergence. How can I assist?")
        st.chat_message("user").write("Summarize the last hour.")
        st.chat_message("assistant").write("Analysis: High activity detected near ")
        st.chat_message("assistant").write("Analysis: High activity detected near Border X. Western sources claim 'aggression' while Eastern sources claim 'drills'. Divergence score: 85%.")
    
    st.chat_input("Enter command...",key="chat_input")



st.markdown("---")
st.markdown("### 📊 NARRATIVE DIVERGENCE ANALYSIS")

m1,m2 =st.columns(2)

with m1:
    st.caption("WESTERN NARRATIVE (CNN, Reddit, BBC)")
    st.progress(80, text="Focus: Aggression / Unprovoked")

with m2:
    st.caption("EASTERN NARRATIVE (TASS, Telegram, Weibo)")
    st.progress(65, text="Focus: Defense / Security Drill")