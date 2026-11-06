---
name: "紫微 · 研习 — 玄金观星台"
description: "深墨承盘，古金定位，青玉联读的本地紫微研习界面。"
colors:
  ground: "#090f13"
  surface: "#111a20"
  raised: "#172329"
  field: "#0d151a"
  soft: "#1c292d"
  ink: "#eeeae0"
  muted: "#acb5b0"
  faint: "#919e98"
  line: "#2b383b"
  control: "#596762"
  accent: "#d5b77b"
  accent-strong: "#e5cb94"
  accent-pale: "#29271e"
  jade: "#93bbac"
  jade-pale: "#1b302c"
  focus: "#e6c78d"
  error: "#f0a39b"
  sidebar: "#0b1217"
  chart-cell: "#121e24"
  chart-related: "#172e2e"
  chart-selected: "#303126"
  day-ground: "#e9ede8"
  day-surface: "#f9faf5"
  day-raised: "#fffef8"
  day-field: "#f0f3ec"
  day-soft: "#e4eae1"
  day-ink: "#23362e"
  day-muted: "#53665a"
  day-faint: "#607165"
  day-line: "#cbd5c9"
  day-control: "#758371"
  day-accent: "#795d2c"
  day-accent-strong: "#60461d"
  day-accent-pale: "#eee5d0"
  day-jade: "#346758"
  day-jade-pale: "#e2ece2"
  day-focus: "#806027"
  day-error: "#a13c36"
  day-sidebar: "#e2e8df"
  day-chart-cell: "#f2f5ed"
  day-chart-related: "#e2ede3"
  day-chart-selected: "#eee6d1"
typography:
  display:
    fontFamily: "ZiweiDisplay, 'Noto Serif SC', 'Songti SC', serif"
    fontSize: "36px"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "0.04em"
  headline:
    fontFamily: "ZiweiDisplay, 'Noto Serif SC', 'Songti SC', serif"
    fontSize: "19px"
    fontWeight: 500
    lineHeight: 1.5
  title:
    fontFamily: "ZiweiDisplay, 'Noto Serif SC', 'Songti SC', serif"
    fontSize: "18px"
    fontWeight: 500
    lineHeight: 1.5
  collection-title:
    fontFamily: "ZiweiDisplay, 'Noto Serif SC', 'Songti SC', serif"
    fontSize: "24px"
    fontWeight: 500
    lineHeight: 1.5
  body:
    fontFamily: "'Microsoft YaHei', 'PingFang SC', system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.7
  reading:
    fontFamily: "'Microsoft YaHei', 'PingFang SC', system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 2.05
  label:
    fontFamily: "'Microsoft YaHei', 'PingFang SC', system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.7
  metadata:
    fontFamily: "'Microsoft YaHei', 'PingFang SC', system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.7
rounded:
  spine: "2px"
  badge: "4px"
  field: "7px"
  button: "8px"
  navigation: "9px"
  palace: "10px"
  panel: "12px"
spacing:
  compact: "8px"
  control: "10px"
  small: "12px"
  inset-small: "14px"
  inset: "16px"
  grid: "18px"
  section: "20px"
  roomy: "24px"
  page: "28px"
  major: "40px"
components:
  celestial-mark:
    textColor: "{colors.accent}"
    size: "48px"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#111b1a"
    rounded: "{rounded.button}"
    padding: "8px 14px"
  button-primary-hover:
    backgroundColor: "{colors.accent-strong}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.button}"
    padding: "8px 14px"
  button-codex:
    backgroundColor: "{colors.accent-pale}"
    textColor: "{colors.accent-strong}"
    rounded: "{rounded.button}"
    padding: "8px 14px"
  input-text:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "8px 10px"
  navigation-active:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.accent-strong}"
    rounded: "{rounded.navigation}"
    padding: "12px 10px"
  segment-active:
    backgroundColor: "{colors.accent-pale}"
    textColor: "{colors.accent-strong}"
    padding: "6px 11px"
  example-badge:
    textColor: "{colors.jade}"
    rounded: "{rounded.badge}"
    padding: "4px 7px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
  palace-selected:
    backgroundColor: "{colors.chart-selected}"
    textColor: "{colors.accent-strong}"
    rounded: "{rounded.palace}"
  palace-related:
    backgroundColor: "{colors.chart-related}"
    textColor: "{colors.ink}"
    rounded: "{rounded.palace}"
  source-entry:
    textColor: "{colors.muted}"
    padding: "13px 0"
  collection-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.accent-strong}"
    rounded: "{rounded.panel}"
    padding: "18px 20px"
