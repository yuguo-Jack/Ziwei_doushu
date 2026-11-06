# 紫微研习工具：从直接提问到备份

以下命令默认在项目根目录执行。先按[安装说明](docs/INSTALLATION.zh-CN.md)完成所需范围；首次公开版本0.1.0。

## 1. 最省事的用法：直接跟 Codex 说

完成安装后，一般不必启动网页或自己编写JSON。是否需要下载嵌入模型由所选安装方式决定。在Codex输入 `$ziwei-knowledge-search`，或明确说“用本地紫微知识库”，再写问题。当前Codex负责读证据、核条件和解释；本地脚本负责排盘和查资料。

只问概念，不需要生日：

```text
$ziwei-knowledge-search 我是初学者。排盘、命宫、身宫、三方四正分别是什么？用通俗话解释，给原文出处和适用范围。

$ziwei-knowledge-search 倪海厦《天纪》怎样讲太阳入庙与落陷？找可回放的课程时间点，区分课程原话和你的总结。

$ziwei-knowledge-search 找《紫微斗数全书》里关于官禄宫天同的原文，带前后文；别把借来的星说成本宫实际坐星。
```

问具体命盘时，一次说清出生资料。**下面都是虚构演示资料，不是你的出生资料：**

```text
$ziwei-knowledge-search 用虚构资料练习：男，公历1990年1月1日，出生地中国江苏南京，当地钟表上午8:30。
先确认采用的经度、时区和真太阳时换算，再排盘，通俗讲解事业。
把盘面事实、旧版案例文字、课程/古籍观点、你这次的解释分开，并给依据。
```

需要提供：

| 信息 | 例子与注意点 |
|---|---|
| 日期 | 明说公历或农历；农历说明是否闰月 |
| 时间 | “当地钟表上午8:30”或“已确定为辰时”；二者含义不同 |
| 性别 | 计算工具当前使用male/female两种参数 |
| 地点 | 国家、省/州、城市，避免同名城市选错；可先查坐标和历史时区 |
| 不确定项 | 时辰、是否夏令时等有疑问就直说，不要补猜值 |

若确实不知道出生时辰：

```text
$ziwei-knowledge-search 公历1990年1月1日，男，时辰不详。列十二时辰候选，比较命宫和主星结构；不要默认子时，也不要给无依据的校时置信度。
```

这是十二种假设，不会自动找出真实时辰；也不能仅靠日期解决真太阳时跨日问题。

## 2. 保存一次，之后按名称追问

起盘确认资料正确后，明确要求保存：

```text
把刚才确认的虚构命盘保存为“学习示例甲”，告诉我记录ID。
```

在同一对话可以直接继续问。换对话后，明确调用技能和记录名称：

```text
$ziwei-knowledge-search 读取本地已保存命盘“学习示例甲”，继续结合出处研读事业，不要重新猜出生资料。
```

名称完全相同且唯一时能直接取回；若重名，先列记录并使用ID。很久以前的记录也能分页找到，不再只看最新100条。

**命盘记录与聊天记录是两件事。** 保存命盘保存的是出生输入和计算口径，当前Codex聊天不会自动全文写进本地SQLite。要长期保留结论，可以说：

```text
把这次问题、你的完整答复、命盘记录ID和引用出处ID保存成一条本地会话，名称“学习示例甲·事业研读”。
```

以后让Codex读取该会话，或在网页“本地记录”里查找。正文可以持续阅读，原始数据可展开核对；单条记录上限为实际UTF-8编码200KB。太长的会话应分段保存或另存Markdown文件。

## 3. 怎样问运限、合盘和专项工具

### 流年与流月

```text
$ziwei-knowledge-search 读取“学习示例甲”，分析农历2026流年的事业，明确使用小限体系，给实际宫位与原文条件。

接着看公历2026年11月6日所在的流月，显式用太岁层级；说明它与上一问小限流年的区别。
```

- 大限为十年层次；流年为年，流月/日/时为更细层次。工具还有小限年龄层。
- CLI的 `--year 2026` 是**农历流年**；`--date 2026-11-06` 是**公历目标日期**。
- 目标日期、目标年、指定大限序号三选一；命令行的新目标会替换输入文件里旧目标。
- 流年支持小限`xiaoxian`与太岁`taishui`。流月、流日、流时目前仅支持显式太岁层级。不能当成网站私有的小限子层。
- 回到本命可以说“回到本命研读”，CLI用 `ask ... --view natal`，会清掉此前输入中的运限选择。
- 旧v4案例是固定版本的本命文字，不是目标年份/月份专用原文。

