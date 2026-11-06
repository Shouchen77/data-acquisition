# 阿里云部署记录

部署日期：2026-10-16。部署成功，两个域名均通过 HTTPS 访问验证。

| 入口 | 内容 |
| --- | --- |
| https://eyecatcher.cn/ | 视焦科技官网 |
| https://eyecatcher.cn/#market | 真人双目 / 机器人实采 / 机器人仿真分类市场 |
| https://3d.eyecatcher.cn/ | 现有印蛙 PrintLink 应用，打开后进入登录页 |
| https://shouchen77.github.io/data-acquisition/ | 官网备用站点 |

## 服务器与域名

- 阿里云轻量应用服务器，杭州，公网 IPv4 `120.26.86.139`。
- `eyecatcher.cn` 的 `@` 和 `3d` 两条 A 记录均指向该 IPv4，默认线路，TTL 600 秒。
- Caddy 为两个新域名提供 HTTPS；官网由 Caddy 直接提供静态文件，印蛙反向代理至原有 `127.0.0.1:8080`。
- 原有 `printlink.tech`、IP 入口及邮件 DNS 记录均保留。

## 文件与数据位置

- 官网当前版本入口：`/srv/eyecatcher/current`，通过软链接指向最新校验通过的 `/srv/eyecatcher/releases/` 版本目录；各次发布记录见下文。
- 网站实际读取的目录数据：`/srv/eyecatcher/current/data/market_catalog.json`，采用 schema 2，现有 466 条机器人参考任务、466 个来源视频链接及 2,963 条动作标注；真人双目 0 个数据集，显示待上架。
- 官网仅部署 `index.html`、`styles.css`、`app.js`、`assets/shijiao-mark.png` 和 `data/market_catalog.json`。
- 原始采集 JSON、CSV、统计和导入报告已在 GitHub 的两个项目仓库中保存；来源视频为外部链接。
- 印蛙代码仍位于 `/opt/printlink`，使用原有运行服务与数据。本次仅新增域名代理配置。

## 验证

- 两个域名 HTTPS 请求成功，证书校验开启，页面标题分别为视焦科技和印蛙 PrintLink。
- 官网五个文件的 SHA-256 与本地发布版本一致。
- 浏览器确认官网显示 466 条任务、411 条真机、55 条仿真和 2,963 条动作标注；触觉筛选返回 8 条，任务详情显示采集配置与动作起止帧。
- 印蛙浏览器打开后正常显示登录页。本次未提交验证码、创建订单或修改应用数据。
- 印蛙登录页当前公开显示演示账号入口；本次未调整其认证策略，正式业务使用前应检查演示账号及验证码配置。

本地机器验证结果见 `output/aliyun-verification.json`，部署回执见 `output/aliyun-deployment-result.json`。

## 配置备份与回退

服务器备份目录：`/var/backups/eyecatcher/20261016T033500Z/`，包含原始 Caddyfile、发布候选配置、验证日志及部署回执。

管理员如需撤回本次域名配置，可在服务器执行：

```sh
sudo cp /var/backups/eyecatcher/20261016T033500Z/Caddyfile.before /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
```

此回退会撤下两个新域名的服务，保留原有印蛙入口和应用数据。DNS 记录需要时可在阿里云 DNS 控制台分别调整。

`deployment/aliyun_deploy.py` 是本次首次部署脚本，含下载哈希校验、配置备份与 reload 失败恢复；检测到已有 `eyecatcher.cn` 配置时会停止。后续更新应创建新版本目录、校验文件，再切换 `current` 链接。


## V3 与真人双目市场更新（2026-10-16）

本次增加 V3 质量标准、真人第一视角双目采集定位、七个场景分类和两种详情结构。现有参考任务 411 条机器人实采、55 条机器人仿真；真人数据集待上架。公开摘要录入说明见 [MARKET_DATA.md](MARKET_DATA.md)。

