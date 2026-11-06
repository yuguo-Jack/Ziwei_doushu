"""Collect complete public Wikisource page ranges with stable revision citations."""
import hashlib,json,re,time,urllib.parse,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
TITLES=['紫微斗數全書/卷一','紫微斗數全書/卷二','紫微斗數全書/卷三','紫微斗數']

def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'ZiweiLocalKnowledge/1.0 (personal source-referenced study)'})
    with urllib.request.urlopen(req,timeout=60) as r:return r.read()

def collect(title,index):
    base='https://zh.wikisource.org/wiki/'+urllib.parse.quote(title,safe='/')
    data=fetch(base);soup=BeautifulSoup(data,'html.parser')
    permanent=soup.select_one('#t-permalink a')
    permanent_url=urllib.parse.urljoin(base,permanent['href']) if permanent else base
    oldid=re.search(r'oldid=(\d+)',permanent_url)
    if oldid:
        data=fetch(permanent_url);soup=BeautifulSoup(data,'html.parser')
    content=soup.select_one('.mw-parser-output')
    if content is None:raise RuntimeError('No article body: '+title)
    for node in content.select('.toc,.mw-editsection,.noprint,.navbox,.sistersitebox,.ws-noexport,.licenseContainer,.metadata'):
        node.decompose()
    headings=[];paragraphs=[]
    for node in content.find_all(['h2','h3','h4','h5','p','li','dd','pre','tr']):
        if node.find_parent(['p','li','dd','pre','tr']):continue
        text=node.get_text(' ',strip=True)
        if not text:continue
        if node.name.startswith('h'):
            headings.append({'level':int(node.name[1]),'text':text,'anchor':node.get('id') or (node.find(id=True).get('id') if node.find(id=True) else '')});continue
        if len(text)<5:continue
        if '此作品在全世界' in text or text.startswith('作者：'):continue
        paragraphs.append({'ordinal':len(paragraphs)+1,'heading':headings[-1]['text'] if headings else title,
            'anchor':headings[-1]['anchor'] if headings else '', 'text':text})
    assert sum(len(x['text']) for x in paragraphs)>3000,(title,'incomplete content')
    name=f'wikisource-{index}'
    (ROOT/f'sources/classics/{name}.html').write_bytes(data)
    result={'id':name,'title':title,'canonical_url':base,'revision':oldid.group(1) if oldid else 'unresolved',
        'permanent_url':permanent_url,'sha256':hashlib.sha256(data).hexdigest(),
        'edition_note':'Wikisource electronic transcription; full page range preserved; not independently collated against all printed editions',
        'license':'public-domain ancient work; preserve Wikisource attribution and applicable transcription terms',
        'namespace':'ziwei' if title!='紫微斗數' else 'historical_ziwei',
        'paragraphs':paragraphs,'headings':headings,'chars':sum(len(x['text']) for x in paragraphs)}
    (ROOT/f'sources/classics/{name}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return {k:v for k,v in result.items() if k not in ['paragraphs','headings']}

if __name__=='__main__':
    results=[]
    for i,title in enumerate(TITLES,1):
        result=collect(title,i);results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True);time.sleep(.5)
    (ROOT/'manifests/classics.json').write_text(json.dumps({'pages':results,'complete_page_ranges':True,
        'gaps':[{'title':'紫微斗數全集','reason':'No independently verified complete open electronic edition collected; repository excerpts remain isolated and are not presented as a full original.'}]},ensure_ascii=False,indent=2),encoding='utf-8')
