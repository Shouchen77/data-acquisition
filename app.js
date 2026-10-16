const PAGE_SIZE = 12;
const state = { all: [], byId: new Map(), filtered: [], visible: PAGE_SIZE, filter: 'all', scene: 'all', subscene: 'all', arm: 'all', query: '', sourceURL: '' };
const grid = document.querySelector('#market-grid');
const resultCount = document.querySelector('#result-count');
const loadMore = document.querySelector('#load-more');
const searchInput = document.querySelector('#search-input');
const sceneFilter = document.querySelector('#scene-filter');
const subsceneFilter = document.querySelector('#subscene-filter');
const armFilter = document.querySelector('#arm-filter');
const dialog = document.querySelector('#task-dialog');
const detail = document.querySelector('#task-detail');

const escapeHTML = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[char]));
const sourceVideoURL = (value) => {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'www.maniformer.net' ? url.href : '';
  } catch { return ''; }
};

function cardTemplate(item) {
  const type = item.data_type || '数据';
  const tags = [item.primary_scene, item.secondary_scene, item.arm_type, item.tactile_info].filter(Boolean);
  return `<article class="data-card"><div class="data-card-top"><span class="data-id">来源 MF / ${escapeHTML(String(item.id).padStart(3, '0'))}</span><span class="data-type ${type === '仿真' ? 'sim' : ''}">${escapeHTML(type)}</span></div><h3>${escapeHTML(item.task_name)}</h3><p>${escapeHTML(item.task_description)}</p><div class="data-tags">${tags.map((tag) => `<span>${escapeHTML(tag)}</span>`).join('')}</div><div class="data-card-bottom"><span>${escapeHTML(item.robot_body_type)} · ${item.action_steps.length} 段动作</span><button type="button" class="task-open" data-task-id="${escapeHTML(item.id)}" aria-label="查看${escapeHTML(item.task_name)}任务详情">查看详情 <span aria-hidden="true">↗</span></button></div></article>`;
}

function render() {
  resultCount.textContent = state.filtered.length;
  const visible = state.filtered.slice(0, state.visible);
  grid.innerHTML = visible.length ? visible.map(cardTemplate).join('') : '<div class="empty-state">没有找到匹配的数据任务，请调整关键词或清空筛选。</div>';
  document.querySelector('#catalog-progress').textContent = `已展示 ${visible.length} / ${state.filtered.length} 条`;
  loadMore.hidden = state.visible >= state.filtered.length;
}

function applyFilters() {
  const query = state.query.trim().toLowerCase();
  state.filtered = state.all.filter((item) => {
    const matchesQuery = !query || item.searchText.includes(query);
    const matchesType = state.filter === 'all' || item.data_type === state.filter || item.tactile_info === state.filter;
    const matchesScene = state.scene === 'all' || item.primary_scene === state.scene;
    const matchesSubscene = state.subscene === 'all' || item.secondary_scene === state.subscene;
    const matchesArm = state.arm === 'all' || item.arm_type === state.arm;
    return matchesQuery && matchesType && matchesScene && matchesSubscene && matchesArm;
  });
  state.visible = PAGE_SIZE;
  render();
}

function fillOptions(select, records, field, label) {
  const counts = new Map();
  records.forEach((item) => { if (item[field]) counts.set(item[field], (counts.get(item[field]) || 0) + 1); });
  select.innerHTML = `<option value="all">${label}</option>` + [...counts].map(([value, count]) => `<option value="${escapeHTML(value)}">${escapeHTML(value)} (${count})</option>`).join('');
}

