#!/usr/bin/env python3
"""SchoolFoundations education headlines: RSS -> durable news.json (stdlib only)."""
import json, os, re, sys, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'news.json'
SOURCE = os.environ.get('NEWS_RSS_URL', 'https://gna.org.gh/education/feed/')
KEYWORDS = ('school', 'teacher', 'education', 'curriculum', 'learning', 'literacy', 'student', 'pupil', 'classroom', 'assessment', 'inspection', 'headteacher', 'principal', 'basic education')
GENERIC = ('stay up to date on the latest news', 'provides comprehensive coverage', 'visit the ghana news agency', 'read more', 'latest news from ghana and the world')

def clean(value):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', value or ''))).strip()

def date_iso(value):
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        return ''

def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    result, seen = [], set()
    entries = root.findall('.//channel/item')
    print(f'DIAGNOSTIC: RSS entries received: {len(entries)}', flush=True)
    for entry in entries:
        title = clean(entry.findtext('title'))
        link = (entry.findtext('link') or '').strip()
        description = clean(entry.findtext('description'))[:300]
        date = date_iso(entry.findtext('pubDate'))
        parsed = urllib.parse.urlparse(link)
        if parsed.scheme != 'https' or parsed.hostname not in ('gna.org.gh', 'www.gna.org.gh') or not title or not date:
            continue
        if not any(word in title.lower() for word in KEYWORDS):
            continue
        canonical = link.rstrip('/').lower()
        if canonical in seen:
            continue
        seen.add(canonical)
        if len(description) < 55 or any(phrase in description.lower() for phrase in GENERIC):
            description = ''
        result.append({'title':title[:180], 'url':link, 'date':date, 'description':description})
    print(f'DIAGNOSTIC: Relevant dated entries: {len(result)}', flush=True)
    return sorted(result, key=lambda x: x['date'], reverse=True)

def previous_items():
    if not OUTPUT.exists():
        return []
    try:
        obj = json.loads(OUTPUT.read_text(encoding='utf-8'))
        return [x for x in obj.get('items', []) if isinstance(x, dict) and
                isinstance(x.get('url'), str) and urllib.parse.urlparse(x['url']).hostname in ('gna.org.gh', 'www.gna.org.gh') and
                isinstance(x.get('title'), str) and isinstance(x.get('date'), str)]
    except (OSError, ValueError, TypeError):
        print('WARNING: Existing news.json unreadable; not using it.', flush=True)
        return []

def main():
    previous = previous_items()
    fresh = []
    try:
        if os.environ.get('RSS_FIXTURE'):
            data = Path(os.environ['RSS_FIXTURE']).read_bytes()
        else:
            req = urllib.request.Request(SOURCE, headers={'User-Agent': 'SchoolFoundationsNews/0.3 (education headlines)'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError('Feed exceeds 2 MB limit')
        fresh = parse_rss(data)
    except Exception as exc:
        print(f'WARNING: News fetch failed: {exc}', flush=True)
    # Keep previously verified items, but never create fabricated placeholders.
    combined = {}
    for item in previous + fresh:
        combined[item['url'].rstrip('/').lower()] = item
    items = sorted(combined.values(), key=lambda x: x['date'], reverse=True)[:12]
    if not items:
        print('NOTICE: No relevant articles and no saved history. No news file published.', flush=True)
        return 0
    payload = {'source':'Ghana News Agency', 'source_url':SOURCE,
               'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
               'status': 'updated' if fresh else 'retained_previous', 'items':items}
    # Do not change the file merely because a scheduled check ran with no fresh news.
    if not fresh and OUTPUT.exists():
        print(f'NOTICE: Retained {len(items)} previously verified articles; no new relevant headlines.', flush=True)
        return 0
    tmp = OUTPUT.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    tmp.replace(OUTPUT)
    print(f'Published news.json: {len(items)} genuine articles ({len(fresh)} from current feed).', flush=True)
    if len(items) < 3:
        print('NOTICE: Fewer than three suitable articles; no fabricated fillers.', flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