- 当前发布：`/srv/eyecatcher/releases/20261016T042032Z`。
- 先前发布：`/srv/eyecatcher/releases/20261016T033500Z`，保留可恢复。
- 更新回执：`/var/backups/eyecatcher/20261016T042032Z/deployment.json`。
- 阿里云命令助手执行 ID：`t-hz0706hbjxgv4e8`，退出码 0。
- 五个线上文件与本地构建 SHA-256 一致；HTTPS 证书校验正常。
- Caddy 配置未修改；PrintLink 健康检查通过。
- 代码版本：公开仓库 `65be3a875d76b7de6d3dbd223eaadc54ffd9de1a`，私有仓库 `4d8acb8`。

本地验证记录：`output/aliyun-v3-verification.json`、`output/aliyun-v3-deployment-result.json`；市场截图：`output/preview/v3-market-live.png`。

`deployment/aliyun_update.py` 用于后续静态更新，接收审阅过的下载源、文件 SHA-256、目录总量和类型数量。先校验五个文件与目录格式，再原子切换软链接，并检查线上文件；检查失败自动恢复原链接。完整参数来自 `output/public_build_manifest.json` 与对应 GitHub 提交。

仅恢复前一个官网版本时，可在服务器执行（无需更改印蛙或域名配置）：

```sh
sudo ln -s /srv/eyecatcher/releases/20261016T033500Z /srv/eyecatcher/rollback-v3
sudo mv -Tf /srv/eyecatcher/rollback-v3 /srv/eyecatcher/current
```

## 联系区与邮箱更新（2026-10-16）

联系区采用石墨黑与灰白配色，将合作说明、商务联系方式和公司地址分组。新增联系邮箱 `fzlunar@hotmail.com`，支持点击发起邮件；电话支持点击拨打，微信和地址支持复制。

- 本次发布：`/srv/eyecatcher/releases/20261016T043520Z`。
- 先前发布：`/srv/eyecatcher/releases/20261016T042032Z`，保留可恢复。
- 阿里云命令助手执行 ID：`t-hz0706in2wkk45c`，退出码 0。
- 代码版本：公开仓库 `9c22e036cfdfb23deffcc4b133c0afb781acd216`，私有仓库 `09dd930`。
- 五个线上文件与本地构建 SHA-256 一致；官网及 PrintLink HTTPS 检查通过，Caddy 配置未修改。
- 已检查桌面及 320、390 像素手机布局，复制微信和地址、电话及邮件链接可用，浏览器无错误。

本地回执：`output/aliyun-contact-deployment-result.json`；验证记录：`output/aliyun-contact-verification.json`；线上截图：`output/preview/contact-redesign-live.png`。

仅撤回此次联系区更新时，可在服务器执行：

```sh
sudo ln -s /srv/eyecatcher/releases/20261016T042032Z /srv/eyecatcher/rollback-contact
sudo mv -Tf /srv/eyecatcher/rollback-contact /srv/eyecatcher/current
```

## 关于与采集服务布局更新（2026-10-16）

关于视焦、采集服务统一为与质量标准和数据市场相同的内容宽度，标签移至标题上方，取消侧栏预留空白。关于区重排为完整标题、企业说明和横向采集框架；采集服务使用三列等宽卡片，按钮底部对齐，手机端改为单列。

- 阿里云命令助手执行 ID：`t-hz0706jot0l4m4g`。
- 代码版本：公开仓库 `a2f7fea3d739b3d08a463e5c7888a79c3f1aa393`，私有仓库 `818a6783cfb36d77739fcd8b69cfbdc1adb7aaf4`。
- 五个线上文件与本地构建 SHA-256 一致，官网和 PrintLink HTTPS 请求正常。
- 本地检查 320、390、1440 像素宽度；线上 1280 像素下，两块内容与质量标准、数据市场左右边界一致，无横向溢出。
- 验证记录：`output/aliyun-layout-verification.json`、`output/layout-browser-verification.json`。
- 线上截图：`output/preview/about-capability-live.png`。

