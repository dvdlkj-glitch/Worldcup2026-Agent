"""
⚽ WC26 // AGENT — World Cup 2026 AI Dashboard  (v3.0)
=====================================================
Live scores · Group standings · AI winner prediction · Next-match preview
· Polymarket crowd odds · Odds trend chart · 中文/EN · Taipei time

Data sources:
  - football-data.org (free tier, code WC) — fixtures, live scores, standings.
  - Polymarket Gamma + CLOB APIs (public, no key) — win odds + price history.
"""

import json
import math
from datetime import datetime, timezone, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

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
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(1100px 540px at 18% -8%, #0d2030 0%, #070b12 50%) fixed, #070b12;
    color: #d7e4f2;
    font-family: 'Rajdhani', 'Noto Sans TC', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.6rem; max-width: 1250px; }

h1, h2, h3 { font-family: 'Orbitron', 'Noto Sans TC', sans-serif !important;
    letter-spacing: 1px; }

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

.stats { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.stat {
    flex: 1; min-width: 180px; padding: 14px 18px; border-radius: 14px;
    background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.08);
}
.stat .lbl { color:#7d93ab; font-size:.78rem; letter-spacing:2.5px;
    text-transform:uppercase; font-family:'Orbitron','Noto Sans TC'; }
.stat .val { font-family:'Orbitron','Noto Sans TC'; font-size:1.5rem;
    color:#00ffb2; margin-top:4px; display:flex; align-items:center; gap:8px;}

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
.sec-h { font-family:'Orbitron','Noto Sans TC'; font-size:1.25rem;
    color:#e8f1fa; margin: 2px 0 12px; }

img.flag { width: 26px; height: 19px; border-radius: 3px; object-fit: cover;
    vertical-align: -4px; box-shadow: 0 0 6px rgba(0,0,0,.6);
    border: 1px solid rgba(255,255,255,.15); }
img.flag.sm { width: 21px; height: 15px; }
.noflag { display:inline-block; width:26px; text-align:center; }

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

.match-card {
    display: grid; grid-template-columns: 1fr auto 1fr 165px;
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

.big-pick {
    text-align: center; padding: 22px 18px 18px; border-radius: 16px;
    background: linear-gradient(150deg, rgba(255,200,0,.08), rgba(0,255,178,.05));
    border: 1px solid rgba(255,200,0,.35); margin-bottom: 12px;
}
.big-pick .pre { color:#8fa6bd; letter-spacing:3px; font-size:.74rem;
    font-family:'Orbitron','Noto Sans TC'; }
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

.wc-table { width: 100%; border-collapse: collapse; font-size: 1rem; }
.wc-table th {
    font-family: 'Orbitron','Noto Sans TC'; font-size: .7rem;
    letter-spacing: 1.6px; color: #7d93ab; text-transform: uppercase;
    font-weight: 600; padding: 8px 10px;
    border-bottom: 1px solid rgba(255,255,255,.12); text-align: center;
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

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Rajdhani','Noto Sans TC'; font-weight: 700; font-size: 1rem;
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

/* language radio — force readable text on any base theme */
div[role="radiogroup"] { gap: 4px; }
div[role="radiogroup"] label {
    background: rgba(10,18,30,.85); border: 1px solid rgba(255,255,255,.18);
    border-radius: 999px; padding: 2px 14px;
}
div[role="radiogroup"] label p, div[role="radiogroup"] label div {
    color: #c7d6e6 !important; font-weight: 600;
}
div[role="radiogroup"] label:has(input:checked) {
    border-color: rgba(0,255,178,.6); background: rgba(0,255,178,.12);
}
div[role="radiogroup"] label:has(input:checked) p {
    color: #00ffb2 !important;
}

.kv { color:#8fa6bd; font-size:.92rem; }
.kv b { color:#e8f1fa; }
.foot { text-align:center; color:#51677e; margin-top:28px; font-size:.9rem; }

/* AI showdown row animations */
.trophy {
    display: inline-block;
    animation: trophyPop .7s cubic-bezier(.2,1.6,.4,1) both,
               trophyGlow 2.2s ease-in-out infinite .7s;
}
@keyframes trophyPop {
    0% { transform: scale(0) rotate(-40deg); }
    70% { transform: scale(1.35) rotate(10deg); }
    100% { transform: scale(1) rotate(0); }
}
@keyframes trophyGlow {
    0%, 100% { filter: drop-shadow(0 0 2px rgba(255,216,77,.4)); }
    50% { filter: drop-shadow(0 0 8px rgba(255,216,77,.9)); }
}
.ft-flash { animation: ftPulse 2.4s ease-in-out 2; }
@keyframes ftPulse {
    0%, 100% { text-shadow: 0 0 4px rgba(0,255,178,.3); }
    50% { text-shadow: 0 0 16px rgba(0,255,178,.9); }
}

/* expander — keep dark on any base theme */
[data-testid="stExpander"] {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.1) !important;
    border-radius: 12px;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #c7d6e6 !important;
}
[data-testid="stExpander"] svg { fill: #c7d6e6; }

/* ---- responsive: tablet ---- */
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
    .match-card { grid-template-columns: 1fr auto 1fr; gap: 8px;
        padding: 11px 13px; }
    .mc-team { font-size: .98rem; }
    .mc-score { font-size: 1.15rem; min-width: 64px; }
    .mc-meta { grid-column: 1 / -1; text-align: center; font-size: .8rem;
        border-top: 1px solid rgba(255,255,255,.06); padding-top: 6px; }
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

/* extra-narrow screens — foldable cover displays (~340px) */
@media (max-width: 380px) {
    .block-container { padding-left: .6rem; padding-right: .6rem; }
    .hero { padding: 14px 12px; }
    .hero h1 { font-size: 1.1rem; }
    .hero p { font-size: .8rem; }
    .hero .byline { font-size: .56rem; letter-spacing: 1px; }
    .stat { min-width: 100%; flex-basis: 100%; padding: 9px 12px; }
    .sec-h { font-size: .95rem; }
    .section-tag { font-size: .6rem; padding: 2px 10px; }
    .mc-score { font-size: 1rem; min-width: 54px; }
    .odds-rank { min-width: 24px; font-size: .68rem; }
    .odds-team { min-width: 92px; font-size: .82rem; }
    .odds-pct { min-width: 42px; font-size: .74rem; }
    .pod { min-width: calc(50% - 10px); }
    .big-pick .team { font-size: 1.2rem; }
    .glass { padding: 10px 10px; }
    .wc-table { min-width: 480px; font-size: .85rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# i18n  (中文 / English)
# ----------------------------------------------------------------------------
TR = {
    "flow_title":   ("🎬 Agent 運作流程", "🎬 How the agent works"),
    "live_now":     ("即時比賽", "Live now"),
    "today":        ("今日賽事", "Matches today"),
    "market_fav":   ("市場最看好", "Market favourite"),
    "days_final":   ("距離決賽", "Days to final"),
    "final_sub":    (" · 7/19 紐約/紐澤西", " · 19 Jul, NY/NJ"),
    "none":         ("無", "none"),
    "live_title":   ("🔴 進行中的比賽", "🔴 Matches in play"),
    "live_caption": ("每 60 秒自動更新。免費版資料可能比轉播稍慢。",
                     "Auto-refreshes every 60 s. Free-tier scores can lag "
                     "broadcast slightly."),
    "pick_title":   ("🤖 AI 奪冠預測", "🤖 Agent's champion pick"),
    "projected":    ("AI 預測世界冠軍", "PROJECTED WORLD CHAMPION"),
    "conf":         ("相對前五強信心值 {c}%", "agent confidence {c}% vs next contenders"),
    "blend_t":      ("模型權重", "Model blend"),
    "blend_o":      ("📈 市場賠率 60%", "📈 market odds 60%"),
    "blend_f":      ("⚽ 即時戰績 40%", "⚽ live table form 40%"),
    "pick_warm":    ("預測引擎啟動中——需要賠率或積分資料。",
                     "Prediction engine warming up — needs odds or standings."),
    "odds_title":   ("💸 賭盤群眾看好誰", "💸 Who the betting crowd backs"),
    "odds_caption": ("數據為 Polymarket「世界盃冠軍」市場的隱含奪冠機率，"
                     "僅供參考與趣味追蹤，不構成任何投注建議。",
                     "Implied win probability from Polymarket's World Cup "
                     "Winner market. Informational only — not betting advice."),
    "trend_title":  ("📈 奪冠機率走勢（前 5 強・近 30 天）",
                     "📈 Title-odds trend (top 5 · last 30 days)"),
    "trend_caption": ("資料：Polymarket 價格歷史，每 12 小時取樣一點。"
                      "賽果會即刻反映在市場價格上。",
                      "Source: Polymarket price history, 12-hour sampling. "
                      "Match results move the market instantly."),
    "next_title":   ("🔮 接下來的比賽——看點分析", "🔮 Coming matches — what to expect"),
    "no_fixtures":  ("找不到賽程——請先設定 API 金鑰。",
                     "No scheduled matches found — add your API key."),
    "exp_clear":    ("<b>{fav}</b> 是明顯的賭盤熱門——市場給出的奪冠路徑強得多。"
                     "預期 {fav} 將掌控節奏；{dog} 的機會在防守反擊與定位球。",
                     "<b>{fav}</b> goes in as clear favourite — the market "
                     "gives them a far stronger title path. Expect {fav} to "
                     "dictate tempo; {dog}'s route is transition play and "
                     "set pieces."),
    "exp_slight":   ("<b>{fav}</b> 稍被看好，但實際差距比看起來小——"
                     "一個瞬間的靈光就能決定勝負。",
                     "<b>{fav}</b> is slightly fancied, but this is closer "
                     "than it looks — one moment of quality could decide it."),
    "exp_coin":     ("五五波——市場分不出高下。預期上半場會打得保守，勝負在細節。",
                     "Coin-flip territory — the market can't split these "
                     "sides. Expect a cagey opening half and fine margins."),
    "title_odds":   ("奪冠機率 — {h}：<b>{hp}%</b> · {a}：<b>{ap}%</b>（Polymarket）",
                     "Title odds — {h}: <b>{hp}%</b> · {a}: <b>{ap}%</b> "
                     "(Polymarket)"),
    "standings_title": ("📊 小組積分榜——全部 12 組", "📊 Standings — all 12 groups"),
    "standings_info": ("設定 API 金鑰後，小組賽開踢（2026/6/11 🇲🇽）即顯示積分榜。",
                       "Standings appear once your API key is set and group "
                       "games kick off (11 June 2026 🇲🇽)."),
    "legend":       ('<span class="g">▎</span> 前 2 名——晉級 32 強 &nbsp;&nbsp; '
                     '<span class="y">▎</span> 第 3 名——可能以最佳第三晉級（取 8 隊）',
                     '<span class="g">▎</span> top 2 — advance to round of 32 '
                     '&nbsp;&nbsp; <span class="y">▎</span> 3rd — may advance '
                     'among 8 best third-placed teams'),
    "results_title": ("✅ 最新賽果", "✅ Latest results"),
    "ft":           ("終場", "FULL TIME"),
    "ht":           (" · 中場", " · HT"),
    "live_lbl":     ("直播中", "LIVE"),
    "warn_key":     ("🔑 **尚未設定 football-data.org API 金鑰。**即時比分、賽程與"
                     "積分榜目前停用。請到 https://www.football-data.org/client/register "
                     "免費註冊，並把 `FOOTBALL_DATA_API_KEY` 加入 Streamlit secrets。",
                     "🔑 **No football-data.org API key found.** Live scores, "
                     "fixtures and standings are disabled. Get a free key at "
                     "https://www.football-data.org/client/register and add "
                     "`FOOTBALL_DATA_API_KEY` to Streamlit secrets."),
    "foot":         ("WC26 // AGENT · 資料：football-data.org + Polymarket · "
                     "國旗：flagcdn.com · 所有預測僅為統計推估，不構成投注建議 · "
                     "Streamlit 製作 🤖",
                     "WC26 // AGENT · data: football-data.org + Polymarket · "
                     "flags: flagcdn.com · predictions are statistical "
                     "projections, not betting advice · built with Streamlit 🤖"),
}


def L(key: str) -> str:
    zh = st.session_state.get("lang", "中文") == "中文"
    return TR[key][0 if zh else 1]


# ----------------------------------------------------------------------------
# Time helpers — display in Taipei time (UTC+8)
# ----------------------------------------------------------------------------
TPE = timezone(timedelta(hours=8))
WEEK_ZH = "一二三四五六日"


def fmt_dt(dt: datetime, long: bool = False) -> str:
    t = dt.astimezone(TPE)
    if st.session_state.get("lang", "中文") == "中文":
        base = f"{t.month}/{t.day}（週{WEEK_ZH[t.weekday()]}）{t:%H:%M}"
        return base + (" 台北時間" if long else " 台北")
    return t.strftime("%a %d %b · %H:%M") + " TPE"


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
FD_BASE = "https://api.football-data.org/v4"
WC_CODE = "WC"
GAMMA = "https://gamma-api.polymarket.com/events"
CLOB_HIST = "https://clob.polymarket.com/prices-history"
POLY_SLUG = "world-cup-winner"
FINAL_DATE = datetime(2026, 7, 19, tzinfo=timezone.utc)

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
    key = (team or "").lower().strip()
    iso = ISO.get(key)
    if iso is None:
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
# Visitor counter (counterapi.dev — free, no key, persists across redeploys)
# ----------------------------------------------------------------------------
VISIT_API = "https://api.counterapi.dev/v1/wc26-agent-davidlau/visits"


def visitor_count():
    """Count once per browser session; afterwards read-only. None on failure."""
    try:
        if not st.session_state.get("_visit_counted"):
            r = requests.get(f"{VISIT_API}/up", timeout=6)
            st.session_state["_visit_counted"] = True
        else:
            r = requests.get(VISIT_API, timeout=6)
        r.raise_for_status()
        return int(r.json().get("count", 0))
    except Exception:
        return None


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
    """[(team, implied_prob, clob_token_id), ...] sorted desc."""
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
            try:
                tid = json.loads(m.get("clobTokenIds") or "[]")[0]
            except (ValueError, TypeError, IndexError):
                tid = None
            if team and p is not None and p > 0.001:
                out.append((team, p, tid))
        out.sort(key=lambda x: -x[1])
        return out
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_odds_history(token_id: str) -> list:
    """[(datetime, prob), ...] — 30 days, 12-hour sampling."""
    try:
        r = requests.get(CLOB_HIST,
                         params={"market": token_id, "interval": "1m",
                                 "fidelity": 720},
                         timeout=15)
        r.raise_for_status()
        return [(datetime.fromtimestamp(pt["t"], tz=timezone.utc), pt["p"])
                for pt in r.json().get("history", [])]
    except Exception:
        return []


FALLBACK_ODDS = [
    ("Spain", 0.16, None), ("France", 0.16, None), ("England", 0.10, None),
    ("Portugal", 0.09, None), ("Argentina", 0.09, None),
    ("Brazil", 0.08, None), ("Germany", 0.06, None),
    ("Netherlands", 0.04, None), ("Italy", 0.03, None), ("Belgium", 0.02, None),
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
    max_p = max(p for _, p, _t in odds) or 1.0
    blended = []
    for team, p, _tid in odds[:15]:
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
# Poisson score predictor
#   λ_home = μ · (P_home/P_away)^0.2  blended 50/50 with live scoring rates
#   P(h,a) = Pois(h;λh)·Pois(a;λa) → argmax = predicted score
# ----------------------------------------------------------------------------
WC_MU = 1.35  # average goals per team per match at recent World Cups


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def team_goal_rates(standings: dict) -> dict:
    """{team: (goals_for_per_game, goals_against_per_game)} once games played."""
    rates = {}
    for s in standings.get("standings", []):
        if s.get("type") != "TOTAL":
            continue
        for row in s.get("table", []):
            played = row.get("playedGames", 0)
            if played > 0:
                rates[row["team"]["name"]] = (row["goalsFor"] / played,
                                              row["goalsAgainst"] / played)
    return rates


def predict_score(ph: float, pa: float, home: str, away: str,
                  rates: dict) -> dict:
    """Most likely scoreline + win/draw/loss probabilities."""
    ph, pa = max(ph, 0.003), max(pa, 0.003)
    lam_h = WC_MU * (ph / pa) ** 0.2
    lam_a = WC_MU * (pa / ph) ** 0.2
    if home in rates and away in rates:  # blend in on-pitch reality
        gf_h, ga_h = rates[home]
        gf_a, ga_a = rates[away]
        lam_h = 0.5 * lam_h + 0.5 * max(0.2, (gf_h + ga_a) / 2)
        lam_a = 0.5 * lam_a + 0.5 * max(0.2, (gf_a + ga_h) / 2)
    lam_h = min(max(lam_h, 0.3), 3.2)
    lam_a = min(max(lam_a, 0.3), 3.2)
    best, best_p, p_win, p_draw, p_loss = (1, 1), 0.0, 0.0, 0.0, 0.0
    for h in range(7):
        for a in range(7):
            p = poisson_pmf(h, lam_h) * poisson_pmf(a, lam_a)
            if p > best_p:
                best, best_p = (h, a), p
            if h > a:
                p_win += p
            elif h == a:
                p_draw += p
            else:
                p_loss += p
    tot = p_win + p_draw + p_loss
    return {"score": best, "p_score": best_p,
            "win": p_win / tot, "draw": p_draw / tot, "loss": p_loss / tot,
            "lam": (lam_h, lam_a)}


# ----------------------------------------------------------------------------
# System-flow animation (embedded, plays inside an iframe component)
# ----------------------------------------------------------------------------
ANIM_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:transparent;color:#d7e4f2;font-family:'Noto Sans TC',sans-serif;
display:flex;flex-direction:column;align-items:center;overflow:hidden}
.cap{font-size:1rem;color:#ffd84d;min-height:1.6em;margin:4px 0 10px;
text-align:center;font-weight:500;transition:opacity .4s;
text-shadow:0 0 14px rgba(255,216,77,.3)}
svg{width:100%;max-width:860px;height:auto}
.node{fill:rgba(255,255,255,.03);stroke:rgba(255,255,255,.14);stroke-width:1.2;
transition:stroke .4s,filter .4s}
.node.on{stroke:#00ffb2;filter:drop-shadow(0 0 10px rgba(0,255,178,.5))}
.node.gold.on{stroke:#ffd84d;filter:drop-shadow(0 0 12px rgba(255,216,77,.55))}
.nlabel{font-family:'Orbitron';font-size:11px;fill:#00ffb2;letter-spacing:2px}
.ntext{font-size:13px;fill:#d7e4f2;font-weight:700}
.nsub{font-size:10.5px;fill:#7d93ab}
.pipe{fill:none;stroke:rgba(0,170,255,.22);stroke-width:2}
.dot{fill:#00ffb2;filter:drop-shadow(0 0 6px #00ffb2)}
.dot.blue{fill:#00aaff;filter:drop-shadow(0 0 6px #00aaff)}
.dot.gold{fill:#ffd84d;filter:drop-shadow(0 0 6px #ffd84d)}
.scoreTxt{font-family:'Orbitron';font-size:17px;fill:#00ffb2}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.liveDot{fill:#ff3b5c;animation:pulse 1.4s infinite}
.barbg{fill:rgba(255,255,255,.07)}
.bar{fill:#00d4a8}
.legend{display:flex;gap:16px;margin-top:6px;flex-wrap:wrap;
justify-content:center;color:#7d93ab;font-size:.82rem}
.chip{display:inline-block;width:9px;height:9px;border-radius:50%;
margin-right:4px;vertical-align:-1px}
button{background:rgba(0,255,178,.08);color:#00ffb2;margin-top:8px;
border:1px solid rgba(0,255,178,.4);border-radius:999px;padding:5px 18px;
font-family:'Orbitron';font-size:.72rem;letter-spacing:2px;cursor:pointer}
@media(max-width:600px){.cap{font-size:.82rem}}
</style></head><body>
<div class="cap" id="caption">準備開賽…</div>
<svg viewBox="0 0 860 520" xmlns="http://www.w3.org/2000/svg">
<g id="nodeFD"><rect class="node" x="30" y="50" width="200" height="92" rx="14"/>
<text class="nlabel" x="50" y="78">DATA SOURCE 01</text>
<text class="ntext" x="50" y="102">football-data.org</text>
<text class="nsub" x="50" y="122">即時比分・賽程・12 組積分榜</text></g>
<g id="nodePM"><rect class="node" x="30" y="290" width="200" height="92" rx="14"/>
<text class="nlabel" x="50" y="318">DATA SOURCE 02</text>
<text class="ntext" x="50" y="342">Polymarket 預測市場</text>
<text class="nsub" x="50" y="362">群眾下注 → 各隊奪冠機率</text></g>
<g id="nodeAI"><rect class="node gold" x="330" y="160" width="210" height="150" rx="16"/>
<text class="nlabel" x="352" y="190" fill="#ffd84d">AI AGENT CORE</text>
<text class="ntext" x="352" y="216">🤖 預測引擎</text>
<text class="nsub" x="352" y="238">市場賠率 60%</text>
<rect class="barbg" x="352" y="246" width="166" height="8" rx="4"/>
<rect class="bar" id="bar60" x="352" y="246" width="0" height="8" rx="4"/>
<text class="nsub" x="352" y="274">即時戰績 40%</text>
<rect class="barbg" x="352" y="282" width="166" height="8" rx="4"/>
<rect class="bar" id="bar40" x="352" y="282" width="0" height="8" rx="4"/></g>
<g id="nodeLive"><rect class="node" x="630" y="20" width="200" height="100" rx="14"/>
<text class="nlabel" x="650" y="48">LIVE</text><circle class="liveDot" cx="700" cy="44" r="4"/>
<text class="ntext" x="650" y="74">🔴 即時比分</text>
<text class="scoreTxt" id="score" x="650" y="102">MEX 0 : 0 KOR</text></g>
<g id="nodeTable"><rect class="node" x="630" y="150" width="200" height="80" rx="14"/>
<text class="nlabel" x="650" y="178">STANDINGS</text>
<text class="ntext" x="650" y="202">📊 12 組積分榜</text>
<text class="nsub" x="650" y="220">前 2 晉級・第 3 名待定</text></g>
<g id="nodePick"><rect class="node gold" x="630" y="260" width="200" height="100" rx="14"/>
<text class="nlabel" x="650" y="288" fill="#ffd84d">AI PROJECTION</text>
<text class="ntext" x="650" y="314">🏆 奪冠預測</text>
<text class="scoreTxt" id="pick" x="650" y="342" fill="#ffd84d">— —</text></g>
<g id="nodeOdds"><rect class="node" x="630" y="390" width="200" height="86" rx="14"/>
<text class="nlabel" x="650" y="418">MARKET ODDS</text>
<text class="ntext" x="650" y="442">💸 群眾賠率排行</text>
<rect class="barbg" x="650" y="452" width="160" height="7" rx="3"/>
<rect class="bar" id="oddsBar" x="650" y="452" width="0" height="7" rx="3"/></g>
<path class="pipe" id="p1" d="M 230 96 C 290 96, 290 200, 330 208"/>
<path class="pipe" id="p2" d="M 230 336 C 290 336, 290 280, 330 272"/>
<path class="pipe" id="p3" d="M 540 190 C 590 170, 590 80, 630 70"/>
<path class="pipe" id="p4" d="M 540 220 C 590 210, 590 190, 630 190"/>
<path class="pipe" id="p5" d="M 540 250 C 590 270, 590 310, 630 310"/>
<path class="pipe" id="p6" d="M 540 280 C 590 320, 590 433, 630 433"/>
<circle class="dot" r="4"><animateMotion dur="2.4s" repeatCount="indefinite"><mpath href="#p1"/></animateMotion></circle>
<circle class="dot" r="4"><animateMotion dur="2.4s" begin="1.2s" repeatCount="indefinite"><mpath href="#p1"/></animateMotion></circle>
<circle class="dot blue" r="4"><animateMotion dur="2.8s" repeatCount="indefinite"><mpath href="#p2"/></animateMotion></circle>
<circle class="dot blue" r="4"><animateMotion dur="2.8s" begin="1.4s" repeatCount="indefinite"><mpath href="#p2"/></animateMotion></circle>
<circle class="dot gold" r="4"><animateMotion dur="2.2s" repeatCount="indefinite"><mpath href="#p3"/></animateMotion></circle>
<circle class="dot gold" r="4"><animateMotion dur="2.5s" begin=".6s" repeatCount="indefinite"><mpath href="#p4"/></animateMotion></circle>
<circle class="dot gold" r="4"><animateMotion dur="2.3s" begin=".3s" repeatCount="indefinite"><mpath href="#p5"/></animateMotion></circle>
<circle class="dot gold" r="4"><animateMotion dur="2.6s" begin=".9s" repeatCount="indefinite"><mpath href="#p6"/></animateMotion></circle>
<g transform="translate(430, 470)">
<circle r="28" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="5"/>
<circle id="timer" r="28" fill="none" stroke="#00ffb2" stroke-width="5"
stroke-linecap="round" stroke-dasharray="175.9" stroke-dashoffset="175.9" transform="rotate(-90)"/>
<text x="0" y="-1" text-anchor="middle" class="scoreTxt" id="timerTxt" font-size="13">60s</text>
<text x="0" y="15" text-anchor="middle" class="nsub" font-size="9">自動更新</text></g>
</svg>
<div class="legend">
<span><span class="chip" style="background:#00ffb2"></span>比分資料</span>
<span><span class="chip" style="background:#00aaff"></span>市場賠率</span>
<span><span class="chip" style="background:#ffd84d"></span>AI 運算結果</span>
<button id="replay">↻ REPLAY</button></div>
<script>
const captions=[
"第 1 步:每 60 秒向 football-data.org 抓取即時比分與積分榜",
"第 2 步:同時讀取 Polymarket — 全球玩家用真金白銀投出的奪冠機率",
"第 3 步:AI 引擎混合運算 — 市場賠率 60% + 即時戰績 40%",
"第 4 步:結果送進儀表板 — 比分、積分榜、奪冠預測、賠率排行",
"進球了!比分即時跳動,AI 預測也跟著重新計算 ⚽"];
const picks=["🇪🇸 SPAIN 16%","🇫🇷 FRANCE 16%","🇪🇸 SPAIN 16%"];
const scores=["MEX 0 : 0 KOR","MEX 1 : 0 KOR","MEX 1 : 1 KOR","MEX 2 : 1 KOR"];
const cap=document.getElementById('caption');
const nodes={fd:document.querySelector('#nodeFD .node'),
pm:document.querySelector('#nodePM .node'),ai:document.querySelector('#nodeAI .node'),
live:document.querySelector('#nodeLive .node'),table:document.querySelector('#nodeTable .node'),
pick:document.querySelector('#nodePick .node'),odds:document.querySelector('#nodeOdds .node')};
let timers=[];
function setCap(t){cap.style.opacity=0;
setTimeout(()=>{cap.textContent=t;cap.style.opacity=1;},300);}
function on(...ks){ks.forEach(k=>nodes[k].classList.add('on'));}
function offAll(){Object.values(nodes).forEach(n=>n.classList.remove('on'));}
function grow(id,w,delay){timers.push(setTimeout(()=>{
document.getElementById(id).setAttribute('width',w);},delay));}
function play(){
timers.forEach(clearTimeout);timers=[];offAll();
document.getElementById('score').textContent=scores[0];
document.getElementById('pick').textContent='— —';
['bar60','bar40','oddsBar'].forEach(id=>
document.getElementById(id).setAttribute('width',0));
timers.push(setTimeout(()=>{setCap(captions[0]);on('fd');},200));
timers.push(setTimeout(()=>{setCap(captions[1]);on('pm');},3200));
timers.push(setTimeout(()=>{setCap(captions[2]);on('ai');
grow('bar60',166,200);grow('bar40',110,700);},6200));
timers.push(setTimeout(()=>{setCap(captions[3]);
on('live','table','pick','odds');
document.getElementById('pick').textContent=picks[0];
grow('oddsBar',160,300);},9400));
scores.slice(1).forEach((s,i)=>timers.push(setTimeout(()=>{
setCap(captions[4]);
document.getElementById('score').textContent=s;
document.getElementById('pick').textContent=picks[(i+1)%picks.length];
},12800+i*2600)));
timers.push(setTimeout(play,12800+3*2600+2000));}
const ring=document.getElementById('timer'),ttxt=document.getElementById('timerTxt');
let t0=Date.now();
setInterval(()=>{const el=((Date.now()-t0)/6000)%1;
ring.setAttribute('stroke-dashoffset',175.9*(1-el));
ttxt.textContent=Math.ceil(60*(1-el))+'s';},50);
document.getElementById('replay').onclick=play;
play();
</script></body></html>
"""


# ----------------------------------------------------------------------------
# Countdown + host-city world clocks (live ticking via embedded JS)
# ----------------------------------------------------------------------------
CLOCK_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Noto+Sans+TC:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:transparent;color:#d7e4f2;font-family:'Noto Sans TC',sans-serif;
display:flex;flex-wrap:nowrap;gap:12px;justify-content:center;
align-items:stretch}
.panel{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.09);
border-radius:14px;padding:14px 20px;text-align:center}
.cd{flex:1.2;min-width:280px}
.wc{flex:1;min-width:280px}
/* narrow screens (incl. foldables' cover display): scale whole strip
   instead of wrapping — keeps both panels visible in the fixed iframe */
@media(max-width:680px){body{zoom:.8}}
@media(max-width:540px){body{zoom:.66}}
@media(max-width:430px){body{zoom:.56}}
@media(max-width:360px){body{zoom:.48}}
.lbl{font-family:'Orbitron','Noto Sans TC';font-size:.7rem;letter-spacing:2.5px;
color:#7d93ab;text-transform:uppercase;margin-bottom:8px}
.cd .match{color:#ffd84d;font-size:.95rem;font-weight:600;margin-bottom:8px}
.digits{display:flex;gap:8px;justify-content:center}
.dbox{background:rgba(10,18,30,.85);border:1px solid rgba(0,255,178,.3);
border-radius:10px;padding:7px 0;width:66px;flex:0 0 auto;
box-shadow:0 0 14px rgba(0,255,178,.12)}
.dnum{font-family:'Orbitron';font-size:1.55rem;color:#00ffb2;
font-variant-numeric:tabular-nums;white-space:nowrap;
text-shadow:0 0 12px rgba(0,255,178,.5)}
.dlab{font-size:.68rem;color:#7d93ab;letter-spacing:1.5px;margin-top:2px}
.kick{font-family:'Orbitron';font-size:1.5rem;color:#ffd84d;
text-shadow:0 0 18px rgba(255,216,77,.5);padding:14px 0;
animation:blink 1.2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.45}}
.cities{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.city{background:rgba(10,18,30,.85);border:1px solid rgba(0,170,255,.25);
border-radius:10px;padding:7px 4px;width:108px;flex:0 0 auto}
.cname{font-size:.74rem;color:#7d93ab;margin-bottom:2px;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.ctime{font-family:'Orbitron';font-size:1.02rem;color:#00aaff;
font-variant-numeric:tabular-nums;white-space:nowrap;
text-shadow:0 0 10px rgba(0,170,255,.4)}
.cflag{font-size:.85rem}
</style></head><body>
<div class="panel cd">
  <div class="lbl">__CD_TITLE__</div>
  <div class="match">__MATCH__</div>
  <div class="digits" id="digits">
    <div class="dbox"><div class="dnum" id="dd">--</div><div class="dlab">__D__</div></div>
    <div class="dbox"><div class="dnum" id="hh">--</div><div class="dlab">__H__</div></div>
    <div class="dbox"><div class="dnum" id="mm">--</div><div class="dlab">__M__</div></div>
    <div class="dbox"><div class="dnum" id="ss">--</div><div class="dlab">__S__</div></div>
  </div>
</div>
<div class="panel wc">
  <div class="lbl">__WC_TITLE__</div>
  <div class="cities">
    <div class="city"><div class="cname"><span class="cflag">🇹🇼</span> __C1__</div><div class="ctime" id="t1">--:--</div></div>
    <div class="city"><div class="cname"><span class="cflag">🇲🇽</span> __C2__</div><div class="ctime" id="t2">--:--</div></div>
    <div class="city"><div class="cname"><span class="cflag">🇺🇸</span> __C3__</div><div class="ctime" id="t3">--:--</div></div>
    <div class="city"><div class="cname"><span class="cflag">🇺🇸</span> __C4__</div><div class="ctime" id="t4">--:--</div></div>
  </div>
</div>
<script>
var target = new Date("__TARGET__").getTime();
function pad(n){return (n<10?"0":"")+n;}
function tick(){
  var now = Date.now();
  var d = target - now;
  if (d <= 0){
    document.getElementById('digits').innerHTML =
      '<div class="kick">__KICKOFF__</div>';
  } else {
    document.getElementById('dd').textContent = Math.floor(d/86400000);
    document.getElementById('hh').textContent = pad(Math.floor(d/3600000)%24);
    document.getElementById('mm').textContent = pad(Math.floor(d/60000)%60);
    document.getElementById('ss').textContent = pad(Math.floor(d/1000)%60);
  }
  var zones = [["t1","Asia/Taipei"],["t2","America/Mexico_City"],
               ["t3","America/New_York"],["t4","America/Los_Angeles"]];
  zones.forEach(function(z){
    document.getElementById(z[0]).textContent =
      new Date().toLocaleTimeString('en-GB',
        {timeZone:z[1],hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'});
  });
}
tick(); setInterval(tick, 1000);
</script></body></html>
"""

# ----------------------------------------------------------------------------
# Tactical preview animation (style-profile simulation, not real pass data)
# ----------------------------------------------------------------------------
TACTICS = {
    "Spain": ("4-3-3", "possession"), "France": ("4-2-3-1", "counter"),
    "England": ("4-2-3-1", "possession"), "Portugal": ("4-3-3", "wing"),
    "Argentina": ("4-3-3", "possession"), "Brazil": ("4-2-3-1", "wing"),
    "Germany": ("4-2-3-1", "press"), "Netherlands": ("4-3-3", "press"),
    "Italy": ("4-3-3", "possession"), "Belgium": ("4-2-3-1", "counter"),
    "Croatia": ("4-3-3", "possession"), "Mexico": ("4-3-3", "press"),
    "USA": ("4-3-3", "press"), "United States": ("4-3-3", "press"),
    "Canada": ("4-4-2", "counter"), "Japan": ("4-2-3-1", "counter"),
    "South Korea": ("4-4-2", "counter"), "Korea Republic": ("4-4-2", "counter"),
    "Morocco": ("4-3-3", "counter"), "Senegal": ("4-3-3", "counter"),
    "Uruguay": ("4-4-2", "press"), "Colombia": ("4-3-3", "wing"),
    "Switzerland": ("4-2-3-1", "counter"), "Denmark": ("4-3-3", "possession"),
    "Norway": ("4-4-2", "counter"), "Australia": ("4-4-2", "counter"),
}
DEFAULT_TACTIC = ("4-4-2", "counter")

# formation coordinates (x 0-100 left→right, y 0-100 top→bottom)
F_ATT = {
    "4-3-3": [(4, 50), (18, 15), (18, 38), (18, 62), (18, 85),
              (38, 30), (38, 50), (38, 70), (60, 20), (63, 50), (60, 80)],
    "4-2-3-1": [(4, 50), (18, 15), (18, 38), (18, 62), (18, 85),
                (33, 38), (33, 62), (48, 22), (48, 50), (48, 78), (63, 50)],
    "4-4-2": [(4, 50), (18, 15), (18, 38), (18, 62), (18, 85),
              (38, 20), (38, 42), (38, 58), (38, 80), (60, 40), (60, 60)],
}
F_DEF = {
    "low": [(96, 50), (84, 18), (84, 34), (84, 50), (84, 66), (84, 82),
            (73, 28), (73, 44), (73, 60), (73, 76), (60, 50)],
    "mid": [(96, 50), (82, 20), (82, 40), (82, 60), (82, 80),
            (69, 25), (69, 45), (69, 62), (69, 80), (57, 42), (57, 58)],
}
# attacking ball routes per style: [x, y, segment_ms]
SEQS = {
    "possession": [[4, 50, 900], [18, 38, 900], [38, 50, 1000], [38, 30, 900],
                   [38, 70, 900], [48, 56, 900], [63, 50, 800], [78, 38, 700],
                   [92, 47, 600]],
    "wing": [[18, 38, 800], [18, 85, 900], [45, 88, 900], [68, 90, 800],
             [80, 86, 700], [86, 62, 600], [78, 50, 550], [93, 48, 500]],
    "counter": [[30, 55, 600], [48, 60, 550], [70, 18, 750], [82, 24, 600],
                [87, 42, 550], [93, 49, 450]],
    "press": [[60, 40, 650], [52, 30, 550], [40, 45, 650], [55, 60, 650],
              [70, 65, 750], [83, 55, 650], [92, 49, 500]],
}
STYLE_LBL = {
    "possession": ("控球組織", "Possession build-up"),
    "wing": ("邊路進攻", "Wing play"),
    "counter": ("防守反擊", "Counter-attack"),
    "press": ("高位逼搶", "High press"),
}
BLOCK_LBL = {"low": ("低位防守 5-4-1", "Low block 5-4-1"),
             "mid": ("中場壓縮 4-4-2", "Mid block 4-4-2")}

TACTICS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:transparent;color:#d7e4f2;font-family:'Noto Sans TC',sans-serif;
display:flex;flex-direction:column;align-items:center;overflow:hidden}
.hd{display:flex;gap:14px;align-items:center;justify-content:center;
flex-wrap:wrap;margin-bottom:6px;font-size:.92rem}
.side{display:flex;gap:6px;align-items:center;font-weight:700}
.tag{font-family:'Orbitron','Noto Sans TC';font-size:.66rem;letter-spacing:1.5px;
border-radius:999px;padding:2px 10px}
.tA{color:#ffd84d;border:1px solid rgba(255,216,77,.45)}
.tD{color:#00aaff;border:1px solid rgba(0,170,255,.45)}
img.fl{width:22px;height:16px;border-radius:3px;vertical-align:-3px;
border:1px solid rgba(255,255,255,.2)}
.desc{color:#8fa6bd;font-size:.85rem;text-align:center;margin-bottom:6px}
svg{width:100%;max-width:760px;height:auto}
.pl{filter:drop-shadow(0 0 5px rgba(255,216,77,.6))}
.pd{filter:drop-shadow(0 0 5px rgba(0,170,255,.55))}
.shot{font-family:'Orbitron';font-size:26px;fill:#ffd84d;opacity:0;
text-shadow:0 0 18px rgba(255,216,77,.6)}
.note{color:#51677e;font-size:.74rem;margin-top:4px;text-align:center}
@media(max-width:600px){.hd{font-size:.8rem}.desc{font-size:.76rem}}
</style></head><body>
<div class="hd">
  <span class="side">__HFLAG__ __HOME__</span>
  <span class="tag tA">__ATT_TAG__</span>
  <span style="color:#4f9fd8;font-family:'Orbitron'">VS</span>
  <span class="tag tD">__DEF_TAG__</span>
  <span class="side">__AFLAG__ __AWAY__</span>
</div>
<div class="desc">__DESC__</div>
<svg viewBox="0 0 700 440" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="680" height="420" rx="8" fill="rgba(0,255,178,.025)"
        stroke="rgba(0,255,178,.25)" stroke-width="1.5"/>
  <line x1="350" y1="10" x2="350" y2="430" stroke="rgba(0,255,178,.2)" stroke-width="1.5"/>
  <circle cx="350" cy="220" r="56" fill="none" stroke="rgba(0,255,178,.2)" stroke-width="1.5"/>
  <rect x="10" y="130" width="86" height="180" fill="none" stroke="rgba(0,255,178,.2)" stroke-width="1.5"/>
  <rect x="604" y="130" width="86" height="180" fill="none" stroke="rgba(0,255,178,.2)" stroke-width="1.5"/>
  <rect x="4" y="185" width="6" height="70" fill="rgba(0,255,178,.35)"/>
  <rect x="690" y="185" width="6" height="70" fill="rgba(0,255,178,.35)"/>
  <g id="defG"></g>
  <g id="attG"></g>
  <circle id="ball" r="6" fill="#ffffff" stroke="#070b12" stroke-width="1.5"
          filter="drop-shadow(0 0 7px #fff)"/>
  <text id="shot" class="shot" x="560" y="150" text-anchor="middle">__SHOTLBL__</text>
</svg>
<div class="note">__NOTE__</div>
<script>
var ATT=__ATT__, DEF=__DEF__, SEQ=__SEQ__;
function px(x){return 10+x*6.8;} function py(y){return 10+y*4.2;}
var NS="http://www.w3.org/2000/svg";
var attG=document.getElementById('attG'), defG=document.getElementById('defG');
var defDots=[];
ATT.forEach(function(p){
  var c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',px(p[0]));c.setAttribute('cy',py(p[1]));
  c.setAttribute('r',8);c.setAttribute('fill','#ffd84d');c.setAttribute('class','pl');
  attG.appendChild(c);});
DEF.forEach(function(p){
  var c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',px(p[0]));c.setAttribute('cy',py(p[1]));
  c.setAttribute('r',8);c.setAttribute('fill','#00aaff');c.setAttribute('class','pd');
  c.dataset.ox=p[0];c.dataset.oy=p[1];
  defG.appendChild(c);defDots.push(c);});
var ball=document.getElementById('ball'), shot=document.getElementById('shot');
var seg=0, t0=null, from=SEQ[0];
ball.setAttribute('cx',px(from[0]));ball.setAttribute('cy',py(from[1]));
function frame(ts){
  if(seg>=SEQ.length-1){ // shot flash then restart
    shot.style.opacity=1;
    setTimeout(function(){shot.style.opacity=0;seg=0;t0=null;
      requestAnimationFrame(frame);},1300);
    return;}
  if(!t0)t0=ts;
  var a=SEQ[seg], b=SEQ[seg+1], dur=b[2];
  var k=Math.min((ts-t0)/dur,1);
  var x=a[0]+(b[0]-a[0])*k, y=a[1]+(b[1]-a[1])*k;
  ball.setAttribute('cx',px(x));ball.setAttribute('cy',py(y));
  // defensive block shifts toward the ball
  defDots.forEach(function(c){
    var ox=+c.dataset.ox, oy=+c.dataset.oy;
    c.setAttribute('cx',px(ox+(x-50)*0.06));
    c.setAttribute('cy',py(oy+(y-50)*0.18));});
  if(k>=1){seg++;t0=null;}
  requestAnimationFrame(frame);}
requestAnimationFrame(frame);
</script></body></html>
"""


def tactics_panel(nxt: dict, odds_map: dict):
    zh = st.session_state.get("lang", "中文") == "中文"
    home, away = nxt["homeTeam"]["name"], nxt["awayTeam"]["name"]

    def o(team):
        if team in odds_map:
            return odds_map[team]
        tl = team.lower()
        for k, v in odds_map.items():
            if tl in k.lower() or k.lower() in tl:
                return v
        return 0.005

    fav, dog = (home, away) if o(home) >= o(away) else (away, home)
    form, style = TACTICS.get(fav, DEFAULT_TACTIC)
    dog_style = TACTICS.get(dog, DEFAULT_TACTIC)[1]
    block = "low" if dog_style == "counter" else "mid"
    i = 0 if zh else 1
    s_lbl, b_lbl = STYLE_LBL[style][i], BLOCK_LBL[block][i]
    if zh:
        title = "⚔️ 戰術預演 — 下一場"
        desc = (f"預期 {fav} 以「{s_lbl}」主導進攻（{form}）；"
                f"{dog} 退守「{b_lbl}」，伺機反擊。")
        note = ("⚠️ 此為基於球隊風格檔案的戰術模擬動畫，非真實傳球數據，僅供趣味參考。")
        shotlbl = "射門！"
    else:
        title = "⚔️ Tactical preview — next match"
        desc = (f"Expect {fav} to attack via {s_lbl} ({form}); "
                f"{dog} defends in a {b_lbl}, looking to break.")
        note = ("⚠️ Style-profile simulation — not real pass data. "
                "For fun & preview only.")
        shotlbl = "SHOT!"
    html = (TACTICS_HTML
            .replace("__ATT__", json.dumps(F_ATT[form]))
            .replace("__DEF__", json.dumps(F_DEF[block]))
            .replace("__SEQ__", json.dumps(SEQS[style]))
            .replace("__HOME__", fav).replace("__AWAY__", dog)
            .replace("__HFLAG__", flag(fav, True))
            .replace("__AFLAG__", flag(dog, True))
            .replace("__ATT_TAG__", ("進攻 · " if zh else "ATT · ") + s_lbl)
            .replace("__DEF_TAG__", ("防守 · " if zh else "DEF · ") + b_lbl)
            .replace("__DESC__", desc).replace("__NOTE__", note)
            .replace("__SHOTLBL__", shotlbl))
    section("TACTICS SIM", title)
    components.html(html, height=560, scrolling=False)


# ----------------------------------------------------------------------------
# API-SPORTS official match-centre widget (live events/stats/lineups/players)
# NOTE: the widget key is rendered into the page HTML — that is by design for
# API-SPORTS widgets. Use the dedicated *Widget* key from your dashboard, NOT
# your main data API key.
# ----------------------------------------------------------------------------
APIF_BASE = "https://v3.football.api-sports.io"


def get_apif_data_key() -> str:
    """Server-side API-Football data key (NOT the widget key)."""
    try:
        return (st.secrets.get("APIFOOTBALL_KEY", "")
                or st.secrets.get("API_FOOTBALL_KEY", "")
                or st.secrets.get("APIFOOTBALL_DATA_KEY", ""))
    except Exception:
        return ""


def _fx_brief(f: dict) -> dict:
    venue = f["fixture"].get("venue") or {}
    vname = venue.get("name") or ""
    vcity = venue.get("city") or ""
    return {"id": f["fixture"]["id"],
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "date": f["fixture"].get("date", ""),
            "venue": (f"{vname} {vcity}").strip(),
            "venue_name": vname}


@st.cache_data(ttl=60, show_spinner=False)
def apif_live_fixtures(key: str) -> list:
    """World Cup fixtures currently in play: [{id, home, away}]."""
    if not key:
        return []
    r = requests.get(f"{APIF_BASE}/fixtures",
                     params={"live": "all", "league": 1},
                     headers={"x-apisports-key": key}, timeout=15)
    r.raise_for_status()
    return [_fx_brief(f) for f in r.json().get("response", [])]


@st.cache_data(ttl=300, show_spinner=False)
def apif_next_fixtures(key: str, n: int = 1) -> list:
    """Next n upcoming World Cup fixtures: [{id, home, away}]."""
    if not key:
        return []
    r = requests.get(f"{APIF_BASE}/fixtures",
                     params={"league": 1, "next": n},
                     headers={"x-apisports-key": key}, timeout=15)
    r.raise_for_status()
    return [_fx_brief(f) for f in r.json().get("response", [])]


# --- pre-match DEMO widget (tabbed, themed; auto-replaced once live) --------
DEMO_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Noto+Sans+TC:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:transparent;color:#d7e4f2;font-family:'Noto Sans TC',sans-serif}
.card{position:relative;max-width:760px;margin:0 auto;
background:rgba(10,18,30,.65);border:1px solid rgba(255,255,255,.1);
border-radius:14px;overflow:hidden}
.badge{position:absolute;top:10px;right:12px;font-family:'Orbitron','Noto Sans TC';
font-size:.6rem;letter-spacing:2px;color:#ffd84d;
border:1px dashed rgba(255,216,77,.55);border-radius:999px;padding:3px 10px;z-index:6}
.wm{position:absolute;inset:0;display:flex;align-items:center;
justify-content:center;pointer-events:none;z-index:5}
.wm span{font-family:'Orbitron';font-size:3.2rem;color:rgba(255,255,255,.035);
transform:rotate(-18deg);letter-spacing:10px;white-space:nowrap}
.hdr{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
padding:18px 20px 8px;gap:10px;text-align:center}
.team{font-weight:700;font-size:1.12rem}
.team img{width:44px;height:31px;border-radius:4px;display:block;
margin:0 auto 6px;border:1px solid rgba(255,255,255,.22);
box-shadow:0 0 10px rgba(0,0,0,.6)}
.team.h{color:#ffd84d}.team.a{color:#00aaff}
.mid .dt{color:#9db3ca;font-size:.92rem}
.mid .sc{font-family:'Orbitron';font-size:1.7rem;color:#d7e4f2;margin:2px 0}
.mid .st{color:#00ffb2;font-size:.78rem;font-family:'Orbitron','Noto Sans TC';
letter-spacing:1.5px}
.ven{text-align:center;color:#7d93ab;font-size:.86rem;padding-bottom:8px}
.stadwrap{display:none;margin:2px 16px 10px;border-radius:10px;
overflow:hidden;border:1px solid rgba(255,255,255,.14)}
.stadwrap img{width:100%;max-height:190px;object-fit:cover;display:block}
.hint{text-align:center;color:#ffd84d;font-size:.85rem;padding:2px 0 8px;
text-shadow:0 0 10px rgba(255,216,77,.3)}
.tabs{display:flex;gap:8px;padding:0 14px 12px}
.tab{flex:1;text-align:center;padding:9px 0;cursor:pointer;
font-family:'Orbitron','Noto Sans TC';font-size:.82rem;letter-spacing:2px;
color:#aebfd2;text-transform:uppercase;border:1px solid rgba(255,255,255,.2);
border-radius:999px;background:rgba(255,255,255,.04);transition:all .2s}
.tab:hover{border-color:rgba(0,255,178,.5);color:#d7e4f2}
.tab.on{color:#00ffb2;border-color:#00ffb2;background:rgba(0,255,178,.1);
box-shadow:0 0 12px rgba(0,255,178,.25)}
.panel{display:none;padding:16px 18px 14px}
.panel.on{display:block}
/* donuts */
.drow{display:flex;justify-content:center;gap:36px;margin-bottom:14px}
.donut{text-align:center}
.donut svg{display:block;margin:0 auto}
.dl{color:#8fa6bd;font-size:.84rem;margin-top:4px}
.dv{font-family:'Orbitron';font-size:.88rem}
.dv.h{fill:#ffd84d;color:#ffd84d}.dv.a{fill:#00aaff;color:#00aaff}
/* bars */
.row{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:.86rem}
.val{font-family:'Orbitron';min-width:30px;text-align:center}
.val.h{color:#ffd84d}.val.a{color:#00aaff}
.lbl{min-width:84px;text-align:center;color:#9db3ca;font-size:.86rem}
.bar{flex:1;height:9px;background:rgba(255,255,255,.06);border-radius:999px;
overflow:hidden;display:flex}
.bh{background:linear-gradient(90deg,#ffd84d,#cc9900);height:100%;
margin-left:auto;border-radius:999px 0 0 999px}
.ba{background:linear-gradient(90deg,#00aaff,#0066aa);height:100%;
border-radius:0 999px 999px 0}
/* events */
.ev{display:flex;align-items:center;gap:10px;padding:8px 4px;
border-bottom:1px solid rgba(255,255,255,.05);font-size:.96rem}
.ev:last-child{border-bottom:none}
.ev .min{font-family:'Orbitron';color:#4f9fd8;min-width:38px;font-size:.88rem}
.ev.h{justify-content:flex-start}.ev.a{flex-direction:row-reverse;text-align:right}
.ev.a .min{text-align:right}
/* pitch */
.fl{display:flex;justify-content:space-between;color:#7d93ab;
font-size:.78rem;margin-bottom:4px}
.fl b.h{color:#ffd84d}.fl b.a{color:#00aaff}
svg.pitch{width:100%;display:block;margin:0 auto}
.note{color:#8fa6bd;font-size:.76rem;text-align:center;padding:0 14px 12px}
@media(max-width:600px){.drow{gap:18px}.lbl{min-width:64px}}
</style></head><body>
<div class="card">
  <div class="badge">__BADGE__</div>
  <div class="wm"><span>DEMO</span></div>
  <div class="hdr">
    <div class="team h">__HFLAG__<div>__HOME__</div></div>
    <div class="mid"><div class="dt">__DATE__</div><div class="sc">&ndash;</div>
      <div class="st">__STATUS__</div></div>
    <div class="team a">__AFLAG__<div>__AWAY__</div></div>
  </div>
  <div class="ven">🏟 __VENUE__</div>
  <div class="stadwrap" id="stadwrap"><img id="stad" alt=""
       onerror="this.parentElement.style.display='none'"></div>
  <div class="hint">__TAB_HINT__</div>
  <div class="tabs">
    <div class="tab" data-p="pEv">__T_EV__</div>
    <div class="tab on" data-p="pSt">__T_ST__</div>
    <div class="tab" data-p="pLu">__T_LU__</div>
  </div>
  <div class="panel" id="pEv">
    <div class="ev h"><span class="min">23'</span><span>⚽ __HOME__ — __EV_GOAL__</span></div>
    <div class="ev a"><span class="min">41'</span><span>🟨 __AWAY__ — __EV_YEL__</span></div>
    <div class="ev h"><span class="min">58'</span><span>🔄 __HOME__ — __EV_SUB__</span></div>
    <div class="ev a"><span class="min">76'</span><span>⚽ __AWAY__ — __EV_GOAL__</span></div>
  </div>
  <div class="panel on" id="pSt">
    <div class="drow">
      <div class="donut">
        <svg width="76" height="76" viewBox="0 0 76 76">
          <circle cx="38" cy="38" r="30" fill="none"
                  stroke="rgba(255,255,255,.07)" stroke-width="8"/>
          <circle cx="38" cy="38" r="30" fill="none" stroke="#ffd84d"
                  stroke-width="8" stroke-linecap="round"
                  stroke-dasharray="109.3 188.5" transform="rotate(-90 38 38)"/>
          <text x="38" y="43" text-anchor="middle" class="dv h"
                font-size="15" font-family="Orbitron">58%</text>
        </svg><div class="dl">__HOME__ __S_POSS__</div>
      </div>
      <div class="donut">
        <svg width="76" height="76" viewBox="0 0 76 76">
          <circle cx="38" cy="38" r="30" fill="none"
                  stroke="rgba(255,255,255,.07)" stroke-width="8"/>
          <circle cx="38" cy="38" r="30" fill="none" stroke="#00aaff"
                  stroke-width="8" stroke-linecap="round"
                  stroke-dasharray="79.2 188.5" transform="rotate(-90 38 38)"/>
          <text x="38" y="43" text-anchor="middle" class="dv a"
                font-size="15" font-family="Orbitron">42%</text>
        </svg><div class="dl">__AWAY__ __S_POSS__</div>
      </div>
    </div>
    <div class="row"><div class="val h">12</div>
      <div class="bar"><div class="bh" style="width:63%"></div></div>
      <div class="lbl">__S_SHOTS__</div>
      <div class="bar"><div class="ba" style="width:37%"></div></div>
      <div class="val a">7</div></div>
    <div class="row"><div class="val h">5</div>
      <div class="bar"><div class="bh" style="width:62%"></div></div>
      <div class="lbl">__S_SOT__</div>
      <div class="bar"><div class="ba" style="width:38%"></div></div>
      <div class="val a">3</div></div>
    <div class="row"><div class="val h">6</div>
      <div class="bar"><div class="bh" style="width:60%"></div></div>
      <div class="lbl">__S_CORN__</div>
      <div class="bar"><div class="ba" style="width:40%"></div></div>
      <div class="val a">4</div></div>
    <div class="row"><div class="val h">9</div>
      <div class="bar"><div class="bh" style="width:45%"></div></div>
      <div class="lbl">__S_FOUL__</div>
      <div class="bar"><div class="ba" style="width:55%"></div></div>
      <div class="val a">11</div></div>
  </div>
  <div class="panel" id="pLu">
    <div class="fl"><b class="h">__HOME__ · 4-3-3</b><b class="a">4-4-2 · __AWAY__</b></div>
    <svg class="pitch" viewBox="0 0 700 330">
      <defs>
        <path id="sh" d="M -12,-11 L -5,-15 Q 0,-11 5,-15 L 12,-11 L 8,-4
                         L 6,-6 L 6,12 L -6,12 L -6,-6 L -8,-4 Z"/>
      </defs>
      <rect x="0" y="0" width="700" height="330" rx="10" fill="#15672f"/>
      <g fill="#1a7a39">
        <rect x="0" y="0" width="100" height="330"/>
        <rect x="200" y="0" width="100" height="330"/>
        <rect x="400" y="0" width="100" height="330"/>
        <rect x="600" y="0" width="100" height="330"/>
      </g>
      <g fill="none" stroke="rgba(255,255,255,.75)" stroke-width="2">
        <rect x="8" y="8" width="684" height="314"/>
        <line x1="350" y1="8" x2="350" y2="322"/>
        <circle cx="350" cy="165" r="44"/>
        <rect x="8" y="95" width="72" height="140"/>
        <rect x="620" y="95" width="72" height="140"/>
        <rect x="8" y="135" width="28" height="60"/>
        <rect x="664" y="135" width="28" height="60"/>
      </g>
      <circle cx="350" cy="165" r="3" fill="rgba(255,255,255,.75)"/>
      <circle cx="62" cy="165" r="2.5" fill="rgba(255,255,255,.75)"/>
      <circle cx="638" cy="165" r="2.5" fill="rgba(255,255,255,.75)"/>
      <g id="L"></g><g id="R"></g>
    </svg>
    <div class="note" style="padding:8px 0 0">__LU_NOTE__</div>
  </div>
  <div class="note">__NOTE__</div>
</div>
<script>
document.querySelectorAll('.tab').forEach(function(t){
  t.onclick=function(){
    document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.panel').forEach(function(x){x.classList.remove('on');});
    t.classList.add('on');
    document.getElementById(t.dataset.p).classList.add('on');};});
var NS="http://www.w3.org/2000/svg";
var L=[[42,165],[115,62],[115,132],[115,198],[115,268],[200,90],[200,165],
[200,240],[285,62],[298,165],[285,268]];
var R=[[658,165],[585,62],[585,132],[585,198],[585,268],[508,62],[508,132],
[508,198],[508,268],[432,122],[432,208]];
var CL=["GK","LB","CB","CB","RB","CM","CM","CM","LW","ST","RW"];
var CR=["GK","RB","CB","CB","LB","RM","CM","CM","LM","ST","ST"];
var NUM=[1,3,4,5,2,8,6,10,11,9,7];
function shirts(arr,codes,g,fill,numfill){
  arr.forEach(function(p,i){
    var u=document.createElementNS(NS,'use');
    u.setAttribute('href','#sh');
    u.setAttribute('transform','translate('+p[0]+','+p[1]+')');
    u.setAttribute('fill',fill);u.setAttribute('stroke','#0a121e');
    u.setAttribute('stroke-width','1.2');g.appendChild(u);
    var n=document.createElementNS(NS,'text');
    n.setAttribute('x',p[0]);n.setAttribute('y',p[1]+6);
    n.setAttribute('text-anchor','middle');n.setAttribute('font-size','11');
    n.setAttribute('font-weight','700');n.setAttribute('fill',numfill);
    n.textContent=NUM[i];g.appendChild(n);
    var t=document.createElementNS(NS,'text');
    t.setAttribute('x',p[0]);t.setAttribute('y',p[1]+26);
    t.setAttribute('text-anchor','middle');t.setAttribute('font-size','10.5');
    t.setAttribute('font-weight','700');t.setAttribute('fill','#ffffff');
    t.setAttribute('style','paint-order:stroke;stroke:#0a3018;stroke-width:3px');
    t.textContent=codes[i];g.appendChild(t);});}
shirts(L,CL,document.getElementById('L'),'#ffd84d','#0a121e');
shirts(R,CR,document.getElementById('R'),'#0a84ff','#eaf4ff');
var V="__VENUE_NAME__";
if(V){
  fetch("https://en.wikipedia.org/api/rest_v1/page/summary/"
        +encodeURIComponent(V.replace(/ /g,"_")))
  .then(function(r){return r.json();})
  .then(function(j){
    var u=(j.originalimage&&j.originalimage.source)
          ||(j.thumbnail&&j.thumbnail.source);
    if(u){document.getElementById('stad').src=u;
      document.getElementById('stadwrap').style.display='block';}})
  .catch(function(){});}
</script></body></html>
"""


def demo_preview_panel(fx: dict):
    zh = st.session_state.get("lang", "中文") == "中文"
    home, away = fx["home"], fx["away"]
    try:
        ko = datetime.fromisoformat(fx.get("date", "").replace("Z", "+00:00"))
        date_str = fmt_dt(ko, long=True)
    except Exception:
        date_str = ""
    html = (DEMO_HTML
            .replace("__HFLAG__", flag(home)).replace("__AFLAG__", flag(away))
            .replace("__HOME__", home).replace("__AWAY__", away)
            .replace("__DATE__", date_str)
            .replace("__VENUE__", fx.get("venue", ""))
            .replace("__VENUE_NAME__",
                     fx.get("venue_name", "").replace('"', ""))
            .replace("__BADGE__", "示意圖・開賽後自動替換" if zh
                     else "DEMO · swaps to live at kick-off")
            .replace("__STATUS__", "尚未開賽" if zh else "NOT STARTED")
            .replace("__TAB_HINT__",
                     "👇 點擊下方按鈕切換：事件・統計・陣容" if zh else
                     "👇 Tap a button below: Events · Statistics · Lineups")
            .replace("__LU_NOTE__",
                     "陣型與位置為風格檔案示意——正式名單於開賽前公布，屆時自動帶入真實球員。"
                     if zh else
                     "Formation shown from style profiles — official lineups "
                     "load automatically once announced.")
            .replace("__T_EV__", "事件" if zh else "Events")
            .replace("__T_ST__", "統計" if zh else "Statistics")
            .replace("__T_LU__", "陣容" if zh else "Lineups")
            .replace("__S_POSS__", "控球率" if zh else "Possession")
            .replace("__S_SHOTS__", "射門" if zh else "Shots")
            .replace("__S_SOT__", "射正" if zh else "On target")
            .replace("__S_CORN__", "角球" if zh else "Corners")
            .replace("__S_FOUL__", "犯規" if zh else "Fouls")
            .replace("__EV_GOAL__", "進球（示意）" if zh else "Goal (sample)")
            .replace("__EV_YEL__", "黃牌（示意）" if zh else "Yellow (sample)")
            .replace("__EV_SUB__", "換人（示意）" if zh else "Sub (sample)")
            .replace("__NOTE__",
                     "⚠️ 以上為版面示意、數字為樣本——開賽後本區自動替換為官方即時數據。"
                     if zh else
                     "⚠️ Layout preview with sample numbers — replaced by "
                     "official live data at kick-off."))
    components.html(html, height=700, scrolling=False)


def apisports_widget_panel():
    zh = st.session_state.get("lang", "中文") == "中文"
    try:
        wkey = (st.secrets.get("APIFOOTBALL_WIDGET_KEY", "")
                or st.secrets.get("API_FOOTBALL_WIDGET_KEY", ""))
        # free API-Football plans only expose seasons 2021-2023.
        # Set APIFOOTBALL_WIDGET_SEASON="2022" in secrets to preview the
        # widget with WC2022 data before upgrading; remove it once on Pro.
        wseason = st.secrets.get("APIFOOTBALL_WIDGET_SEASON", "2026")
    except Exception:
        wkey, wseason = "", "2026"
    section("MATCH CENTER",
            "📺 賽事中心 — 進行中／即將開賽自動釘選"
            if zh else "📺 Match centre — live & next match auto-pinned")
    if not wkey:
        st.info("在 Streamlit secrets 加入 `APIFOOTBALL_WIDGET_KEY = \"...\"`"
                "（API-SPORTS 後台 Widget Builder 的專用 key）即可啟用。"
                if zh else
                "Add `APIFOOTBALL_WIDGET_KEY = \"...\"` (the dedicated key "
                "from the API-SPORTS Widget Builder) to Streamlit secrets "
                "to enable.")
        return

    widget_js = ('<script type="module" '
                 'src="https://widgets.api-sports.io/2.0.3/widgets.js">'
                 '</script>')

    # --- auto-pin: all live games, else the next upcoming game -------------
    dkey = get_apif_data_key()
    fixtures, live_mode, fetch_err = [], False, None
    if dkey:
        try:
            fixtures = apif_live_fixtures(dkey)
            live_mode = bool(fixtures)
            if not fixtures:
                fixtures = apif_next_fixtures(dkey, 1)
        except Exception as e:  # noqa: BLE001
            fetch_err = str(e)

    if fixtures:
        cap = (("🔴 進行中——數據即時更新" if live_mode else "⏳ 下一場——開賽後自動切換")
               if zh else
               ("🔴 LIVE — stats updating" if live_mode
                else "⏳ Next match — switches automatically at kick-off"))
        st.caption(cap)
        if live_mode:
            for fx in fixtures[:3]:  # at most 3 simultaneous games
                game_html = f"""
                <div id="wg-api-football-game"
                     data-host="v3.football.api-sports.io"
                     data-key="{wkey}"
                     data-id="{fx['id']}"
                     data-theme="dark"
                     data-refresh="60"
                     data-show-errors="false"
                     data-show-logos="true">
                </div>
                {widget_js}
                """
                components.html(game_html, height=780, scrolling=True)
        else:
            # pre-match: themed demo widget only (official one renders
            # almost empty before kick-off and leaves a huge gap)
            demo_preview_panel(fixtures[0])
    elif not dkey:
        st.info("再加 `APIFOOTBALL_KEY = \"...\"`（資料用主 key）即可自動釘選"
                "進行中／下一場比賽的完整數據。" if zh else
                "Also add `APIFOOTBALL_KEY = \"...\"` (your main data key) "
                "to auto-pin the live / next match detail.")
    elif fetch_err:
        st.warning(f"API-Football: {fetch_err}")
    else:
        st.info("目前查無進行中或即將開賽的場次（免費方案查不到 2026 球季——"
                "升級後自動恢復）。" if zh else
                "No live or upcoming fixtures found (free plans cannot query "
                "season 2026 — resolves after upgrading).")


def full_schedule_panel():
    """Full schedule list — rendered at the very bottom of the page."""
    zh = st.session_state.get("lang", "中文") == "中文"
    try:
        wkey = (st.secrets.get("APIFOOTBALL_WIDGET_KEY", "")
                or st.secrets.get("API_FOOTBALL_WIDGET_KEY", ""))
        wseason = st.secrets.get("APIFOOTBALL_WIDGET_SEASON", "2026")
    except Exception:
        return
    if not wkey:
        return
    with st.expander("📋 完整賽程列表" if zh else "📋 Full schedule", False):
        list_html = f"""
        <div id="wg-api-football-games"
             data-host="v3.football.api-sports.io"
             data-key="{wkey}"
             data-league="1"
             data-season="{wseason}"
             data-theme="dark"
             data-refresh="60"
             data-show-toolbar="true"
             data-show-errors="false"
             data-show-logos="true"
             data-modal-game="true"
             data-modal-standings="true"
             data-modal-show-logos="true">
        </div>
        <script type="module"
                src="https://widgets.api-sports.io/2.0.3/widgets.js"></script>
        """
        components.html(list_html, height=700, scrolling=True)


# fallback: opening match — Mexico City, 11 Jun 2026 20:00 local (UTC-6)
OPENING_UTC = "2026-06-12T02:00:00Z"


def clock_panel(next_match=None):
    zh = st.session_state.get("lang", "中文") == "中文"
    if next_match:
        target = next_match["utcDate"]
        h, a = next_match["homeTeam"]["name"], next_match["awayTeam"]["name"]
        match_lbl = f"{h} vs {a}"
    else:
        target = OPENING_UTC
        match_lbl = "揭幕戰・墨西哥城" if zh else "Opening match · Mexico City"
    html = (CLOCK_HTML
            .replace("__TARGET__", target)
            .replace("__MATCH__", match_lbl)
            .replace("__CD_TITLE__", "⏳ 距離下一場開賽" if zh else "⏳ Next kickoff in")
            .replace("__D__", "天" if zh else "DAYS")
            .replace("__H__", "時" if zh else "HRS")
            .replace("__M__", "分" if zh else "MIN")
            .replace("__S__", "秒" if zh else "SEC")
            .replace("__KICKOFF__", "比賽進行中 ⚽" if zh else "KICK-OFF! ⚽")
            .replace("__WC_TITLE__", "🌍 主辦地現在時間" if zh else "🌍 Host-city time now")
            .replace("__C1__", "台北" if zh else "Taipei")
            .replace("__C2__", "墨西哥城" if zh else "Mexico City")
            .replace("__C3__", "紐約" if zh else "New York")
            .replace("__C4__", "洛杉磯" if zh else "Los Angeles"))
    components.html(html, height=150, scrolling=False)


def flow_panel():
    st.markdown(f'<span class="section-tag">SYSTEM FLOW</span>'
                f'<div class="sec-h">{L("flow_title")}</div>',
                unsafe_allow_html=True)
    components.html(ANIM_HTML, height=560, scrolling=False)


# ----------------------------------------------------------------------------
# UI sections
# ----------------------------------------------------------------------------
def section(tag: str, title: str, live: bool = False):
    dot = '<span class="live-dot"></span>' if live else ""
    st.markdown(f'<span class="section-tag">{dot}{tag}</span>'
                f'<div class="sec-h">{title}</div>', unsafe_allow_html=True)


def hero():
    now = datetime.now(timezone.utc).astimezone(TPE).strftime(
        "%d %b %Y · %H:%M") + " TPE"
    visits = visitor_count()
    vbadge = (f' &nbsp;·&nbsp; <span style="color:#00ffb2">👥 '
              f'{visits:,} visits</span>' if visits else "")
    st.markdown(
        f"""<div class="hero"><h1>⚽ WC26 // AGENT</h1>
        <p>Autonomous World Cup 2026 intelligence — live scores · standings ·
        AI winner projection · prediction-market odds &nbsp;|&nbsp;
        {flag('USA', True)} {flag('Mexico', True)} {flag('Canada', True)}
        United 2026 &nbsp;·&nbsp; last sync {now}{vbadge}</p>
        <div class="byline">★ David Lau World Cup Vision // WC26 AI Agent
        Supportive ★</div></div>""",
        unsafe_allow_html=True)


def stat_strip(live_n: int, today_n: int, fav: str, fav_p: float):
    days_left = max((FINAL_DATE - datetime.now(timezone.utc)).days, 0)
    live_html = (f'<span class="live-dot"></span>{live_n}' if live_n
                 else f'<span style="color:#7d93ab">{L("none")}</span>')
    st.markdown(
        f"""<div class="stats">
        <div class="stat"><div class="lbl">{L("live_now")}</div>
            <div class="val">{live_html}</div></div>
        <div class="stat"><div class="lbl">{L("today")}</div>
            <div class="val">{today_n}</div></div>
        <div class="stat"><div class="lbl">{L("market_fav")}</div>
            <div class="val" style="font-size:1.15rem">{flag(fav)} {fav}
            <span style="color:#4f9fd8;font-size:.95rem">{fav_p*100:.1f}%</span>
            </div></div>
        <div class="stat"><div class="lbl">{L("days_final")}</div>
            <div class="val">{days_left}<span style="font-size:.85rem;
            color:#7d93ab">{L("final_sub")}</span></div></div>
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
        meta = (f'<span class="st-live"><span class="live-dot"></span>'
                f'{L("live_lbl")}' + (L("ht") if status == "PAUSED" else "")
                + "</span>")
    elif status == "FINISHED":
        score, meta = f"{hs} : {as_}", L("ft")
    else:
        score = "—"
        meta = fmt_dt(when)

    st.markdown(
        f"""<div class="match-card">
        <div class="mc-team home">{home} {flag(home)}</div>
        <div class="mc-score">{score}</div>
        <div class="mc-team">{flag(away)} {away}</div>
        <div class="mc-meta">{meta}<br>{stage}</div></div>""",
        unsafe_allow_html=True)


def prediction_panel(blend: list):
    section("AI PROJECTION", L("pick_title"))
    if not blend:
        st.info(L("pick_warm"))
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
        <div class="big-pick"><div class="pre">{L("projected")}</div>
            <div class="team">{flag(top[0])} {top[0].upper()} 🏆</div>
            <div class="conf">{L("conf").format(c=f"{conf:.0f}")}</div>
        </div>
        <div class="podium">{pods}</div>
        <div class="method">
            <div class="m-lbl"><span>{L("blend_t")}</span><span></span></div>
            <div class="m-bar"><div class="m-odds"></div><div class="m-form"></div></div>
            <div class="m-lbl"><span>{L("blend_o")}</span>
            <span>{L("blend_f")}</span></div>
        </div></div>""", unsafe_allow_html=True)


def odds_panel(odds: list, source_live: bool):
    tag = "POLYMARKET · LIVE" if source_live else "POLYMARKET · SNAPSHOT"
    section(tag, L("odds_title"))
    top = odds[:10]
    max_p = top[0][1] if top else 1
    rows = ""
    for i, (team, p, _tid) in enumerate(top, 1):
        rows += (f'<div class="odds-row"><div class="odds-rank">#{i:02d}</div>'
                 f'<div class="odds-team">{flag(team, True)} {team}</div>'
                 f'<div class="odds-bar-bg"><div class="odds-bar" '
                 f'style="width:{p/max_p*100:.1f}%"></div></div>'
                 f'<div class="odds-pct">{p*100:.1f}%</div></div>')
    st.markdown(f'<div class="glass">{rows}</div>', unsafe_allow_html=True)
    st.caption(L("odds_caption"))


def trend_panel(odds: list):
    top5 = [(t, p, tid) for t, p, tid in odds[:5] if tid]
    if not top5:
        return  # fallback odds have no token ids — skip silently
    data = {}
    for team, _p, tid in top5:
        for ts, prob in fetch_odds_history(tid):
            data.setdefault(ts, {})[team] = round(prob * 100, 2)
    if not data:
        return
    section("ODDS HISTORY", L("trend_title"))
    df = pd.DataFrame.from_dict(data, orient="index").sort_index()
    df.index = df.index.tz_convert("Asia/Taipei") if df.index.tz \
        else df.index
    long = (df.reset_index().rename(columns={"index": "time"})
            .melt("time", var_name="team", value_name="prob"))
    palette = ["#00ffb2", "#00aaff", "#ffd84d", "#ff6b87", "#b07cff"]
    axis_kw = dict(labelColor="#7d93ab", titleColor="#7d93ab",
                   gridColor="rgba(255,255,255,.07)",
                   domainColor="rgba(255,255,255,.25)",
                   tickColor="rgba(255,255,255,.25)")
    chart = (
        alt.Chart(long)
        .mark_line(strokeWidth=2.5, interpolate="monotone")
        .encode(
            x=alt.X("time:T", axis=alt.Axis(title=None, format="%m/%d",
                                            **axis_kw)),
            y=alt.Y("prob:Q", axis=alt.Axis(title="%", **axis_kw),
                    scale=alt.Scale(zero=False)),
            color=alt.Color(
                "team:N",
                scale=alt.Scale(range=palette),
                legend=alt.Legend(title=None, orient="top",
                                  labelColor="#d7e4f2", labelFontSize=13)),
            tooltip=[alt.Tooltip("time:T", format="%m/%d %H:%M"),
                     alt.Tooltip("team:N"),
                     alt.Tooltip("prob:Q", format=".1f")],
        )
        .properties(height=320, background="transparent")
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(L("trend_caption"))


# ----------------------------------------------------------------------------
# 🏆 AI Prediction Showdown — Gemini vs ChatGPT vs Claude
# Scoring: exact score = 3 pts · correct outcome (W/D/L) = 1 pt · miss = 0
# Gemini/ChatGPT predictions supplied by the site owner (2026-06-11);
# Claude predictions generated by this site's model.
# ----------------------------------------------------------------------------
AI_MODELS = [("g", "Gemini", "🔷", "#4e8cff"),
             ("c", "ChatGPT", "🟢", "#10c98d"),
             ("a", "Claude", "⭐", "#ffb13d")]

SHOWDOWN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Noto+Sans+TC:wght@400;500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
body{background:transparent;color:#d7e4f2;font-family:'Noto Sans TC',sans-serif;
overflow:hidden;position:relative}
.p{position:absolute;border-radius:50%;pointer-events:none;opacity:.5}
@keyframes drift1{0%,100%{transform:translate(0,0)}50%{transform:translate(40px,-22px)}}
@keyframes drift2{0%,100%{transform:translate(0,0)}50%{transform:translate(-35px,18px)}}
@keyframes drift3{0%,100%{transform:translate(0,0)}50%{transform:translate(22px,26px)}}
.hdwrap{text-align:center;padding-top:6px}
.tag{display:inline-block;font-family:'Orbitron','Noto Sans TC';font-size:.8rem;
letter-spacing:3px;color:#ffd84d;border:1px solid rgba(255,216,77,.5);
border-radius:999px;padding:5px 22px;
animation:tagPulse 2.4s ease-in-out infinite}
@keyframes tagPulse{0%,100%{box-shadow:0 0 10px rgba(255,216,77,.15)}
50%{box-shadow:0 0 26px rgba(255,216,77,.5)}}
.title{font-family:'Orbitron','Noto Sans TC';font-size:1.8rem;margin-top:10px;
background:linear-gradient(90deg,#4e8cff,#10c98d,#ffb13d,#4e8cff);
background-size:300% 100%;-webkit-background-clip:text;
-webkit-text-fill-color:transparent;animation:shimmer 6s linear infinite}
@keyframes shimmer{0%{background-position:0% 0}100%{background-position:300% 0}}
.sub{color:#8fa6bd;font-size:.95rem;margin:6px 0 16px}
.cards{display:flex;gap:14px;justify-content:center;flex-wrap:nowrap;
padding:0 8px 14px}
.lbcard{flex:1;max-width:250px;min-width:170px;text-align:center;
padding:18px 10px;border-radius:16px;background:rgba(10,18,30,.75);
border:1.5px solid var(--c);opacity:0;
animation:rise .7s cubic-bezier(.2,.8,.3,1.2) forwards,
glow 3s ease-in-out infinite}
@keyframes rise{from{opacity:0;transform:translateY(26px) scale(.92)}
to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes glow{0%,100%{box-shadow:0 0 10px color-mix(in srgb,var(--c) 25%,transparent)}
50%{box-shadow:0 0 28px color-mix(in srgb,var(--c) 55%,transparent)}}
.nm{font-size:1.1rem;font-weight:700;color:var(--c)}
.crown{display:inline-block;animation:bob 1.8s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-6deg)}
50%{transform:translateY(-5px) rotate(8deg)}}
.pts{font-family:'Orbitron';font-size:2.3rem;color:var(--c);margin:6px 0;
text-shadow:0 0 16px color-mix(in srgb,var(--c) 60%,transparent)}
.dl{color:#8fa6bd;font-size:.84rem}
@media(max-width:680px){body{zoom:.78}}
@media(max-width:520px){body{zoom:.62}}
@media(max-width:400px){body{zoom:.5}}
</style></head><body>
<div class="p" style="width:5px;height:5px;background:#4e8cff;top:18%;left:6%;
animation:drift1 7s ease-in-out infinite"></div>
<div class="p" style="width:4px;height:4px;background:#10c98d;top:60%;left:14%;
animation:drift2 9s ease-in-out infinite"></div>
<div class="p" style="width:6px;height:6px;background:#ffb13d;top:30%;left:88%;
animation:drift3 8s ease-in-out infinite"></div>
<div class="p" style="width:4px;height:4px;background:#ffd84d;top:72%;left:80%;
animation:drift1 10s ease-in-out infinite"></div>
<div class="p" style="width:5px;height:5px;background:#00ffb2;top:8%;left:55%;
animation:drift2 11s ease-in-out infinite"></div>
<div class="hdwrap">
  <span class="tag">🏆 AI SHOWDOWN</span>
  <div class="title">__TITLE__</div>
  <div class="sub">__SUB__</div>
</div>
<div class="cards">__CARDS__</div>
<script>
document.querySelectorAll('.pts').forEach(function(el){
  var v=+el.dataset.v, t0=null;
  function step(ts){
    if(!t0)t0=ts;
    var k=Math.min((ts-t0)/1400,1);
    k=1-Math.pow(1-k,3);
    el.textContent=Math.round(v*k);
    if(k<1)requestAnimationFrame(step);}
  requestAnimationFrame(step);});
</script></body></html>
"""

# (home, away, gemini, chatgpt, claude)
AI_PRED = {
 "A": [("Mexico", "South Africa", (2, 1), (2, 0), (2, 0)),
       ("South Korea", "Czechia", (1, 1), (1, 1), (2, 1)),
       ("Czechia", "South Africa", (2, 0), (1, 0), (2, 1)),
       ("Mexico", "South Korea", (2, 1), (1, 1), (2, 1)),
       ("South Africa", "South Korea", (1, 2), (0, 2), (0, 1)),
       ("Czechia", "Mexico", (1, 1), (1, 2), (1, 1))],
 "B": [("Canada", "Bosnia & Herzegovina", (2, 0), (2, 1), (2, 0)),
       ("Qatar", "Switzerland", (0, 2), (0, 2), (0, 2)),
       ("Switzerland", "Bosnia & Herzegovina", (1, 0), (2, 0), (2, 1)),
       ("Canada", "Qatar", (3, 1), (2, 0), (3, 0)),
       ("Switzerland", "Canada", (1, 1), (1, 1), (2, 1)),
       ("Bosnia & Herzegovina", "Qatar", (2, 1), (1, 1), (2, 0))],
 "C": [("Brazil", "Morocco", (3, 0), (2, 1), (2, 0)),
       ("Haiti", "Scotland", (0, 2), (1, 2), (0, 1)),
       ("Brazil", "Haiti", (4, 0), (3, 0), (3, 0)),
       ("Scotland", "Morocco", (1, 1), (1, 2), (0, 1)),
       ("Scotland", "Brazil", (0, 2), (0, 2), (1, 2)),
       ("Morocco", "Haiti", (2, 0), (2, 0), (3, 0))],
 "D": [("USA", "Paraguay", (2, 0), (2, 1), (1, 0)),
       ("Australia", "Türkiye", (1, 1), (1, 2), (0, 1)),
       ("Türkiye", "Paraguay", (2, 1), (1, 1), (2, 0)),
       ("USA", "Australia", (2, 1), (2, 0), (2, 1)),
       ("Türkiye", "USA", (1, 2), (1, 1), (2, 2)),
       ("Paraguay", "Australia", (0, 1), (1, 1), (1, 0))],
 "E": [("Ivory Coast", "Ecuador", (1, 2), (1, 1), (1, 1)),
       ("Germany", "Curaçao", (3, 0), (4, 0), (5, 0)),
       ("Germany", "Ivory Coast", (2, 1), (2, 0), (1, 0)),
       ("Ecuador", "Curaçao", (2, 0), (2, 0), (3, 0)),
       ("Curaçao", "Ivory Coast", (1, 2), (0, 2), (0, 1)),
       ("Ecuador", "Germany", (1, 2), (1, 2), (0, 1))],
 "F": [("Netherlands", "Japan", (2, 0), (2, 1), (1, 1)),
       ("Sweden", "Tunisia", (2, 1), (1, 0), (1, 1)),
       ("Netherlands", "Sweden", (1, 1), (2, 1), (2, 0)),
       ("Tunisia", "Japan", (0, 1), (1, 1), (0, 2)),
       ("Japan", "Sweden", (2, 2), (1, 1), (1, 0)),
       ("Tunisia", "Netherlands", (0, 3), (0, 2), (1, 2))],
 "G": [("Belgium", "Egypt", (2, 0), (2, 1), (1, 0)),
       ("Iran", "New Zealand", (1, 1), (1, 0), (2, 0)),
       ("Belgium", "Iran", (3, 1), (2, 0), (2, 1)),
       ("New Zealand", "Egypt", (1, 2), (0, 2), (1, 1)),
       ("New Zealand", "Belgium", (0, 2), (0, 3), (1, 2)),
       ("Egypt", "Iran", (1, 0), (1, 1), (1, 0))],
 "H": [("Spain", "Cape Verde", (3, 0), (3, 0), (4, 0)),
       ("Saudi Arabia", "Uruguay", (0, 2), (1, 2), (0, 1)),
       ("Uruguay", "Cape Verde", (3, 0), (2, 0), (2, 0)),
       ("Spain", "Saudi Arabia", (2, 0), (3, 1), (3, 0)),
       ("Uruguay", "Spain", (1, 1), (1, 2), (0, 2)),
       ("Cape Verde", "Saudi Arabia", (1, 1), (1, 1), (1, 0))],
 "I": [("France", "Senegal", (2, 0), (2, 1), (2, 1)),
       ("Iraq", "Norway", (0, 2), (0, 2), (1, 3)),
       ("France", "Iraq", (3, 0), (3, 0), (4, 0)),
       ("Norway", "Senegal", (1, 1), (2, 2), (2, 1)),
       ("Norway", "France", (1, 3), (1, 2), (0, 2)),
       ("Senegal", "Iraq", (2, 0), (2, 0), (3, 0))],
 "J": [("Argentina", "Algeria", (3, 0), (2, 0), (2, 0)),
       ("Austria", "Jordan", (2, 0), (2, 0), (1, 0)),
       ("Argentina", "Austria", (2, 0), (2, 1), (3, 1)),
       ("Jordan", "Algeria", (1, 2), (0, 2), (0, 1)),
       ("Algeria", "Austria", (1, 1), (1, 2), (0, 1)),
       ("Jordan", "Argentina", (0, 4), (0, 3), (0, 2))],
 "K": [("Portugal", "DR Congo", (3, 0), (3, 1), (4, 1)),
       ("Uzbekistan", "Colombia", (1, 2), (0, 2), (0, 1)),
       ("Portugal", "Uzbekistan", (2, 0), (2, 0), (3, 0)),
       ("Colombia", "DR Congo", (2, 1), (2, 1), (3, 1)),
       ("Colombia", "Portugal", (2, 2), (1, 2), (1, 1)),
       ("DR Congo", "Uzbekistan", (1, 1), (1, 0), (0, 0))],
 "L": [("England", "Croatia", (2, 1), (1, 1), (2, 0)),
       ("Ghana", "Panama", (2, 0), (2, 1), (1, 0)),
       ("England", "Ghana", (3, 0), (2, 0), (2, 1)),
       ("Panama", "Croatia", (0, 2), (0, 2), (1, 2)),
       ("Croatia", "Ghana", (1, 0), (1, 1), (2, 0)),
       ("Panama", "England", (0, 4), (0, 3), (0, 2))],
}

TEAM_ALIAS = {
    "korea republic": "south korea", "czech republic": "czechia",
    "côte d'ivoire": "ivory coast", "cote d'ivoire": "ivory coast",
    "congo dr": "dr congo", "democratic republic of the congo": "dr congo",
    "united states": "usa", "cabo verde": "cape verde", "ir iran": "iran",
    "türkiye": "turkiye", "turkey": "turkiye", "curacao": "curaçao",
}


def norm_team(t: str) -> str:
    t = (t or "").lower().strip().replace(" and ", " & ")
    return TEAM_ALIAS.get(t, t)


def actual_results(finished: list) -> dict:
    out = {}
    for m in finished:
        ft = m.get("score", {}).get("fullTime", {})
        hs, as_ = ft.get("home"), ft.get("away")
        if hs is None or as_ is None:
            continue
        out[(norm_team(m["homeTeam"]["name"]),
             norm_team(m["awayTeam"]["name"]))] = (hs, as_)
    return out


def pred_points(pred: tuple, act: tuple) -> int:
    if pred == act:
        return 3
    sgn = lambda x: (x > 0) - (x < 0)  # noqa: E731
    return 1 if sgn(pred[0] - pred[1]) == sgn(act[0] - act[1]) else 0


def ai_competition_panel(finished: list):
    zh = st.session_state.get("lang", "中文") == "中文"
    results = actual_results(finished)

    # ---- settle every match & accumulate league table ----------------------
    table = {k: {"pts": 0, "exact": 0, "outcome": 0, "played": 0}
             for k, *_ in AI_MODELS}
    settled = {}  # (group, idx) -> (actual, {model: pts}, winners)
    for grp, matches in AI_PRED.items():
        for i, (h, a, pg, pc, pa) in enumerate(matches):
            act = results.get((norm_team(h), norm_team(a)))
            if act is None:
                rev = results.get((norm_team(a), norm_team(h)))
                act = (rev[1], rev[0]) if rev else None
            if act is None:
                continue
            preds = {"g": pg, "c": pc, "a": pa}
            pts = {k: pred_points(p, act) for k, p in preds.items()}
            best = max(pts.values())
            winners = {k for k, v in pts.items() if v == best and best > 0}
            settled[(grp, i)] = (act, pts, winners)
            for k, v in pts.items():
                table[k]["pts"] += v
                table[k]["played"] += 1
                if v == 3:
                    table[k]["exact"] += 1
                elif v == 1:
                    table[k]["outcome"] += 1

    # ---- animated header + leaderboard (iframe component) ------------------
    ranked = sorted(AI_MODELS, key=lambda m: -table[m[0]]["pts"])
    top_pts = table[ranked[0][0]]["pts"]
    cards = ""
    for i, (key, name, icon, color) in enumerate(ranked):
        t = table[key]
        crown = ('<span class="crown">👑</span>'
                 if (t["pts"] == top_pts and top_pts > 0) else "")
        if zh:
            detail = ("已結算 %d 場・全中 %d・猜中勝負 %d"
                      % (t["played"], t["exact"], t["outcome"]))
        else:
            detail = ("%d settled · %d exact · %d outcome"
                      % (t["played"], t["exact"], t["outcome"]))
        cards += (
            f'<div class="lbcard" style="--c:{color};'
            f'animation-delay:{i * .18}s,{i * .18}s;">'
            f'<div class="nm">{icon} {name} {crown}</div>'
            f'<div class="pts" data-v="{t["pts"]}">0</div>'
            f'<div class="dl">{detail}</div></div>')
    head_html = (SHOWDOWN_HTML
                 .replace("__TITLE__",
                          "AI 預測比分大對決" if zh
                          else "AI Score-Prediction Showdown")
                 .replace("__SUB__",
                          "Gemini vs ChatGPT vs Claude — 72 場小組賽全預測・"
                          "全中 3 分・猜中勝負 1 分" if zh else
                          "Gemini vs ChatGPT vs Claude — all 72 group games · "
                          "exact 3 pts · outcome 1 pt")
                 .replace("__CARDS__", cards))
    components.html(head_html, height=300, scrolling=False)

    # ---- per-group prediction rows ------------------------------------------
    tabs = st.tabs([f"Group {g}" for g in AI_PRED])
    for tab, (grp, matches) in zip(tabs, AI_PRED.items()):
        with tab:
            rows = ""
            for i, (h, a, pg, pc, pa) in enumerate(matches):
                preds = {"g": pg, "c": pc, "a": pa}
                s = settled.get((grp, i))
                chips = ""
                for key, name, icon, color in AI_MODELS:
                    p = preds[key]
                    win = s and key in s[2]
                    trophy = ' <span class="trophy">🏆</span>' if win else ""
                    border = (f"1.5px solid {color}" if win
                              else "1px solid rgba(255,255,255,.14)")
                    glow = f"box-shadow:0 0 10px {color}55;" if win else ""
                    chips += (
                        f'<div style="flex:1;min-width:92px;text-align:center;'
                        f'padding:6px 4px;border-radius:10px;{glow}'
                        f'background:rgba(255,255,255,.03);border:{border};">'
                        f'<div style="font-size:.72rem;color:{color};">'
                        f'{icon} {name}</div>'
                        f'<div style="font-family:\'Orbitron\';font-size:1.05rem;'
                        f'color:#d7e4f2;">{p[0]} - {p[1]}{trophy}</div></div>')
                if s:
                    act_html = (f'<span class="ft-flash" style="color:#00ffb2;'
                                f'font-family:'
                                f"'Orbitron'"
                                f';">{s[0][0]} - {s[0][1]}</span> '
                                f'<span class="kv">{"終場" if zh else "FT"}</span>')
                else:
                    act_html = (f'<span class="kv">'
                                f'{"未開賽" if zh else "not played"}</span>')
                rows += (
                    f'<div style="border-bottom:1px solid rgba(255,255,255,.06);'
                    f'padding:10px 0;">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;flex-wrap:wrap;gap:6px;">'
                    f'<div style="font-weight:700;font-size:1.02rem;">'
                    f'{flag(h, True)} {h} <span style="color:#4f9fd8">vs</span> '
                    f'{a} {flag(a, True)}</div><div>{act_html}</div></div>'
                    f'<div style="display:flex;gap:8px;margin-top:7px;'
                    f'flex-wrap:wrap;">{chips}</div></div>')
            st.markdown(f'<div class="glass">{rows}</div>',
                        unsafe_allow_html=True)
    st.caption(
        "Gemini／ChatGPT 預測由站長收集（2026-06-11）；Claude 預測由本站 AI 生成。"
        "純屬趣味競賽，不構成投注建議。" if zh else
        "Gemini/ChatGPT predictions collected by the site owner (2026-06-11); "
        "Claude predictions generated by this site's AI. For fun only — "
        "not betting advice.")


def next_match_panel(upcoming: list, odds_map: dict, rates: dict = None):
    section("NEXT UP", L("next_title"))
    if not upcoming:
        st.info(L("no_fixtures"))
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
        expect = L("exp_clear").format(fav=fav, dog=dog)
    elif edge > 0.015:
        expect = L("exp_slight").format(fav=fav, dog=dog)
    else:
        expect = L("exp_coin")
    when = datetime.fromisoformat(nxt["utcDate"].replace("Z", "+00:00"))
    stage = (nxt.get("group") or nxt.get("stage", "")).replace("_", " ").title()
    st.markdown(
        f"""<div class="glass">
        <div style="font-size:1.45rem;font-weight:700;">
            {flag(home)} {home} &nbsp;<span style="color:#4f9fd8">vs</span>&nbsp;
            {away} {flag(away)}</div>
        <div class="kv" style="margin-top:4px;">🗓
            <b>{fmt_dt(when, long=True)}</b> · {stage}</div>
        <p style="margin:10px 0 8px;font-size:1.05rem;">{expect}</p>
        <div class="kv">{L("title_odds").format(
            h=home, hp=f"{ph*100:.1f}", a=away, ap=f"{pa*100:.1f}")}</div>
        </div>""",
        unsafe_allow_html=True)

    # --- AI predicted score (Poisson model) --------------------------------
    zh = st.session_state.get("lang", "中文") == "中文"
    pred = predict_score(ph, pa, home, away, rates or {})
    sh, sa = pred["score"]
    lam_h, lam_a = pred["lam"]
    lbl = "AI 預測比分" if zh else "AI predicted score"
    wlbl, dlbl, llbl = ((f"{home} 勝", "和局", f"{away} 勝") if zh
                        else (f"{home} win", "Draw", f"{away} win"))
    meth = (f"Poisson 模型 · λ {lam_h:.2f} vs {lam_a:.2f} · 此比分出現機率 "
            f"{pred['p_score']*100:.0f}%" if zh else
            f"Poisson model · λ {lam_h:.2f} vs {lam_a:.2f} · scoreline "
            f"probability {pred['p_score']*100:.0f}%")
    st.markdown(
        f"""<div class="glass" style="text-align:center;">
        <span class="section-tag">🤖 {lbl}</span>
        <div style="font-family:'Orbitron';font-size:2.2rem;color:#00ffb2;
            text-shadow:0 0 18px rgba(0,255,178,.45);margin:6px 0;">
            {flag(home, True)} {sh} &nbsp;:&nbsp; {sa} {flag(away, True)}</div>
        <div style="display:flex;height:14px;border-radius:999px;
            overflow:hidden;margin:10px 8%;border:1px solid rgba(255,255,255,.1);">
          <div style="width:{pred['win']*100:.1f}%;
              background:linear-gradient(90deg,#ffd84d,#cc9900);"></div>
          <div style="width:{pred['draw']*100:.1f}%;
              background:rgba(255,255,255,.18);"></div>
          <div style="width:{pred['loss']*100:.1f}%;
              background:linear-gradient(90deg,#0066aa,#00aaff);"></div>
        </div>
        <div class="kv" style="display:flex;justify-content:space-between;
            margin:0 8%;">
          <span style="color:#ffd84d">{wlbl} {pred['win']*100:.0f}%</span>
          <span>{dlbl} {pred['draw']*100:.0f}%</span>
          <span style="color:#00aaff">{llbl} {pred['loss']*100:.0f}%</span>
        </div>
        <div class="kv" style="margin-top:8px;color:#51677e;">{meth}</div>
        </div>""",
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
    section("GROUP STAGE", L("standings_title"))
    tables = [s for s in standings.get("standings", [])
              if s.get("type") == "TOTAL"]
    if not tables:
        st.info(L("standings_info"))
        return
    tabs = st.tabs([s.get("group", f"G{i}").replace("GROUP_", "Group ")
                    for i, s in enumerate(tables)])
    for tab, s in zip(tabs, tables):
        with tab:
            st.markdown(standings_table_html(s.get("table", [])),
                        unsafe_allow_html=True)
    st.markdown(f'<div class="legend">{L("legend")}</div>',
                unsafe_allow_html=True)


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
    odds_map = {t: p for t, p, _tid in odds}

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

    nxt = upcoming[0] if upcoming else None
    if live:
        clock_panel(None if not upcoming else nxt)
    else:
        clock_panel(nxt)
    stat_strip(len(live), today_n, odds[0][0], odds[0][1])

    if not api_key:
        st.warning(L("warn_key"), icon="⚠️")
    elif api_err:
        st.error(f"football-data.org error: {api_err}")

    if live:
        section("LIVE NOW", L("live_title"), live=True)
        for m in live:
            match_card(m)
        st.caption(L("live_caption"))

    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        prediction_panel(blended_prediction(odds, table_strength(standings)))
    with c2:
        odds_panel(odds, odds_live)

    ai_competition_panel(finished)   # ⭐ AI showdown (replaces odds history)
    apisports_widget_panel()
    next_match_panel(upcoming, odds_map, team_goal_rates(standings))
    # tactics_panel(upcoming[0], odds_map)  # disabled — re-enable anytime
    standings_panel(standings)

    if finished:
        section("RESULTS", L("results_title"))
        for m in finished[:6]:
            match_card(m)

    full_schedule_panel()
    st.markdown(f'<p class="foot">{L("foot")}</p>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Page assembly
# ----------------------------------------------------------------------------
hero()
st.radio("language", ["中文", "EN"], horizontal=True,
         label_visibility="collapsed", key="lang")
flow_panel()
dashboard()
