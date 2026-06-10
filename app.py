"""
⚽ WC26 // AGENT — World Cup 2026 AI Dashboard
================================================
Live scores · Group standings · AI winner prediction · Next-match preview
· Polymarket crowd odds

Data sources:
  - football-data.org (free tier, competition code WC) — fixtures, live
    scores, standings. Requires a free API key in Streamlit secrets.
  - Polymarket Gamma API (public, no key) — market-implied win odds.

Deploy: push to GitHub → share.streamlit.io → add FOOTBALL_DATA_API_KEY
to app secrets.
"""

import json
from datetime import datetime, timezone, timedelta

import pandas as pd
import requests
import streamlit as st

# ----------------------------------------------------------------------------
# Page config + theme
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="WC26 // AGENT — World Cup 2026 AI Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 600px at 20% -10%, #0e2233 0%, #070b12 45%) fixed,
                #070b12;
    color: #d7e4f2;
    font-family: 'Rajdhani', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; letter-spacing: 1px; }

.hero {
    padding: 26px 30px;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(0,255,178,.08), rgba(0,170,255,.06));
    border: 1px solid rgba(0,255,178,.25);
    box-shadow: 0 0 40px rgba(0,255,178,.08), inset 0 0 60px rgba(0,170,255,.05);
    margin-bottom: 6px;
}
.hero h1 {
    margin: 0;
    font-size: 2.1rem;
    background: linear-gradient(90deg, #00ffb2, #00aaff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero p { margin: 6px 0 0; color: #8fa6bd; font-size: 1.05rem; }

.glass {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 16px;
    padding: 18px 20px;
    backdrop-filter: blur(8px);
    margin-bottom: 14px;
}
.glass:hover { border-color: rgba(0,255,178,.35); transition: border-color .3s; }

.section-tag {
    display: inline-block;
    font-family: 'Orbitron', sans-serif;
    font-size: .72rem;
    letter-spacing: 3px;
    color: #00ffb2;
    border: 1px solid rgba(0,255,178,.4);
    border-radius: 999px;
    padding: 3px 14px;
    margin-bottom: 10px;
    text-transform: uppercase;
}

.live-dot {
    display: inline-block; width: 10px; height: 10px; border-radius: 50%;
    background: #ff3b5c; margin-right: 8px;
    box-shadow: 0 0 0 0 rgba(255,59,92,.7);
    animation: pulse 1.6s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255,59,92,.7); }
    70% { box-shadow: 0 0 0 12px rgba(255,59,92,0); }
    100% { box-shadow: 0 0 0 0 rgba(255,59,92,0); }
}

