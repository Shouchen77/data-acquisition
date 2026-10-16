# 视焦科技 · 具身智能数据采集与数据市场

杭州视焦科技有限公司官网，采用静态 HTML、CSS 和 JavaScript，可通过 GitHub Pages 发布。

## 网站内容

品牌介绍、数据采集服务、数据市场、定制服务流程和企业联系信息。网站内容与页面规划见 [网站架构](SITE_ARCHITECTURE.md)。

数据市场包含 466 条成功采集的公开任务记录：真机 411 条、仿真 55 条、有触觉 8 条，覆盖 5 个一级场景和 26 个细分场景，附 2,963 条动作标注。支持任务搜索、组合筛选、分批加载、任务详情及按需播放视频。

## 数据文件

| 文件 | 内容 |
| --- | --- |
| `data/maniformer_data_market.json` | 原始公开任务记录及解析后的动作数组 |
| `data/maniformer_data_market.csv` | 便于表格软件使用的扁平化导出 |
| `data/maniformer_data_market_summary.json` | 采集数量和各维度统计 |
| `data/market_catalog.json` | 网站读取的 466 条任务目录 |
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

`build_public.py` 生成 `output/public_site/` 及静态部署包。GitHub Actions 工作流仅发布首页、样式、脚本、Logo 和市场目录。推送至 `main` 后自动部署。详见 [发布说明](GITHUB_PUBLISH.md)。

## 联系我们

- 公司：杭州视焦科技有限公司
- 联系人：首辰
- 电话：13285719508
- 微信：sochyf
- 地址：杭州市西湖区振华路210号栖锦云座2号楼539室

设备采集程序单独维护。本仓库包含完整的网站项目、市场数据、采集与导入脚本及部署工具。
