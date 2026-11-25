import json
import os
from datetime import datetime, timezone, timedelta
import yfinance as yf
import feedparser
import requests

SGT = timezone(timedelta(hours=8))

TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    "VIX": "^VIX",
    "US 10Y Yield": "^TNX",
    "DXY": "DX-Y.NYB",
    "Gold": "GC=F",
    "WTI Crude": "CL=F",
}

RSS_FEEDS = [
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",  # CNBC Finance
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",  # MarketWatch Top Stories
]


def fetch_indices():
    symbols = list(TICKERS.values())
    # Single batch call for last 5 daily bars to compute clean prev close vs latest close
    df = yf.download(symbols, period="5d", interval="1d", progress=False, auto_adjust=False)["Close"]
    results = []
    for label, sym in TICKERS.items():
        series = df[sym].dropna()
        if len(series) >= 2:
            last = float(series.iloc[-1])
            prev = float(series.iloc[-2])
            chg = last - prev
            pct = (chg / prev) * 100.0
            results.append({
                "name": label,
                "symbol": sym,
                "price": round(last, 2),
                "chg": round(chg, 2),
                "pct": round(pct, 2),
            })
    return results


def fetch_headlines(limit=8):
    items = []
    seen = set()
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:6]:
            title = entry.get("title", "").strip()
            if title and title not in seen:
                seen.add(title)
                items.append({
                    "title": title,
                    "link": entry.get("link", "#"),
                    "published": entry.get("published", ""),
                })
    return items[:limit]


def summarize_brief(indices, headlines):
    """
    Optional: If GEMINI_API_KEY is set in env, generates a 3-bullet overnight synthesis.
    Otherwise falls back to a fast deterministic market tape summary (0 external dependencies).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    market_line = ", ".join(f"{x['name']}: {x['price']} ({x['pct']:+.2f}%)" for x in indices[:5])

    if not api_key:
        top_movers = sorted(indices, key=lambda x: abs(x["pct"]), reverse=True)[:3]
        movers_txt = "; ".join(f"{m['name']} {m['pct']:+.2f}%" for m in top_movers)
        return [
            f"Overnight close: {market_line}.",
            f"Largest moves: {movers_txt}.",
            f"Lead story: {headlines[0]['title']}" if headlines else "No headlines fetched.",
        ]

    prompt = (
        "Summarize the overnight US market session in 3 concise, factual bullets for an institutional trader. "
        "No fluff.\n\n"
        f"Indices: {market_line}\n"
        f"Headlines:\n" + "\n".join(f"- {h['title']}" for h in headlines)
    )
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=10,
    )
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return [line.lstrip("-*• ").strip() for line in text.splitlines() if line.strip()][:4]


def main():
    indices = fetch_indices()
    headlines = fetch_headlines()
    summary = summarize_brief(indices, headlines)

    payload = {
        "updated_sgt": datetime.now(SGT).strftime("%a, %d %b %Y %H:%M SGT"),
        "summary": summary,
        "indices": indices,
        "headlines": headlines,
    }
    with open("brief.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Updated brief.json at {payload['updated_sgt']}")


if __name__ == "__main__":
    main()