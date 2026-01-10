"""Streamlit dashboard for the FlashPoint front-end UI.

This file creates a three-column dashboard showing a live feed, a
geospatial operational map, and an intelligence chat interface.
The comments have been cleaned and consolidated for clarity; no
functional changes were made.
"""

import os
import base64
from datetime import datetime

import streamlit as st
import folium
import requests
from streamlit_folium import st_folium

from report import create_pdf, trigger_auto_download

# Base URL for back-end APIs (port appended at call sites)
API_BASE_URL = "http://localhost:"


# Page configuration
st.set_page_config(page_title="FLASHPOINT | INTEL COMMAND", page_icon="⚡", layout="wide")


# Assets
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(current_dir, "assets", "logo.svg")


# Small collection of inline SVG icons used in the UI
ICONS = {
    "broadcast": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M5 18.08c-1.42-.87-2.67-2.07-3.64-3.5L3.63 12C4.38 13.06 5.34 13.93 6.45 14.5l-1.45 3.58zm12.55 0l-1.45-3.58c1.11-.57 2.06-1.44 2.82-2.5L22.64 14.58c-.97 1.43-2.22 2.63-3.64 3.5zM2 10.5C2 5.25 6.25 1 11.5 1S21 5.25 21 10.5c0 2.33-.82 4.47-2.19 6.13l-1.44-3.56c.49-.78.78-1.7.78-2.69 0-2.9-2.35-5.25-5.25-5.25S7.65 7.48 7.65 10.38c0 1 .29 1.91.78 2.69l-1.44 3.56C5.67 14.97 4.85 12.83 4.85 10.5zM11.5 8c1.38 0 2.5 1.12 2.5 2.5 0 1.05-.64 1.94-1.55 2.32l-1.9-4.72C10.66 8.04 11.07 8 11.5 8z"/></svg>',
    "map": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>',
    "robot": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c-5.33 0-8 3.16-8 5v6c0 1.35.73 2.64 1.97 3.5H3.5v2h17v-2h-2.47C19.27 15.64 20 14.35 20 13V7c0-1.84-2.67-5-8-5zm0 2c3.51 0 5.4 1.83 5.86 3H6.14c.46-1.17 2.35-3 5.86-3zM7 11.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5S9.33 13 8.5 13 7 12.33 7 11.5zm8.5 1.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L1 21h22L12 2zm1.25 16.75h-2.5v-2.5h2.5v2.5zm0-4.5h-2.5v-6h2.5v6z"/></svg>',
    "chip": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h12v2H6V2zm0 18h12v2H6v-2zm12-4V8l4 4-4 4zm-12 0l-4-4 4-4v8zm2-6h8v4H8v-4z"/></svg>'
}