---

# Design System: 紫微 · 研习 — 玄金观星台

## Overview

**Creative North Star: "玄金观星台"**

深墨夜空承托真实十二宫，古金标识当前选择与主要动作，青玉串联关联宫位、计算事实和资料线索。中文宋体提供名字与标题的仪式感；操作与长文保持清晰的中文无衬线。神秘与精致来自克制的细线环轨、稀疏星光和有秩序的目录，不来自虚构星位、金属贴图或遮挡内容的装饰。

这是本地研习工作界面。命盘、原文、适用条件和 Codex 问答入口各有清楚身份；五个目的地共享相同导航、标题、控件和金玉状态。用户已确认替换旧白底后台工具风格。配套日景沿用相同角色，以浅青玉底和墨绿文字支持阅读；原始白底导出独立于屏幕主题。

**Key Characteristics:**
- 深墨与不透明工作面分层，细线界定面板。
- 古金指向当前选择，青玉指向关联与依据。
- 自托管中文展示字体与清晰无衬线分工。
- 方形十二宫包围圆形星轨，真实盘面始终是主体。
- 桌面并列研习，窄屏整盘概览、放大与逐宫全文并存。

本文件是 2026-11-06 的 shipped scan：入口为 `web/dist/index.html`；样式顺序为 `web/src/style.css` 基础层与最后加载的 `web/src/observatory.css`。本轮属于经用户确认的视觉世界替换，旧文档已存入 `design/archive/2026-11-06-before-redesign/`，不再作为当前样式约束。未有获批 image comp；Saville QUALITY BAR 图卡返回 403，不能据此宣称达到外部图卡标准，也不据 Ouranic 登录弹窗宣称超过其整站。

## Colors

夜景以暖白文字落在偏青的深墨上，古金和青玉分别承担明确状态；前置 tokens 为规范值。`day-*` 是同名角色在 `[data-theme=light]` 中的实际值，运行时切换原有 CSS 变量，不增加第二套组件语义。

### Primary

- **古金**（`accent`）：主动作、当前宫位描边、焦点附近的几何标记与链接。
- **明金**（`accent-strong`）：宋体主星、当前导航和强调标题；`accent-pale` 承托选中的分段按钮及 Codex 入口。
- 日景对应 `day-accent`、`day-accent-strong`、`day-accent-pale`，以褐金保持同一层级。

### Secondary

- **青玉**（`jade`）：三方四正描边、关联线、当前事实、坐标说明与示例身份。
- **玉影**（`jade-pale`）：范围说明与玉色资料标记的承托底。
- 日景对应 `day-jade` 与 `day-jade-pale`。

### Neutral

| Token | 实际职责 | 日景对应 |
| --- | --- | --- |
| `ground` / `sidebar` | 页面深墨场 / 固定导航所在底层 | `day-ground` / `day-sidebar` |
| `surface` / `raised` | 不透明面板 / 导航 hover 等局部升层 | `day-surface` / `day-raised` |
| `field` / `soft` | 输入与命盘承托 / hover 或辅助承托 | `day-field` / `day-soft` |
| `ink` / `muted` / `faint` | 正文 / 次要说明 / 元信息 | 同名 `day-*` |
| `line` / `control` | 面板细分隔 / 原生控件可辨边框 | 同名 `day-*` |
| `chart-cell` | 十二宫默认底面 | `day-chart-cell` |
| `chart-selected` / `chart-related` | 所选宫古金底 / 关联宫青玉底 | 同名 `day-*` |

`focus` 是独立的清楚金色焦点轮廓；`error` 用于真实错误与破坏性动作的 hover，不承担装饰。日景主按钮文字实际为 `#fffbed`，夜景默认值见 frontmatter；夜景 hover 受基础层规则影响改用 `surface`。它们是按钮局部配对，不是新的全局文字角色。

**The Gold Selects, Jade Relates Rule.** 古金表示当前选择和主要操作，青玉表示关联与可核对线索；关联色不得暗示尚未计算的关系或分数。

**The Theme Roles Rule.** 明暗切换替换角色值，保留主次、宫位状态和来源身份；日景不是恢复旧白底后台布局。

现有对比度记录覆盖两主题的 12 组指定 token 配对：文字配对至少 4.5:1，控件边框对字段底至少 3:1。该记录不等于每个屏幕元素均已审计。Sidecar 的八步色带为面板预览派生，未新增生产颜色。

