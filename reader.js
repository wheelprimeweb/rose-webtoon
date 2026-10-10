'use strict';
const body = document.body;
const toggle = document.getElementById('menu-toggle');
function showMenu(show) {
  body.classList.toggle('reading-mode', !show);
  toggle.setAttribute('aria-expanded', String(show));
  toggle.textContent = show ? '닫기' : '메뉴';
}
toggle.addEventListener('click', () => showMenu(body.classList.contains('reading-mode')));
document.querySelector('.reader').addEventListener('click', event => {
  if (!event.target.closest('button, a')) showMenu(body.classList.contains('reading-mode'));
});
document.addEventListener('keydown', event => { if (event.key === 'Escape') showMenu(false); });
document.querySelectorAll('.cut img').forEach(img => {
  const retry = img.nextElementSibling;
  let attempts = 0;
  const retryLoad = () => {
    retry.hidden = true;
    // Native-size optimized fallback first, preserved original on the second failure.
    img.removeAttribute('srcset');
    img.src = attempts++ ? img.dataset.original : img.getAttribute('src');
  };
  img.addEventListener('error', () => {
    if (attempts < 2) retryLoad();
    else retry.hidden = false;
  });
  img.addEventListener('load', () => { retry.hidden = true; });
  retry.addEventListener('click', retryLoad);
  if (img.complete && img.naturalWidth === 0) retryLoad();
});
