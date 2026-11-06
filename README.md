# 紫微研习 · Ziwei Doushu

**可在本机使用的紫微斗数工具、可回查知识库、Codex 搜索技能与网页工作台。**

程序负责历法、排盘、星位与运限计算；知识库提供原文、出处、版本和适用条件；Codex 负责解释、比较与多轮追问。CLI 和技能是完整入口，网页提供“玄金观星台”界面。

Local, source-referenced Ziwei tools and retrieval with a Codex-powered workbench. Windows is the verified platform; Linux/macOS are experimental.

[安装](docs/INSTALLATION.zh-CN.md) · [使用](USAGE.zh-CN.md) · [网页功能](docs/WEB.zh-CN.md) · [知识库构建](docs/KNOWLEDGE_BASE.zh-CN.md) · [第三方依赖与许可](THIRD_PARTY_NOTICES.md) · [维护开发](docs/DEVELOPMENT.zh-CN.md)

![本地工作台，虚构示例盘](docs/screenshots/workbench.jpg)

## 可以做什么

| 能力 | 本地命令 / 入口 |
|---|---|
| 概念、原话、条件和出处检索 | `ask`、`search`、`source`、`catalog`、`browse`；无需生日 |
| 出生地点、历史时区、公农历、真太阳时与排盘 | `city`、`calendar`、`chart`；钟表小时和时辰序号分别输入 |
| 十三主题、本命/大限/流年/月/日/时 | `context`、`period`、`period-context`、`flights` |
| 感情、合伙、上下级、朋友双盘比较 | `compare`；不伪造网站专属评分 |
| 未知时辰、同盘结构、小六壬 | `time-candidates`、`twins`、`liuren`；候选不等于真实时辰 |
| 旧版本命案例与待核候选资料 | `case`、显式候选检索；完整安装启用 |
| 可直接连续提问 | `chat ask`、`chat get/list/export`；实际调用已登录的 Codex CLI |
| 保存、收藏、备份、导出 | `personal`；HTML、Markdown、SVG、PNG、PDF 报告 |
| 网页六个页面 | 命盘研究、问答研读、资料库、合盘、工具箱、本地记录 |

每项能力都有 CLI/技能入口。`ask`返回证据包，由当前 Codex 对话解释；`chat ask`会另调用 Codex CLI 自动回答。普通排盘、检索、保存和导出不需要聊天模型。

## 快速开始

