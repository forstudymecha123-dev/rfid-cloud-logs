"""
  AURA — RFID Attendance Intelligence
  ─────────────────────────────────────────────────────────
  Stack  : Python · Firebase RTDB · firebase-admin · Streamlit
  Deploy : Streamlit Community Cloud (GitHub)
  Build  : 3.0.0 — Premium Edition
"""

import streamlit as st
import pandas as pd
import time
import os
import random
from datetime import datetime, timedelta

# ── Firebase Admin ────────────────────────────────────────
try:
    import firebase_admin
    from firebase_admin import credentials, db as rtdb
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# ─────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://your-project-default-rtdb.firebaseio.com"   # ← replace
)
SERVICE_ACCOUNT_PATH = os.environ.get(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    "serviceAccountKey.json"                              # ← replace
)
RFID_LOG_NODE        = "rfid_logs"
AUTO_REFRESH_SECONDS = 6

# ─────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Aura — Attendance Intelligence",
    page_icon="○",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────
#  CSS — QUIET LUXURY / PREMIUM DARK
# ─────────────────────────────────────────────────────────
PREMIUM_CSS = """
<style>

/* ── Typeface ──────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Design Tokens ──────────────────────────────────────── */
:root {
  --bg-base:            #0a0a0a;
  --bg-elevated:        #111111;
  --bg-card:            rgba(255,255,255,0.035);
  --bg-card-hover:      rgba(255,255,255,0.055);
  --bg-input:           rgba(255,255,255,0.05);
  --border-subtle:      rgba(255,255,255,0.07);
  --border-moderate:    rgba(255,255,255,0.12);
  --border-strong:      rgba(255,255,255,0.22);
  --text-primary:       #f0f0f0;
  --text-secondary:     #888888;
  --text-tertiary:      #555555;
  --accent:             #4f8ef7;
  --accent-dim:         rgba(79,142,247,0.15);
  --status-ok:          #34c759;
  --status-ok-dim:      rgba(52,199,89,0.1);
  --status-denied:      #ff3b30;
  --status-denied-dim:  rgba(255,59,48,0.1);
  --status-unknown:     #636366;
  --status-unknown-dim: rgba(99,99,102,0.15);
  --radius-sm:  10px;
  --radius-md:  14px;
  --radius-lg:  18px;
  --radius-xl:  24px;
  --ease-apple: cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --dur-fast:   140ms;
  --dur-base:   240ms;
  --dur-slow:   420ms;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display',
          'Helvetica Neue', sans-serif;
}

/* ── Global Base ─────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .block-container {
  background: var(--bg-base) !important;
  color: var(--text-primary) !important;
  font-family: var(--font) !important;
  -webkit-font-smoothing: antialiased;
}

.block-container {
  padding: 2rem 2.5rem 3rem !important;
  max-width: 1440px !important;
}

/* ── Strip Streamlit Chrome ───────────────────────────── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stToolbar"]  { display: none !important; }
[data-testid="stSidebar"]  { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 99px;
}

/* ── Column gap ───────────────────────────────────────── */
[data-testid="stHorizontalBlock"] { gap: 1.5rem !important; }

/* ══════════════════════════════════════════════════════════
   KEYFRAMES
══════════════════════════════════════════════════════════ */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes heartbeat {
  0%, 100% { opacity: 1;   transform: scale(1); }
  50%       { opacity: 0.3; transform: scale(0.6); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes bar-rise {
  from { transform: scaleY(0); }
  to   { transform: scaleY(1); }
}

/* ══════════════════════════════════════════════════════════
   NAV BAR
══════════════════════════════════════════════════════════ */
.aura-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 1.8rem;
  border-bottom: 0.5px solid var(--border-subtle);
  margin-bottom: 2.5rem;
  animation: fade-in var(--dur-slow) var(--ease-apple) both;
}
.aura-brand { display: flex; align-items: baseline; gap: 0.6rem; }
.aura-brand-name {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-primary);
}
.aura-brand-sep { color: var(--border-moderate); font-weight: 300; font-size: 1rem; }
.aura-brand-sub {
  font-size: 0.73rem;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
}
.aura-nav-right { display: flex; align-items: center; gap: 1.4rem; }
.live-pill {
  display: flex; align-items: center; gap: 0.45rem;
  background: var(--status-ok-dim);
  border: 0.5px solid rgba(52,199,89,0.22);
  border-radius: 99px;
  padding: 0.28rem 0.75rem;
  font-size: 0.68rem; font-weight: 500;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--status-ok);
}
.live-pill.offline {
  background: var(--status-unknown-dim);
  border-color: rgba(99,99,102,0.25);
  color: var(--text-secondary);
}
.live-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--status-ok);
  animation: heartbeat 2s ease-in-out infinite;
}
.live-pill.offline .live-dot { background: var(--status-unknown); animation: none; }
.nav-ts {
  font-size: 0.7rem; color: var(--text-tertiary);
  font-variant-numeric: tabular-nums; letter-spacing: 0.04em;
}

/* ══════════════════════════════════════════════════════════
   STAT CARDS
══════════════════════════════════════════════════════════ */
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 2.5rem;
}
.stat-card {
  background: var(--bg-card);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.6rem 1.5rem 1.3rem;
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  position: relative; overflow: hidden;
  transition:
    background var(--dur-base) var(--ease-apple),
    transform  var(--dur-base) var(--ease-apple),
    border-color var(--dur-base) var(--ease-apple);
  animation: fade-up var(--dur-slow) var(--ease-apple) both;
  cursor: default;
}
.stat-card:nth-child(1) { animation-delay: 0.04s; }
.stat-card:nth-child(2) { animation-delay: 0.08s; }
.stat-card:nth-child(3) { animation-delay: 0.12s; }
.stat-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-moderate);
  transform: translateY(-2px);
}
/* etched aluminum highlight */
.stat-card::before {
  content: '';
  position: absolute; top: 0; left: 14%; right: 14%; height: 0.5px;
  background: linear-gradient(90deg,
    transparent, rgba(255,255,255,0.16) 40%,
    rgba(255,255,255,0.16) 60%, transparent);
}
.stat-icon { font-size: 1rem; margin-bottom: 0.9rem; opacity: 0.4; }
.stat-label {
  font-size: 0.66rem; font-weight: 500;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-secondary); margin-bottom: 0.5rem;
}
.stat-value {
  font-size: 2.8rem; font-weight: 700;
  letter-spacing: -0.03em; line-height: 1;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.stat-value.clr-accent { color: var(--accent); }
.stat-value.clr-ok     { color: var(--status-ok); }
.stat-note {
  margin-top: 0.55rem; font-size: 0.66rem;
  color: var(--text-tertiary); letter-spacing: 0.02em;
}

/* ══════════════════════════════════════════════════════════
   SECTION HEADER
══════════════════════════════════════════════════════════ */
.sec-hdr {
  display: flex; align-items: center;
  justify-content: space-between;
  margin-bottom: 0.9rem;
}
.sec-label {
  font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--text-secondary);
}
.sec-count { font-size: 0.66rem; color: var(--text-tertiary); font-variant-numeric: tabular-nums; }

/* ══════════════════════════════════════════════════════════
   LOG CAPSULE FEED
══════════════════════════════════════════════════════════ */
.log-feed { display: flex; flex-direction: column; gap: 0.45rem; }
.log-capsule {
  display: flex; align-items: center; gap: 0.9rem;
  background: var(--bg-card);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 0.85rem 1rem;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  transition:
    background var(--dur-fast) var(--ease-apple),
    border-color var(--dur-fast) var(--ease-apple);
  animation: fade-up var(--dur-base) var(--ease-apple) both;
  position: relative; overflow: hidden;
}
.log-capsule::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 0.5px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
}
.log-capsule:hover { background: var(--bg-card-hover); border-color: var(--border-moderate); }
.log-capsule:nth-child(1) { animation-delay: 0.04s; }
.log-capsule:nth-child(2) { animation-delay: 0.08s; }
.log-capsule:nth-child(3) { animation-delay: 0.12s; }
.log-capsule:nth-child(4) { animation-delay: 0.16s; }
.log-capsule:nth-child(5) { animation-delay: 0.20s; }
.log-capsule:nth-child(n+6){ animation-delay: 0.23s; }

.log-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 600; flex-shrink: 0;
  background: rgba(255,255,255,0.055);
  border: 0.5px solid rgba(255,255,255,0.1);
  color: var(--text-secondary); letter-spacing: 0.02em;
}
.log-body { flex: 1; min-width: 0; }
.log-name {
  font-size: 0.85rem; font-weight: 500; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.log-uid {
  font-size: 0.65rem; color: var(--text-tertiary);
  font-variant-numeric: tabular-nums; margin-top: 0.15rem;
  letter-spacing: 0.04em;
}
.log-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.3rem; flex-shrink: 0; }
.log-time {
  font-size: 0.65rem; color: var(--text-tertiary);
  font-variant-numeric: tabular-nums; letter-spacing: 0.03em;
}

/* ── Status Pill ── */
.pill {
  display: inline-flex; align-items: center; gap: 0.28rem;
  padding: 0.18rem 0.55rem; border-radius: 99px;
  font-size: 0.6rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
}
.pill::before { content: ''; width: 4px; height: 4px; border-radius: 50%; }
.pill-ok      { background: var(--status-ok-dim);      color: var(--status-ok);      border: 0.5px solid rgba(52,199,89,0.25); }
.pill-ok::before { background: var(--status-ok); }
.pill-denied  { background: var(--status-denied-dim);  color: var(--status-denied);  border: 0.5px solid rgba(255,59,48,0.25); }
.pill-denied::before { background: var(--status-denied); }
.pill-unknown { background: var(--status-unknown-dim); color: var(--status-unknown); border: 0.5px solid rgba(99,99,102,0.3); }
.pill-unknown::before { background: var(--status-unknown); }

/* ── Loading ── */
.loading-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 4rem 2rem; gap: 1rem;
}
.loading-ring {
  width: 26px; height: 26px;
  border: 1.5px solid var(--border-subtle);
  border-top-color: var(--text-tertiary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.loading-txt { font-size: 0.75rem; color: var(--text-tertiary); letter-spacing: 0.06em; }

/* ══════════════════════════════════════════════════════════
   SIDE PANELS
══════════════════════════════════════════════════════════ */
.panel {
  background: var(--bg-card);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.3rem 1.2rem;
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  margin-bottom: 1rem;
  position: relative; overflow: hidden;
  animation: fade-up var(--dur-slow) var(--ease-apple) 0.12s both;
}
.panel::before {
  content: ''; position: absolute; top: 0; left: 12%; right: 12%; height: 0.5px;
  background: linear-gradient(90deg,
    transparent, rgba(255,255,255,0.11) 40%,
    rgba(255,255,255,0.11) 60%, transparent);
}

/* ── Bar Chart ── */
.bar-chart-wrap {
  display: flex; align-items: flex-end; gap: 4px;
  height: 68px; margin-top: 0.9rem; padding-bottom: 4px;
}
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 3px; }
.bar-fill {
  width: 100%; border-radius: 3px 3px 0 0;
  background: rgba(255,255,255,0.1);
  transform-origin: bottom;
  animation: bar-rise var(--dur-slow) var(--ease-apple) both; min-height: 3px;
}
.bar-fill.active { background: var(--accent); opacity: 0.8; }
.bar-tick { font-size: 0.5rem; color: var(--text-tertiary); font-variant-numeric: tabular-nums; }

/* ── Mini list ── */
.mini-list { display: flex; flex-direction: column; margin-top: 0.75rem; }
.mini-row {
  display: flex; align-items: center; gap: 0.65rem;
  padding: 0.45rem 0; border-bottom: 0.5px solid var(--border-subtle);
}
.mini-row:last-child { border-bottom: none; }
.mini-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.mini-dot.ok      { background: var(--status-ok); }
.mini-dot.denied  { background: var(--status-denied); }
.mini-dot.unknown { background: var(--status-unknown); }
.mini-name { flex: 1; font-size: 0.77rem; font-weight: 500; color: var(--text-primary); }
.mini-time { font-size: 0.63rem; color: var(--text-tertiary); font-variant-numeric: tabular-nums; }

/* ── Alert ── */
.alert-banner {
  display: flex; align-items: center; gap: 0.7rem;
  background: rgba(255,255,255,0.03);
  border: 0.5px solid var(--border-subtle);
  border-radius: var(--radius-md); padding: 0.65rem 1rem;
  margin-bottom: 2rem; font-size: 0.71rem; color: var(--text-secondary);
  letter-spacing: 0.02em;
  animation: fade-up var(--dur-base) var(--ease-apple) both;
}
.alert-icon { opacity: 0.5; font-size: 0.8rem; }

/* ══════════════════════════════════════════════════════════
   STREAMLIT WIDGET OVERRIDES
══════════════════════════════════════════════════════════ */
div[data-testid="stSelectbox"] label {
  font-family: var(--font) !important;
  font-size: 0.66rem !important; font-weight: 500 !important;
  letter-spacing: 0.1em !important; text-transform: uppercase !important;
  color: var(--text-secondary) !important;
}
div[data-testid="stSelectbox"] > div > div {
  background: var(--bg-input) !important;
  border: 0.5px solid var(--border-moderate) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-family: var(--font) !important; font-size: 0.82rem !important;
}
div[data-testid="stButton"] > button {
  width: 100% !important;
  background: rgba(255,255,255,0.04) !important;
  border: 0.5px solid var(--border-moderate) !important;
  color: var(--text-primary) !important;
  font-family: var(--font) !important;
  font-size: 0.77rem !important; font-weight: 500 !important;
  letter-spacing: 0.06em !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.58rem 1rem !important;
  transition: background var(--dur-fast) var(--ease-apple),
              border-color var(--dur-fast) var(--ease-apple) !important;
  margin-top: 0.5rem !important;
}
div[data-testid="stButton"] > button:hover {
  background: rgba(255,255,255,0.08) !important;
  border-color: var(--border-strong) !important;
}
div[data-testid="stButton"] > button:active { transform: scale(0.98) !important; }

/* ══════════════════════════════════════════════════════════
   FOOTER
══════════════════════════════════════════════════════════ */
.aura-footer {
  margin-top: 3rem; padding-top: 1.2rem;
  border-top: 0.5px solid var(--border-subtle);
  display: flex; justify-content: space-between; align-items: center;
}
.footer-l, .footer-r {
  font-size: 0.63rem; color: var(--text-tertiary); letter-spacing: 0.05em;
}

</style>
"""

