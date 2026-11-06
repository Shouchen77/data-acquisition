# 数据市场维护

运行目录为 `data/market_catalog.json`（schema 2），由 `import_market.py` 合并机器人参考源与真人双目摘要。

## 当前记录

- 真人双目：4 组工程样例（橘子、树莓、金桔采摘与汽修），各 1 段。
- 机器人实采：60 条，每个既有来源场景保留 12 条，覆盖不同设备、细分场景和触觉配置。
- 机器人仿真：55 条。

其余 351 条实采记录已从当前 JSON、CSV、源统计和运行目录移除。`data/robot_curation.json` 记录保留 ID 和筛选方法。Git 历史保留正常版本记录，不重写提交历史。

## 真人样例字段

`data/eyecatcher_stereo_datasets.json` 使用 `schema_version: 1` 和 `datasets` 数组。

| 字段 | 内容 |
| --- | --- |
| dataset_id / title / description | 唯一编号、名称与场景描述 |
| scene_id / subscene | 一级与细分场景；新增 agriculture（农业） |
| availability / episode_count | available 或 sampling；实际任务段数 |
| duration_seconds / capture | 真实时长及分辨率、帧率、IMU 频率等；缺失项不自动补造 |
| previews.left / right | 两路公开 HTTPS 或 `media/stereo/` 下的站内视频 |
| poster | 真实样例视频截帧 |
| sample_data_url | 传感器与文件清单摘要 JSON |
| delivery_contents / sample_stats | 包内实际内容、帧数和 IMU 样本数 |
| qa_report_url | 如有正式公开 QA 报告再填写 |

样例详情分为双目视频、传感器数据、文件下载。传感器摘要展示原始 CSV 前 8 行、抽样 IMU 曲线、完整候选标定内容；每个原始文件可下载并查看 SHA-256，另提供不含视频的传感器与标定 ZIP。

## 文件生成与发布

`prepare_market_samples.py` 从用户提供的四个样例目录复制 MP4、CSV、YAML，生成截图、实测统计和展示用摘要。视频原始文件与 CSV 不改写；网页预览使用样例包中已有的 H.264 版本。IMU 曲线单位为 counts，不把空白 SI 列当作有效物理量。

原始视频每目 1920 × 1200，预览 1280 × 800。每组实际有 901 帧/目、9,002 个 IMU 样本。时间频率按设备计数器测算；主机 Unix 时间只是估计值。候选标定、UTC、量程与轴向验证状态保持原始文件结论；VIO 和完整 QA 报告未包含。

52 个公开文件打包在 GitHub Release `stereo-samples-20261106`，并部署到阿里云网站。二进制媒体不进入 Git 历史；`fetch_stereo_samples.py` 根据 `output/stereo_sample_manifest.json` 校验恢复。用户原始微信 ZIP 和其他采集目录不修改。

普通摘要改动后执行 `python3 import_market.py` 与 `python3 build_public.py`。具体发布和回退见 `ALIYUN_DEPLOYMENT.md`。
