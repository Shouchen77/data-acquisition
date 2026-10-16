# 公网访问与发布

长期在线地址：<https://shouchen77.github.io/data-acquisition/>。网站已由 GitHub Pages 托管，不依赖本地电脑开机。

以下为此前的本机临时预览方式，可按需使用。

当前公网预览：

<https://difficulties-impact-cabinet-jets.trycloudflare.com/>

数据市场：

<https://difficulties-impact-cabinet-jets.trycloudflare.com/#market>

这是 Cloudflare Quick Tunnel 临时预览，朋友可直接通过 HTTPS 链接访问，无需连接同一个局域网。网站服务器与隧道已在本机后台启动；电脑需要保持开机、联网并避免睡眠。关闭隧道、电脑断网或关机后，链接无法访问；重新创建隧道会生成新地址。该服务适合分享预览，没有长期在线保证。

## 管理预览

在项目目录运行：

```sh
python3 public_preview.py status
```

重新启动或更新当前网站内容：

```sh
python3 public_preview.py start
```

命令会重新生成发布目录；如果预览进程仍在运行，会继续使用当前链接，不重复创建隧道。进程已停止时会生成新链接，以终端输出和 `.runtime/public-preview.json` 中的地址为准。

停止公网分享：

```sh
python3 public_preview.py stop
```

只停止本项目创建的服务器和隧道。日志位于 `.runtime/website-server.log`、`.runtime/cloudflare-tunnel.log`；这些文件不在发布目录中。

## 长期部署产物

- `output/public_site/`：独立静态网站目录，包含首页、样式、脚本、Logo 和数据目录。
- `output/website-public.zip`：可上传至静态网站托管或服务器的压缩包，解压根目录直接包含 `index.html`。
- `output/public_build_manifest.json`：发布文件校验信息及任务数量。

重新生成发布文件：

```sh
python3 build_public.py
```

长期在线应把 `output/public_site/` 部署到云端静态托管或 Web 服务器，此时不再依赖当前电脑。可以先使用托管平台提供的网址，再绑定自己的域名；具体平台、账号与域名需按实际拥有的资源选择。

当前本机提供发布文件的地址为 `http://127.0.0.1:8766`。公网服务只提供发布目录，关闭目录列表；原始采集文件、脚本、文档、运行日志与 Git 目录均不对外提供。来源视频继续按用户点击直接从 Maniformer 加载。

参考：[Cloudflare Quick Tunnel 官方说明](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)。
