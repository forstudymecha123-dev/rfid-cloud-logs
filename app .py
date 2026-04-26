"""
╔══════════════════════════════════════════════════════════════════╗
║  NEXUS-RFID // ESP32 Attendance Monitoring System               ║
║  Build: 2.4.1 | Deploy: Streamlit Community Cloud              ║
║  Stack: Python · Firebase RTDB · firebase-admin · Streamlit     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import time
import json
import os
import random
from datetime import datetime, timedelta

# ── Firebase Admin ────────────────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, db as rtdb
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────
#  CONFIGURATION  (edit these or use Streamlit Secrets)
# ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://your-project-default-rtdb.firebaseio.com"  # ← replace
)

# Path to serviceAccountKey.json  OR  inject via Streamlit secrets
SERVICE_ACCOUNT_PATH = os.environ.get(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    "serviceAccountKey.json"  # ← replace / use secrets
)

RFID_LOG_NODE = "rfid_logs"   # Firebase node where ESP32 writes logs
AUTO_REFRESH_SECONDS = 5      # polling interval for real-time feed

# ─────────────────────────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEXUS-RFID // Attendance Monitor",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────
#  INJECT GLOBAL CSS  — Cyberpunk / Industrial Dark Mode
# ─────────────────────────────────────────────────────────────────
CYBER_CSS = """
<style>
/* ── Google Font Import ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@300;400;500;600;700&display=swap');

/* ── Root Variables ── */
:root {
  --bg-void:       #000000;
  --bg-surface:    #080808;
  --bg-glass:      rgba(0, 255, 240, 0.04);
  --bg-glass-dark: rgba(0, 0, 0, 0.60);
  --cyan:          #00ffe0;
  --cyan-dim:      #00ffe040;
  --cyan-glow:     0 0 8px #00ffe080, 0 0 24px #00ffe030;
  --lime:          #b4ff39;
  --lime-dim:      #b4ff3930;
  --purple:        #c353ff;
  --purple-dim:    #c353ff25;
  --red-alert:     #ff3860;
  --text-primary:  #e8fff8;
  --text-muted:    #4a7a6e;
  --border-dim:    rgba(0, 255, 224, 0.12);
  --border-active: rgba(0, 255, 224, 0.55);
  --font-mono:     'Share Tech Mono', monospace;
  --font-display:  'Rajdhani', sans-serif;
  --radius-sm:     4px;
  --radius-md:     8px;
}

/* ── Global Reset ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
  background: var(--bg-void) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-mono) !important;
}

/* ── Tight layout ── */
.block-container { padding: 1.4rem 2rem 2rem !important; max-width: 1600px; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #050505; }
::-webkit-scrollbar-thumb { background: var(--cyan-dim); border-radius: 2px; }

/* ══════════════════════════════════════════════════════════
   TOPBAR / HEADER
══════════════════════════════════════════════════════════ */
.nexus-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1.5rem;
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-md);
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  margin-bottom: 1.4rem;
  position: relative;
  overflow: hidden;
}
.nexus-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
  animation: scan-line 3s linear infinite;
}
@keyframes scan-line {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.nexus-logo {
  font-family: var(--font-display);
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: var(--cyan);
  text-shadow: var(--cyan-glow);
  text-transform: uppercase;
}
.nexus-logo span { color: var(--lime); }
.nexus-sub {
  font-size: 0.7rem;
  letter-spacing: 0.25em;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-top: 2px;
}
.nexus-status-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  letter-spacing: 0.15em;
  color: var(--lime);
  text-transform: uppercase;
}
.nexus-status-badge .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--lime);
  box-shadow: 0 0 6px var(--lime), 0 0 12px var(--lime);
  animation: pulse-dot 1.4s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.4; transform: scale(0.75); }
}
.nexus-clock {
  font-size: 0.85rem;
  color: var(--text-muted);
  letter-spacing: 0.1em;
}

