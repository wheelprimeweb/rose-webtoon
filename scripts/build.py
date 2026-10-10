"""Static ROSE publisher. Originals are read-only; native WebP is pixel-exact."""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageOps, __version__ as PILLOW_VERSION

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
VERSION = 'rose-lossless-3-' + PILLOW_VERSION

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def natural(name):
    return tuple((0, int(p)) if p.isdigit() else (1, p.casefold()) for p in re.split(r'(\d+)', name))

def discover(root):
    episodes = []
    seen = set()
    for folder in (root / 'episodes').iterdir():
        if not folder.is_dir() or folder.name.startswith('.'): continue
        if not folder.name.isascii() or not folder.name.isdigit() or int(folder.name) < 1:
            raise ValueError(f'회차 폴더는 01, 02, 03처럼 양의 정수여야 합니다: {folder.name}')
        number = int(folder.name)
        if number in seen: raise ValueError(f'회차 번호 중복: {number}')
        seen.add(number)
        files = sorted((p for p in folder.iterdir() if p.suffix.lower() in EXTENSIONS), key=lambda p: natural(p.name))
        if not files: raise ValueError(f'이미지가 없는 회차: {folder.name}')
        keys = [natural(p.stem) for p in files]
        if len(keys) != len(set(keys)): raise ValueError(f'컷 번호/이름 중복: {folder.name}')
        if any(p.is_dir() for p in folder.iterdir()): raise ValueError(f'회차 안에 하위 폴더를 넣지 마세요: {folder.name}')
        episodes.append((number, folder, files))
    if not episodes: raise ValueError('회차 이미지가 없습니다.')
    return sorted(episodes)

def optimize(source, cache):
    source_hash = digest(source)
    key = hashlib.sha256((VERSION + source_hash).encode()).hexdigest()
    directory = cache / key
    record = directory / 'info.json'
    if record.exists():
        info = json.loads(record.read_text())
        if all((directory / v['name']).exists() and digest(directory / v['name']) == v['sha256'] for v in info['variants']):
            return directory, info, True
    directory.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as raw:
        if getattr(raw, 'n_frames', 1) != 1: raise ValueError(f'움직이는 이미지는 지원하지 않습니다: {source}')
        oriented = ImageOps.exif_transpose(raw)
        image = oriented.convert('RGBA' if 'A' in oriented.getbands() or 'transparency' in raw.info else 'RGB')
        width, height = image.size
        if max(width, height) > 16383: raise ValueError(f'WebP 최대 크기 초과: {source}')
        variants = []
        for w in sorted({min(640, width), min(960, width), width}):
            h = max(1, round(height * w / width))
            rendered = image if w == width else image.resize((w, h), Image.Resampling.LANCZOS)
            output = directory / f'{w}.webp'
            options = {'icc_profile': raw.info['icc_profile']} if raw.info.get('icc_profile') else {}
            rendered.save(output, 'WEBP', lossless=True, method=6, exact=True, **options)
            with Image.open(output) as checked:
                if checked.convert(rendered.mode).tobytes() != rendered.tobytes():
                    raise ValueError(f'무손실 화질 검사 실패: {source}')
            variants.append({'width':w, 'height':h, 'name':output.name, 'bytes':output.stat().st_size, 'sha256':digest(output)})
    info = {'sha256':source_hash, 'width':width, 'height':height, 'original_bytes':source.stat().st_size, 'variants':variants, 'native_pixel_exact':True}
    record.write_text(json.dumps(info), encoding='utf-8')
    return directory, info, False

def page(title, body, extra=''):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ROSE | {html.escape(title)}</title><link rel="stylesheet" href="style.css">{extra}</head>{body}</html>'