先准备 **Python 3.12、Node.js 24+、Git**。PNG/PDF 导出需要 Cairo 和中文字体，Windows 配置见[安装说明](docs/INSTALLATION.zh-CN.md#系统依赖)。GPU 可选；CPU 可以运行嵌入模型。

```powershell
git clone https://github.com/yuguo-Jack/Ziwei_doushu.git
cd Ziwei_doushu
python -X utf8 scripts/bootstrap.py --profile full --device cpu --install-skill
python -X utf8 ziwei.py doctor
python -X utf8 ziwei.py serve --port 8765
```

打开 **http://127.0.0.1:8765/**。完整安装会获取固定版本的三个上游仓库、下载约1.21GB嵌入模型、构建77年案例与候选库及同盘索引，建议至少留 **20GB** 空间；首次可能需要数十分钟到数小时。下载与构建可保留已完成阶段，失败后修复原因并重跑同一命令。

想先体验计算、知识检索和网页，可选择较轻安装：

```powershell
python -X utf8 scripts/bootstrap.py --profile core --lexical-only --install-skill
```

此方式不下载嵌入模型，使用关键词检索；**不含旧版案例、案例候选库和同盘索引**。去掉`--lexical-only`即启用语义检索；以后重跑完整安装可补齐资料。`status`和`doctor`会说明已安装范围。

`--dry-run`只显示准备步骤。已有合适的 Python/Node 依赖可分别用`--skip-python-deps`、`--skip-node-deps`；这些选项不会替你验证或修复缺失依赖。

### 接通网页里的 Codex

按 [Codex CLI 官方说明](https://developers.openai.com/codex/cli/)安装并登录，在终端检查：

```powershell
codex login
codex login status
python -X utf8 ziwei.py chat status
```

网页“问答研读”会使用当前账号额度。无需本网站 API Key，无需再下载聊天模型。**Codex 回答需要联网**；问题、选定命盘、相关引文与有限前文会交给模型服务。资料库、索引与嵌入模型留在本机。

![实际Codex多轮研读，使用虚构示例](docs/screenshots/chat-desktop.jpg)

### 在 Codex 中直接调用技能

安装器会将技能复制到标准技能目录，并在本机绑定当前项目路径。新建一个 Codex 对话后可问：

```text
$ziwei-knowledge-search 三方四正是什么意思？用通俗语言解释，给出处和适用条件。
```

未使用安装器时可单独运行`python -X utf8 scripts/install_skill.py`。技能可从任意工作目录调用，项目搬家后重新安装即可；也可设置`ZIWEI_KB_ROOT`。切换到另一个工作区需要显式`--replace`。

### 直接使用 CLI

```powershell
python -X utf8 ziwei.py search '空宫借星' --limit 5
python -X utf8 ziwei.py source GUIDE-borrow --max-chars 100000
python -X utf8 ziwei.py chart --input-file examples/fictional-first.json
python -X utf8 ziwei.py ask '结合条件研读事业' --input-file examples/fictional-first.json --topic career
python -X utf8 ziwei.py chat ask '150字解释空宫借星，附出处'
```

所有示例出生资料均为虚构。真实使用先核对日期、钟表时刻/时辰、地点、时区与流派参数。详细命令、保存和跨对话追问见[使用手册](USAGE.zh-CN.md)。

## 知识库与数据范围

固定来源基线包括：

- 天纪4,886条原始记录，去重后4,881组；人纪六部课程19,294条原行另域保存。
- 四个古籍电子页、1,818个原段落，保留固定修订、卷章与网站出处。
- 完整安装提供1950–2026共77年的674,976种出生配置、8,774,688个主题；这些是生成的旧版本命存档，**不是实际真人档案**。
- 34,204个城市的GeoNames固定快照、传统算法说明、公开引擎规则和术语。

原文与可执行条件分开保存；检索到某条断语不代表本盘满足。课程未逐条复听、古籍未通校所有刻本，候选材料不进入默认语义索引。具体来源、版本、许可和缺口见[SOURCES.zh-CN.md](SOURCES.zh-CN.md)。

## 项目组织

```text
src/ziwei_kb/       Python工具、检索、会话、网页后端
web/               React网页与固定npm依赖
scripts/           安装、获取固定来源、安装技能、启动/停止
tools/             知识库、案例、向量和同盘构建器及回归检查
tests/             发布与迁移检查
skill/             可安装的Codex技能模板
config/            上游版本、模型、快照校验和Codex设置
design/            数据库schema与界面规范
docs/              安装、功能、构建、架构和维护文档
sources/           小型可分发快照；其它上游由脚本获取
repo/              安装器获取的固定上游引擎（不提交）
knowledge/ cases/ indexes/ models/ manifests/  本机构建结果（不提交）
runtime/ logs/ exports/                     个人数据与运行产物（不提交）
```

本仓库保存源码、构建配方、固定版本清单、许可和必要的小型快照。模型和大型数据库在本地构建，不通过Git传输；无需Git LFS。

## 更新与维护

```powershell
python -X utf8 ziwei.py personal backup
python -X utf8 ziwei.py chat backup
# 停止正在使用本工作区的网页与查询后更新
git pull --ff-only
python -X utf8 scripts/bootstrap.py --profile full --device cpu --install-skill
```

保留原有配置选择；使用GPU或关键词安装时沿用相应参数。安装器按输入指纹复用构建，不会删除模型或个人记录，也不会重置被修改的上游仓库。完整维护、故障排查、测试与发布步骤见[开发维护说明](docs/DEVELOPMENT.zh-CN.md)。

## 许可与范围

项目新增代码使用[MIT](LICENSE)。上游MIT代码、课程CC BY-NC-SA 4.0、案例声明CC BY 4.0及其中引文例外、GeoNames CC BY 4.0、古籍电子版本条款、字体OFL等**分别保留**，详见[第三方说明](THIRD_PARTY_NOTICES.md)。代码MIT不代表所有知识材料可商业使用。

本项目基于[Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu)及公开语料构建，与收费网站无隶属关系。未恢复其私有评分、闭源专属断语和小限子层，也未取得《紫微斗数全集》可靠完整底本。用于传统文化资料研读；计算和检索验收不等于预测有效性认证。