/* ══════════════════════════════════════════════════════════
   STAT CARDS (glassmorphism)
══════════════════════════════════════════════════════════ */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.4rem;
}
.stat-card {
  background: var(--bg-glass);
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-md);
  padding: 1.1rem 1.3rem;
  backdrop-filter: blur(16px);
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s, box-shadow 0.3s;
  cursor: default;
}
.stat-card:hover {
  border-color: var(--border-active);
  box-shadow: 0 0 20px rgba(0,255,224,0.08);
}
.stat-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}
.stat-card.card-cyan::after  { background: linear-gradient(90deg, transparent, var(--cyan), transparent); }
.stat-card.card-lime::after  { background: linear-gradient(90deg, transparent, var(--lime), transparent); }
.stat-card.card-purple::after{ background: linear-gradient(90deg, transparent, var(--purple), transparent); }
.stat-label {
  font-size: 0.62rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.stat-value {
  font-family: var(--font-display);
  font-size: 2.6rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.04em;
}
.stat-value.cyan   { color: var(--cyan);   text-shadow: var(--cyan-glow); }
.stat-value.lime   { color: var(--lime);   text-shadow: 0 0 8px var(--lime), 0 0 22px #b4ff3940; }
.stat-value.purple { color: var(--purple); text-shadow: 0 0 8px var(--purple), 0 0 22px var(--purple-dim); }
.stat-corner {
  position: absolute;
  top: 0.7rem; right: 0.9rem;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  opacity: 0.35;
  text-transform: uppercase;
}

/* ══════════════════════════════════════════════════════════
   SECTION TITLES
══════════════════════════════════════════════════════════ */
.section-title {
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.35em;
  text-transform: uppercase;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 0.75rem;
}
.section-title::before {
  content: '';
  display: inline-block;
  width: 16px; height: 1px;
  background: var(--cyan);
  box-shadow: var(--cyan-glow);
}
.section-title::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-dim);
}

/* ══════════════════════════════════════════════════════════
   LOG TABLE
══════════════════════════════════════════════════════════ */
.log-wrapper {
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-glass-dark);
  margin-bottom: 1.4rem;
}
.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
  font-family: var(--font-mono);
}
.log-table thead tr {
  border-bottom: 1px solid var(--border-active);
}
.log-table thead th {
  padding: 0.65rem 1rem;
  text-align: left;
  font-size: 0.6rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--cyan);
  font-weight: normal;
  background: rgba(0,255,224,0.04);
}
.log-table tbody tr {
  border-bottom: 1px solid var(--border-dim);
  transition: background 0.15s;
}
.log-table tbody tr:hover { background: rgba(0,255,224,0.04); }
.log-table tbody tr:last-child { border-bottom: none; }
.log-table td {
  padding: 0.55rem 1rem;
  color: var(--text-primary);
  vertical-align: middle;
}
.log-table td.ts    { color: var(--text-muted); font-size: 0.72rem; }
.log-table td.name  { color: var(--cyan); }
.log-table td.uid   { color: var(--text-muted); letter-spacing: 0.1em; font-size: 0.7rem; }
.badge {
  display: inline-block;
  padding: 0.18rem 0.6rem;
  border-radius: 2px;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-weight: 600;
}
.badge-access  { background: rgba(180,255,57,0.1);  color: var(--lime);    border: 1px solid rgba(180,255,57,0.3); }
.badge-denied  { background: rgba(255,56,96,0.1);   color: var(--red-alert);border: 1px solid rgba(255,56,96,0.3); }
.badge-unknown { background: rgba(195,83,255,0.1);  color: var(--purple);  border: 1px solid rgba(195,83,255,0.3); }

