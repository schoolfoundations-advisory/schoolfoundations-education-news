"""Read-only diagnostic for GNA's public education archive.

Does not alter update_news.py, news.json, or the existing workflow.
"""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import re

ARCHIVE = 'https://gna.org.gh/education/'

class ArchiveLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            title = ' '.join(' '.join(self.parts).split())
            url = urljoin(ARCHIVE, self.href)
            parsed = urlparse(url)
            if parsed.netloc in ('gna.org.gh', 'www.gna.org.gh') and re.match(r'^/20\d\d/\d\d/[^/]+/?$', parsed.path) and len(title) >= 18:
                self.links.append((title, url))
            self.href = None
            self.parts = []


def main():
    request = Request(ARCHIVE, headers={'User-Agent': 'SchoolFoundationsNewsResearch/0.1 (read-only diagnostic)'})
    try:
        with urlopen(request, timeout=20) as response:
            page = response.read(2_000_000).decode('utf-8', errors='replace')
            print('HTTP status:', response.status)
    except Exception as exc:
        print('Archive request failed:', type(exc).__name__, str(exc))
        return
    parser = ArchiveLinks()
    parser.feed(page)
    unique = list(dict.fromkeys(parser.links))
    print('Article-style links found:', len(unique))
    print('First 10 candidate links (not yet date/relevance verified):')
    for title, url in unique[:10]:
        print('-', title[:110], '|', url)
    if not unique:
        print('No article links detected; inspect HTML structure before proceeding.')

if __name__ == '__main__':
    main()
