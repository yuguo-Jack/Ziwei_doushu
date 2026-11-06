"""Conversation lifecycle regression tests. Codex and retrieval are stubbed explicitly."""
import json,os,sys,threading,time,unittest,uuid
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb import codex_chat as chat
from ziwei_kb.chat_context import period_intent,validate_scope
from ziwei_kb.presentation import source_view

OUT=ROOT/'evaluations/codex-chat-20261106';OUT.mkdir(parents=True,exist_ok=True)

def prepared(question,scope,history):
    return {'scope':scope,'topic':'overview','facts':{},'notes':[],'sources':[{'number':1,'evidence_id':'GUIDE-borrow','title':'借星方法','category':'排盘方法说明','text':'借星不等于实际同宫。'}]}

def answer(prompt,settings,cancelled):
    return {'answer':'借星不等于实际同宫。[1]','citations':[1],'follow_ups':['什么是空宫？'],'memory':'用户正在研读借星。'},{'test_stub':True}

class ChatTests(unittest.TestCase):
    def setUp(self):
        self.threads=set(threading.enumerate())
        self.database=OUT/('unit-'+uuid.uuid4().hex+'.sqlite')
        self.patches=[patch.object(chat,'DB',self.database),patch.object(chat,'prepare_context',prepared),patch.object(chat,'run_codex',answer)]
        for value in self.patches:value.start()
    def tearDown(self):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            with chat.connection() as conn:busy=conn.execute("SELECT count(*) FROM turns WHERE status IN ('queued','preparing','generating')").fetchone()[0]
            if not busy:break
            time.sleep(.02)
        for worker in set(threading.enumerate())-self.threads:
            worker.join(timeout=5)
        for value in reversed(self.patches):value.stop()
        for suffix in ['','-wal','-shm']:
            path=Path(str(self.database)+suffix)
            if path.exists():path.unlink()
    def complete(self,question='解释借星',**kwargs):
        job=chat.submit(question,**kwargs);result=chat.wait_for_turn(job['session_id'],job['turn_id'],5)
        self.assertTrue(result['passed'],result);return job,result
    def test_completed_response_and_source(self):
        job,result=self.complete();self.assertEqual(result['turn']['sources'][0]['evidence_id'],'GUIDE-borrow')
        self.assertIn('<p>',result['turn']['answer_html']);self.assertEqual(len(chat.list_conversations()['items']),1)
    def test_followup_keeps_history_and_memory(self):
        job,_=self.complete();received=[]
        def context(q,s,h):received.extend(h);return prepared(q,s,h)
        with patch.object(chat,'prepare_context',context):self.complete('那为什么呢',session_id=job['session_id'])
        self.assertEqual(received[0]['question'],'解释借星');self.assertEqual(received[0]['memory'],'用户正在研读借星。')
    def test_request_ack_retry_is_idempotent(self):
        request=uuid.uuid4().hex;job,_=self.complete(request_id=request)
        self.assertEqual(chat.submit('解释借星',request_id=request),job)
        self.assertEqual(len(chat.get_conversation(job['session_id'])['messages']),1)
        with self.assertRaises(ValueError):chat.submit('不同问题',request_id=request)
    def test_scope_cannot_change_inside_conversation(self):
        job,_=self.complete()
        with self.assertRaises(ValueError):chat.submit('换资料',scope={'mode':'knowledge','namespace':'yijing'},session_id=job['session_id'])
    def test_busy_duplicate_blocked(self):
        started=threading.Event();release=threading.Event()
        def delayed(*args):started.set();release.wait(3);return answer(*args)
        with patch.object(chat,'run_codex',delayed):
            job=chat.submit('等待测试');self.assertTrue(started.wait(3))
            with self.assertRaises(ValueError):chat.submit('第二条',session_id=job['session_id'])
            release.set();self.assertTrue(chat.wait_for_turn(job['session_id'],job['turn_id'],5)['passed'])
    def test_cancel_then_immediate_retry_old_worker_cannot_overwrite(self):
        started=threading.Event();release=threading.Event();old_done=threading.Event();calls=[]
        def delayed(prompt,settings,cancelled):
            calls.append(1)
            if len(calls)==1:
                started.set();release.wait(3)
                try:raise InterruptedError('旧进程停止')
                finally:old_done.set()
            return answer(prompt,settings,cancelled)
        with patch.object(chat,'run_codex',delayed):
            job=chat.submit('停止再试');self.assertTrue(started.wait(3));chat.cancel(job['turn_id']);chat.retry(job['turn_id'])
            result=chat.wait_for_turn(job['session_id'],job['turn_id'],5);self.assertTrue(result['passed'],result)
            release.set();self.assertTrue(old_done.wait(2));time.sleep(.15)
            self.assertEqual(chat.get_conversation(job['session_id'])['messages'][-1]['status'],'succeeded')
    def test_delete_stops_active_worker(self):
        started=threading.Event();cancelled=threading.Event()
        def delayed(prompt,settings,stop):
            started.set();deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                if stop():cancelled.set();raise InterruptedError('已停止')
                time.sleep(.02)
            return answer(prompt,settings,stop)
        with patch.object(chat,'run_codex',delayed):
            job=chat.submit('删除测试');self.assertTrue(started.wait(3));chat.delete(job['session_id']);self.assertTrue(cancelled.wait(2))
            with self.assertRaises(ValueError):chat.get_conversation(job['session_id'])
    def test_recovery_marks_orphan_without_losing_question(self):
        job,_=self.complete()
        with chat.connection() as conn:conn.execute("UPDATE turns SET status='generating',worker_pid=NULL WHERE id=?",(job['turn_id'],));conn.commit()
        value=chat.get_conversation(job['session_id'])['messages'][0]
        self.assertEqual(value['status'],'failed');self.assertIn('服务已重启',value['error']);self.assertEqual(value['question'],'解释借星')
    def test_unknown_citation_rejected(self):
        def wrong(*args):v,m=answer(*args);v['citations']=[99];return v,m
        with patch.object(chat,'run_codex',wrong):
            job=chat.submit('核对');result=chat.wait_for_turn(job['session_id'],job['turn_id'],5)
            self.assertFalse(result['passed']);self.assertIn('出处',result['turn']['error'])
    def test_inline_number_must_be_returned(self):
        def wrong(*args):v,m=answer(*args);v['citations']=[];return v,m
        with patch.object(chat,'run_codex',wrong):
            job=chat.submit('核对');self.assertFalse(chat.wait_for_turn(job['session_id'],job['turn_id'],5)['passed'])
    def test_markdown_disallows_script_image_and_javascript_url(self):
        html=chat.answer_html('<script>alert(1)</script>\n![x](https://e.test/p.png)\n[x](javascript:alert(1))\n[出处](https://e.test)')
        self.assertNotIn('<script',html);self.assertNotIn('<img',html);self.assertNotIn('href="javascript:',html);self.assertIn('noreferrer noopener',html)
    def test_invalid_input_is_rejected_before_worker(self):
        for value in ['',None,'a'*3001]:
            with self.assertRaises(ValueError):chat.submit(value)
        for value in ['../../x','g'*32,None]:
            with self.assertRaises(ValueError):chat.get_conversation(value)
    def test_export_keeps_citations(self):
        job,_=self.complete();result=chat.export(job['session_id']);path=Path(result['path'])
        try:self.assertIn('[1] 借星方法',path.read_text(encoding='utf8'))
        finally:path.unlink()
    def test_consistent_sqlite_backup_contains_conversations_and_sources(self):
        job,_=self.complete();self.complete('继续追问',session_id=job['session_id']);self.complete('另一段研读')
        path=Path(chat.backup()['path'])
        try:
            import sqlite3
            from contextlib import closing
            with closing(sqlite3.connect(path)) as conn:
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                self.assertEqual(conn.execute('SELECT count(*) FROM conversations').fetchone()[0],2)
                self.assertEqual(conn.execute('SELECT count(*) FROM turns').fetchone()[0],3)
                self.assertIn('GUIDE-borrow',conn.execute('SELECT sources FROM turns LIMIT 1').fetchone()[0])
        finally:path.unlink()
    def test_source_code_is_humanized_without_mutating_source(self):
        raw={'id':'CODE-test','artifact_kind':'source_code','title':'代码格局规则 / 借星','text':'return isEmpty && borrowedStars.length;'}
        view=source_view(raw);self.assertNotIn('return',view['text']);self.assertIn('isEmpty',raw['text']);self.assertTrue(view['is_method'])
    def test_period_and_topic_switch_are_explicit(self):
        payload={'year':1990,'period':{'view':'yearly','target_year':2026,'annual_method':'xiaoxian'}}
        value,notes=period_intent(payload,'2027年感情呢');self.assertEqual(value['period']['target_year'],2027);self.assertEqual(payload['period']['target_year'],2026)
        self.assertNotIn('period',period_intent(value,'回到本命')[0])
        self.assertTrue(period_intent(payload,'看看流月')[1]);self.assertTrue(period_intent(payload,'2027-11-06流时')[1])
    def test_explicit_birth_year_does_not_become_target_year(self):
        payload={'year':1990};value,notes=period_intent(payload,'我是1992年出生');self.assertNotIn('period',value);self.assertTrue(notes)
    def test_scope_validation_and_domains(self):
        with self.assertRaises(ValueError):validate_scope({'mode':'chart'})
        with self.assertRaises(ValueError):validate_scope({'mode':'knowledge','execute':'whoami'})
        self.assertEqual(validate_scope({'mode':'knowledge','namespace':'renji'})['namespace'],'renji')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ChatTests))
    (OUT/'unit-results.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'scope':'Conversation lifecycle and rendering; Codex/retrieval explicitly stubbed.'},indent=2),encoding='utf8')
    sys.exit(not result.wasSuccessful())