/* ══════════════════════════════════════════════════════════
   ACTIVITY BAR CHART (CSS-only)
══════════════════════════════════════════════════════════ */
.chart-wrapper {
  border: 1px solid var(--border-dim);
  border-radius: var(--radius-md);
  padding: 1.1rem 1.3rem;
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  margin-bottom: 1.4rem;
}
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 80px;
  padding-top: 0.5rem;
}
.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.bar-fill {
  width: 100%;
  border-radius: 2px 2px 0 0;
  background: linear-gradient(180deg, var(--cyan) 0%, rgba(0,255,224,0.2) 100%);
  box-shadow: 0 -2px 6px rgba(0,255,224,0.4);
  animation: bar-grow 0.8s ease-out both;
  transform-origin: bottom;
}
@keyframes bar-grow {
  from { transform: scaleY(0); }
  to   { transform: scaleY(1); }
}
.bar-label {
  font-size: 0.55rem;
  color: var(--text-muted);
  letter-spacing: 0.05em;
}

/* ══════════════════════════════════════════════════════════
   SCAN TICKER (live feed strip)
══════════════════════════════════════════════════════════ */
.scan-ticker {
  background: var(--bg-surface);
  border: 1px solid var(--border-dim);
  border-left: 3px solid var(--cyan);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: 0.5rem 1rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  animation: slide-in 0.35s ease-out both;
}
@keyframes slide-in {
  from { opacity: 0; transform: translateX(-12px); }
  to   { opacity: 1; transform: translateX(0); }
}
.scan-ticker .ts   { color: var(--text-muted); font-size: 0.68rem; }
.scan-ticker .name { color: var(--cyan); flex: 1; }
.scan-ticker .uid  { color: var(--text-muted); font-size: 0.68rem; }

/* ══════════════════════════════════════════════════════════
   LOADING / SCANNING ANIMATION
══════════════════════════════════════════════════════════ */
.scan-loader {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  color: var(--text-muted);
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}
.scan-loader .bars {
  display: flex;
  gap: 3px;
  align-items: flex-end;
  height: 18px;
}
.scan-loader .bar {
  width: 3px;
  background: var(--cyan);
  border-radius: 1px;
  animation: loader-bounce 1.0s ease-in-out infinite;
}
.scan-loader .bar:nth-child(1) { height: 6px;  animation-delay: 0.0s; }
.scan-loader .bar:nth-child(2) { height: 12px; animation-delay: 0.1s; }
.scan-loader .bar:nth-child(3) { height: 18px; animation-delay: 0.2s; }
.scan-loader .bar:nth-child(4) { height: 12px; animation-delay: 0.3s; }
.scan-loader .bar:nth-child(5) { height: 6px;  animation-delay: 0.4s; }
@keyframes loader-bounce {
  0%, 100% { transform: scaleY(0.3); opacity: 0.3; }
  50%       { transform: scaleY(1.0); opacity: 1.0; }
}

/* ══════════════════════════════════════════════════════════
   FOOTER
══════════════════════════════════════════════════════════ */
.nexus-footer {
  margin-top: 2rem;
  border-top: 1px solid var(--border-dim);
  padding-top: 0.8rem;
  display: flex;
  justify-content: space-between;
  font-size: 0.6rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-muted);
  opacity: 0.6;
}

