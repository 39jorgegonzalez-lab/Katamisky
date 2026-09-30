import { installments } from './story-manifest.js?v=installments-20260930-2';
import { createPageReader } from './reader-pages.js?v=book-pages-1';

export const STORAGE_KEY = 'katamisky_reader_progress';
const byURL = new Map(installments.map(item => [item.url, item]));

export function validateProgress(value) {
  if (!value || value.version !== 1 || typeof value.url !== 'string') return null;
  const item = byURL.get(value.url);
  if (!item || value.storyOrder !== item.storyOrder || typeof value.savedAt !== 'string' || !Number.isFinite(Date.parse(value.savedAt))) return null;
  const fraction = typeof value.fraction === 'number' && Number.isFinite(value.fraction) ? Math.max(0, Math.min(1, value.fraction)) : 0;
  return { ...item, version: 1, savedAt: value.savedAt, fraction };
}

export function readProgress() {
  try { return validateProgress(JSON.parse(localStorage.getItem(STORAGE_KEY))); }
  catch { return null; }
}

export function saveProgress(url, fraction = 0) {
  const item = byURL.get(url);
  if (!item) return false;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({version: 1, ...item, fraction: Number.isFinite(fraction) ? Math.max(0, Math.min(1, fraction)) : 0, savedAt: new Date().toISOString()}));
    window.dispatchEvent(new Event('katamisky-progress'));
    return true;
  } catch { return false; }
}

const story = document.querySelector('.story-body');
if (story && byURL.has(location.pathname)) {
  const indicator = document.querySelector('.reading-progress');
  const bar = indicator?.querySelector('span');
  const status = document.querySelector('.reading-status');
  let visibleSeconds = 0;
  let fraction = 0;
  let lastSave = -Infinity;
  let pending = false;
  let storageFailed = false;
  const pageReader = createPageReader(story, () => {measure(); save(true);});
  function measure() {
    const section = pageReader?.element || story;
    const rect = section.getBoundingClientRect();
    const start = rect.top + window.scrollY;
    const travel = Math.max(1, section.offsetHeight - window.innerHeight * .65);
    const offset = pageReader ? 0 : window.innerHeight * .15;
    const withinPage = Math.max(0, Math.min(1, (window.scrollY + offset - start) / travel));
    // A completed screen still belongs to this page when resuming later.
    fraction = pageReader ? (pageReader.index + Math.min(.999999, withinPage)) / pageReader.count : withinPage;
    if (bar) bar.style.transform = `scaleX(${fraction})`;
    indicator?.setAttribute('aria-valuenow', String(Math.round(fraction * 100)));
    if (status) status.textContent = `${Math.round(fraction * 100)}% of this installment${storageFailed ? ' · Reading position cannot be saved in this browser.' : ''}`;
    pending = false;
  }
  function save(force = false) {
    if (!force && (visibleSeconds < 8 || fraction < .12 || performance.now() - lastSave < 5000)) return;
    storageFailed = !saveProgress(location.pathname, fraction);
    lastSave = performance.now();
    measure();
  }
  function schedule() { if (!pending) { pending = true; requestAnimationFrame(measure); } }
  window.addEventListener('scroll', schedule, {passive: true});
  window.addEventListener('resize', schedule, {passive: true});
  const timer = setInterval(() => {
    if (document.visibilityState !== 'visible') return;
    visibleSeconds += 1;
    measure();
    save();
  }, 1000);
  document.querySelector('[data-next]')?.addEventListener('click', () => save(true));
  window.addEventListener('pagehide', () => {save(); clearInterval(timer);});
  document.addEventListener('visibilitychange', () => {if (document.visibilityState === 'hidden') save();});
  window.addEventListener('pageshow', event => {if (event.persisted) location.reload();});
  indicator.hidden = false;
  status.hidden = false;
  measure();
  const saved = readProgress();
  if (location.hash === '#resume' && saved?.url === location.pathname) {
    Promise.race([document.fonts.ready, new Promise(resolve => setTimeout(resolve, 1000))]).then(() => {
      const localFraction = pageReader ? pageReader.restore(saved.fraction) : saved.fraction;
      const section = pageReader?.element || story;
      const start = section.getBoundingClientRect().top + window.scrollY;
      const travel = Math.max(1, section.offsetHeight - window.innerHeight * .65);
      const offset = pageReader ? 0 : window.innerHeight * .15;
      window.scrollTo({top: Math.max(0, start + localFraction * travel - offset), behavior:'instant'});
      measure();
    });
  }
}