## Typography

**Display Font:** 自托管 `ZiweiDisplay`，CSS 依次以 `Noto Serif SC`、`Songti SC`、serif 作缺字与加载失败 fallback。

**Body Font:** `Microsoft YaHei`、`PingFang SC`、system-ui、sans-serif。

**Character:** 展示声音来自实际加载的中文宋体文件，不来自 fallback 名称。`web/public/fonts/ziwei-serif.woff2` 是 Noto Serif SC 的重命名、500 字重静态 subset（139156 bytes）；同目录的 `provenance.json` 记录来源、SHA-256 与派生说明，`OFL.txt` 保留 SIL Open Font License 1.1。它用于站名、页标题、主星和原典标题；长段正文与控件使用无衬线。全局数字采用 tabular-nums。

### Hierarchy

| Role | 实际使用与响应 |
| --- | --- |
| `display` | 页主标题；桌面使用 frontmatter 值，≤760px 为（30px）。 |
| `headline` | 全局二级标题基准；面板标题改用 `title`。 |
| `title` | 主要面板标题；研读小标题桌面为（16px），手机为（18px）。 |
| `collection-title` | 资料书架标题；≤1350px 为（21px），≤760px 为（18px）。 |
| `body` | 操作与一般内容基准；≤760px 为（15px）。普通段落行高（1.9）。 |
| `reading` | 来源详情与原典段落；手机正文为（16px），来源详情行高（2），原典段落保留（2.05）。 |
| `label` | 表单标签；手机主字段为（14px），原生输入为（16px），避免缩放依赖。 |
| `metadata` | 状态、版本与目录辅助信息；不得替代可读正文。 |

来源正文保留换行、允许长 ID 和文字换行。原典 passage 的最大行宽为（70ch）；来源侧栏本身限制行长，未设置全站统一的正文 ch 宽度。命盘 SVG 按容器等比缩放；手机缩略盘字不作为正文阅读字号。

**The Two Voices Rule.** 宋体承担名字、标题和主星，无衬线承担操作、说明与长文；不要把系统 fallback 宣称为已加载的展示字体。

## Layout

桌面是命名侧栏与弹性内容区。基准侧栏（184px）、页面横向内边距（28px）、顶栏高度（68px）；主内容最大宽（1950px）。研究区用出生资料（250px）、弹性命盘、依据（300px）三列，列间距（18px），项目对齐顶部。面板内部主要使用（16–24px），小控件使用（8–14px）；这些是实际组合的间距步骤，不是统一倍数网格。

| 条件 | 当前实现 |
| --- | --- |
| ≥1750px | 侧栏（208px），横向内边距（36px）；研究区为（280px / minmax(580px, 1fr) / 340px）。 |
| ≤1350px 且仍为桌面 | 侧栏（160px）、横向内边距（20px）、列距（14px）；研究区（230px / 1fr / 280px）。 |
| ≤1190px 且 >1100px | 研究区改为（240px / 1fr），研读和来源跨列；双盘两表单并列、结果跨列。 |
| ≤1100px | 侧栏变为有图标和文字的五项底栏，高（76px + safe-area-inset-bottom）；内容留同高底部空间。顶栏（60px），页面横向内边距（24px），研究区按出生资料、命盘、依据纵向排列。 |
| ≤760px | 页面横向内边距（16px），顶栏（58px）；页标题与保存/导出图标动作同排，动作保留 aria-label 和 title。底栏目的地标签（11px）。书架仍为三列；正文区域与合盘逐项纵排。 |

基础层仍有两个有效的边界条件：≤1200px 提前使研读栏跨列；≥1700px 将命盘面板上限设为（850px）。它们是当前 cascade 的遗留事实，不升级为新增页面需要照搬的布局档位。以此文件复核现有界面时须同时读取两层 CSS。

≤1100px 的出生资料默认收起，标题和“虚构示例” badge 在 disclosure 外持续可见。展开后平板使用两列表单；手机除时间类型与时间字段外主要按单列阅读。初始示例标记随实际编辑或本地命盘回载撤销，不将示例身份错误附给用户数据。

