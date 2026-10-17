#!/usr/bin/env python3
"""SchoolFoundations RSS-to-JSON processor. Standard library only."""
import json, os, re, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET
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
    value = re.sub(r'<[^>]*>', ' ', value or '')
    return re.sub(r'\s+', ' ', unescape(value)).strip()

def date_iso(value):
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        return ''

def parse_rss(xml_bytes):
    root = ET.fromstring(xml_bytes)
    result, seen = [], set()
    for item in root.findall('.//channel/item'):
        title = clean(item.findtext('title'))
        link = (item.findtext('link') or '').strip()
        description = clean(item.findtext('description'))[:300]
        date = date_iso(item.findtext('pubDate'))
        parsed = urllib.parse.urlparse(link)
        if parsed.scheme != 'https' or parsed.hostname not in ('gna.org.gh', 'www.gna.org.gh') or not title or not date:
            continue
        if not any(word in title.lower() for word in KEYWORDS):
            continue
        canonical = link.rstrip('/').lower()
        if canonical in seen:
            continue
        seen.add(canonical)
        if any(phrase in description.lower() for phrase in GENERIC) or len(description) < 55:
            description = ''  # Never invent a summary or display generic site boilerplate.
        result.append({'title':title[:180], 'url':link, 'date':date, 'description':description})
    return sorted(result, key=lambda x:x['date'], reverse=True)[:12]

def main():
    try:
        if os.environ.get('RSS_FIXTURE'):
            data = Path(os.environ['RSS_FIXTURE']).read_bytes()
        else:
            req = urllib.request.Request(SOURCE, headers={'User-Agent':'SchoolFoundationsNews/0.2 (education headlines)'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = response.read(2_000_001)
                if len(data) > 2_000_000:
                    raise ValueError('Feed exceeds 2 MB limit')
        items = parse_rss(data)
        entries = ET.fromstring(data).findall('.//channel/item')
        print(f'DIAGNOSTIC: RSS entries received: {len(entries)}')
        for entry in entries[:3]:
            print('TITLE:', entry.findtext('title'))
            print('DATE:', entry.findtext('pubDate'))
            print('LINK:', entry.findtext('link'))
        print(f'DIAGNOSTIC: Accepted articles: {len(items)}')
        if not items:
            raise ValueError('No suitable dated education headlines found')
        payload = {'source':'Ghana News Agency', 'source_url':SOURCE, 'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'), 'items':items}
        temp = OUTPUT.with_suffix('.tmp')
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        temp.replace(OUTPUT)
        print(f'Updated news.json: {len(items)} items; {sum(bool(x["description"]) for x in items)} usable descriptions')
        if len(items) < 3:
            print('NOTICE: Fewer than 3 suitable headlines. Do not fill with fictional articles.')
    except Exception as exc:
        print(f'News refresh failed: {exc}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
