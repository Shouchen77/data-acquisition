# 上传 GitHub 与发布网站

完整项目包：`output/shijiao-data-website-github.zip`。

## 上传项目

1. 解压项目包，得到 `shijiao-data-website` 文件夹。
2. 在 GitHub 新建仓库，例如 `shijiao-data-website`。
3. 将该文件夹内的内容上传至仓库根目录，确保 `index.html`、`README.md` 和 `.github/` 都直接位于仓库根目录。主分支使用 `main` 或 `master`。

项目包含网站源码、三个品牌图片文件、全部 466 条目录数据及原始 JSON/CSV、采集与导入脚本、公网预览工具、架构与发布说明、设备采集子项目的源码/测试/文档及已有工程验证记录。原始录像、厂商 SDK、临时下载工具、运行状态、日志、Git 历史与生成的压缩包按忽略规则排除。

使用终端上传时，在解压后的项目目录运行以下示例命令，并把仓库地址替换为你创建的真实地址：

```sh
git init -b main
git add .
git commit -m "Initial website project"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

认证时使用 GitHub 提供的登录方式。仓库中已包含 `.gitignore`，无需提交本机运行文件。设备采集程序依赖特定硬件与配置，使用说明见 `device_capture/离线使用说明.md`。

## 使用 GitHub Pages 长期在线

1. 打开仓库的 **Settings → Pages**。
2. 在 **Build and deployment → Source** 中选择 **GitHub Actions**。
3. 打开 **Actions → Deploy website to GitHub Pages → Run workflow**，选择主分支运行。以后推送到 `main` 或 `master` 会自动更新网站。
4. 工作流成功后，在 **Settings → Pages** 查看实际访问网址。普通项目仓库通常使用 `https://你的用户名.github.io/仓库名/`。

免费账户可使用公开仓库发布 Pages；私有仓库的可用性取决于账号方案。启用 Pages 后，网站由 GitHub 托管，不依赖当前电脑开机或本地临时隧道。

工作流仅将 `build_public.py` 生成的 `output/public_site/` 发布为网站，包含 HTML、CSS、JavaScript、网站 Logo 和市场目录。设备采集代码保留在项目仓库中，不作为网站页面发布。网站资源使用相对路径，兼容普通项目仓库下的路径。

现有数据市场引用 Maniformer 公开任务目录和来源视频链接；视频仍从来源站点按需加载，压缩包没有下载视频文件。

## 本地运行与更新

网站运行只需要 Python 3，无需 Node.js 或 npm：

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

访问 `http://127.0.0.1:8765/`。

更新原始采集数据后执行 `python3 import_market.py`；执行 `python3 build_public.py` 可生成静态部署包，执行 `python3 package_project.py` 可重新生成 GitHub 完整项目包。

官方参考：[GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。
