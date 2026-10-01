// Pure unit/integration harness: no browser, network, real GA ID or events.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');
const {createMeasurement, createReadingMeter, eventParameters} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
let count = 0;
const test = (name, fn) => { fn(); count++; console.log('PASS:', name); };
const context = {content_type:'installment', chapter_id:'chapter-01', installment_id:'qa-only', section:'chapter'};
test('only explicitly allowed context is sent; prose and PII rejected', () => {
  assert.deepEqual(eventParameters({...context,title:'Private text',email:'x@example.com',chapter_id:'Contains spaces.'},'unknown'),{installment_id:'qa-only',section:'chapter',content_type:'installment'});
});
test('one pageview and installment view per document after activation; no backfill', () => {
  const events=[], tracker=createMeasurement((...args)=>events.push(args),context);
  tracker.event('begin_story'); assert.equal(events.length,0);
  tracker.activate(); tracker.activate();
  assert.deepEqual(events.map(e=>e[0]),['page_view','installment_view']);
  tracker.deactivate(); tracker.event('next_installment'); assert.equal(events.length,2);
});
test('all explicit navigation events; unknown events rejected', () => {
  const events=[], tracker=createMeasurement(name=>events.push(name),context); tracker.activate();
  for (const name of ['begin_story','next_installment','previous_installment','continue_reading','unknown']) tracker.event(name,'installment');
  assert.deepEqual(events.slice(2),['begin_story','next_installment','previous_installment','continue_reading']);
});
test('archive event belongs to the destination view and fires once', () => {
  const events=[], tracker=createMeasurement(name=>events.push(name),{content_type:'archive'}); tracker.activate(); tracker.activate();
  assert.deepEqual(events,['page_view','archive_visit']);
});
const allBands=Array.from({length:10},(_,i)=>i);
test('load, saved position, instant end jump and delayed timer give no completion', () => {
  const events=[], meter=createReadingMeter([100,100,100,100],e=>events.push(e));
  assert.deepEqual(events,[]); meter.sample(3,1,allBands); meter.sample(3,1000,allBands); assert.deepEqual(events,[]);
});
test('time alone cannot count unseen portions', () => {
  const events=[], meter=createReadingMeter([100],e=>events.push(e));
  for(let i=0;i<100;i++) meter.sample(0,1,[0,1,2]); assert.deepEqual(events,[]);
});
test('coverage alone cannot count a fast scroll', () => {
  const events=[], meter=createReadingMeter([100],e=>events.push(e));
  for(let i=0;i<10;i++) meter.sample(0,.1,[i]); assert.deepEqual(events,[]);
});
test('four milestones require timed coverage and are deduplicated', () => {
  const events=[], meter=createReadingMeter([100,100,100,100],e=>events.push(e));
  for(let p=0;p<4;p++) for(let t=0;t<30;t++) meter.sample(p,1,allBands);
  assert.deepEqual(events,['reading_25','reading_50','reading_75','reading_complete']);
  meter.sample(3,1,allBands); assert.equal(events.length,4);
});
test('resume at final page cannot complete skipped pages', () => {
  const events=[], meter=createReadingMeter([100,100,100,100],e=>events.push(e));
  for(let t=0;t<30;t++) meter.sample(3,1,allBands);
  assert.deepEqual(events,['reading_25']);
});
test('refresh does not repeat session milestone events', () => {
  const events=[], meter=createReadingMeter([4],e=>events.push(e),['reading_25','reading_50','reading_75','reading_complete']);
  for(let t=0;t<10;t++) meter.sample(0,1,allBands); assert.deepEqual(events,[]);
});