.match-card {
    display: flex; justify-content: space-between; align-items: center;
    background: rgba(10,18,30,.75);
    border: 1px solid rgba(0,170,255,.2);
    border-radius: 14px;
    padding: 14px 22px;
    margin-bottom: 10px;
}
.match-card .teams { font-size: 1.25rem; font-weight: 700; }
.match-card .score {
    font-family: 'Orbitron', sans-serif; font-size: 1.6rem; color: #00ffb2;
    min-width: 110px; text-align: center;
}
.match-card .meta { color: #8fa6bd; font-size: .95rem; text-align: right; }

.odds-row { display: flex; align-items: center; margin: 7px 0; }
.odds-rank {
    font-family: 'Orbitron', sans-serif; width: 34px; color: #00aaff;
    font-size: .9rem;
}
.odds-team { width: 150px; font-weight: 600; font-size: 1.05rem; }
.odds-bar-bg {
    flex: 1; height: 14px; background: rgba(255,255,255,.06);
    border-radius: 999px; overflow: hidden; margin: 0 12px;
}
.odds-bar {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #00ffb2, #00aaff);
    box-shadow: 0 0 12px rgba(0,255,178,.5);
}
.odds-pct { width: 64px; font-family: 'Orbitron', sans-serif; color: #00ffb2; }

.big-pick {
    text-align: center; padding: 22px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(255,200,0,.07), rgba(0,255,178,.06));
    border: 1px solid rgba(255,200,0,.35);
}
.big-pick .team {
    font-family: 'Orbitron', sans-serif; font-size: 2.2rem; color: #ffd84d;
    text-shadow: 0 0 24px rgba(255,216,77,.45);
}
.big-pick .conf { color: #8fa6bd; font-size: 1rem; margin-top: 4px; }

.kv { color:#8fa6bd; font-size:.92rem; }
.kv b { color:#d7e4f2; }

[data-testid="stMetricValue"] { font-family: 'Orbitron', sans-serif; color:#00ffb2; }
.stTabs [data-baseweb="tab"] { font-family:'Rajdhani'; font-weight:600; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Constants & helpers
# ----------------------------------------------------------------------------
FD_BASE = "https://api.football-data.org/v4"
WC_CODE = "WC"  # FIFA World Cup competition code on football-data.org
GAMMA = "https://gamma-api.polymarket.com/events"
POLY_SLUG = "world-cup-winner"

FLAGS = {
    "Argentina": "🇦🇷", "Brazil": "🇧🇷", "France": "🇫🇷", "Spain": "🇪🇸",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Portugal": "🇵🇹", "Germany": "🇩🇪", "Netherlands": "🇳🇱",
    "Italy": "🇮🇹", "Belgium": "🇧🇪", "Croatia": "🇭🇷", "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴", "Mexico": "🇲🇽", "USA": "🇺🇸", "United States": "🇺🇸",
    "Canada": "🇨🇦", "Japan": "🇯🇵", "South Korea": "🇰🇷", "Korea Republic": "🇰🇷",
    "Morocco": "🇲🇦", "Senegal": "🇸🇳", "Ghana": "🇬🇭", "Nigeria": "🇳🇬",
    "Australia": "🇦🇺", "Switzerland": "🇨🇭", "Denmark": "🇩🇰", "Norway": "🇳🇴",
    "Austria": "🇦🇹", "Ecuador": "🇪🇨", "Paraguay": "🇵🇾", "Panama": "🇵🇦",
    "Iran": "🇮🇷", "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦", "Uzbekistan": "🇺🇿",
    "Jordan": "🇯🇴", "Egypt": "🇪🇬", "Algeria": "🇩🇿", "Tunisia": "🇹🇳",
    "Ivory Coast": "🇨🇮", "Côte d'Ivoire": "🇨🇮", "Cape Verde": "🇨🇻",
    "South Africa": "🇿🇦", "New Zealand": "🇳🇿", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Haiti": "🇭🇹", "Curaçao": "🇨🇼", "Honduras": "🇭🇳", "Costa Rica": "🇨🇷",
}


def flag(team: str) -> str:
    return FLAGS.get(team, "⚽")


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
    r = requests.get(
        f"{FD_BASE}/competitions/{WC_CODE}/matches",
        headers={"X-Auth-Token": api_key},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_standings(api_key: str) -> dict:
    if not api_key:
        return {}
    r = requests.get(
        f"{FD_BASE}/competitions/{WC_CODE}/standings",
        headers={"X-Auth-Token": api_key},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=120, show_spinner=False)
def fetch_polymarket() -> list:
    """Return [(team, implied_prob), ...] sorted desc from Polymarket."""
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


# Fallback odds (Polymarket snapshot, June 2026) if the API is unreachable
FALLBACK_ODDS = [
    ("Spain", 0.16), ("France", 0.16), ("England", 0.10), ("Portugal", 0.09),
    ("Argentina", 0.09), ("Brazil", 0.08), ("Germany", 0.06),
    ("Netherlands", 0.04), ("Italy", 0.03), ("Belgium", 0.02),
]


# ----------------------------------------------------------------------------
# Prediction engine: blend table form + market odds
# ----------------------------------------------------------------------------
def table_strength(standings: dict) -> dict:
    """Score each team from group table: points + goal-difference signal, 0..1."""
    scores = {}
    for s in standings.get("standings", []):
        if s.get("type") != "TOTAL":
            continue
        for row in s.get("table", []):
            name = row["team"]["name"]
            played = max(row.get("playedGames", 0), 1)
            pts = row.get("points", 0) / (played * 3)          # 0..1
            gd = row.get("goalDifference", 0) / (played * 4)   # roughly -1..1
            scores[name] = max(0.0, min(1.0, 0.7 * pts + 0.3 * (0.5 + gd / 2)))
    return scores


def blended_prediction(odds: list, strength: dict) -> list:
    """60% market odds + 40% on-pitch table form → ranked list."""
    if not odds:
        return []
    max_p = max(p for _, p in odds) or 1.0
    blended = []
    for team, p in odds[:15]:
        s = strength.get(team)
        if s is None:  # try loose name match (e.g. "USA" vs "United States")
            for k, v in strength.items():
                if team.lower() in k.lower() or k.lower() in team.lower():
                    s = v
                    break
        score = 0.6 * (p / max_p) + 0.4 * (s if s is not None else p / max_p)
        blended.append((team, p, score))
    blended.sort(key=lambda x: -x[2])
    return blended


# ----------------------------------------------------------------------------
# UI building blocks
# ----------------------------------------------------------------------------
def hero():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    st.markdown(
        f"""
        <div class="hero">
          <h1>⚽ WC26 // AGENT</h1>
          <p>Autonomous World Cup 2026 intelligence — live scores · standings ·
          AI winner projection · crowd-market odds &nbsp;|&nbsp;
          🇺🇸 🇲🇽 🇨🇦 United 2026 &nbsp;·&nbsp; sync {now}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def match_card(m: dict):
    home, away = m["homeTeam"]["name"], m["awayTeam"]["name"]
    status = m.get("status", "")
    ft = m.get("score", {}).get("fullTime", {})
    hs, as_ = ft.get("home"), ft.get("away")
    when = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
    stage = (m.get("stage") or "").replace("_", " ").title()
    group = (m.get("group") or "").replace("_", " ").title()

    if status in ("IN_PLAY", "PAUSED"):
        score = f"{hs if hs is not None else 0} : {as_ if as_ is not None else 0}"
        meta = f'<span class="live-dot"></span>LIVE — {status.replace("_", " ")}'
    elif status == "FINISHED":
        score = f"{hs} : {as_}"
        meta = "FULL TIME"
    else:
        score = "vs"
        meta = when.strftime("%a %d %b · %H:%M UTC")

    st.markdown(
        f"""
        <div class="match-card">
          <div class="teams">{flag(home)} {home} &nbsp;—&nbsp; {away} {flag(away)}</div>
          <div class="score">{score}</div>
          <div class="meta">{meta}<br>{group or stage}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def odds_panel(odds: list, source_live: bool):
    tag = "POLYMARKET · LIVE" if source_live else "POLYMARKET · SNAPSHOT"
    st.markdown(f'<span class="section-tag">{tag}</span>', unsafe_allow_html=True)
    st.markdown("### 💸 Who the betting crowd backs")
    top = odds[:10]
    max_p = top[0][1] if top else 1
    rows = ""
    for i, (team, p) in enumerate(top, 1):
        rows += (
            f'<div class="odds-row"><div class="odds-rank">#{i:02d}</div>'
            f'<div class="odds-team">{flag(team)} {team}</div>'
            f'<div class="odds-bar-bg"><div class="odds-bar" '
            f'style="width:{p / max_p * 100:.1f}%"></div></div>'
            f'<div class="odds-pct">{p * 100:.1f}%</div></div>'
        )
    st.markdown(f'<div class="glass">{rows}</div>', unsafe_allow_html=True)
    st.caption(
        "Implied win probability from Polymarket's World Cup Winner market "
        "(real-money prediction market). Higher % = market favourite. "
        "Informational only — not betting advice."
    )


def prediction_panel(blend: list):
    st.markdown('<span class="section-tag">AI PROJECTION</span>',
                unsafe_allow_html=True)
    st.markdown("### 🤖 Agent's champion pick")
    if not blend:
        st.info("Prediction engine warming up — needs odds or standings data.")
        return
    top = blend[0]
    conf = top[2] / sum(b[2] for b in blend[:5]) * 100
    st.markdown(
        f"""
        <div class="big-pick">
          <div style="color:#8fa6bd;letter-spacing:3px;font-size:.8rem;">
            PROJECTED WORLD CHAMPION</div>
          <div class="team">{flag(top[0])} {top[0].upper()} 🏆</div>
          <div class="conf">agent confidence {conf:.0f}% · blend = 60% market
          odds + 40% live table form</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    podium = blend[1:4]
    cols = st.columns(3)
    for c, (team, p, s) in zip(cols, podium):
        c.metric(f"{flag(team)} {team}", f"{p * 100:.1f}%", "contender")


def next_match_panel(upcoming: list, odds_map: dict):
    st.markdown('<span class="section-tag">NEXT UP</span>', unsafe_allow_html=True)
    st.markdown("### 🔮 Coming matches — what to expect")
    if not upcoming:
        st.info("No scheduled matches found.")
        return
    nxt = upcoming[0]
    home, away = nxt["homeTeam"]["name"], nxt["awayTeam"]["name"]
    ph, pa = odds_map.get(home, 0.01), odds_map.get(away, 0.01)
    fav, dog = (home, away) if ph >= pa else (away, home)
    edge = abs(ph - pa)
    if edge > 0.05:
        expect = (f"<b>{fav}</b> goes in as clear favourite — the market gives "
                  f"them a much stronger title path. Expect {fav} to control "
                  f"possession; {dog}'s best route is transition and set pieces.")
    elif edge > 0.015:
        expect = (f"<b>{fav}</b> is slightly fancied, but this is closer than "
                  f"it looks. A single moment of quality could decide it.")
    else:
        expect = ("Coin-flip territory — the market can't split these sides. "
                  "Expect a cagey opening 30 minutes and fine margins.")
    when = datetime.fromisoformat(nxt["utcDate"].replace("Z", "+00:00"))
    st.markdown(
        f"""
        <div class="glass">
          <div style="font-size:1.5rem;font-weight:700;">
            {flag(home)} {home} &nbsp;vs&nbsp; {away} {flag(away)}</div>
          <div class="kv">🗓 <b>{when.strftime('%A %d %B %Y · %H:%M UTC')}</b>
            &nbsp;·&nbsp; {(nxt.get('group') or nxt.get('stage', '')).replace('_',' ').title()}</div>
          <p style="margin-top:10px;">{expect}</p>
          <div class="kv">Title odds: {home} <b>{ph*100:.1f}%</b> ·
            {away} <b>{pa*100:.1f}%</b> (Polymarket)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for m in upcoming[1:6]:
        match_card(m)


def standings_panel(standings: dict):
    st.markdown('<span class="section-tag">GROUP STAGE</span>',
                unsafe_allow_html=True)
    st.markdown("### 📊 Standings — all 12 groups")
    tables = [s for s in standings.get("standings", []) if s.get("type") == "TOTAL"]
    if not tables:
        st.info("Standings appear once the API key is set and group games begin "
                "(kickoff: 11 June 2026 🇲🇽).")
        return
    tabs = st.tabs([s.get("group", f"G{i}").replace("GROUP_", "Group ")
                    for i, s in enumerate(tables)])
    for tab, s in zip(tabs, tables):
        with tab:
            rows = [{
                "#": r["position"],
                "Team": f'{flag(r["team"]["name"])} {r["team"]["name"]}',
                "P": r["playedGames"], "W": r["won"], "D": r["draw"],
                "L": r["lost"], "GF": r["goalsFor"], "GA": r["goalsAgainst"],
                "GD": r["goalDifference"], "Pts": r["points"],
            } for r in s.get("table", [])]
            st.dataframe(pd.DataFrame(rows).set_index("#"),
                         use_container_width=True)


# ----------------------------------------------------------------------------
# Main — auto-refreshing fragment so live scores tick without manual reload
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
    upcoming = sorted(
        (m for m in all_matches if m.get("status") in ("TIMED", "SCHEDULED")),
        key=lambda m: m["utcDate"],
    )
    finished = sorted(
        (m for m in all_matches if m.get("status") == "FINISHED"),
        key=lambda m: m["utcDate"], reverse=True,
    )

    if not api_key:
        st.warning(
            "🔑 **No football-data.org API key found.** Live scores, fixtures "
            "and standings are disabled. Get a free key at "
            "https://www.football-data.org/client/register and add "
            "`FOOTBALL_DATA_API_KEY` to Streamlit secrets. "
            "Polymarket odds & the AI pick still work below.",
            icon="⚠️",
        )
    elif api_err:
        st.error(f"football-data.org error: {api_err}")

    # LIVE strip
    if live:
        st.markdown(
            '<span class="section-tag"><span class="live-dot"></span>'
            'LIVE NOW</span>', unsafe_allow_html=True)
        st.markdown("### 🔴 Matches in play")
        for m in live:
            match_card(m)
        st.caption("Auto-refreshes every 60 s. Free-tier scores can lag "
                   "slightly behind broadcast.")

    # Prediction + odds side by side
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        prediction_panel(blended_prediction(odds, table_strength(standings)))
    with c2:
        odds_panel(odds, odds_live)

    # Next matches
    next_match_panel(upcoming, odds_map)

    # Standings
    standings_panel(standings)

    # Recent results
    if finished:
        st.markdown('<span class="section-tag">RESULTS</span>',
                    unsafe_allow_html=True)
        st.markdown("### ✅ Latest results")
        for m in finished[:6]:
            match_card(m)

    st.markdown(
        '<p style="text-align:center;color:#5b7188;margin-top:24px;">'
        'WC26 // AGENT · data: football-data.org + Polymarket · '
        'predictions are statistical projections, not betting advice · '
        'built with Streamlit 🤖</p>',
        unsafe_allow_html=True,
    )


hero()
dashboard()
