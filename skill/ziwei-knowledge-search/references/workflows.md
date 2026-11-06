# 阅读、记录、报告与诊断

以下命令均在项目根目录通过`python -X utf8 ziwei.py`，也可使用技能的`query.py`。

| 目的 | 命令与行为 |
|---|---|
| 直接知识问答 | `ask "问题"`返回证据包，Codex核对后作答；不伪装独立聊天模型 |
| 持续命盘追问 | `ask "继续分析事业" --profile ID --topic career`，或复用此前的出生JSON |
| 课程/古籍目录 | `catalog`；`browse tianji-462faa4 --offset 0 --limit 20 --filter 紫微`；`source ID`读完整片段 |
| 人纪历史原文 | `search "问题" --namespace renji`；`browse renji-fdafae1`；分组证据含原行ID，不将检索排序当医学核定 |
| 保存命盘 | 用户要求保存时：`personal save --kind profile --title "名称" --input-file <出生JSON>`，记住返回ID |
| 列出/取回记录 | `personal list --kind profile --query "名称" --offset 0 --limit 100`；按has_more翻页，`personal get --id ID`读全文；`--kind`还支持note/bookmark/session/liuren；命盘可按ID或精确唯一名称调用 |
| 更新/收藏 | `personal save --kind bookmark --id <可选旧ID> --title "出处" --input-file <JSON>`；收藏数据`{"evidence_id":"TJ-462faa4-0396"}`；已有ID不可变更kind |
| 本地会话 | 用户要求保存时将问题、Codex答复、出生引用、出处ID写成JSON，用`personal save --kind session`；不自动记录所有聊天 |
| 删除 | 用户明确要求时`personal delete --id ID`，仅处理指定记录 |
| 一致性备份 | 用户要求时`personal backup`，返回exports内独立.sqlite路径，或`--output-file <绝对路径.sqlite>`；不覆盖旧文件，只含个人记录，不含全部知识库/模型 |
| 五种报告 | `report --input-file <出生JSON> --mode sanhe --hide-birth`生成HTML/Markdown/SVG/PNG/PDF，绝对路径返回；mode还支持feixing/sihua |
| 保存本次解释 | 先将当前Codex综合解释及引文写为UTF-8 Markdown，再`report ... --analysis-file <绝对路径>`；报告把本次解释和原文分开标注 |
| 范围/完整性 | `coverage`查看资料与评测；`doctor`检查所选范围；`doctor --deep`做完整性校验；`doctor --experience`实际验完整语义/计算/案例/同盘、网页资源、技能绑定和Codex接口/登录，不发起模型回答 |
| 可选网页 | `serve --port 8765`或工作区`scripts/start-workbench.ps1`；网页使用同一工具层，CLI不依赖它 |

`ask "问题" --namespace renji --mode lexical`用于知识型分域词检索，不带出生输入。`ask`带`--view natal`明确返回本命，移除保存输入的period；日期、农历流年、大限序号互斥，显式CLI目标会替换旧period目标。doctor必需项失败退出码为1；网页停止用`scripts/stop-workbench.ps1`核对归属，不能按端口盲杀。

网页记录支持名称/类型筛选、20条分页、正文持续阅读及更名；编辑查询会清掉旧结果，关闭或切换后旧异步请求不会重开过时详情。命盘与会话分开保存，未授权不自动记录全部聊天。单条JSON按UTF-8实际字节上限200KB，过长会话应分段或另存Markdown。

模型固定于工作区`models/Qwen3-Embedding-0.6B/<revision>`，为独立普通文件，不提交Git。查询编码器仅监听127.0.0.1:8788，按需启动，闲置5分钟退出。修改模型路径、提示前缀或长度后，旧进程会被配置契约校验拒绝；等待闲置退出或依维护文档验证进程归属后重启。检索索引与原文指纹不符时应重建，不能隐瞒语义降级。

数据空白：未取得经核完整《紫微斗数全集》底本；网站专属精解、完整评分公式、私有运限断语、另外四项安星流派及旬空的非基准切换未声称复刻。当前四部古籍电子页、天纪/人纪及公开案例覆盖各自声明范围，不等于天下资料全部收齐。使用范围与许可见工作区SOURCES.zh-CN.md，功能与差异见README.md及docs/WEB.zh-CN.md。core或关键词安装的未安装能力先用status/doctor核对，不当成资料全库不存在。


## 网页直接问答与 CLI 会话

网页“问答研读”实际调用当前账号的 Codex CLI；从命盘/合盘/工具/原典旁直接发起带上下文的提问，引用可打开，支持逐轮追问与重算。`chat status`检查连接；`chat ask "问题"`直接生成答案，出生输入/`--profile`绑定命盘，`--second`加另一盘，`--source ID`解释原典，`--tool`解释工具；`--session ID`续问时不另传输入。`chat list/get/export/delete/backup`管理会话；`chat cancel/retry --turn ID`停止/重试。

`ask`返回证据供当前 Codex 对话解释；`chat`会额外发起模型调用并自动保存本地会话，二者不能混称。`chat backup`单独备份聊天库；旧 `personal backup`只备份个人记录。两类数据库都可能包含私人出生资料，不提交。完整图文步骤与 LLM职责表见工作区 `USAGE.zh-CN.md`。

`chat ask --session ID`续问时，主题/关系/时间变更写在问题中；不要同时传`--topic/--namespace/--relation`，这些选项只用于新建会话。出生对象、资料领域或所选原典变化时新建研读。数字中文完整日期及ISO日期可用于追问，农历日期先转换；一个问题含多个目标时间时应拆开提问，尚无完整多时点并列计算。原典研读默认使用所选来源的领域补查。具体问题如“不要感情，改看公历2027年11月6日的太岁事业流日”“不是感情了，改看合伙”。