# Minimal CSS injected for consistent styling
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
      html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; background-color: #0b0e11; color: #e0e6ed; }
      .block-container { padding: 1rem 2rem; }
      .cyber-card { background-color: rgba(21,25,33,0.7); border-left: 3px solid #00e5ff; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
      .alert-card { border-left: 3px solid #ffb703; background-color: rgba(255,183,3,0.05); }
      .text-cyan { color: #00e5ff; }
      .text-muted { color: #94a3b8; }
      header, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_svg(svg_path, dim=32):
    """Return an <img> tag containing the SVG at svg_path encoded as base64.

    If the file doesn't exist or can't be read, an empty string is returned.
    """
    try:
        if os.path.exists(svg_path):
            with open(svg_path, "r", encoding="utf-8") as f:
                svg = f.read()
            b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
            return f'<img src="data:image/svg+xml;base64,{b64}" width="{dim}" height="{dim}"/>'
    except Exception:
        return ""
    return ""


def get_icon(name, color="#00e5ff", size=24):
    """Return a small inline SVG wrapper for an icon name.

    Falls back to an empty string if the icon is not defined.
    """
    svg = ICONS.get(name, "")
    return f'<div style="display:inline-flex;align-items:center;justify-content:center;width:{size}px;height:{size}px;color:{color};margin-right:8px">{svg}</div>'


def get_utc_time():
    return datetime.utcnow().strftime("%H:%M:%S UTC")


# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []


def fetch_feed():
    """Request latest feed items from the backend; return list or empty list on error."""
    try:
        response = requests.get(f"{API_BASE_URL}8000/v1/frontend/feed")
        if response.status_code == 200:
            return response.json()
    except Exception:
        # Keep UI resilient to transient backend failures
        return []
    return []


def send_chat_query(query):
    """Send a chat query to the intelligence API and return its response.

    On error, return a short error string that can be displayed to the user.
    """
    try:
        response = requests.post(f"{API_BASE_URL}8011/v1/query", json={"messages": query})
        if response.status_code == 200:
            return response.json()
        return "⚠️ Connection Error: Intel Core Unreachable."
    except Exception as e:
        return f"⚠️ System Error: {e}"


@st.fragment(run_every="2s")
def render_live_feed():
    """Render the live feed panel; polls backend and writes short cards for each item."""
    items = fetch_feed()
    west, east = calculate_narrative_balance(items)
    st.session_state["divergence"] = [west, east]

    if not items:
        st.info("Waiting for data stream...")
        return

    for item in reversed(items):
        text = item.get("text", "")
        source = item.get("source", "UNKNOWN")
        bias = item.get("bias", "Neutral")

        # Choose a compact class for visual emphasis on certain biases
        card_class = "cyber-card"
        if "Russia" in bias or "China" in bias:
            card_class += " alert-card"

        st.markdown(
            f"""
            <div class="{card_class}">
                <small style="color:#94a3b8;font-weight:bold;">{source} • {bias}</small>
                <div style="color:#e2e8f0;margin-top:4px;">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def calculate_narrative_balance(items):
    """Return (west_pct, east_pct) calculated from item bias tags.

    If there are no items, the function returns (50, 50) as a neutral default.
    """
    total = len(items)
    if total == 0:
        return 50, 50

    western_count = sum(1 for i in items if "Western" in i.get("bias", ""))
    eastern_count = sum(1 for i in items if ("Chine" in i.get("bias", "") or "Russia" in i.get("bias", "")))

    west_pct = int((western_count / total) * 100)
    east_pct = int((eastern_count / total) * 100)

    if west_pct + east_pct == 0:
        return 50, 50

    return west_pct, east_pct


def get_narration():
    """Return a short label indicating narrative divergence based on session state."""
    if "divergence" in st.session_state:
        west, east = st.session_state["divergence"]
        if (west - east > 30) or (west > 50):
            return "WEST"
        if (east - west > 30) or (east > 50):
            return "EAST"
    return "STABLE"


# --- Top navigation (three columns) ---
h1, h2, h3 = st.columns([2, 4, 2])

with h1:
    logo_html = render_svg(logo_path, dim=40)
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;">
            {logo_html}
            <h2 style="margin:0 0 0 10px;color:#fff;font-size:1.8rem;">FLASHPOINT</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h2:
    icon_alert = get_icon("alert", "#ffb703", 16)
    icon_sys = get_icon("chip", "#00e5ff", 16)
    st.markdown(
        f"""
        <div style="background:rgba(0,229,255,0.05);border-left:2px solid #00e5ff;padding:10px;color:#00e5ff;font-family:JetBrains Mono;white-space:nowrap;overflow:hidden;display:flex;align-items:center;">
            <span style="display:inline-block;padding-left:100%;animation:marquee 25s linear infinite;">REGION-4 MONITORING ACTIVE ... {icon_alert} NARRATIVE DIVERGENCE: {get_narration()} ... {icon_sys}</span>
        </div>
        <style>@keyframes marquee {{ from {{ transform: translate(0); }} to {{ transform: translate(-100%); }} }}</style>
        """,
        unsafe_allow_html=True,
    )

with h3:
    st.markdown(
        f"""
        <div style="text-align:right;"><span class="text-cyan">● SYSTEM ONLINE</span><br><span class="text-muted" style="font-size:0.8em;">{get_utc_time()}</span></div>
        """,
        unsafe_allow_html=True,
    )

st.divider()


# --- Dashboard columns: feed / map / intel ---
col_feed, col_map, col_intel = st.columns([1.2, 2.5, 1.3])


with col_feed:
    # Live feed header
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;margin-bottom:10px;">{get_icon('broadcast','#94a3b8',28)}<h4 class="text-muted" style="margin:0;">LIVE FEED</h4></div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(height=500):
        render_live_feed()

    # Generate report button: requests backend and stores report text in session state
    if st.button("GENERATE REPORT", use_container_width=True):
        with st.spinner("Generating SITREP..."):
            try:
                res = requests.get(f"{API_BASE_URL}8000/v1/generate_report")
                if res.status_code == 200:
                    st.session_state["latest_report"] = res.json().get("report", "No report generated.")
                    st.success("Report Generated Successfully")
                else:
                    st.error("Failed to contact Intelligence Core.")
            except Exception as e:
                st.error(f"Connection Error: {e}")

    # If a report exists, show preview and provide PDF download
    if "latest_report" in st.session_state:
        st.text_area("Preview", st.session_state["latest_report"], height=300)
        pdf_bytes = create_pdf(st.session_state["latest_report"])
        trigger_auto_download(pdf_bytes, f"SITREP_{datetime.date}.pdf")


with col_map:
    st.markdown(f"""<div style="display:flex;align-items:center;">{get_icon('map','#00e5ff',28)}<h4 class="text-cyan" style="margin:0;">OPERATIONAL PICTURE</h4></div>""", unsafe_allow_html=True)

    items = fetch_feed()
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbdark_matter")

    map_data_found = False
    for item in items:
        if "lat" in item and "lon" in item:
            map_data_found = True
            bias = item.get("bias", "Neutral")
            if "Russia" in bias or "China" in bias or "Eastern" in bias:
                color = "#ef4444"
            elif "Western" in bias or "US" in bias:
                color = "#0ea5e9"
            else:
                color = "#22c55e"

            folium.CircleMarker(
                location=[item["lat"], item["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(f"<b>{item.get('source','')}</b><br>{item.get('text','')[:100]}...", max_width=300),
                tooltip=f"{item.get('source','')} ({bias})",
            ).add_to(m)

    # Render the map or show a friendly message if no geo data is present
    if map_data_found:
        st_folium(m, width=None, height=450, use_container_width=True)
    else:
        st.info("📡 Scanning for geolocation signals...")
        st_folium(m, width=None, height=450, use_container_width=True)

    west_pct, east_pct = st.session_state.get("divergence", (0, 0))
    neutral_pct = max(0, 100 - (east_pct + west_pct))

    st.markdown("""<div style="display:flex;width:100%;font-size:1rem;font-weight:bold;"> <div style="width:33%;text-align:left;color:#00e5ff;">WESTERN</div> <div style="width:33%;text-align:center;color:#999;">NEUTRAL</div> <div style="width:33%;text-align:right;color:#ffb703;">EASTERN</div> </div>""", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="display:flex;width:100%;height:24px;background:#334155;border-radius:12px;overflow:hidden;font-family:monospace;font-weight:bold;">
            <div style="width:{west_pct}%;background:#00e5ff;display:flex;align-items:center;justify-content:center;color:black">{int(west_pct)}%</div>
            <div style="width:{neutral_pct}%;background:#999;display:flex;align-items:center;justify-content:center;color:black">{int(neutral_pct)}%</div>
            <div style="width:{east_pct}%;background:#ffb703;display:flex;align-items:center;justify-content:center;color:black">{int(east_pct)}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col_intel:
    st.markdown(f"""<div style="display:flex;align-items:center;margin-bottom:10px;">{get_icon('robot','#00e5ff',28)}<h4 class='text-cyan' style='margin:0;'>INTEL ANALYSIS</h4></div>""", unsafe_allow_html=True)

    # Chat history area
    container = st.container(height=500)
    with container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input handling
    if prompt := st.chat_input("Query the intelligence database..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with container:
            with st.chat_message("user"):
                st.markdown(prompt)

        with container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🔄 *Analyzing secure channels...*")
                full_response = send_chat_query(prompt)
                message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
