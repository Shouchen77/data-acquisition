const PAGE_SIZE = 12;
const isMarketPage = document.body.dataset.page === 'market';
let activeTaskId = '';
const sampleCache = new Map();
const KINDS = { all: '全部类型', human_stereo: '真人双目', robot_real: '机器人实采', robot_sim: '机器人仿真' };
const defaults = { kind: 'all', scene: 'all', subscene: 'all', arm: 'all', tactile: 'all', query: '' };
const state = { ...defaults, all: [], byId: new Map(), scenes: [], filtered: [], visible: PAGE_SIZE, sourceURL: '', ready: false };
const $ = (selector) => document.querySelector(selector);
const grid = $('#market-grid');
const loadMore = $('#load-more');
const dialog = $('#task-dialog');
const detail = $('#task-detail');
const escapeHTML = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[char]));
// Keep focus on the combobox while its custom list supports mouse, touch and keyboard.
class FilterSelect {
  static opened = null;
  constructor(root, onChange) {
    this.root = root;
    this.onChange = onChange;
    this.options = [];
    this.value = 'all';
    this.active = 0;
    this.typeahead = '';
    root.innerHTML = `<button type="button" class="filter-trigger" role="combobox" aria-haspopup="listbox" aria-expanded="false" aria-controls="${root.id}-list" aria-labelledby="${root.id}-label ${root.id}-value" disabled><span id="${root.id}-value">加载中…</span><svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m4 6 4 4 4-4" /></svg></button><div class="filter-popup" id="${root.id}-list" role="listbox" aria-labelledby="${root.id}-label" hidden></div>`;
    this.button = root.querySelector('button');
    this.caption = root.querySelector('.filter-trigger > span');
    this.list = root.querySelector('.filter-popup');
    this.button.addEventListener('click', () => this.list.hidden ? this.open() : this.close());
    this.button.addEventListener('keydown', event => this.keydown(event));
    this.list.addEventListener('pointerdown', event => event.preventDefault());
    this.list.addEventListener('click', event => {
      const option = event.target.closest('[role="option"]');
      if (option) this.choose(Number(option.dataset.index));
    });
    root.addEventListener('focusout', event => { if (!root.contains(event.relatedTarget)) this.close(); });
  }
  setOptions(options, value, disabled = false) {
    this.close();
    this.options = options;
    this.value = value;
    this.button.disabled = disabled;
    this.caption.textContent = options.find(option => option.value === value)?.label || options[0].label;
    this.list.innerHTML = options.map((option, index) => `<div class="filter-option" id="${this.root.id}-option-${index}" role="option" aria-selected="${option.value === value}" data-index="${index}"><span class="filter-option-check" aria-hidden="true">${option.value === value ? '✓' : ''}</span><span class="filter-option-label">${escapeHTML(option.label)}</span>${option.count == null ? '' : `<span class="filter-option-count">${option.count}</span>`}</div>`).join('');
  }
  open() {
    if (this.button.disabled) return;
    FilterSelect.opened?.close();
    FilterSelect.opened = this;
    this.list.hidden = false;
    this.root.classList.add('is-open');
    this.button.setAttribute('aria-expanded', 'true');
    this.position();
    this.highlight(Math.max(0, this.options.findIndex(option => option.value === this.value)));
  }
  position() {
    const rect = this.button.getBoundingClientRect();
    const below = window.innerHeight - rect.bottom - 16;
    const above = rect.top - 16;
    const upward = below < Math.min(this.list.scrollHeight, 300) && above > below;
    this.root.classList.toggle('opens-up', upward);
    this.list.style.maxHeight = `${Math.max(48, Math.min(300, upward ? above : below))}px`;
  }
  close() {
    this.list.hidden = true;
    this.root.classList.remove('is-open', 'opens-up');
    this.button.setAttribute('aria-expanded', 'false');
    this.button.removeAttribute('aria-activedescendant');
    this.typeahead = '';
    if (FilterSelect.opened === this) FilterSelect.opened = null;
  }
  highlight(index) {
    this.active = index;
    [...this.list.children].forEach((node, i) => node.classList.toggle('is-focused', i === index));
    const node = this.list.children[index];
    this.button.setAttribute('aria-activedescendant', node.id);
    // Scroll the list itself, without moving the page around the filters.
    if (node.offsetTop < this.list.scrollTop) this.list.scrollTop = node.offsetTop;
    else if (node.offsetTop + node.offsetHeight > this.list.scrollTop + this.list.clientHeight) this.list.scrollTop = node.offsetTop + node.offsetHeight - this.list.clientHeight;
  }
  choose(index) {
    const value = this.options[index].value;
    this.close();
    this.button.focus({ preventScroll: true });
    if (value !== this.value) this.onChange(value);
  }
  keydown(event) {
    const key = event.key;
    if (key === 'Tab') { this.close(); return; }
    if (key === 'Escape') { if (!this.list.hidden) event.preventDefault(); this.close(); return; }
    if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', ' '].includes(key)) {
      event.preventDefault();
      if (this.list.hidden) {
        this.open();
        if (key === 'Home') this.highlight(0);
        if (key === 'End') this.highlight(this.options.length - 1);
      } else if (key === 'Enter' || key === ' ') this.choose(this.active);
      else this.highlight(key === 'Home' ? 0 : key === 'End' ? this.options.length - 1 : Math.max(0, Math.min(this.options.length - 1, this.active + (key === 'ArrowDown' ? 1 : -1))));
    } else if (key.length === 1 && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      if (this.list.hidden) this.open();
      clearTimeout(this.typeaheadTimer);
      this.typeahead += key.toLocaleLowerCase();
      const index = this.options.findIndex(option => option.label.toLocaleLowerCase().startsWith(this.typeahead));
      if (index >= 0) this.highlight(index);
      this.typeaheadTimer = setTimeout(() => { this.typeahead = ''; }, 600);
    }
  }
}
const controls = {};
if (isMarketPage) {
  for (const key of ['scene', 'subscene', 'arm', 'tactile']) {
    controls[key] = new FilterSelect($(`#${key}-filter`), value => {
      state[key] = value;
      if (key === 'scene') { state.subscene = 'all'; state.arm = 'all'; }
      applyFilters();
    });
  }
  document.addEventListener('pointerdown', event => {
    const opened = FilterSelect.opened;
    if (opened && !opened.root.contains(event.target)) opened.close();
  });
  window.addEventListener('resize', () => FilterSelect.opened?.position());
}

