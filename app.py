"""
  VOID — RFID Attendance Intelligence  ✦ Space Edition ✦
  ─────────────────────────────────────────────────────────
  Stack  : Python · Firebase RTDB · firebase-admin · Streamlit
  Theme  : Deep Space — Void black, nebula violet, stellar gold
  Build  : 3.4.0 — Space Edition
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
    page_title="Void — Space Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  /* ── Deep Space / Nebula Palette ── */
  --bg-base:            #03020a;
  --bg-elevated:        #07051a;
  --bg-card:            rgba(120, 80, 220, 0.07);
  --bg-card-hover:      rgba(140, 100, 240, 0.12);
  --bg-input:           rgba(120, 80, 220, 0.09);

  --border-subtle:      rgba(160, 100, 255, 0.08);
  --border-moderate:    rgba(160, 100, 255, 0.16);
  --border-strong:      rgba(180, 120, 255, 0.38);

  --text-primary:       #e8e0ff;
  --text-secondary:     #6050a0;
  --text-tertiary:      #302848;

  --accent:             #b06aff;
  --accent-dim:         rgba(176,106,255,0.12);
  --accent-glow:        0 0 24px rgba(176,106,255,0.18), 0 0 60px rgba(100,50,200,0.08);

  /* Stellar gold for ok status — stars */
  --status-ok:          #ffd166;
  --status-ok-dim:      rgba(255,209,102,0.09);
  --status-denied:      #ff4560;
  --status-denied-dim:  rgba(255,69,96,0.09);
  --status-unknown:     #3a2860;
  --status-unknown-dim: rgba(58,40,96,0.20);

  --radius-sm:10px; --radius-md:14px; --radius-lg:18px; --radius-xl:24px;
  --ease:cubic-bezier(0.25,0.46,0.45,0.94);
  --ease-warp:cubic-bezier(0.16,1,0.3,1);
  --dur-fast:140ms; --dur-base:280ms; --dur-slow:520ms;
  --font:'Inter',-apple-system,'Helvetica Neue',sans-serif;
}

*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main,.block-container{
  background:var(--bg-base) !important; color:var(--text-primary) !important;
  font-family:var(--font) !important; -webkit-font-smoothing:antialiased;
}

/* Nebula cosmic background — layered radial gradients */
[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(ellipse 60% 40% at 75% 15%, rgba(120,40,200,0.12) 0%, transparent 60%),
    radial-gradient(ellipse 50% 35% at 20% 75%, rgba(60,20,140,0.10) 0%, transparent 55%),
    radial-gradient(ellipse 80% 60% at 50% 50%, rgba(40,10,80,0.08) 0%, transparent 70%),
    #03020a !important;
}

.block-container{padding:2rem 2.5rem 3rem !important; max-width:1440px !important;}
#MainMenu,footer,header{visibility:hidden !important;}
[data-testid="stToolbar"],[data-testid="stSidebar"],section[data-testid="stSidebar"],
.stDeployButton,[data-testid="collapsedControl"]{display:none !important;}
::-webkit-scrollbar{width:3px;} ::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(176,106,255,0.20);border-radius:99px;}
[data-testid="stHorizontalBlock"]{gap:1.5rem !important;}

/* ── Keyframes ── */
@keyframes fade-up     {from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
@keyframes fade-in     {from{opacity:0;}to{opacity:1;}}
@keyframes spin        {to{transform:rotate(360deg);}}
@keyframes bar-rise    {from{transform:scaleY(0);}to{transform:scaleY(1);}}

/* Pulsar — rhythmic like a spinning neutron star */
@keyframes pulsar {
  0%   {box-shadow:0 0 0 0 rgba(176,106,255,0.7);}
  50%  {box-shadow:0 0 0 6px rgba(176,106,255,0.1);}
  100% {box-shadow:0 0 0 10px rgba(176,106,255,0);}
}

/* Stellar rotation on brand icon */
@keyframes stellar-spin {
  from{transform:rotate(0deg);}
  to{transform:rotate(360deg);}
}

/* Warp-speed reveal — entries slide in fast */
@keyframes warp-in {
  from{opacity:0; transform:translateY(8px) scale(0.97);}
  to{opacity:1; transform:translateY(0) scale(1);}
}

/* Nebula shimmer on brand name */
@keyframes nebula {
  0%,100%{color:#b06aff;}
  33%{color:#d090ff;}
  66%{color:#8840e0;}
}

/* Twinkling star field in background (pseudo-star dots via text-shadow) */
@keyframes twinkle {
  0%,100%{opacity:0.3;} 50%{opacity:1;}
}

/* ── NAV ── */
.aura-nav{display:flex;align-items:center;justify-content:space-between;padding-bottom:1.8rem;border-bottom:0.5px solid var(--border-subtle);margin-bottom:2.5rem;animation:fade-in var(--dur-slow) var(--ease) both;}
.aura-brand{display:flex;align-items:baseline;gap:0.8rem;}
.brand-star{font-size:0.9rem;animation:stellar-spin 8s linear infinite;display:inline-block;}
.aura-brand-name{font-size:1.1rem;font-weight:600;letter-spacing:0.14em;text-transform:uppercase;animation:nebula 8s ease-in-out infinite;}
.aura-brand-sep{color:var(--border-moderate);font-weight:300;font-size:1rem;}
.aura-brand-sub{font-size:0.73rem;color:var(--text-tertiary);letter-spacing:0.05em;}
.aura-nav-right{display:flex;align-items:center;gap:1.4rem;}
.live-pill{display:flex;align-items:center;gap:0.45rem;background:var(--status-ok-dim);border:0.5px solid rgba(255,209,102,0.22);border-radius:99px;padding:0.28rem 0.75rem;font-size:0.68rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:var(--status-ok);}
.live-pill.offline{background:var(--status-unknown-dim);border-color:rgba(58,40,96,0.3);color:var(--text-secondary);}
.live-dot{width:5px;height:5px;border-radius:50%;background:var(--accent);animation:pulsar 2.4s ease-out infinite;}
.live-pill.offline .live-dot{background:var(--status-unknown);animation:none;}
.nav-ts{font-size:0.7rem;color:var(--text-tertiary);font-variant-numeric:tabular-nums;}

/* ── STAT CARDS ── */
.stat-row{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:2.5rem;}
.stat-card{background:var(--bg-card);border:0.5px solid var(--border-subtle);border-radius:var(--radius-xl);padding:1.6rem 1.5rem 1.3rem;backdrop-filter:blur(30px) saturate(200%);-webkit-backdrop-filter:blur(30px) saturate(200%);position:relative;overflow:hidden;cursor:default;transition:background var(--dur-base) var(--ease),transform var(--dur-base) var(--ease-warp),border-color var(--dur-base) var(--ease);animation:fade-up var(--dur-slow) var(--ease) both;}
.stat-card:nth-child(1){animation-delay:0.05s;} .stat-card:nth-child(2){animation-delay:0.10s;} .stat-card:nth-child(3){animation-delay:0.15s;}
.stat-card:hover{background:var(--bg-card-hover);border-color:var(--border-moderate);transform:translateY(-3px);box-shadow:var(--accent-glow);}
/* event horizon highlight line */
.stat-card::before{content:'';position:absolute;top:0;left:8%;right:8%;height:0.5px;background:linear-gradient(90deg,transparent,rgba(176,106,255,0.45) 30%,rgba(220,160,255,0.45) 70%,transparent);}
/* subtle nebula glow at corner */
.stat-card::after{content:'';position:absolute;bottom:-20px;right:-20px;width:80px;height:80px;border-radius:50%;background:radial-gradient(circle,rgba(120,60,200,0.08) 0%,transparent 70%);}
.stat-icon{font-size:1rem;margin-bottom:0.9rem;opacity:0.5;}
.stat-label{font-size:0.66rem;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;color:var(--text-secondary);margin-bottom:0.5rem;}
.stat-value{font-size:2.8rem;font-weight:700;letter-spacing:-0.03em;line-height:1;font-variant-numeric:tabular-nums;}
.stat-value.clr-accent{color:var(--accent);}
.stat-value.clr-ok{color:var(--status-ok);}
.stat-note{margin-top:0.55rem;font-size:0.66rem;color:var(--text-tertiary);}

.sec-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:0.9rem;}
.sec-label{font-size:0.68rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--text-secondary);}
.sec-count{font-size:0.66rem;color:var(--text-tertiary);font-variant-numeric:tabular-nums;}

/* ── LOG FEED — warp speed reveal ── */
.log-feed{display:flex;flex-direction:column;gap:0.45rem;}
.log-capsule{display:flex;align-items:center;gap:0.9rem;background:var(--bg-card);border:0.5px solid var(--border-subtle);border-radius:var(--radius-lg);padding:0.85rem 1rem;backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);transition:background var(--dur-fast) var(--ease),border-color var(--dur-fast) var(--ease);animation:warp-in var(--dur-base) var(--ease-warp) both;position:relative;overflow:hidden;}
.log-capsule::before{content:'';position:absolute;top:0;left:0;right:0;height:0.5px;background:linear-gradient(90deg,transparent,rgba(176,106,255,0.16),transparent);}
.log-capsule:hover{background:var(--bg-card-hover);border-color:var(--border-moderate);}
.log-capsule:nth-child(1){animation-delay:0.03s;} .log-capsule:nth-child(2){animation-delay:0.07s;}
.log-capsule:nth-child(3){animation-delay:0.11s;} .log-capsule:nth-child(4){animation-delay:0.15s;}
.log-capsule:nth-child(5){animation-delay:0.19s;} .log-capsule:nth-child(n+6){animation-delay:0.22s;}
.log-avatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:600;flex-shrink:0;background:rgba(176,106,255,0.10);border:0.5px solid rgba(176,106,255,0.22);color:var(--accent);}
.log-body{flex:1;min-width:0;}
.log-name{font-size:0.85rem;font-weight:500;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.log-uid{font-size:0.65rem;color:var(--text-tertiary);font-variant-numeric:tabular-nums;margin-top:0.15rem;}
.log-right{display:flex;flex-direction:column;align-items:flex-end;gap:0.3rem;flex-shrink:0;}
.log-time{font-size:0.65rem;color:var(--text-tertiary);font-variant-numeric:tabular-nums;}
.pill{display:inline-flex;align-items:center;gap:0.28rem;padding:0.18rem 0.55rem;border-radius:99px;font-size:0.6rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;}
.pill::before{content:'';width:4px;height:4px;border-radius:50%;}
.pill-ok{background:var(--status-ok-dim);color:var(--status-ok);border:0.5px solid rgba(255,209,102,0.28);}
.pill-ok::before{background:var(--status-ok);}
.pill-denied{background:var(--status-denied-dim);color:var(--status-denied);border:0.5px solid rgba(255,69,96,0.28);}
.pill-denied::before{background:var(--status-denied);}
.pill-unknown{background:var(--status-unknown-dim);color:#6050a0;border:0.5px solid rgba(58,40,96,0.4);}
.pill-unknown::before{background:#3a2860;}

.loading-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:4rem 2rem;gap:1rem;}
.loading-ring{width:26px;height:26px;border:1.5px solid var(--border-subtle);border-top-color:var(--accent);border-radius:50%;animation:spin 1.2s linear infinite;}
.loading-txt{font-size:0.75rem;color:var(--text-tertiary);letter-spacing:0.06em;}

.panel{background:var(--bg-card);border:0.5px solid var(--border-subtle);border-radius:var(--radius-xl);padding:1.3rem 1.2rem;backdrop-filter:blur(30px) saturate(200%);-webkit-backdrop-filter:blur(30px) saturate(200%);margin-bottom:1rem;position:relative;overflow:hidden;animation:fade-up var(--dur-slow) var(--ease) 0.12s both;}
.panel::before{content:'';position:absolute;top:0;left:12%;right:12%;height:0.5px;background:linear-gradient(90deg,transparent,rgba(176,106,255,0.28) 40%,rgba(220,160,255,0.28) 60%,transparent);}

.bar-chart-wrap{display:flex;align-items:flex-end;gap:4px;height:68px;margin-top:0.9rem;padding-bottom:4px;}
.bar-col{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;}
.bar-fill{width:100%;border-radius:3px 3px 0 0;background:rgba(176,106,255,0.12);transform-origin:bottom;animation:bar-rise var(--dur-slow) var(--ease) both;min-height:3px;}
.bar-fill.active{background:var(--accent);opacity:0.75;}
.bar-tick{font-size:0.5rem;color:var(--text-tertiary);font-variant-numeric:tabular-nums;}

.mini-list{display:flex;flex-direction:column;margin-top:0.75rem;}
.mini-row{display:flex;align-items:center;gap:0.65rem;padding:0.45rem 0;border-bottom:0.5px solid var(--border-subtle);}
.mini-row:last-child{border-bottom:none;}
.mini-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0;}
.mini-dot.ok{background:var(--status-ok);} .mini-dot.denied{background:var(--status-denied);} .mini-dot.unknown{background:#3a2860;}
.mini-name{flex:1;font-size:0.77rem;font-weight:500;color:var(--text-primary);}
.mini-time{font-size:0.63rem;color:var(--text-tertiary);font-variant-numeric:tabular-nums;}

.alert-banner{display:flex;align-items:center;gap:0.7rem;background:rgba(176,106,255,0.04);border:0.5px solid var(--border-subtle);border-radius:var(--radius-md);padding:0.65rem 1rem;margin-bottom:2rem;font-size:0.71rem;color:var(--text-secondary);animation:fade-up var(--dur-base) var(--ease) both;}

div[data-testid="stSelectbox"] label{font-family:var(--font) !important;font-size:0.66rem !important;font-weight:500 !important;letter-spacing:0.1em !important;text-transform:uppercase !important;color:var(--text-secondary) !important;}
div[data-testid="stSelectbox"] > div > div{background:var(--bg-input) !important;border:0.5px solid var(--border-moderate) !important;border-radius:var(--radius-sm) !important;color:var(--text-primary) !important;font-family:var(--font) !important;font-size:0.82rem !important;}
div[data-testid="stButton"] > button{width:100% !important;background:rgba(176,106,255,0.06) !important;border:0.5px solid var(--border-moderate) !important;color:var(--accent) !important;font-family:var(--font) !important;font-size:0.77rem !important;font-weight:500 !important;letter-spacing:0.06em !important;border-radius:var(--radius-sm) !important;padding:0.58rem 1rem !important;margin-top:0.5rem !important;transition:background var(--dur-fast) var(--ease),border-color var(--dur-fast) var(--ease) !important;}
div[data-testid="stButton"] > button:hover{background:rgba(176,106,255,0.12) !important;border-color:var(--border-strong) !important;}
div[data-testid="stButton"] > button:active{transform:scale(0.98) !important;}

.aura-footer{margin-top:3rem;padding-top:1.2rem;border-top:0.5px solid var(--border-subtle);display:flex;justify-content:space-between;align-items:center;}
.footer-l,.footer-r{font-size:0.63rem;color:var(--text-tertiary);letter-spacing:0.05em;}
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

def compute_stats(df,start_time):
    if df.empty: return 0,0,"00:00:00"
    today=datetime.utcnow().date(); ts=df["timestamp"]
    if pd.api.types.is_datetime64_any_dtype(ts):
        try: ts_n=ts.dt.tz_convert(None)
        except: ts_n=ts
        mask=ts_n.dt.date==today
    else: mask=pd.Series([True]*len(df))
    t=df[mask]; up=int((datetime.utcnow()-start_time).total_seconds())
    h,r=divmod(up,3600); m,s=divmod(r,60)
    return len(t),t["name"].nunique(),f"{h:02d}:{m:02d}:{s:02d}"

def build_hourly(df):
    now=datetime.utcnow(); labels=[(now-timedelta(hours=11-i)).strftime("%H") for i in range(12)]; slots=[0]*12
    if df.empty: return list(zip(labels,slots))
    ts=df["timestamp"]
    if not pd.api.types.is_datetime64_any_dtype(ts): return list(zip(labels,slots))
    try: ts=ts.dt.tz_convert(None)
    except: pass
    for i in range(12):
        s0=(now-timedelta(hours=11-i)).replace(minute=0,second=0,microsecond=0); s1=s0+timedelta(hours=1)
        slots[i]=int(((ts>=s0)&(ts<s1)).sum())
    return list(zip(labels,slots))

def pill_html(status):
    s=str(status).upper()
    if s in("ACCESS","GRANTED","OK"): return '<span class="pill pill-ok">Access</span>'
    if s in("DENIED","REJECTED"):     return '<span class="pill pill-denied">Denied</span>'
    return f'<span class="pill pill-unknown">{s.title()}</span>'

def dot_cls(status):
    s=str(status).upper()
    if s in("ACCESS","GRANTED","OK"): return "ok"
    if s in("DENIED","REJECTED"):     return "denied"
    return "unknown"

def initials(name):
    p=name.strip().split()
    return (p[0][0]+p[-1][0]).upper() if len(p)>=2 else name[:2].upper()

def render_nav(is_live,ts):
    pc="live-pill" if is_live else "live-pill offline"; pt="Live" if is_live else "Demo"
    st.markdown(f'<div class="aura-nav"><div class="aura-brand"><span class="brand-star">✦</span><span class="aura-brand-name">Void</span><span class="aura-brand-sep">/</span><span class="aura-brand-sub">RFID Attendance Intelligence · Space Edition</span></div><div class="aura-nav-right"><div class="{pc}"><div class="live-dot"></div>{pt}</div><span class="nav-ts">{ts} UTC</span></div></div>',unsafe_allow_html=True)

def render_stats(total,unique,uptime):
    st.markdown(f'<div class="stat-row"><div class="stat-card"><div class="stat-icon">✦</div><div class="stat-label">Total Scans Today</div><div class="stat-value clr-accent">{total:,}</div><div class="stat-note">RFID events logged</div></div><div class="stat-card"><div class="stat-icon">◎</div><div class="stat-label">Students Present</div><div class="stat-value clr-ok">{unique:,}</div><div class="stat-note">Unique identities verified</div></div><div class="stat-card"><div class="stat-icon">⊛</div><div class="stat-label">System Uptime</div><div class="stat-value" style="font-size:2rem;letter-spacing:-0.02em;">{uptime}</div><div class="stat-note">hh : mm : ss continuous</div></div></div>',unsafe_allow_html=True)

def render_log_feed(df,max_rows=50):
    if df.empty:
        st.markdown('<div class="loading-state"><div class="loading-ring"></div><div class="loading-txt">Awaiting RFID events</div></div>',unsafe_allow_html=True); return
    caps=""
    for _,row in df.head(max_rows).iterrows():
        ts=row["timestamp"]; d=ts.strftime("%b %d") if hasattr(ts,"strftime") else ""; t=ts.strftime("%H:%M:%S") if hasattr(ts,"strftime") else str(ts)
        caps+=f'<div class="log-capsule"><div class="log-avatar">{initials(str(row["name"]))}</div><div class="log-body"><div class="log-name">{row["name"]}</div><div class="log-uid">{row["uid"]}</div></div><div class="log-right"><span class="log-time">{d} · {t}</span>{pill_html(row["status"])}</div></div>'
    st.markdown(f'<div class="log-feed">{caps}</div>',unsafe_allow_html=True)

def render_chart(chart_data):
    max_v=max(v for _,v in chart_data) or 1; now_h=datetime.utcnow().strftime("%H"); bars=""
    for label,val in chart_data:
        pct=max(4,int((val/max_v)*100)); cls="bar-fill active" if label==now_h else "bar-fill"
        bars+=f'<div class="bar-col"><div class="{cls}" style="height:{pct}%;"></div><div class="bar-tick">{label}</div></div>'
    st.markdown(f'<div class="bar-chart-wrap">{bars}</div>',unsafe_allow_html=True)

def render_mini_list(df,n=6):
    if df.empty: return
    rows=""
    for _,row in df.head(n).iterrows():
        ts=row["timestamp"]; t=ts.strftime("%H:%M") if hasattr(ts,"strftime") else "—"
        rows+=f'<div class="mini-row"><div class="mini-dot {dot_cls(row["status"])}"></div><div class="mini-name">{row["name"]}</div><div class="mini-time">{t}</div></div>'
    st.markdown(f'<div class="mini-list">{rows}</div>',unsafe_allow_html=True)

if "start_time" not in st.session_state: st.session_state.start_time=datetime.utcnow()
if "max_rows"   not in st.session_state: st.session_state.max_rows=50

def main():
    st.markdown(THEME_CSS,unsafe_allow_html=True)
    db_ref,firebase_error=init_firebase(); is_live=db_ref is not None
    df=fetch_logs_firebase(db_ref,limit=200) if is_live else fetch_logs_demo(n=60)
    refresh_ts=datetime.utcnow().strftime("%Y-%m-%d  %H:%M:%S")
    render_nav(is_live,refresh_ts)
    if firebase_error and not is_live:
        st.markdown(f'<div class="alert-banner"><span>✦</span> Firebase unreachable — {firebase_error} — Demo data active</div>',unsafe_allow_html=True)
    total,unique,uptime=compute_stats(df,st.session_state.start_time); render_stats(total,unique,uptime)
    col_main,col_side=st.columns([5,2],gap="large")
    with col_main:
        st.markdown(f'<div class="sec-hdr"><span class="sec-label">Access Log</span><span class="sec-count">{min(len(df),st.session_state.max_rows)} entries</span></div>',unsafe_allow_html=True)
        render_log_feed(df,max_rows=st.session_state.max_rows)
    with col_side:
        st.markdown('<div class="panel"><div class="sec-label">Hourly Activity</div>',unsafe_allow_html=True)
        render_chart(build_hourly(df)); st.markdown('</div>',unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="sec-label">Recent Scans</div>',unsafe_allow_html=True)
        render_mini_list(df,n=6); st.markdown('</div>',unsafe_allow_html=True)
        st.markdown('<div class="panel"><div class="sec-label" style="margin-bottom:0.75rem;">Controls</div>',unsafe_allow_html=True)
        st.session_state.max_rows=st.selectbox("Visible entries",[25,50,100,200],index=1,key="row_select")
        if st.button("↺  Refresh Now"): (fetch_logs_firebase if is_live else fetch_logs_demo).clear(); st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="aura-footer"><span class="footer-l">Void · Space Edition · Build 3.4.0</span><span class="footer-r">Last sync: {refresh_ts} UTC</span></div>',unsafe_allow_html=True)
    time.sleep(AUTO_REFRESH_SECONDS); st.rerun()

if __name__ == "__main__": main()
