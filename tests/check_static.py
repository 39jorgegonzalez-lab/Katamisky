"""Check production files, links, metadata, and excluded editor sources."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote, urljoin
import argparse
import json
import re

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.tags=[];self.ids=set();self.refs=[];self.stack=[];self.errors=[]
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append((tag,a))
        if 'id' in a:
            if a['id'] in self.ids:self.errors.append('duplicate '+a['id'])
            self.ids.add(a['id'])
        for k in ('href','src'):
            if k in a:self.refs.append(a[k])
        if tag=='img':
            assert 'alt' in a and 'width' in a and 'height' in a
            assert a['width'].isdigit() and a['height'].isdigit()
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append(tag)
    def handle_endtag(self,tag):
        if not self.stack or self.stack.pop()!=tag:self.errors.append('misnested '+tag)

def check(root):
    files=[root/'index.html',root/'about.html',*root.glob('story/**/index.html'),root/'archive/index.html',root/'privacy/index.html']
    pages={f:Page(f.read_text()) for f in files}
    titles=[]
    for f,p in pages.items():
        text=f.read_text()
        assert text.startswith('<!DOCTYPE html>'),f
        assert not p.errors and not p.stack,(f,p.errors,p.stack)
        assert len([1 for t,a in p.tags if t=='h1'])==1,f
        assert len([1 for t,a in p.tags if t=='main'])==1,f
        assert any(t=='meta' and a.get('name')=='description' and a.get('content') for t,a in p.tags)
        expected_url='https://www.katamisky.com/' + f.relative_to(root).as_posix().removesuffix('index.html')
        assert any(t=='link' and a.get('rel')=='canonical' and a.get('href')==expected_url for t,a in p.tags)
        assert any(t=='meta' and a.get('property')=='og:url' and a.get('content')==expected_url for t,a in p.tags)
        titles.append(re.search('<title>(.*?)</title>',text)[1])
        for ref in p.refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc:continue
            assert ref!='#'
            page_url='/' + f.relative_to(root).as_posix()
            dest=root/unquote(urlsplit(urljoin(page_url,ref)).path).lstrip('/')
            if dest.is_dir():dest=dest/'index.html'
            assert dest.is_file(),(f,ref)
            if u.fragment and u.fragment!='resume':assert u.fragment in (pages.get(dest) or Page(dest.read_text())).ids
        assert not re.search(r'<audio\b|AudioContext|audio-manager|Enable Sound|development-installment',text,re.I)
        assert not any(x in text for x in ['/templates/','/tests/','/content/','.qa/'])
    assert len(titles)==len(set(titles))
    from xml.etree import ElementTree
    urls = [n.text for n in ElementTree.parse(root/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    expected = {'https://www.katamisky.com/' + f.relative_to(root).as_posix().removesuffix('index.html') for f in files}
    assert set(urls)==expected, 'Sitemap must contain exactly the public pages'
    assert len(urls)==len(set(urls)), 'Duplicate sitemap URL'
    for css in (root/'assets/css').glob('*.css'):
        for url in re.findall(r'url\(([^)]+)\)',css.read_text()):assert (root/url.lstrip('/')).is_file(),url
    assert (root/'CNAME').read_text()=='www.katamisky.com'
    assert not list(root.rglob('*audio*'))
    manifest=(root/'assets/js/story-manifest.js').read_text()
    entries=json.loads(manifest.split('export const installments = ',1)[1].strip().removesuffix(';'))
    assert [i['storyOrder'] for i in entries]==list(range(1,len(entries)+1))
    reader_urls={'/' + f.relative_to(root).as_posix().removesuffix('index.html') for f in root.glob('story/*/*/index.html')}
    assert {i['url'] for i in entries}==reader_urls and len(entries)==len(reader_urls), 'Manifest must match public installments'
    if 'export const installments = [];' in manifest:
        assert len(files)>=6
        assert all('Begin the Story' not in f.read_text() for f in files)
        assert not list(root.glob('story/*/*/index.html'))
    print(f'PASS: {len(files)} pages; balanced HTML, links/assets, SEO, semantics, no public sample or editor links.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]/'.qa/public');a=p.parse_args();check(a.root.resolve())
