# 知识库制作与可复现构建

## 数据分层

1. 原始来源：固定提交的课程、引擎，带固定修订和哈希的古籍/GeoNames快照，发布版77个案例归档。
2. 核心库：SQLite原文、分段、来源版本、定位、条件原句、备注与核验状态；FTS5用于词检索。
3. 向量：只编码合格核心片段，Qwen3-Embedding-0.6B固定revision、1024维、归一化。长度预算和行映射绑定实际来源。
4. 存档与候选：旧版本命案例无损分片保存；抽取的重复段落独立候选库，只有显式选择才查，不因重复而变成通用规则。
5. 解释：每轮根据实际问题重算/检索；Codex读取事实、原文与有限历史，用可核对编号回答。模型生成的解释不写成古籍原文。

完整来源与许可见[SOURCES](../SOURCES.zh-CN.md)和[第三方说明](../THIRD_PARTY_NOTICES.md)。课程有非商业等要求，不把本项目MIT许可扩展到全部知识材料。

## 固定输入在哪里

| 清单 | 用途 |
|---|---|
| `config/sources.lock.json` | 引擎、天纪、人纪的仓库URL与完整commit |
| `config/source-assets.lock.json` | 随Git分发的4个古籍JSON和3个GeoNames文件的大小与SHA-256 |
| `config/embedding-model.json` | Qwen模型revision、相对快照路径、维度、前缀与长度设置 |
| `config/model-checksums.json` | 固定模型文件的预期大小和SHA-256 |
| `data/MANIFEST.json`、`SHA256SUMS.txt` | v4.0-13d年度归档大小、哈希、出生配置和主题数量 |
| `design/*schema.sql` | 原文知识库与无损案例分片schema |

固定版本用于复现，不跟随上游最新分支。安装器检查现有上游的HEAD和已跟踪改动，拒绝强制重置。随库快照用原字节提交以保持哈希。

## 自动构建

```powershell
python -X utf8 scripts/bootstrap.py --profile full --device cpu
```

core模式同样取得课程和古籍，只省略大型旧案例/候选与同盘索引。`--lexical-only`省略模型与向量；这是明确的词检索选择，返回结果会显示实际模式。

各阶段日志显示在终端，状态和输入指纹在`runtime/`。本机覆盖清单在`manifests/`，它反映实际构建结果，不随Git伪装成已安装数据库。

## 构建阶段与维护入口

安装、补齐和重建统一使用`bootstrap.py`，避免手抄一组工具命令漏建目录、清单或后续索引。用`--dry-run`查看当前版本实际命令、顺序和输入输出；`--workers 1`同时降低案例建库与候选抽取并发；`--rebuild`要求重跑构建（年度案例仍会校验后复用）。

| 阶段 | 实现工具 | 保留的契约 |
|---|---|---|
| 固定仓库与公开引擎 | `fetch_sources.py`、`extract_engine.ts` | 精确commit、现有改动不被重置 |
| 核心原文与城市 | `build_knowledge.py`、`import_renji.py`、`collect_geography.py` | 原字形、领域、来源、定位、条件和固定快照 |
| 模型与向量 | `download_model.py`、`build_embeddings.py` | 从`config/`读固定模型和校验值，生成实际`manifests/`；无需手工复制清单 |
| 原始案例与分片 | `download_assets.py`、`build_cases.py` | 每包SHA、完整出生键、去重主题逐字还原核验 |
| 隔离候选 | `extract_dataset_references.py`、`import_dataset_references.py` | 来源例盘、主题和未知条件；不进入默认语义索引 |
| 同盘 | `build_twins.ts`、`pack_twins.py`、`verify_twins.ts` | 命身与14主星16维筛选，再逐盘核对原生完整结构 |

模型约1.21GB；已有完整文件先核SHA后离线复用，配置改变则按新pin准备，旧权重保留。向量长度审计随索引保存，复用索引时可恢复审计清单。`manifests/`表示本机实际准备结果，不作为下一次下载选择的来源。

不存在精确出生键时不使用邻近生日替代，当前QS与旧XD2口径分别保留；同盘索引是合成出生配置，不是实际人口档案。开发者单独调用底层工具时需负责全部前置阶段与范围标记，最终仍用`doctor --experience`核对完整安装。

## 质量与条件

- 每条保留原字形、来源修订、原段哈希、视频时间/卷章、许可和适用条件原句。没有自动识别到条件不等于无条件。
- 原生规则保留实际TypeScript谓词；自然语言规则未全部转换为机器可执行条件。
- 编码损伤、可疑古籍整理和数据集候选独立标记，默认不进入正常语义索引。
- 借对宫不等于本宫实坐，必须核对实际同宫、亮度、煞曜、四化、性别、层次和流派。
- 引文返回`truncated:true`时必须用更大的`source --max-chars`完整重读，再判断条件。
- 向量记录来源ID、标题/原文指纹、模型与查询契约，错配时拒绝旧映射并说明降级。
- 语料改变后重建原文库与向量，不能只替换向量文件。

## 更新与重建注意

先备份个人记录，停止正在查询本工作区数据库的网页/脚本，再构建。生成表不存私人笔记。写入使用暂存数据库并校验后替换；Windows若有未关闭读句柄，替换会失败而不是删除旧库。

`collect_classics.py`和`collect_geography.py`可用于主动采集新资料，但不是复现当前固定快照的必要步骤。替换快照须更新锁文件和来源修订、保留旧版与差异，不要混用同一ID下不同原文。

案例归档、分片和候选库应按需备份；模型、来源和数据库不放Git。个人笔记在`runtime/personal.sqlite`，网页研读在`runtime/chat.sqlite`，两者分别备份。
