# GitHub 上传与网站发布

本仓库为视焦科技官网与数据市场的公开项目：<https://github.com/Shouchen77/data-acquisition>。

## 自动发布

仓库使用 GitHub Actions 发布 GitHub Pages。主分支为 `main`，工作流为 `.github/workflows/deploy-pages.yml`。推送更新后，工作流运行 `python3 build_public.py`，将 `output/public_site/` 部署为网站。

可在仓库 **Actions** 查看部署状态，在 **Settings → Pages** 查看访问地址。Pages 的 Source 使用 **GitHub Actions**。

仓库包含网站源码、品牌图片、466 条市场目录、原始 JSON/CSV、采集与导入脚本、预览工具和架构说明。网站部署目录只包含网页运行所需文件。

## 本地运行

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

访问 <http://127.0.0.1:8765/>。

更新原始采集数据后执行 `python3 import_market.py`；执行 `python3 build_public.py` 可生成静态部署包，执行 `python3 package_project.py` 可重新打包本仓库。

市场条目引用 Maniformer 公开目录并保留来源标识。视频按需从来源站加载，仓库不含视频文件。

官方参考：[GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。
