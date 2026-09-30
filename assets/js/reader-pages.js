// Page boundaries are editorial metadata; paragraph nodes and their text stay intact.
export function createPageReader(story, onTurn) {
  const pages = [...story.querySelectorAll(':scope > .book-page')];
  const navigation = document.querySelector('[data-page-navigation]');
  if (pages.length < 2 || !navigation) return null;
  const previous = navigation.querySelector('[data-page-previous]');
  const next = navigation.querySelector('[data-page-next]');
  const label = navigation.querySelector('[data-page-label]');
  const end = document.querySelector('[data-story-end]');
  let current = 0;
  let gesture = null;
  const fromHash = () => {
    const match = /^#page-([1-9]\d*)$/.exec(location.hash);
    return match ? Math.min(pages.length - 1, Number(match[1]) - 1) : null;
  };
  function show(index, {interactive = false, focus = false, writeHash = false} = {}) {
    const target = Math.max(0, Math.min(pages.length - 1, index));
    const changed = target !== current;
    story.dataset.turn = target < current ? 'previous' : 'next';
    current = target;
    pages.forEach((page, i) => { page.hidden = i !== current; });
    previous.disabled = current === 0;
    previous.textContent = current === 0 ? '←' : `← ${current}`;
    previous.setAttribute('aria-label', current === 0 ? 'No previous page' : `Previous page, page ${current}`);
    next.disabled = current === pages.length - 1;
    next.textContent = next.disabled ? '→' : `${current + 2} →`;
    next.setAttribute('aria-label', next.disabled ? 'No next page' : `Next page, page ${current + 2}`);
    label.textContent = `Page ${current + 1} of ${pages.length}`;
    if (end) end.hidden = current !== pages.length - 1;
    if (writeHash) history.replaceState(null, '', `#page-${current + 1}`);
    if (interactive && changed) {
      story.scrollIntoView({block: 'start', behavior: 'instant'});
      if (focus) pages[current].focus({preventScroll: true});
      onTurn();
    }
  }
  previous.addEventListener('click', () => show(current - 1, {interactive: true, focus: true, writeHash: true}));
  next.addEventListener('click', () => show(current + 1, {interactive: true, focus: true, writeHash: true}));
  story.addEventListener('keydown', event => {
    if (event.target.closest('a,button,input,textarea,select') || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    show(current + (event.key === 'ArrowRight' ? 1 : -1), {interactive: true, focus: true, writeHash: true});
  });
  story.addEventListener('pointerdown', event => {
    gesture = null;
    if (!event.isPrimary || !['touch', 'pen'].includes(event.pointerType)) return;
    if (event.target.closest('a,button,input,textarea,select') || window.getSelection()?.toString()) return;
    // Keep browser edge gestures and ordinary text selection available.
    if (event.clientX < 24 || event.clientX > innerWidth - 24) return;
    gesture = {id: event.pointerId, x: event.clientX, y: event.clientY, time: performance.now()};
  }, {passive: true});
  story.addEventListener('pointermove', event => {
    if (!gesture || event.pointerId !== gesture.id) return;
    const dx = Math.abs(event.clientX - gesture.x), dy = Math.abs(event.clientY - gesture.y);
    if (dy > 16 && dy > dx * .7) gesture = null;
  }, {passive: true});
  story.addEventListener('pointercancel', () => { gesture = null; }, {passive: true});
  story.addEventListener('pointerup', event => {
    const start = gesture;
    gesture = null;
    if (!start || event.pointerId !== start.id || performance.now() - start.time > 900 || window.getSelection()?.toString()) return;
    const dx = event.clientX - start.x, dy = Math.abs(event.clientY - start.y);
    const threshold = Math.min(100, Math.max(65, story.clientWidth * .18));
    if (Math.abs(dx) < threshold || dy > Math.min(60, Math.abs(dx) * .45)) return;
    show(current + (dx < 0 ? 1 : -1), {interactive: true, writeHash: true});
  }, {passive: true});
  window.addEventListener('hashchange', () => {
    const index = fromHash();
    if (index !== null) show(index, {interactive: true, focus: true});
  });
  story.classList.add('reader-paged');
  navigation.hidden = false;
  show(fromHash() ?? 0);
  return {
    get index() { return current; },
    get count() { return pages.length; },
    get element() { return pages[current]; },
    restore(fraction) {
      const position = Math.min(pages.length - .000001, Math.max(0, fraction) * pages.length);
      show(Math.floor(position));
      return position - current;
    }
  };
}
