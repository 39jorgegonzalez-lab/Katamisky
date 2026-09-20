"""Verify author-approval and publication boundaries in isolated temporary trees."""
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publisher',ROOT/'scripts/build.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
count=0
with tempfile.TemporaryDirectory(prefix='katamisky-publish-') as temp:
    # Exercise an unnormalized caller path, as Windows temporary aliases can do.
    (Path(temp)/'path-normalization').mkdir()
    root=Path(temp)/'path-normalization'/'..'
    for folder in ['content','templates','assets']:shutil.copytree(ROOT/folder,root/folder)
    shutil.copy2(ROOT/'CNAME',root/'CNAME')
    def reset(entries,chapter='QA chapter — not a memoir title'):
        (root/'content/chapters.json').write_text(json.dumps([{'id':'chapter-01','number':'01','title':chapter}]))
        (root/'content/installments.json').write_text(json.dumps(entries))
        (root/'content/published-paths.json').write_text('[]')
    def rejects(entry,expected):
        global count
        reset([entry])
        try:module.build(root)
        except ValueError as error:
            assert expected in str(error),str(error);count+=1
        else:raise AssertionError('Expected refusal: '+expected)
    base={'id':'qa-only','chapter':'chapter-01','title':'QA fixture only','description':'QA metadata only','date':'2000-01-01','status':'published','authorApproved':True,'source':'qa.html','document':False,'objects':[]}
    (root/'content/qa.html').write_text('<p>QA fixture only. No memoir content.</p>')
    rejects({**base,'authorApproved':False},'author approval')
    rejects({**base,'date':None},'publication date')
    rejects({**base,'date':'2999-01-01'},'Future installment')
    rejects({**base,'id':'../unsafe'},'Invalid installment')
    rejects({**base,'status':'development'},'Only draft and published')
    (root/'content/qa.html').write_text('<p>[AUTHOR-SUPPLIED MEMOIR TEXT]</p>');rejects(base,'template fields')
    (root/'content/qa.html').write_text('<script>alert(1)</script>');rejects(base,'semantic text')
    (root/'content/qa.html').write_text('<p>QA fixture only. No memoir content.</p>')
    reset([{**base,'status':'draft'}]);module.build(root);assert 'export const installments = [];' in (root/'assets/js/story-manifest.js').read_text();count+=1
    reset([base,base]);
    try:module.build(root)
    except ValueError as error:assert 'Duplicate permanent URL' in str(error);count+=1
    else:raise AssertionError('Duplicate accepted')
    reset([base]);module.build(root)
    output=root/'story/chapter-01/qa-only/index.html'
    assert 'class="objects"' not in output.read_text() and 'newsletter-title' not in output.read_text();count+=1
    (root/'content/installments.json').write_text('[]')
    try:module.build(root)
    except ValueError as error:assert 'cannot disappear' in str(error);count+=1
    else:raise AssertionError('Published URL silently removed')
    obj={'title':'QA related-object link','url':'https://www.amazon.com/dp/QA?tag=katamisky-20','connection':'QA connection specimen only'}
    reset([{**base,'objects':[obj]}]);module.build(root)
    html=output.read_text();assert 'As an Amazon Associate I earn from qualifying purchases.' in html and 'rel="nofollow sponsored noopener"' in html and html.index('class="objects"')>html.index('class="story-body"');count+=1
    rejects({**base,'objects':[{**obj,'url':'https://www.amazon.com/dp/QA'}]},'affiliate tag')
    rejects({**base,'objects':[{**obj,'connection':''}]},'author-supplied connection')
    config=(ROOT/'_config.yml').read_text();assert not (ROOT/'.nojekyll').exists()
    for excluded in ['templates','content','scripts','tests','docs','node_modules']:
        assert '\n  - '+excluded+'\n' in config
    assert not list((ROOT/'.qa/public').glob('templates/*'))
    count+=1
print(f'PASS: {count} publication, commercial-integrity, permanent-URL, and export-boundary checks')
