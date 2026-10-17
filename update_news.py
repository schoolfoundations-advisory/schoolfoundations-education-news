#!/usr/bin/env python3
"""RSS -> small JSON file. Python standard library only; no API key."""
import json, os, re, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'news.json'
SOURCE = os.environ.get('NEWS_RSS_URL', 'https://gna.org.gh/education/feed/')
KEYWORDS = ('school','teacher','education','curriculum','learning','literacy','student','pupil','classroom','assessment','private school','inspection')

def clean(value):
    value = re.sub(r'<[^>]*>', ' ', value or '')
    return re.sub(r'\s+', ' ', unescape(value)).strip()

def date_iso(value):
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError):
        return ''

def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    result = []
    for item in root.findall('.//channel/item'):
        title = clean(item.findtext('title'))
        link = (item.findtext('link') or '').strip()
        description = clean(item.findtext('description'))[:240]
        date = date_iso(item.findtext('pubDate'))
        parsed = urllib.parse.urlparse(link)
        if parsed.scheme != 'https' or not parsed.netloc or not title or not date:
            continue
        if not any(word in (title + ' ' + description).lower() for word in KEYWORDS):
            continue
        result.append({'title':title[:180], 'url':link, 'date':date, 'description':description})
    unique = {item['url']: item for item in result}
    return sorted(unique.values(), key=lambda x:x['date'], reverse=True)[:12]

def main():
    try:
        if os.environ.get('RSS_FIXTURE'):
            data = Path(os.environ['RSS_FIXTURE']).read_bytes()
        else:
            req = urllib.request.Request(SOURCE, headers={'User-Agent':'SchoolFoundationsNewsPrototype/0.1 (education headlines; contact via site)'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = response.read(2_000_001)
                if len(data)>2_000_000: raise ValueError('Feed exceeds size limit')
        items = parse_rss(data)
        if not items: raise ValueError('No valid relevant dated RSS items; retaining previous file')
        payload = {'source':'Ghana News Agency', 'source_url':SOURCE, 'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'), 'items':items}
        tmp = OUTPUT.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        tmp.replace(OUTPUT)
        print(f'Updated {OUTPUT.name}: {len(items)} items')
    except Exception as exc:
        print(f'News refresh failed; existing news.json preserved: {exc}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__': main()
