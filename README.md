# 视焦科技 · 具身智能数据采集与数据市场

[官网](https://eyecatcher.cn/) · [数据市场](https://eyecatcher.cn/market.html) · [合作咨询](https://eyecatcher.cn/contact.html)

网站采用静态 HTML、CSS、JavaScript 和 JSON 目录，部署在阿里云。印蛙 PrintLink 独立运行于 <https://3d.eyecatcher.cn/>。发布记录见 [ALIYUN_DEPLOYMENT.md](ALIYUN_DEPLOYMENT.md)。

## 页面

- `index.html`：品牌、采集服务、视焦数据标准V3规范、6 条精选数据预览、定制流程及合作入口。
- `market.html`：独立数据市场，支持类型、场景、臂型、触觉和关键词筛选；详情链接可直接分享。
- `contact.html`：独立合作咨询页，商务对接依次为陈先生、方先生；电话、微信复制、公共邮箱与公司地址。

## 当前数据

121 条目录：6 组真人双目工程样例、60 条机器人实采参考和 55 条机器人仿真参考。机器人实采从 411 条筛选为 60 条，其余 351 条已从当前源 JSON、CSV、统计和运行目录中移除。每个既有应用场景保留 12 条，兼顾细分场景、设备、臂型与触觉配置。

真人样例为橘子采摘、树莓采摘、金桔采摘、汽修、电焊和裁缝。前四组附带左右目 MediaPipe 手部关键点 JSON，并在详情中提供逐帧 3D 骨架视图；电焊和裁缝已上架双目视频、时间戳、IMU 与标定文件，手部关键点待补充。样例按文件的工程状态披露：UTC 对齐、SI 量程与坐标轴、候选标定尚待验证；不自动声明已通过完整 V3 验收。

- `data/maniformer_data_market.json` / `.csv`：115 条保留的机器人参考记录。
- `data/maniformer_data_market_summary.json`：保留目录的统计。
- `data/robot_curation.json`：实采保留策略和 ID。
- `data/eyecatcher_stereo_datasets.json`：6 组真人样例摘要。
- `data/market_catalog.json`：网站读取的 schema 2 混合目录。
- `output/stereo_sample_manifest.json`：82 个公开样例文件的大小与 SHA-256。
- `media/stereo/20261124/`：公开样例文件，不在 Git 中重复保存；由 GitHub Release 的 14 个分片分发并部署到阿里云。

参考来源为 [Maniformer](https://www.maniformer.net/dataShop)，保留来源与公开参考身份。最初采集 466 条记录；当前项目仅保留 115 条。机器人视频继续使用来源链接。

## 本地预览与构建

```sh
python3 fetch_stereo_samples.py
python3 import_market.py
python3 -m unittest discover -s tests
node --check app.js
node --check site.js
python3 build_public.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory output/public_site
```

打开 <http://127.0.0.1:8765/>。`fetch_stereo_samples.py` 校验并下载已公开的样例，已有正确文件时跳过下载。GitHub Actions 在构建前自动执行同一步骤。`output/public_site/` 和 `output/website-public.zip` 是完整发布产物，包含样例数据。

## 商务联系

1. 陈先生：13750899295；微信 cfj19960208pw。
2. 方先生：13285719508；微信 sochyf。

公司：杭州视焦科技有限公司 / EYECATCHER TECHNOLOGY。邮箱：fzlunar@hotmail.com。地址：杭州市西湖区振华路210号栖锦云座2号楼539室。

设备采集子项目 `device_capture/` 单独维护。公开样例之外的设备录像、SDK 和其他本地采集数据不进入网站构建。
