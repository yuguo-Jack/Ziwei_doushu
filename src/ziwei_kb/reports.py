import html,json,re,uuid
from .common import ROOT,TOPICS
from .engine import chart
from .cases import lookup
from .retrieval import search

POSITIONS={5:(0,0),6:(1,0),7:(2,0),8:(3,0),4:(0,1),9:(3,1),3:(0,2),10:(3,2),2:(0,3),1:(1,3),0:(2,3),11:(3,3)}
BRANCHES='子丑寅卯辰巳午未申酉戌亥'
def chart_svg(calculated,hide_birth=False,mode='sanhe',period=None):
    if mode not in ['sanhe','feixing','sihua']:raise ValueError('盘面模式不支持。')
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200" role="img" aria-label="紫微十二宫命盘">',
        '<rect width="1200" height="1200" fill="#fff"/>',
        '<style>text{font-family:"Microsoft YaHei","PingFang SC",sans-serif;fill:#252c31}.muted{fill:#626c75}.red{fill:#a84036}.major{font-size:34px;font-weight:600}.minor{font-size:24px}.label{font-size:27px;font-weight:600}.small{font-size:22px}.center-title{font-size:40px;font-weight:600}.center-date{font-size:31px}</style>']
    def text(x,y,value,klass='',anchor='start',size=None):
        style=f' style="font-size:{size}px"' if size else ''
        parts.append(f'<text x="{x}" y="{y}" class="{klass}" text-anchor="{anchor}"{style}>{html.escape(str(value))}</text>')
    c=calculated['chart']
    overlays={p['branch']:p.get('period_palace','') for p in (period or {}).get('selected',{}).get('palaces',[])}
    for p in c['palaces']:
        x,y=POSITIONS[p['branch']];x=x*290+20;y=y*290+20
        parts.append(f'<g data-branch="{p["branch"]}">')
        parts.append(f'<rect x="{x}" y="{y}" width="290" height="290" fill="{("#fcf4f2" if p.get("isMingGong") else "#fff")}" stroke="#d9dddf"/>')
        text(x+18,y+36,BRANCHES[p['branch']],'small muted')
        label=p['name']+(' / '+overlays.get(p['branch'],'') if overlays else '')
        text(x+272,y+36,label,'label',anchor='end',size=22 if overlays else None)
        major=[s for s in p['stars'] if s['type']=='major']
        for j,s in enumerate(major):
            suffix=(' '+s.get('brightnessRaw','')) if mode=='sanhe' else ''
            sh=s.get('siHua','');suffix+=' '+({'禄':'A','权':'B','科':'C','忌':'D'}.get(sh,sh) if mode=='sihua' else sh)
            text(x+18,y+84+j*39,s['name']+suffix,'major'+(' red' if sh else ''))
        if not major:
            text(x+18,y+84,'空宫','major muted');text(x+18,y+113,'借看：'+'、'.join(p.get('borrowedStars',[])),'minor muted')
        minor=[s['name']+('化'+s['siHua'] if s.get('siHua') else '') for s in p['stars'] if s['type']!='major']
        lines=[];line=[];length=0
        for name in minor:
            if line and length+len(name)>8:lines.append('  '.join(line));line=[];length=0
            line.append(name);length+=len(name)+1
        if line:lines.append('  '.join(line))
        start=150 if len(major)!=1 else 116;end=216 if mode=='feixing' else 246
        pitch=min(28,(end-start)/max(len(lines)-1,1));font=min(24,max(16,pitch))
        for j,line in enumerate(lines):text(x+18,y+start+j*pitch,line,'minor muted',size=font)
        if mode=='feixing':
            fs=next((q for q in calculated.get('flights',{}).get('palaces',[]) if q['branch']==p['branch']),None)
            if fs:
                labels=[t['kind']+t['star'] for t in fs['transforms']]
                text(x+18,y+240,'  '.join(labels[:2]),'small red')
                text(x+18,y+267,'  '.join(labels[2:]),'small red')
        elif p.get('daXianAge'):text(x+18,y+264,str(p['daXianAge'][0])+'–'+str(p['daXianAge'][1])+' 虚岁','small muted')
        parts.append('</g>')
    text(600,470,'紫微 · 研习','center-title',anchor='middle')
    text(600,520,'本地命盘与原典依据','small muted',anchor='middle')
    birth=calculated['normalized_birth']
    text(600,580,'生辰已隐藏' if hide_birth else f"{birth['year']}-{birth['month']:02}-{birth['day']:02} · {BRANCHES[birth['hour']]}时",'center-date',anchor='middle')
    if not hide_birth:text(600,619,'男' if birth['gender']=='male' else '女','small muted',anchor='middle')
    text(600,670,c['wuxingJuName']+' · 命主'+str(c.get('mingZhu',''))+' · 身主'+str(c.get('shenZhu','')),'small',anchor='middle')
    text(600,710,calculated['calculation_profile']['brightness']+' / '+calculated['calculation_profile']['leap_month'],'small muted',anchor='middle')
    if period:
        text(600,750,period['selected']['name']+' · '+period['target_date'],'small red',anchor='middle')
        text(600,785,'宫名：本命 / 本期','small muted',anchor='middle')
    parts.append('</svg>');return ''.join(parts)