/* ══════════════════════════════════════════════════════════
   STREAMLIT WIDGET OVERRIDES
══════════════════════════════════════════════════════════ */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stCheckbox"] label,
div[data-testid="stRadio"] label,
div[data-testid="stNumberInput"] label {
  font-family: var(--font-mono) !important;
  font-size: 0.7rem !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  color: var(--text-muted) !important;
}
div[data-testid="stSelectbox"] div,
div[data-testid="stNumberInput"] div input {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border-dim) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-mono) !important;
  border-radius: var(--radius-sm) !important;
}
div[data-testid="stButton"] > button {
  background: transparent !important;
  border: 1px solid var(--border-active) !important;
  color: var(--cyan) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.2em !important;
  text-transform: uppercase !important;
  border-radius: var(--radius-sm) !important;
  transition: background 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
  background: var(--cyan-dim) !important;
  box-shadow: var(--cyan-glow) !important;
}
</style>
"""

# ─────────────────────────────────────────────────────────────────
#  FIREBASE INIT  (singleton via st.cache_resource)
# ─────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_firebase():
    """Initialise Firebase Admin SDK once per deployment lifecycle."""
    if not FIREBASE_AVAILABLE:
        return None, "firebase_admin not installed"

    try:
        if firebase_admin._apps:
            app = firebase_admin.get_app()
        else:
            # Priority 1 → Streamlit Secrets (recommended for Cloud)
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cred_dict)
            # Priority 2 → local serviceAccountKey.json (dev)
            elif os.path.exists(SERVICE_ACCOUNT_PATH):
                cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            else:
                return None, f"No credentials found at '{SERVICE_ACCOUNT_PATH}'"

            app = firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

        return rtdb, None

    except Exception as exc:
        return None, str(exc)


# ─────────────────────────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────────────────────────
def fetch_logs_firebase(db_ref, limit: int = 200) -> pd.DataFrame:
    """Pull last `limit` records from Firebase RTDB."""
    try:
        ref = db_ref.reference(RFID_LOG_NODE)
        data = ref.order_by_key().limit_to_last(limit).get()
        if not data:
            return pd.DataFrame()

        rows = []
        for key, val in data.items():
            rows.append({
                "timestamp": val.get("timestamp", key),
                "name":      val.get("name", "UNKNOWN"),
                "uid":       val.get("uid", "—"),
                "status":    val.get("status", "ACCESS"),
            })

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
        return df

    except Exception as e:
        st.warning(f"Firebase read error: {e}")
        return pd.DataFrame()


# ── Demo data generator (used when Firebase is not connected) ────
_DEMO_NAMES = [
    "Mira Nakamura", "Dex Ortega", "Yuki Tanaka", "Echo Vasquez",
    "Kai Reinholt", "Zara Okonkwo", "Finn Mercer", "Aria Zheng",
    "Niko Papadopoulos", "Sable Torres",
]
_DEMO_UIDS  = [f"A{random.randint(1,9)}:{random.randint(10,99)}:FF:{random.randint(10,99)}" for _ in range(10)]
_STATUSES   = ["ACCESS", "ACCESS", "ACCESS", "ACCESS", "DENIED", "UNKNOWN"]

@st.cache_data(ttl=AUTO_REFRESH_SECONDS)
def fetch_logs_demo(n: int = 40) -> pd.DataFrame:
    """Generate synthetic RFID log data for demo / offline mode."""
    now = datetime.utcnow()
    rows = []
    for i in range(n):
        offset = timedelta(minutes=random.randint(0, 480), seconds=random.randint(0, 59))
        idx = random.randint(0, len(_DEMO_NAMES) - 1)
        rows.append({
            "timestamp": now - offset,
            "name":      _DEMO_NAMES[idx],
            "uid":       _DEMO_UIDS[idx],
            "status":    random.choice(_STATUSES),
        })

    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    return df


def compute_stats(df: pd.DataFrame, start_time: datetime):
    """Derive KPI metrics from log dataframe."""
    if df.empty:
        return 0, 0, "00:00:00"

    today = datetime.utcnow().date()

    if pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        today_mask = df["timestamp"].dt.date == today
    else:
        today_mask = pd.Series([True] * len(df))

    today_df     = df[today_mask]
    total_scans  = len(today_df)
    unique_stds  = today_df["name"].nunique() if not today_df.empty else 0

    uptime_secs  = int((datetime.utcnow() - start_time).total_seconds())
    h, remainder = divmod(uptime_secs, 3600)
    m, s         = divmod(remainder, 60)
    uptime_str   = f"{h:02d}:{m:02d}:{s:02d}"

    return total_scans, unique_stds, uptime_str


def build_hourly_chart(df: pd.DataFrame) -> list:
    """Return 12-slot hourly scan counts for bar chart (last 12h)."""
    slots = [0] * 12
    labels = []
    now = datetime.utcnow()

    for i in range(11, -1, -1):
        slot_start = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
        labels.append(slot_start.strftime("%H"))

    if df.empty:
        return list(zip(labels, slots))

    ts_col = df["timestamp"]
    if not pd.api.types.is_datetime64_any_dtype(ts_col):
        return list(zip(labels, slots))

    # strip tz if present
    try:
        ts_col = ts_col.dt.tz_convert(None)
    except TypeError:
        pass

    for i, label in enumerate(labels):
        slot_start = (now - timedelta(hours=11 - i)).replace(minute=0, second=0, microsecond=0)
        slot_end   = slot_start + timedelta(hours=1)
        count = ((ts_col >= slot_start) & (ts_col < slot_end)).sum()
        slots[i] = int(count)

    return list(zip(labels, slots))


# ─────────────────────────────────────────────────────────────────
#  HTML COMPONENT BUILDERS
# ─────────────────────────────────────────────────────────────────
def render_header(live: bool, refresh_ts: str):
    mode_text  = "SYSTEM LIVE" if live else "DEMO MODE"
    mode_color = "#b4ff39" if live else "#c353ff"
    st.markdown(f"""
    <div class="nexus-header">
      <div>
        <div class="nexus-logo">NEXUS<span>-</span>RFID</div>
        <div class="nexus-sub">ESP32 · Attendance Monitoring System · v2.4.1</div>
      </div>
      <div class="nexus-status-badge" style="color:{mode_color}">
        <div class="dot" style="background:{mode_color};box-shadow:0 0 6px {mode_color};"></div>
        {mode_text}
      </div>
      <div class="nexus-clock">{refresh_ts} UTC</div>
    </div>
    """, unsafe_allow_html=True)


def render_stat_cards(total_scans, unique_stds, uptime_str):
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card card-cyan">
        <div class="stat-corner">Today</div>
        <div class="stat-label">Total Scans</div>
        <div class="stat-value cyan">{total_scans:04d}</div>
      </div>
      <div class="stat-card card-lime">
        <div class="stat-corner">Unique</div>
        <div class="stat-label">Students Present</div>
        <div class="stat-value lime">{unique_stds:03d}</div>
      </div>
      <div class="stat-card card-purple">
        <div class="stat-corner">HH:MM:SS</div>
        <div class="stat-label">System Uptime</div>
        <div class="stat-value purple" style="font-size:2rem;">{uptime_str}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_hourly_chart(chart_data: list):
    max_val = max(v for _, v in chart_data) or 1
    bars_html = ""
    for label, val in chart_data:
        pct = max(4, int((val / max_val) * 100))
        bars_html += f"""
        <div class="bar-item">
          <div class="bar-fill" style="height:{pct}%;"></div>
          <div class="bar-label">{label}</div>
        </div>"""

    st.markdown(f"""
    <div class="chart-wrapper">
      <div class="section-title">Hourly Activity (last 12 h)</div>
      <div class="bar-chart">{bars_html}</div>
    </div>
    """, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    s = str(status).upper()
    if s in ("ACCESS", "GRANTED", "OK"):
        return f'<span class="badge badge-access">ACCESS</span>'
    elif s in ("DENIED", "REJECTED"):
        return f'<span class="badge badge-denied">DENIED</span>'
    else:
        return f'<span class="badge badge-unknown">{s}</span>'


def render_log_table(df: pd.DataFrame, max_rows: int = 50):
    if df.empty:
        st.markdown("""
        <div class="log-wrapper">
          <div class="scan-loader">
            <div class="bars">
              <div class="bar"></div><div class="bar"></div>
              <div class="bar"></div><div class="bar"></div>
              <div class="bar"></div>
            </div>
            Awaiting RFID signal&hellip;
          </div>
        </div>""", unsafe_allow_html=True)
        return

    rows_html = ""
    for _, row in df.head(max_rows).iterrows():
        ts = row["timestamp"]
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        rows_html += f"""
        <tr>
          <td class="ts">{ts_str}</td>
          <td class="name">{row['name']}</td>
          <td class="uid">{row['uid']}</td>
          <td>{status_badge(row['status'])}</td>
        </tr>"""

    st.markdown(f"""
    <div class="log-wrapper">
      <table class="log-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Student Name</th>
            <th>UID</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)


