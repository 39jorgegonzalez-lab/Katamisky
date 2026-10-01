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
import hashlib
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

BASE = 'https://www.katamisky.com'
e = lambda value: html.escape(str(value), quote=True)
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
SOCIAL_FALLBACK = {'path':'/assets/images/site/katamisky-share.png', 'alt':'KATAMISKY — A Serialized Illustrated Memoir by Henry', 'width':1200, 'height':630}
ARCHIVE_PAGE_SIZE = 50


def json_script(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def schemas(title, description, url, crumbs, item=None, social=None):
    author = {'@type':'Person', '@id':BASE+'/about.html#author', 'name':'Henry', 'url':BASE+'/about.html'}
    website = {'@type':'WebSite', '@id':BASE+'/#website', 'url':BASE+'/', 'name':'KATAMISKY', 'inLanguage':'en', 'author':{'@id':author['@id']}}
    graph = [website, author]
    if crumbs:
        graph.append({'@type':'BreadcrumbList', '@id':BASE+url+'#breadcrumb', 'itemListElement':[{'@type':'ListItem','position':n,'name':name,'item':BASE+path} for n,(name,path) in enumerate(crumbs,1)]})
    if item:
        article = {'@type':'Article', '@id':BASE+url+'#article', 'headline':item['title'], 'description':description, 'author':{'@id':author['@id']}, 'datePublished':item['date'], 'mainEntityOfPage':BASE+url, 'url':BASE+url, 'isPartOf':{'@id':website['@id']}, 'inLanguage':'en', 'image':BASE+social['path']}
        if item.get('dateModified'): article['dateModified'] = item['dateModified']
        graph.append(article)
    return {'@context':'https://schema.org', '@graph':graph}


def chapter_label(chapter):
    return 'Prologue' if chapter.get('kind') == 'prologue' else 'Chapter '+chapter['number']


def chapter_heading(chapter):
    label = chapter_label(chapter)
    return label + (' — '+chapter['title'] if chapter.get('title') and chapter['title'] != label else '')


def installment_count(group):
    return str(len(group))+' published installment'+('s' if len(group) != 1 else '')


def installment_url(item):
    return item.get('permalink', f'/story/{item["chapter"]}/{item["id"]}/')


def resume():
    return '<div class="resume" data-resume hidden><p class="eyebrow">Welcome back.</p><a href="/story/" data-measure="continue_reading">Continue Reading</a></div>'


def layout(title, description, url, body, active='', reader=False, document=False, home=False, item=None, crumbs=None, context=None, analytics=None, versions=None):
    styles = ['fonts', 'site', 'components'] + (['home'] if home else []) + (['reader'] if reader else []) + (['document-font'] if document else [])
    versions = versions or {}
    links = '\n'.join(f'<link rel="stylesheet" href="/assets/css/{s}.css?v={versions.get(s, "1")}">' for s in styles)
    social = (item.get('socialImage') or SOCIAL_FALLBACK) if item else SOCIAL_FALLBACK
    context = context or {'content_type': 'home' if home else 'installment' if reader else 'archive' if url.startswith('/archive/') else 'story' if url=='/story/' else 'chapter' if url.startswith('/story/') else 'privacy' if url=='/privacy/' else 'about'}
    crumbs = crumbs if crumbs is not None else ([] if home else [('KATAMISKY','/'),(title,url)])
    config = {'analytics':analytics or {'enabled':False,'measurementId':''},'canonical':BASE+url,'context':context}
    consent = '''<aside class="container notice" aria-labelledby="analytics-choice-title" data-analytics-consent hidden><h2 id="analytics-choice-title">Optional analytics</h2><p>May KATAMISKY use Google Analytics to measure visits and reading navigation? It uses cookies and sends usage and device information to Google. The story works without it.</p><div class="actions"><button class="button secondary" type="button" data-analytics-choice="denied">Decline analytics</button><button class="button secondary" type="button" data-analytics-choice="granted">Allow analytics</button><a href="/privacy/#analytics">Privacy and choices</a></div></aside>''' if config['analytics']['enabled'] else ''
    nav = ''.join(f'<a href="{href}"'+(' aria-current="page"' if label == active else '')+f'>{label}</a>' for label, href in [('Story','/story/'),('Chapters','/story/#chapters-title'),('Archive','/archive/'),('About','/about.html')])
    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | KATAMISKY</title><meta name="description" content="{e(description)}">
<meta name="theme-color" content="#f8f5f1"><link rel="canonical" href="{BASE}{e(url)}">
<meta property="og:title" content="{e(title)} | KATAMISKY"><meta property="og:description" content="{e(description)}">
<meta property="og:type" content="{'article' if reader else 'website'}"><meta property="og:url" content="{BASE}{e(url)}">
<meta property="og:site_name" content="KATAMISKY"><meta property="og:locale" content="en_US">
<meta property="og:image" content="{BASE}{e(social['path'])}"><meta property="og:image:alt" content="{e(social['alt'])}"><meta property="og:image:width" content="{social['width']}"><meta property="og:image:height" content="{social['height']}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)} | KATAMISKY"><meta name="twitter:description" content="{e(description)}"><meta name="twitter:image" content="{BASE}{e(social['path'])}"><meta name="twitter:image:alt" content="{e(social['alt'])}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<script type="application/ld+json">{json_script(schemas(title, description, url, crumbs, item, social))}</script>
<script type="application/json" id="katamisky-config">{json_script(config)}</script>
<link rel="icon" type="image/svg+xml" href="/assets/images/site/favicon.svg">
{links}<script type="module" src="/assets/js/continue-reading.js?v={versions.get('continue-reading','1')}"></script>
<script type="module" src="/assets/js/analytics.js?v={versions.get('analytics','1')}"></script>
</head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="container header-inner"><a class="brand" href="/" aria-label="KATAMISKY home">KATAMISKY</a><nav class="site-nav" aria-label="Main">{nav}</nav></div></header>
{body}
{consent}
<footer class="site-footer"><div class="container footer-inner"><div><a class="brand" href="/">KATAMISKY</a><p>A Serialized Illustrated Memoir</p></div><nav aria-label="Footer"><a href="/story/">Story</a><a href="/archive/">Archive</a><a href="/about.html">About</a><a href="/privacy/">Privacy</a></nav></div></footer>
</body></html>\n'''


def listing(group, latest_url, start=1):
    rows = []
    for installment_number, item in enumerate(group, start):
        latest = ' · Latest installment' if item['url'] == latest_url else ''
        rows.append(f'<li><a href="{item["url"]}"><span class="index-number">{installment_number:02}</span><span><span class="item-title">{e(item["title"])}</span><span class="small"><time datetime="{item["date"]}">{item["date"]}</time>{latest}</span><span class="current-position" data-position="{item["url"]}" hidden>Your saved reading position</span></span><span aria-hidden="true">→</span></a></li>')
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
        if chapter.get('kind', 'chapter') not in ('chapter', 'prologue'):
            raise ValueError('Section kind must be chapter or prologue')
        if chapter.get('kind') == 'prologue' and chapter['number']:
            raise ValueError('The prologue is unnumbered')
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
        url = installment_url(item)
        if not isinstance(url, str) or not re.fullmatch(r'/story/[a-z0-9-]+/[a-z0-9-]+/', url):
            raise ValueError('Invalid permanent installment URL')
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
        if item.get('dateModified'):
            try:
                modified = date.fromisoformat(item['dateModified'])
                if modified < parsed or modified > date.today(): raise ValueError()
            except (TypeError, ValueError): raise ValueError('dateModified must be a real date between publication and today')
        if item.get('socialImage') is not None:
            image = item['socialImage']
            if not isinstance(image, dict) or not isinstance(image.get('path'), str) or not re.fullmatch(r'/assets/images/[a-zA-Z0-9/_-]+\.(?:png|jpg|jpeg|webp)', image['path']) or not (root/image['path'].lstrip('/')).is_file():
                raise ValueError('socialImage must reference an existing local raster image')
            if not isinstance(image.get('alt'), str) or not image['alt'].strip() or any(type(image.get(k)) is not int or image[k] <= 0 for k in ('width','height')):
                raise ValueError('socialImage needs supplied alt text and positive dimensions')
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
    settings_path = root/'content/site-settings.json'
    analytics = read_json(settings_path).get('analytics', {}) if settings_path.exists() else {'enabled':False,'measurementId':''}
    if type(analytics.get('enabled')) is not bool or not isinstance(analytics.get('measurementId'), str) or (analytics['enabled'] and not re.fullmatch(r'G-[A-Z0-9]+', analytics['measurementId'])):
        raise ValueError('Analytics needs enabled boolean and a real G- measurement ID before activation')
    if preview: analytics = {'enabled':False,'measurementId':''}
    validate_metadata(root, chapters, entries)
    chapter_map = {c['id']: c for c in chapters}
    if len(chapter_map) != len(chapters) or 'chapter-01' not in chapter_map:
        raise ValueError('Chapters need unique IDs and a Chapter 01 index')
    for c in chapters:
        if not SLUG.fullmatch(c['id']):
            raise ValueError('Invalid chapter slug')
    if any(i.get('status') not in ('draft','published') for i in entries):
        raise ValueError('Only draft and published statuses are supported; no public development installments')
    chapter_order = {c['id']: n for n, c in enumerate(chapters)}
    items = sorted([dict(i) for i in entries if i['status'] == 'published'], key=lambda i: chapter_order[i['chapter']])
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
        item['url'] = installment_url(item)
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
    # Version the entire reader import chain on every publication; cached
    # manifests must never strand returning readers on an obsolete hierarchy.
    digest = lambda text: hashlib.sha256(text.encode()).hexdigest()[:12]
    manifest = [{'url':i['url'],'chapter':chapter_heading(chapter_map[i['chapter']]),'installment':i['title'],'storyOrder':i['storyOrder']} for i in items]
    manifest_js = '// Generated by scripts/build.py; published installments only.\nexport const installments = '+json.dumps(manifest,indent=2)+';\n'
    pages['assets/js/story-manifest.js'] = manifest_js
    progress = (root/'assets/js/reader-progress.js').read_text()
    progress = re.sub(r"story-manifest.js\?v=[^']+", 'story-manifest.js?v='+digest(manifest_js), progress)
    progress = re.sub(r"reader-pages.js\?v=[^']+", 'reader-pages.js?v='+digest((root/'assets/js/reader-pages.js').read_text()), progress)
    pages['assets/js/reader-progress.js'] = progress
    continuation = re.sub(r"reader-progress.js\?v=[^']+", 'reader-progress.js?v='+digest(progress), (root/'assets/js/continue-reading.js').read_text())
    pages['assets/js/continue-reading.js'] = continuation
    versions = {p.stem:digest(p.read_text()) for p in (root/'assets/css').glob('*.css')}
    versions.update({'continue-reading':digest(continuation),'analytics':digest((root/'assets/js/analytics.js').read_text())})
    def page(path, *args, **kwargs):
        pages[path] = layout(*args, analytics=analytics, versions=versions, **kwargs)
    def begin():
        return f'<a class="button" href="{first}" data-measure="begin_story">Begin the Story →</a>' if first else '<p class="lead forthcoming">Henry’s story begins here soon.</p>'
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
        label = e(chapter_heading(c))
        state = installment_count(group) if group else 'Not yet published'
        story += f'<li><a href="/story/{c["id"]}/"><span class="index-number">{e(c["number"])}</span><span><span class="item-title">{label}</span><span class="small">{state}</span></span><span aria-hidden="true">→</span></a></li>'
    story += '</ol></section><a class="button secondary" href="/archive/">Visit the archive</a></main>'
    page('story/index.html','Story','Read Henry’s serialized illustrated memoir in chapter and installment order.','/story/',story,'Story')
    for c in chapters:
        group = [i for i in items if i['chapter']==c['id']]
        title = c.get('title') or 'Chapter '+c['number']
        body = f'''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">{e(chapter_label(c))}</p><h1>{e(title)}</h1><p class="lead">{installment_count(group) if group else 'This chapter has not yet been published.'}</p>{'<p>The chapter title and first installment will appear when they are ready.</p>' if not c.get('title') else ''}<a href="/story/">← All chapters</a></header>{resume()}{'<section><h2>Installments</h2>'+listing(group, latest)+'</section>' if group else '<p>No installments are available yet.</p>'}<p><a class="button secondary" href="/archive/">Explore the archive →</a></p></main>'''
        page(f'story/{c["id"]}/index.html',chapter_heading(c),chapter_heading(c)+' of Henry’s serialized illustrated memoir.',f'/story/{c["id"]}/',body,'Chapters', crumbs=[('KATAMISKY','/'),('Story','/story/'),(chapter_heading(c),f'/story/{c["id"]}/')], context={'content_type':'chapter','chapter_id':c['id'],'section':c.get('kind','chapter')})
    template = (root/'templates/story-installment.html').read_text()
    for n,item in enumerate(items):
        c = chapter_map[item['chapter']]
        values = {'CHAPTER_URL':f'/story/{c["id"]}/','CHAPTER_NUMBER':e(c['number']),'CHAPTER_TITLE':e(c['title']),'INSTALLMENT_NUMBER':str(n+1),'TITLE':e(item['title']),'DATE':e(item['date']),'DATE_LABEL':e(item['date']),'PAGE_NUMBER': ' · Page '+e(item['pageNumber']) if item.get('pageNumber') is not None else '', 'MEMOIR_TEXT':item['prose'], 'END_STATE': '<p class="small">You’re caught up with Henry’s story.</p>' if item['url']==latest else '', 'PREVIOUS':f'<a href="{items[n-1]["url"]}" rel="prev">← Previous</a>' if n else '<span></span>', 'NEXT':f'<a class="next" href="{items[n+1]["url"]}" rel="next" data-next>Next →</a>' if n+1<len(items) else '<span></span>', 'OBJECTS':object_module(item), 'EMAIL_MODULE':''}
        values.update(CHAPTER_LABEL=e(chapter_label(c)), INDEX_LABEL='Prologue Index' if c.get('kind') == 'prologue' else 'Chapter Index', INSTALLMENT_NUMBER=str(sum(i['chapter'] == item['chapter'] for i in items[:n+1])))
        # Editorial comments remain in the excluded source, not the visitor document.
        markup = re.sub(r'<!--.*?-->','',template,flags=re.S)
        markup = re.sub(r'\{\{([A-Z_]+)\}\}',lambda m:values[m[1]],markup)
        markup = markup.replace('rel="prev"', 'rel="prev" data-measure="previous_installment"').replace('rel="next"', 'rel="next" data-measure="next_installment"')
        page(item['url'].lstrip('/')+'index.html',item['title']+' — '+chapter_label(c),item['description'],item['url'],markup,reader=True,document=item.get('document',False),item=item,crumbs=[('KATAMISKY','/'),('Story','/story/'),(chapter_heading(c),f'/story/{c["id"]}/'),(item['title'],item['url'])],context={'content_type':'installment','installment_id':item['id'],'chapter_id':c['id'],'section':c.get('kind','chapter')})
    archive_urls = []
    archive_chunks = [items[n:n+ARCHIVE_PAGE_SIZE] for n in range(0,len(items),ARCHIVE_PAGE_SIZE)] or [[]]
    for page_number, chunk in enumerate(archive_chunks, 1):
        archive_url = '/archive/' if page_number == 1 else f'/archive/page/{page_number}/'
        archive_urls.append(archive_url)
        title = 'Archive' if page_number == 1 else f'Archive — Page {page_number}'
        archive = '<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">KATAMISKY</p><h1>The archive</h1><p class="lead">'+('Published installments, organized by chapter.' if items else 'The archive will grow with Henry’s story.')+'</p></header>'
        for c in chapters:
            full_group = [i for i in items if i['chapter']==c['id']]
            group = [i for i in chunk if i['chapter']==c['id']]
            if group:
                archive += f'<section><h2>{e(chapter_heading(c))}</h2><p class="small">{installment_count(full_group)}</p>'+listing(group,latest,full_group.index(group[0])+1)+'</section>'
        if not items: archive += '<p>No memoir installments have been published yet.</p>'
        if len(archive_chunks) > 1:
            archive += '<nav class="actions" aria-label="Archive pages">'
            if page_number > 1:
                previous = '/archive/' if page_number == 2 else f'/archive/page/{page_number-1}/'
                archive += f'<a class="button secondary" rel="prev" href="{previous}">← Previous archive page</a>'
            archive += f'<span>Page {page_number} of {len(archive_chunks)}</span>'
            if page_number < len(archive_chunks): archive += f'<a class="button secondary" rel="next" href="/archive/page/{page_number+1}/">Next archive page →</a>'
            archive += '</nav>'
        archive += '<p><a class="button secondary" href="/story/">Return to the story →</a></p></main>'
        description = 'Browse published KATAMISKY installments by chapter and publication date.' + (f' Archive page {page_number}.' if page_number > 1 else '')
        page(archive_url.lstrip('/')+'index.html',title,description,archive_url,archive,'Archive')
    about = '''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">About KATAMISKY</p><h1 id="author">A Serialized<br>Illustrated Memoir</h1><p class="lead">The permanent digital home of Henry’s story.</p></header><div class="prose"><p>KATAMISKY is a long-form memoir, published in installments. The writing comes first, supported by original illustrations and clearly identified archival material.</p><h2>A living digital book</h2><p>Chapters and installments will remain accessible as the story grows. Each installment will have its own permanent address, and readers can save their place in their own browser without an account.</p><h2>Illustrations and archival material</h2><p>Artistic reconstructions will be labeled separately from authentic photographs and documents. Sources and dates will appear only when known.</p><h2>Related objects</h2><p>Objects directly connected to a memory may appear after an installment. Any commercial links will be separate from the memoir and clearly disclosed.</p><h2>Contact</h2><p><a href="mailto:hello@katamisky.com">hello@katamisky.com</a></p><p><a href="/story/">Explore the Story →</a></p></div></main>'''
    page('about.html','About','About KATAMISKY, the permanent digital home of Henry’s serialized illustrated memoir.','/about.html',about,'About')
    privacy = '''<main id="main" tabindex="-1" class="container"><header class="page-heading"><p class="eyebrow">Reader privacy</p><h1>Your reading place<br>stays in your browser.</h1></header><div class="prose"><h2>Reading position</h2><p>When installments are available, this site can save the current installment address, title, order, approximate reading position, and save time in your browser using <code>katamisky_reader_progress</code>. This reading history is not sent to a server. Clearing this site’s browser data removes it.</p><p>No account is required. If local storage is unavailable, the text and navigation still work.</p><h2>Email updates</h2><p>No newsletter service is connected and this site does not collect email addresses through a signup form. This notice will be updated before an email service is enabled.</p><h2>Site resources</h2><p>Fonts, styles, and scripts are served with the site. No advertising scripts or social feeds are used. Optional analytics is described below. GitHub Pages processes requests to deliver the site under its own privacy practices.</p><h2>External links</h2><p>External services have their own privacy practices. Any future affiliate links will be disclosed separately from the story.</p></div></main>'''
    analytics_notice = '<h2 id="analytics">Optional analytics</h2>'
    if analytics['enabled']:
        analytics_notice += '<p>Google Analytics 4 loads only after you choose to allow it. It measures visits, installment navigation, and estimates of reading progress using cookies and usage and device information sent to Google. It does not receive manuscript text, your saved reading bookmark, names, email addresses, or form entries from this site. We do not enable advertising personalization, session recording, or fingerprinting.</p><p>Your choice is kept in this browser for up to 180 days under <code>katamisky_analytics_consent</code>. Analytics cookies last up to 180 days. Milestone event flags remain in session storage for this browser tab to prevent repeat events. These estimates cannot prove that a person read or understood the text.</p><p>Declining leaves the story and saved reading position available. You can change your choice here. Withdrawing stops new measurement and removes this site’s analytics cookies; it cannot undo data already received by Google.</p><p data-analytics-status>Choose whether to allow optional analytics in this browser.</p><div class="actions"><button type="button" class="button secondary" data-analytics-choice="denied">Decline analytics</button><button type="button" class="button secondary" data-analytics-choice="granted">Allow analytics</button></div>'
    else:
        analytics_notice += '<p>Optional Google Analytics support is prepared but disabled. No Google Analytics tag loads and no analytics events are sent. If it is enabled in the future, readers will be offered a choice before measurement starts.</p>'
    privacy = privacy.replace('<h2>External links</h2>',analytics_notice+'<h2>External links</h2>')
    page('privacy/index.html','Reader Privacy','How KATAMISKY saves reading progress in your browser and handles site resources.','/privacy/',privacy)
    site_urls = ['/', '/story/', '/story/chapter-01/', '/about.html', '/privacy/'] + archive_urls + [f'/story/{c["id"]}/' for c in chapters if c['id']!='chapter-01'] + [i['url'] for i in items]
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
