import argparse,json,sys
from pathlib import Path
from .common import ROOT,TOPICS,read_json,connect,installation

def profile_payload(id):
    from .library import profile_record
    return profile_record(id)['data']

def period_payload(payload,args):
    if not isinstance(payload,dict):raise ValueError('出生输入应为JSON对象。')
    if getattr(args,'action',None)=='ask' and args.view=='natal':
        if any(getattr(args,k,None) is not None for k in ['date','year','decadal_index','hour','method']):raise ValueError('本命追问无需运限参数；年龄参考日用出生JSON的as_of。')
        value=dict(payload);value.pop('period',None);return value
    raw=payload.get('period',{})
    if not isinstance(raw,dict):raise ValueError('period应为JSON对象。')
    request=dict(raw)
    if any(getattr(args,k,None) is not None for k in ['date','year','decadal_index']):
        for k in ['target_date','target_year','decadal_index']:request.pop(k,None)
    for k,v in {'view':args.view,'target_date':args.date,'target_year':args.year,'hour':args.hour,'decadal_index':args.decadal_index,'annual_method':args.method}.items():
        if v is not None:request[k]=v
    return {**payload,'period':request} if request else dict(payload)

def status():
    files={'knowledge':'manifests/knowledge.json','cases':'manifests/cases.json','model':'manifests/embedding-model.json','index':'indexes/current.json','evaluation':'evaluations/results.json'};result={'workspace':str(ROOT),'installation':installation()}
    for name,file in files.items():
        path=ROOT/file
        if not path.exists():result[name]={'available':False};continue
        data=read_json(path)
        if name in ['cases','model']:data={k:v for k,v in data.items() if k!='files'}
        if name=='evaluation':data={k:v for k,v in data.items() if k!='results'}
        if name=='cases':data.update({'minimum_birth_date':'1950-01-01','maximum_birth_date':'2026-12-31','scope':'natal, fixed v4 archive profiles'})
        result[name]=data
    return result

