"""Append explicitly labeled dataset-derived candidate references to the canonical store."""
import sys,json,sqlite3,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import normalize,tokenize,sha,read_json,write_json,TOPICS

if __name__=='__main__':
    path=ROOT/'sources/supplementary/v4-reference-materials.jsonl';stage=ROOT/'knowledge/references.building.sqlite'
    if stage.exists():stage.unlink()
    conn=sqlite3.connect(stage);conn.executescript((ROOT/'design/knowledge-schema.sql').read_text(encoding='utf-8'))
    digest=hashlib.sha256(path.read_bytes()).hexdigest();sid='v4-reference-sections'
    conn.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?,?,?)',(sid,'dataset_derived_candidate','https://github.com/Renhuai123/ziwei-doushu/releases/tag/v4.0-13d','ca268829f7a9',digest,str(path.relative_to(ROOT)),json.dumps({'declared':'CC-BY-4.0','quotation_exception':'Ni Haixia course quotations retain separate rights'}),json.dumps({'extraction':'all 77 years, four reference sections, exact content deduplication'})))
    count=0;chunks=0
    for line in path.read_text(encoding='utf-8').splitlines():
        row=json.loads(line);id='V4REF-'+row['hash'][:24]
        if conn.execute('SELECT 1 FROM source_units WHERE id=?',(id,)).fetchone():continue
        count+=1;text=row['text'];title='v4解读候选 / '+TOPICS[row['topic']]+' / '+row['section']
        loc={'examples':row['examples'],'section':row['section'],'topic':row['topic'],'occurrences':row['occurrences']}
        verification={'text_extracted_exactly':True,'source_cases_locatable':True,'semantic_rule_verified':False,'scope':'case-conditioned output; do not infer missing conditions'}
        notes='来自规则生成的案例输出，尚未核成通用规则；重复次数不代表独立证据数。'
        conn.execute('INSERT INTO source_units VALUES (?,?,?,?,?,?,?,?,?)',(id,sid,json.dumps(loc,ensure_ascii=False),text,normalize(text),sha(text),'ziwei',notes,json.dumps(verification)))
        qualifiers=[s.strip() for s in re.split(r'(?<=[。；\n])',text) if re.search(r'若|如|逢|遇|男命|女命|同宫|落陷|入庙|只有|必须|不宜',s)][:20]
        meta={'source_url':'https://github.com/Renhuai123/ziwei-doushu/releases/tag/v4.0-13d','conditions_verbatim':qualifiers,'conditions_status':'not fully established; see exact source case and declared profile','topic':row['topic'],'section':row['section'],'examples':row['examples']}
        # Keep candidates outside the default evidence/vector index, but permit explicit lexical lookup.
        pieces=[text[i:i+1200] for i in range(0,len(text),1200)]
        for i,piece in enumerate(pieces):
            conn.execute('INSERT INTO chunks(stable_id,source_unit_id,title,text,title_terms,body_terms,namespace,evidence_kind,eligible,content_sha256,metadata_json) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                (id+f':{i}',id,title,piece,tokenize(title),tokenize(piece),'ziwei','dataset_candidate',0,sha(piece),json.dumps(meta,ensure_ascii=False)));chunks+=1
        if count%1000==0:conn.commit()
    conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')");conn.commit()
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    units=conn.execute('SELECT count(*) FROM source_units').fetchone()[0];allchunks=conn.execute('SELECT count(*) FROM chunks').fetchone()[0]
    conn.close();stage.replace(ROOT/'knowledge/reference-materials.sqlite')
    stats=read_json(ROOT/'manifests/knowledge.json');stats['dataset_reference_units']=units
    stats['source_units_total']=stats['source_units']+units;stats['chunks_total']=stats['chunks']+allchunks
    stats['reference_database']='knowledge/reference-materials.sqlite';stats['candidate_policy']='dataset candidates available explicitly; separate database preserves default retrieval quality'
    write_json(ROOT/'manifests/knowledge.json',stats);print(json.dumps({'new_units':count,'new_chunks':chunks,'stats':stats},ensure_ascii=False,indent=2))
