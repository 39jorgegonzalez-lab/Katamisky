"""Regression coverage for draft isolation, author helpers and fail-before-write validation."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build import build, preview_drafts
from new_installment import create_draft
ROOT=Path(__file__).resolve().parents[1]
count=0
with tempfile.TemporaryDirectory(prefix='katamisky-workflow-') as directory:
    root=Path(directory)
    for name in ('content','templates','assets'): shutil.copytree(ROOT/name,root/name)
    shutil.copy2(ROOT/'CNAME',root/'CNAME')
    (root/'content/chapters.json').write_text(json.dumps([{'id':'chapter-01','number':'01','title':'QA only'}]))
    metadata=root/'content/installments.json'
    base={'id':'qa-only','chapter':'chapter-01','title':'QA only','description':'Test fixture; not memoir.','date':'2000-01-01','status':'draft','authorApproved':False,'source':'qa.html'}
    prose=root/'content/qa.html';prose.write_text('<p>Test fixture. No autobiographical material.</p>')
    def reset(entry):
        metadata.write_text(json.dumps([entry] if isinstance(entry,dict) else entry))
        (root/'content/published-paths.json').write_text('[]')
    def snapshot():
        return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '.qa' not in p.parts and 'content' not in p.relative_to(root).parts}
    def reject(entry, expected):
        global count
        reset(entry); before=snapshot()
        try: build(root)
        except ValueError as error: assert expected.lower() in str(error).lower(),str(error)
        else: raise AssertionError('Expected refusal: '+expected)
        assert snapshot()==before, 'Failed build modified public output'
        count+=1
    for approval in (False,True):
        reset({**base,'authorApproved':approval});build(root,export=True)
        assert 'export const installments = [];' in (root/'assets/js/story-manifest.js').read_text()
        assert not (root/'story/chapter-01/qa-only/index.html').exists();count+=1
    before=snapshot(); original=metadata.read_bytes();registry=(root/'content/published-paths.json').read_bytes()
    preview_drafts(root)
    assert (root/'.qa/draft-preview/story/chapter-01/qa-only/index.html').exists()
    assert 'NOT PUBLISHED' in (root/'.qa/draft-preview/index.html').read_text()
    assert metadata.read_bytes()==original and registry==(root/'content/published-paths.json').read_bytes() and snapshot()==before;count+=1
    reset(base);preview_drafts(root)
    assert not (root/'.qa/draft-preview/story/chapter-01/qa-only/index.html').exists();count+=1
    published={**base,'status':'published','authorApproved':True}
    for key in ('title','description','date','source'):
        reject({**published,key:None},'Supply real')
    reject({**published,'authorApproved':'true'},'must be true or false')
    reject({**published,'date':'2026-99-99'},'YYYY-MM-DD')
    reject({**published,'date':'2999-01-01'},'Future installment')
    reject({**published,'source':'missing.html'},'Invalid prose source')
    reject({**published,'source':'../index.html'},'Invalid prose source')
    reject({**published,'pageNumber':True},'positive integer')
    reject([base,base],'Duplicate permanent URL')
    reject({'unrelated':'object'},'Only draft')
    reject([True],'array of objects')
    reject({**published,'title':'REPLACE WITH TITLE'},'template fields')
    for markup in ('<p><a href="/missing/">Broken</a></p>', '<img src="/assets/missing.png" alt="QA" width="1" height="1">', '<p><a href="/content/qa.html">Private source</a></p>', '<p>Unclosed'):
        prose.write_text(markup);reject(published,'validation failed')
    prose.write_text('<p>QA only.</p>')
    museum={'title':'QA reference','connection':'QA context','url':'https://example.org/reference'}
    reset({**published,'objects':[museum]});build(root)
    html=(root/'story/chapter-01/qa-only/index.html').read_text()
    assert 'rel="noopener"' in html and 'sponsored' not in html;count+=1
    reset([])
    before=metadata.read_bytes()
    for kwargs in ({'slug':'../escape'}, {'chapter':'missing'}, {'publication_date':'bad'}, {'source':'../unsafe.html'}):
        args=dict(chapter='chapter-01',title='QA helper',slug='qa-helper',description='QA only',publication_date='2000-01-01',source='qa-helper.html');args.update(kwargs)
        try:create_draft(root,**args)
        except ValueError:pass
        else:raise AssertionError('Invalid helper input accepted')
        assert metadata.read_bytes()==before and not (root/'content/qa-helper.html').exists();count+=1
    args=dict(chapter='chapter-01',title='QA helper',slug='qa-helper',description='QA only',publication_date='2000-01-01',source='qa-helper.html')
    created=create_draft(root,**args);assert created['status']=='draft' and created['authorApproved'] is False;count+=1
    before=metadata.read_bytes();source=(root/'content/qa-helper.html').read_bytes()
    try:create_draft(root,**args)
    except ValueError:pass
    else:raise AssertionError('Duplicate helper input accepted')
    assert metadata.read_bytes()==before and source==(root/'content/qa-helper.html').read_bytes();count+=1
    result=subprocess.run([sys.executable,str(ROOT/'scripts/new_installment.py'),'--root',str(root)], input='chapter-01\nQA prompt fixture\nqa-prompt\nQA only\n2000-01-01\n\n', text=True, capture_output=True)
    assert result.returncode==0 and 'status=draft' in result.stdout, result.stderr
    assert json.loads(metadata.read_text())[-1]['authorApproved'] is False;count+=1
    metadata.write_text('{invalid')
    before=snapshot()
    try:build(root)
    except ValueError as error:assert 'Cannot read installments.json' in str(error)
    else:raise AssertionError('Malformed JSON accepted')
    assert snapshot()==before;count+=1
print(f'PASS: {count} workflow, metadata, isolated-preview, helper and no-partial-publication checks')
