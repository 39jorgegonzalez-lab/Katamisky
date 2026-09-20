#!/usr/bin/env python3
"""Create an unpublished starter, never memoir content or a publication decision."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from build import read_json, validate_metadata, SLUG


def create_draft(root, chapter, title, slug, description, publication_date, source):
    root = root.resolve()
    entries = read_json(root/'content/installments.json')
    chapters = read_json(root/'content/chapters.json')
    validate_metadata(root, chapters, entries)
    if not SLUG.fullmatch(slug): raise ValueError('Slug must be lowercase words separated by hyphens')
    if any(i['chapter'] == chapter and i['id'] == slug for i in entries):
        raise ValueError('Duplicate permanent URL; choose a new slug')
    if any(u == f'/story/{chapter}/{slug}/' for u in read_json(root/'content/published-paths.json')):
        raise ValueError('This URL already belongs to a published installment')
    if not source.endswith('.html') or Path(source).name != source or not SLUG.fullmatch(source[:-5]):
        raise ValueError('Source must be a simple lowercase-hyphenated filename ending .html')
    destination = root/'content'/source
    if destination.exists(): raise ValueError('Source already exists; nothing overwritten')
    item = {'id': slug, 'chapter': chapter, 'title': title.strip(), 'description': description.strip(),
            'date': publication_date, 'pageNumber': None, 'status': 'draft', 'authorApproved': False,
            'source': source, 'document': False, 'objects': []}
    # Exclusive creation prevents overwrite; failed validation rolls the new starter back.
    starter = (root/'templates/memoir-prose.html').read_text()
    with destination.open('x') as stream:
        stream.write(starter)
    temporary = None
    try:
        validate_metadata(root, chapters, entries + [item])
        with tempfile.NamedTemporaryFile(mode='w', dir=root/'content', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(entries + [item], indent=2, ensure_ascii=False)+'\n')
        os.replace(temporary, root/'content/installments.json')
    except Exception:
        destination.unlink()
        if temporary and temporary.exists(): temporary.unlink()
        raise
    return item


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print('PUBLIC REPOSITORY: write sensitive/unapproved memoir drafts elsewhere.\nThis creates only an unpublished starter; it never publishes.')
    try:
        chapter = input('Chapter ID [chapter-01]: ').strip() or 'chapter-01'
        title = input('Approved installment title: ').strip()
        slug = input('Permanent meaningful slug: ').strip()
        description = input('Approved short description: ').strip()
        publication_date = input('Intended publication date (YYYY-MM-DD): ').strip()
        source = input(f'Source filename [{slug}.html]: ').strip() or slug+'.html'
        item = create_draft(args.root, chapter, title, slug, description, publication_date, source)
        print(f"Created content/{item['source']}: status=draft, authorApproved=false. No public page created.")
    except (ValueError, OSError, EOFError, KeyboardInterrupt) as error:
        parser.exit(1, f'Draft creation stopped: {error}\n')
