"""
  AURA — RFID Attendance Intelligence  ◆ Linear Edition ◆
  ──────────────────────────────────────────────────────
  Stack  : Python · Firebase RTDB · firebase-admin · Streamlit
  Theme  : Linear.app Clone — Precision, Borders, Inter Typography
  Build  : 4.0.0 — Linear Edition
"""

import streamlit as st
import pandas as pd
import time
import os
import random
from datetime import datetime, timedelta

try:
    import firebase_admin
    from firebase_admin import credentials, db as rtdb
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

DATABASE_URL         = os.environ.get("FIREBASE_DATABASE_URL", "https://your-project-default-rtdb.firebaseio.com")
SERVICE_ACCOUNT_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
RFID_LOG_NODE        = "rfid_logs"
AUTO_REFRESH_SECONDS = 6

st.set_page_config(
    page_title="Aura — Attendance",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LINEAR_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ═══════════════════════════════════════════════════════════
   THE ARCHITECTURAL CANVAS — LINEAR'S LAYERED DARKNESS
   ═══════════════════════════════════════════════════════════ */

:root {
  /* The Void — Strictly Layered Dark Palette */
  --bg-workspace:       #0a0a0a;  /* The absolute base */
  --bg-surface:         #111111;  /* Card/panel level */
  --bg-overlay:         #161616;  /* Hover/active level */
  --bg-elevated:        #1a1a1a;  /* Button base */
  
  /* The Border (Linear's Signature) */
  --border-base:        rgba(255, 255, 255, 0.08);
  --border-hover:       rgba(255, 255, 255, 0.1);
  --border-strong:      rgba(255, 255, 255, 0.3);
  
  /* The Gradient Mist — Subtle Top-Down Glow */
  --gradient-mist:      linear-gradient(180deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0) 100%);
  
  /* Typography Precision */
  --text-primary:       #eeeeee;
  --text-secondary:     #888888;
  --text-tertiary:      #555555;
  
  /* Linear Purple & Status Colors */
  --linear-purple:      #5e6ad2;
  --status-ok:          #34d399;   /* Green dot for connected */
  --status-denied:      #f87171;   /* Red for denied */
  --status-warning:     #fbbf24;   /* Yellow for unknown */
  
  /* Spacing & Rhythm */
  --radius:             4px;
  --transition:         120ms ease;
  
  /* Typography */
  --font-primary:       'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono:          'JetBrains Mono', 'Geist Mono', monospace;
}

/* ═══════════════════════════════════════════════════════════
   GLOBAL RESETS & BASE STYLES
   ═══════════════════════════════════════════════════════════ */

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
  background: var(--bg-workspace) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-primary) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Clean canvas - no gradients, pure flat darkness */
[data-testid="stAppViewContainer"] {
  background: var(--bg-workspace) !important;
}

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header {
  visibility: hidden !important;
}

[data-testid="stToolbar"],
[data-testid="stSidebar"],
section[data-testid="stSidebar"],
.stDeployButton,
[data-testid="collapsedControl"] {
  display: none !important;
}

/* Linear-style scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* Remove default Streamlit gaps */
[data-testid="stHorizontalBlock"] {
  gap: 0 !important;
}

[data-testid="column"] {
  padding: 0 !important;
}

/* ═══════════════════════════════════════════════════════════
   THE NAVIGATION BAR — SLIM, FIXED-HEIGHT HEADER (48px)
   ═══════════════════════════════════════════════════════════ */

.linear-nav {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-base);
  background: var(--bg-workspace);
  position: sticky;
  top: 0;
  z-index: 100;
}

/* Breadcrumb Navigation */
.linear-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.breadcrumb-separator {
  color: var(--text-tertiary);
  font-weight: 400;
}

.breadcrumb-item {
  color: var(--text-secondary);
  transition: color var(--transition);
}

.breadcrumb-item:last-child {
  color: var(--text-primary);
}

.breadcrumb-item:hover {
  color: var(--text-primary);
}

/* Connection Status Pill */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all var(--transition);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--status-ok);
  animation: pulse 2s ease-in-out infinite;
}

.status-pill.offline .status-dot {
  background: var(--text-tertiary);
  animation: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ═══════════════════════════════════════════════════════════
   THE ISSUE-LIST FEED — LINEAR'S SIGNATURE ROW DESIGN
   ═══════════════════════════════════════════════════════════ */

.linear-content {
  display: flex;
  min-height: calc(100vh - 48px);
}

.linear-main {
  flex: 1;
  border-right: 1px solid var(--border-base);
}

.linear-sidebar {
  width: 320px;
  background: var(--bg-workspace);
}

/* Section Header */
.section-header {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-base);
  background: var(--bg-workspace);
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.section-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
}