## 视焦数据标准V3规范名称更新（2026-11-03）

官网首页、采集能力、质量标准和数据市场中的相关文案统一为「视焦数据标准V3规范」，并更新脚本缓存版本。采集参数、目录和样式保持本次构建校验结果。

- 当前发布：`/srv/eyecatcher/releases/20261103T131620Z`。
- 先前发布：`/srv/eyecatcher/releases/20261016T044705Z`，保留可恢复。
- 阿里云命令助手执行 ID：`t-hz0720160rdmn7k`，退出码 0。
- 代码版本：公开仓库 `1936b0f923de49d2fef95ac70de312dcbb7670d5`，私有仓库 `0aa92be0961a36ae52aa5d782f1899bdae8c0da5`。
- 服务器通过 HTTPS 校验五个线上文件 SHA-256；目录 466 条（机器人实采 411、机器人仿真 55、真人双目 0）。
- 浏览器确认质量标准与真人双目市场说明使用完整名称，无横向溢出。
- Caddy 配置校验通过，PrintLink 健康检查通过。

部署回执：`output/aliyun-standard-name-deployment-result.json`；验证记录：`output/aliyun-standard-name-verification.json`；线上截图：`output/preview/shijiao-data-standard-v3-live.png`。


## 独立数据市场、真人双目样例与商务咨询（2026-11-06）

官网新增 `market.html` 与 `contact.html` 独立页面；首页保留 6 条精选数据，查看更多和合作咨询分别进入独立页。商务对接按陈先生、方先生排序，保留公司地址和邮箱。

- 当前发布：`/srv/eyecatcher/releases/20261106T065143Z`。
- 先前发布：`/srv/eyecatcher/releases/20261103T131620Z`，保留可恢复。
- 部署回执：`/var/backups/eyecatcher/20261106T065143Z/deployment.json`。
- 阿里云命令助手执行 ID：`t-hz0729s797wd3pc`，退出码 0。
- 官网核心文件版本：公开仓库 `adabbdb18bbe3842ad401b2c14bfe720b4df69fe`，私有仓库 `0849718ef638926a46f4862df8c1c957e6753cf2`。后续部署脚本和记录提交不改变该组静态文件。
- 当前目录 119 条：真人双目 4 组、机器人实采 60 条、机器人仿真 55 条。其余 351 条实采记录已从当前源 JSON、CSV、统计和运行目录移除。
- 8 个核心文件和 52 个样例文件均通过 SHA-256 校验；16 个 MP4 均通过 HTTP Range 检查。数据在阿里云共享目录 `/srv/eyecatcher/shared/stereo-20261106-280167a1bef3/media/`，由当前版本的 `media` 软链接提供访问。
- 浏览器核对左右目视频播放、时间戳/IMU/候选标定展示、真实 CSV 下载、联系人顺序与微信复制；首页 320 像素下无横向溢出。
- 样例保留原始工程状态披露，UTC 对齐、SI 单位、轴向及候选标定尚待验证，未声称通过完整 V3 验收。
- Caddy 配置未修改，PrintLink 健康检查通过。

样例通过 Workbench 上传到 `/tmp/stereo-samples-20261106.zip` 后校验并解包。`deployment/aliyun_market_update.py` 支持已校验的本地上传包，也支持从已发布静态镜像逐文件下载；先校验文件，再原子切换官网软链接，线上检查失败自动回退。下载源使用 HTTPS 并保留证书校验。