窄屏命盘默认是适应容器的完整概览，末尾覆盖已撤销早先（680px）最小盘宽。只有点击“放大命盘”才设置局部（780px）最小宽度，由命盘区域内部滚动；“适应屏幕”可退回概览。所选宫摘要在盘下提供可读主星与“查看依据”；“逐宫文字”可展开全部十二宫星曜。手机概览隐藏中心生辰日期与命身主小字，放大后恢复；隐藏生辰的原有开关仍有效。

资料库以三项来源书架进入真实目录；下方桌面两列为检索与逐段阅读，≤760px 纵排。来源面板在研究页替换右侧研读栏；其他页以内容加（360px）来源栏显示，≤1190px 来源栏为（330px），≤1100px 转为文流。

**The Overview and Reading Rule.** 完整概览负责位置感；放大、选中宫摘要与全部逐宫文字负责阅读，任何一个入口都不替代其余入口。

## Elevation & Depth

主体通过不透明的深浅工作面、细边框和有节制的径向光场获得深度，常规面板不带投影。内容区有低透明青玉径向光场，命盘底有局部青玉光场；细金环轨留在十二宫中央空白，Canvas 星光位于界面后方且不接收指针事件。这里的轨道与星光是装饰，不是天文坐标或新的计算结果。

### Shadow Vocabulary

- **状态提示浮层**（`box-shadow: 0 8px 28px #0003`）：仅 toast 使用，以便与工作面分离。
- **分段选中标记**（`box-shadow: inset 0 -2px var(--accent)`）：选中分段底部的内描线，不是面板 elevation。

**The Opaque Work Surface Rule.** 阅读和输入落在不透明工作面；星光与环轨留在数据之外，不穿透正文承托层。

按钮状态过渡为（160ms，CSS 默认 ease），普通按钮 hover 上移（1px）、按下下移（1px）；分段、来源列表等行式动作停留原位。加载标记可用（30s linear infinite）缓慢旋转，命盘忙碌态以 opacity（0.55）反馈。星光可在顶栏显式停用；Canvas 在隐藏标签页及 prefers-reduced-motion 下停止循环。reduced-motion 同时关闭 CSS 动画、过渡和 smooth scroll。动效开关在手机最终实现中保持可见、至少（44px）触达。

## Shapes

主容器为细边框柔角矩形，宫格围成方形十二宫，中心使用圆与放射刻度。面板使用 `panel` 圆角；输入、按钮、导航和宫格分别使用自己的圆角 token，不扩展为全站胶囊。细线通常为（1px）；宫格默认描边（1.5px）、所选宫（2px）、键盘焦点宫（5px）。书架书脊为扁平目录记号：细框、左侧内线、竖排宋体；不冒充摄影或实体材质。自绘图标使用描边 SVG，常用（16–24px），以 currentColor 继承语义色。

分段控件外壳为（7px）圆角并裁切；基础层首尾按钮仍继承 `--radius` 的端角，文档不将其扩散为新的独立端角 token。正文链接保留可辨下划线偏移（5px），不以金色细线替代文字身份。

## Components

### Buttons

轻而清楚，实心古金保留给提交与计算。

- **Primary:** 通用最小高（40px）、字重（600）、内边距见 frontmatter；hover 转明金。出生提交桌面最小高（46px）、字号（14px），手机为（48px / 16px）。
- **Secondary:** 页头保存与导出采用面板底、细分隔边框，桌面最小高（42px / 13px）；手机为（44 × 44px）图标动作，仍有可访问名称。
- **Codex:** 古金边框、淡金底、明金文字；桌面最小高（46px / 13px），手机（48px / 15px）。它复制问题到 Codex，不伪装成独立网页 LLM。
- **Focus / disabled:** 键盘焦点为（2px）`focus` 实线，外偏移（4px）；disabled 不位移，opacity（0.55），使用原生 disabled 属性。

### Chips

状态是可验证身份，不是内容装饰。“虚构示例”使用青玉描边、透明底、`badge` 圆角，文字（11px / 1.4），内边距见 frontmatter；放在出生资料标题右侧，折叠时仍显示。没有通用 tag 云或虚构等级样式。

### Cards / Containers

面板以 `surface`、（1px）`line` 与 `panel` 圆角构成，不添加常规阴影。标题行桌面通常（18px 20px），内文通常（18px 20px 22px）；窄桌面收紧至（16px），手机按组件使用（18px）。资料书架是可点的整卡，书脊区分古金、青玉与石色资料域，数量来自来源目录。空态展示下一步操作，保持真实空记录，不填入虚构人名或历史。

### Inputs / Fields

