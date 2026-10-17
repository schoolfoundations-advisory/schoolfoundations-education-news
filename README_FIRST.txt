SCHOOLFOUNDATIONS ADVISORY — NEWS ADAPTER PROTOTYPE

PURPOSE
A separate prototype that fetches an RSS feed, validates headlines and writes news.json.
It does NOT modify the working SchoolFoundations website.
The GNA candidate RSS endpoint has NOT been confirmed to work from GitHub Actions.

TEST OFFLINE (Windows with Python installed):
1. Extract this ZIP.
2. Open Command Prompt inside the extracted folder.
3. Run:
   set RSS_FIXTURE=tests\sample_feed.xml
   python update_news.py
4. Open news.json with Notepad. Sample entries are fictional and marked Sample.
5. Delete news.json after this test so fictional data cannot be published.

TEST REAL NEWS (requires internet):
1. Close and reopen Command Prompt (clears RSS_FIXTURE).
2. Run: python update_news.py
3. If it succeeds, inspect news.json: headlines, links and dates must be genuine.
4. If it fails, the previous news.json remains unchanged. Do not claim live news works.

FUTURE ONLINE AUTOMATION (not yet deployed):
- Create a GitHub repository for this adapter; enable Actions and allow Actions write access.
- Run the workflow manually once and inspect the output/logs.
- Only if the feed succeeds, publish news.json via an HTTPS endpoint (e.g. GitHub Pages).
- Check cross-origin access from the actual website. GitHub Pages hosting and CORS
  compatibility must be verified, especially for locally opened HTML files.
- Connect the homepage only after this end-to-end test succeeds.
- GitHub Actions schedules are best-effort and may be delayed or disabled on inactive repositories.
- Do not put passwords/API keys in the website or public repository.

The default feed is a candidate: https://gna.org.gh/education/feed/
The script uses Python standard library, filters relevant terms, requires dates,
limits results, and preserves the previous JSON if retrieval fails.

IMPORTANT: Any source's reuse terms and permitted automation must be checked before launch.