公开备份位于 [真人双目样例 Release](https://github.com/Shouchen77/data-acquisition/releases/tag/stereo-samples-20261106)，使用 8 个分片传输；`fetch_stereo_samples.py` 自动拼接并校验，不需要手工合并。

本地回执：`output/aliyun-market-pages-deployment-result.json`；验证记录：`output/aliyun-market-pages-verification.json`、`output/market-pages-local-verification.json`、`output/stereo-release-verification.json`；线上截图：`output/preview/contact-page-live-20261106.png`、`output/preview/market-page-live-20261106.png`、`output/preview/stereo-sensor-live-20261106.png`。

仅恢复之前官网版本时，在服务器执行：

```sh
sudo ln -s /srv/eyecatcher/releases/20261103T131620Z /srv/eyecatcher/rollback-market-pages
sudo mv -Tf /srv/eyecatcher/rollback-market-pages /srv/eyecatcher/current
```


## 网站图标与自定义筛选控件（2026-11-06）

首页、独立数据市场和合作咨询页使用用户提供的图标，包含多尺寸 `favicon.ico`、32 像素 PNG 和 Apple Touch Icon。数据市场四个下拉筛选改为自定义浅色面板，使用橄榄绿选中状态、数量徽标和可滚动列表；移除“数据来源”筛选以及旧链接中的 `source` 筛选参数，保留记录本身的来源说明。

- 当前发布：`/srv/eyecatcher/releases/20261106T081710Z`，先前发布：`/srv/eyecatcher/releases/20261106T065143Z`。
- 阿里云命令助手执行 ID：`t-hz0729ztnq9d88w`，退出码 0。
- 核心代码提交：公开仓库 `78b5a325d0254bbd5510da74133cc65256aa3ece`，私有仓库 `f4c1475`。
- 11 个核心文件和 52 个样例文件通过校验；16 个视频 Range 检查通过，目录保持 119 条。
- 验证桌面和 320 像素布局、场景与细分场景联动、方向键/End/Enter/Escape、单面板展开、点击外部关闭、重置及空场景。线上“果园”返回 3 条，浏览器无错误。
- Caddy 配置保持原样，PrintLink 健康检查通过。

发布回执：`output/aliyun-controls-deployment-result.json`；本地与线上验证：`output/market-controls-verification.json`、`output/market-controls-live-verification.json`；线上效果：`output/preview/market-controls-live.png`。

## 全站内容边界与定制服务缩进（2026-11-06）

统一首页、独立数据市场、合作咨询及页脚的左右边界：宽屏内容最大宽度 1440 像素，桌面沿用 8.3vw 边距，900 像素及以下使用 7vw。定制服务取消旧的双列侧栏，标签、标题、说明和流程共用左边界；手机流程每行第一项取消额外内边距。首屏底部分隔线预留 100 像素，避免说明文字与线条重叠。

- 当前发布：`/srv/eyecatcher/releases/20261106T090820Z`；上次发布：`/srv/eyecatcher/releases/20261106T084557Z`；更新前官网：`/srv/eyecatcher/releases/20261106T081710Z`。
- 阿里云命令助手执行 ID：`t-hz072a4dy4vcmww`，退出码 0。
- 核心代码提交：公开仓库 `e05f270d6ad5d64f3f8d6c94f1b87ac52bb872a6`，私有仓库 `6ceaa62fe737664adbc16fa20ac9bf7c6570feff`。
- 11 个核心文件、52 个样例文件和 16 个视频 Range 请求通过校验，数据目录保持 119 条。
- 首页检查 1920、1280、900、390、320 像素；市场和咨询页检查 1920、320 像素，内容边界一致且无横向溢出。补充核对首屏在 1920、1280、320 像素下的底部间距。
- 线上 1920 像素各板块左右边距均为 240 像素，定制服务标题与下方咨询提示左边界一致，浏览器无错误。
- Caddy 配置未修改，PrintLink 健康检查通过。

发布回执：`output/aliyun-alignment-deployment-result.json`；验证记录：`output/alignment-audit-20261106.json`、`output/hero-spacing-verification-20261106.json`、`output/alignment-live-verification-20261106.json`；线上截图：`output/preview/workflow-alignment-live.png`。
