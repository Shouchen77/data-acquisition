const PAGE_SIZE = 12;
const KINDS = { all: '全部类型', human_stereo: '真人双目', robot_real: '机器人实采', robot_sim: '机器人仿真' };
const SOURCES = { all: '全部来源', eyecatcher: '视焦自采', maniformer: 'Maniformer 公开参考' };
const defaults = { kind: 'all', scene: 'all', subscene: 'all', source: 'all', arm: 'all', tactile: 'all', query: '' };
const state = { ...defaults, all: [], byId: new Map(), scenes: [], filtered: [], visible: PAGE_SIZE, sourceURL: '', ready: false };
const $ = (selector) => document.querySelector(selector);
const grid = $('#market-grid');
const loadMore = $('#load-more');
const dialog = $('#task-dialog');
const detail = $('#task-detail');
const controls = { scene: $('#scene-filter'), subscene: $('#subscene-filter'), source: $('#source-filter'), arm: $('#arm-filter'), tactile: $('#tactile-filter') };
const escapeHTML = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[char]));
function publicURL(value, sourceOnly = false) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password && (!sourceOnly || url.hostname === 'www.maniformer.net') ? url.href : '';
  } catch { return ''; }
}
const sceneLabel = (id) => state.scenes.find((scene) => scene.id === id)?.label || '全部场景';
const isHuman = (item) => item.dataset_kind === 'human_stereo';
const number = (value) => Number(value).toLocaleString('zh-CN');
const duration = (seconds) => seconds == null ? '待披露' : seconds >= 3600 ? `${(seconds / 3600).toFixed(1)} 小时` : `${(seconds / 60).toFixed(1)} 分钟`;
const resolution = (capture = {}) => capture.width && capture.height ? `${capture.width} × ${capture.height}` : '待披露';

function cardTemplate(item) {
  const human = isHuman(item);
  const tags = human ? [sceneLabel(item.scene_id), item.secondary_scene, '真人第一视角', '左右双目'] : [sceneLabel(item.scene_id), item.secondary_scene, item.arm_type, item.tactile_info];
  const status = human ? (item.availability === 'available' ? '可咨询交付' : '样例采集中') : KINDS[item.dataset_kind];
  const source = human ? '视焦自采 / EGO' : `MF 公开参考 / ${String(item.id).padStart(3, '0')}`;
  const foot = human ? `${item.episode_count == null ? '任务段数量待披露' : number(item.episode_count) + ' 个任务段'} · V3 采集基准` : `${item.robot_body_type || '机器人'} · ${item.action_steps.length} 段动作`;
  return `<article class="data-card ${human ? 'human-card' : ''}"><div class="data-card-top"><span class="data-id">${escapeHTML(source)}</span><span class="data-type ${item.dataset_kind === 'robot_sim' ? 'sim' : ''}">${escapeHTML(status)}</span></div><h3>${escapeHTML(item.task_name)}</h3><p>${escapeHTML(item.task_description)}</p><div class="data-tags">${tags.filter(Boolean).map((tag) => `<span>${escapeHTML(tag)}</span>`).join('')}</div>${human ? `<div class="card-capture"><span>${escapeHTML(resolution(item.capture))}</span><span>${item.capture.fps ? escapeHTML(item.capture.fps) + ' FPS' : '帧率待披露'}</span><span>${item.qa_report_url ? '质检报告可查看' : '质检信息待披露'}</span></div>` : ''}<div class="data-card-bottom"><span>${escapeHTML(foot)}</span><button type="button" class="task-open" data-task-id="${escapeHTML(item.catalog_id)}" aria-label="查看${escapeHTML(item.task_name)}详情">查看详情 <span aria-hidden="true">↗</span></button></div></article>`;
}

