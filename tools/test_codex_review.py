"""Adversarial conversation review. All databases and provider stubs are isolated."""
import concurrent.futures,contextlib,io,json,os,sys,threading,unittest,uuid
from pathlib import Path
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import test_codex_chat as baseline
from ziwei_kb import codex_chat as chat,chat_context as ctx,codex_process as provider,cli

OUT=ROOT/'evaluations/codex-review-20261106';OUT.mkdir(parents=True,exist_ok=True);baseline.OUT=OUT

class ConversationReview(baseline.ChatTests):
    def test_parallel_retries_accept_exactly_one_request(self):
        counts=[]
        with patch.object(chat,'_answer',lambda *args:None):
            job=chat.submit('并发重试')
            try:
                for _ in range(12):
                    with chat.connection() as c:c.execute("UPDATE turns SET status='cancelled' WHERE id=?",(job['turn_id'],));c.commit()
                    barrier=threading.Barrier(8)
                    def run(_):
                        barrier.wait()
                        try:chat.retry(job['turn_id']);return 1
                        except ValueError:return 0
                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:counts.append(sum(pool.map(run,range(8))))
                self.assertEqual(counts,[1]*12)
            finally:chat.cancel(job['turn_id'])
        (OUT/'retry-race-after.json').write_text(json.dumps({'passed':True,'accepted_per_8_parallel_retries':counts,'scope':'Actual SQLite transactions; worker explicitly disabled, no model calls.'},indent=2),encoding='utf8')

    def test_retry_respects_global_active_limit(self):
        with patch.object(chat,'_answer',lambda *args:None):
            old=chat.submit('已停止的请求');chat.cancel(old['turn_id']);jobs=[]
            try:
                jobs=[chat.submit('排队'+str(index)) for index in range(8)]
                with self.assertRaisesRegex(ValueError,'当前研读较多'):chat.retry(old['turn_id'])
            finally:
                for job in jobs:chat.cancel(job['turn_id'])

    def test_equal_timestamps_preserve_insert_order_and_history(self):
        received=[]
        def context(q,s,h):received.append([turn['question'] for turn in h]);return baseline.prepared(q,s,h)
        with patch.object(chat,'now',lambda:'2026-11-06T00:00:00+00:00'),patch.object(chat,'prepare_context',context):
            job,_=self.complete('第一问');self.complete('第二问',session_id=job['session_id'])
        self.assertEqual(received,[[],['第一问']])
        self.assertEqual([m['question'] for m in chat.get_conversation(job['session_id'])['messages']],['第一问','第二问'])

    def test_cancel_before_preparation_keeps_previous_effective_scope(self):
        base={'mode':'chart','payload':{'year':1990,'month':1,'day':1,'hour':4,'gender':'male'},'topic':'career'}
        previous={**base,'payload':{**base['payload'],'period':{'view':'yearly','target_year':2027,'annual_method':'xiaoxian'}},'topic':'love'}
        job,_=self.complete('先看2027',scope=base)
        with chat.connection() as c:c.execute('UPDATE turns SET effective_scope=? WHERE id=?',(json.dumps(previous),job['turn_id']));c.commit()
        with patch.object(chat,'_answer',lambda *args:None):
            next_job=chat.submit('暂未准备的追问',session_id=job['session_id']);chat.cancel(next_job['turn_id'])
        self.assertEqual(chat.get_conversation(job['session_id'])['current_scope'],previous)

    def test_orphan_snapshot_cannot_overwrite_new_execution(self):
        job,_=self.complete();new_id=uuid.uuid4().hex
        with chat.connection() as c:c.execute("UPDATE turns SET status='generating',worker_pid=NULL WHERE id=?",(job['turn_id'],));c.commit()
        def replace_worker(pid):
            with chat.connection() as c:c.execute("UPDATE turns SET status='queued',worker_pid=?,execution_id=? WHERE id=?",(os.getpid(),new_id,job['turn_id']));c.commit()
            return False
        with patch.object(chat,'process_alive',replace_worker):
            with chat.connection() as c:chat.recover_orphans(c)
        with chat.connection() as c:
            row=c.execute('SELECT status,execution_id FROM turns WHERE id=?',(job['turn_id'],)).fetchone();self.assertEqual(tuple(row),('queued',new_id))
        chat.cancel(job['turn_id'])

    def test_completed_answer_is_not_reported_as_cancelled(self):
        job,_=self.complete();self.assertFalse(chat.cancel(job['turn_id'])['cancelled']);self.assertEqual(chat.get_conversation(job['session_id'])['messages'][0]['status'],'succeeded')

    def test_provider_malformed_json_becomes_readable_error(self):
        process=Mock();process.communicate.return_value=(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'NOT JSON'}}),'private diagnostic');process.poll.return_value=0;process.returncode=0
        with patch.object(provider,'cli_command',lambda:['fixture']),patch.object(provider.subprocess,'Popen',return_value=process),patch.object(provider,'ProcessJob'):
            with self.assertRaisesRegex(RuntimeError,'回答格式未能核对'):provider.run_codex('fixture',{'timeout_seconds':30},lambda:False)

    def test_explicit_session_options_are_not_silently_ignored(self):
        job,_=self.complete()
        for flag,value in [('--topic','wealth'),('--namespace','yijing'),('--relation','business')]:
            output=io.StringIO()
            with patch.object(sys,'argv',['ziwei.py','chat','ask','继续','--session',job['session_id'],flag,value]),contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):code=cli.main()
            self.assertNotEqual(code,0);self.assertIn('已有会话',output.getvalue())

    def test_nan_never_enters_conversation_scope(self):
        with self.assertRaisesRegex(ValueError,'无效数值'):ctx.validate_scope({'mode':'chart','payload':{'year':float('nan')}})

    def test_empty_or_duplicate_followups_do_not_create_empty_controls(self):
        def provider(*args):
            value,meta=baseline.answer(*args);value['follow_ups']=['  ','继续研读','继续研读','核对原文'];return value,meta
        with patch.object(chat,'run_codex',provider):_,result=self.complete()
        self.assertEqual(result['turn']['follow_ups'],['继续研读','核对原文'])

    def test_whitespace_response_is_not_a_completed_blank_answer(self):
        def provider(*args):
            value,meta=baseline.answer(*args);value['answer']=' \n  ';return value,meta
        with patch.object(chat,'run_codex',provider):
            job=chat.submit('复核空回答');result=chat.wait_for_turn(job['session_id'],job['turn_id'],5)
        self.assertFalse(result['passed']);self.assertIn('可读回答',result['turn']['error'])

