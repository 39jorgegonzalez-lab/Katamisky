#!/usr/bin/env python3
"""Prepare a private browser density review, or validate recorded editorial pagination.

Browser measurements are required: this tool never estimates lines from word counts.
"""
import argparse, hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def signature(root):
    paths = ['assets/css/site.css', 'assets/css/reader.css']
    paths += [str(p.relative_to(root)) for p in sorted((root/'assets/fonts').rglob('*')) if p.is_file()]
    return hashlib.sha256(b''.join((root/p).read_bytes() for p in paths)).hexdigest()


def check(root=ROOT, record=None):
    if record is None: record = json.loads((root/'content/page-density.json').read_text())
    assert record['canonicalViewport'] == 1440 and record['readerWidth'] == 680
    assert record['layoutSignature'] == signature(root), 'Reader typography changed: repeat browser density review'
    entries = json.loads((root/'content/installments.json').read_text())
    for item in entries:
        if item['status'] != 'published': continue
        evidence = record['installments'].get(item['id'])
        assert evidence, f"{item['id']}: browser density review required before publishing"
        assert evidence['sourceSHA256'] == hashlib.sha256((root/'content'/item['source']).read_bytes()).hexdigest(), f"{item['id']}: source changed; repeat density review"
        assert not evidence.get('shortWraps') or evidence.get('wrapException'), f"{item['id']}: short wraps need layout correction or a documented exception"
        lines = evidence['paragraphLines']
        paragraphs = re.findall(r'<p(?:\s[^>]*)?>.*?</p>', (root/'content'/item['source']).read_text(), re.S)
        assert len(lines) == len(paragraphs) and all(type(n) is int and n > 0 for n in lines)
        assert evidence['pageBreaks'] == item['pageBreaks'], f"{item['id']}: page breaks changed; repeat review"
        ends = [0, *item['pageBreaks'], len(lines)]
        for number, (a, b) in enumerate(zip(ends, ends[1:]), 1):
            count = sum(lines[a:b])
            assert 28 <= count <= 31 or evidence.get('exceptions', {}).get(str(number)), f"{item['id']} page {number}: {count} lines needs a literary explanation, not forced prose edits"
    print('PASS: all published installments have current desktop density evidence; out-of-window pages have literary explanations.')


def prepare(root=ROOT):
    from build import build
    build(root, export=True)
    items = json.loads((root/'content/installments.json').read_text())
    data = [{'id':i['id'], 'url':i.get('permalink', f"/story/{i['chapter']}/{i['id']}/"),
             'pageBreaks':i['pageBreaks'], 'sourceSHA256':hashlib.sha256((root/'content'/i['source']).read_bytes()).hexdigest()}
            for i in items if i['status'] == 'published']
    template = (root/'scripts/page-density-review.html').read_text()
    data_json = json.dumps({'layoutSignature':signature(root), 'items':data}).replace('<','\\u003c')
    (root/'.qa/public/density-review.html').write_text(template.replace('/*REVIEW_DATA*/', data_json))
    print('Open /density-review.html on the private local preview. It measures real rendered lines at desktop and mobile widths. Never publish this review page.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--record', type=Path, help='Record a completed browser report after adding literary exception reasons')
    args=parser.parse_args()
    if args.prepare: prepare()
    elif args.record:
        record=json.loads(args.record.read_text())
        check(record=record)
        assert record.get('mobile') and not any(x['overflow'] for x in record['mobile']), 'Resolve responsive overflow before recording'
        (ROOT/'content/page-density.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
    else: check()