### 两人比较

```text
$ziwei-knowledge-search 读取“学习示例甲”和“学习示例乙”，按合伙关系比较实际星位、空宫借星与当前大限，给条件与出处；没有公开完整评分公式就不编分数。
```

支持感情、合伙、上下级、朋友四种关系。需要双方资料或已保存命盘，不能从单人命盘补猜另一方。

### 其它直接问法

```text
$ziwei-knowledge-search 查询“学习示例甲”的宫干四化去向、自化和对宫关系，先列计算事实。
$ziwei-knowledge-search 查这个命盘的同盘配置，分清“命身与14主星相同”和“全部原生盘面结构相同”，附各地钟表时间窗口。
$ziwei-knowledge-search 算当前时刻的小六壬，展示月、日、时的含起点计数过程。
$ziwei-knowledge-search 把农历2023年闰二月初一换成公历，并往返检查。
```

同盘结果是出生配置与盘面结构，不是实际真人名册、人口数量或“命运相同”的证明。小六壬目前按民用日，23时不自动换日。

## 4. 网页怎么用

启动：

```powershell
& 'scripts\start-workbench.ps1' -OpenBrowser
```

然后访问 [本地工作台](http://127.0.0.1:8765/)。仅本机监听。已有正确服务会直接复用；端口被其它服务占用时会拒绝启动，避免误停其它工程。

| 页面 | 操作 |
|---|---|
| 命盘研究 | 填生日、公历/农历、钟表时刻/已知时辰、性别；查城市后**点选匹配城市**，核对“用于计算”坐标和时区，再“排盘并查资料” |
| 命盘显示 | 选择本命/大限/流年/月/日/时；选目标日期与体系；三合/飞星/四化切换，点击宫位看对应主题 |
| 原文 | 点来源标题，在侧栏看正文、条件、勘误、相邻引文、原始链接；收藏后在本地记录回查，Esc关闭并回到来源按钮 |
| 资料库 | 选领域并检索；右侧选课程/古籍，填写“章节或原文筛选”再阅读，可翻页；繁简筛选统一匹配，原文保持原字形 |
| 合盘 | 核对甲乙双方资料和关系类型，再“比较双盘与依据”；修改资料后需重新比较 |
| 工具箱 | 同盘、历法、十二时辰候选使用研究页已排资料；小六壬使用当前设备时间 |
| 本地记录 | 按名称/类型查找、翻页；点命盘名称回载，点收藏打开来源，点笔记/会话读正文；“详情/更名”改标题；删除需确认 |
| 导出 | 导出报告会生成五种文件并打开HTML；SVG/PNG按钮可单独导出盘图；文件都在工作区exports |

初始页面是虚构示例。修改出生资料后出现“尚未更新”提示时，当前图和依据仍属于上次已排结果，需要重新排盘。

界面采用“玄金观星台”。右上角可切换夜景/日景，也可暂停星光动效；系统设为减少动态时会自动停止装饰动画。桌面左侧导航，手机底部导航，功能相同。小屏先点出生资料的“编辑资料”展开输入；时区、经度和流派参数收在“时区与排盘口径”中。

命盘默认适应屏幕，手机可看到全部十二宫概览。点“放大命盘”后可在图内横向滚动，再点“适应屏幕”还原。点宫位，或用Tab聚焦宫位后按Enter/空格，查看对应主题和三方四正；小屏下方另有清晰的所选宫位文字，“逐宫文字”可展开全部星曜。运限的事实栏同时标出当前层次宫位与对应本命宫位。概览中的细字需要放大或用文字版阅读。

资料库顶部三部书架可直接进入对应课程或古籍；《全书》书架进入卷一，右侧下拉框可换卷二、卷三。原文保持原字形，搜索和筛选同时支持繁简。手机顶部的书签和下载图标分别是“保存命盘”和“导出报告”。盘图与报告仍提供清晰的白底打印版本。

网页已经直接接入 **本机 Codex CLI**，使用当前登录的 Codex 账号，无需网站 API Key，也无需另下载聊天模型。进入左侧/底部的 **“问答研读”** 即可。手机新对话可点首屏“写下问题”直接跳到输入框。

1. **只问知识**：选“知识问答”和资料领域，输入“什么是三方四正”“比较两段原典的适用条件”等；无需生日。
2. **解读命盘**：先在命盘研究页修改并核对出生资料，点击“排盘并查资料”。再点右侧“解读当前命盘”，会带入已计算的出生资料、主题和当前运限；也可在问答页选“当前命盘”。初始填入的出生资料始终为虚构示例。
3. **全盘综述**：在问答中说“做一次覆盖十三主题的全盘综述，给出处与适用条件”。程序会准备十三主题，而非只复制当前宫位的一段提示。
4. **连续追问**：直接问“那感情呢”“不要感情，改看事业”“换成2027年呢”“回到本命”“这条为什么适用”“解释上一条引用[3]的原文”。程序保留同一出生对象，按识别出的主题/年份重新计算并检索。具体流月、流日、流时请给出完整日期，例如“公历2027年11月6日的太岁流日呢”或“2027-11-06的太岁流日呢”；农历可写“农历2027年1月1日的流日”，会先换算，流时再给“申时”。合盘中可说“不是感情了，改看合伙”，会重算关系视角并保留已有目标年。每轮先明确一个目标时间；多个日期/年份的并列比较尚未完整实现，会提示确认，不能把单一结果当作比较。含糊、缺失或不支持的目标会说明需要什么信息。
5. **合盘和工具**：先完成比较/计算，再点“解读这组双盘”或“解释这项结果”。小六壬使用当次计算时刻的快照，不会在解释时偷换成出生日期或新的当前时间。十二候选保持为假设，不代替校时定论。
6. **核对出处**：点回答下方的引用，打开原段、课程时间点或方法说明；也可点“解释这条资料”。从命盘研读中进入原典解释时会同时带入该命盘。程序代码改为通俗的方法说明；版本和核对标识保留在折叠区，原始出处仍可打开。
7. **切换、恢复与导出**：左侧“研读记录”（手机可展开）选择以前的对话；刷新网页可恢复最近一段。每段对话固定研读对象，换人、换双盘或换资料时新建研读。运限和主题可在同段中追问。回答期间可停止；失败后可重试原问题。底部可导出 Markdown 对话或删除该段。

**哪些地方需要 LLM？**

| 需求 | 本地程序与 Codex 各自负责什么 |
|---|---|
| 日期换算、排盘、星位、借星、四化、运限 | 程序确定性计算，不需要 LLM 猜答案 |
| 原文检索、出处定位、命盘保存、图像导出 | 本地索引、模型及脚本完成，不依赖聊天回答 |
| 术语解释、命盘十三主题和全盘综述 | Codex读计算结果与相关原典，组织通俗解释、条件和缺口 |
| “那感情呢”“换成明年呢” | 程序识别支持的主题/时间切换并重算，Codex结合前文继续分析 |
| 观点比较、借星条件、古今语义、证据冲突 | Codex对读已取回资料，区分原话、条件和综合解释 |
| 双盘、十二时辰候选、同盘与小六壬的含义 | 程序提供真实比较/算法结果，Codex解释差异，不造分数或概率 |

网页研读会把**问题、选定资料/命盘、相关引文及有限的前文**交给当前 Codex 账号使用的模型服务，使用其额度并需要联网；这不意味着大模型在本机离线运行。知识库、检索索引和嵌入模型仍在本机，不会把整个资料库一次性发送。只做排盘和查原文时不发起 Codex 回答。复杂解读耗时通常比短问答长，页面会显示核对/组织回答状态，支持停止。

网页和 `chat` CLI 的对话自动保存在 `runtime/chat.sqlite`，其中可能含出生资料；可导出、删除，或用 `chat backup`做一致性备份。它独立于原有 `personal` 记录，因此 `personal backup`不包含这份聊天数据库。当前 Codex 对话中使用 `ask`技能的既有“要求保存时才写个人记录”行为保持不变。

**网页不开也能调用的直接研读命令**：

```powershell
python -X utf8 ziwei.py chat status
python -X utf8 ziwei.py chat ask '三方四正是什么意思？150字内，给出处。'
python -X utf8 ziwei.py chat list
# 用上一条返回的 session.id 续问；不要另传出生资料，以免换错对象。
python -X utf8 ziwei.py chat ask '空宫借星为什么不等于同宫？' --session <会话ID>
# 下列文件是虚构示例；真实使用时替换为自己的输入文件或 --profile 命盘名。
python -X utf8 ziwei.py chat ask '用这张虚构示例盘做十三主题全盘综述' --input-file examples\fictional-first.json
python -X utf8 ziwei.py chat ask '比较合伙关系' --input-file <甲JSON> --second <乙JSON> --relation business
python -X utf8 ziwei.py chat ask '解释借星条件' --source GUIDE-borrow
python -X utf8 ziwei.py chat get --session <会话ID>
python -X utf8 ziwei.py chat export --session <会话ID>
python -X utf8 ziwei.py chat backup
```

`chat cancel --turn <消息ID>`停止，`chat retry --turn <消息ID>`重试最后一条失败/停止的问题，`chat delete --session <会话ID>`删除。`--tool calendar|liuren|time-candidates|twins`加主输入资料可研读工具结果；`--namespace tianji|yijing|fengshui|renji|all`等选择资料领域。`chat`会等待实际模型回答并返回状态、正文和引用，失败时退出码为1。`ask`仍只准备证据包，适合已经在 Codex 中的技能调用，避免无必要地再套一层模型。网页/`chat`会话与当前 Codex 聊天的上下文分开；需要在此继续某段网页研读时，可以让当前 Codex 用 `chat list/get`读取指定会话，无需手工复制正文。模型每轮使用最近10轮和简短记忆，完整会话仍保存在本地。

`chat ask`的`--topic`、`--namespace`、`--relation`用于新建会话；`--session`续问时把主题、关系和目标日期写进问题，例如`chat ask '不是感情，改看2027年合伙关系' --session <会话ID>`。续问中另传这些设置会明确报错，避免参数看似生效却仍使用旧设置。更换出生对象、原典或资料领域请新建会话。原典研读默认从所选来源所属领域补查相关资料。

未连接时先在终端运行 `codex login status`，必要时执行 `codex login`完成登录，然后在网页点“检查连接”。更换 CLI 路径可设置 `ZIWEI_CODEX_CLI`为本机可信程序绝对路径；模型名可用 `ZIWEI_CODEX_MODEL`或`config/codex-chat.json`配置。默认使用 Codex 内置可用模型，不继承全局工具/插件设置；可在项目配置中指定模型。模型超时默认300秒，单个网页服务进程最多2路并行、同一会话库最多8条活动请求，同一会话一次回答一条；不会自动反复重试消耗额度。

计算失败会保留上次成功的盘面与目标日期；“重试”会重放刚才失败的操作，包括首次起盘、目标日期、研究主题、保存或导出。历法转换等待时可继续修改性别等资料；若同时改了日期，旧转换会被丢弃，请重新点选历法。保存中的按钮会显示“正在保存”，避免连点生成重复记录。

停止和重启：

```powershell
& 'scripts\stop-workbench.ps1'
& 'scripts\start-workbench.ps1' -Restart
```

停止网页不影响skill/CLI和已有资料。其它端口用 `-Port 8766`，启动和停止时须用同一端口。前台运行可用 `-Foreground`，Ctrl+C停止；不要同时用`-Foreground -Restart`。

## 5. 可直接复制的命令行用法

日常让Codex操作即可。需要自己调用时，在PowerShell当前窗口定义一个简写函数，之后任意目录都能用：

```powershell
$ziweiProject=(Get-Location).Path
function ziwei { & python -X utf8 (Join-Path $ziweiProject 'ziwei.py') @args }
ziwei --help
```

这个函数只在当前终端有效。`ask/search/chart`等命令输出JSON证据或计算包，交给当前Codex解释；`chat ask`会实际调用Codex CLI，自动返回研读答复并保存会话。

`ask --limit 6`控制知识、本命或运限提问返回的证据条数（1–20），不是解释长度。出生资料以stdin/JSON参数临时传入即可；需要长期复用时再明确保存命盘。

### 知识、目录与原文

```powershell
ziwei ask '三方四正是什么意思？' --limit 6
ziwei search '太阳 入庙 落陷' --namespace ziwei --limit 6
ziwei source TJ-462faa4-0396 --neighbors 2 --max-chars 10000
ziwei catalog
ziwei browse tianji-462faa4 --filter 紫微 --limit 20
ziwei browse wikisource-1 --filter 官禄 --offset 0 --limit 20
ziwei browse wikisource-1 --filter 官禄 --offset 20 --limit 20
```

领域可选`ziwei/yijing/fengshui/tieban/tianji/historical_ziwei/renji/all`；`tianji`为资料自己的领域标记，不表示自动并集全部天纪子领域。日常用具体领域，明确跨域再用all。人纪历史课程需显式选择renji，不混入紫微解读：

```powershell
ziwei ask '黄帝内经课程中怎样表述阴阳？只找历史原文' --namespace renji
ziwei search '阴阳' --namespace renji --mode lexical
```

人纪是历史课程资料，不能把检索排序当作治疗或用药依据。候选断语、存疑节选默认隔离；明确研究它们时才用`search ... --include-candidates --mode lexical`，不能当成已核通用规则。

### 出生与持续提问

现成的两个虚构输入文件在`examples/`。它们带固定`as_of`，用于重复验证；真实使用应替换全部出生资料，并删除`as_of`以用当天年龄，或显式填自己的参考日。

```powershell
ziwei city '南京'
ziwei chart --input-file examples\fictional-first.json
ziwei ask '结合条件研读事业' --input-file examples\fictional-first.json --topic career
ziwei personal save --kind profile --title '学习示例甲' --input-file examples\fictional-first.json
ziwei ask '继续研读财富' --profile '学习示例甲' --topic wealth
```

`--profile`接受精确唯一名称或ID；重名时用ID。主题：overview命格、personality性格、career事业、wealth财富、love感情、health疾厄、family兄弟、children子女、move迁移、friends人际、home田宅、spirit福德、parents父母。

输入格式示例：

```json
{
  "calendar": "solar",
  "year": 1990, "month": 1, "day": 1,
  "clock_hour": 8, "clock_minute": 30,
  "gender": "male",
  "longitude": 118.78,
  "timezone": "Asia/Shanghai"
}
```

`clock_hour:8`是钟表上午8点；`hour:8`是申时，辰时应为`hour:4`。不要混填。农历用`calendar:"lunar"`并说明`is_leap_month`。有IANA时区时不能再手工重复加UTC/DST修正；历史重复时刻需`fold:0/1`。具体计算口径见技能`references/usage.md`。

### 运限、比较与专项工具

```powershell
ziwei ask '研读流年事业' --profile '学习示例甲' --topic career --view yearly --year 2026 --method xiaoxian
ziwei ask '研读当日所在流月' --profile '学习示例甲' --topic career --view monthly --date 2026-11-06 --method taishui
ziwei period --profile '学习示例甲' --view decadal --decadal-index 2
ziwei ask '回到本命研读' --profile '学习示例甲' --view natal
ziwei flights --profile '学习示例甲'
ziwei compare --first examples\fictional-first.json --second examples\fictional-second.json --relation business
ziwei twins --profile '学习示例甲' --limit 5
ziwei time-candidates --input-file examples\fictional-first.json
ziwei liuren
```

`compare`也支持`--first-profile/--second-profile`，关系另有love/hierarchy/friendship。`period`返回完整计算事实，`period-context`或`ask`另带供Codex解释的精简证据包。大限序号从0起，界面年龄标注为虚岁。

### 旧案例与报告

```powershell
ziwei case 1990-01-01-4-male --topic career
ziwei case 1990-01-01-4-male --topic all --export
ziwei report --profile '学习示例甲' --mode sanhe
ziwei report --profile '学习示例甲' --hide-birth --analysis-file exports\本次研读.md
```

案例键为公历排盘日、时辰序号0–11、male/female，必须精确匹配。当前默认QS盘与v4旧XD2案例的口径差异会保留。

报告同时生成HTML、Markdown、SVG、PNG、PDF，返回绝对路径。`--mode`还可选feixing/sihua。**先让Codex把本次完整解释及引文写入Markdown，再用`--analysis-file`加入报告**；否则报告含盘面、存档和依据，不会自动带上整个聊天。`--hide-birth`隐藏显式生日/出生键，不等于加密或不可反推的匿名化。

### 本地记录和备份

```powershell
ziwei personal list --kind profile --query '学习' --offset 0 --limit 100
ziwei personal list --kind profile --offset 100 --limit 100
ziwei personal get --id 实际记录ID
ziwei personal backup
```

列表返回`total/offset/limit/has_more`。`personal get`返回全文。新建笔记/会话可将JSON文件交给`personal save --kind note/session --title ... --input-file ...`；更新使用相同`--id`且保持kind，完整data应保留，避免只为更名而误清正文。删除用`personal delete --id ...`，只处理自己确认的那一条。

`personal backup`使用SQLite在线备份接口，生成独立、一致的`.sqlite`文件并校验完整性，默认在exports，**不会覆盖已有文件**。可通过`--output-file <绝对路径.sqlite>`指定位置。它备份的是个人记录，不含模型、古籍、全量案例。恢复时让Codex先核验备份、当前数据库与目标位置，再执行明确的恢复任务；不要直接覆盖仍在使用的数据库。

## 6. 数据和模型放在哪，应该备份什么

| 目录 | 用途 |
|---|---|
| `models/Qwen3-Embedding-0.6B/<revision>` | 启用语义检索时下载的本地嵌入模型，约1.21GB，普通文件；不提交Git |
| `sources/` | 原始材料、原始存档、来源与版本核查依据 |
| `knowledge/` | 核心库、候选库、城市库 |
| `cases/` | 1950–2026全部77年本命案例数据库 |
| `indexes/`、`manifests/` | 向量索引、模型/资料版本、哈希与覆盖清单 |
| `runtime/personal.sqlite` | 命盘、收藏、笔记、会话等个人记录 |
| `exports/` | 报告、导出和个人记录备份，可能含私人资料 |
| `skill/ziwei-knowledge-search/` | 可安装的技能模板；绑定当前目录的信息只在本机生成 |

**整套系统备份应备份整个工作目录**，尤其原始资料、数据库、模型、个人记录和导出。不能只备份向量或只复制Git源代码。个人记录优先用`personal backup`取得一致副本。换机还需要系统Python/Node及依赖，详见`MAINTENANCE.zh-CN.md`。

语义安装会配置本地嵌入模型，关键词安装不下载它；两者都不需另下载聊天模型或网站API Key。完成安装后计算和本地检索可离线；Codex的语言解释使用当前Codex服务，打开视频/原站链接需要网络。网页8765与查询编码器8788是不同服务：后者仅语义检索按需启动，闲置5分钟退出，首次加载可等数秒。

## 7. 出问题先看这里

| 现象 | 处理 |
|---|---|
| 新对话没识别技能 | 输入完整`$ziwei-knowledge-search`或明确指向已安装SKILL.md；可新开对话重新发现技能；直接`ziwei.py`仍可用 |
| 网页打不开 | 执行启动脚本；8765被占时换端口，不要盲杀其它服务 |
| 查资料变成词检索 | 关键词安装本来就使用词检索；语义安装则查看`degraded_to_lexical`原因，执行doctor并读logs/query-encoder.log，不隐瞒意外降级 |
| 模型路径/配置刚改过 | 旧编码器会被配置契约拒绝；等闲置退出，或按维护文档核实进程归属后重启 |
| 原文与向量不匹配 | 在备份和停止查询后按维护文档重建知识与索引；错误行映射会被拒绝，不继续配错引文 |
| 名称查不到或重名 | 用personal list的query筛选并分页，取确切ID；名称须精确匹配 |
| 年龄或大限不是预期 | 核对as_of参考日、虚岁口径、目标日期/农历年，不直接改原文凑答案 |
| 没有对应旧案例 | 1950–2026之外不具备v4存档；仍可在引擎范围内排盘与查资料，不能替换邻近生日 |
| PDF/PNG异常 | doctor检查字体与报告依赖；本机已通过中文PDF/五格式导出，换机需另验证字体/Cairo |

```powershell
ziwei status
ziwei doctor
ziwei doctor --deep
```

doctor任何必需项失败会返回非零退出码，可用于脚本诊断。深检会读模型哈希和大数据库，耗时高于普通查询。

## 8. 当前完整性的边界

核心已收27,068条来源单元、27,090切片，7,717合格片段进混合检索；包括天纪4,881个去重引文组合、人纪19,294原行/888分组、四页古籍的1,818原段落，以及公开程序规则与方法资料。人纪为独立领域，不能把总条数当成全是紫微规则。

v4案例覆盖1950–2026全部77年、674,976种出生配置、8,774,688个主题文本；它们是生成式固定版本案例，**不是独立真人验证集或通用规则全集**。294,573条候选材料保留原案例出处，默认隔离。

尚缺作者闭源断语、完整私有评分/精解、网站小限子层、部分安星流派、可靠完整《紫微斗数全集》底本。已有古籍电子版也不是所有版本影印通校；课程整理不等于全套板书/逐字复听。检索与哈希通过说明数据可追溯、程序可复现，不说明每条传统论述已经证明为真。

继续扩充时，应先保留来源、版本、许可、定位、完整条件与不确定项，再建立可核规则；不能拿LLM补写文字充当古籍或原话。来源许可、非商用条件见`SOURCES.zh-CN.md`，功能和保留缺口见`README.md`及`docs/WEB.zh-CN.md`。
