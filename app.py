"""
⚽ WC26 // AGENT — World Cup 2026 AI Dashboard  (v2.0)
=====================================================
Live scores · Group standings · AI winner prediction · Next-match preview
· Polymarket crowd odds

v2: custom-themed HTML standings tables (no white st.dataframe),
real flag images via flagcdn.com (Windows-safe), tightened pro layout.

Data sources:
  - football-data.org (free tier, code WC) — fixtures, live scores, standings.
  - Polymarket Gamma API (public, no key) — market-implied win odds.
"""

import json
from datetime import datetime, timezone, timedelta

import requests
import streamlit as st

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="WC26 // AGENT — World Cup 2026 AI Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# Theme CSS
# ----------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(1100px 540px at 18% -8%, #0d2030 0%, #070b12 50%) fixed, #070b12;
    color: #d7e4f2;
    font-family: 'Rajdhani', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.6rem; max-width: 1250px; }

h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; letter-spacing: 1px; }

/* ---- hero ---- */
.hero {
    padding: 24px 30px; border-radius: 18px;
    background: linear-gradient(135deg, rgba(0,255,178,.07), rgba(0,170,255,.05));
    border: 1px solid rgba(0,255,178,.22);
    box-shadow: 0 0 36px rgba(0,255,178,.07);
    margin-bottom: 16px;
}
.hero h1 { margin: 0; font-size: 2rem;
    background: linear-gradient(90deg, #00ffb2, #00aaff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { margin: 6px 0 0; color: #8fa6bd; font-size: 1.02rem; }
.hero .byline {
    font-family: 'Orbitron'; font-size: .82rem; letter-spacing: 2.5px;
    color: #ffd84d; margin-top: 10px; text-transform: uppercase;
    text-shadow: 0 0 14px rgba(255,216,77,.35);
}

/* ---- stat strip ---- */
.stats { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.stat {
    flex: 1; min-width: 180px; padding: 14px 18px; border-radius: 14px;
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08);
}
.stat .lbl { color:#7d93ab; font-size:.78rem; letter-spacing:2.5px;
    text-transform:uppercase; font-family:'Orbitron'; }
.stat .val { font-family:'Orbitron'; font-size:1.5rem; color:#00ffb2;
    margin-top:4px; display:flex; align-items:center; gap:8px;}
.stat .sub { color:#7d93ab; font-size:.88rem; }

/* ---- cards & tags ---- */
.glass {
    background: rgba(255,255,255,.028); border: 1px solid rgba(255,255,255,.08);
    border-radius: 16px; padding: 20px 22px; margin-bottom: 14px;
}
.section-tag {
    display: inline-block; font-family: 'Orbitron'; font-size: .7rem;
    letter-spacing: 3px; color: #00ffb2; border: 1px solid rgba(0,255,178,.4);
    border-radius: 999px; padding: 3px 14px; margin: 4px 0 8px;
    text-transform: uppercase;
}
.sec-h { font-family:'Orbitron'; font-size:1.25rem; color:#e8f1fa;
    margin: 2px 0 12px; }

/* ---- flags ---- */
img.flag { width: 26px; height: 19px; border-radius: 3px; object-fit: cover;
    vertical-align: -4px; box-shadow: 0 0 6px rgba(0,0,0,.6);
    border: 1px solid rgba(255,255,255,.15); }
img.flag.sm { width: 21px; height: 15px; }
.noflag { display:inline-block; width:26px; text-align:center; }

/* ---- live pulse ---- */
.live-dot {
    display: inline-block; width: 9px; height: 9px; border-radius: 50%;
    background: #ff3b5c; margin-right: 7px;
    animation: pulse 1.6s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255,59,92,.7); }
    70% { box-shadow: 0 0 0 11px rgba(255,59,92,0); }
    100% { box-shadow: 0 0 0 0 rgba(255,59,92,0); }
}

/* ---- match cards ---- */
.match-card {
    display: grid; grid-template-columns: 1fr auto 1fr 150px;
    align-items: center; gap: 14px;
    background: rgba(10,18,30,.7); border: 1px solid rgba(0,170,255,.18);
    border-radius: 14px; padding: 13px 20px; margin-bottom: 9px;
}
.match-card:hover { border-color: rgba(0,255,178,.4); }
.mc-team { font-size: 1.12rem; font-weight: 700; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; }
.mc-team.home { text-align: right; }
.mc-score { font-family: 'Orbitron'; font-size: 1.35rem; color: #00ffb2;
    min-width: 92px; text-align: center; white-space: nowrap; }
.mc-meta { color: #7d93ab; font-size: .88rem; text-align: right;
    line-height: 1.35; }
.mc-meta .st-live { color:#ff6b87; font-weight:600; }

/* ---- odds rows ---- */
.odds-row { display: flex; align-items: center; margin: 8px 0;
    white-space: nowrap; }
.odds-rank { font-family: 'Orbitron'; min-width: 42px; flex-shrink: 0;
    color: #4f9fd8; font-size: .85rem; }
.odds-team { min-width: 168px; flex-shrink: 0; font-weight: 600;
    font-size: 1.02rem; overflow: hidden; text-overflow: ellipsis; }
.odds-bar-bg { flex: 1; height: 13px; background: rgba(255,255,255,.06);
    border-radius: 999px; overflow: hidden; margin: 0 12px; min-width: 60px; }
.odds-bar { height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #00ffb2, #00aaff);
    box-shadow: 0 0 10px rgba(0,255,178,.45); }
.odds-pct { min-width: 58px; flex-shrink: 0; font-family: 'Orbitron';
    color: #00ffb2; font-size: .92rem; text-align: right; }

/* ---- champion pick ---- */
.big-pick {
    text-align: center; padding: 22px 18px 18px; border-radius: 16px;
    background: linear-gradient(150deg, rgba(255,200,0,.08), rgba(0,255,178,.05));
    border: 1px solid rgba(255,200,0,.35); margin-bottom: 12px;
}
.big-pick .pre { color:#8fa6bd; letter-spacing:3px; font-size:.74rem;
    font-family:'Orbitron'; }
.big-pick .team { font-family: 'Orbitron'; font-size: 2rem; color: #ffd84d;
    text-shadow: 0 0 22px rgba(255,216,77,.4); margin: 8px 0 4px; }
.big-pick .team img.flag { width: 38px; height: 28px; vertical-align: -5px; }
.big-pick .conf { color: #8fa6bd; font-size: .95rem; }

.podium { display: flex; gap: 10px; }
.pod {
    flex: 1; text-align: center; padding: 13px 8px; border-radius: 13px;
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.09);
}
.pod .rk { font-family:'Orbitron'; font-size:.7rem; color:#4f9fd8;
    letter-spacing:2px; }
.pod .nm { font-weight: 700; font-size: 1rem; margin: 5px 0 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pod .pc { font-family: 'Orbitron'; color: #00ffb2; font-size: 1.1rem; }

.method { margin-top: 12px; }
.method .m-bar { display:flex; height:9px; border-radius:999px;
    overflow:hidden; margin:6px 0 4px; }
.method .m-odds { background:linear-gradient(90deg,#00aaff,#0077cc); width:60%; }
.method .m-form { background:linear-gradient(90deg,#00ffb2,#00cc8e); width:40%; }
.method .m-lbl { display:flex; justify-content:space-between;
    color:#7d93ab; font-size:.85rem; }

/* ---- standings tables ---- */
.wc-table { width: 100%; border-collapse: collapse; font-size: 1rem; }
.wc-table th {
    font-family: 'Orbitron'; font-size: .7rem; letter-spacing: 1.6px;
    color: #7d93ab; text-transform: uppercase; font-weight: 600;
    padding: 8px 10px; border-bottom: 1px solid rgba(255,255,255,.12);
    text-align: center;
}
.wc-table th.l, .wc-table td.l { text-align: left; }
.wc-table td {
    padding: 9px 10px; text-align: center; color: #c7d6e6;
    border-bottom: 1px solid rgba(255,255,255,.05);
}
.wc-table tr:last-child td { border-bottom: none; }
.wc-table tr.q1 td:first-child { box-shadow: inset 3px 0 0 #00ffb2; }
.wc-table tr.q3 td:first-child { box-shadow: inset 3px 0 0 #ffd84d; }
.wc-table tr:hover td { background: rgba(0,255,178,.04); }
.wc-table .pts { font-family:'Orbitron'; color:#00ffb2; font-weight:700; }
.wc-table .pos { color:#7d93ab; font-family:'Orbitron'; font-size:.85rem; }
.legend { color:#7d93ab; font-size:.85rem; margin-top:8px; }
.legend .g { color:#00ffb2; } .legend .y { color:#ffd84d; }

/* ---- tabs ---- */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Rajdhani'; font-weight: 700; font-size: 1rem;
    color: #7d93ab; background: rgba(255,255,255,.03);
    border-radius: 10px 10px 0 0; padding: 6px 16px;
    border: 1px solid rgba(255,255,255,.07); border-bottom: none;
}
.stTabs [aria-selected="true"] {
    color: #00ffb2 !important;
    background: rgba(0,255,178,.07) !important;
    border-color: rgba(0,255,178,.35) !important;
}
.stTabs [data-baseweb="tab-highlight"] { background-color: #00ffb2; }
.stTabs [data-baseweb="tab-border"] { background: rgba(255,255,255,.1); }

.kv { color:#8fa6bd; font-size:.92rem; }
.kv b { color:#e8f1fa; }
.foot { text-align:center; color:#51677e; margin-top:28px; font-size:.9rem; }

/* ---- responsive: tablet (iPad portrait & below) ---- */
.tbl-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.wc-table { min-width: 560px; }
@media (max-width: 1024px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .stat { min-width: 150px; }
}

/* ---- responsive: phones ---- */
@media (max-width: 740px) {
    .hero { padding: 18px 18px; }
    .hero h1 { font-size: 1.45rem; }
    .hero p { font-size: .92rem; }
    .hero .byline { font-size: .66rem; letter-spacing: 1.6px; }

    .stats { gap: 8px; }
    .stat { min-width: calc(50% - 8px); flex: 1 1 calc(50% - 8px);
        padding: 11px 13px; }
    .stat .val { font-size: 1.2rem; }

    .glass { padding: 14px 14px; }
    .sec-h { font-size: 1.05rem; }

    /* match card: teams+score on row 1, meta centered below */
    .match-card { grid-template-columns: 1fr auto 1fr; gap: 8px;
        padding: 11px 13px; }
    .mc-team { font-size: .98rem; }
    .mc-score { font-size: 1.15rem; min-width: 64px; }
    .mc-meta { grid-column: 1 / -1; text-align: center; font-size: .8rem;
        border-top: 1px solid rgba(255,255,255,.06); padding-top: 6px; }

    /* odds rows: tighter columns */
    .odds-rank { min-width: 30px; font-size: .75rem; }
    .odds-team { min-width: 116px; font-size: .92rem; }
    .odds-bar-bg { margin: 0 7px; min-width: 40px; }
    .odds-pct { min-width: 48px; font-size: .82rem; }

    .big-pick .team { font-size: 1.45rem; }
    .big-pick .team img.flag { width: 30px; height: 22px; }
    .podium { flex-wrap: wrap; }
    .pod { min-width: calc(33% - 10px); padding: 10px 5px; }
    .pod .nm { font-size: .85rem; }
    .pod .pc { font-size: .95rem; }

    img.flag { width: 22px; height: 16px; }
    img.flag.sm { width: 18px; height: 13px; }
}

@media (max-width: 420px) {
    .hero h1 { font-size: 1.25rem; }
    .stat .val { font-size: 1.05rem; }
    .mc-team { font-size: .88rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
FD_BASE = "https://api.football-data.org/v4"
WC_CODE = "WC"
GAMMA = "https://gamma-api.polymarket.com/events"
POLY_SLUG = "world-cup-winner"
FINAL_DATE = datetime(2026, 7, 19, tzinfo=timezone.utc)

# team name → ISO code for flagcdn.com (Windows-safe flag images)
ISO = {
    "argentina": "ar", "brazil": "br", "france": "fr", "spain": "es",
    "england": "gb-eng", "scotland": "gb-sct", "wales": "gb-wls",
    "portugal": "pt", "germany": "de", "netherlands": "nl", "italy": "it",
    "belgium": "be", "croatia": "hr", "switzerland": "ch", "austria": "at",
    "denmark": "dk", "norway": "no", "sweden": "se", "poland": "pl",
    "czechia": "cz", "czech republic": "cz", "slovakia": "sk",
    "slovenia": "si", "serbia": "rs", "türkiye": "tr", "turkey": "tr",
    "ukraine": "ua", "ireland": "ie", "republic of ireland": "ie",
    "hungary": "hu", "greece": "gr", "romania": "ro", "albania": "al",
    "north macedonia": "mk", "bosnia": "ba", "kosovo": "xk",
    "usa": "us", "united states": "us", "mexico": "mx", "canada": "ca",
    "panama": "pa", "costa rica": "cr", "honduras": "hn", "jamaica": "jm",
    "haiti": "ht", "curaçao": "cw", "curacao": "cw", "el salvador": "sv",
    "ecuador": "ec", "colombia": "co", "uruguay": "uy", "paraguay": "py",
    "peru": "pe", "chile": "cl", "venezuela": "ve", "bolivia": "bo",
    "japan": "jp", "south korea": "kr", "korea republic": "kr",
    "australia": "au", "iran": "ir", "saudi arabia": "sa", "qatar": "qa",
    "uzbekistan": "uz", "jordan": "jo", "iraq": "iq",
    "united arab emirates": "ae", "china": "cn", "indonesia": "id",
    "morocco": "ma", "senegal": "sn", "ghana": "gh", "nigeria": "ng",
    "egypt": "eg", "algeria": "dz", "tunisia": "tn", "ivory coast": "ci",
    "côte d'ivoire": "ci", "cameroon": "cm", "mali": "ml",
    "burkina faso": "bf", "cape verde": "cv", "cabo verde": "cv",
    "south africa": "za", "dr congo": "cd", "congo dr": "cd",
    "new zealand": "nz", "new caledonia": "nc",
}


def flag(team: str, sm: bool = False) -> str:
    """Return an <img> flag for a team name (flagcdn), or a neutral dot."""
    key = (team or "").lower().strip()
    iso = ISO.get(key)
    if iso is None:  # loose match: "Korea Republic" vs "South Korea" etc.
        for k, v in ISO.items():
            if k in key or key in k:
                iso = v
                break
    if iso is None:
        return '<span class="noflag">⚽</span>'
    cls = "flag sm" if sm else "flag"
    return f'<img class="{cls}" src="https://flagcdn.com/w40/{iso}.png" alt="">'


def get_api_key() -> str:
    try:
        return st.secrets.get("FOOTBALL_DATA_API_KEY", "")
    except Exception:
        return ""


# ----------------------------------------------------------------------------
# Data fetchers (cached)
# ----------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def fetch_matches(api_key: str) -> dict:
    if not api_key:
        return {}
    r = requests.get(f"{FD_BASE}/competitions/{WC_CODE}/matches",
                     headers={"X-Auth-Token": api_key}, timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_standings(api_key: str) -> dict:
    if not api_key:
        return {}
    r = requests.get(f"{FD_BASE}/competitions/{WC_CODE}/standings",
                     headers={"X-Auth-Token": api_key}, timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_polymarket() -> list:
    try:
        r = requests.get(GAMMA, params={"slug": POLY_SLUG}, timeout=15)
        r.raise_for_status()
        events = r.json()
        if not events:
            return []
        out = []
        for m in events[0].get("markets", []):
            team = m.get("groupItemTitle") or m.get("question", "")
            try:
                prices = json.loads(m.get("outcomePrices") or "[]")
                p = float(prices[0]) if prices else None
            except (ValueError, TypeError, IndexError):
                p = m.get("lastTradePrice")
                p = float(p) if p is not None else None
            if team and p is not None and p > 0.001:
                out.append((team, p))
        out.sort(key=lambda x: -x[1])
        return out
    except Exception:
        return []


FALLBACK_ODDS = [
    ("Spain", 0.16), ("France", 0.16), ("England", 0.10), ("Portugal", 0.09),
    ("Argentina", 0.09), ("Brazil", 0.08), ("Germany", 0.06),
    ("Netherlands", 0.04), ("Italy", 0.03), ("Belgium", 0.02),
]


# ----------------------------------------------------------------------------
# Prediction engine
# ----------------------------------------------------------------------------
def table_strength(standings: dict) -> dict:
    scores = {}
    for s in standings.get("standings", []):
        if s.get("type") != "TOTAL":
            continue
        for row in s.get("table", []):
            name = row["team"]["name"]
            played = max(row.get("playedGames", 0), 1)
            pts = row.get("points", 0) / (played * 3)
            gd = row.get("goalDifference", 0) / (played * 4)
            scores[name] = max(0.0, min(1.0, 0.7 * pts + 0.3 * (0.5 + gd / 2)))
    return scores


def blended_prediction(odds: list, strength: dict) -> list:
    if not odds:
        return []
    max_p = max(p for _, p in odds) or 1.0
    blended = []
    for team, p in odds[:15]:
        s = strength.get(team)
        if s is None:
            tl = team.lower()
            for k, v in strength.items():
                kl = k.lower()
                if tl in kl or kl in tl:
                    s = v
                    break
        score = 0.6 * (p / max_p) + 0.4 * (s if s is not None else p / max_p)
        blended.append((team, p, score))
    blended.sort(key=lambda x: -x[2])
    return blended


# ----------------------------------------------------------------------------
# UI sections
# ----------------------------------------------------------------------------
def section(tag: str, title: str, live: bool = False):
    dot = '<span class="live-dot"></span>' if live else ""
    st.markdown(f'<span class="section-tag">{dot}{tag}</span>'
                f'<div class="sec-h">{title}</div>', unsafe_allow_html=True)


def hero():
    now = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    st.markdown(
        f"""<div class="hero"><h1>⚽ WC26 // AGENT</h1>
        <p>Autonomous World Cup 2026 intelligence — live scores · standings ·
        AI winner projection · prediction-market odds &nbsp;|&nbsp;
        {flag('USA', True)} {flag('Mexico', True)} {flag('Canada', True)}
        United 2026 &nbsp;·&nbsp; last sync {now}</p>
        <div class="byline">★ David Lau World Cup Vision // WC26 AI Agent
        Supportive ★</div></div>""",
        unsafe_allow_html=True)


def stat_strip(live_n: int, today_n: int, fav: str, fav_p: float):
    days_left = max((FINAL_DATE - datetime.now(timezone.utc)).days, 0)
    live_html = (f'<span class="live-dot"></span>{live_n} match'
                 f'{"es" if live_n != 1 else ""}' if live_n
                 else '<span style="color:#7d93ab">none</span>')
    st.markdown(
        f"""<div class="stats">
        <div class="stat"><div class="lbl">Live now</div>
            <div class="val">{live_html}</div></div>
        <div class="stat"><div class="lbl">Matches today</div>
            <div class="val">{today_n}</div></div>
        <div class="stat"><div class="lbl">Market favourite</div>
            <div class="val" style="font-size:1.15rem">{flag(fav)} {fav}
            <span style="color:#4f9fd8;font-size:.95rem">{fav_p*100:.1f}%</span>
            </div></div>
        <div class="stat"><div class="lbl">Days to final</div>
            <div class="val">{days_left}<span style="font-size:.85rem;
            color:#7d93ab"> · 19 Jul, NY/NJ</span></div></div>
        </div>""", unsafe_allow_html=True)


def match_card(m: dict):
    home, away = m["homeTeam"]["name"], m["awayTeam"]["name"]
    status = m.get("status", "")
    ft = m.get("score", {}).get("fullTime", {})
    hs, as_ = ft.get("home"), ft.get("away")
    when = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
    stage = (m.get("group") or m.get("stage") or "").replace("_", " ").title()

    if status in ("IN_PLAY", "PAUSED"):
        score = f"{hs or 0} : {as_ or 0}"
        meta = ('<span class="st-live"><span class="live-dot"></span>LIVE'
                + (" · HT" if status == "PAUSED" else "") + "</span>")
    elif status == "FINISHED":
        score, meta = f"{hs} : {as_}", "FULL TIME"
    else:
        score = "—"
        meta = when.strftime("%a %d %b · %H:%M UTC")

    st.markdown(
        f"""<div class="match-card">
        <div class="mc-team home">{home} {flag(home)}</div>
        <div class="mc-score">{score}</div>
        <div class="mc-team">{flag(away)} {away}</div>
        <div class="mc-meta">{meta}<br>{stage}</div></div>""",
        unsafe_allow_html=True)


def prediction_panel(blend: list):
    section("AI PROJECTION", "🤖 Agent's champion pick")
    if not blend:
        st.info("Prediction engine warming up — needs odds or standings data.")
        return
    top = blend[0]
    conf = top[2] / sum(b[2] for b in blend[:5]) * 100
    pods = ""
    for i, (team, p, _s) in enumerate(blend[1:4], 2):
        pods += (f'<div class="pod"><div class="rk">#{i}</div>'
                 f'<div class="nm">{flag(team, True)} {team}</div>'
                 f'<div class="pc">{p*100:.1f}%</div></div>')
    st.markdown(
        f"""<div class="glass">
        <div class="big-pick"><div class="pre">PROJECTED WORLD CHAMPION</div>
            <div class="team">{flag(top[0])} {top[0].upper()} 🏆</div>
            <div class="conf">agent confidence {conf:.0f}% vs next contenders</div>
        </div>
        <div class="podium">{pods}</div>
        <div class="method">
            <div class="m-lbl"><span>Model blend</span><span></span></div>
            <div class="m-bar"><div class="m-odds"></div><div class="m-form"></div></div>
            <div class="m-lbl"><span>📈 market odds 60%</span>
            <span>⚽ live table form 40%</span></div>
        </div></div>""", unsafe_allow_html=True)


def odds_panel(odds: list, source_live: bool):
    tag = "POLYMARKET · LIVE" if source_live else "POLYMARKET · SNAPSHOT"
    section(tag, "💸 Who the betting crowd backs")
    top = odds[:10]
    max_p = top[0][1] if top else 1
    rows = ""
    for i, (team, p) in enumerate(top, 1):
        rows += (f'<div class="odds-row"><div class="odds-rank">#{i:02d}</div>'
                 f'<div class="odds-team">{flag(team, True)} {team}</div>'
                 f'<div class="odds-bar-bg"><div class="odds-bar" '
                 f'style="width:{p/max_p*100:.1f}%"></div></div>'
                 f'<div class="odds-pct">{p*100:.1f}%</div></div>')
    st.markdown(f'<div class="glass">{rows}</div>', unsafe_allow_html=True)
    st.caption("Implied win probability from Polymarket's World Cup Winner "
               "market. Informational only — not betting advice.")


def next_match_panel(upcoming: list, odds_map: dict):
    section("NEXT UP", "🔮 Coming matches — what to expect")
    if not upcoming:
        st.info("No scheduled matches found — add your API key to load fixtures.")
        return
    nxt = upcoming[0]
    home, away = nxt["homeTeam"]["name"], nxt["awayTeam"]["name"]

    def title_odds(team):
        if team in odds_map:
            return odds_map[team]
        tl = team.lower()
        for k, v in odds_map.items():
            if tl in k.lower() or k.lower() in tl:
                return v
        return 0.005

    ph, pa = title_odds(home), title_odds(away)
    fav, dog = (home, away) if ph >= pa else (away, home)
    edge = abs(ph - pa)
    if edge > 0.05:
        expect = (f"<b>{fav}</b> goes in as clear favourite — the market gives "
                  f"them a far stronger title path. Expect {fav} to dictate "
                  f"tempo; {dog}'s route is transition play and set pieces.")
    elif edge > 0.015:
        expect = (f"<b>{fav}</b> is slightly fancied, but this is closer than "
                  f"it looks — one moment of quality could decide it.")
    else:
        expect = ("Coin-flip territory — the market can't split these sides. "
                  "Expect a cagey opening half and fine margins.")
    when = datetime.fromisoformat(nxt["utcDate"].replace("Z", "+00:00"))
    stage = (nxt.get("group") or nxt.get("stage", "")).replace("_", " ").title()
    st.markdown(
        f"""<div class="glass">
        <div style="font-size:1.45rem;font-weight:700;">
            {flag(home)} {home} &nbsp;<span style="color:#4f9fd8">vs</span>&nbsp;
            {away} {flag(away)}</div>
        <div class="kv" style="margin-top:4px;">🗓
            <b>{when.strftime('%A %d %B %Y · %H:%M UTC')}</b> · {stage}</div>
        <p style="margin:10px 0 8px;font-size:1.05rem;">{expect}</p>
        <div class="kv">Title odds — {home}: <b>{ph*100:.1f}%</b> · {away}:
            <b>{pa*100:.1f}%</b> (Polymarket)</div></div>""",
        unsafe_allow_html=True)
    for m in upcoming[1:6]:
        match_card(m)


def standings_table_html(table: list) -> str:
    rows = ""
    for r in table:
        name = r["team"]["name"]
        pos = r["position"]
        cls = "q1" if pos <= 2 else ("q3" if pos == 3 else "")
        rows += (f'<tr class="{cls}"><td class="pos">{pos}</td>'
                 f'<td class="l">{flag(name, True)}&nbsp; {name}</td>'
                 f'<td>{r["playedGames"]}</td><td>{r["won"]}</td>'
                 f'<td>{r["draw"]}</td><td>{r["lost"]}</td>'
                 f'<td>{r["goalsFor"]}</td><td>{r["goalsAgainst"]}</td>'
                 f'<td>{r["goalDifference"]:+d}</td>'
                 f'<td class="pts">{r["points"]}</td></tr>')
    return (f'<div class="glass tbl-scroll" style="padding:10px 14px;">'
            f'<table class="wc-table"><thead><tr>'
            f'<th>#</th><th class="l">Team</th><th>P</th><th>W</th><th>D</th>'
            f'<th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')


def standings_panel(standings: dict):
    section("GROUP STAGE", "📊 Standings — all 12 groups")
    tables = [s for s in standings.get("standings", [])
              if s.get("type") == "TOTAL"]
    if not tables:
        st.info("Standings appear once your API key is set and group games "
                "kick off (11 June 2026 🇲🇽).")
        return
    tabs = st.tabs([s.get("group", f"G{i}").replace("GROUP_", "Group ")
                    for i, s in enumerate(tables)])
    for tab, s in zip(tabs, tables):
        with tab:
            st.markdown(standings_table_html(s.get("table", [])),
                        unsafe_allow_html=True)
    st.markdown(
        '<div class="legend"><span class="g">▎</span> top 2 — advance to '
        'round of 32 &nbsp;&nbsp; <span class="y">▎</span> 3rd — may advance '
        'among 8 best third-placed teams</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Main — auto-refreshing fragment
# ----------------------------------------------------------------------------
@st.fragment(run_every=timedelta(seconds=60))
def dashboard():
    api_key = get_api_key()

    odds = fetch_polymarket()
    odds_live = bool(odds)
    if not odds:
        odds = FALLBACK_ODDS
    odds_map = dict(odds)

    matches, standings, api_err = {}, {}, None
    if api_key:
        try:
            matches = fetch_matches(api_key)
            standings = fetch_standings(api_key)
        except Exception as e:  # noqa: BLE001
            api_err = str(e)

    all_matches = matches.get("matches", [])
    live = [m for m in all_matches if m.get("status") in ("IN_PLAY", "PAUSED")]
    today = datetime.now(timezone.utc).date()
    today_n = sum(1 for m in all_matches
                  if m.get("utcDate", "")[:10] == today.isoformat())
    upcoming = sorted((m for m in all_matches
                       if m.get("status") in ("TIMED", "SCHEDULED")),
                      key=lambda m: m["utcDate"])
    finished = sorted((m for m in all_matches if m.get("status") == "FINISHED"),
                      key=lambda m: m["utcDate"], reverse=True)

    stat_strip(len(live), today_n, odds[0][0], odds[0][1])

    if not api_key:
        st.warning("🔑 **No football-data.org API key found.** Live scores, "
                   "fixtures and standings are disabled. Get a free key at "
                   "https://www.football-data.org/client/register and add "
                   "`FOOTBALL_DATA_API_KEY` to Streamlit secrets.", icon="⚠️")
    elif api_err:
        st.error(f"football-data.org error: {api_err}")

    if live:
        section("LIVE NOW", "🔴 Matches in play", live=True)
        for m in live:
            match_card(m)
        st.caption("Auto-refreshes every 60 s. Free-tier scores can lag "
                   "broadcast slightly.")

    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        prediction_panel(blended_prediction(odds, table_strength(standings)))
    with c2:
        odds_panel(odds, odds_live)

    next_match_panel(upcoming, odds_map)
    standings_panel(standings)

    if finished:
        section("RESULTS", "✅ Latest results")
        for m in finished[:6]:
            match_card(m)

    st.markdown(
        '<p class="foot">WC26 // AGENT · data: football-data.org + Polymarket '
        '· flags: flagcdn.com · predictions are statistical projections, not '
        'betting advice · built with Streamlit 🤖</p>',
        unsafe_allow_html=True)


hero()
dashboard()