function harness({enabled=true,id='G-TESTONLY',choice=null,storageBlocked=false,writeBlocked=false,removeBlocked=false,cookies=''}={}) {
  const clicks={}, windowEvents={}, appended=[], stored=new Map(), cookieWrites=[];
  if(choice) stored.set('katamisky_analytics_consent',JSON.stringify({version:1,value:choice,expires:Date.now()+86400000}));
  const storage={getItem:k=>{if(storageBlocked)throw Error('blocked');return stored.get(k)||null;},setItem:(k,v)=>{if(storageBlocked||writeBlocked)throw Error('blocked');stored.set(k,v);},removeItem:k=>{if(removeBlocked)throw Error('blocked');stored.delete(k);}};
  const banner={hidden:true},status={textContent:''}; let reloads=0;
  const document={cookie:'',head:{append:s=>appended.push(s)},createElement:()=>({}),querySelector:s=>s==='#katamisky-config'?{textContent:JSON.stringify({analytics:{enabled,measurementId:id},context,canonical:'https://www.katamisky.com/story/chapter-01/qa-only/'})}:s==='[data-analytics-consent]'?banner:s==='[data-analytics-status]'?status:null,addEventListener:(name,fn)=>clicks[name]=fn};
  Object.defineProperty(document,'cookie',{get:()=>cookies,set:value=>cookieWrites.push(value)});
  const sandbox={document,window:{},location:{origin:'https://www.katamisky.com',reload:()=>reloads++},localStorage:storage,sessionStorage:storage,performance:{now:()=>0},Date,addEventListener:(name,fn)=>windowEvents[name]=fn,setInterval:()=>1,clearInterval:()=>{}};
  vm.runInNewContext(source.replaceAll('export function ','function '),sandbox);
  const choose=value=>clicks.click({target:{closest:selector=>selector==='[data-analytics-choice]'?{dataset:{analyticsChoice:value}}:null}});
  const clickLink=name=>clicks.click({target:{closest:selector=>selector==='a[data-measure]'?{dataset:{measure:name}}:null}});
  const events=()=>Array.from(sandbox.window.dataLayer||[]).filter(a=>a[0]==='event').map(a=>[a[1],a[2]]);
  return {sandbox,appended,banner,status,choose,clickLink,events,stored,windowEvents,cookieWrites,reloads:()=>reloads};
}
test('disabled configuration loads no tag, banner or measurement',()=>{const h=harness({enabled:false});assert.equal(h.appended.length,0);assert.equal(h.banner.hidden,true);assert.equal(h.events().length,0);});
test('invalid measurement ID cannot activate analytics',()=>{const h=harness({id:'invalid',choice:'granted'});assert.equal(h.appended.length,0);});
test('unknown and denied consent send no Google requests',()=>{const h=harness();assert.equal(h.appended.length,0);assert.equal(h.banner.hidden,false);h.choose('denied');assert.equal(h.appended.length,0);assert.equal(h.events().length,0);assert.equal(h.banner.hidden,true);});
test('grant queues one sanitized pageview; repeated grant is idempotent',()=>{const h=harness();h.choose('granted');h.choose('granted');assert.equal(h.appended.length,1);assert.deepEqual(h.events().map(e=>e[0]),['page_view','installment_view']);const p=h.events()[0][1];assert.equal(p.page_referrer,'');assert.ok(!p.page_title.includes('Private'));assert.ok(!p.page_location.includes('?'));const config=h.sandbox.window.dataLayer.find(a=>a[0]==='config')[2];assert.equal(config.send_page_view,false);assert.equal(config.allow_google_signals,false);});
test('saved consent activates on direct loads with one new view',()=>{const h=harness({choice:'granted'});assert.equal(h.appended.length,1);assert.equal(h.events().length,2);});
test('withdrawal disables collection and unloads Google tag',()=>{const h=harness({choice:'granted'});h.choose('denied');assert.equal(h.sandbox.window['ga-disable-G-TESTONLY'],true);assert.equal(h.reloads(),1);assert.equal(h.events().length,2);});
test('storage unavailable leaves reading unaffected; consent applies only now',()=>{const h=harness({storageBlocked:true});assert.equal(h.appended.length,0);h.choose('granted');assert.equal(h.appended.length,1);});
test('a full storage quota cannot restore an old grant after withdrawal',()=>{
  const h=harness({choice:'granted',writeBlocked:true}); h.choose('denied');
  assert.equal(h.stored.has('katamisky_analytics_consent'),false);
  assert.equal(h.reloads(),1); assert.equal(h.sandbox.window['ga-disable-G-TESTONLY'],true);
});
test('unmodifiable old consent stops this page without reloading into the grant',()=>{
  const h=harness({choice:'granted',writeBlocked:true,removeBlocked:true}); h.choose('denied'); h.clickLink('next_installment');
  assert.equal(h.reloads(),0); assert.equal(h.sandbox.window['ga-disable-G-TESTONLY'],true);
  assert.equal(h.events().length,2); assert.match(h.status.textContent,/could not save/);
});
test('withdrawal expires accessible GA cookie names on host and parent domains only',()=>{
  const h=harness({choice:'granted',cookies:'_ga=example; _ga_TESTONLY=example; unrelated=keep'}); h.choose('denied');
  assert.equal(h.cookieWrites.length,6);
  assert.ok(h.cookieWrites.every(value=>/^_ga(?:_|=)/.test(value)&&value.includes('Max-Age=0; path=/')));
  assert.ok(h.cookieWrites.some(value=>value.includes('domain=.katamisky.com')));
  assert.ok(h.cookieWrites.some(value=>value.includes('domain=www.katamisky.com')));
});
test('actual navigation handlers obey consent; hashes and unmeasured book-page clicks add no views',()=>{
  const h=harness(); h.clickLink('begin_story'); assert.equal(h.events().length,0); h.choose('granted');
  for(const name of ['begin_story','next_installment','previous_installment','continue_reading']) h.clickLink(name);
  const before=h.events().length; h.clickLink(undefined); h.windowEvents.hashchange?.({}); h.windowEvents.popstate?.({});
  assert.equal(h.events().length,before); assert.equal(h.events().filter(e=>e[0]==='page_view').length,1);
  assert.deepEqual(h.events().slice(2).map(e=>e[0]),['begin_story','next_installment','previous_installment','continue_reading']);
  h.choose('denied'); h.clickLink('next_installment'); assert.equal(h.events().length,before);
});
test('all advertising consent stays denied and config disables automatic views and advertising signals',()=>{
  const h=harness({choice:'granted'}), queue=h.sandbox.window.dataLayer;
  const defaults=queue.find(a=>a[0]==='consent'&&a[1]==='default')[2];
  for(const key of ['analytics_storage','ad_storage','ad_user_data','ad_personalization']) assert.equal(defaults[key],'denied');
  const update=queue.find(a=>a[0]==='consent'&&a[1]==='update')[2]; assert.deepEqual(Object.keys(update),['analytics_storage']);
  const config=queue.find(a=>a[0]==='config')[2];
  for(const key of ['send_page_view','allow_google_signals','allow_ad_personalization_signals']) assert.equal(config[key],false);
  assert.equal(config.cookie_update,false); assert.equal(config.cookie_expires,180*86400);
});
test('consent changes in another tab and back-forward cache restoration force a fresh consent check',()=>{
  const h=harness({choice:'granted'}); h.windowEvents.storage({key:'katamisky_analytics_consent'});
  assert.equal(h.sandbox.window['ga-disable-G-TESTONLY'],true); assert.equal(h.reloads(),1);
  h.windowEvents.pageshow({persisted:true}); assert.equal(h.reloads(),2);
});
console.log(`PASS: ${count} analytics checks; mocked transport only, no Google receipt claimed.`);