def markdown_html(text):
    from markdown_it import MarkdownIt
    return MarkdownIt('commonmark',{'html':False,'breaks':True}).enable('table').render(text)

def export_report(payload,hide_birth=False,mode='sanhe',analysis_text=''):
    if not isinstance(analysis_text,str) or len(analysis_text)>100000:raise ValueError('综合研读文字最多100000字符。')
    calculated=chart(payload,'period' if payload.get('period') else 'chart');period=calculated.get('period')
    archive=lookup(calculated['birth_key'],'all',100000) if period is None else {'found':False}
    svg=chart_svg(calculated,hide_birth,mode,period=period)
    folder=ROOT/'exports';folder.mkdir(exist_ok=True);id='report-'+uuid.uuid4().hex[:12]
    source_note='旧版v4本命文字，亮度XD2，与当前QS/所选表不保证全部兼容；以下保留原文，不视为本次独立核定结论。'
    sections=[];md=['# 紫微研习报告','当前计算、旧版案例和文献摘录分别标注。']
    if not hide_birth:md.append('排盘键：'+calculated['birth_key'])
    else:md.append('生辰已隐藏。')
    md.extend(['排盘口径：'+calculated['calculation_profile']['brightness']+' / '+calculated['calculation_profile']['leap_month']+' / 晚子'+calculated['calculation_profile']['late_zi']+' / 庚年'+calculated['calculation_profile']['geng_year_sihua'],'参考日：'+calculated['calculation_profile']['as_of']])
    palace_for={'overview':'命','personality':'命','love':'夫妻','career':'官禄','wealth':'财帛','health':'疾厄','family':'兄弟','children':'子女','move':'迁移','friends':'仆役','home':'田宅','spirit':'福德','parents':'父母'}
    def scrub(text):
        if not hide_birth:return text
        b=calculated['normalized_birth']
        text=text.replace(calculated['birth_key'],'[生辰隐藏]')
        for pattern in [rf"{b['year']}[-/.年]\s*0?{b['month']}[-/.月]\s*0?{b['day']}日?",rf"{b['year']}年\s*{b['month']}月\s*{b['day']}日"]:text=re.sub(pattern,'[生辰隐藏]',text)
        return text
    if analysis_text:
        analysis_text=scrub(analysis_text);md.extend(['\n## 本次Codex综合研读','本次会话生成的综合解释；下列原典与旧版案例另行保存。',analysis_text])
        sections.append('<section><h2>本次Codex综合研读</h2><p class="note">本次会话生成的解释；与下列原文分开核对。</p>'+markdown_html(analysis_text)+'</section>')
    for topic,label in TOPICS.items():
        palace=next(p for p in calculated['chart']['palaces'] if p['name'].replace('宫','')==palace_for[topic])
        factual='本命'+palace['name']+'：'+('、'.join(s['name'] for s in palace['stars'] if s['type']=='major') or '无十四主星，借看对宫'+ '、'.join(palace.get('borrowedStars',[])))
        if period:
            current=next((p for p in period['selected']['palaces'] if p['period_palace'].replace('宫','')==palace_for[topic]),None)
            if current:
                actual='、'.join(s['name'] for s in current['physical_main_stars']) or '无十四主星，借看对宫'+'、'.join(current['borrowed_stars'])
                factual=period['selected']['name']+palace_for[topic]+'宫对应本命'+current['natal_palace']+'：'+actual
            else:factual=period['selected']['name']+'未生成本主题宫位。'
        evidence=search(label+' '+factual+' 适用条件',limit=3)
        text=archive.get('topics',{}).get(topic,{}).get('text','本主题无已发布的精确原文；请在Codex中结合本盘和来源进一步研读。')
        text=scrub(text)
        sections.append('<section><h2>'+html.escape(label)+'</h2><p class="fact">'+html.escape(factual)+'</p><h3>'+('v4旧版本命原文' if archive.get('found') else '资料状态')+'</h3>'+markdown_html(text))
        md.extend(['\n## '+label,factual,'### '+('v4旧版本命原文' if archive.get('found') else '资料状态'),text])
        sections.append('<details><summary>研读依据与条件</summary>')
        for hit in [h for h in evidence['hits'] if h['kind']!='code_rule']:
            content=scrub(hit['text']);url=hit['source_url']
            sections.append('<p><strong>'+html.escape(hit['title'])+'</strong></p>'+markdown_html(content))
            if url.startswith('https://'):sections.append('<p><a href="'+html.escape(url,quote=True)+'">原始出处</a></p>')
            sections.append('<p class="note">'+html.escape(hit.get('conditions_status') or '需逐项核对原文条件')+'</p>')
            md.extend(['### 研读依据：'+hit['title'],content,'出处：'+('[原始出处]('+url+')' if url.startswith('https://') else url)])
        sections.append('</details></section>')
    doc='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>紫微研习报告</title><style>body{font:16px/1.85 "Microsoft YaHei",sans-serif;color:#253039;max-width:940px;margin:40px auto;padding:0 24px}h1{font-size:30px}h2{border-bottom:1px solid #ddd;padding-bottom:8px}section{break-inside:auto;margin:48px 0}.note{color:#6f757d;font-size:13px}.fact{border-left:3px solid #a84036;padding-left:16px}svg{width:100%;height:auto}button{padding:10px 20px}summary{cursor:pointer}a{color:#a84036}@media print{button{display:none}body{margin:0;font-size:12px}details{display:block}details>*{display:block}svg{max-height:23cm}section{break-before:page}}</style><body><button onclick="window.print()">打印 / 另存 PDF</button><h1>紫微研习报告</h1>'''
    doc+='<p><a href="'+id+'.pdf" download>下载PDF</a> · <a href="'+id+'.png" download>下载命盘PNG</a> · <a href="'+id+'.md" download>Markdown</a> · <a href="'+id+'.svg" download>SVG</a></p>'
    doc+='<p class="note">'+html.escape(source_note if archive.get('found') else '当前计算与研读资料；无本期发布原文。')+'</p>'+svg+''.join(sections)+'</body></html>'
    doc=doc.replace('</style>','table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14px}th,td{border:1px solid #d9dddf;padding:8px;text-align:left;vertical-align:top}a,td,p{overflow-wrap:anywhere}pre{white-space:pre-wrap}blockquote{margin:20px 0;padding-left:16px;border-left:1px solid #b8bfc4}</style>')
    (folder/(id+'.html')).write_text(doc,encoding='utf-8');(folder/(id+'.md')).write_text('\n\n'.join(md),encoding='utf-8');(folder/(id+'.svg')).write_text(svg,encoding='utf-8')
    from .report_formats import extra_formats
    formats=extra_formats(svg,'\n\n'.join(md),folder,id)
    return {'html_path':str(folder/(id+'.html')),'markdown_path':str(folder/(id+'.md')),'svg_path':str(folder/(id+'.svg')),**formats,'file_stem':id,'hide_birth':hide_birth,'mode':mode,'topics':13,'usage':'CLI and web share HTML/Markdown/SVG/PNG/PDF export, including the selected chart mode and birth hiding.'}
