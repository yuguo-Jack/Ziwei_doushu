# 来源、条件与覆盖目录

本文件说明已收录的来源范围。逐条机器可读来源位于 `knowledge/*.sqlite` 的 `sources`、`source_units`、`chunks` 等表；命中 `evidence_id` 可用 `ziwei.py source ID` 回查。

| 来源 | 固定版本、范围与定位 | 使用状态 |
|---|---|---|
| [ziwei-doushu 源码](https://github.com/Renhuai123/ziwei-doushu/tree/a600484a49255039d0725f1ba9e11ca81a948f97) | 提交 a600484；41 个规则函数、主星/四化表、合盘整理资料；文件和代码行 | 程序实现可复核，描述和归因需另核；保留 MIT 许可 |
| [nihai-tianji-corpus](https://github.com/Renhuai123/nihai-tianji-corpus/tree/462faa4c70af40b8b87ad82ffa82a5823a485e94) | 提交 462faa4；全部 4,886 原始记录及字段说明、178 条勘误账本；引文按视频、分 P、秒数回查 | 4,881 个唯一来源组合；CC BY-NC-SA 4.0，代码许可与引文许可区分 |
| [nihai-renji-corpus](https://github.com/Renhuai123/nihai-renji-corpus/tree/fdafae1ea685756a92a59179fdfa2e6a01379100) | 固定fdafae1；六部课程19,294字幕原行完整保留，另按语义段拼成888检索组，组内原行ID可回查 | 独立renji域，CC BY-NC-SA 4.0；历史原文研习，不是已核现代临床依据 |
| [v4.0-13d 发布](https://github.com/Renhuai123/ziwei-doushu/releases/tag/v4.0-13d) | contentVersion ca268829f7a9；77 个年度归档、674,976 盘 × 13 主题；出生键、主题和文字哈希 | 规则生成的本命案例；发布数据声明 CC BY 4.0，倪师引文另循其许可；不等于原作者全部规则源码 |
| [《紫微斗數全書》卷一](https://zh.wikisource.org/w/index.php?title=%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%8D%B7%E4%B8%80&oldid=7913704) | oldid 7913704；完整该电子页，21,928 字，卷章/段落/网页锚点 | 电子文本原文；尚未与所有影印刻本通校 |
| [《紫微斗數全書》卷二](https://zh.wikisource.org/w/index.php?title=%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%8D%B7%E4%BA%8C&oldid=1963110) | oldid 1963110；完整该电子页，43,672 字 | 同上 |
| [《紫微斗數全書》卷三](https://zh.wikisource.org/w/index.php?title=%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%8D%B7%E4%B8%89&oldid=2268626) | oldid 2268626；完整该电子页，12,102 字 | 同上 |
| [《紫微斗數》](https://zh.wikisource.org/w/index.php?title=%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8&oldid=11135824) | oldid 11135824；31,555 字，《續道藏》所载系统 | 与当前体系分域为 historical_ziwei，显式选择；不当成《全集》 |
| 仓库“古籍”75 段节选 | 固定原仓库源码、段落 ID | 现代整理和古籍引文混杂，隔离为 quarantined_excerpt，不能称已核全本 |
| 本地工具说明 | `tools/chart_engine.ts` 及固定原引擎的规则、README、常量 | project_guide 是工具契约与解释，不能伪装古籍原话 |
| [GeoNames城市](https://download.geonames.org/export/dump/) | 2026-11-05城市/国家快照，34,204城市、244国家/地区，保留zip/readme/countryInfo哈希及GeoNames ID；时区按已安装IANA tzdata2026.1解析 | CC BY 4.0；cities15000或首府范围，不是所有村镇或对历史民用时间记录的独立认证 |

古籍原作年代久远，电子网页快照仍保留网站归属与适用条款；不要删除电子版本出处，或把现代注释按公版原文处理。课程出处链接会跳到原公开视频的时间点，查看需要网络。

四个古籍电子页合计1,818个原段落、109,257字；为检索切成1,833片。原段落数与切片数不可混称。人纪分组是原字幕的显式拼接，没有新增解释，source返回metadata.member_quote_ids以便逐行核对。源文含U+FFFD编码损伤的四个切片保留并退出默认索引，不能当完整逐字引文。

## 适用条件怎样保存

每条核心与候选资料保留原文、原文哈希、来源版本、定位、备注和 verification。条件字段保存从原文识别的条件句；没有识别到不代表无条件，`conditions_status` 会注明限制。常见维度包括宫位/星曜关系、同宫或借宫、庙陷、煞曜、性别、四化、运限和流派。

原生 41 个规则有实际谓词代码，由排盘检测器判定本盘是否触发。自然语言条件并未全部转成可执行谓词。`context` 中只有匹配的原生规则标为 detected_in_this_chart；文献片段仍要求逐句核对。代码中的文字归因没有被标为已校原典。

候选段落 V4REF 可追溯到若干具体例盘、主题和章节，并记录重复次数；重复是模板复用，不能作为多份独立证据。对这些候选不会声称已恢复闭源规则的完整前提。

## 已知冲突和缺口

- 《紫微斗數全集》完整可靠电子底本尚未收得。2026-11-05 对公开古籍站点补查仍未取得可独立核对的完整文本；这是本次采集状态，不是断言网络上不存在。
- “紫微化忌”整理节选与工程十干四化表不一致，已隔离；不能因为搜得到就判定成立。
- 当前默认 QS 与 v4 旧 XD2、私有引擎版本差异明确保存；旧文闰月等口径有未知项。
- 某些旧案例同时说“空宫借星”和“本宫双星同宫”。原文不修改，当前事实另列并警示措辞冲突。
- 不同古籍刻本、其它流派、未被公开整理的课程段落和全部动态运限，不能宣称全面覆盖。

覆盖数与来源哈希见 `manifests/knowledge.json`（本机构建后生成）、`manifests/classics.json`（本机构建后生成）、`manifests/v4-downloads.json`（本机构建后生成） 和 `manifests/cases.json`（本机构建后生成）。

## 网页视觉资源

“玄金观星台”的标志、星轨和背景星点为本项目自绘 SVG/canvas 几何，不表示真实天文观测位置，也未加入知识库原典统计。标题字体由本机已安装的 Noto Serif SC 按 500 字重静态化、裁切并改名为 Ziwei Display，正文仍有系统中文字体回退。字体依据 SIL Open Font License 1.1 使用；原始版权、许可证和派生文件 SHA-256 保存在 [fonts](web/public/fonts/provenance.json) 与同目录 OFL.txt，派生文件随源码分发；修改字体时需保留OFL和来源记录。发布文件随网页提供，不依赖外部字体 CDN。