/* Log Feed Container */
.log-feed {
  background: var(--bg-workspace);
}

/* Individual Log Row (40px height) */
.log-row {
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background: var(--bg-workspace);
  transition: background var(--transition);
  cursor: pointer;
  animation: row-appear 0.2s ease;
}

.log-row:hover {
  background: var(--bg-overlay);
}

@keyframes row-appear {
  from {
    opacity: 0;
    transform: translateY(-2px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Scan Animation — 1px horizontal line moving top-to-bottom */
.log-row.scanning::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--linear-purple), transparent);
  animation: scan-line 1s ease-in-out;
}

@keyframes scan-line {
  from { top: 0; opacity: 0; }
  50% { opacity: 1; }
  to { top: 100%; opacity: 0; }
}

/* Avatar Circle */
.log-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}

/* Name & UID */
.log-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.log-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.log-uid {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-tertiary);
  white-space: nowrap;
}

/* Timestamp */
.log-timestamp {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-tertiary);
  white-space: nowrap;
}

/* Status Badge */
.log-status {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: var(--radius);
  border: 1px solid;
  white-space: nowrap;
}

.log-status.access {
  color: var(--status-ok);
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.2);
}

.log-status.denied {
  color: var(--status-denied);
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.2);
}

.log-status.unknown {
  color: var(--status-warning);
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.2);
}

/* ═══════════════════════════════════════════════════════════
   THE SIDEBAR WIDGETS — COMMAND MENU STYLING
   ═══════════════════════════════════════════════════════════ */

.sidebar-panel {
  padding: 24px;
  border-bottom: 1px solid var(--border-base);
}

.sidebar-panel:last-child {
  border-bottom: none;
}

.panel-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

/* Stats Cards (Top Row) */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid var(--border-base);
}

.stat-card {
  padding: 16px;
  background: var(--bg-surface);
  background-image: var(--gradient-mist);
  border: 1px solid var(--border-base);
  border-radius: var(--radius);
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

/* Hourly Activity Chart — Minimalist Sparkline */
.activity-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 60px;
  margin-top: 12px;
}

.activity-bar {
  flex: 1;
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: 2px;
  transition: all var(--transition);
  position: relative;
  min-height: 4px;
}

.activity-bar.active {
  background: var(--linear-purple);
  border-color: var(--linear-purple);
}

.activity-bar:hover {
  background: var(--bg-overlay);
  border-color: var(--border-strong);
}

.activity-label {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 400;
  color: var(--text-tertiary);
  text-align: center;
  margin-top: 6px;
}

/* Recent Scans List */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.recent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.recent-dot.ok {
  background: var(--status-ok);
}

.recent-dot.denied {
  background: var(--status-denied);
}

.recent-dot.unknown {
  background: var(--status-warning);
}

.recent-name {
  flex: 1;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

.recent-time {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 400;
  color: var(--text-tertiary);
}

/* ═══════════════════════════════════════════════════════════
   PRECISION BUTTONS — LINEAR STYLE
   ═══════════════════════════════════════════════════════════ */

/* Streamlit Button Override */
div[data-testid="stButton"] > button {
  width: 100% !important;
  height: 32px !important;
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-base) !important;
  border-radius: var(--radius) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-primary) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  padding: 0 12px !important;
  transition: all var(--transition) !important;
  cursor: pointer !important;
}

div[data-testid="stButton"] > button:hover {
  background: var(--bg-overlay) !important;
  border-color: var(--border-strong) !important;
}

div[data-testid="stButton"] > button:active {
  transform: scale(0.98) !important;
}

/* Streamlit Selectbox Override */
div[data-testid="stSelectbox"] > label {
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  color: var(--text-secondary) !important;
  margin-bottom: 8px !important;
}

div[data-testid="stSelectbox"] > div > div {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border-base) !important;
  border-radius: var(--radius) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-primary) !important;
  font-size: 12px !important;
  transition: all var(--transition) !important;
}

div[data-testid="stSelectbox"] > div > div:hover {
  border-color: var(--border-strong) !important;
}

/* ═══════════════════════════════════════════════════════════
   LOADING & EMPTY STATES
   ═══════════════════════════════════════════════════════════ */

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.3;
}

