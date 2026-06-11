"""
⚽ WC26 // AGENT — Telegram 進球通知小幫手
==========================================
獨立腳本，在你自己的電腦（或任何能跑 Python 的機器）上執行。
每 60 秒檢查一次世界盃賽況，發生以下事件時推播到你的 Telegram：

  🟢 比賽開始（kick-off）
  ⚽ 進球（任一方比分改變）
  🏁 比賽結束（終場比分）

安全須知（重要）：
  - 不要把 Token 寫死在程式碼裡、不要 commit 到 GitHub。
  - 一律用環境變數提供，外洩時立即到 @BotFather 撤換（/revoke）。

設定步驟：
  1. Telegram 搜尋 @BotFather → /newbot → 取得 BOT TOKEN
  2. 跟你的新 bot 說一句話，然後開
     https://api.telegram.org/bot<TOKEN>/getUpdates 找到你的 chat id
  3. 設定環境變數後執行：

     # Windows (PowerShell)
     $env:FOOTBALL_DATA_API_KEY="你的football-data金鑰"
     $env:TELEGRAM_BOT_TOKEN="你的bot token"
     $env:TELEGRAM_CHAT_ID="你的chat id"
     python telegram_alerts.py

     # macOS / Linux
     FOOTBALL_DATA_API_KEY=xxx TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=xxx \
         python telegram_alerts.py
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

FD_URL = "https://api.football-data.org/v4/competitions/WC/matches"
POLL_SECONDS = 60          # free tier: 10 req/min — 1 req/min is well within
TPE = timezone(timedelta(hours=8))

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def die(msg: str):
    print(f"[設定錯誤] {msg}")
    sys.exit(1)


if not API_KEY:
    die("缺少環境變數 FOOTBALL_DATA_API_KEY")
if not BOT_TOKEN:
    die("缺少環境變數 TELEGRAM_BOT_TOKEN")
if not CHAT_ID:
    die("缺少環境變數 TELEGRAM_CHAT_ID")


def send(text: str):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        if not r.ok:
            print(f"[Telegram 失敗] {r.status_code} {r.text[:120]}")
    except Exception as e:  # noqa: BLE001
        print(f"[Telegram 例外] {e}")


def fetch_today():
    """Fetch today's WC matches (UTC date window covers TPE evening games)."""
    r = requests.get(FD_URL, headers={"X-Auth-Token": API_KEY}, timeout=15)
    r.raise_for_status()
    return r.json().get("matches", [])


def fmt_score(m) -> str:
    ft = m.get("score", {}).get("fullTime", {})
    return f'{ft.get("home", 0) or 0} : {ft.get("away", 0) or 0}'


def names(m):
    return m["homeTeam"]["name"], m["awayTeam"]["name"]


def main():
    print("⚽ WC26 Telegram 通知啟動 — 每"
          f" {POLL_SECONDS}s 檢查一次（Ctrl+C 結束）")
    send("🤖 WC26 // AGENT 通知服務已啟動，等待比賽事件…")
    state = {}  # match_id -> (status, score_str)

    while True:
        try:
            for m in fetch_today():
                mid = m["id"]
                status = m.get("status", "")
                score = fmt_score(m)
                prev_status, prev_score = state.get(mid, (None, None))
                home, away = names(m)

                if prev_status is None:
                    state[mid] = (status, score)
                    continue  # first sighting — record silently

                if status in ("IN_PLAY",) and prev_status in (
                        "TIMED", "SCHEDULED", "PAUSED") and prev_status != "PAUSED":
                    send(f"🟢 <b>開賽</b>\n{home} vs {away}")
                if score != prev_score and status in ("IN_PLAY", "PAUSED"):
                    send(f"⚽ <b>進球！</b>\n{home} <b>{score}</b> {away}")
                if status == "FINISHED" and prev_status != "FINISHED":
                    send(f"🏁 <b>終場</b>\n{home} <b>{score}</b> {away}")

                state[mid] = (status, score)
            now = datetime.now(TPE).strftime("%H:%M:%S")
            print(f"[{now} 台北] 檢查完成，追蹤 {len(state)} 場比賽")
        except KeyboardInterrupt:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[警告] 本輪檢查失敗：{e}（{POLL_SECONDS}s 後重試）")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止。")