# ─────────────────────────────────────────────────────────
#  FIREBASE INIT
# ─────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_firebase():
    if not FIREBASE_AVAILABLE:
        return None, "firebase_admin not installed"
    try:
        if firebase_admin._apps:
            firebase_admin.get_app()
        else:
            if "firebase" in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
            elif os.path.exists(SERVICE_ACCOUNT_PATH):
                cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            else:
                return None, f"No credentials at '{SERVICE_ACCOUNT_PATH}'"
            firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
        return rtdb, None
    except Exception as exc:
        return None, str(exc)


# ─────────────────────────────────────────────────────────
#  DATA LAYER
# ─────────────────────────────────────────────────────────
def fetch_logs_firebase(db_ref, limit: int = 200) -> pd.DataFrame:
    try:
        ref  = db_ref.reference(RFID_LOG_NODE)
        data = ref.order_by_key().limit_to_last(limit).get()
        if not data:
            return pd.DataFrame()
        rows = [
            {"timestamp": v.get("timestamp", k), "name": v.get("name", "Unknown"),
             "uid": v.get("uid", "—"), "status": v.get("status", "ACCESS")}
            for k, v in data.items()
        ]
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    except Exception as e:
        st.warning(f"Firebase error: {e}")
        return pd.DataFrame()


