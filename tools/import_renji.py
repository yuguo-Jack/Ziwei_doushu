"""Import the explicitly separate historical medicine course; preserve every original line."""
import collections,hashlib,json,subprocess
from pathlib import Path

def add_renji(builder,root):
    folder=root/'sources/renji';path=folder/'data/entries.jsonl'
    if not path.exists():return
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=folder,text=True).strip()
    sid='renji-'+revision[:7]
    builder.source(sid,'historical_medical_course_quotes','https://github.com/Renhuai123/nihai-renji-corpus',revision,path,
        {'declared':'CC BY-NC-SA 4.0','original_course_rights':'Ni Haixia and heirs'},
        {'scope':'course-text study, not current clinical guidance','granularity':'raw caption lines plus explicitly identified retrieval groups'})
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    groups=collections.defaultdict(list);counts=collections.Counter()
    for i,row in enumerate(rows,1):
        id=f'RJ-{revision[:7]}-{i:05d}';h,m,s=map(int,row['t_hms'].split(':'));seconds=h*3600+m*60+s
        title='倪海厦《人纪》 / '+row['part_name']+' / '+row['h2']
        loc={'line':i,'bvid':row['bvid'],'part':row['part'],'ep':row['ep'],'section':row['section'],'seconds':seconds}
        url=f"https://www.bilibili.com/video/{row['bvid']}?p={row['part']}&t={seconds}"
        builder.add(id,sid,title,row['quote'],url,'course_quote_line','renji',loc,
            {'book':row['book'],'school':'Ni Haixia historical medicine course','quote_status':'source-caption text, not independently re-listened or modern clinical verification'},
            row.get('note','')+'；历史课程文字研习，不作为诊断、用药或针灸操作指引。',eligible=False)
        groups[(row['book'],row['part_name'],row['h2'],row['h3'],row['bvid'],row['part'],row['ep'],row['section'])].append((seconds,id,row['quote']))
        counts[row['part_name']]+=1
    aggregates=0
    for key,entries in groups.items():
        entries.sort();parts=[];size=0
        def add_group(parts):
            nonlocal aggregates
            if not parts:return
            text='\n'.join(x[2] for x in parts);id='RJG-'+revision[:7]+'-'+hashlib.sha256('|'.join(x[1] for x in parts).encode()).hexdigest()[:16]
            url=f'https://www.bilibili.com/video/{key[4]}?p={key[5]}&t={parts[0][0]}'
            builder.add(id,sid,'倪海厦《人纪》 / '+key[1]+' / '+key[2],text,url,'course_quote_group','renji',
                {'bvid':key[4],'part':key[5],'ep':key[6],'section':'RAG:'+str(key[7]),'seconds':parts[0][0],'last_seconds':parts[-1][0]},
                {'book':key[0],'school':'historical course study','member_quote_ids':[x[1] for x in parts],'quote_status':'explicit grouping of caption lines; no added prose'},
                '逐行字幕按同一语义段拼接；不能将零碎引文当成完整诊疗条件。')
            aggregates+=1
        for entry in entries:
            if size+len(entry[2])>900 and parts:add_group(parts);parts=[];size=0
            parts.append(entry);size+=len(entry[2])+1
        add_group(parts)
    assert len(rows)==19294
    report={'revision':revision,'source_id':sid,'raw_rows_preserved':len(rows),'retrieval_groups':aggregates,'by_book':dict(counts),
        'entry_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'namespace':'renji','default_ziwei_search_includes':False,
        'license':'CC BY-NC-SA 4.0','scope':'historical text study; neither a complete transcript nor validated clinical guidance'}
    (root/'manifests/renji.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
