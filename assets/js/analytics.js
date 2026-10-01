// Optional GA4. No Google request, cookie, or event before an explicit opt-in.
// This module is independent of the reader: a failure must never stop navigation.
const EVENTS = new Set(['begin_story', 'next_installment', 'previous_installment', 'continue_reading', 'archive_visit', 'installment_view', 'reading_25', 'reading_50', 'reading_75', 'reading_complete']);
const CONSENT_KEY = 'katamisky_analytics_consent';
const MILESTONE_PREFIX = 'katamisky_reading_events:';
const CONSENT_DAYS = 180;

export function eventParameters(context, origin) {
  const result = {};
  for (const key of ['installment_id', 'chapter_id', 'section', 'content_type']) {
    if (typeof context[key] === 'string' && /^[a-z0-9_-]{1,100}$/.test(context[key])) result[key] = context[key];
  }
  if (['home', 'story', 'archive', 'installment', 'chapter', 'about', 'privacy'].includes(origin)) result.navigation_origin = origin;
  return result;
}

export function createMeasurement(send, context) {
  let active = false, viewed = false;
  return {
    activate() {
      active = true;
      if (viewed) return;
      viewed = true;
      send('page_view', eventParameters(context));
      if (context.content_type === 'installment') send('installment_view', eventParameters(context));
      if (context.content_type === 'archive') send('archive_visit', eventParameters(context));
    },
    deactivate() { active = false; },
    event(name, origin) {
      if (active && EVENTS.has(name)) send(name, eventParameters(context, origin));
    }
  };
}

// Conservative engagement proxy: each book page needs active viewing time AND
// all ten vertical bands viewed. Restoring/jumping to the end supplies no credit.
// Text length stays in memory; no words, prose, coordinates or timings are sent.
export function createReadingMeter(weights, onMilestone, alreadySent = []) {
  const states = weights.map(weight => ({weight: Math.max(1, weight), seconds: 0, bands: new Set(), done: false}));
  const sent = new Set(alreadySent);
  const total = states.reduce((n, page) => n + page.weight, 0);
  return {
    sample(index, seconds, bands) {
      const state = states[index];
      if (!state || seconds <= 0 || seconds > 1.5 || !bands.length) return;
      state.seconds += seconds;
      bands.filter(n => Number.isInteger(n) && n >= 0 && n < 10).forEach(n => state.bands.add(n));
      state.done = state.bands.size === 10 && state.seconds >= Math.max(8, state.weight / 4);
      const fraction = states.reduce((n, page) => n + (page.done ? page.weight : 0), 0) / total;
      for (const [threshold, name] of [[.25, 'reading_25'], [.5, 'reading_50'], [.75, 'reading_75'], [1, 'reading_complete']]) {
        if (fraction >= threshold && !sent.has(name)) { sent.add(name); onMilestone(name, [...sent]); }
      }
    }
  };
}