async function loadCatalog() {
  try {
    const response = await fetch('data/market_catalog.json?v=20261014-catalog1');
    if (!response.ok) throw new Error('目录加载失败');
    const payload = await response.json();
    if (payload.schema_version !== 1 || !Array.isArray(payload.records) || payload.total !== payload.records.length) throw new Error('目录格式不正确');
    state.all = payload.records.map((item) => ({ ...item, searchText: [item.id, item.task_name, item.task_description, item.primary_scene, item.secondary_scene, item.robot_body_type, item.arm_model, item.hand_type, item.collection_method, ...item.action_steps.map((step) => `${step.skill} ${step.action_text}`)].join(' ').toLowerCase() }));
    state.byId = new Map(state.all.map((item) => [String(item.id), item]));
    state.sourceURL = sourceVideoURL(payload.source_url);
    const stats = {
      tasks: state.all.length,
      real: state.all.filter((item) => item.data_type === '真机').length,
      sim: state.all.filter((item) => item.data_type === '仿真').length,
      tactile: state.all.filter((item) => item.tactile_info === '有触觉').length,
      scenes: new Set(state.all.map((item) => item.primary_scene)).size,
      actions: state.all.reduce((count, item) => count + item.action_steps.length, 0),
    };
    document.querySelectorAll('[data-catalog-stat]').forEach((element) => { element.textContent = stats[element.dataset.catalogStat].toLocaleString('zh-CN'); });
    [['all', 'tasks'], ['real', 'real'], ['sim', 'sim'], ['tactile', 'tactile']].forEach(([id, key]) => { document.querySelector(`#count-${id}`).textContent = stats[key]; });
    fillOptions(sceneFilter, state.all, 'primary_scene', '全部场景');
    fillOptions(subsceneFilter, state.all, 'secondary_scene', '全部细分场景');
    fillOptions(armFilter, state.all, 'arm_type', '全部臂型');
    sceneFilter.value = state.scene; subsceneFilter.value = state.subscene; armFilter.value = state.arm;
    applyFilters();
  } catch {
    grid.innerHTML = '<div class="empty-state" role="alert">任务目录暂时无法加载。<button class="catalog-retry" type="button" id="retry-catalog">重新加载</button></div>';
    resultCount.textContent = '—';
    document.querySelector('#catalog-progress').textContent = '';
    loadMore.hidden = true;
  }
}