function publicURL(value, sourceOnly = false) {
  try {
    if (!value) return '';
    const url = new URL(value, location.href);
    if (!sourceOnly && url.origin === location.origin && url.pathname.includes('/media/stereo/') && !url.username && !url.password) return url.href;
    return url.protocol === 'https:' && !url.username && !url.password && (!sourceOnly || url.hostname === 'www.maniformer.net') ? url.href : '';
  } catch { return ''; }
}
const sceneLabel = (id) => state.scenes.find((scene) => scene.id === id)?.label || '全部场景';
const isHuman = (item) => item.dataset_kind === 'human_stereo';
const number = (value) => Number(value).toLocaleString('zh-CN');
const duration = (seconds) => seconds == null ? '待披露' : seconds < 60 ? `${seconds.toFixed(2)} 秒` : seconds >= 3600 ? `${(seconds / 3600).toFixed(1)} 小时` : `${(seconds / 60).toFixed(1)} 分钟`;
const resolution = (capture = {}) => capture.width && capture.height ? `${capture.width} × ${capture.height}` : '待披露';

function cardTemplate(item) {
  const human = isHuman(item);
  const tags = human ? [sceneLabel(item.scene_id), item.secondary_scene, '真人第一视角', '左右双目'] : [sceneLabel(item.scene_id), item.secondary_scene, item.arm_type, item.tactile_info];
  const status = human ? (item.availability === 'available' ? '工程样例 · 可查看' : '样例采集中') : KINDS[item.dataset_kind];
  const source = human ? '视焦自采 / EGO' : `MF 公开参考 / ${String(item.id).padStart(3, '0')}`;
  const foot = human ? `${item.episode_count == null ? '任务段数量待披露' : number(item.episode_count) + ' 个任务段'} · 视焦数据标准V3规范采集基准` : `${item.robot_body_type || '机器人'} · ${item.action_steps.length} 段动作`;
  return `<article class="data-card ${human ? 'human-card' : ''}">${human && publicURL(item.poster) ? `<a class="sample-cover" href="market.html?dataset=${encodeURIComponent(item.catalog_id)}"><img src="${escapeHTML(publicURL(item.poster))}" loading="lazy" width="960" height="600" alt="${escapeHTML(item.task_name)}第一视角实拍画面" /><span>STEREO SAMPLE <b>↗</b></span></a>` : ''}<div class="data-card-top"><span class="data-id">${escapeHTML(source)}</span><span class="data-type ${item.dataset_kind === 'robot_sim' ? 'sim' : ''}">${escapeHTML(status)}</span></div><h3>${escapeHTML(item.task_name)}</h3><p>${escapeHTML(item.task_description)}</p><div class="data-tags">${tags.filter(Boolean).map((tag) => `<span>${escapeHTML(tag)}</span>`).join('')}</div>${human ? `<div class="card-capture"><span>${escapeHTML(resolution(item.capture))}</span><span>${item.capture.fps ? escapeHTML(item.capture.fps) + ' FPS' : '帧率待披露'}</span><span>${item.sample_data_url ? '传感器数据可查看' : '质检信息待披露'}</span></div>` : ''}<div class="data-card-bottom"><span>${escapeHTML(foot)}</span>${isMarketPage ? `<button type="button" class="task-open" data-task-id="${escapeHTML(item.catalog_id)}" aria-label="查看${escapeHTML(item.task_name)}详情">查看详情 <span aria-hidden="true">↗</span></button>` : `<a class="task-open" href="market.html?dataset=${encodeURIComponent(item.catalog_id)}">查看${human ? '样例' : '详情'} ↗</a>`}</div></article>`;
}

