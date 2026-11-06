"""Chinese, user-facing views. The original corpus and provenance remain unchanged."""
import re

KINDS={'adapter_code':'排盘方法说明','project_guide':'排盘方法说明','code_rule':'格局判定方法','source_code':'格局判定方法',
 'course_quote':'课程引文','course_quotes':'课程引文','course_quote_group':'课程引文',
 'historical_medical_course_quotes':'历史医籍课程','classic_transcription':'古籍原文',
 'compiled_secondary':'整理资料','quarantined_excerpt':'待核节选','unverified_curated_excerpt':'待核节选','dataset_candidate':'旧版案例节选','archived_case':'旧版本命案例'}
METHODS={
 'GUIDE-twelve':'命盘有十二个宫位。研读分成十三个主题，是因为命格总览与性格等主题可以共同参照命宫，并不是多出一个实体宫位。',
 'GUIDE-leap':'闰月有不同归属方法，包括月中分界、归下月、归前月和保留本月闰月标识。当前默认月中分界。换用方法后应重新排盘，不能把另一种口径的旧解读直接当作完全相同的结果。',
 'GUIDE-age':'这里采用农历年差加一的虚岁，并明确保留年龄参考日。公历年初的生日可能仍属于上一农历年，大限也按同一虚岁口径定位。虚岁与周岁不可混用。',
 'GUIDE-school-variants':'魁钺提供全书两表、钟义明表与网络表；截空提供正副双星、单星与占验表。旬空和副旬仍按基准盘计算。其他尚未核实实现的安星流派，不能当作已经生效。',
 'GUIDE-flights':'宫干四化会列出各宫天干所化星曜的实际落宫、本宫自化及对宫关系。几何联系本身不等于某件事一定发生；庚年四化采用哪张表，也需要明确保留。',
 'GUIDE-twins':'同盘先比较命宫、身宫和十四主星位置，再逐盘核对宫干、完整星曜、亮度、四化、五行局与大限等结构。主星相同与完整盘面相同是两种不同结果。这些配置不是实际真人档案，同盘也不表示经历相同。',
 'GUIDE-liuren':'小六壬按大安、留连、速喜、赤口、小吉、空亡六宫顺序起数：月从大安起，日从月落点起，时从日落点起，均含起点计数。子时计一，亥时计十二；闰月取本月数，二十三时不自动换日。它是一种传统文化算法，不能保证事件结局。',
 'GUIDE-borrow':'本宫没有十四主星时，可以参考对宫的主星来研读，但这些星仍然实际位于对宫。借星不等于星曜移动，也不等于本宫真的有两颗主星。同宫、庙陷、四化及煞曜等条件，仍需按实际盘面逐项核对。',
 'GUIDE-sanfang':'三方四正包含本宫、与本宫相隔四个和八个地支位置的两宫，以及正对面的宫。四个宫位一起看，用来核对相关星曜与相互关系。',
 'GUIDE-paipan':'排盘把出生日期、时刻、地点和选用的历法口径换算成十二宫及星曜位置。星位由程序计算；怎样理解这些位置，需要结合原典、适用条件与具体问题研读。',
 'GUIDE-time':'钟表时间与用于排盘的时辰不一定相同。出生地经度、当日时区、夏令时及均时差，都可能影响换算；已经明确提供时辰时，不再重复换算钟表时间。',
 'GUIDE-period':'本命、十年大限与流年、流月、流日、流时属于不同层次。研读时要保留目标日期与采用的体系，不能把旧版本命解读改称为当期运势。当前流月、流日与流时采用太岁体系。',
 'GUIDE-versions':'不同排盘口径和流派可能使用不同的星曜亮度表、闰月或换日规则。旧版存档和当前排盘应分别核对，出生日期相同也不代表全部算法相同。',
 'GUIDE-invalid-sihua':'同一术语在不同整理资料中可能有误记或冲突。遇到与当前四化表不一致的断语，应先回查原文、流派和条件；存疑节选不作为默认依据。',
}

def source_title(title):
    text=str(title or '研读资料').replace('代码格局规则 / ','格局判定 · ').replace('代码格局规则','格局判定方法')
    return text

def location_label(locator):
    if not isinstance(locator,dict):return ''
    if isinstance(locator.get('seconds'),(int,float)):
        seconds=max(0,int(locator['seconds']));clock=f'{seconds//60:02d}:{seconds%60:02d}'
        if seconds>=3600:clock=f'{seconds//3600}:{seconds%3600//60:02d}:{seconds%60:02d}'
        return (f'第{locator["part"]}段 · ' if locator.get('part') else '')+clock
    if locator.get('paragraph') is not None:return f'原文第{locator["paragraph"]}段'
    return ''

def source_view(source):
    kind=source.get('artifact_kind',source.get('kind',''))
    technical=kind in ['source_code','adapter_code','code_rule','project_guide'] or source.get('id','').startswith(('CODE-','GUIDE-'))
    text=source.get('text','')
    if technical:
        text=METHODS.get(source.get('id'))
        if not text:
            text='这是一条排盘程序的判定依据，用于核对所选格局或计算方法。它与古籍原文、课程观点分开保存，不应把程序识别结果直接等同于必然发生的事情。可打开原始出处核对具体条件，也可以让问答研读结合当前命盘解释。'
    notes=source.get('notes','') or ''
    chinese_notes=notes if re.search(r'[\u3400-\u9fff]',notes) and not re.search(r'\b(?:isEmpty|borrowedStars|return|function|sha256)\b',notes) else ''
    return {'title':source_title(source.get('title')),'category':KINDS.get(kind,'研读资料'),
      'text':text,'is_method':technical,'location':location_label(source.get('locator')),
      'conditions_note':'方法适用于相应的实际盘面，需逐项核对条件。' if technical else '请结合原文上下文、宫位与星曜关系核对适用条件；没有列出的条件不代表无条件成立。',
      'notes':chinese_notes,'html':markdown_html(text) if kind=='archived_case' else ''}

def markdown_html(text):
    from markdown_it import MarkdownIt
    parser=MarkdownIt('commonmark',{'html':False,'breaks':True}).enable('table').disable('image')
    original=parser.renderer.rules.get('link_open')
    def link(tokens,idx,options,env):
        tokens[idx].attrSet('target','_blank');tokens[idx].attrSet('rel','noreferrer noopener')
        return original(tokens,idx,options,env) if original else parser.renderer.renderToken(tokens,idx,options,env)
    parser.renderer.rules['link_open']=link
    return parser.render(text)
