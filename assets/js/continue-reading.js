import {readProgress} from './reader-progress.js?v=structure-20260930';

function update() {
  const saved = readProgress();
  for (const box of document.querySelectorAll('[data-resume]')) {
    box.hidden = !saved;
    if (!saved) continue;
    const link = box.querySelector('a');
    link.href = saved.url + '#resume';
    link.textContent = `Continue from ${saved.installment} →`;
  }
  for (const marker of document.querySelectorAll('[data-position]')) {
    marker.hidden = marker.dataset.position !== saved?.url;
  }
}
update();
window.addEventListener('storage', update);
window.addEventListener('pageshow', update);
window.addEventListener('katamisky-progress', update);
