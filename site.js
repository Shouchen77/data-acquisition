const menuButton = document.querySelector('.menu-toggle');
const mobileMenu = document.querySelector('.mobile-menu');
function setMenu(open) {
  mobileMenu.classList.toggle('is-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单');
  mobileMenu.setAttribute('aria-hidden', String(!open)); mobileMenu.inert = !open;
}
setMenu(false);
menuButton.addEventListener('click', () => setMenu(!mobileMenu.classList.contains('is-open')));
mobileMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', event => { if (event.key === 'Escape' && mobileMenu.classList.contains('is-open')) { setMenu(false); menuButton.focus(); } });
document.querySelectorAll('[data-inquiry]').forEach(link => { link.href = 'contact.html?topic=' + encodeURIComponent(link.dataset.inquiry); });
document.addEventListener('click', event => {
  const link = event.target.closest('[data-inquiry]');
  if (link) link.href = 'contact.html?topic=' + encodeURIComponent(link.dataset.inquiry);
});
document.querySelectorAll('[data-copy-text]').forEach(button => button.addEventListener('click', async () => {
  const status = document.querySelector('#contact-action-status');
  const label = button.querySelector('[data-copy-label]');
  try { await navigator.clipboard.writeText(button.dataset.copyText); label.textContent='已复制'; status.textContent=`${button.dataset.copyName}已复制：${button.dataset.copyText}`; }
  catch { label.textContent='重新复制'; status.textContent=`请手动保存${button.dataset.copyName}：${button.dataset.copyText}`; }
}));
const inquiry = document.querySelector('#inquiry-context');
const topic = new URLSearchParams(location.search).get('topic');
if(inquiry && topic) { inquiry.hidden=false; inquiry.textContent=`咨询方向：${topic.slice(0,200)}。可通过电话、微信或邮箱沟通。`; }
