"""Independent CLI image/PDF generation; no browser or chat model required."""
import html,os,re,unicodedata
from pathlib import Path

def report_font():
    configured=os.environ.get('ZIWEI_REPORT_FONT')
    if configured:
        path=Path(configured).expanduser()
        if not path.is_file():raise RuntimeError('ZIWEI_REPORT_FONT指定的中文字体不存在。')
        return path
    for name in ['C:/Windows/Fonts/msyh.ttc','/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc','/usr/share/fonts/truetype/arphic/uming.ttc']:
        if Path(name).is_file():return Path(name)
    raise RuntimeError('PDF需要可嵌入的TrueType中文字体；请设置ZIWEI_REPORT_FONT，参阅安装说明。')

def extra_formats(svg,markdown,folder,id):
    import cairosvg
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle
    from bs4 import BeautifulSoup,NavigableString
    from .reports import markdown_html
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    png=folder/(id+'.png');pdf=folder/(id+'.pdf')
    cairosvg.svg2png(bytestring=svg.encode('utf-8'),write_to=str(png),output_width=2400,output_height=2400)
    font=report_font()
    if 'ZiweiReport' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('ZiweiReport',str(font),subfontIndex=0))
        pdfmetrics.registerFontFamily('ZiweiReport',normal='ZiweiReport',bold='ZiweiReport',italic='ZiweiReport',boldItalic='ZiweiReport')
    glyphs=pdfmetrics.getFont('ZiweiReport').face.charWidths
    def printable(text):
        # The searchable Markdown retains source symbols; PDF must not silently print missing-glyph boxes.
        result=[]
        for char in text:
            if char in ['\ufe0f','\u200d']:continue
            if ord(char) not in glyphs and not char.isspace():
                char={'🟡':'[黄]','🟢':'[绿]','🔴':'[红]','🔵':'[蓝]','⚠':'[提示]','⚙':'[配置]'}.get(char,'·' if unicodedata.category(char)=='So' else '[U+%04X]'%ord(char))
            result.append(char)
        return ''.join(result)
    styles={
        'body':ParagraphStyle('body',fontName='ZiweiReport',fontSize=10.5,leading=18,spaceAfter=9,wordWrap='CJK',textColor=colors.HexColor('#252c31')),
        'h1':ParagraphStyle('h1',fontName='ZiweiReport',fontSize=21,leading=30,spaceAfter=18),
        'h2':ParagraphStyle('h2',fontName='ZiweiReport',fontSize=17,leading=25,spaceBefore=22,spaceAfter=14,keepWithNext=True),
        'h3':ParagraphStyle('h3',fontName='ZiweiReport',fontSize=12,leading=20,spaceBefore=12,spaceAfter=9,textColor=colors.HexColor('#a84036'),keepWithNext=True),
        'cell':ParagraphStyle('cell',fontName='ZiweiReport',fontSize=9,leading=15,wordWrap='CJK')}
    story=[];chart_added=False
    def inline(node):
        if isinstance(node,NavigableString):return html.escape(printable(str(node)))
        children=''.join(inline(c) for c in node.children)
        if node.name=='br':return '<br/>'
        if node.name in ['strong','b']:return '<b>'+children+'</b>'
        if node.name in ['em','i']:return '<i>'+children+'</i>'
        if node.name=='a' and node.get('href','').startswith(('https://','http://')):
            return '<a href="'+html.escape(node['href'],quote=True)+'" color="#a84036">'+children+'</a>'
        return children
    soup=BeautifulSoup(markdown_html(markdown),'html.parser')
    for node in soup.children:
        if isinstance(node,NavigableString):continue
        kind='h1' if node.name=='h1' else 'h2' if node.name=='h2' else 'h3' if node.name in ['h3','h4','h5','h6'] else 'body'
        if node.name=='h2' and not chart_added:
            story.extend([Image(str(png),width=475,height=475),PageBreak()]);chart_added=True
        if node.name=='table':
            rows=[[Paragraph(''.join(inline(c) for c in cell.children),styles['cell']) for cell in row.find_all(['td','th'],recursive=False)] for row in node.find_all('tr')]
            if not rows:continue
            columns=max(len(r) for r in rows)
            rows=[r+['']*(columns-len(r)) for r in rows]
            table=Table(rows,colWidths=[(A4[0]-100)/columns]*columns,repeatRows=1 if node.find('thead') else 0,hAlign='LEFT')
            table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.5,colors.HexColor('#d9dddf')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f6f7f7')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
            story.extend([table,Spacer(1,12)])
        elif node.name in ['ul','ol']:
            for i,item in enumerate(node.find_all('li',recursive=False),1):
                story.append(Paragraph((str(i)+'. ' if node.name=='ol' else '· ')+inline(item),styles['body']))
        elif node.name=='hr':story.append(Spacer(1,10))
        else:
            text=inline(node)
            if text.strip():story.append(Paragraph(text,styles[kind]))
    def footer(canvas,doc):
        canvas.setFont('ZiweiReport',8);canvas.setFillColor(colors.HexColor('#626c75'));canvas.drawString(50,26,'紫微研习 · 来源与适用条件分别核对');canvas.drawRightString(A4[0]-50,26,str(doc.page))
    SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=48,bottomMargin=45,title='紫微研习报告',author='Local Ziwei Study').build(story,onFirstPage=footer,onLaterPages=footer)
    return {'png_path':str(png),'pdf_path':str(pdf)}
