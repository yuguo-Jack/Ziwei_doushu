import datetime,json,sqlite3,unicodedata
from zoneinfo import ZoneInfo
from .common import ROOT,read_json,normalize,ManagedConnection

def city_search(name,limit=30):
    if not isinstance(name,str) or not name.strip() or len(name)>100:raise ValueError('城市查询应为1–100字符。')
    term=normalize(name).casefold();matches=[]
    for province in read_json(ROOT/'sources/supplementary/engine-knowledge.json')['cities']:
        for city in province['cities']:
            if term in normalize(city['name']).casefold():matches.append({'province':province['name'],**city,'country':'CN','timezone':'Asia/Shanghai','source':'pinned project reference'})
    db=ROOT/'knowledge/geography.sqlite'
    if db.exists():
        with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True,factory=ManagedConnection) as conn:
            conn.row_factory=sqlite3.Row
            pattern='%'+term.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
            for row in conn.execute("SELECT id,name,country,latitude,longitude,timezone,population FROM cities WHERE aliases LIKE ? ESCAPE '!' ORDER BY population DESC LIMIT ?",(pattern,limit)):
                matches.append({**dict(row),'source':'GeoNames CC BY 4.0','source_url':f"https://www.geonames.org/{row['id']}/"})
    return {'query':name,'matches':matches[:limit],'returned':min(len(matches),limit),'note':'优先原项目国内参照点，再查全球城市；地名可能重名，请核对国家和坐标。IANA时区可用出生日期解析历史偏移。'}

def resolve_clock(payload):
    """Resolve a supplied IANA zone at the actual historical civil time, rejecting gaps/folds."""
    value=dict(payload);zone=value.pop('timezone',None);fold=value.pop('fold',None)
    if zone is None:
        if fold is not None:raise ValueError('fold需要timezone。')
        return value,None
    if 'clock_hour' not in value:raise ValueError('IANA时区需要钟表时间；已知时辰序号不再二次换算。')
    if value.get('calendar')=='lunar':raise ValueError('请先将农历转为公历后再解析历史时区。')
    if 'utc_offset_minutes' in value or 'dst_adjust_minutes' in value:raise ValueError('timezone与手工UTC/DST偏移不能同时设置。')
    if fold is not None and (type(fold) is not int or fold not in [0,1]):raise ValueError('fold只能为0或1。')
    naive=datetime.datetime(value['year'],value['month'],value['day'],value['clock_hour'],value.get('clock_minute',0))
    tz=ZoneInfo(zone);valid={}
    for f in [0,1]:
        aware=naive.replace(tzinfo=tz,fold=f);back=aware.astimezone(datetime.timezone.utc).astimezone(tz)
        if back.replace(tzinfo=None)==naive:valid[f]=aware
    if not valid:raise ValueError('该当地钟表时间因夏令时/时区跳变而不存在，请核对原始记录。')
    if len({x.utcoffset() for x in valid.values()})>1 and fold is None:raise ValueError('当地时间重复出现，需fold=0(第一次)或1(第二次)。')
    selected=valid.get(fold if fold is not None else 0)
    if selected is None:raise ValueError('所选fold对应的时刻不存在。')
    offset=selected.utcoffset().total_seconds()/60;dst=selected.dst().total_seconds()/60
    if not offset.is_integer() or not dst.is_integer():raise ValueError('该历史时区含秒级偏移；当前接口仅支持整分钟，请人工核实。')
    value['utc_offset_minutes']=int(offset-dst);value['dst_adjust_minutes']=int(dst)
    return value,{'timezone':zone,'fold':selected.fold,'actual_utc_offset_minutes':int(offset),'standard_utc_offset_minutes':int(offset-dst),'dst_adjust_minutes':int(dst),'source':'installed IANA tzdata; historical civil-time evidence may still require verification'}
