# 真人双目数据市场录入

网站运行时读取 `data/market_catalog.json`（schema 2）。通过 `import_market.py` 合并两类来源：既有 Maniformer 机器人参考任务，以及 `data/eyecatcher_stereo_datasets.json` 中的视焦真人双目公开摘要。

当前真人摘要源为 `{"schema_version":1,"datasets":[]}`。没有真实已审核的公开数据时，保持空数组；页面显示“待上架”和场景定制入口。

## 录入字段

每个 `datasets` 元素使用下列字段：

| 字段 | 要求 | 含义 |
| --- | --- | --- |
| dataset_id | 必填、唯一字符串 | 视焦数据集编号，导入后自动加 `ec:` 命名空间 |
| title / description | 必填字符串 | 数据集标题、范围与任务说明 |
| scene_id | 必填 | factory / medical / home / logistics / retail / office / food |
| subscene | 必填字符串 | 如装配工位、器械准备区、厨房 |
| availability | 必填 | sampling（样例采集中）或 available（可咨询交付） |
| episode_count | 可空整数 | 实际任务段数；available 必须大于 0 |
| duration_seconds | 可空非负数 | 实际总时长，单位秒 |
| task_tags | 字符串数组 | 任务标签，如分拣、收纳；默认空数组 |
| capture | 对象 | 实测 width、height、fps、imu_hz、fov_h、fov_v；未测填 null 或省略 |
| previews | 对象 | left / right 为已审核公开 HTTPS 视频地址，两路同时填写或同时省略 |
| qa_report_url | 可选字符串 | 已审核公开的 HTTPS 质检报告地址 |
| delivery_contents | 字符串数组 | 此数据集确认可提供的内容；不填写未知内容 |

`capture` 是实测值，不能用官网 V3 最低参数自动补齐。报告存在只展示“报告可查看”，不自动认定验收通过。缺失规格显示“待披露”。

数据集可区分不同场景，机器人专有字段（机械臂、手型、触觉）不要求真人填写。已有机器人详情与动作步骤保持独立。

## 发布步骤

1. 确认实际样例、公开授权和摘要内容；填写真人摘要源中的真实记录。
2. 执行 `python3 import_market.py`，检查 `data/market_import_report.json` 中真人数据集数、机器人参考数和总数。
3. 执行 `python3 -m unittest discover -s tests -v` 与 `node --check app.js`。
4. 执行 `python3 build_public.py`，通过 HTTP 预览 `output/public_site/`；验证真人卡片、双目预览与质检入口。
5. 发布构建文件到官网，保留旧版本，核对文件哈希与线上结果。

不需要修改前端代码来增加普通真人数据集。新增一级场景时，在 `import_market.py` 的 `SCENES` 统一维护，再重新导入。

## 公开目录与原始交付

导入程序只将规定的公开摘要字段写入运行时目录。操作者身份、原始 GPS、设备本地路径等额外字段不会进入官网。原始录像、IMU、标定、VIO 与逐帧文件不放入网站或 GitHub，公开预览和报告使用单独审核后的文件地址。

`data/eyecatcher_stereo_datasets.json` 本身是版本库中的**公开摘要源**，不要在其中写入秘密、操作者信息或未经审核的链接。白名单是导入时的防线，不替代源文件管理。

既有 Maniformer 记录保留 `mf:` 命名空间与公开参考属性，不改变为自有数据或真人数据。不要把参考视频链接当作本站可交付原始文件。
