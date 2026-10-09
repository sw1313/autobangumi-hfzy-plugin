> 这是 AutoBangumi 3.x 的归档。4.x 请使用仓库根目录。

# AutoBangumi HFZY Plugin

皇甫朝云的 AutoBangumi 杂项插件。设置页是单独一块，各项开关互不影响，配置写在
`config/hfzy.json`，不进入 AutoBangumi 主配置。

本仓库只包含这个杂项插件，不包含 CD2 插件、AutoBangumi 核心源码、真实配置、
下载数据或数据库。

## 功能

- 下载列表播放按钮。
- 非聚合订阅填写了名称时，TMDB 查询优先使用这个名称。
- 添加或编辑规则时，在季度后面显示过滤后的版本数和视频数。版本按去掉集号后的发布差异计算，第 12 集的 [END]、修订版 v2、标题末尾的 `.mp4.torrent` 都不会单独成版；合集不会计入。
- 用 http 打开页面时，RSS 源旁边的复制按钮仍能复制完整链接。
- 某条过滤正则命中 RSS 标题时，对应标签套上橘黄色框。
- 搜索剧集和电影时包含 TMDB 标记为成人的动画。同名但没有动画类型的条目仍会跳过。
- 收集和订阅时，对话框里填写的季度优先于文件名上的季号。同一条 RSS 里如果混了好几季，都会进这个季度。
- 方括号里的 `[v2]` 识别为更高修订版。发布组名字带空格时，用标题开头的方括号补上。
- 判断单集时只数视频。字幕或字体压缩包、ass、srt 不再把这一集算成多文件。
- 同一集已经有文件时，更高修订版可以挂起，或替换旧文件。默认挂起。

## 更新

### 2026-10-08

- 特别篇可以按第 0 季重命名。开关在杂项里，电视特别篇、OVA、SP 改成 S00E。没有数字的 TVSP 为 S00E01。剧场版仍按标题重命名。
- 添加 RSS 且解析器是 TMDB、没有打开聚合 RSS 时，可以选剧集或电影并填写 TMDB 编号。编号优先于可选名称，名称优先于种子标题。打开聚合 RSS 后这一栏隐藏并清掉编号。
- 添加对话框只在主程序里留一个插槽来渲染插件组件。编号查询和特别篇重命名都在插件里。
- 杂项设置增加修订冲突，可选挂起或替换。
- 补上带空格发布组的修订识别，`[Nekomoe kissaten]...[v2]` 这种标题可以和没有 v2 的同一集比较。
- 自动替换时忽略视频以外的字幕和字体附件。

只数视频会替换 `revision_file_count`。重命名代码调用这个函数后，字幕压缩包开关才会生效。

## 目录

```text
overlay/extensions/hfzy/                 后端插件、启动入口和测试
overlay/webui/src/extensions/hfzy/       WebUI 设置与下载页组件
config/hfzy.example.json                 配置示例
```

## 安装

将 `overlay` 下的目录合并到 AutoBangumi 源码挂载目录：

```bash
cp -a overlay/. /volume1/docker/autobangumi/app/
```

Docker Compose 挂载插件目录，并把后端加入 `PYTHONPATH`：

```yaml
volumes:
  - /volume1/docker/autobangumi/app/extensions:/extensions

environment:
  - PYTHONPATH=/extensions/hfzy/backend
```

启动 AutoBangumi 前执行 `/extensions/hfzy/backend/ab_entry.py`。源码挂载部署
可以在 entrypoint 中设置：

```bash
export AB_APP_DIR=/app
export PYTHONPATH="/extensions/hfzy/backend:${PYTHONPATH}"
exec python /extensions/hfzy/backend/ab_entry.py
```

如果同时使用 CD2 插件，两个后端目录都要放进 `PYTHONPATH`，并由各自的
bootstrap 注册。

WebUI 需要在项目的本地扩展注册器中调用
`registerHfzyExtension(registry)`，然后重新构建 WebUI。

## 配置

复制示例配置到 AutoBangumi 的持久化配置目录：

```bash
cp config/hfzy.example.json /volume1/docker/autobangumi/config/hfzy.json
```

请勿提交真实的 `config/hfzy.json`。

## 测试

```bash
PYTHONPATH=overlay/extensions/hfzy/backend \
pytest overlay/extensions/hfzy/tests -q
```

## 兼容性

该插件通过启动时 bootstrap 注册设置和 API，并在运行时修补 RSS、TMDB
相关调用，不修改 AutoBangumi 的 `module/` 核心源码。上游内部接口发生变化时
仍可能需要适配。

## 安全说明

- 仓库只提供开关默认值，不包含账号、令牌或下载地址。
- 播放接口使用 AutoBangumi 现有登录态签发短时流令牌，仓库里没有密钥。

## 许可证

MIT