function start(config) {
  const id = config.analytics?.measurementId;
  if (!config.analytics?.enabled || !/^G-[A-Z0-9]+$/.test(id || '') || location.origin !== 'https://www.katamisky.com') return;
  const context = config.context;
  const banner = document.querySelector('[data-analytics-consent]');
  let active = false, loaded = false, timer, lastActivity = performance.now(), lastTick = performance.now();
  const consent = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(CONSENT_KEY));
      return saved?.version === 1 && saved.expires > Date.now() && ['granted','denied'].includes(saved.value) ? saved.value : null;
    } catch { return null; }
  };
  function gtag() { window.dataLayer.push(arguments); }
  const common = {
    page_location: config.canonical,
    page_title: `KATAMISKY | ${context.content_type} | ${context.installment_id || context.chapter_id || ''}`,
    // Deliberately omit referrer paths, queries, titles and user-supplied text.
    page_referrer: '',
    send_to: id
  };
  const measurement = createMeasurement((name, params) => {
    if (active) gtag('event', name, {...common, ...params});
  }, context);
  function readerTracking() {
    const story = document.querySelector('.story-body');
    if (!story) return;
    const pages = [...story.querySelectorAll(':scope > .book-page')];
    if (!pages.length) pages.push(story);
    const key = MILESTONE_PREFIX + context.installment_id;
    let previous = [];
    try { previous = JSON.parse(sessionStorage.getItem(key) || '[]'); } catch { /* session-only fallback */ }
    if (!Array.isArray(previous)) previous = [];
    const meter = createReadingMeter(pages.map(p => p.textContent.trim().split(/\s+/).length), (name, sent) => {
      measurement.event(name);
      try { sessionStorage.setItem(key, JSON.stringify(sent)); } catch { /* never block reading */ }
    }, previous);
    lastTick = performance.now();
    timer = setInterval(() => {
      const now = performance.now(), delta = (now - lastTick) / 1000;
      lastTick = now;
      if (!active || document.visibilityState !== 'visible' || !document.hasFocus() || now - lastActivity > 60000) return;
      pages.forEach((page, index) => {
        if (page.hidden) return;
        const rect = page.getBoundingClientRect(), bands = [];
        if (rect.height <= 0) return;
        for (let band = 0; band < 10; band++) {
          const top = rect.top + rect.height * band / 10, bottom = top + rect.height / 10;
          if (Math.max(0, Math.min(innerHeight, bottom) - Math.max(0, top)) >= (bottom - top) * .5) bands.push(band);
        }
        meter.sample(index, delta, bands);
      });
    }, 1000);
  }
  function activate() {
    if (active) return;
    active = true;
    window['ga-disable-' + id] = false;
    if (!loaded) {
      loaded = true;
      window.dataLayer = window.dataLayer || [];
      // gtag's documented queue uses Arguments objects, not arbitrary objects.
      window.gtag = gtag;
      gtag('consent', 'default', {analytics_storage:'denied', ad_storage:'denied', ad_user_data:'denied', ad_personalization:'denied'});
      gtag('consent', 'update', {analytics_storage:'granted'});
      gtag('js', new Date());
      gtag('config', id, {...common, send_page_view:false, allow_google_signals:false, allow_ad_personalization_signals:false, cookie_expires:60*60*24*180, cookie_update:false});
      const script = document.createElement('script');
      script.async = true;
      script.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
      script.referrerPolicy = 'no-referrer';
      document.head.append(script);
    }
    measurement.activate();
    readerTracking();
  }
  function removeAnalyticsCookies() {
    for (const cookie of document.cookie.split(';')) {
      const name = cookie.split('=')[0].trim();
      if (!/^_ga(?:_|$)/.test(name)) continue;
      for (const domain of ['', '; domain=www.katamisky.com', '; domain=.katamisky.com']) document.cookie = name + '=; Max-Age=0; path=/' + domain + '; SameSite=Lax; Secure';
    }
  }
  function choose(value) {
    try {
      // Remove an old grant first: a full storage quota must not restore it.
      if (value === 'denied') localStorage.removeItem(CONSENT_KEY);
      localStorage.setItem(CONSENT_KEY, JSON.stringify({version:1,value,expires:Date.now()+CONSENT_DAYS*86400000}));
    } catch { /* choice applies to this document */ }
    if (banner) banner.hidden = true;
    const status = document.querySelector('[data-analytics-status]');
    if (status) status.textContent = value === 'granted' ? 'Optional analytics is allowed in this browser.' : 'Optional analytics is off in this browser.';
    if (value === 'granted') activate();
    else {
      active = false;
      window['ga-disable-' + id] = true;
      measurement.deactivate();
      clearInterval(timer);
      removeAnalyticsCookies();
      try { Object.keys(sessionStorage).filter(k => k.startsWith(MILESTONE_PREFIX)).forEach(k => sessionStorage.removeItem(k)); } catch { /* unavailable storage */ }
      // Unload the tag after withdrawal, avoiding denied-consent cookieless pings.
      if (loaded && consent() !== 'granted') location.reload();
      else if (loaded && status) status.textContent = 'Analytics is off on this page. Your browser could not save this choice. Clear this site’s browser data before returning to keep analytics off.';
    }
  }
  document.addEventListener('click', event => {
    const choice = event.target.closest('[data-analytics-choice]');
    if (choice) { choose(choice.dataset.analyticsChoice); return; }
    const link = event.target.closest('a[data-measure]');
    if (link) measurement.event(link.dataset.measure, context.content_type);
  });
  ['scroll', 'pointerdown', 'keydown'].forEach(name => addEventListener(name, () => {lastActivity = performance.now();}, {passive:true}));
  addEventListener('storage', event => { if (event.key === CONSENT_KEY) { window['ga-disable-' + id] = true; location.reload(); } });
  addEventListener('pagehide', () => clearInterval(timer));
  addEventListener('pageshow', event => { if (event.persisted) location.reload(); });
  const savedChoice = consent();
  const status = document.querySelector('[data-analytics-status]');
  if (status && savedChoice) status.textContent = savedChoice === 'granted' ? 'Optional analytics is allowed in this browser.' : 'Optional analytics is off in this browser.';
  if (savedChoice === 'granted') activate();
  else if (!consent() && banner) banner.hidden = false;
}

if (typeof document !== 'undefined') {
  try { start(JSON.parse(document.querySelector('#katamisky-config')?.textContent || '{}')); }
  catch { /* Optional measurement must never interfere with the book. */ }
}
