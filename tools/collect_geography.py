"""Freeze the licensed GeoNames cities15000 source and build local city lookup."""
import hashlib,json,sqlite3,urllib.request,zipfile,datetime,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import normalize

if __name__=='__main__':
    folder=ROOT/'sources/geonames';folder.mkdir(parents=True,exist_ok=True)
    urls={name:'https://download.geonames.org/export/dump/'+name for name in ['cities15000.zip','readme.txt','countryInfo.txt']}
    sources=[]
    for name,url in urls.items():
        path=folder/name
        if not path.exists():
            with urllib.request.urlopen(url,timeout=60) as r:path.write_bytes(r.read())
        sources.append({'path':str(path.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    stage=ROOT/'knowledge/geography.building.sqlite'
    if stage.exists():stage.unlink()
    conn=sqlite3.connect(stage);conn.execute('CREATE TABLE cities(id INTEGER PRIMARY KEY,name TEXT,country TEXT,latitude REAL,longitude REAL,timezone TEXT,population INTEGER,aliases TEXT)')
    with zipfile.ZipFile(folder/'cities15000.zip') as z:
        assert z.testzip() is None
        for line in z.read('cities15000.txt').decode('utf-8').splitlines():
            v=line.split('\t');assert len(v)==19
            aliases=normalize('|'.join([v[1],v[2],v[3]])).casefold()
            conn.execute('INSERT INTO cities VALUES(?,?,?,?,?,?,?,?)',(int(v[0]),v[1],v[8],float(v[4]),float(v[5]),v[17],int(v[14]),aliases))
    conn.execute('CREATE INDEX cities_by_country ON cities(country)');conn.commit()
    count=conn.execute('SELECT count(*) FROM cities').fetchone()[0];countries=conn.execute('SELECT count(DISTINCT country) FROM cities').fetchone()[0]
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';conn.close();stage.replace(ROOT/'knowledge/geography.sqlite')
    report={'source':'GeoNames cities15000','license':'CC BY 4.0','built_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot_lock':'config/source-assets.lock.json','cities':count,'countries_with_cities':countries,'sources':sources,'scope':'cities over 15000 population or capitals; not every settlement; timezone values are IANA IDs'}
    (ROOT/'manifests/geography.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