原生 input、select 与 checkbox/radio 保留键盘和系统交互。标准字段为 `field` 底、（1px）`control` 边框、`field` 圆角，最小高（42px），手机通常（44px / 16px）。placeholder 用 `faint`；字段正文用 `ink`，说明用 `muted`。组合输入的连接端角与边框依实际组件覆盖，不套用统一独立输入外观。聚焦使用全局焦点轮廓，错误以实际错误文案和 `error` 色共同表达。

分段按钮默认 `field` 底、`muted` 文字、细分隔线；选中为淡金底、明金文字与（2px）底部内描线。它们保留 aria-pressed；原生性别单选仍以实际 checked 状态控制金色边框与底面。

### Navigation

桌面命名侧栏的五项入口使用线性图标、主标签与一行辅助说明；选中入口显示明金、面板底与细框，常规入口用次要文字，hover 以升层底和正文色反馈。≤1100px 转为固定底栏，保留五个可读标签；辅助说明和箭头收起，选中项顶部增加（金色 26 × 2px）短线。主题按钮显示可切换到的“日景 / 夜景”，状态与动效按钮留在顶栏。

### 十二宫与真实联动

原生 SVG 保留全部真实星曜；所选宫用古金描边与专属底，关联宫用青玉。选中或 hover 的地支按（b、b+4、b+8、b+6）mod 12 计算三方四正；三合实线与对宫虚线落在中央留白。hover 只预览关联，激活宫位才切换研究主题并请求对应依据；Enter 或 Space 可激活宫位，焦点留在真实宫组。线与星标不承担虚构结果。

默认完整盘面、局部放大、所选宫摘要和十二宫全文共用同一计算数据。原始 SVG 下载和 PNG 生成使用 `calculated.svg`；屏幕上的样式增强、中心星轨与关系覆盖层不写回导出。原始白底导出保持独立，切换夜景不会把阅读型导出改成深色图。

### Sources and Reading

当前事实用青玉文字的字段底容器承托；原文入口按细线目录排列，尾部使用 SVG 箭头。点击后来源面板显示标题、版本、原段 ID、真实 URL、适用条件、完整正文与邻近段落；长 ID 可换行。来源桌面 sticky（top 18px，max-height calc(100dvh - 36px)），窄屏进入文流。打开时聚焦关闭按钮，Escape 关闭并返回原入口。

合盘的方法资料按共同标题分组，最多五个条目各显示真实短摘录和原段 ID，各自仍能打开完整原文；“通用方法资料”身份不将其冒配给单个宫位。旧版案例、当前计算与 Codex 综合解释保持文字身份区别，不通过视觉制造闭源评分或未恢复的精解能力。

本轮证据边界：detector 单次结果为 `[]`；现有 browser-checks 记录 10 组通过，responsive-checks 在（390、768、1024、1280、1440、1536px）六档无根溢出。`finish-review.md` 提出的示例身份与合盘来源区分两项修正，在同名、同尺寸重拍后由 `finish-verdict.md` 判为 resolved / ship；该 verdict 只覆盖这两项修正，不扩大为所有表面均无问题。

## Do's and Don'ts

### Do:

- **Do** 用古金表示当前选择与主要动作，用青玉表示真实关联和可核对线索。
- **Do** 让自托管 ZiweiDisplay 承担标题与主星，让无衬线承担控件与长文，并保留字体许可与 provenance。
- **Do** 在手机保留完整盘概览、显式放大、所选宫摘要与全部逐宫文字。
- **Do** 让初始示例身份在折叠状态也可见，实际编辑和回载本地命盘后撤销该标记。
- **Do** 保留原段 ID、版本、条件、独立来源入口和键盘焦点返回。
- **Do** 同时维护日景、夜景、减少动态偏好与独立白底导出。

### Don't:

- **Don't** 将已被用户替换的白底后台工具风格重新作为屏幕工作界面的视觉约束。
- **Don't** 为氛围删减真实星曜，或把手机概览的小字当作唯一阅读方式。
- **Don't** 用装饰星光、轨道、资料数量或虚构分数冒充计算结果与证据。
- **Don't** 把 fallback 字体当作已加载的展示声音，或把旧案例混成当前盘面的事实。
- **Don't** 将屏幕主题写入原始白底导出，或把通用方法原文冒配到某个宫位。
- **Don't** 将局部修正的 ship 结论、不可见的外部质量图卡或单张竞品登录画面扩写为整站优越性认证。
