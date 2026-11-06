import math,datetime,json,subprocess
from zoneinfo import ZoneInfo
import numpy as np
from .common import ROOT,read_json
from .engine import chart
from .geography import city_search

def location_windows(calculated,cities):
    """Minute-resolution inverse windows; same chart date/branch under the explicit policy."""
    birth=calculated['normalized_birth'];date=datetime.date(birth['year'],birth['month'],birth['day']);target_branch=birth['hour']
    late=calculated['calculation_profile']['late_zi'];result=[]
    for city in cities[:8]:
        tz=ZoneInfo(city['timezone']);points=[]
        for delta in [-1,0,1]:
            day=date+datetime.timedelta(days=delta)
            for minute in range(1440):
                naive=datetime.datetime.combine(day,datetime.time())+datetime.timedelta(minutes=minute)
                aware=naive.replace(tzinfo=tz);back=aware.astimezone(datetime.timezone.utc).astimezone(tz)
                if back.replace(tzinfo=None)!=naive:continue
                offset=aware.utcoffset().total_seconds()/60;dst=aware.dst().total_seconds()/60
                standard=naive-datetime.timedelta(minutes=dst)
                days=366 if (standard.year%4==0 and (standard.year%100!=0 or standard.year%400==0)) else 365
                fractional=standard.hour+standard.minute/60
                gamma=2*math.pi/days*(standard.timetuple().tm_yday-1+(fractional-12)/24)
                eot=229.18*(.000075+.001868*math.cos(gamma)-.032077*math.sin(gamma)-.014615*math.cos(2*gamma)-.040849*math.sin(2*gamma))
                raw=minute+4*city['longitude']-offset+eot
                # Match engine rounding to the nearest second, then its date/late-Zi policy.
                total=math.floor(raw*60+.5);shift=total//86400;seconds=total%86400
                branch=0 if seconds>=82800 or seconds<3600 else (seconds-3600)//7200+1
                chartday=day+datetime.timedelta(days=shift+(1 if branch==0 and seconds>=82800 and late=='next-day' else 0))
                if chartday==date and branch==target_branch:points.append(naive)
        windows=[]
        for point in points:
            end=point+datetime.timedelta(minutes=1)
            if windows and windows[-1]['end_exclusive']==point.isoformat(timespec='minutes'):windows[-1]['end_exclusive']=end.isoformat(timespec='minutes')
            else:windows.append({'start':point.isoformat(timespec='minutes'),'end_exclusive':end.isoformat(timespec='minutes')})
        result.append({'name':city['name'],'country':city.get('country'),'longitude':city['longitude'],'timezone':city['timezone'],'windows':windows})
    return {'locations':result,'resolution':'one civil clock minute; ordinary fold=0 windows; repeated DST hour alternatives need explicit verification','method':'same longitude+NOAA equation-of-time, date and late-Zi policy as chart adapter; not real birth records'}

def twins(payload,limit=10):
    if not 1<=limit<=20:raise ValueError('limit范围1–20。')
    if not (ROOT/'manifests/twins.json').is_file():raise ValueError('同盘索引尚未安装，请按安装说明启用完整资料。')
    calculated=chart(payload)
    if calculated['calculation_profile']['leap_month']!='split':raise ValueError('全库主星索引采用split闰月口径；不会静默套用到其它口径。')
    meta=read_json(ROOT/'manifests/twins.json');folder=ROOT/'indexes/twins-major-split-v1'
    features=np.load(folder/'features.npy',mmap_mode='r',allow_pickle=False);dates=np.load(folder/'dates.npy',mmap_mode='r',allow_pickle=False)
    c=calculated['chart'];target=np.array([c['mingGongBranch'],c['shenGongBranch'],*[next(p['branch'] for p in c['palaces'] if any(s['name']==name and s['type']=='major' for s in p['stars'])) for name in meta['features'][2:]]],dtype='uint8')
    scores=np.sum(features==target,axis=1,dtype=np.int16);b=calculated['normalized_birth'];own=np.all(dates==[b['year'],b['month'],b['day'],b['hour']],axis=1)
    candidates=dates[(scores==16)&~own].tolist()
    command=['node','--import','./node_modules/tsx/dist/loader.mjs','../tools/verify_twins.ts']
    verified=subprocess.run(command,input=json.dumps({'birth':b,'profile':calculated['calculation_profile'],'candidates':candidates}),encoding='utf-8',text=True,capture_output=True,cwd=ROOT/'repo',timeout=90)
    exact=json.loads(verified.stdout)
    if verified.returncode or 'error' in exact:raise RuntimeError('完整同盘结构复核失败：'+exact.get('error',verified.stderr[-500:]))
    def rows(mask):
        ids=np.flatnonzero(mask&~own);ids=ids[np.argsort(-scores[ids],kind='stable')][:limit]
        return [{'birth_key':f'{int(dates[i,0]):04}-{int(dates[i,1]):02}-{int(dates[i,2]):02}-{int(dates[i,3])}-{b["gender"]}',
            'matching_components':int(scores[i]),'total_components':16,'same_major_geometry':bool(scores[i]==16),'is_real_person_record':False} for i in ids]
    cities=[]
    for name in ['北京','Kuala Lumpur','London','New York','Sydney']:
        found=city_search(name)['matches'];city=next((x for x in found if x.get('timezone')),None)
        if city:cities.append(city)
    return {'query_birth_key':calculated['birth_key'],'profile':meta['profile'],'searched_birth_configurations':meta['chart_configurations_with_two_genders'],
        'indexed_date_branch_rows':int(len(dates)),'compared_configurations_for_selected_gender':int(len(dates)),
        'exact_major_geometry_other_configurations_same_gender':int(np.sum((scores==16)&~own)),
        'full_chart_verification':exact,'exact_full_chart_other_configurations_same_gender':len(exact['matches']),
        'same_year':rows(dates[:,0]==b['year']),'cross_year':rows(dates[:,0]!=b['year']),
        'regional_clock_windows':location_windows(calculated,cities),'population_estimate':None,
        'limitations':['These are synthetic birth configurations, never actual people.','16-component match is major-star geometry, not every minor star, four transformation or equal destiny.','No unsourced demographic population estimate is fabricated.']}