def render_live_ticker(df: pd.DataFrame, n: int = 5):
    if df.empty:
        return
    for _, row in df.head(n).iterrows():
        ts = row["timestamp"]
        ts_str = ts.strftime("%H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        st.markdown(f"""
        <div class="scan-ticker">
          <span class="ts">{ts_str}</span>
          <span class="name">{row['name']}</span>
          <span class="uid">{row['uid']}</span>
          {status_badge(row['status'])}
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.utcnow()
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.utcnow()
if "max_rows" not in st.session_state:
    st.session_state.max_rows = 50


# ─────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────
def main():
    # Inject CSS
    st.markdown(CYBER_CSS, unsafe_allow_html=True)

    # ── Firebase init ──
    db_ref, firebase_error = init_firebase()
    is_live = (db_ref is not None)

    # ── Fetch data ──
    if is_live:
        df = fetch_logs_firebase(db_ref, limit=200)
    else:
        df = fetch_logs_demo(n=60)

    refresh_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # ── Header ──
    render_header(live=is_live, refresh_ts=refresh_ts)

    # ── Firebase error notice ──
    if firebase_error and not is_live:
        st.markdown(f"""
        <div style="
          border:1px solid #c353ff40; background:#c353ff08;
          border-left:3px solid #c353ff; border-radius:0 4px 4px 0;
          padding:0.55rem 1rem; font-size:0.72rem; color:#c353ff;
          letter-spacing:0.1em; margin-bottom:1rem;">
          ⬡ FIREBASE OFFLINE — {firebase_error} — Rendering synthetic demo data
        </div>""", unsafe_allow_html=True)

    # ── KPI Cards ──
    total_scans, unique_stds, uptime_str = compute_stats(
        df, st.session_state.start_time
    )
    render_stat_cards(total_scans, unique_stds, uptime_str)

    # ── Two-column layout ──
    col_left, col_right = st.columns([2, 1], gap="medium")

    with col_left:
        st.markdown('<div class="section-title">Scan Log Feed</div>', unsafe_allow_html=True)
        render_log_table(df, max_rows=st.session_state.max_rows)

    with col_right:
        st.markdown('<div class="section-title">Hourly Activity</div>', unsafe_allow_html=True)
        chart_data = build_hourly_chart(df)
        render_hourly_chart(chart_data)

        st.markdown('<div class="section-title" style="margin-top:1rem;">Recent Scans</div>', unsafe_allow_html=True)
        render_live_ticker(df, n=6)

        # ── Controls ──
        st.markdown('<div class="section-title" style="margin-top:1.2rem;">Controls</div>', unsafe_allow_html=True)
        st.session_state.max_rows = st.selectbox(
            "Rows to display", [25, 50, 100, 200],
            index=1, key="row_select"
        )
        if st.button("⟳  Force Refresh"):
            st.session_state.last_refresh = datetime.utcnow()
            if is_live:
                fetch_logs_firebase.clear()          # bust cache
            else:
                fetch_logs_demo.clear()
            st.rerun()

    # ── Footer ──
    st.markdown(f"""
    <div class="nexus-footer">
      <span>NEXUS-RFID // ESP32 Attendance Monitor</span>
      <span>Refreshed: {refresh_ts} UTC</span>
      <span>Node: {RFID_LOG_NODE}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Auto-refresh (polling) ──
    time.sleep(AUTO_REFRESH_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