function emptyTemplate() {
  const humanScope = state.kind === 'human_stereo' || state.source === 'eyecatcher';
  if (humanScope && !state.query && state.subscene === 'all') {
    const scenes = state.scene === 'all' ? state.scenes.filter((scene) => ['factory', 'medical', 'home'].includes(scene.id)) : state.scenes.filter((scene) => scene.id === state.scene);
    return `<div class="stereo-empty"><span class="empty-kicker">HUMAN EXPERIENCE / STEREO DATA</span><h3>${state.scene === 'all' ? '从真实操作，开始采集。' : escapeHTML(sceneLabel(state.scene)) + '场景，开放定制采集。'}</h3><p>真人双目数据集正在筹备，审核后的样例将在这里上架。可先沟通任务、设备规格与交付要求。</p><div class="planned-scenes">${scenes.map((scene, index) => `<article><span>0${index + 1} / ${escapeHTML(scene.label)}</span><h4>${escapeHTML(scene.description)}</h4><p>可沟通的采集方向 · 非已上架数据</p><a href="#contact" data-inquiry="真人双目 · ${escapeHTML(scene.label)}场景定制采集">讨论${escapeHTML(scene.label)}任务 <span>↗</span></a></article>`).join('')}</div><div class="empty-delivery"><strong>计划交付内容</strong><span>左右目视频</span><span>逐帧时间戳</span><span>IMU</span><span>标定</span><span>VIO 轨迹</span><span>QA 报告</span></div><p class="empty-footnote">以 V3 为采集基准，具体交付范围由项目约定。</p></div>`;
  }
  return `<div class="empty-state"><span class="empty-kicker">NO MATCHING RECORDS</span><h3>暂未找到匹配的数据</h3><p>可以清除筛选条件，或告诉我们你希望采集的任务。</p><div><button class="button button-outline" type="button" data-reset>清除全部筛选</button><a class="button button-dark" href="#contact" data-inquiry="${escapeHTML(KINDS[state.kind])} · ${escapeHTML(sceneLabel(state.scene))}数据需求">咨询定制采集 ↗</a></div></div>`;
}

function matches(item, excluded = []) {
  const skip = new Set(excluded);
  return (skip.has('kind') || state.kind === 'all' || item.dataset_kind === state.kind)
    && (skip.has('source') || state.source === 'all' || item.source_id === state.source)
    && (skip.has('scene') || state.scene === 'all' || item.scene_id === state.scene)
    && (skip.has('subscene') || state.subscene === 'all' || item.secondary_scene === state.subscene)
    && (skip.has('arm') || state.arm === 'all' || item.arm_type === state.arm)
    && (skip.has('tactile') || state.tactile === 'all' || item.tactile_info === state.tactile)
    && (skip.has('query') || !state.query.trim() || item.searchText.includes(state.query.trim().toLowerCase()));
}

function fillOptions(select, values, allLabel, key) {
  const counts = new Map();
  values.filter(Boolean).forEach((value) => counts.set(value, (counts.get(value) || 0) + 1));
  if (state[key] !== 'all' && !counts.has(state[key])) state[key] = 'all';
  select.innerHTML = `<option value="all">${allLabel}</option>` + [...counts].map(([value, count]) => `<option value="${escapeHTML(value)}">${escapeHTML(value)} (${count})</option>`).join('');
  select.value = state[key];
  select.disabled = !counts.size;
}