def build(root, out, cache):
    config = json.loads((root/'site-config.json').read_text(encoding='utf-8'))
    episodes = discover(root)
    # Stop accidental deletion, reordering or replacement of the published 1/2 originals.
    baseline = json.loads((root/'originals-lock.json').read_text(encoding='utf-8'))
    for folder, files in baseline.items():
        current = next((fs for _, d, fs in episodes if d.name == folder), [])
        if [p.name for p in current] != [f['file'] for f in files]: raise ValueError(f'{folder}화 원본 목록이 변경되었습니다. 기존 컷을 복원하세요.')
        for saved, path in zip(files, current):
            if digest(path) != saved['sha256']: raise ValueError(f'기존 원본 변경 감지: {path}')
    if out.exists():
        # Only the explicitly designated generated directory may be replaced.
        if out.name != '_site' or out.resolve().parent != root.resolve(): raise ValueError('출력 폴더는 저장소 바로 아래 _site여야 합니다.')
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for filename in ['style.css','reader.js']:
        shutil.copy2(root/filename, out/filename)
    for filename in ['CNAME','robots.txt','favicon.ico']:
        if (root/filename).is_file(): shutil.copy2(root/filename, out/filename)
    (out/'.nojekyll').touch()
    manifest = {'format':1, 'compression':'lossless WebP; native pixels verified', 'episodes':[]}
    cache_hits = 0
    for position, (number, folder, files) in enumerate(episodes):
        settings = config['episodes'].get(folder.name, {})
        width = settings.get('width', 900)
        entry = {'number':number,'url':f'episode-{number:02}.html','count':len(files),'images':[], 'warnings':[]}
        hashes = {}
        markup = []
        originals_dir = out/'episodes'/folder.name
        originals_dir.mkdir(parents=True)
        for index, source in enumerate(files):
            directory, info, hit = optimize(source, cache)
            cache_hits += hit
            if info['sha256'] in hashes: entry['warnings'].append(f'같은 내용의 이미지: {hashes[info["sha256"]]} / {source.name} (자동 삭제하지 않음)')
            hashes[info['sha256']] = source.name
            shutil.copy2(source, originals_dir/source.name) # old image URLs remain valid
            asset_dir = out/'assets'/directory.name
            asset_dir.mkdir(parents=True, exist_ok=True)
            variants = []
            for variant in info['variants']:
                shutil.copy2(directory/variant['name'], asset_dir/variant['name'])
                variants.append({**variant,'url':f'assets/{directory.name}/{variant["name"]}'})
            original_url = f'episodes/{quote(folder.name)}/{quote(source.name)}'
            gap = settings.get('gaps',{}).get(source.name, config['default_gap'])
            item = {**info,'file':source.name,'original_url':original_url,'gap':gap,'variants':variants}
            entry['images'].append(item)
            srcset = ', '.join(f'{v["url"]} {v["width"]}w' for v in variants)
            priority = 'fetchpriority="high" loading="eager"' if index == 0 else 'loading="lazy"'
            markup.append(f'<div class="cut" style="padding-top:{gap}px"><img src="{variants[-1]["url"]}" srcset="{srcset}" sizes="(max-width: {width}px) 100vw, {width}px" width="{info["width"]}" height="{info["height"]}" alt="{number}화 컷 {index+1}" {priority} decoding="async" data-original="{original_url}"><button class="retry" type="button" hidden>이 컷 다시 불러오기</button></div>')
        entry['original_bytes'] = sum(x['original_bytes'] for x in entry['images'])
        entry['native_bytes'] = sum(x['variants'][-1]['bytes'] for x in entry['images'])
        entry['mobile_640_bytes'] = sum(x['variants'][0]['bytes'] for x in entry['images'])
        entry['mobile_960_bytes'] = sum(next((v['bytes'] for v in x['variants'] if v['width'] >= min(960,x['width'])),x['variants'][-1]['bytes']) for x in entry['images'])
        entry['saved_percent'] = round(100*(1-entry['native_bytes']/entry['original_bytes']),1)
        links = ['<a href="index.html">목록보기</a>']
        if position: links.insert(0,f'<a rel="prev" href="episode-{episodes[position-1][0]:02}.html">이전화</a>')
        if position+1 < len(episodes): links.append(f'<a rel="next" href="episode-{episodes[position+1][0]:02}.html">다음화</a>')
        else: links.append('<span>다음화 준비 중</span>')
        nav = ' '.join(links)
        heading = '<section class="reader-title"><h1>1화</h1><p>아래로 스크롤해 감상하세요</p></section>' if number == 1 else ''
        edges = ''
        for direction, target, arrow in [('prev',position-1,'‹'),('next',position+1,'›')]:
            if 0 <= target < len(episodes):
                label = '이전화' if direction == 'prev' else '다음화'
                edges += f'<a class="edge viewer-control {direction}" href="episode-{episodes[target][0]:02}.html" aria-label="{label}">{arrow}</a>'
        body = f'<body class="reading-mode episode-page episode-{number}"><header class="viewer-control"><a href="index.html"><strong>ROSE</strong></a><span>{number}화 · {len(files)}컷</span></header>{edges}<main class="reader" style="max-width:{width}px">{heading}{"".join(markup)}</main><footer class="bottom">{nav}</footer><button id="menu-toggle" aria-expanded="false" aria-controls="reader-menu" type="button">메뉴</button><nav id="reader-menu" class="viewer-toolbar viewer-control" aria-label="회차 이동">{nav}</nav><script src="reader.js" defer></script></body>'
        (out/entry['url']).write_text(page(f'{number}화',body), encoding='utf-8')
        manifest['episodes'].append(entry)
        print(f'{number}화: {len(files)}컷, 원본 {entry["original_bytes"]/1e6:.1f} MB → 무손실 {entry["native_bytes"]/1e6:.1f} MB / 640px {entry["mobile_640_bytes"]/1e6:.1f} MB',flush=True)
    listing = ''.join(f'<a class="chapter" href="{ep["url"]}">{ep["number"]}화 보기 <small>{ep["count"]}컷</small></a>' for ep in manifest['episodes'])
    (out/'index.html').write_text(page('회차 목록',f'<body><header><a href="index.html"><strong>ROSE</strong></a><span>임신혜 웹툰</span></header><main class="list"><h1>회차 목록</h1>{listing}</main></body>'), encoding='utf-8')
    (out/'episodes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    rows = '\n'.join(f'|{e["number"]}화|{e["count"]}|{e["original_bytes"]/1e6:.1f}|{e["native_bytes"]/1e6:.1f}|{e["mobile_640_bytes"]/1e6:.1f}|{e["mobile_960_bytes"]/1e6:.1f}|' for e in manifest['episodes'])
    summary = '# ROSE 빌드 결과\n\n원본 픽셀과 무손실 WebP 일치 검사 통과. 640/960px는 비율을 유지해 축소한 별도 표시용 이미지입니다. 기기 화면과 배율에 따라 선택 크기가 달라집니다.\n\n|회차|컷|원본 MB|원래 해상도 WebP MB|640px MB|960px MB|\n|---|---:|---:|---:|---:|---:|\n'+rows+f'\n\n재사용한 이미지: {cache_hits}개. 번호 공백은 오류가 아닙니다.\n'
    for e in manifest['episodes']:
        for warning in e['warnings']: summary += f'\n- {e["number"]}화: {warning}'
    (out/'build-report.md').write_text(summary,encoding='utf-8')
    total_size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    if total_size > 950 * 1024**2:
        raise ValueError('사이트가 GitHub Pages 1GB 한도에 가까워졌습니다. 기존 사이트를 유지하고 배포를 중단합니다. 이미지 저장소 분리가 필요합니다.')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f: f.write(summary)
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try: build(args.root, args.root/'_site', args.root/'.cache/images')
    except Exception as error:
        print(f'::error::빌드 중단: {error}',flush=True)
        raise
