Two Ways to View on Mobile in <10 Seconds
Free Cloud Static Hosting (Works even when your PC is asleep):

Push build_brief.py and index.html to a GitHub repo and enable GitHub Pages.

Add a .github/workflows/brief.yml cron job at 0 23 * * 1-5 UTC (7:00 AM SGT Tue–Sat, right after US close) that runs python build_brief.py and commits brief.json.

Bookmark the GitHub Pages URL on your phone's home screen—opening or tapping Refresh loads in ~200–400ms.

Direct from Your PC (Zero GitHub needed):

Run build_brief.py via Windows Task Scheduler every morning at 6:30 AM SGT (or on demand).

Serve the folder with python -m http.server 8080 and access it securely from your iPhone over Tailscale (http://<pc-tailscale-ip>:8080), or add a tiny Flask/FastAPI endpoint on /refresh if you want tapping Refresh on your phone to trigger build_brief.py live on your PC (~2–3 seconds total execution).
