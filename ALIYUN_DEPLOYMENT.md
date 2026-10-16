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

- 官网当前版本：`/srv/eyecatcher/current`，指向 `/srv/eyecatcher/releases/20261016T043520Z`。
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
