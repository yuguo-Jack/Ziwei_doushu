# 出生输入与确定性计算

直接入口：`python -X utf8 ziwei.py ...`，与技能启动脚本参数相同。所有输入命令支持`--input-file`、`--input-json`或`--stdin`；出生命令还支持`--profile ID`或精确唯一名称（四者互斥）。路径用绝对路径。UTF-8文件与stdin支持Windows BOM。

## 出生 JSON

虚构例子，未提供经度时不做真太阳时：

```json
{"year":1990,"month":1,"day":1,"clock_hour":8,"clock_minute":30,"gender":"male","longitude":118.78,"timezone":"Asia/Shanghai","brightness":"QS","leap_month":"split","late_zi":"next-day","geng_year_sihua":"GYWYT"}
```

- 公历默认`calendar:"solar"`，1900–2100。农历用`calendar:"lunar"`与`is_leap_month:true/false`，1900–2050；闰月必须真实存在，先转公历再做时区处理。
- 已知时辰：`{"year":1990,"month":1,"day":1,"hour":4,"gender":"male"}`。0子、1丑、2寅、3卯、4辰、5巳、6午、7未、8申、9酉、10戌、11亥。日期为已经确定的排盘日；不再二次做钟表/经度/时区换算。不能同时填`hour`和`clock_hour`。
- `timezone`为IANA名，自动解析该日期实际偏移；重复时刻需`fold:0/1`，不存在时刻拒绝。不能同时设置timezone和手工UTC/DST偏移。历史秒级偏移当前拒绝，应人工核对记录。
- 手工偏移：`utc_offset_minutes`是当时标准时区分钟数（默认480），`dst_adjust_minutes`为需从钟表读数扣除的夏令时分钟数（默认0）。有依据才设置，不能把含DST的总偏移再重复加DST。
- 亮度`brightness`：QS/XD1/XD2/ZZ；闰月`leap_month`：split/next-month/prev-month/origin-month。晚子`late_zi`：next-day/current-day/all-current/day-cur-time-next。庚年四化：GYWYT/GYWTY/GYWFT/GYWFX/GYWTX。魁钺`kuiyue_school`为qs1/qs2/zhong-yiming/network，截空`jiekong_school`为double/single/zhanyan（旬空、副旬维持基准）。其它网站安星流派开关尚未实现，不接受伪参数。
- `as_of:"2026-11-05"`固定当前虚岁/大限参考日，否则按香港当前日期。四柱的年/月柱按实际时刻转UTC+8交节，日/时柱按选定本地真太阳日和晚子规则；只有时辰时仍为中点近似。保留计算配置，不声称统一所有八字流派。
- `unknown_time:true`拒绝确定排盘。`time-candidates --input-file ...`明确逐一计算十二时辰，不指定真实值；此时输入日期仅为候选排盘日，不能自动解决经度导致的跨日。

主题：overview命格、personality性格、love感情、career事业、wealth财富、health健康、family兄弟、children子女、move迁移、friends人际、home田宅、spirit福德、parents父母。

## 运限与四化

```powershell
python -X utf8 ziwei.py period --input-file evaluations\birth-example.json --view yearly --year 2026 --method xiaoxian
python -X utf8 ziwei.py period-context --input-file evaluations\birth-example.json --view monthly --date 2026-11-05 --method taishui --question "研读流月事业的条件" --topic career
```

`--view`：natal/decadal/yearly/monthly/daily/hourly/age；`--date`目标公历日；`--year`目标农历流年；`--hour`目标时辰0–11；`--decadal-index`选择0起的大限。不要同时给相冲突的目标选择。流年可选xiaoxian/taishui；月/日/时只支持显式taishui，未取得网站小限子层和私有断语。

也可把`"period":{"view":"yearly","target_year":2026,"annual_method":"xiaoxian"}`嵌入出生JSON，供`ask/context/report`使用。`flights`返回每个宫干的四化星实际去向、自化、对宫标志；这些是表和位置事实，不自动等于事件判断。

`--date/--year/--decadal-index`互斥，显式命令行目标先清除JSON中的旧目标再应用；原始JSON也不能同时填多个目标。回到本命用`ask ... --view natal`，会清掉旧period，避免误带上一轮运限。只有运限参数却不提供出生资料的ask会明确报错，不把参数静默忽略。

## 小六壬与同盘

`liuren`不带输入使用香港当前年月日和钟表小时；显式输入可用公历/农历及hour或clock_hour。按月、日、时含起点计数，闰月用同一月数，23时不自动换民用日；不做真太阳时转换。

`twins --input-file ... --limit 10`返回同年/跨年主星几何匹配与五地钟表时窗。全库674,976种男女配置，特征由337,488个日期时辰共享；本次比较同一性别。第一阶段为命身宫及十四主星的16分量，split闰月口径；再对全部精确候选调用原生引擎，核对全部星曜、亮度、四化、宫干和大限结构，full_chart_verification返回结果。主星匹配与完整原生盘面匹配分列，均不是实际真人、人口估计或命运相同。时窗精度一分钟；DST重复小时只列fold0，需另核。

## 回查

`source TJ-462faa4-0396 --neighbors 2`返回同课程语义段相邻可用引文，不是完整逐字稿。`source CASE:v4.0-13d:1990-01-01-0-male:career`回查精确旧例。`case ... --topic all --export`的JSON可截断，但导出的Markdown保留13主题全文；区分当前QS与旧XD2。
