# 视焦科技 · 具身智能数据采集与数据市场

网站：<https://eyecatcher.cn/> · [数据市场](https://eyecatcher.cn/#market)

印蛙 PrintLink：<https://3d.eyecatcher.cn/> · GitHub Pages 备用站点：<https://shouchen77.github.io/data-acquisition/>

杭州视焦科技有限公司官网，采用静态 HTML、CSS 和 JavaScript，已部署至阿里云服务器，GitHub Pages 保留作为备用站点。配置、数据位置及回退说明见 [阿里云部署记录](ALIYUN_DEPLOYMENT.md)。

## 网站内容

品牌介绍、真人第一视角双目采集服务、V3 质量标准、数据市场、定制服务流程和企业联系信息。网站内容与页面规划见 [网站架构](SITE_ARCHITECTURE.md)。

数据市场包含 466 条成功采集的公开任务记录：真机 411 条、仿真 55 条、有触觉 8 条，覆盖 5 个一级场景和 26 个细分场景，附 2,963 条动作标注。市场按“真人双目 / 机器人实采 / 机器人仿真”分类，并按工厂、医疗、家居等七个场景筛选。支持任务搜索、组合筛选、分批加载、任务详情及按需播放视频。真人双目暂未上架，展示场景定制入口；数据录入方法见 [真人数据录入说明](MARKET_DATA.md)。

## 数据文件

| 文件 | 内容 |
| --- | --- |
| `data/maniformer_data_market.json` | 原始公开任务记录及解析后的动作数组 |
| `data/maniformer_data_market.csv` | 便于表格软件使用的扁平化导出 |
| `data/maniformer_data_market_summary.json` | 采集数量和各维度统计 |
| `data/market_catalog.json` | 网站读取的 schema 2 混合目录，现有 466 条参考任务 |
| `data/eyecatcher_stereo_datasets.json` | 真人双目公开摘要源，目前为空 |
| `data/market_import_report.json` | 导入校验结果 |

目录来源为 [Maniformer 数据市场](https://www.maniformer.net/dataShop)，条目保留来源信息，作为网站演示内容使用，不代表视焦自有数据商品。视频保存为来源链接，未下载或转存视频文件。

原接口声明总量为 467；采集时 ID 341 的服务端数据异常导致 HTTP 500，实际成功采集 466 条。`collect_maniformer.py` 为采集脚本，`import_market.py` 为规范化导入脚本。

## 本地预览

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8765/>。请通过 HTTP 访问，以便浏览器读取 JSON 文件。

## 更新与发布

```sh
python3 import_market.py
python3 build_public.py
```

`build_public.py` 生成 `output/public_site/` 及静态部署包。GitHub Actions 工作流仅发布首页、样式、脚本、Logo 和市场目录。推送至 `main` 后自动更新 GitHub Pages 备用站点，阿里云站点需单独发布。详见 [发布说明](GITHUB_PUBLISH.md) 与 [阿里云部署记录](ALIYUN_DEPLOYMENT.md)。

## 联系我们

- 公司：杭州视焦科技有限公司
- 联系人：首辰
- 电话：13285719508
- 微信：sochyf
- 联系邮箱：fzlunar@hotmail.com
- 地址：杭州市西湖区振华路210号栖锦云座2号楼539室

设备采集程序单独维护。本仓库包含完整的网站项目、市场数据、采集与导入脚本及部署工具。