def main():
    p=argparse.ArgumentParser(description='Ziwei local source-referenced knowledge tools');sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('status');sub.add_parser('coverage')
    s=sub.add_parser('city');s.add_argument('name')
    s=sub.add_parser('search');s.add_argument('query');s.add_argument('--limit',type=int,default=6);s.add_argument('--namespace',choices=['ziwei','yijing','fengshui','tieban','tianji','historical_ziwei','renji','all']);s.add_argument('--mode',choices=['hybrid','lexical'],default='hybrid');s.add_argument('--include-candidates',action='store_true')
    s=sub.add_parser('source');s.add_argument('id');s.add_argument('--max-chars',type=int,default=6000);s.add_argument('--neighbors',type=int,default=2)
    s=sub.add_parser('case');s.add_argument('key');s.add_argument('--topic',choices=[*TOPICS,'all'],default='overview');s.add_argument('--max-chars',type=int,default=5000);s.add_argument('--offset',type=int,default=0);s.add_argument('--export',action='store_true')
    for action in ['chart','context','calendar','period','period-context','liuren','flights','twins','report','ask','time-candidates']:
        s=sub.add_parser(action);g=s.add_mutually_exclusive_group(required=action not in ['liuren','ask']);g.add_argument('--input-file');g.add_argument('--input-json');g.add_argument('--stdin',action='store_true')
        if action not in ['calendar','liuren']:g.add_argument('--profile')
        if action=='ask':
            s.add_argument('question');s.add_argument('--topic',choices=TOPICS,default='overview');s.add_argument('--limit',type=int,default=6)
            s.add_argument('--namespace',choices=['ziwei','yijing','fengshui','tieban','tianji','historical_ziwei','renji','all']);s.add_argument('--mode',choices=['hybrid','lexical'],default='hybrid')
        if action in ['context','period-context']:s.add_argument('--question',required=True);s.add_argument('--topic',choices=TOPICS,default='overview')
        if action in ['period','period-context','ask']:
            s.add_argument('--view',choices=['natal','decadal','yearly','monthly','daily','hourly','age']);target=s.add_mutually_exclusive_group();target.add_argument('--date');target.add_argument('--year',type=int);target.add_argument('--decadal-index',type=int);s.add_argument('--hour',type=int);s.add_argument('--method',choices=['xiaoxian','taishui'])
        if action=='twins':s.add_argument('--limit',type=int,default=10)
        if action=='report':s.add_argument('--hide-birth',action='store_true');s.add_argument('--mode',choices=['sanhe','feixing','sihua'],default='sanhe');s.add_argument('--analysis-file')
    s=sub.add_parser('compare');g=s.add_mutually_exclusive_group(required=True);g.add_argument('--first');g.add_argument('--first-profile');g=s.add_mutually_exclusive_group(required=True);g.add_argument('--second');g.add_argument('--second-profile');s.add_argument('--question',default='比较两人的相关宫位与适用条件');s.add_argument('--relation',choices=['love','business','hierarchy','friendship'],default='love')
    sub.add_parser('catalog')
    s=sub.add_parser('browse');s.add_argument('source_id');s.add_argument('--offset',type=int,default=0);s.add_argument('--limit',type=int,default=20);s.add_argument('--filter',default='')
    s=sub.add_parser('personal');s.add_argument('operation',choices=['list','get','save','delete','backup']);s.add_argument('--kind',choices=['profile','note','bookmark','session','liuren']);s.add_argument('--id');s.add_argument('--title');s.add_argument('--input-file');s.add_argument('--offset',type=int,default=0);s.add_argument('--limit',type=int,default=100);s.add_argument('--query',default='');s.add_argument('--output-file')
    s=sub.add_parser('serve');s.add_argument('--port',type=int,default=8765)
    s=sub.add_parser('doctor');s.add_argument('--deep',action='store_true')
    s=sub.add_parser('chat',help='通过本机Codex CLI进行有出处的连续研读')
    s.add_argument('operation',choices=['status','list','get','ask','cancel','retry','delete','export','backup']);s.add_argument('question',nargs='?')
    s.add_argument('--session');s.add_argument('--turn');g=s.add_mutually_exclusive_group();g.add_argument('--input-file');g.add_argument('--input-json');g.add_argument('--stdin',action='store_true');g.add_argument('--profile')
    s.add_argument('--second');s.add_argument('--relation',choices=['love','business','hierarchy','friendship'],default=None,help='新双盘的关系类型；续问请在问题里写明关系')
    s.add_argument('--topic',choices=TOPICS,default=None,help='新会话主题；续问请在问题里写明主题');s.add_argument('--namespace',choices=['ziwei','yijing','fengshui','tieban','tianji','historical_ziwei','renji','all'],default=None,help='新知识会话的资料领域')
    s.add_argument('--source');s.add_argument('--tool',choices=['liuren','calendar','time-candidates','twins']);s.add_argument('--offset',type=int,default=0);s.add_argument('--limit',type=int,default=20)
    args=p.parse_args()
    try:
        if getattr(args,'limit',1)<1 or getattr(args,'limit',1)>({'browse':50,'personal':100,'chat':50}.get(args.action,20)):raise ValueError('limit超出允许范围。')
        if getattr(args,'max_chars',1)<1 or getattr(args,'max_chars',1)>100000:raise ValueError('max-chars 范围1–100000。')
        if getattr(args,'offset',0)<0:raise ValueError('offset 不能为负。')
        if args.action in ['status','coverage']:result=status()
        elif args.action=='doctor':
            from .diagnostics import doctor
            result=doctor(args.deep)
        elif args.action=='serve':
            from .webapp import serve
            serve(args.port);return 0
        elif args.action=='catalog':
            from .library import catalog
            result=catalog()
        elif args.action=='chat':
            from . import codex_chat
            if args.operation=='status':result=codex_chat.status()
            elif args.operation=='list':result=codex_chat.list_conversations(args.offset,args.limit)
            elif args.operation=='get':result=codex_chat.get_conversation(args.session)
            elif args.operation=='cancel':result=codex_chat.cancel(args.turn)
            elif args.operation=='delete':result=codex_chat.delete(args.session)
            elif args.operation=='export':result=codex_chat.export(args.session)
            elif args.operation=='backup':result=codex_chat.backup()
            elif args.operation=='retry':
                job=codex_chat.retry(args.turn);result=codex_chat.wait_for_turn(job['session_id'],job['turn_id'])
            else:
                scope=None
                if args.session and any([args.input_file,args.input_json,args.stdin,args.profile,args.source,args.tool,args.second,args.topic,args.namespace,args.relation]):raise ValueError('已有会话请直接在追问里指定主题、关系或目标时间；更换出生资料、原典、工具或资料领域时请新建会话。')
                if not args.session:
                    payload=profile_payload(args.profile) if args.profile else read_json(args.input_file) if args.input_file else json.loads(args.input_json.lstrip('\ufeff')) if args.input_json else json.loads(sys.stdin.read().lstrip('\ufeff')) if args.stdin else None
                    if sum(bool(value) for value in [args.source,args.tool,args.second])>1:raise ValueError('请只选择原典、工具或双盘中的一种研读方式。')
                    if payload is None and (args.tool or args.second):raise ValueError('工具或双盘研读需要先提供主输入资料。')
                    if args.source:
                        scope={'mode':'source','source_id':args.source,'topic':args.topic or 'overview'}
                        if args.namespace:scope['namespace']=args.namespace
                        if payload is not None:scope['payload']=payload
                    elif payload is not None:
                        scope={'mode':'chart','payload':payload,'topic':args.topic or 'overview'}
                        if args.second:scope.update(mode='compare',second=read_json(args.second),relation=args.relation or 'love')
                        elif args.tool:scope.update(mode='tool',tool=args.tool,tool_input=payload if args.tool=='liuren' else {})
                    else:scope={'mode':'knowledge','namespace':args.namespace or 'ziwei'}
                job=codex_chat.submit(args.question,scope,args.session);result=codex_chat.wait_for_turn(job['session_id'],job['turn_id'])
            if args.operation in ['ask','retry'] and not result.get('passed'):
                print(json.dumps(result,ensure_ascii=False,indent=2));return 1
        elif args.action=='browse':
            from .library import browse
            result=browse(args.source_id,args.offset,args.limit,args.filter)
        elif args.action=='personal':
            from .library import personal
            result=personal(args.operation,args.kind,args.id,args.title,read_json(args.input_file) if args.input_file else None,args.offset,args.limit,args.query,args.output_file)
        elif args.action=='city':
            from .geography import city_search
            result=city_search(args.name)
        elif args.action=='search':
            if not args.query.strip() or len(args.query)>3000:raise ValueError('问题不能为空且不超过3000字符。')
            from .retrieval import search
            result=search(args.query,args.limit,args.namespace,args.mode,args.include_candidates)
        elif args.action=='source':
            if args.id.startswith('CASE:'):
                from .cases import lookup
                _,version,key,topic=args.id.split(':')
                if version!='v4.0-13d':raise ValueError('不支持该案例版本；本库仅有 v4.0-13d，不替换其它版本。')
                result=lookup(key,topic,args.max_chars)
            else:
                from .retrieval import source_record
                if not 0<=args.neighbors<=5:raise ValueError('neighbors 范围0–5。')
                result=source_record(args.id,args.max_chars,args.neighbors)
        elif args.action=='case':
            from .cases import lookup
            result=lookup(args.key,args.topic,args.max_chars,args.offset)
            if args.export and result.get('found'):
                full=lookup(args.key,'all',100000);file=ROOT/'exports'/f"case-{args.key}.md"
                file.parent.mkdir(exist_ok=True)
                lines=[f'# v4 原始案例 {args.key}',f"内容版本：{full['content_version']}",f"来源：{full['source_url']}",full['applicability']]
                for topic,data in full['topics'].items():lines.extend(['\n## '+data['label'],data['text']])
                file.write_text('\n\n'.join(lines),encoding='utf-8');result['export_path']=str(file)
        elif args.action in ['chart','context','calendar','period','period-context','liuren','flights','twins','report','ask','time-candidates']:
            if args.stdin:payload=json.loads(sys.stdin.read().lstrip('\ufeff'))
            elif args.input_file:payload=read_json(args.input_file)
            elif args.input_json:payload=json.loads(args.input_json)
            elif getattr(args,'profile',None):payload=profile_payload(args.profile)
            elif args.action=='ask':payload=None
            else:
                import datetime
                from zoneinfo import ZoneInfo
                now=datetime.datetime.now(ZoneInfo('Asia/Hong_Kong'));payload={'year':now.year,'month':now.month,'day':now.day,'clock_hour':now.hour}
            from .engine import chart,context,calendar,liuren,period_context
            if args.action=='ask':
                if not args.question.strip() or len(args.question)>3000:raise ValueError('问题应为1–3000字符。')
                if payload is None:
                    if any(v is not None for v in [args.view,args.date,args.year,args.hour,args.decadal_index,args.method]):raise ValueError('运限参数需要出生资料或已保存命盘，未当成普通知识检索忽略。')
                    from .retrieval import search
                    result={'question':args.question,'answerer':'Codex','evidence':search(args.question,args.limit,args.namespace,args.mode),'answer_contract':'Use retrieved source text, conditions and citations; the CLI does not impersonate a chat model.'}
                else:
                    if args.namespace is not None or args.mode!='hybrid':raise ValueError('命盘追问使用固定的上下文检索流程；分域/词检索请用不带出生输入的ask或search。')
                    result=context(period_payload(payload,args),args.question,args.topic,args.limit)
            elif args.action=='chart':result=chart(payload)
            elif args.action=='context':result=context(payload,args.question,args.topic)
            elif args.action=='calendar':result=calendar(payload)
            elif args.action=='liuren':result=liuren(payload)
            elif args.action=='flights':result=chart(payload)['flights']
            elif args.action=='time-candidates':
                from .engine import time_candidates
                result=time_candidates(payload)
            elif args.action in ['period','period-context']:
                payload=period_payload(payload,args)
                result=chart(payload,'period') if args.action=='period' else period_context(payload,args.question,args.topic)
            elif args.action=='twins':
                from .twins import twins
                result=twins(payload,args.limit)
            else:
                from .reports import export_report
                result=export_report(payload,args.hide_birth,args.mode,Path(args.analysis_file).read_text(encoding='utf-8') if args.analysis_file else '')
        else:
            from .engine import compare
            result=compare(profile_payload(args.first_profile) if args.first_profile else read_json(args.first),profile_payload(args.second_profile) if args.second_profile else read_json(args.second),args.question,args.relation)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if args.action=='doctor' and not result['passed']:return 1
    except Exception as exc:
        print(json.dumps({'error':str(exc),'action':args.action},ensure_ascii=False,indent=2));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
