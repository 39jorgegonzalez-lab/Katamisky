"""Build an isolated reader fixture, NEVER used as production content."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
fixture=root/'.qa/fixture'
if fixture.exists():shutil.rmtree(fixture)
fixture.mkdir(parents=True)
for folder in ['assets','templates','content']:
    shutil.copytree(root/folder,fixture/folder)
shutil.copy2(root/'CNAME',fixture/'CNAME')
(fixture/'content/published-paths.json').write_text('[]')
(fixture/'content/chapters.json').write_text('[{"id":"chapter-01","number":"01","title":"QA chapter — test data only"}]')
prose='<p>QA FIXTURE ONLY. This paragraph tests line length and reading progress. It is not Henry’s memoir and contains no autobiographical claim.</p>'*12
prose+='<h2>Typography fixture</h2><p class="story-dialogue">QA dialogue treatment only.</p><p class="inner-thought">QA italic treatment only.</p><p class="story-emphasis">QA emphasis only.</p><div class="environmental-text">QA SIGN SPECIMEN</div>'
prose+='<figure class="document"><figcaption>QA transcription specimen — no authentic document</figcaption><pre class="document-text">QA TRANSCRIPTION SAMPLE</pre></figure><aside class="editorial-note">QA editorial label: Memory uncertain</aside>'
# Real optimized image fixture with exact dimensions; copied ONLY to the isolated site.
import struct, zlib
chunk=lambda tag,data:struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
raw=(b'\x00'+bytes([246,237,223])*640)*360
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',640,360,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')
(fixture/'assets/images/site/qa.png').write_bytes(png)
prose+='<figure class="illustration illustration--narrative"><img src="/assets/images/site/qa.png" width="640" height="360" alt="Plain ivory rectangle used only as a layout fixture" loading="lazy"><figcaption>QA layout image; no historical scene depicted.</figcaption></figure>'
items=[]
for n in [1,2]:
    (fixture/f'content/qa-{n}.html').write_text(prose)
    items.append({'id':f'qa-fixture-{n}','chapter':'chapter-01','title':f'QA fixture {n} — not memoir','description':'Isolated test fixture, never for publication.','date':'2000-01-01','pageNumber':n,'status':'published','authorApproved':True,'source':f'qa-{n}.html','document':True,'objects':[]})
items[1]['objects']=[{'title':'QA related object — test display only','url':'https://www.amazon.com/dp/QA?tag=katamisky-20','connection':'QA layout specimen, not a recommendation or a connection to Henry.'}]
(fixture/'content/installments.json').write_text(json.dumps(items))
subprocess.run([sys.executable,str(root/'scripts/build.py'),'--root',str(fixture),'--export'],check=True)
print('Fixture output:',fixture/'.qa/public')
