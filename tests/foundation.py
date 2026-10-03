"""SEO, locked-text and archive-growth regression checks; no network."""
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher', ROOT/'scripts/build.py')
builder = importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
public = ROOT/'.qa/public'
files = [public/'index.html', public/'about.html', *public.glob('story/**/index.html'), *public.glob('archive/**/index.html'), public/'privacy/index.html']
descriptions = []
for path in files:
    text = path.read_text()
    assert not re.search(r'<meta[^>]+(?:noindex|nofollow)', text, re.I)
    assert 'http://' not in text.replace('http://schema.org', '')
    graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)[1])
    assert graph['@context'] == 'https://schema.org'
    nodes = graph['@graph']; kinds = [node['@type'] for node in nodes]
    assert kinds.count('WebSite') == kinds.count('Person') == 1
    if path != public/'index.html': assert kinds.count('BreadcrumbList') == 1
    for node in nodes:
        if node['@type'] == 'BreadcrumbList':
            assert [n['position'] for n in node['itemListElement']] == list(range(1, len(node['itemListElement'])+1))
        if node['@type'] == 'Article':
            assert node['datePublished'] and node['author']['@id'].endswith('/about.html#author')
            assert 'dateModified' not in node  # No invented modification dates.
            assert 'articleBody' not in node
    for key in ('og:image','og:image:alt','og:image:width','og:image:height'):
        assert re.search(fr'<meta property="{key}" content="[^"]+">', text), (path,key)
    assert '<meta name="twitter:card" content="summary_large_image">' in text
    image = re.search(r'<meta property="og:image" content="https://www.katamisky.com([^"]+)">', text)[1]
    assert (public/image.lstrip('/')).is_file()
    config = json.loads(re.search(r'<script type="application/json" id="katamisky-config">(.*?)</script>',text,re.S)[1])
    assert config['canonical'] == builder.BASE+'/' + path.relative_to(public).as_posix().removesuffix('index.html')
    assert config['analytics'] == json.loads((ROOT/'content/site-settings.json').read_text())['analytics']
    assert 'googletagmanager.com' not in text and 'google-analytics.com' not in text
    descriptions.append(html.unescape(re.search(r'<meta name="description" content="([^"]+)">',text)[1]))
assert len(set(descriptions)) == len(files)
assert (public/'robots.txt').read_text() == 'User-agent: *\nAllow: /\nSitemap: https://www.katamisky.com/sitemap.xml\n'
locks = {'what-they-left-behind':(108,'29ec2b7a64e8e64133e6b1f26611c862b3ab80067342a77484fcaf3dca0bc38d'), 'i-have-been-angry':(78,'dad8723ab5b0346e9b2098816752f293912e54389c5f75b699e752c6744d8b04'), 'before-there-was-me':(137,'cf2861d10b5a7a560d55da0339d6d07f92e4ec8b256f171b4696b1151e2efe52')}
for slug,(count,digest) in locks.items():
    source = (ROOT/f'content/{slug}.html').read_text()
    rendered = (public/f'story/chapter-01/{slug}/index.html').read_text().split('<div class="story-body" id="story-pages">',1)[1].split('<footer',1)[0]
    for label,text in [('source',source),('rendered',rendered)]:
        paragraphs = [html.unescape(re.sub('<[^>]+>','',p)) for p in re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>',text,re.S)]
        assert len(paragraphs)==count,(slug,label,len(paragraphs))
        assert hashlib.sha256('\n'.join(paragraphs).encode()).hexdigest()==digest,(slug,label)
angry=(public/'story/chapter-01/i-have-been-angry/index.html').read_text()
before=(public/'story/chapter-01/before-there-was-me/index.html').read_text()
assert '"chapter_id":"prologue"' in angry and '"chapter_id":"chapter-01"' in before
assert 'data-measure="next_installment"' in angry and 'data-measure="previous_installment"' in before
assert 'data-measure="begin_story"' in (public/'index.html').read_text()
assert 'data-measure="continue_reading"' in (public/'archive/index.html').read_text() or 'data-measure="continue_reading"' in (public/'story/index.html').read_text()
print('PASS: all 10 public pages: SEO, schema syntax/relationships, unique metadata, image fallback, consent-gated analytics configuration, 323 locked paragraphs and hierarchy.')

with tempfile.TemporaryDirectory(prefix='katamisky-scale-') as directory:
    root=Path(directory)
    for folder in ('assets','content','templates'): shutil.copytree(ROOT/folder,root/folder)
    shutil.copy2(ROOT/'CNAME',root/'CNAME')
    (root/'content/chapters.json').write_text(json.dumps([{'id':'chapter-01','number':'1','title':'QA only'}]))
    (root/'content/published-paths.json').write_text('[]')
    entries=[]
    for n in range(121):
        source=f'qa-{n}.html'; (root/'content'/source).write_text('<p>QA fixture, never memoir or production content.</p>')
        entries.append({'id':f'qa-{n}','chapter':'chapter-01','title':f'QA {n}','description':f'QA description {n}','source':source,'date':'2000-01-01','status':'published','authorApproved':True})
    # Ensure future drafts stay out of archive, sitemap, schema and manifest.
    entries[-1]['status']='draft'
    (root/'content/installments.json').write_text(json.dumps(entries))
    start=time.monotonic(); builder.build(root,export=True)
    archive_paths=[root/'archive/index.html',root/'archive/page/2/index.html',root/'archive/page/3/index.html']
    counts=[len(re.findall(r'class="item-title"',p.read_text())) for p in archive_paths]
    assert counts == [50,50,20], counts
    assert all('qa-120' not in p.read_text() for p in archive_paths)
    assert 'qa-120' not in (root/'sitemap.xml').read_text()
    assert '/archive/page/3/' in (root/'sitemap.xml').read_text()
    assert 'rel="prev" href="/archive/"' in archive_paths[1].read_text()
    assert 'href="https://www.katamisky.com/archive/page/2/"' in archive_paths[1].read_text()
    assert 'story-manifest.js?v=' in (root/'assets/js/reader-progress.js').read_text()
    print(f'PASS: 120-installment build, 3 crawlable self-canonical archive pages (50/50/20), draft exclusion, navigation and link validation; {time.monotonic()-start:.2f}s.')
    (root/'content/site-settings.json').write_text('{"analytics":{"enabled":true,"measurementId":"invalid"}}')
    try: builder.build(root)
    except ValueError as error: assert 'real G-' in str(error)
    else: raise AssertionError('Invalid analytics configuration accepted')
    print('PASS: invalid analytics configuration rejected before publication.')