function syncControls() {
  const humanScope = state.kind === 'human_stereo' || state.source === 'eyecatcher';
  if (humanScope) { state.arm = 'all'; state.tactile = 'all'; }
  $('#robot-filters').hidden = humanScope;
  $('#stereo-filter-note').hidden = !humanScope;
  const scopeRecords = state.all.filter((item) => matches(item, ['scene', 'subscene', 'arm', 'tactile', 'query']));
  controls.scene.innerHTML = '<option value="all">全部场景</option>' + state.scenes.map((scene) => {
    const count = scopeRecords.filter((item) => item.scene_id === scene.id).length;
    return `<option value="${escapeHTML(scene.id)}">${escapeHTML(scene.label)} (${count})</option>`;
  }).join('');
  controls.scene.value = state.scene;
  const context = scopeRecords.filter((item) => state.scene === 'all' || item.scene_id === state.scene);
  fillOptions(controls.subscene, context.map((item) => item.secondary_scene), '全部细分场景', 'subscene');
  fillOptions(controls.arm, context.filter((item) => !isHuman(item)).map((item) => item.arm_type), '全部臂型', 'arm');
  controls.source.value = state.source;
  for (const option of controls.source.options) option.disabled = (state.kind === 'human_stereo' && option.value === 'maniformer') || (state.kind.startsWith('robot_') && option.value === 'eyecatcher');
  controls.tactile.value = state.tactile;
  $('#search-input').value = state.query;
  document.querySelectorAll('[data-kind]').forEach((button) => {
    const active = button.dataset.kind === state.kind;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

function updateURL() {
  const url = new URL(location.href);
  for (const key of Object.keys(defaults)) {
    if (state[key] !== defaults[key]) url.searchParams.set(key, state[key]);
    else url.searchParams.delete(key);
  }
  history.replaceState(null, '', url);
}

function render() {
  $('#result-count').textContent = number(state.filtered.length);
  $('#result-scope').textContent = `${KINDS[state.kind]} / ${sceneLabel(state.scene)}`;
  const visible = state.filtered.slice(0, state.visible);
  grid.innerHTML = visible.length ? visible.map(cardTemplate).join('') : emptyTemplate();
  $('#catalog-progress').textContent = state.filtered.length ? `已展示 ${visible.length} / ${state.filtered.length} 条目录` : '';
  loadMore.hidden = state.visible >= state.filtered.length;
  const humanCount = state.filtered.filter(isHuman).length;
  const references = state.filtered.length - humanCount;
  $('#catalog-context').textContent = state.kind === 'human_stereo' || state.source === 'eyecatcher'
    ? `真人双目 · ${humanCount} 个数据集。实测规格、任务段数量与质检信息在数据集详情中披露。`
    : `${humanCount} 个真人双目数据集 · ${references} 条机器人参考任务。参考任务按来源展示，可用于了解任务与动作结构。`;
  const labels = { kind: KINDS[state.kind], scene: sceneLabel(state.scene), subscene: state.subscene, source: SOURCES[state.source], arm: state.arm, tactile: state.tactile, query: `搜索：${state.query}` };
  const active = Object.keys(defaults).filter((key) => state[key] !== defaults[key]);
  $('#active-filters').hidden = !active.length;
  $('#active-filters').innerHTML = active.map((key) => `<button type="button" data-remove-filter="${key}" aria-label="移除筛选：${escapeHTML(labels[key])}">${escapeHTML(labels[key])}<span aria-hidden="true">×</span></button>`).join('');
}

function applyFilters() {
  if (!state.ready) return;
  syncControls();
  state.filtered = state.all.filter((item) => matches(item));
  state.visible = PAGE_SIZE;
  updateURL();
  render();
}
function resetFilters() { Object.assign(state, defaults); applyFilters(); }
function selectKind(kind) {
  state.kind = Object.hasOwn(KINDS, kind) ? kind : 'all';
  state.arm = 'all'; state.tactile = 'all'; state.subscene = 'all';
  if ((kind === 'human_stereo' && state.source === 'maniformer') || (kind.startsWith('robot_') && state.source === 'eyecatcher')) state.source = 'all';
  applyFilters();
}
function readURL() {
  const params = new URLSearchParams(location.search);
  for (const key of Object.keys(defaults)) state[key] = params.get(key) || defaults[key];
  if (!Object.hasOwn(KINDS, state.kind)) state.kind = 'all';
  if (!Object.hasOwn(SOURCES, state.source)) state.source = 'all';
  if (!state.scenes.some((scene) => scene.id === state.scene)) state.scene = 'all';
  if (!['all', '有触觉', '无触觉'].includes(state.tactile)) state.tactile = 'all';
  if ((state.kind === 'human_stereo' && state.source === 'maniformer') || (state.kind.startsWith('robot_') && state.source === 'eyecatcher')) state.source = 'all';
}

async function loadCatalog() {
  try {
    const response = await fetch('data/market_catalog.json?v=20261016-v3-market2');
    if (!response.ok) throw new Error('目录加载失败');
    const payload = await response.json();
    if (payload.schema_version !== 2 || !Array.isArray(payload.records) || payload.total !== payload.records.length || !Array.isArray(payload.scene_taxonomy)) throw new Error('目录格式不正确');
    state.scenes = payload.scene_taxonomy;
    state.all = payload.records.map((item) => ({ ...item, searchText: [item.catalog_id, item.task_name, item.task_description, item.primary_scene, sceneLabel(item.scene_id), item.secondary_scene, KINDS[item.dataset_kind], item.source_name, item.robot_body_type, item.arm_model, item.hand_type, item.collection_method, ...(item.task_tags || []), ...(isHuman(item) ? ['真人 人类 第一视角 双目 双摄像头 EGO stereo IMU V3'] : []), ...(item.action_steps || []).map((step) => `${step.skill} ${step.action_text}`)].join(' ').toLowerCase() }));
    state.byId = new Map(state.all.map((item) => [item.catalog_id, item]));
    if (state.byId.size !== state.all.length) throw new Error('目录标识重复');
    state.sourceURL = publicURL(payload.source_url, true);
    [['all', 'all'], ['human', 'human_stereo'], ['real', 'robot_real'], ['sim', 'robot_sim']].forEach(([id, kind]) => {
      const count = kind === 'all' ? state.all.length : state.all.filter((item) => item.dataset_kind === kind).length;
      $(`#count-${id}`).textContent = kind === 'human_stereo' && !count ? '待上架' : number(count);
    });
    state.ready = true;
    readURL();
    applyFilters();
  } catch {
    state.ready = false;
    grid.innerHTML = '<div class="empty-state" role="alert"><h3>数据目录暂时无法加载</h3><button class="catalog-retry" type="button" id="retry-catalog">重新加载</button></div>';
    $('#result-count').textContent = '—';
    $('#catalog-context').textContent = '请稍后重试，或直接联系我们讨论数据需求。';
    $('#catalog-progress').textContent = '';
    loadMore.hidden = true;
  }
}

function specsTemplate(fields, title = '采集配置') {
  return `<section class="detail-specs" aria-labelledby="specs-title"><h3 id="specs-title">${title} <span>SPECIFICATION</span></h3><dl>${fields.map(([label, value]) => `<div><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value == null || value === '' ? '待披露' : value)}</dd></div>`).join('')}</dl></section>`;
}
function openTask(id) {
  const item = state.byId.get(id);
  if (!item) return;
  const human = isHuman(item);
  const title = `<header class="task-detail-heading"><div class="detail-kicker"><span>${human ? 'EYECATCHER / 真人双目' : 'MANIFORMER / 公开参考 ' + escapeHTML(item.id)}</span><span class="data-type">${escapeHTML(KINDS[item.dataset_kind])}</span></div><h2 id="task-title">${escapeHTML(item.task_name)}</h2><p>${escapeHTML(item.task_description)}</p></header>`;
  if (human) {
    const c = item.capture || {};
    const previews = ['left', 'right'].map((eye) => publicURL(item.previews?.[eye]));
    const qa = publicURL(item.qa_report_url);
    const fields = [['应用场景', sceneLabel(item.scene_id)], ['细分场景', item.secondary_scene], ['每目实测分辨率', resolution(c)], ['实测视频帧率', c.fps ? c.fps + ' FPS' : null], ['实测 IMU 采样率', c.imu_hz ? c.imu_hz + ' Hz' : null], ['实测视场角', c.fov_h && c.fov_v ? `${c.fov_h}° H / ${c.fov_v}° V` : null], ['任务段数量', item.episode_count == null ? null : number(item.episode_count)], ['总时长', duration(item.duration_seconds)], ['采集基准', 'V3'], ['上架状态', item.availability === 'available' ? '可咨询交付' : '样例采集中']];
    detail.innerHTML = title + `<p class="detail-notice">以 V3 为采集基准。以下为已披露的实测参数，完整验收结论以项目质检报告为准。</p><div class="stereo-detail-previews"><div class="stereo-preview-toolbar"><h3>左右目样例</h3>${previews.every(Boolean) ? '<button type="button" class="button button-outline" id="start-stereo">加载双目样例 ↗</button>' : '<span>预览待发布</span>'}</div>${['左目 / LEFT', '右目 / RIGHT'].map((label, i) => `<section><h4>${label}</h4><div class="detail-video-frame"><div class="video-placeholder"><span class="video-reference">${previews[i] ? '点击加载后，可分别播放两路视频' : '样例审核后发布'}</span></div><video controls playsinline preload="none" hidden aria-label="${label}样例视频"></video></div>${previews[i] ? `<a class="preview-source" href="${escapeHTML(previews[i])}" target="_blank" rel="noopener noreferrer">打开${i ? '右' : '左'}目视频 ↗</a>` : ''}</section>`).join('')}<p id="stereo-video-status" role="status"></p></div>${specsTemplate(fields, '数据集实测规格')}<section class="delivery-detail"><h3>交付内容与质检</h3><ul>${item.delivery_contents.length ? item.delivery_contents.map((entry) => `<li>${escapeHTML(entry)}</li>`).join('') : '<li>具体交付范围待确认</li>'}</ul>${qa ? `<a href="${escapeHTML(qa)}" target="_blank" rel="noopener noreferrer">查看已发布质检报告 ↗</a>` : '<p>质检报告尚未公开，可联系确认样例与验收范围。</p>'}</section>`;
    detail.querySelector('#start-stereo')?.addEventListener('click', (event) => {
      const status = detail.querySelector('#stereo-video-status');
      detail.querySelectorAll('.stereo-detail-previews video').forEach((video, i) => {
        video.previousElementSibling.hidden = true; video.hidden = false; video.src = previews[i]; video.load();
        video.addEventListener('error', () => { if (status.isConnected && dialog.open) status.textContent = '样例暂时无法播放，可使用各视频下方的来源链接。'; });
      });
      event.currentTarget.hidden = true;
      status.textContent = '已加载两路样例，可分别播放。网页预览不作为传感器同步验收依据。';
    });
  } else {
    const videoURL = publicURL(item.video_url, true);
    const fields = [['应用场景', sceneLabel(item.scene_id)], ['来源场景名称', item.primary_scene], ['细分场景', item.secondary_scene], ['机器人本体', item.robot_body_type], ['机械臂型号', item.arm_model], ['手型', item.hand_type], ['臂型', item.arm_type], ['采集方式', item.collection_method], ['触觉信息', item.tactile_info], ['采集环境', item.environment], ['学习主题', item.theme], ['Episode ID', item.episode_uuid]];
    detail.innerHTML = title + `<p class="detail-notice">Maniformer 公开参考任务 · 按来源展示。该记录不代表视焦自有数据或 V3 验收结果。</p><div class="detail-layout"><section aria-label="来源样例视频"><div class="detail-video-frame"><div class="video-placeholder" id="video-placeholder"><span class="video-reference">SOURCE VIDEO / 参考样例</span><button id="start-video" class="video-play" type="button" ${videoURL ? '' : 'disabled'}><span aria-hidden="true">▶</span>播放任务样例</button><p>点击后加载 Maniformer 来源视频</p></div><video id="task-video" controls playsinline preload="none" aria-label="${escapeHTML(item.task_name)}样例视频" hidden></video></div><div class="video-caption"><span id="video-status" aria-live="polite">来源样例 · ${escapeHTML(item.collection_method)}</span>${videoURL ? `<a href="${escapeHTML(videoURL)}" target="_blank" rel="noopener noreferrer">打开来源视频 ↗</a>` : ''}</div></section>${specsTemplate(fields)}</div><section class="detail-actions" aria-labelledby="actions-title"><div class="detail-actions-heading"><h3 id="actions-title">动作序列 <span>${item.action_steps.length} STEPS</span></h3><p>按来源起止帧展示</p></div><ol>${item.action_steps.map((step, index) => `<li><span class="action-number">${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHTML(step.skill || '动作')}</strong><p>${escapeHTML(step.action_text || '未提供动作描述')}</p></div><span class="action-frames">帧 ${escapeHTML(step.start_frame)} → ${escapeHTML(step.end_frame)}</span></li>`).join('')}</ol></section>`;
    const video = detail.querySelector('#task-video');
    const status = detail.querySelector('#video-status');
    detail.querySelector('#start-video').addEventListener('click', () => {
      $('#video-placeholder').hidden = true; video.hidden = false; video.src = videoURL;
      status.textContent = '正在加载来源视频…';
      video.play().catch(() => { if (video.isConnected && dialog.open && !video.error) status.textContent = '请使用播放器开始播放。'; });
    });
    video.addEventListener('loadeddata', () => { status.textContent = '样例视频 · Maniformer'; });
    video.addEventListener('error', () => { status.textContent = '视频暂时无法播放，可通过右侧链接打开来源视频。'; });
  }
  detail.insertAdjacentHTML('beforeend', `<footer class="detail-footer"><p>${human ? '数据来源：视焦科技 · 真人第一视角双目采集' : `来源：Maniformer 公开任务目录${state.sourceURL ? ` · <a href="${escapeHTML(state.sourceURL)}" target="_blank" rel="noopener noreferrer">查看来源 ↗</a>` : ''}`}</p><a class="button button-dark" href="#contact" data-inquiry="${escapeHTML(KINDS[item.dataset_kind])} · ${escapeHTML(item.task_name)}">咨询${human ? '此数据集' : '同类任务'} <span>↗</span></a></footer>`);
  dialog.showModal(); document.body.classList.add('modal-open'); dialog.scrollTop = 0;
}

document.addEventListener('click', (event) => {
  const task = event.target.closest('[data-task-id]');
  if (task) openTask(task.dataset.taskId);
  const kind = event.target.closest('[data-kind], [data-select-kind]');
  if (kind) {
    if (kind.dataset.selectKind) Object.assign(state, defaults);
    selectKind(kind.dataset.kind || kind.dataset.selectKind);
  }
  const inquiry = event.target.closest('[data-inquiry]');
  if (inquiry) {
    if (dialog.open) dialog.close();
    $('#inquiry-context').hidden = false;
    $('#inquiry-context').textContent = `咨询方向：${inquiry.dataset.inquiry}。欢迎通过下方电话或微信沟通。`;
  }
  if (event.target.closest('[data-reset], #reset-filters')) resetFilters();
  const remove = event.target.closest('[data-remove-filter]');
  if (remove) { const key = remove.dataset.removeFilter; state[key] = defaults[key]; if (key === 'scene') state.subscene = 'all'; applyFilters(); }
  if (event.target.closest('#retry-catalog')) loadCatalog();
});
Object.entries(controls).forEach(([key, select]) => select.addEventListener('change', () => {
  state[key] = select.value;
  if (['scene', 'source'].includes(key)) { state.subscene = 'all'; state.arm = 'all'; }
  applyFilters();
}));
$('#search-input').addEventListener('input', (event) => { state.query = event.target.value; applyFilters(); });
$('#close-task').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
dialog.addEventListener('close', () => {
  document.body.classList.remove('modal-open');
  detail.querySelectorAll('video').forEach((video) => { video.pause(); video.removeAttribute('src'); video.load(); });
  detail.innerHTML = '';
});
loadMore.addEventListener('click', () => { state.visible += PAGE_SIZE; render(); });
window.addEventListener('popstate', () => { if (state.ready) { readURL(); applyFilters(); } });
loadCatalog();

const menuButton = $('.menu-toggle');
const mobileMenu = $('.mobile-menu');
function setMenu(open) {
  mobileMenu.classList.toggle('is-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? '关闭菜单' : '打开菜单');
  mobileMenu.setAttribute('aria-hidden', String(!open)); mobileMenu.inert = !open;
}
setMenu(false);
menuButton.addEventListener('click', () => setMenu(!mobileMenu.classList.contains('is-open')));
mobileMenu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && mobileMenu.classList.contains('is-open')) { setMenu(false); menuButton.focus(); }
});
