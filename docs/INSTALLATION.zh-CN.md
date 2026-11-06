# 安装与首次运行

## 系统依赖

推荐Windows 10/11、Python 3.12、Node.js 24+、Git。Python 3.13可尝试，Linux/macOS仍以实际CI与本机验证为准。不要把项目放在下载缓存目录。所有命令从项目根目录执行，默认用PATH上的`python`。

| 依赖 | 用途 / 核查 |
|---|---|
| Python | `python --version`；推荐3.12；UTF-8方式运行 |
| Node.js与npm | `node --version`、`npm --version`；固定引擎适配器需要Node 24+ |
| Git | `git --version`；获取三个固定版本的公开源仓库 |
| Cairo原生运行库 | PNG/PDF导出；安装Python的CairoSVG包不能代替Cairo本体 |
| TrueType中文字体 | Windows默认微软雅黑；其它系统可设置`ZIWEI_REPORT_FONT` |
| Codex CLI和已登录账号 | 仅自动问答需要；计算、原文检索、图文导出可独立运行 |
| CUDA GPU | 可选；CPU也能运行语义检索，首次编码会更慢 |

Cairo安装以[CairoSVG官方说明](https://cairosvg.org/documentation/)为准：Windows可通过GTK等方式提供Cairo，并使其DLL所在目录在当前进程PATH内；macOS安装cairo/libffi；Linux安装对应发行版的Cairo/FFI依赖。原生依赖放在可维护的工具目录，无需复制进本Git。

Ubuntu示例（实验性平台）：

```bash
sudo apt-get update
sudo apt-get install libcairo2 libffi-dev fonts-wqy-zenhei
```

自定义PDF字体应为ReportLab支持、允许嵌入的中文TrueType字体（`.ttf`或适用`.ttc`），不是任意CFF/OpenType。PowerShell中可设置：

```powershell
$env:ZIWEI_REPORT_FONT = '你的中文字体绝对路径.ttf'
```

## 选择安装范围

| 方式 | 具体内容 | 主要不包含的内容 |
|---|---|---|
| `--profile full`（默认） | 全部课程/古籍、地点、计算、语义检索、77年案例、候选库、同盘索引、网页 | Codex账号与聊天模型服务需另登录 |
| `--profile core` | 课程/古籍、地点、计算、语义检索、网页、报告 | 旧版案例、案例候选库和同盘索引 |
| 任一方式加`--lexical-only` | 以原文关键词检索；不下载嵌入模型或建向量 | 语义召回；其它已选范围仍可构建 |

完整资料约包含3.46GB案例分片、3.45GB候选数据库、1.21GB模型和其它源文件/中间结果，建议至少20GB空闲。core关键词方式不需要GPU和聊天模型下载。完整安装的批量构建可能耗时较长，终端会显示当前阶段。

## 完整安装自动获取的仓库与模型

使用者只需克隆主仓库`yuguo-Jack/Ziwei_doushu`。执行`bootstrap.py --profile full`后，安装器会自动获取下列来源，按固定版本放入对应子目录；**不需要用户再自行逐个git clone或手动下载模型**。

| 类型 | 上游与固定版本 | 用途 / 保存位置 |
|---|---|---|
| 引擎仓库 | [Renhuai123/ziwei-doushu · a600484](https://github.com/Renhuai123/ziwei-doushu/tree/a600484a49255039d0725f1ba9e11ca81a948f97) | 公开排盘和算法代码，位于`repo/` |
| 天纪仓库 | [Renhuai123/nihai-tianji-corpus · 462faa4](https://github.com/Renhuai123/nihai-tianji-corpus/tree/462faa4c70af40b8b87ad82ffa82a5823a485e94) | 课程引文、时间点和勘误，位于`sources/tianji-462faa4/` |
| 人纪仓库 | [Renhuai123/nihai-renji-corpus · fdafae1](https://github.com/Renhuai123/nihai-renji-corpus/tree/fdafae1ea685756a92a59179fdfa2e6a01379100) | 独立领域的历史课程原文，位于`sources/renji/` |
| 嵌入模型 | [Qwen/Qwen3-Embedding-0.6B · 固定快照](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/tree/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3) | 约1.21GB、1024维，用于本地语义检索；位于`models/Qwen3-Embedding-0.6B/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/` |
| 年度案例数据 | [ziwei-doushu v4.0-13d](https://github.com/Renhuai123/ziwei-doushu/releases/tag/v4.0-13d) | 1950–2026共77个`.jsonl.zst`原包，位于`sources/v4.0-13d/`；构建为案例分片及候选库 |

古籍电子页和GeoNames快照已包含在主仓库，不需另克隆仓库。仓库完整commit见`config/sources.lock.json`，模型完整revision见`config/embedding-model.json`，案例归档逐包SHA-256见`data/MANIFEST.json`。安装器会核对模型文件和案例归档，模型快照包含权重、分词器及必要配置，不要只复制一个权重文件。

自动准备顺序：Python依赖与可编辑CLI → 三个固定源仓库 → 两个Node项目依赖 → 核心知识与城市库 → 嵌入模型和向量 → 77年案例、候选与同盘索引 → 网页生产构建 → doctor → 可选技能安装。

**需要手动准备的部分**是前述Python、Node.js、Git、Cairo和中文字体。要用网页自动问答，再单独安装Codex CLI并完成自己的账号登录；Qwen嵌入模型负责检索，Codex账号所用模型服务负责生成解释。安装器不下载本地聊天模型，也不代为授权账号。来源许可分别保留，见[第三方说明](../THIRD_PARTY_NOTICES.md)。

## 安装

```powershell
git clone https://github.com/yuguo-Jack/Ziwei_doushu.git
cd Ziwei_doushu
python -X utf8 scripts/bootstrap.py --profile full --device cpu --install-skill
```

安装器会安装固定Python依赖和可编辑包，获取固定上游，执行两个`npm ci`，核验随库快照，构建资料/索引与网页并运行doctor。原生Cairo与中文字体需先按上文准备。命令失败会返回非零退出码，保留已完成阶段；修复对应原因后重跑，不会删除个人记录。

已有适配GPU的PyTorch时，保留自己的官方CUDA构建，使用`--device auto`。显式`--device cpu`会请求CPU PyTorch并使构建子进程使用CPU。PyTorch CUDA版本选择按[官方安装页](https://pytorch.org/get-started/locally/)核对；不要盲目复制另一台机器的CUDA后缀。

较轻体验：

```powershell
python -X utf8 scripts/bootstrap.py --profile core --lexical-only --install-skill
```

安装命令的其它选项：

- `--dry-run`：只显示步骤，不下载、不构建。
- `--workers 1`：减少完整案例构建的并行内存和CPU占用，默认3，范围1–8。
- `--npm-cache <目录>`：控制npm缓存。检测到本机`D:/codex/tools`时优先使用其npm-cache，否则使用项目`.cache/npm`。
- `--skip-python-deps` / `--skip-node-deps`：只在已准备好对应依赖时使用；不会自动补缺。
- `--rebuild`：重新执行构建阶段；已有通过校验的年度分片等仍可能被其构建器复用。

`runtime/build-state.json`保存构建输入指纹，`runtime/installation.json`保存本机所选范围。项目的`models/`为持久模型位置，不是可随意清理的缓存。Git不跟踪这些生成结果。

## 验证与启动

```powershell
python -X utf8 ziwei.py doctor
python -X utf8 ziwei.py status
python -X utf8 ziwei.py search '三方四正' --limit 3
python -X utf8 ziwei.py chart --input-file examples/fictional-first.json
python -X utf8 ziwei.py serve --port 8765
```

安装成功并启动最后一条`serve`命令后，在**运行该服务的同一台电脑**的浏览器地址栏输入：

```text
http://127.0.0.1:8765/
```

`127.0.0.1`也叫localhost，代表浏览器所在的电脑；不是作者的电脑或公网站点。每位使用者安装并启动自己的服务后，都可以在自己的电脑使用同一地址。GitHub展示源码与文档，当前项目未提供公共在线演示。保持服务终端开启，Ctrl+C停止后地址便不可用。

`doctor`必须项失败会返回1；明确未请求的可选资料会显示未安装，不冒称完整安装。网页仅监听127.0.0.1。Windows还可用`scripts/start-workbench.ps1`后台启动，`scripts/stop-workbench.ps1`按身份核对后停止；其它平台可前台运行并用Ctrl+C停止。

端口被其它应用占用时换`--port 8766`，不要按端口盲目终止进程。查询编码器使用本机8788端口，按需启动、闲置5分钟退出；同机多个工作区暂不能同时共享它，请先停止旧工作区编码器或等待退出。

## Codex与技能

按[Codex CLI官方说明](https://developers.openai.com/codex/cli/)安装后：

```powershell
codex login
codex login status
python -X utf8 ziwei.py chat status
python -X utf8 scripts/install_skill.py
```

网页问答和`chat`使用本机当前登录账号，需要联网和可用额度。不会索要或记录登录令牌。配置可见`config/codex-chat.json`与`.env.example`；本应用读取进程环境变量，不自动加载`.env`文件。

技能默认装入`CODEX_HOME/skills/ziwei-knowledge-search`，未设置CODEX_HOME时使用用户目录`.codex/skills/`。安装器生成的`workspace.json`只存在本机，绑定当前项目；搬家重新安装，另一个工作区需显式`--replace`。新建Codex对话以发现技能。

## 常见安装问题

| 现象 | 处理 |
|---|---|
| `python`指向商店占位程序 | 安装真实Python并核对PATH；Windows也可先用`py -3.12`确认 |
| `npm`找不到或Node版本旧 | 使用含npm的Node 24+标准安装，重开终端检查 |
| 上游版本不同或有改动 | 安装器会拒绝重置；保留改动，用新目录安装或自己审核迁移 |
| GitHub/Hugging Face不可达 | 检查本机网络/代理；修复后重跑，不需要交出账号令牌 |
| 模型未完整下载 | 重跑安装或`tools/download_model.py`，保持固定revision |
| `no library called cairo` | 配好原生Cairo及其进程PATH，重开终端再doctor |
| 缺少PDF中文字体 | 设置有效`ZIWEI_REPORT_FONT`；网页标题裁切字体不能代替完整报告字体 |
| core中旧案例或同盘不可用 | 按需重跑`--profile full`，不要把未安装误报成资料不存在 |
| 问答未连接 | 核对`codex login status`及`chat status`；普通排盘检索仍可用 |

进一步排查见[开发维护](DEVELOPMENT.zh-CN.md)。