_NAMES = [
    "Aiden Park", "Zoe Nakamura", "Luca Ferrara", "Maya Okonkwo",
    "Ethan Mercer", "Sasha Ivanova", "Priya Sharma", "Noah Chen",
    "Isla Torres", "Ravi Kapoor", "Emma Lindqvist", "Jin-Ho Bae",
]
_UIDS  = [f"{random.randint(10,99)}:{random.randint(10,99)}:FF:{random.randint(10,99)}" for _ in range(12)]
_STATS = ["ACCESS","ACCESS","ACCESS","ACCESS","ACCESS","DENIED","UNKNOWN"]


@st.cache_data(ttl=AUTO_REFRESH_SECONDS)
def fetch_logs_demo(n: int = 50) -> pd.DataFrame:
    now = datetime.utcnow()
    rows = []
    for _ in range(n):
        idx = random.randint(0, len(_NAMES) - 1)
        rows.append({
            "timestamp": now - timedelta(minutes=random.randint(0, 480),
                                         seconds=random.randint(0, 59)),
            "name":   _NAMES[idx],
            "uid":    _UIDS[idx],
            "status": random.choice(_STATS),
        })
    return (pd.DataFrame(rows)
            .sort_values("timestamp", ascending=False)
            .reset_index(drop=True))


