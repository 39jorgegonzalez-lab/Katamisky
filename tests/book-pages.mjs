// Reader state regression checks; mocked DOM, not browser/layout verification.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../assets/js/reader-pages.js',import.meta.url),'utf8');
function reader(start,count,hash='') {
  const node=()=>({dataset:{},hidden:false,disabled:false,textContent:'',listeners:{},attributes:{},addEventListener(n,fn){this.listeners[n]=fn;},setAttribute(n,v){this.attributes[n]=v;},focus(){}});
  const pages=Array.from({length:count},(_,i)=>Object.assign(node(),{dataset:{bookPage:String(start+i)}}));
  const prev=node(),next=node(),label=node(),end=node(),nav=node(),story=node(),events={};let turns=0;
  nav.querySelector=s=>({'[data-page-previous]':prev,'[data-page-next]':next,'[data-page-label]':label}[s]);
  story.querySelectorAll=()=>pages;story.classList={add(){}};story.scrollIntoView=()=>{};story.clientWidth=340;
  const location={hash};const sandbox={document:{querySelector:s=>s==='[data-page-navigation]'?nav:end},location,history:{replaceState(a,b,h){location.hash=h;}},window:{addEventListener(n,f){events[n]=f;},getSelection:()=>null},innerWidth:390,performance:{now:()=>0}};
  vm.createContext(sandbox);vm.runInContext(source.replace('export function','function'),sandbox);
  const state=sandbox.createPageReader(story,()=>turns++);
  return {state,prev,next,label,story,pages,end,location,events,turns:()=>turns};
}
for(const [start,count] of [[1,5],[6,8],[14,7],[21,1]]) {
  const r=reader(start,count);
  assert.equal(r.label.textContent,`Page ${start}`);assert(r.prev.disabled);
  for(let i=1;i<count;i++) {
    assert.equal(r.next.attributes['aria-label'],`Next page, page ${start+i}`);
    r.next.listeners.click();assert.equal(r.label.textContent,`Page ${start+i}`);
    assert.equal(r.location.hash,`#page-${i+1}`);
    assert.equal(r.pages.filter(p=>!p.hidden).length,1);
  }
  assert(r.next.disabled);assert(!r.end.hidden);
  if(count>1){r.prev.listeners.click();assert.equal(r.label.textContent,`Page ${start+count-2}`);}
}
const legacy=reader(14,7,'#page-2');assert.equal(legacy.label.textContent,'Page 15');
assert.equal(legacy.state.restore(3/7),0);assert.equal(legacy.label.textContent,'Page 17');
legacy.story.listeners.keydown({target:{closest:()=>null},key:'ArrowRight',preventDefault(){}});
assert.equal(legacy.label.textContent,'Page 18');assert.equal(legacy.location.hash,'#page-5');
const touch={target:{closest:()=>null},isPrimary:true,pointerType:'touch',pointerId:1,clientX:270,clientY:150};
legacy.story.listeners.pointerdown(touch);legacy.story.listeners.pointerup({...touch,clientX:100});
assert.equal(legacy.label.textContent,'Page 19');
legacy.location.hash='#page-1';legacy.events.hashchange();assert.equal(legacy.label.textContent,'Page 14');
assert.equal(legacy.state.count,7);
console.log('PASS: continuous labels/arrows, single-page installment, unchanged local hashes, saved fractions, keyboard and touch state transitions (mocked DOM).');