function emptyTemplate() {
  const humanScope = state.kind === 'human_stereo';
  if (humanScope && !state.query && state.subscene === 'all') {
    const scenes = state.scene === 'all' ? state.scenes.filter((scene) => ['factory', 'medical', 'home'].includes(scene.id)) : state.scenes.filter((scene) => scene.id === state.scene);
    return `<div class="stereo-empty"><span class="empty-kicker">HUMAN EXPERIENCE / STEREO DATA</span><h3>${state.scene === 'all' ? '从真实操作，开始采集。' : escapeHTML(sceneLabel(state.scene)) + '场景，开放定制采集。'}</h3><p>真人双目数据集正在筹备，审核后的样例将在这里上架。可先沟通任务、设备规格与交付要求。</p><div class="planned-scenes">${scenes.map((scene, index) => `<article><span>0${index + 1} / ${escapeHTML(scene.label)}</span><h4>${escapeHTML(scene.description)}</h4><p>可沟通的采集方向 · 非已上架数据</p><a href="contact.html" data-inquiry="真人双目 · ${escapeHTML(scene.label)}场景定制采集">讨论${escapeHTML(scene.label)}任务 <span>↗</span></a></article>`).join('')}</div><div class="empty-delivery"><strong>计划交付内容</strong><span>左右目视频</span><span>逐帧时间戳</span><span>IMU</span><span>标定</span><span>VIO 轨迹</span><span>QA 报告</span></div><p class="empty-footnote">以视焦数据标准V3规范为采集基准，具体交付范围由项目约定。</p></div>`;
  }
  return `<div class="empty-state"><span class="empty-kicker">NO MATCHING RECORDS</span><h3>暂未找到匹配的数据</h3><p>可以清除筛选条件，或告诉我们你希望采集的任务。</p><div><button class="button button-outline" type="button" data-reset>清除全部筛选</button><a class="button button-dark" href="contact.html" data-inquiry="${escapeHTML(KINDS[state.kind])} · ${escapeHTML(sceneLabel(state.scene))}数据需求">咨询定制采集 ↗</a></div></div>`;
}

function matches(item, excluded = []) {
  const skip = new Set(excluded);
  return (skip.has('kind') || state.kind === 'all' || item.dataset_kind === state.kind)
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
  select.setOptions([{ value: 'all', label: allLabel }, ...[...counts].map(([value, count]) => ({ value, label: value, count }))], state[key], !counts.size);
}