class SemanticReview(unittest.TestCase):
    def setUp(self):self.birth={'year':1990,'month':1,'day':1,'hour':4,'gender':'male','period':{'view':'yearly','target_year':2026,'annual_method':'xiaoxian'}}
    def period(self,question):return ctx.period_intent(self.birth,question)
    def test_iso_date_is_applied_to_yearly_layer(self):
        p,n=self.period('看2027-11-06的流年');self.assertEqual(p['period'],{'view':'yearly','target_date':'2027-11-06','annual_method':'xiaoxian'});self.assertFalse(n)
    def test_chinese_full_date_is_not_requested_again(self):
        p,n=self.period('2027年11月6日的流日呢');self.assertEqual(p['period']['view'],'daily');self.assertEqual(p['period']['target_date'],'2027-11-06');self.assertFalse(n)
    def test_negated_relative_year_does_not_override_explicit_year(self):
        p,n=self.period('2027年，不是今年');self.assertEqual(p['period']['target_year'],2027);self.assertFalse(n)
    def test_negated_year_and_topic_are_excluded(self):
        p,_=self.period('不看2027年，只看2028年');self.assertEqual(p['period']['target_year'],2028)
        self.assertEqual(ctx.ordered_mentions('不要感情，改看事业',ctx.TOPIC_WORDS),['career'])
        self.assertEqual(ctx.ordered_mentions('健康先看，事业暂时不谈',ctx.TOPIC_WORDS),['health'])
    def test_relations_change_only_when_requested(self):
        self.assertEqual(ctx.relation_intent('那合伙呢'),['business']);self.assertEqual(ctx.relation_intent('不是夫妻关系，按合伙看'),['business'])
        self.assertEqual(ctx.relation_intent('我们换成朋友看，150字以内'),['friendship']);self.assertEqual(ctx.relation_intent('朋友说这段古籍是否真的支持这个条件'),[])
        self.assertEqual(ctx.relation_intent('朋友说的？'),[])
    def test_multiple_times_require_clarification(self):
        for q in ['比较2027年和2028年','今年和明年对比','比较2027-01-01和2027-11-06']:
            p,n=self.period(q);self.assertEqual(p,self.birth);self.assertTrue(n)
    def test_mixed_date_and_year_never_silently_select_one_target(self):
        for q in ['比较2027年与2028年11月6日的流年','看2027年流年，和2028-01-01比一下','2027年11月6日和明年对比']:
            p,n=self.period(q);self.assertEqual(p,self.birth);self.assertTrue(n)
    def test_out_of_range_year_is_forwarded_to_engine_validation(self):
        p,n=self.period('看2200年的流年');self.assertEqual(p['period']['target_year'],2200)
        p,n=self.period('看2200-11-06的流日');self.assertEqual(p['period']['target_date'],'2200-11-06')
    def test_impossible_date_reports_chinese_error(self):
        with self.assertRaisesRegex(ValueError,'目标日期无效'):self.period('2027年2月30日的流日')
    def test_lunar_target_uses_calendar_conversion(self):
        with patch.object(ctx,'calendar',return_value={'solar':{'year':2027,'month':2,'day':6}}) as convert:
            p,n=self.period('农历2027年1月1日的流日')
        self.assertEqual(p['period']['target_date'],'2027-02-06');self.assertEqual(convert.call_args.args[0]['calendar'],'lunar')
    def test_hour_is_never_guessed(self):
        p,n=self.period('2027-11-06的流时');self.assertEqual(p,self.birth);self.assertTrue(n)
        p,n=self.period('2027-11-06申时的流时');self.assertEqual(p['period']['hour'],8);self.assertFalse(n)
    def test_subperiod_scheme_respects_negation(self):
        p,n=self.period('2027-11-06的小限流月');self.assertEqual(p,self.birth);self.assertTrue(n)
        p,n=self.period('2027-11-06流月，不用小限，改用太岁');self.assertEqual(p['period']['annual_method'],'taishui');self.assertEqual(p['period']['view'],'monthly');self.assertFalse(n)
    def test_concept_question_does_not_demand_a_target_date(self):
        p,n=self.period('流月和流日有什么区别');self.assertEqual(p,self.birth);self.assertFalse(n)
    def test_decadal_is_not_mistaken_for_yearly(self):
        p,n=self.period('看看2027年的大限');self.assertEqual(p['period']['view'],'decadal');self.assertEqual(p['period']['target_year'],2027)
    def test_birth_year_does_not_hide_a_separate_target(self):
        p,n=self.period('我是1990年出生，2027年感情呢');self.assertEqual(p['period']['target_year'],2027);self.assertTrue(n)
        for q in ['我的出生年份是1990年','出生日期是公历1990年1月1日','我是1990年1月1日上午8点出生']:
            p,n=self.period(q);self.assertEqual(p,self.birth);self.assertTrue(n)
    def test_natal_reset_clears_period(self):
        p,n=self.period('2027年不看了，回到本命');self.assertNotIn('period',p)
    def test_calendar_uses_nearest_explicit_qualifier(self):
        dates=ctx.question_dates('农历如何转换？把公历2027年11月6日换算成农历',False);self.assertEqual(dates[0]['calendar'],'solar')
        dates=ctx.question_dates('把出生日期公历1990年1月1日换成农历',False);self.assertEqual(len(dates),1);self.assertEqual(dates[0]['calendar'],'solar')
    def test_source_followup_search_uses_selected_sources_domain(self):
        raw={'id':'test-source','title':'乾卦课程','text':'复核用原段','namespace':'yijing','artifact_kind':'course_quote'}
        with patch.object(ctx,'source_record',return_value=raw),patch.object(ctx,'search',return_value={'hits':[]}) as search:
            value=ctx.prepare_context('解释这段原文',{'mode':'source','source_id':'test-source'},[])
        self.assertEqual(search.call_args.kwargs['namespace'],'yijing');self.assertEqual(value['scope']['namespace'],'yijing')

if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(ConversationReview),unittest.defaultTestLoader.loadTestsFromTestCase(SemanticReview)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'unit-results.json').write_text(json.dumps({'passed':result.wasSuccessful(),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'scope':'Conversation/SQLite and request semantics. Model/retrieval/calendar fixtures are explicit; real context checks are separate.'},indent=2),encoding='utf8')
    sys.exit(not result.wasSuccessful())
