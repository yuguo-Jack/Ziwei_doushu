# 产品介绍视频

延续根目录`DESIGN.md`的深墨、古金、青玉与中文宋体，1920×1080、60fps、严格30秒。140BPM的70拍对应九个镜头组、八个导航章节；用短句、界面特写、透视推进、方向转场和工具快闪展示功能，再交代克隆/安装/登录/提问与网页/CLI/技能入口。完整安装命令留在README。网页与问答画面来自仓库已公开的虚构示例截图，不读取个人记录。

剪辑节奏与参考见[REFERENCES.md](REFERENCES.md)。

文件按用途分开保存：

| 目录 | 内容 |
|---|---|
| `media/product-tour/` | 制作源文件、最终音轨、字体及许可、重制说明 |
| `web/public/media/product-tour/` | `intro.mp4`成片、`poster.jpg`封面、`chapters.json`章节、`zh-CN.vtt`字幕 |
| `.cache/product-tour/` | 本机制作缓存、原始语音、中间文件与验证记录，不提交 |

网页右上角“观看介绍”使用本地成片；已烧录字幕，文字字幕另供下载。

## 可维护源文件

- `index.html`、`composition.css`、`composition.js`：HyperFrames画面、排版与可反向拖动的GSAP时间轴。
- `storyboard.json`：中文旁白、章节、BPM与固定拍数；`timing.json`为按拍生成并核对实际旁白时长的确定时序。
- `assets/soundtrack.m4a`：已完成的旁白与原创合成配乐，可直接离线复用。配乐由`produce.py`确定性合成，不引用第三方音乐录音。
- `assets/display.woff2`、`sans.woff2`：Noto中文字体的重命名静态子集，来源、哈希及OFL许可在同目录。
- `produce.py`：准备隔离制作目录、可选重制旁白，以及将HyperFrames成片压缩为浏览器兼容的H.264/AAC MP4。
- `manifest.json`：实际交付文件的时长、编码、大小和SHA；更新成片时重新生成。

## 重制流程

观看与安装工作台无需执行本节。重制需要Python 3.12、Node.js 22+、FFmpeg/FFprobe和可供HyperFrames调用的Chrome/Chromium。

制作依赖使用HyperFrames **0.9.19**和GSAP **3.14.2**，与网页运行依赖分开。将它们安装到自己的工具目录；下面以项目忽略目录演示，Windows也可将`--prefix`和`--cache`指向D盘共享工具目录：

```powershell
npm install --prefix .cache/product-tour/tools --cache .cache/npm --ignore-scripts --no-audit --no-fund hyperframes@0.9.19 gsap@3.14.2
python -X utf8 media/product-tour/produce.py prepare --gsap-file .cache/product-tour/tools/node_modules/gsap/dist/gsap.min.js
$VideoCli = '.cache/product-tour/tools/node_modules/hyperframes/bin/hyperframes.mjs'
node $VideoCli check .cache/product-tour/composition
node $VideoCli snapshot .cache/product-tour/composition --at 0.5,1.2,2.5,5,8.5,11.8,14.3,15.2,16,16.9,19,22.5,24.7,25.8,26.8,28.6 --no-end
node $VideoCli render .cache/product-tour/composition --output .cache/product-tour/master.mp4 --fps 60 --quality standard --workers 4 --crf 18
python -X utf8 media/product-tour/produce.py package --render .cache/product-tour/master.mp4
```

首次制作可先使用`hyperframes init`的blank模板；当前`prepare`已能从仓库源文件重建制作目录，不依赖模板留下的临时文件。浏览器路径可用`HYPERFRAMES_BROWSER_PATH`指定；HyperFrames工具缓存用`HYPERFRAMES_CACHE_DIR`指定；渲染临时目录与帧缓存应指向本项目`.cache/product-tour/`，不要进入源码。

修改旁白后，再执行以下可选步骤，然后重新`prepare`、检查、查看关键帧、渲染和打包：

```powershell
python -m pip install -r media/product-tour/requirements.txt
python -X utf8 media/product-tour/produce.py audio
```

`audio`会把`storyboard.json`中的公开旁白文字发送到Edge TTS服务，复用未变片段并裁去首尾静音，然后合成140BPM鼓点、低音、琶音、转场音与旁白，更新时序和字幕。旁白超过固定拍数窗口会报错，避免偷偷截断或拖长30秒时间线。不发送命盘、知识库或私人资料；服务可用性和声音不保证永久不变，已提供的完成版音轨可离线复用。

新增画面文字后可用`produce.py fonts --display-font <NotoSerifSC-VF.ttf路径> --sans-font <NotoSansSC-VF.ttf路径>`重新生成带OFL的静态子集并更新`assets/fonts.json`；工具会拒绝遗漏的中文字符。展示字重700，正文字重400，CSS与实际字体匹配。

`package`两遍编码并将视频控制在单文件10MiB发布限制内，保留1080p画面和faststart以便浏览器起播。它同时更新唯一的封面和成片清单。更新后重新构建网页，并核对实际播放、章节、字幕、音频、手机布局及HTTP Range拖动。

GitHub首页使用GitHub视频附件内嵌播放，不能链接到仓库的大文件预览页。更换成片后，在GitHub的README编辑器上传新MP4，将生成的附件链接单独放一行，并通过该编辑器提交，使附件关联到公开README；再拉取这次提交。不要只复制未提交草稿的附件链接。附件与本地成片保持同一版本，发布后核对未登录访问和实际播放。

所有原始语音片段、WAV、中间MP4、编码日志、快照、制作目录和HyperFrames记录位于被忽略的`.cache/product-tour/`。这些不属于交付源码；不要把整个制作目录或工具安装目录加入Git。网页成片、完成版音轨和字体为明确的最终资产。视频制作与工作台启动均不会自动提交或推送。