def compute_stats(df: pd.DataFrame, start_time: datetime):
    if df.empty:
        return 0, 0, "00:00:00"
    today = datetime.utcnow().date()
    ts = df["timestamp"]
    if pd.api.types.is_datetime64_any_dtype(ts):
        try:    ts_n = ts.dt.tz_convert(None)
        except: ts_n = ts
        mask = ts_n.dt.date == today
    else:
        mask = pd.Series([True] * len(df))
    today_df = df[mask]
    up = int((datetime.utcnow() - start_time).total_seconds())
    h, r = divmod(up, 3600); m, s = divmod(r, 60)
    return len(today_df), today_df["name"].nunique(), f"{h:02d}:{m:02d}:{s:02d}"


def build_hourly(df: pd.DataFrame) -> list:
    now    = datetime.utcnow()
    labels = [(now - timedelta(hours=11 - i)).strftime("%H") for i in range(12)]
    slots  = [0] * 12
    if df.empty:
        return list(zip(labels, slots))
    ts = df["timestamp"]
    if not pd.api.types.is_datetime64_any_dtype(ts):
        return list(zip(labels, slots))
    try:    ts = ts.dt.tz_convert(None)
    except: pass
    for i in range(12):
        s0 = (now - timedelta(hours=11 - i)).replace(minute=0, second=0, microsecond=0)
        s1 = s0 + timedelta(hours=1)
        slots[i] = int(((ts >= s0) & (ts < s1)).sum())
    return list(zip(labels, slots))