function openTask(id) {
  const item = state.byId.get(String(id));
  if (!item) return;
  const videoURL = sourceVideoURL(item.video_url);
  const fields = [
    ['一级场景', item.primary_scene], ['细分场景', item.secondary_scene],
    ['机器人本体', item.robot_body_type], ['机械臂型号', item.arm_model],
    ['手型', item.hand_type], ['臂型', item.arm_type],
    ['采集方式', item.collection_method], ['触觉信息', item.tactile_info],
    ['采集环境', item.environment], ['学习主题', item.theme], ['Episode ID', item.episode_uuid],
  ];
  detail.innerHTML = `<header class="task-detail-heading"><div class="detail-kicker"><span>MANIFORMER / ${escapeHTML(String(item.id).padStart(3, '0'))}</span><span class="data-type ${item.data_type === '仿真' ? 'sim' : ''}">${escapeHTML(item.data_type)}</span></div><h2 id="task-title">${escapeHTML(item.task_name)}</h2><p>${escapeHTML(item.task_description)}</p></header><div class="detail-layout"><section class="detail-video-section" aria-label="样例视频"><div class="detail-video-frame"><div class="video-placeholder" id="video-placeholder"><span class="video-reference">SOURCE VIDEO / 参考样例</span><button id="start-video" class="video-play" type="button" ${videoURL ? '' : 'disabled'}><span aria-hidden="true">▶</span>播放任务样例</button><p>点击后加载 Maniformer 来源视频</p></div><video id="task-video" controls playsinline preload="none" aria-label="${escapeHTML(item.task_name)}样例视频" hidden></video></div><div class="video-caption"><span id="video-status" aria-live="polite">样例视频 · ${escapeHTML(item.collection_method)}</span>${videoURL ? `<a href="${escapeHTML(videoURL)}" target="_blank" rel="noopener noreferrer">打开来源视频 ↗</a>` : ''}</div></section><section class="detail-specs" aria-labelledby="specs-title"><h3 id="specs-title">采集配置 <span>SPECIFICATION</span></h3><dl>${fields.map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHTML(value || '未提供')}</dd></div>`).join('')}</dl></section></div><section class="detail-actions" aria-labelledby="actions-title"><div class="detail-actions-heading"><h3 id="actions-title">动作序列 <span>${item.action_steps.length} STEPS</span></h3><p>按来源起止帧展示</p></div><ol>${item.action_steps.map((step, index) => `<li><span class="action-number">${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHTML(step.skill || '动作')}</strong><p>${escapeHTML(step.action_text || '未提供动作描述')}</p></div><span class="action-frames">帧 ${escapeHTML(step.start_frame)} → ${escapeHTML(step.end_frame)}</span></li>`).join('')}</ol></section><footer class="detail-footer"><p>来源：Maniformer 公开任务目录${state.sourceURL ? ` · <a href="${escapeHTML(state.sourceURL)}" target="_blank" rel="noopener noreferrer">查看来源 ↗</a>` : ''}</p><a class="button button-dark" id="task-inquiry" href="#contact">咨询同类任务 <span>↗</span></a></footer>`;
  const video = detail.querySelector('#task-video');
  const videoStatus = detail.querySelector('#video-status');
  detail.querySelector('#start-video').addEventListener('click', () => {
    detail.querySelector('#video-placeholder').hidden = true;
    video.hidden = false;
    video.src = videoURL;
    videoStatus.textContent = '正在加载来源视频…';
    video.play().catch(() => { if (video.isConnected && dialog.open && !video.error) videoStatus.textContent = '请使用播放器开始播放。'; });
  });
  video.addEventListener('loadeddata', () => { videoStatus.textContent = '样例视频 · Maniformer'; });
  video.addEventListener('error', () => { videoStatus.textContent = '视频暂时无法播放，可通过右侧链接打开来源视频。'; });
  detail.querySelector('#task-inquiry').addEventListener('click', () => dialog.close());
  dialog.showModal();
  document.body.classList.add('modal-open');
  dialog.scrollTop = 0;
}

grid.addEventListener('click', (event) => {
  const trigger = event.target.closest('[data-task-id]');
  if (trigger) openTask(trigger.dataset.taskId);
  if (event.target.closest('#retry-catalog')) loadCatalog();
});
document.querySelector('#close-task').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
dialog.addEventListener('close', () => {
  document.body.classList.remove('modal-open');
  const video = detail.querySelector('video');
  if (video) { video.pause(); video.removeAttribute('src'); video.load(); }
  detail.innerHTML = '';
});

document.querySelectorAll('.filter-button').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.filter-button').forEach((item) => { item.classList.remove('is-active'); item.setAttribute('aria-pressed', 'false'); });
  button.classList.add('is-active');
  button.setAttribute('aria-pressed', 'true');
  state.filter = button.dataset.filter;
  applyFilters();
}));
searchInput.addEventListener('input', (event) => { state.query = event.target.value; applyFilters(); });
sceneFilter.addEventListener('change', () => {
  state.scene = sceneFilter.value;
  state.subscene = 'all';
  fillOptions(subsceneFilter, state.all.filter((item) => state.scene === 'all' || item.primary_scene === state.scene), 'secondary_scene', '全部细分场景');
  applyFilters();
});
subsceneFilter.addEventListener('change', () => { state.subscene = subsceneFilter.value; applyFilters(); });
armFilter.addEventListener('change', () => { state.arm = armFilter.value; applyFilters(); });
document.querySelector('#reset-filters').addEventListener('click', () => {
  state.query = ''; state.filter = 'all'; state.scene = 'all'; state.subscene = 'all'; state.arm = 'all';
  searchInput.value = ''; sceneFilter.value = 'all'; armFilter.value = 'all';
  fillOptions(subsceneFilter, state.all, 'secondary_scene', '全部细分场景');
  document.querySelectorAll('.filter-button').forEach((item) => {
    const active = item.dataset.filter === 'all';
    item.classList.toggle('is-active', active); item.setAttribute('aria-pressed', String(active));
  });
  applyFilters();
});
loadMore.addEventListener('click', () => { state.visible += PAGE_SIZE; render(); });
loadCatalog();

const menuButton = document.querySelector('.menu-toggle');
const mobileMenu = document.querySelector('.mobile-menu');
function setMenu(open) {
  mobileMenu.classList.toggle('is-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单');
  mobileMenu.setAttribute('aria-hidden', String(!open));
  mobileMenu.inert = !open;
}
setMenu(false);
menuButton.addEventListener('click', () => setMenu(!mobileMenu.classList.contains('is-open')));
mobileMenu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && mobileMenu.classList.contains('is-open')) { setMenu(false); menuButton.focus(); }
});
