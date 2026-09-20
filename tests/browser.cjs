/* Production foundation + isolated reader QA. No test pages enter production. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {createRequire}=require('node:module');
const rr=process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?createRequire(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'package.json')):require;
const {chromium}=rr('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'.qa/foundation');fs.mkdirSync(out,{recursive:true});
const axe=process.env.AXE_PATH||require.resolve('axe-core/axe.min.js');
const opts={headless:true,executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox']};
const urls=['/','/story/','/story/chapter-01/','/archive/','/about.html','/privacy/'];
const one='/story/chapter-01/qa-fixture-1/',two='/story/chapter-01/qa-fixture-2/',key='katamisky_reader_progress';
const results=[],errors=[],requests=[];
function pass(name,details){results.push({name,result:'pass',details});console.log('PASS',name);}
function serve(dir){return new Promise(resolve=>{const s=http.createServer((req,res)=>{let f=path.resolve(dir,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!f.startsWith(dir+path.sep)&&f!==dir){res.writeHead(403).end();return;}try{if(fs.statSync(f).isDirectory())f=path.join(f,'index.html');const ext=path.extname(f);res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.woff2':'font/woff2','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'})[ext]||'application/octet-stream');res.end(fs.readFileSync(f));}catch{res.writeHead(404).end('Not found');}}).listen(0,'127.0.0.1',()=>resolve({server:s,base:'http://127.0.0.1:'+s.address().port}));});}
(async()=>{
 const production=await serve(path.join(root,'.qa/public')),fixture=await serve(path.join(root,'.qa/fixture/.qa/public'));
 const browser=await chromium.launch(opts);let lifecycle;
 try{
 const context=await browser.newContext({viewport:{width:1440,height:900}}),p=await context.newPage();
 p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 p.on('request',r=>requests.push(r.url()));
 await p.addInitScript(()=>{window.__cls=0;new PerformanceObserver(list=>{for(const e of list.getEntries())if(!e.hadRecentInput)__cls+=e.value;}).observe({type:'layout-shift',buffered:true});});
 for(const width of [320,360,375,390,430,768,1024,1280,1440]){
  await p.setViewportSize({width,height:900});
  for(const [base,list] of [[production.base,urls],[fixture.base,[one,two]]])for(const url of list){
   await p.goto(base+url);await p.evaluate(()=>document.fonts.ready);
   const v=await p.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,reader:document.querySelector('.story-body')?.getBoundingClientRect().width,cls:__cls}));
   assert(!v.overflow,`${width} ${url} overflow`);assert(v.cls<.1,`${url} CLS ${v.cls}`);
   if(width>=1024&&v.reader)assert(v.reader>=650&&v.reader<=700);
   if(width===390||width===1440){await p.addScriptTag({path:axe});const violations=await p.evaluate(async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})));assert.deepEqual(violations,[],JSON.stringify({url,width,violations}));}
   if([320,375,390,430,1440].includes(width)&&['/',one].includes(url)){
    const name=url==='/'?'home':'reader';await p.screenshot({path:path.join(out,`${name}-${width}.png`)});
    if(name==='reader'){await p.locator('.story-body').scrollIntoViewIfNeeded();await p.screenshot({path:path.join(out,`prose-${width}.png`)});}
   }
  }
  pass(`8 pages across public foundation and isolated reader at ${width}px`);
 }
 pass('16 axe WCAG A/AA scans: zero violations');assert.deepEqual(errors,[]);pass('No page, console, or asset errors in page matrix');
 await p.goto(production.base+'/');assert.equal(await p.locator('[data-resume]').isVisible(),false);assert.equal(await p.getByRole('link',{name:/Begin the Story/}).count(),0);assert((await p.locator('main').innerText()).includes('begins here soon'));
 await p.getByRole('link',{name:'Explore the Story →',exact:true}).click();await p.waitForURL('**/story/');
 await p.locator('.index-list a').click();await p.waitForURL('**/story/chapter-01/');await p.getByRole('link',{name:'Explore the archive →',exact:true}).click();await p.waitForURL('**/archive/');await p.getByRole('link',{name:'Return to the story →',exact:true}).click();await p.waitForURL('**/story/');await p.goto(production.base+'/');await p.getByRole('link',{name:'About the memoir',exact:true}).click();await p.waitForURL('**/about.html');pass('Production navigation and honest pre-publication state');
 for(const url of urls){await p.goto(production.base+url);assert.equal(await p.locator('form,.objects,a[href*="development-installment"]').count(),0);}
 // Retired prototype data must never expose a Continue Reading destination.
 await p.evaluate(k=>localStorage.setItem(k,JSON.stringify({version:1,url:'/story/chapter-01/development-installment-01/',storyOrder:1,savedAt:new Date().toISOString()})),key);await p.goto(production.base+'/');assert.equal(await p.locator('[data-resume]').isVisible(),false);pass('Retired prototype progress discarded; no fake Begin or newsletter');
 const sourceProbe=await context.request.get(production.base+'/templates/story-installment.html');assert.equal(sourceProbe.status(),404);pass('Editor template absent from public-only export');
 await p.goto(fixture.base+'/');await p.getByRole('link',{name:'Begin the Story →',exact:true}).click();await p.waitForURL('**'+one);assert.equal(await p.evaluate(k=>localStorage.getItem(k),key),null);await p.locator('[data-next]').click();await p.waitForURL('**'+two);await p.getByRole('link',{name:'← Previous',exact:true}).click();await p.waitForURL('**'+one);await p.getByRole('link',{name:'Chapter Index',exact:true}).click();await p.waitForURL('**/story/chapter-01/');pass('Future publication: Begin, Next, Previous, Chapter Index');
 await p.goto(fixture.base+two);await p.evaluate(k=>localStorage.removeItem(k),key);await p.reload();await p.evaluate(()=>window.scrollTo(0,document.querySelector('.story-body').offsetTop+650));await p.waitForFunction(k=>localStorage.getItem(k)!==null,key,{timeout:12000});
 const saved=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)),key);assert.equal(saved.url,two);assert(saved.fraction>=.12);await p.goto(fixture.base+'/');await p.locator('[data-resume] a').click();await p.waitForURL('**#resume');await p.waitForFunction(()=>scrollY>300);await p.reload();assert.equal(await p.evaluate(k=>JSON.parse(localStorage.getItem(k)).url,key),two);pass('Meaningful progress, Continue Reading, scroll restoration and refresh');
 for(const value of ['{bad','null',JSON.stringify({...saved,url:'https://example.invalid/'}),JSON.stringify({...saved,url:'/story/deleted/'}),JSON.stringify({...saved,version:9}),JSON.stringify({...saved,savedAt:'bad date'})]){await p.evaluate(([k,v])=>localStorage.setItem(k,v),[key,value]);await p.goto(fixture.base+'/');assert.equal(await p.locator('[data-resume]').isVisible(),false);}pass('Malformed/incompatible/deleted/external stored progress is harmless');
 const blocked=await browser.newContext();await blocked.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError');}}));const bp=await blocked.newPage();await bp.goto(fixture.base+one);await bp.locator('[data-next]').click();await bp.waitForURL('**'+two);await blocked.close();pass('Storage unavailable: core reading and navigation continue');
 const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:320,height:900}});const np=await nojs.newPage();await np.goto(fixture.base+one);assert((await np.locator('.story-body').innerText()).length>1000);await np.locator('[data-next]').click();await np.waitForURL('**'+two);await nojs.close();pass('No JavaScript: memoir HTML and Previous/Next remain usable');
 await p.goto(fixture.base+one);await p.evaluate(()=>document.fonts.ready);const fonts=await p.evaluate(()=>({loaded:[...document.fonts].filter(f=>f.status==='loaded').map(f=>({family:f.family,weight:f.weight,style:f.style})),requests:performance.getEntriesByType('resource').filter(r=>r.name.endsWith('.woff2')).map(r=>r.name.split('/').pop())}));assert(fonts.loaded.some(f=>f.family==='IBM Plex Mono'));assert(fonts.loaded.some(f=>f.family==='Source Serif 4'));pass('Reader fonts and contextual documentary font loaded',fonts);
 await p.goto(production.base+'/');await p.evaluate(()=>document.fonts.ready);const mainFonts=await p.evaluate(()=>performance.getEntriesByType('resource').filter(r=>r.name.endsWith('.woff2')).map(r=>r.name.split('/').pop()));assert(!mainFonts.some(n=>n.includes('plex')));pass('Homepage font requests',mainFonts);
 const fallback=await browser.newContext({viewport:{width:375,height:900}});await fallback.route('**/*.woff2',route=>route.abort());const fp=await fallback.newPage();await fp.goto(fixture.base+one);assert(await fp.locator('.story-body').isVisible());assert(!(await fp.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));await fallback.close();pass('Blocked-font fallback remains readable without overflow');
 await p.goto(production.base+'/');await p.keyboard.press('Tab');assert.equal(await p.evaluate(()=>document.activeElement.className),'skip-link');assert.equal(await p.evaluate(()=>getComputedStyle(document.activeElement).outlineStyle),'solid');await p.keyboard.press('Enter');assert.equal(await p.evaluate(()=>document.activeElement.id),'main');await p.emulateMedia({reducedMotion:'reduce'});assert(await p.evaluate(()=>matchMedia('(prefers-reduced-motion:reduce)').matches));
 const controls=await p.locator('.site-nav a,.button').evaluateAll(nodes=>nodes.map(n=>({label:n.textContent.trim(),height:n.getBoundingClientRect().height,width:n.getBoundingClientRect().width})));assert(controls.every(x=>x.height>=44));pass('Keyboard skip/focus, Enter, reduced motion, 44px navigation/CTA targets',controls);
 const profile=path.join(out,'browser-profile');lifecycle=await chromium.launchPersistentContext(profile,opts);let lp=await lifecycle.newPage();await lp.goto(fixture.base+'/');await lp.evaluate(([k,v])=>localStorage.setItem(k,JSON.stringify(v)),[key,saved]);await lifecycle.close();lifecycle=null;
 lifecycle=await chromium.launchPersistentContext(profile,opts);lp=await lifecycle.newPage();await lp.goto(fixture.base+'/');assert.equal(await lp.locator('[data-resume]').isVisible(),true);await lifecycle.close();lifecycle=null;fs.rmSync(profile,{recursive:true,force:true});pass('Actual browser process close/reopen retains reader progress');
 assert(requests.every(u=>u.startsWith(production.base)||u.startsWith(fixture.base)));assert(!requests.some(u=>/audio|\.mp3|\.wav/.test(u)));pass('No third-party or sound requests');
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({browser:browser.version(),timestamp:new Date().toISOString(),results},null,2));
 }finally{if(lifecycle)await lifecycle.close();await browser.close();production.server.close();fixture.server.close();}
})().catch(e=>{console.error(e);fs.writeFileSync(path.join(out,'failure.txt'),e.stack);process.exitCode=1;});
