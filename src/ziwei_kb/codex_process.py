"""Existing authenticated Codex CLI, without a shell or model-selected tools."""
import ctypes,json,os,shutil,subprocess,time
from pathlib import Path
from .common import ROOT

def cli_command():
    custom=os.environ.get('ZIWEI_CODEX_CLI')
    if custom:
        path=Path(custom).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() not in ['.exe','']:raise RuntimeError('配置的Codex程序不存在。')
        return [str(path)]
    native=shutil.which('codex.exe')
    if native:return [native]
    wrapper=shutil.which('codex.cmd') or shutil.which('codex')
    if wrapper:
        folder=Path(wrapper).parent
        package=folder/'node_modules/@openai/codex'
        for target in ['x86_64-pc-windows-msvc','aarch64-pc-windows-msvc']:
            name='codex-win32-x64' if target.startswith('x86_64') else 'codex-win32-arm64'
            for vendor in [package/f'node_modules/@openai/{name}/vendor',package/'vendor']:
                candidate=vendor/target/'bin/codex.exe'
                if candidate.is_file():return [str(candidate)]
        entry=package/'bin/codex.js'
        if entry.is_file() and shutil.which('node'):return [shutil.which('node'),str(entry)]
        if os.name!='nt':return [wrapper]
    raise RuntimeError('未找到Codex CLI，请先在本机安装并登录。')

class ProcessJob:
    """Windows closes this job when the parent service exits, also ending its children."""
    def __init__(self,process):
        self.handle=None
        if os.name!='nt':return
        from ctypes import wintypes as w
        class IO(ctypes.Structure):_fields_=[(name,ctypes.c_ulonglong) for name in ['ReadOperationCount','WriteOperationCount','OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount']]
        class BASIC(ctypes.Structure):_fields_=[('PerProcessUserTimeLimit',ctypes.c_longlong),('PerJobUserTimeLimit',ctypes.c_longlong),('LimitFlags',w.DWORD),('MinimumWorkingSetSize',ctypes.c_size_t),('MaximumWorkingSetSize',ctypes.c_size_t),('ActiveProcessLimit',w.DWORD),('Affinity',ctypes.c_size_t),('PriorityClass',w.DWORD),('SchedulingClass',w.DWORD)]
        class EXTENDED(ctypes.Structure):_fields_=[('BasicLimitInformation',BASIC),('IoInfo',IO),('ProcessMemoryLimit',ctypes.c_size_t),('JobMemoryLimit',ctypes.c_size_t),('PeakProcessMemoryUsed',ctypes.c_size_t),('PeakJobMemoryUsed',ctypes.c_size_t)]
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];kernel.CreateJobObjectW.restype=w.HANDLE
        kernel.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
        kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
        kernel.CloseHandle.argtypes=[w.HANDLE]
        handle=kernel.CreateJobObjectW(None,None)
        if not handle:raise RuntimeError('无法创建独立研读进程。')
        limits=EXTENDED();limits.BasicLimitInformation.LimitFlags=0x2000
        if not kernel.SetInformationJobObject(handle,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(handle,int(process._handle)):
            kernel.CloseHandle(handle);raise RuntimeError('无法设置研读进程的退出保护。')
        self.kernel=kernel;self.handle=handle
    def close(self):
        if self.handle:self.kernel.CloseHandle(self.handle);self.handle=None

def run_codex(prompt,settings,cancelled):
    command=cli_command()+['exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--sandbox','read-only',
      '--disable','shell_tool','--disable','unified_exec','--disable','multi_agent','--disable','plugins','--disable','apps',
      '--disable','remote_plugin','--disable','skill_search','--disable','shell_snapshot','-c','approval_policy="never"',
      '--output-schema',str(ROOT/'config/codex-answer.schema.json'),'--json','-']
    model=os.environ.get('ZIWEI_CODEX_MODEL') or settings.get('model')
    if model:command[-1:-1]=['--model',str(model)]
    work=ROOT/'runtime/codex-work';work.mkdir(parents=True,exist_ok=True)
    process=subprocess.Popen(command,cwd=work,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
      text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    job=None;first=True;started=time.monotonic()
    try:
        job=ProcessJob(process)
        while True:
            if cancelled():raise InterruptedError('本次研读已停止。')
            if time.monotonic()-started>settings['timeout_seconds']:raise TimeoutError('本次研读等待超时，请稍后重试。')
            try:
                output,stderr=process.communicate(input=prompt if first else None,timeout=.3);break
            except subprocess.TimeoutExpired:first=False
        events=[]
        for line in output.splitlines():
            try:events.append(json.loads(line))
            except (ValueError,TypeError):continue
        if process.returncode:
            error=' '.join(str(e.get('message','')) for e in events if e.get('type')=='error')+' '+stderr
            if any(word in error.lower() for word in ['unauthorized','authentication','login','401']):raise RuntimeError('Codex登录需要刷新，请先在本机完成登录后重试。')
            if any(word in error.lower() for word in ['rate limit','quota','usage limit','429']):raise RuntimeError('当前Codex账号额度暂不可用，请稍后重试。')
            raise RuntimeError('Codex暂时未能完成回答，请检查网络或稍后重试。')
        messages=[e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
        if not messages:raise RuntimeError('本次未取得完整回答，请重试。')
        try:value=json.loads(messages[-1])
        except (ValueError,TypeError):raise RuntimeError('这次回答格式未能核对，请重试。') from None
        usage=next((e.get('usage',{}) for e in reversed(events) if e.get('type')=='turn.completed'),{})
        return value,{'seconds':round(time.monotonic()-started,2),'usage':usage,'tools_disabled':True}
    finally:
        if process.poll() is None:
            process.kill()
            try:process.communicate(timeout=5)
            except subprocess.TimeoutExpired:pass
        if job:job.close()
