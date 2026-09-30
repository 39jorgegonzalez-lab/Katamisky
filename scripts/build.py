#!/usr/bin/env python3
"""Generate the static digital book. Authoring sources never enter the export."""
import argparse
import html
import json
import re
import shutil
import tempfile
import importlib.util
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

BASE = 'https://www.katamisky.com'
e = lambda value: html.escape(str(value), quote=True)
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def resume():
    return '<div class="resume" data-resume hidden><p class="eyebrow">Welcome back.</p><a href="/story/">Continue Reading</a></div>'


def layout(title, description, url, body, active='', reader=False, document=False, home=False):
    styles = ['fonts', 'site', 'components'] + (['home'] if home else []) + (['reader'] if reader else []) + (['document-font'] if document else [])
    versions = {'reader': '?v=book-pages-1', 'home': '?v=landing-1'}
    links = '\n'.join(f'<link rel="stylesheet" href="/assets/css/{s}.css{versions.get(s, "")}">' for s in styles)
    nav = ''.join(f'<a href="{href}"'+(' aria-current="page"' if label == active else '')+f'>{label}</a>' for label, href in [('Story','/story/'),('Chapters','/story/chapter-01/'),('Archive','/archive/'),('About','/about.html')])
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | KATAMISKY</title><meta name="description" content="{e(description)}">
<meta name="theme-color" content="#f8f5f1"><link rel="canonical" href="{BASE}{e(url)}">
<meta property="og:title" content="{e(title)} | KATAMISKY"><meta property="og:description" content="{e(description)}">
<meta property="og:type" content="{'article' if reader else 'website'}"><meta property="og:url" content="{BASE}{e(url)}">
<link rel="icon" type="image/svg+xml" href="/assets/images/site/favicon.svg">
{links}<script type="module" src="/assets/js/continue-reading.js?v=book-pages-1"></script>
</head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="container header-inner"><a class="brand" href="/" aria-label="KATAMISKY home">KATAMISKY</a><nav class="site-nav" aria-label="Main">{nav}</nav></div></header>
{body}
<footer class="site-footer"><div class="container footer-inner"><div><a class="brand" href="/">KATAMISKY</a><p>A Serialized Illustrated Memoir</p></div><nav aria-label="Footer"><a href="/story/">Story</a><a href="/archive/">Archive</a><a href="/about.html">About</a><a href="/privacy/">Privacy</a></nav></div></footer>
</body></html>\n'''


def listing(group, latest_url):
    rows = []
    for item in group:
        latest = ' · Latest installment' if item['url'] == latest_url else ''
        rows.append(f'<li><a href="{item["url"]}"><span class="index-number">{item["storyOrder"]:02}</span><span><span class="item-title">{e(item["title"])}</span><span class="small"><time datetime="{item["date"]}">{item["date"]}</time>{latest}</span><span class="current-position" data-position="{item["url"]}" hidden>Your saved reading position</span></span><span aria-hidden="true">→</span></a></li>')
    return '<ol class="index-list">'+''.join(rows)+'</ol>'


def object_module(item):
    objects = item.get('objects', [])
    if not objects:
        return ''
    links = []
    amazon = False
    for obj in objects:
        if not isinstance(obj, dict) or not isinstance(obj.get('title'), str) or not obj['title'].strip() or not isinstance(obj.get('url'), str):
            raise ValueError('Related object needs title, URL, and connection')
        if type(obj.get('affiliate', False)) is not bool:
            raise ValueError('Object affiliate flag must be boolean')
        if not obj.get('connection'):
            raise ValueError('Related object needs an author-supplied connection')
        parts = urlsplit(obj['url'])
        if parts.scheme != 'https' or not parts.hostname:
            raise ValueError('Object URL must be HTTPS')
        is_amazon = parts.hostname == 'amazon.com' or parts.hostname.endswith('.amazon.com')
        if is_amazon and parse_qs(parts.query).get('tag') != ['katamisky-20']:
            raise ValueError('Preserve the Amazon affiliate tag')
        amazon |= is_amazon
        relation = 'nofollow sponsored noopener' if is_amazon or obj.get('affiliate') else 'noopener'
        links.append(f'<li><a href="{e(obj["url"])}" rel="{relation}">{e(obj["title"])}</a><p>{e(obj["connection"])}</p></li>')
    disclosure = '<p class="small">As an Amazon Associate I earn from qualifying purchases.</p>' if amazon else ''
    return '<section class="objects"><h2>Objects From This Memory</h2>'+disclosure+'<ul class="object-list">'+''.join(links)+'</ul></section>'


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {path.name}: {error}") from error


def book_pages(prose, breaks):
    """Wrap complete paragraphs in numbered pages without altering their markup."""
    if breaks is None:
        return prose
    paragraphs = re.findall(r'<p(?:\s[^>]*)?>.*?</p>', prose, re.S)
    remainder = re.sub(r'<p(?:\s[^>]*)?>.*?</p>', '', prose, flags=re.S)
    if remainder.strip() or not paragraphs:
        raise ValueError('pageBreaks requires paragraph-only prose; never split other content automatically')
    if not isinstance(breaks, list) or any(type(n) is not int or n < 1 or n >= len(paragraphs) for n in breaks) or breaks != sorted(set(breaks)):
        raise ValueError('pageBreaks must be unique increasing paragraph boundaries within the manuscript')
    boundaries = [0, *breaks, len(paragraphs)]
    pages = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), 1):
        label = f'Page {index} of {len(boundaries) - 1}'
        pages.append(f'<div class="book-page" id="page-{index}" role="group" aria-label="{label}" tabindex="-1">\n' + '\n'.join(paragraphs[start:end]) + '\n</div>')
    return '\n'.join(pages)


def validate_metadata(root, chapters, entries):
    if not isinstance(chapters, list) or not all(isinstance(c, dict) for c in chapters):
        raise ValueError('Chapters must be a JSON array of objects')
    if not isinstance(entries, list) or not all(isinstance(i, dict) for i in entries):
        raise ValueError('Installments must be a JSON array of objects')
    chapter_ids = set()
    for chapter in chapters:
        if not isinstance(chapter.get('id'), str) or not SLUG.fullmatch(chapter['id']):
            raise ValueError('Invalid chapter slug')
        if chapter['id'] in chapter_ids or not isinstance(chapter.get('number'), str):
            raise ValueError('Chapters need unique IDs and string chapter numbers')
        if chapter.get('title') is not None and not isinstance(chapter['title'], str):
            raise ValueError('Chapter title must be text or null')
        chapter_ids.add(chapter['id'])
    urls = set()
    sources = set()
    for item in entries:
        if item.get('status') not in ('draft', 'published'):
            raise ValueError('Only draft and published statuses are supported')
        if type(item.get('authorApproved')) is not bool:
            raise ValueError('authorApproved must be true or false, not text')
        if not isinstance(item.get('id'), str) or not SLUG.fullmatch(item['id']) or item.get('chapter') not in chapter_ids:
            raise ValueError('Invalid installment/chapter slug')
        url = (item['chapter'], item['id'])
        if url in urls:
            raise ValueError('Duplicate permanent URL (including draft entries)')
        urls.add(url)
        for key in ('title', 'description', 'date', 'source'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f"Supply real title, description, publication date, and source: missing {key}")
        try:
            parsed = date.fromisoformat(item['date'])
            if parsed.isoformat() != item['date']: raise ValueError()
        except ValueError:
            raise ValueError('Publication date must use YYYY-MM-DD')
        source = (root/'content'/item['source']).resolve()
        if not source.is_relative_to((root/'content').resolve()) or not source.is_file() or source.suffix != '.html':
            raise ValueError('Invalid prose source: use an existing HTML file inside content/')
        if source in sources: raise ValueError('Each installment needs its own source file')
        sources.add(source)
        if type(item.get('document', False)) is not bool or not isinstance(item.get('objects', []), list):
            raise ValueError('document must be boolean and objects must be an array')
        if item.get('pageNumber') is not None and (type(item['pageNumber']) is not int or item['pageNumber'] < 1):
            raise ValueError('Optional pageNumber must be a positive integer')


def validate_pages(root, pages):
    # Reuse the static checker before touching any generated production file.
    spec = importlib.util.spec_from_file_location('static_check', Path(__file__).resolve().parents[1]/'tests/check_static.py')
    checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
    with tempfile.TemporaryDirectory(prefix='katamisky-validate-') as temp:
        staged = Path(temp)
        shutil.copytree(root/'assets', staged/'assets')
        shutil.copy2(root/'CNAME', staged/'CNAME')
        for path, text in pages.items():
            target = staged/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        try: checker.check(staged)
        except (AssertionError, OSError) as error:
            raise ValueError(f'Generated HTML/link/asset validation failed: {error}') from error


def preview_drafts(root):
    # Only approved material may enter a preview. Never mutate production metadata.
    with tempfile.TemporaryDirectory(prefix='katamisky-preview-') as temp:
        staging = Path(temp)
        for folder in ('content', 'templates', 'assets'):
            shutil.copytree(root/folder, staging/folder)
        shutil.copy2(root/'CNAME', staging/'CNAME')
        entries = read_json(staging/'content/installments.json')
        validate_metadata(staging, read_json(staging/'content/chapters.json'), entries)
        selected = [i for i in entries if i['status'] == 'published' or i['authorApproved']]
        for item in selected: item['status'] = 'published'
        (staging/'content/installments.json').write_text(json.dumps(selected))
        build(staging, export=True, preview=True)
        destination = root/'.qa/draft-preview'
        if destination.exists(): shutil.rmtree(destination)
        shutil.copytree(staging/'.qa/public', destination)
        print('LOCAL APPROVED-DRAFT PREVIEW — never deploy this directory:', destination)


def build(root, export=False, preview=False):
    root = root.resolve()
    chapters = read_json(root/'content/chapters.json')
    entries = read_json(root/'content/installments.json')
    validate_metadata(root, chapters, entries)
    chapter_map = {c['id']: c for c in chapters}
    if len(chapter_map) != len(chapters) or 'chapter-01' not in chapter_map:
        raise ValueError('Chapters need unique IDs and a Chapter 01 index')
    for c in chapters:
        if not SLUG.fullmatch(c['id']):
            raise ValueError('Invalid chapter slug')
    if any(i.get('status') not in ('draft','published') for i in entries):
        raise ValueError('Only draft and published statuses are supported; no public development installments')
    items = [dict(i) for i in entries if i['status'] == 'published']
    urls = set()
    for order, item in enumerate(items, 1):
        if not SLUG.fullmatch(item['id']) or item['chapter'] not in chapter_map:
            raise ValueError('Invalid installment/chapter slug')
        if not item.get('authorApproved') or not chapter_map[item['chapter']].get('title'):
            raise ValueError('Publication requires author approval and a real chapter title')
        if not item.get('title') or not item.get('description') or not item.get('date'):
            raise ValueError('Supply real title, description, and publication date')
        if not preview and date.fromisoformat(item['date']) > date.today():
            raise ValueError('Future installment must remain draft until publication day')
        source = (root/'content'/item['source']).resolve()
        if not source.is_relative_to(root/'content') or not source.is_file():
            raise ValueError('Invalid prose source')
        prose = source.read_text()
        if not prose.strip() or re.search(r'\[(AUTHOR|APPROVED|ACTUAL|CONCISE|KNOWN|APPLICABLE|OPTIONAL)|DEVELOPMENT PLACEHOLDER|REPLACE WITH|REPLACE-WITH', prose + item['title'] + item['description'] + chapter_map[item['chapter']]['title'], re.I):
            raise ValueError('Replace all template fields before publication')
        if re.search(r'<(?:script|iframe|audio|video)\b|\son\w+\s*=|javascript:', prose, re.I):
            raise ValueError('Memoir source must be semantic text/images, without embedded executable content')
        if 'document-text' in prose and not item.get('document'):
            raise ValueError('Document transcription requires document: true')
        item['prose'] = book_pages(prose, item.get('pageBreaks'))
        item['url'] = f'/story/{item["chapter"]}/{item["id"]}/'
        if item['url'] in urls:
            raise ValueError('Duplicate permanent URL')
        urls.add(item['url'])
        item['storyOrder'] = order
    registry = root/'content/published-paths.json'
    registered = read_json(registry)
    if not isinstance(registered, list) or any(not isinstance(u, str) or not re.fullmatch(r'/story/[a-z0-9-]+/[a-z0-9-]+/', u) for u in registered):
        raise ValueError('Published path registry must be an array of permanent story URLs')
    old_urls = set(registered)
    if old_urls - urls:
        raise ValueError('Previously published URLs cannot disappear; restore entries or plan explicit redirects: '+str(old_urls-urls))
    first = items[0]['url'] if items else None
    latest = items[-1]['url'] if items else None
    pages = {}
    def page(path, *args, **kwargs):
        pages[path] = layout(*args, **kwargs)
    def begin():
        return f'<a class="button" href="{first}">Begin the Story →</a>' if first else '<p class="lead forthcoming">Henry’s story begins here soon.</p>'
    opening_chapter = chapter_map[items[0]['chapter']] if items else chapters[0]
    # Draw the title and excerpt directly from approved, published material.
    # The manuscript itself and its paragraph boundaries remain untouched.
    opening_paragraphs = re.findall(r'<p(?:\s[^>]*)?>.*?</p>', items[0]['prose'], re.S) if items else []
    home_values = {
        'OPENING_TITLE': e(items[0]['title']) if items else 'Every life holds a story.',
        'CHAPTER_TITLE': e(opening_chapter.get('title') or 'The beginning'),
        'CHAPTER_NUMBER': e(opening_chapter['number']),
        'BEGIN': begin(), 'RESUME': resume(),
        'READING_NOTE': 'Read in order. Return to your saved place.' if first else 'The first installment is being prepared.',
        'EXCERPT': '<figure class="home-excerpt"><blockquote>'+opening_paragraphs[-1]+'</blockquote><figcaption class="eyebrow">From '+e(opening_chapter.get('title') or 'the story')+'</figcaption></figure>' if opening_paragraphs else '<p class="lead">The permanent digital home of Henry’s story.</p>',
    }
    home = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: home_values[m[1]], (root/'templates/home.html').read_text())
    page('index.html','A Serialized Illustrated Memoir','KATAMISKY is the permanent digital home of Henry’s serialized illustrated memoir.','/',home,home=True)
    story = f'''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">KATAMISKY</p><h1>A Serialized<br>Illustrated Memoir</h1>{begin()}<p>{'Read the published installments in order, or resume your saved place.' if first else 'The first installment is being prepared. Published writing will appear here, in reading order.'}</p>{resume()}</header><section aria-labelledby="chapters-title"><h2 id="chapters-title">Chapters</h2><ol class="index-list">'''
    for c in chapters:
        group = [i for i in items if i['chapter']==c['id']]
        label = e(c['title']) if c.get('title') else 'Chapter '+e(c['number'])
        state = str(len(group))+' published installment'+('s' if len(group)!=1 else '') if group else 'Not yet published'
        story += f'<li><a href="/story/{c["id"]}/"><span class="index-number">{e(c["number"])}</span><span><span class="item-title">{label}</span><span class="small">{state}</span></span><span aria-hidden="true">→</span></a></li>'
    story += '</ol></section><a class="button secondary" href="/archive/">Visit the archive</a></main>'
    page('story/index.html','Story','Read Henry’s serialized illustrated memoir in chapter and installment order.','/story/',story,'Story')
    for c in chapters:
        group = [i for i in items if i['chapter']==c['id']]
        title = c.get('title') or 'Chapter '+c['number']
        body = f'''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">Chapter {e(c['number'])}</p><h1>{e(title)}</h1><p class="lead">{'Read the published installments below.' if group else 'This chapter has not yet been published.'}</p>{'<p>The chapter title and first installment will appear when they are ready.</p>' if not c.get('title') else ''}<a href="/story/">← All chapters</a></header>{resume()}{'<section><h2>Installments</h2>'+listing(group, latest)+'</section>' if group else '<p>No installments are available yet.</p>'}<p><a class="button secondary" href="/archive/">Explore the archive →</a></p></main>'''
        page(f'story/{c["id"]}/index.html',f'Chapter {c["number"]}'+(' — '+c['title'] if c.get('title') else ''),f'Chapter {c["number"]} of Henry’s serialized illustrated memoir.',f'/story/{c["id"]}/',body,'Chapters')
    template = (root/'templates/story-installment.html').read_text()
    for n,item in enumerate(items):
        c = chapter_map[item['chapter']]
        values = {'CHAPTER_URL':f'/story/{c["id"]}/','CHAPTER_NUMBER':e(c['number']),'CHAPTER_TITLE':e(c['title']),'INSTALLMENT_NUMBER':str(n+1),'TITLE':e(item['title']),'DATE':e(item['date']),'DATE_LABEL':e(item['date']),'PAGE_NUMBER': ' · Page '+e(item['pageNumber']) if item.get('pageNumber') is not None else '', 'MEMOIR_TEXT':item['prose'], 'END_STATE': '<p class="small">You’re caught up with Henry’s story.</p>' if item['url']==latest else '', 'PREVIOUS':f'<a href="{items[n-1]["url"]}" rel="prev">← Previous</a>' if n else '<span></span>', 'NEXT':f'<a class="next" href="{items[n+1]["url"]}" rel="next" data-next>Next →</a>' if n+1<len(items) else '<span></span>', 'OBJECTS':object_module(item), 'EMAIL_MODULE':''}
        # Editorial comments remain in the excluded source, not the visitor document.
        markup = re.sub(r'<!--.*?-->','',template,flags=re.S)
        markup = re.sub(r'\{\{([A-Z_]+)\}\}',lambda m:values[m[1]],markup)
        page(item['url'].lstrip('/')+'index.html',item['title']+' — Chapter '+c['number'],item['description'],item['url'],markup,reader=True,document=item.get('document',False))
    archive = '<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">KATAMISKY</p><h1>The archive</h1><p class="lead">'+('Published installments, organized by chapter.' if items else 'The archive will grow with Henry’s story.')+'</p></header>'
    for c in chapters:
        group = [i for i in items if i['chapter']==c['id']]
        if group:
            archive += f'<section><h2>Chapter {e(c["number"])} · {e(c["title"])}</h2>'+listing(group,latest)+'</section>'
    if not items:
        archive += '<p>No memoir installments have been published yet.</p>'
    archive += '<p><a class="button secondary" href="/story/">Return to the story →</a></p></main>'
    page('archive/index.html','Archive','Browse published KATAMISKY installments by chapter and publication date.','/archive/',archive,'Archive')
    about = '''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">About KATAMISKY</p><h1>A Serialized<br>Illustrated Memoir</h1><p class="lead">The permanent digital home of Henry’s story.</p></header><div class="prose"><p>KATAMISKY is a long-form memoir, published in installments. The writing comes first, supported by original illustrations and clearly identified archival material.</p><h2>A living digital book</h2><p>Chapters and installments will remain accessible as the story grows. Each installment will have its own permanent address, and readers can save their place in their own browser without an account.</p><h2>Illustrations and archival material</h2><p>Artistic reconstructions will be labeled separately from authentic photographs and documents. Sources and dates will appear only when known.</p><h2>Related objects</h2><p>Objects directly connected to a memory may appear after an installment. Any commercial links will be separate from the memoir and clearly disclosed.</p><h2>Contact</h2><p><a href="mailto:hello@katamisky.com">hello@katamisky.com</a></p><p><a href="/story/">Explore the Story →</a></p></div></main>'''
    page('about.html','About','About KATAMISKY, the permanent digital home of Henry’s serialized illustrated memoir.','/about.html',about,'About')
    privacy = '''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">Reader privacy</p><h1>Your reading place<br>stays in your browser.</h1></header><div class="prose"><h2>Reading position</h2><p>When installments are available, this site can save the current installment address, title, order, approximate reading position, and save time in your browser using <code>katamisky_reader_progress</code>. This reading history is not sent to a server. Clearing this site’s browser data removes it.</p><p>No account is required. If local storage is unavailable, the text and navigation still work.</p><h2>Email updates</h2><p>No newsletter service is connected and this site does not collect email addresses through a signup form. This notice will be updated before an email service is enabled.</p><h2>Site resources</h2><p>Fonts, styles, and scripts are served with the site. No analytics, advertising scripts, or social feeds have been added. GitHub Pages processes requests to deliver the site under its own privacy practices.</p><h2>External links</h2><p>External services have their own privacy practices. Any future affiliate links will be disclosed separately from the story.</p></div></main>'''
    page('privacy/index.html','Reader Privacy','How KATAMISKY saves reading progress in your browser and handles site resources.','/privacy/',privacy)
    manifest = [{'url':i['url'],'chapter':'Chapter '+chapter_map[i['chapter']]['number'],'installment':i['title'],'storyOrder':i['storyOrder']} for i in items]
    pages['assets/js/story-manifest.js'] = '// Generated by scripts/build.py; published installments only.\nexport const installments = '+json.dumps(manifest,indent=2)+';\n'
    site_urls = ['/', '/story/', '/story/chapter-01/', '/archive/', '/about.html', '/privacy/'] + [f'/story/{c["id"]}/' for c in chapters if c['id']!='chapter-01'] + [i['url'] for i in items]
    pages['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+BASE+u+'</loc></url>' for u in site_urls)+'</urlset>\n'
    pages['robots.txt'] = 'User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n'
    if preview:
        for path in pages:
            if path.endswith('.html'):
                pages[path] = pages[path].replace('</head>', '<meta name="robots" content="noindex, nofollow"></head>').replace('<main ', '<aside class="container">LOCAL APPROVED-DRAFT PREVIEW — NOT PUBLISHED</aside><main ', 1)
        pages['robots.txt'] = 'User-agent: *\nDisallow: /\n'
    validate_pages(root, pages)
    for path,text in pages.items():
        target=root/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(text)
    registry.write_text(json.dumps(sorted(urls),indent=2)+'\n')
    if export:
        # Review/test artifact only. Pages still serves main/root using _config.yml.
        dest = root/'.qa/public'
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        for path in pages:
            target=dest/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/path,target)
        shutil.copytree(root/'assets',dest/'assets',dirs_exist_ok=True)
        shutil.copy2(root/'CNAME',dest/'CNAME')
        print('Public-only preview:',dest)
    print(f'Built {len(items)} published installments, {len(chapters)} chapter indexes, and public foundation.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--export',action='store_true')
    parser.add_argument('--preview-drafts', action='store_true', help='Isolated local preview of approved drafts; never changes production')
    args=parser.parse_args()
    try:
        if args.preview_drafts: preview_drafts(args.root.resolve())
        else: build(args.root.resolve(),args.export)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f'Build stopped: {error}\n')
