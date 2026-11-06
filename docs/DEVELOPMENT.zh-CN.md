# 开发、更新与发布

## 日常更新

先备份，再停止正在使用本工作区的网页与查询：

```powershell
python -X utf8 ziwei.py personal backup
python -X utf8 ziwei.py chat backup
& .\scripts\stop-workbench.ps1
git pull --ff-only
python -X utf8 scripts/bootstrap.py --profile full --device cpu --install-skill
```

沿用原来的core/full、关键词/GPU选择。bootstrap按输入指纹复用步骤，不删除模型、源文件、出生记录或对话。更新后运行doctor并启动网页。源码工作区使用`pip install -e .`，不要只搬一个wheel而漏掉引擎、配置和资料。

个人库分别备份：`personal backup`与`chat backup`互不包含。完整迁移还需模型、来源、知识/案例、索引和清单。恢复数据库前停止写入、保留现库并校验备份，不直接覆盖活跃SQLite。

## 修改代码

```powershell
python -m pip install -r requirements-dev.txt
python -X utf8 tools/test_codex_review.py
python -X utf8 -m unittest discover -s tests -v
cd web
npm ci --ignore-scripts
npm run build
cd ..
python -X utf8 scripts/check_release.py
```

会话回归使用明确的模型/检索替身及隔离数据库，不消耗真实模型额度。发布/迁移检查验证固定快照、路径绑定、安装计划和公开文件保护。涉及实际排盘/检索时再用虚构输入运行真实CLI；涉及网页时还须实际操作、桌面/手机截图和控制台检查。构建成功不等于功能已验收。

`tools/evaluate.py`读取随仓库提供的`tests/fixtures/retrieval-questions.json`固定60题与`examples/fictional-first.json`虚构样例，需要完整资料及语义模型，不再依赖作者本机输入。不要改题目来提升分数。报告/来源/版本变化要保留适用条件和差异，不把程序正常等同于传统断语预测准确。

## 更新知识或上游

1. 登记来源URL、固定修订、许可、定位、哈希、条件和未知项。
2. 需要新版本时修改`config/sources.lock.json`或快照/模型清单，审查上游差异。
3. 安装器遇到不匹配的旧上游目录会拒绝重置。请保留旧工作区，用新目录获取新pin并验证；不要为通过安装而丢弃自己改动。
4. 重建受影响原文和向量，校验行映射、词检索、领域、完整出处和模型离线载入。
5. 案例或同盘算法更新时重新核对生成版本、还原哈希和原生匹配；当前QS与旧XD2差异仍保留。
6. 更新CHANGELOG与文档，再提交。

`runtime/build-state.json`仅是复用记录，不是原始资料。如果需要重新执行阶段可用`--rebuild`；不要删除`runtime/`来清构建缓存，因为其中还可能有个人记录和对话。模型选择以`config/`为准，下载器校验后记录本机`manifests/`，不继续沿用过时下载清单。

## 网页开发

正式页面由Python服务提供`web/dist/`。一般修改后运行`npm run build`，再刷新本地网页。`npm run dev`只提供前端开发服务，本项目未配置通往Python API的Vite代理；完整交互验证请使用构建后的Python工作台。

页面使用DESIGN.md和web样式。不要把内部英文枚举、哈希、CLI stderr或代码直接展示为普通解读；核对信息和原始出处仍保留。新增页面操作应有同等CLI/技能入口。

## 本机服务与编码器

网页默认8765，编码器8788。Windows启动/停止脚本会核对服务归属，拒绝误停其它应用。编码器5分钟闲置退出；多工作区有端口冲突时，先等待旧服务退出，或核对其命令行与工作区后停止。不要按进程名批量结束Python/Node。

本机语义模型和库可离线使用；Codex回答需要模型服务联网。查网络错误时只保留脱敏诊断，不在Issue粘贴登录文件、真实出生输入或完整私人对话。

## 发布流程

1. 建分支，完成代码/文档/虚构示例与相关检查。
2. `git status`核对仅源码、固定清单、小型快照与文档；运行`check_release.py`。
3. 提交时给具体行为说明，推送后检查GitHub Actions。
4. 更新版本与CHANGELOG后可创建tag/release；不将本机数据库或模型挂成未经许可的数据发布。

CI包含Windows/Linux会话与迁移检查、网页生产构建，以及Ubuntu核心词检索构建。它不会下载1.21GB模型、跑全77年重建或使用个人Codex账号；这些完整链路仍需发布前本机实测。完整安装后用`doctor --experience`验本地功能/技能/网页与Codex连接，再做一次真实问答，不能把登录成功计为模型实答。平台支持以实际验证范围为准。