function syncControls() {
  const humanScope = state.kind === 'human_stereo';
  if (humanScope) { state.arm = 'all'; state.tactile = 'all'; }
  $('#robot-filters').hidden = humanScope;
  $('#stereo-filter-note').hidden = !humanScope;
  const scopeRecords = state.all.filter((item) => matches(item, ['scene', 'subscene', 'arm', 'tactile', 'query']));
  controls.scene.setOptions([{ value: 'all', label: '全部场景', count: scopeRecords.length }, ...state.scenes.map(scene => ({ value: scene.id, label: scene.label, count: scopeRecords.filter(item => item.scene_id === scene.id).length }))], state.scene);
  const context = scopeRecords.filter((item) => state.scene === 'all' || item.scene_id === state.scene);
  fillOptions(controls.subscene, context.map((item) => item.secondary_scene), '全部细分场景', 'subscene');
  fillOptions(controls.arm, context.filter((item) => !isHuman(item)).map((item) => item.arm_type), '全部臂型', 'arm');
  fillOptions(controls.tactile, context.filter(item => !isHuman(item)).map(item => item.tactile_info), '全部触觉配置', 'tactile');
  $('#search-input').value = state.query;
  document.querySelectorAll('[data-kind]').forEach((button) => {
    const active = button.dataset.kind === state.kind;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

function updateURL() {
  const url = new URL(location.href);
  url.searchParams.delete('source');
  for (const key of Object.keys(defaults)) {
    if (state[key] !== defaults[key]) url.searchParams.set(key, state[key]);
    else url.searchParams.delete(key);
  }
  history.replaceState(null, '', url);
}

function render() {
  if (!isMarketPage) {
    const humans = state.all.filter(isHuman).slice(0, 4);
    const robots = state.all.filter(item => item.dataset_kind === 'robot_real').slice(0, 2);
    grid.innerHTML = [...humans, ...robots].map(cardTemplate).join('');
    return;
  }
  $('#result-count').textContent = number(state.filtered.length);
  $('#result-scope').textContent = `${KINDS[state.kind]} / ${sceneLabel(state.scene)}`;
  const visible = state.filtered.slice(0, state.visible);
  grid.innerHTML = visible.length ? visible.map(cardTemplate).join('') : emptyTemplate();
  $('#catalog-progress').textContent = state.filtered.length ? `已展示 ${visible.length} / ${state.filtered.length} 条目录` : '';
  loadMore.hidden = state.visible >= state.filtered.length;
  const humanCount = state.filtered.filter(isHuman).length;
  const references = state.filtered.length - humanCount;
  $('#catalog-context').textContent = state.kind === 'human_stereo'
    ? `真人双目 · ${humanCount} 个数据集。实测规格、任务段数量与质检信息在数据集详情中披露。`
    : `${humanCount} 个真人双目数据集 · ${references} 条机器人参考任务。参考任务按来源展示，可用于了解任务与动作结构。`;
  const labels = { kind: KINDS[state.kind], scene: sceneLabel(state.scene), subscene: state.subscene, arm: state.arm, tactile: state.tactile, query: `搜索：${state.query}` };
  const active = Object.keys(defaults).filter((key) => state[key] !== defaults[key]);
  $('#active-filters').hidden = !active.length;
  $('#active-filters').innerHTML = active.map((key) => `<button type="button" data-remove-filter="${key}" aria-label="移除筛选：${escapeHTML(labels[key])}">${escapeHTML(labels[key])}<span aria-hidden="true">×</span></button>`).join('');
}

function applyFilters() {
  if (!state.ready) return;
  if (!isMarketPage) { render(); return; }
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
  applyFilters();
}
function readURL() {
  const params = new URLSearchParams(location.search);
  for (const key of Object.keys(defaults)) state[key] = params.get(key) || defaults[key];
  if (!Object.hasOwn(KINDS, state.kind)) state.kind = 'all';
  if (!state.scenes.some((scene) => scene.id === state.scene)) state.scene = 'all';
  if (!['all', '有触觉', '无触觉'].includes(state.tactile)) state.tactile = 'all';
}

async function loadCatalog() {
  const initialHash = location.hash;
  const firstLoad = !state.ready;
  try {
    const response = await fetch('data/market_catalog.json?v=20261106-samples1');
    if (!response.ok) throw new Error('目录加载失败');
    const payload = await response.json();
    if (payload.schema_version !== 2 || !Array.isArray(payload.records) || payload.total !== payload.records.length || !Array.isArray(payload.scene_taxonomy)) throw new Error('目录格式不正确');
    state.scenes = payload.scene_taxonomy;
    state.all = payload.records.map((item) => ({ ...item, searchText: [item.catalog_id, item.task_name, item.task_description, item.primary_scene, sceneLabel(item.scene_id), item.secondary_scene, KINDS[item.dataset_kind], item.source_name, item.robot_body_type, item.arm_model, item.hand_type, item.collection_method, ...(item.task_tags || []), ...(isHuman(item) ? ['真人 人类 第一视角 双目 双摄像头 EGO stereo IMU V3 视焦数据标准V3规范'] : []), ...(item.action_steps || []).map((step) => `${step.skill} ${step.action_text}`)].join(' ').toLowerCase() }));
    state.byId = new Map(state.all.map((item) => [item.catalog_id, item]));
    if (state.byId.size !== state.all.length) throw new Error('目录标识重复');
    state.sourceURL = publicURL(payload.source_url, true);
    [['all', 'all'], ['human', 'human_stereo'], ['real', 'robot_real'], ['sim', 'robot_sim']].forEach(([id, kind]) => {
      const count = kind === 'all' ? state.all.length : state.all.filter((item) => item.dataset_kind === kind).length;
      if ($(`#count-${id}`)) $(`#count-${id}`).textContent = kind === 'human_stereo' && !count ? '待上架' : number(count);
    });
    state.ready = true;
    if (isMarketPage) readURL();
    applyFilters();
    if (isMarketPage) { const requested = new URLSearchParams(location.search).get('dataset'); if (requested && state.byId.has(requested)) openTask(requested); }
    if (firstLoad && initialHash && location.hash === initialHash) {
      const anchor = document.getElementById(initialHash.slice(1));
      if (anchor) requestAnimationFrame(() => anchor.scrollIntoView({ behavior: 'instant', block: 'start' }));
    }
  } catch {
    state.ready = false;
    grid.innerHTML = '<div class="empty-state" role="alert"><h3>数据目录暂时无法加载</h3><button class="catalog-retry" type="button" id="retry-catalog">重新加载</button></div>';
    if (!isMarketPage) return;
    $('#result-count').textContent = '—';
    $('#catalog-context').textContent = '请稍后重试，或直接联系我们讨论数据需求。';
    $('#catalog-progress').textContent = '';
    loadMore.hidden = true;
  }
}

function specsTemplate(fields, title = '采集配置') {
  return `<section class="detail-specs" aria-labelledby="specs-title"><h3 id="specs-title">${title} <span>SPECIFICATION</span></h3><dl>${fields.map(([label, value]) => `<div><dt>${escapeHTML(label)}</dt><dd>${escapeHTML(value == null || value === '' ? '待披露' : value)}</dd></div>`).join('')}</dl></section>`;
}
const bytes = value => value >= 1024*1024 ? `${(value/1024/1024).toFixed(1)} MB` : `${(value/1024).toFixed(1)} KB`;
function sampleTable(table, columns) {
  return `<div class="sample-table-scroll" tabindex="0" role="region" aria-label="原始数据前8行，可横向滚动"><table class="sample-table"><thead><tr>${columns.map(([key,label])=>`<th scope="col">${escapeHTML(label)}<small>${key}</small></th>`).join('')}</tr></thead><tbody>${table.rows.map(row=>`<tr>${columns.map(([key])=>`<td>${escapeHTML(row[key] || '—')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function imuChart(points, prefix, title) {
  const keys=['x','y','z'].map(axis=>`${prefix}_${axis}_counts`);
  const all=points.flatMap(p=>keys.map(k=>p[k])); const min=Math.min(...all),max=Math.max(...all); const range=max-min||1;
  const colors=['#b7d431','#5fa5c7','#df8b61'];
  return `<figure class="imu-chart"><figcaption><strong>${title}</strong><span>单位：原始 counts</span></figcaption><svg viewBox="0 0 800 210" role="img" aria-label="${title}原始counts随设备相对时间变化，X、Y、Z三轴"><path d="M44 15V175H780M44 95H780" stroke="currentColor" opacity=".18" fill="none"/>${keys.map((key,i)=>`<polyline points="${points.map((p,j)=>`${(44+j/(points.length-1)*736).toFixed(1)},${(175-(p[key]-min)/range*155).toFixed(1)}`).join(' ')}" fill="none" stroke="${colors[i]}" stroke-width="1.5"/>`).join('')}<text x="4" y="22">${max}</text><text x="4" y="175">${min}</text><text x="44" y="201">0 s</text><text x="740" y="201">${points.at(-1).t.toFixed(1)} s</text></svg><div class="chart-legend">${keys.map((k,i)=>`<span><i style="background:${colors[i]}"></i>${['X','Y','Z'][i]} 轴</span>`).join('')}<span>抽样显示 ${points.length} 个点；完整数据见 CSV</span></div></figure>`;
}
async function loadSample(item) {
  const id=item.catalog_id;
  try {
    if(!sampleCache.has(id)) {
      const response=await fetch(publicURL(item.sample_data_url));
      if(!response.ok) throw new Error('sample');
      const value=await response.json();
      if(value.dataset_id!==item.id || !value.tables || !Array.isArray(value.files)) throw new Error('format');
      sampleCache.set(id,value);
    }
    if(activeTaskId!==id) return;
    const data=sampleCache.get(id);
    const timestampFile=data.files.find(f=>f.path==='timestamps/top_left_camera.csv');
    const imuFile=data.files.find(f=>f.path==='imu/imu.csv');
    const dataContent=detail.querySelector('.sample-data-content');dataContent.removeAttribute('role');
    dataContent.innerHTML=`<div class="sample-stat-grid"><div><span>左 / 右目帧数</span><strong>${number(data.frames.left)} / ${number(data.frames.right)}</strong></div><div><span>IMU 样本数</span><strong>${number(data.imu_samples)}</strong></div><div><span>设备时钟视频帧率</span><strong>${data.fps} <small>FPS</small></strong></div><div><span>设备时钟 IMU 频率</span><strong>${data.imu_hz} <small>Hz</small></strong></div></div><section class="sample-data-section"><div class="sample-section-heading"><div><span class="eyebrow">01 / TIME</span><h3>逐帧时间戳</h3></div><a class="arrow-link" href="${escapeHTML(publicURL(timestampFile.url))}" download>下载左目 CSV ↗</a></div><p>左右目时间戳共 ${number(data.frames.left)} 对；按文件中的设备计数器比较，最大差值 ${data.paired_timestamp_max_delta_us} μs。${escapeHTML(data.timestamp_status)}。</p>${sampleTable(data.tables.timestamps,[['frame_index','帧序号'],['device_timestamp_unwrapped_us','设备时间 / μs'],['timestamp_unix','Unix 时间估计 / s'],['exposure_duration_us','曝光时长 / μs']])}<p class="sample-caption">表格显示左目文件前 8 行，完整左右目文件均可下载。相同设备时间计数不等同于已验证的曝光同步。</p></section><section class="sample-data-section"><div class="sample-section-heading"><div><span class="eyebrow">02 / INERTIAL</span><h3>IMU 原始数据</h3></div><a class="arrow-link" href="${escapeHTML(publicURL(imuFile.url))}" download>下载 IMU CSV ↗</a></div><p>${escapeHTML(data.imu_status)}。以下展示实际原始采样值。</p>${imuChart(data.imu_plot,'gyro','陀螺仪三轴')}${imuChart(data.imu_plot,'accel','加速度计三轴')}${sampleTable(data.tables.imu,[['sample_index','样本序号'],['device_timestamp_unwrapped_us','设备时间 / μs'],['gyro_x_counts','陀螺仪 X'],['gyro_y_counts','陀螺仪 Y'],['gyro_z_counts','陀螺仪 Z'],['accel_x_counts','加速度 X'],['accel_y_counts','加速度 Y'],['accel_z_counts','加速度 Z']])}</section><section class="sample-data-section"><div class="sample-section-heading"><div><span class="eyebrow">03 / CALIBRATION</span><h3>标定与验证状态</h3></div></div><div class="sample-status-list"><div><span>相机内参</span><strong>候选参数 / 尚未验收</strong></div><div><span>双目基线候选值</span><strong>${(data.extrinsics.stereo_baseline_m*1000).toFixed(3)} mm</strong></div><div><span>相机与 IMU 外参</span><strong>历史候选 / 尚未验收</strong></div><div><span>UTC 时间对齐</span><strong>待验证</strong></div><div><span>VIO 轨迹 / 完整 QA 报告</span><strong>本样例包未提供</strong></div></div>${[['相机内参文件',data.intrinsics],['相机外参文件',data.extrinsics],['IMU 配置信息',data.imu_info]].map(([title,value])=>`<details class="sample-code"><summary>${title}<span>展开原始内容 ＋</span></summary><pre>${escapeHTML(JSON.stringify(value,null,2))}</pre></details>`).join('')}</section>`;
    const fileContent=detail.querySelector('.sample-files-content');fileContent.removeAttribute('role');
    fileContent.innerHTML=`<div class="sample-download-heading"><div><span class="eyebrow">ORIGINAL SAMPLE FILES</span><h3>数据文件，直接查看。</h3><p>包含原始视频、网页预览、逐帧时间戳、IMU 与候选标定文件。</p></div><a class="button button-dark" href="${escapeHTML(publicURL(data.data_archive))}" download>下载传感器与标定包 ↓</a></div><div class="sample-file-list">${data.files.map(f=>`<article><div><strong>${escapeHTML(f.path)}</strong><span>${bytes(f.bytes)}${f.path.startsWith('videos/') ? ' · 原始 HEVC' : f.path.startsWith('preview/') ? ' · 网页 H.264 预览' : ''}</span><details><summary>SHA-256 校验值</summary><code>${escapeHTML(f.sha256)}</code></details></div><a class="arrow-link" href="${escapeHTML(publicURL(f.url))}" download>下载 <span>↓</span></a></article>`).join('')}</div>`;
  } catch {
    if(activeTaskId!==id) return;
    detail.querySelectorAll('.sample-data-content,.sample-files-content').forEach(el=>{el.innerHTML='<p>样例数据暂时无法加载。</p><button type="button" class="button button-outline" data-retry-sample>重新加载</button>';});
  }
}
function selectSampleTab(name, focus=false) {
  detail.querySelectorAll('[data-sample-tab]').forEach(button=>{const active=button.dataset.sampleTab===name;button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;if(active&&focus)button.focus();});
  ['video','data','files'].forEach(key=>{detail.querySelector('#sample-'+key).hidden=key!==name;});
  if(name!=='video') detail.querySelectorAll('video').forEach(video=>video.pause());
}
document.addEventListener('click',event=>{
  const tab=event.target.closest('[data-sample-tab]');if(tab)selectSampleTab(tab.dataset.sampleTab);
  if(event.target.closest('[data-retry-sample]'))loadSample(state.byId.get(activeTaskId));
});
document.addEventListener('keydown',event=>{
  const tab=event.target.closest('[data-sample-tab]');if(!tab)return;
  const names=['video','data','files'];let i=names.indexOf(tab.dataset.sampleTab);
  if(event.key==='ArrowRight')i=(i+1)%3;else if(event.key==='ArrowLeft')i=(i+2)%3;else if(event.key==='Home')i=0;else if(event.key==='End')i=2;else return;
  event.preventDefault();selectSampleTab(names[i],true);
});

function openTask(id) {
  const item = state.byId.get(id);
  if (!item) return;
  const human = isHuman(item);
  const title = `<header class="task-detail-heading"><div class="detail-kicker"><span>${human ? 'EYECATCHER / 真人双目' : 'MANIFORMER / 公开参考 ' + escapeHTML(item.id)}</span><span class="data-type">${escapeHTML(KINDS[item.dataset_kind])}</span></div><h2 id="task-title">${escapeHTML(item.task_name)}</h2><p>${escapeHTML(item.task_description)}</p></header>`;
  activeTaskId = id;
  if (human) {
    const c = item.capture || {};
    const fields = [['应用场景', sceneLabel(item.scene_id)], ['细分场景', item.secondary_scene], ['原始视频分辨率 / 每目', resolution(c)], ['视频帧率 / 设备时间测算', c.fps ? c.fps + ' FPS' : null], ['IMU 采样率 / 设备时间测算', c.imu_hz ? c.imu_hz + ' Hz' : null], ['样例时长', duration(item.duration_seconds)]];
    detail.innerHTML = title + `<div class="sample-tabs" role="tablist" aria-label="数据集详情"><button id="sample-tab-video" type="button" role="tab" aria-selected="true" aria-controls="sample-video" data-sample-tab="video">双目视频</button><button id="sample-tab-data" type="button" role="tab" aria-selected="false" aria-controls="sample-data" tabindex="-1" data-sample-tab="data">传感器数据</button><button id="sample-tab-files" type="button" role="tab" aria-selected="false" aria-controls="sample-files" tabindex="-1" data-sample-tab="files">文件下载</button></div><section id="sample-video" role="tabpanel" aria-labelledby="sample-tab-video"><div class="sample-playbar"><span>真人第一视角 / 左右目配对</span><button class="button button-dark" id="play-pair" type="button">播放双目样例 ▶</button></div><div class="sample-video-grid">${['left','right'].map((eye,i)=>`<div><h3>${i ? '右目 / RIGHT' : '左目 / LEFT'}</h3><video controls playsinline preload="none" poster="${escapeHTML(publicURL(item.poster))}" src="${escapeHTML(publicURL(item.previews[eye]))}" aria-label="${escapeHTML(item.task_name)}${i ? '右' : '左'}目视频"></video></div>`).join('')}</div><p id="stereo-video-status" class="sample-caption" role="status">网页预览为 H.264 / 1280 × 800；原始 HEVC / 1920 × 1200 视频可在文件页下载。网页配对播放用于观察，不作为同步验收依据。</p>${specsTemplate(fields,'样例实测规格')}<p class="detail-notice">公开工程样例 · 采集基准为视焦数据标准V3规范。标定与 UTC 对齐状态尚待验证，详情见传感器数据页。</p></section><section id="sample-data" role="tabpanel" aria-labelledby="sample-tab-data" hidden><div class="sample-data-content" role="status">正在读取传感器数据…</div></section><section id="sample-files" role="tabpanel" aria-labelledby="sample-tab-files" hidden><div class="sample-files-content" role="status">正在读取文件清单…</div></section>`;
    const videos = [...detail.querySelectorAll('video')];
    detail.querySelector('#play-pair').addEventListener('click', async event => {
      const button=event.currentTarget; const playing=videos.some(v=>!v.paused);
      if (playing) { videos.forEach(v=>v.pause()); button.textContent='播放双目样例 ▶'; return; }
      videos[1].currentTime=videos[0].currentTime;
      try { await Promise.all(videos.map(v=>v.play())); button.textContent='暂停双目样例 Ⅱ'; }
      catch { $('#stereo-video-status').textContent='可分别使用播放器播放，或在文件下载页打开视频。'; }
    });
    videos.forEach(v=>v.addEventListener('ended',()=>{ if(activeTaskId===id) $('#play-pair').textContent='播放双目样例 ▶'; }));
    videos[0].addEventListener('timeupdate',()=>{if(videos.every(v=>!v.paused)&&Math.abs(videos[0].currentTime-videos[1].currentTime)>.2) videos[1].currentTime=videos[0].currentTime;});
    videos.forEach(v=>v.addEventListener('error',()=>{if(activeTaskId===id) $('#stereo-video-status').textContent='视频暂时无法加载，请尝试文件下载页中的预览链接。';}));
    loadSample(item);
  } else {
    const videoURL = publicURL(item.video_url, true);
    const fields = [['应用场景', sceneLabel(item.scene_id)], ['来源场景名称', item.primary_scene], ['细分场景', item.secondary_scene], ['机器人本体', item.robot_body_type], ['机械臂型号', item.arm_model], ['手型', item.hand_type], ['臂型', item.arm_type], ['采集方式', item.collection_method], ['触觉信息', item.tactile_info], ['采集环境', item.environment], ['学习主题', item.theme], ['Episode ID', item.episode_uuid]];
    detail.innerHTML = title + `<p class="detail-notice">Maniformer 公开参考任务 · 按来源展示。该记录不代表视焦自有数据或视焦数据标准V3规范验收结果。</p><div class="detail-layout"><section aria-label="来源样例视频"><div class="detail-video-frame"><div class="video-placeholder" id="video-placeholder"><span class="video-reference">SOURCE VIDEO / 参考样例</span><button id="start-video" class="video-play" type="button" ${videoURL ? '' : 'disabled'}><span aria-hidden="true">▶</span>播放任务样例</button><p>点击后加载 Maniformer 来源视频</p></div><video id="task-video" controls playsinline preload="none" aria-label="${escapeHTML(item.task_name)}样例视频" hidden></video></div><div class="video-caption"><span id="video-status" aria-live="polite">来源样例 · ${escapeHTML(item.collection_method)}</span>${videoURL ? `<a href="${escapeHTML(videoURL)}" target="_blank" rel="noopener noreferrer">打开来源视频 ↗</a>` : ''}</div></section>${specsTemplate(fields)}</div><section class="detail-actions" aria-labelledby="actions-title"><div class="detail-actions-heading"><h3 id="actions-title">动作序列 <span>${item.action_steps.length} STEPS</span></h3><p>按来源起止帧展示</p></div><ol>${item.action_steps.map((step, index) => `<li><span class="action-number">${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHTML(step.skill || '动作')}</strong><p>${escapeHTML(step.action_text || '未提供动作描述')}</p></div><span class="action-frames">帧 ${escapeHTML(step.start_frame)} → ${escapeHTML(step.end_frame)}</span></li>`).join('')}</ol></section>`;
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
  detail.insertAdjacentHTML('beforeend', `<footer class="detail-footer"><p>${human ? '数据来源：视焦科技 · 真人第一视角双目采集' : `来源：Maniformer 公开任务目录${state.sourceURL ? ` · <a href="${escapeHTML(state.sourceURL)}" target="_blank" rel="noopener noreferrer">查看来源 ↗</a>` : ''}`}</p><a class="button button-dark" href="contact.html" data-inquiry="${escapeHTML(KINDS[item.dataset_kind])} · ${escapeHTML(item.task_name)}">咨询${human ? '此数据集' : '同类任务'} <span>↗</span></a></footer>`);
  const taskURL = new URL(location.href); taskURL.searchParams.set('dataset', id); history.replaceState(null, '', taskURL);
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
  if (event.target.closest('[data-reset], #reset-filters')) resetFilters();
  const remove = event.target.closest('[data-remove-filter]');
  if (remove) { const key = remove.dataset.removeFilter; state[key] = defaults[key]; if (key === 'scene') state.subscene = 'all'; applyFilters(); }
  if (event.target.closest('#retry-catalog')) loadCatalog();
});
$('#search-input')?.addEventListener('input', (event) => { state.query = event.target.value; applyFilters(); });
$('#close-task')?.addEventListener('click', () => dialog.close());
dialog?.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
dialog?.addEventListener('close', () => {
  activeTaskId = '';
  const closedURL = new URL(location.href); closedURL.searchParams.delete('dataset'); history.replaceState(null, '', closedURL);
  document.body.classList.remove('modal-open');
  detail.querySelectorAll('video').forEach((video) => { video.pause(); video.removeAttribute('src'); video.load(); });
  detail.innerHTML = '';
});
loadMore?.addEventListener('click', () => { state.visible += PAGE_SIZE; render(); });
window.addEventListener('popstate', () => { if (state.ready) { readURL(); applyFilters(); } });
loadCatalog();
