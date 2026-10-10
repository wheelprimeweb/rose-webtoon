"""Validate generated pages and every local link before publishing."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.images, self.links, self.references = [], [], []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            self.images.append(attrs)
            for part in attrs.get('srcset','').split(','):
                if part.strip(): self.references.append(part.strip().split()[0])
        if tag == 'a': self.links.append(attrs)
        for name in ('src','href','data-original'):
            if attrs.get(name): self.references.append(attrs[name])

def check(root):
    manifest = json.loads((root/'episodes.json').read_text(encoding='utf-8'))
    episodes = manifest['episodes']
    for i, episode in enumerate(episodes):
        text = (root/episode['url']).read_text(encoding='utf-8')
        doc = Document(text)
        assert len(doc.images) == episode['count'], '컷 수 불일치'
        assert 'api.github.com' not in text, '실시간 API 사용 발견'
        assert doc.images[0]['loading'] == 'eager'
        assert doc.images[0]['fetchpriority'] == 'high'
        assert all(im['loading'] == 'lazy' for im in doc.images[1:])
        assert all(int(im['width']) > 0 and int(im['height']) > 0 for im in doc.images)
        for im, saved in zip(doc.images, episode['images']):
            assert im['data-original'] == saved['original_url'], '이미지 순서 불일치'
        for direction, target in [('prev', i-1),('next',i+1)]:
            links = [a['href'] for a in doc.links if a.get('rel') == direction]
            expected = episodes[target]['url'] if 0 <= target < len(episodes) else None
            assert (set(links) == {expected}) if expected else not links, '이전/다음 회차 불일치'
    for path in root.glob('*.html'):
        for ref in Document(path.read_text(encoding='utf-8')).references:
            parts = urlsplit(ref)
            if not parts.scheme and parts.path:
                assert (root/unquote(parts.path)).is_file(), f'링크 누락: {ref}'
    print(f'페이지/이미지/이전·다음 링크 검사 통과: {len(episodes)}개 회차')

if __name__ == '__main__': check(Path(__file__).resolve().parents[1]/'_site')