# ─────────────────────────────────────────────────────────
#  HTML HELPERS
# ─────────────────────────────────────────────────────────
def pill_html(status: str) -> str:
    s = str(status).upper()
    if s in ("ACCESS", "GRANTED", "OK"):
        return '<span class="pill pill-ok">Access</span>'
    if s in ("DENIED", "REJECTED"):
        return '<span class="pill pill-denied">Denied</span>'
    return f'<span class="pill pill-unknown">{s.title()}</span>'


def dot_cls(status: str) -> str:
    s = str(status).upper()
    if s in ("ACCESS", "GRANTED", "OK"):   return "ok"
    if s in ("DENIED", "REJECTED"):        return "denied"
    return "unknown"


def initials(name: str) -> str:
    p = name.strip().split()
    return (p[0][0] + p[-1][0]).upper() if len(p) >= 2 else name[:2].upper()


# ─────────────────────────────────────────────────────────
#  RENDER FUNCTIONS
# ─────────────────────────────────────────────────────────
def render_nav(is_live: bool, ts: str):
    pill_cls  = "live-pill" if is_live else "live-pill offline"
    pill_text = "Live" if is_live else "Demo"
    st.markdown(f"""
    <div class="aura-nav">
      <div class="aura-brand">
        <span class="aura-brand-name">Aura</span>
        <span class="aura-brand-sep">/</span>
        <span class="aura-brand-sub">RFID Attendance Intelligence</span>
      </div>
      <div class="aura-nav-right">
        <div class="{pill_cls}">
          <div class="live-dot"></div>{pill_text}
        </div>
        <span class="nav-ts">{ts} UTC</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats(total: int, unique: int, uptime: str):
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-icon">◉</div>
        <div class="stat-label">Total Scans Today</div>
        <div class="stat-value clr-accent">{total:,}</div>
        <div class="stat-note">RFID events logged</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⊙</div>
        <div class="stat-label">Students Present</div>
        <div class="stat-value clr-ok">{unique:,}</div>
        <div class="stat-note">Unique identities verified</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">◌</div>
        <div class="stat-label">System Uptime</div>
        <div class="stat-value" style="font-size:2rem;letter-spacing:-0.02em;">{uptime}</div>
        <div class="stat-note">hh : mm : ss continuous</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_log_feed(df: pd.DataFrame, max_rows: int = 50):
    if df.empty:
        st.markdown("""
        <div class="loading-state">
          <div class="loading-ring"></div>
          <div class="loading-txt">Awaiting RFID events</div>
        </div>""", unsafe_allow_html=True)
        return

    caps = ""
    for _, row in df.head(max_rows).iterrows():
        ts     = row["timestamp"]
        date_s = ts.strftime("%b %d") if hasattr(ts, "strftime") else ""
        time_s = ts.strftime("%H:%M:%S") if hasattr(ts, "strftime") else str(ts)
        ini    = initials(str(row["name"]))
        caps += f"""
        <div class="log-capsule">
          <div class="log-avatar">{ini}</div>
          <div class="log-body">
            <div class="log-name">{row['name']}</div>
            <div class="log-uid">{row['uid']}</div>
          </div>
          <div class="log-right">
            <span class="log-time">{date_s} · {time_s}</span>
            {pill_html(row['status'])}
          </div>
        </div>"""

    st.markdown(f'<div class="log-feed">{caps}</div>', unsafe_allow_html=True)


def render_chart(chart_data: list):
    max_v = max(v for _, v in chart_data) or 1
    now_h = datetime.utcnow().strftime("%H")
    bars  = ""
    for label, val in chart_data:
        pct = max(4, int((val / max_v) * 100))
        cls = "bar-fill active" if label == now_h else "bar-fill"
        bars += f"""
        <div class="bar-col">
          <div class="{cls}" style="height:{pct}%;"></div>
          <div class="bar-tick">{label}</div>
        </div>"""
    st.markdown(f'<div class="bar-chart-wrap">{bars}</div>', unsafe_allow_html=True)


def render_mini_list(df: pd.DataFrame, n: int = 6):
    if df.empty:
        return
    rows = ""
    for _, row in df.head(n).iterrows():
        ts = row["timestamp"]
        t  = ts.strftime("%H:%M") if hasattr(ts, "strftime") else "—"
        rows += f"""
        <div class="mini-row">
          <div class="mini-dot {dot_cls(row['status'])}"></div>
          <div class="mini-name">{row['name']}</div>
          <div class="mini-time">{t}</div>
        </div>"""
    st.markdown(f'<div class="mini-list">{rows}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────
if "start_time" not in st.session_state:
    st.session_state.start_time = datetime.utcnow()
if "max_rows" not in st.session_state:
    st.session_state.max_rows = 50


# ─────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────
def main():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

    # Firebase
    db_ref, firebase_error = init_firebase()
    is_live = db_ref is not None

    # Data
    df = fetch_logs_firebase(db_ref, limit=200) if is_live else fetch_logs_demo(n=60)

    refresh_ts = datetime.utcnow().strftime("%Y-%m-%d  %H:%M:%S")

    # Nav
    render_nav(is_live, refresh_ts)

    # Alert
    if firebase_error and not is_live:
        st.markdown(f"""
        <div class="alert-banner">
          <span class="alert-icon">○</span>
          Firebase unreachable — {firebase_error} — Displaying synthetic demo data
        </div>""", unsafe_allow_html=True)

    # Stats
    total, unique, uptime = compute_stats(df, st.session_state.start_time)
    render_stats(total, unique, uptime)

    # Body
    col_main, col_side = st.columns([5, 2], gap="large")

    with col_main:
        st.markdown(f"""
        <div class="sec-hdr">
          <span class="sec-label">Access Log</span>
          <span class="sec-count">{min(len(df), st.session_state.max_rows)} entries</span>
        </div>""", unsafe_allow_html=True)
        render_log_feed(df, max_rows=st.session_state.max_rows)

    with col_side:
        # Chart panel
        st.markdown('<div class="panel"><div class="sec-label">Hourly Activity</div>', unsafe_allow_html=True)
        render_chart(build_hourly(df))
        st.markdown('</div>', unsafe_allow_html=True)

        # Recent panel
        st.markdown('<div class="panel"><div class="sec-label">Recent Scans</div>', unsafe_allow_html=True)
        render_mini_list(df, n=6)
        st.markdown('</div>', unsafe_allow_html=True)

        # Controls panel
        st.markdown('<div class="panel"><div class="sec-label" style="margin-bottom:0.75rem;">Controls</div>', unsafe_allow_html=True)
        st.session_state.max_rows = st.selectbox(
            "Visible entries", [25, 50, 100, 200], index=1, key="row_select"
        )
        if st.button("↺  Refresh Now"):
            (fetch_logs_firebase if is_live else fetch_logs_demo).clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="aura-footer">
      <span class="footer-l">Aura · ESP32 RFID · Build 3.0.0</span>
      <span class="footer-r">Last sync: {refresh_ts} UTC</span>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh
    time.sleep(AUTO_REFRESH_SECONDS)
    st.rerun()


if __name__ == "__main__":
    main()