.empty-text {
  font-size: 13px;
  font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUT TAGS
   ═══════════════════════════════════════════════════════════ */

.kbd {
  display: inline-block;
  padding: 2px 6px;
  background: #333333;
  border: 1px solid var(--border-base);
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
}

/* ═══════════════════════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════════════════════ */

.linear-footer {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-top: 1px solid var(--border-base);
  background: var(--bg-workspace);
  font-size: 11px;
  color: var(--text-tertiary);
}

</style>
"""

@st.cache_resource(show_spinner=False)
def init_firebase():
    if not FIREBASE_AVAILABLE: return None, "firebase_admin not installed"
    try:
        if not firebase_admin._apps:
            if "firebase" in st.secrets: cred = credentials.Certificate(dict(st.secrets["firebase"]))
            elif os.path.exists(SERVICE_ACCOUNT_PATH): cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            else: return None, f"No credentials at '{SERVICE_ACCOUNT_PATH}'"
            firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
        return rtdb, None
    except Exception as exc: return None, str(exc)

def fetch_logs_firebase(db_ref, limit=200):
    try:
        data = db_ref.reference(RFID_LOG_NODE).order_by_key().limit_to_last(limit).get()
        if not data: return pd.DataFrame()
        rows = [{"timestamp":v.get("timestamp",k),"name":v.get("name","Unknown"),"uid":v.get("uid","—"),"status":v.get("status","ACCESS")} for k,v in data.items()]
        df = pd.DataFrame(rows); df["timestamp"] = pd.to_datetime(df["timestamp"],errors="coerce",utc=True)
        return df.sort_values("timestamp",ascending=False).reset_index(drop=True)
    except Exception as e: st.warning(f"Firebase error: {e}"); return pd.DataFrame()

_NAMES=["Aiden Park","Zoe Nakamura","Luca Ferrara","Maya Okonkwo","Ethan Mercer","Sasha Ivanova","Priya Sharma","Noah Chen","Isla Torres","Ravi Kapoor","Emma Lindqvist","Jin-Ho Bae"]
_UIDS=[f"{random.randint(10,99)}:{random.randint(10,99)}:FF:{random.randint(10,99)}" for _ in range(12)]
_STATS=["ACCESS","ACCESS","ACCESS","ACCESS","ACCESS","DENIED","UNKNOWN"]

@st.cache_data(ttl=AUTO_REFRESH_SECONDS)
def fetch_logs_demo(n=50):
    now=datetime.utcnow()
    rows=[{"timestamp":now-timedelta(minutes=random.randint(0,480),seconds=random.randint(0,59)),"name":_NAMES[random.randint(0,11)],"uid":_UIDS[random.randint(0,11)],"status":random.choice(_STATS)} for _ in range(n)]
    return pd.DataFrame(rows).sort_values("timestamp",ascending=False).reset_index(drop=True)

def compute_stats(df):
    if df.empty: return 0, 0, 0
    today = datetime.utcnow().date()
    ts = df["timestamp"]
    if pd.api.types.is_datetime64_any_dtype(ts):
        try: ts_n = ts.dt.tz_convert(None)
        except: ts_n = ts
        mask = ts_n.dt.date == today
    else: mask = pd.Series([True]*len(df))
    today_df = df[mask]
    return len(today_df), today_df["name"].nunique(), len(df)

def build_hourly(df):
    now = datetime.utcnow()
    labels = [(now - timedelta(hours=11-i)).strftime("%H") for i in range(12)]
    slots = [0] * 12
    if df.empty: return list(zip(labels, slots))
    ts = df["timestamp"]
    if not pd.api.types.is_datetime64_any_dtype(ts): return list(zip(labels, slots))
    try: ts = ts.dt.tz_convert(None)
    except: pass
    for i in range(12):
        s0 = (now - timedelta(hours=11-i)).replace(minute=0, second=0, microsecond=0)
        s1 = s0 + timedelta(hours=1)
        slots[i] = int(((ts >= s0) & (ts < s1)).sum())
    return list(zip(labels, slots))

def initials(name):
    p = name.strip().split()
    return (p[0][0] + p[-1][0]).upper() if len(p) >= 2 else name[:2].upper()

def status_class(status):
    s = str(status).upper()
    if s in ("ACCESS", "GRANTED", "OK"): return "access"
    if s in ("DENIED", "REJECTED"): return "denied"
    return "unknown"

def status_text(status):
    s = str(status).upper()
    if s in ("ACCESS", "GRANTED", "OK"): return "Access"
    if s in ("DENIED", "REJECTED"): return "Denied"
    return s.title()

def render_nav(is_live):
    status_class_name = "status-pill" if is_live else "status-pill offline"
    status_text = "Connected" if is_live else "Demo Mode"
    
    st.markdown(f'''
    <div class="linear-nav">
        <div class="linear-breadcrumb">
            <span class="breadcrumb-item">AURA</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">ATTENDANCE</span>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-item">LIVE FEED</span>
        </div>
        <div class="{status_class_name}">
            <div class="status-dot"></div>
            <span>{status_text}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def render_stats_grid(total_today, unique_today, total_all):
    st.markdown(f'''
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{total_today:,}</div>
            <div class="stat-label">Today's Scans</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{unique_today:,}</div>
            <div class="stat-label">Unique Students</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{total_all:,}</div>
            <div class="stat-label">Total Events</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def render_log_feed(df, max_rows=50):
    if df.empty:
        st.markdown('''
        <div class="empty-state">
            <div class="empty-icon">◆</div>
            <div class="empty-text">Awaiting RFID events</div>
        </div>
        ''', unsafe_allow_html=True)
        return
    
    rows_html = ""
    for idx, row in df.head(max_rows).iterrows():
        ts = row["timestamp"]
        timestamp_str = ts.strftime("%b %d · %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        
        status_cls = status_class(row["status"])
        status_txt = status_text(row["status"])
        
        rows_html += f'''
        <div class="log-row">
            <div class="log-avatar">{initials(str(row["name"]))}</div>
            <div class="log-info">
                <div class="log-name">{row["name"]}</div>
                <div class="log-uid">{row["uid"]}</div>
            </div>
            <div class="log-timestamp">{timestamp_str}</div>
            <div class="log-status {status_cls}">{status_txt}</div>
        </div>
        '''
    
    st.markdown(f'<div class="log-feed">{rows_html}</div>', unsafe_allow_html=True)

def render_hourly_chart(chart_data):
    max_val = max(v for _, v in chart_data) or 1
    now_h = datetime.utcnow().strftime("%H")
    
    bars_html = ""
    for label, val in chart_data:
        height_pct = max(5, int((val / max_val) * 100))
        active_class = " active" if label == now_h else ""
        
        bars_html += f'''
        <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
            <div class="activity-bar{active_class}" style="height: {height_pct}%;"></div>
            <div class="activity-label">{label}</div>
        </div>
        '''
    
    st.markdown(f'<div class="activity-chart">{bars_html}</div>', unsafe_allow_html=True)

def render_recent_list(df, n=6):
    if df.empty: return
    
    items_html = ""
    for _, row in df.head(n).iterrows():
        ts = row["timestamp"]
        time_str = ts.strftime("%H:%M") if hasattr(ts, "strftime") else "—"
        
        dot_class = status_class(row["status"])
        if dot_class == "access": dot_class = "ok"
        
        items_html += f'''
        <div class="recent-item">
            <div class="recent-dot {dot_class}"></div>
            <div class="recent-name">{row["name"]}</div>
            <div class="recent-time">{time_str}</div>
        </div>
        '''
    
    st.markdown(f'<div class="recent-list">{items_html}</div>', unsafe_allow_html=True)

if "max_rows" not in st.session_state:
    st.session_state.max_rows = 50

def main():
    st.markdown(LINEAR_CSS, unsafe_allow_html=True)
    
    # Initialize Firebase
    db_ref, firebase_error = init_firebase()
    is_live = db_ref is not None
    
    # Fetch data
    df = fetch_logs_firebase(db_ref, limit=200) if is_live else fetch_logs_demo(n=60)
    
    # Render navigation
    render_nav(is_live)
    
    # Compute stats
    total_today, unique_today, total_all = compute_stats(df)
    
    # Render stats grid
    render_stats_grid(total_today, unique_today, total_all)
    
    # Main layout: 4:1.5 split
    st.markdown('<div class="linear-content">', unsafe_allow_html=True)
    
    col_main, col_side = st.columns([4, 1.5], gap="medium")
    
    with col_main:
        st.markdown('<div class="linear-main">', unsafe_allow_html=True)
        
        # Section header
        st.markdown(f'''
        <div class="section-header">
            <div class="section-label">Access Log</div>
            <div class="section-count">{min(len(df), st.session_state.max_rows)} entries</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Log feed
        render_log_feed(df, max_rows=st.session_state.max_rows)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_side:
        st.markdown('<div class="linear-sidebar">', unsafe_allow_html=True)
        
        # Hourly Activity Panel
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Hourly Activity</div>', unsafe_allow_html=True)
        render_hourly_chart(build_hourly(df))
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent Scans Panel
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Recent Scans</div>', unsafe_allow_html=True)
        render_recent_list(df, n=6)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Controls Panel
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-label">Controls</div>', unsafe_allow_html=True)
        
        st.session_state.max_rows = st.selectbox(
            "Visible entries",
            [25, 50, 100, 200],
            index=1,
            key="row_select"
        )
        
        if st.button("↻ Refresh Now"):
            if is_live:
                fetch_logs_firebase.clear()
            else:
                fetch_logs_demo.clear()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    refresh_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f'''
    <div class="linear-footer">
        <span>Aura · Linear Edition · v4.0.0</span>
        <span>Last sync: {refresh_ts} UTC</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(AUTO_REFRESH_SECONDS)
    st.rerun()

if __name__ == "__main__":
    main()
