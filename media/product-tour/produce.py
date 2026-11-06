"""Prepare editable HyperFrames sources and package the final, local product video.

Only the optional `audio` command calls an external speech service with storyboard text.
Intermediate files are confined to .cache/product-tour; no Git operation is performed.
"""
import argparse,asyncio,hashlib,json,re,shutil,subprocess,sys,wave
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).resolve().parent
WORK=ROOT/'.cache/product-tour'
PUBLIC=ROOT/'web/public/media'

def read(path):return json.loads(path.read_text(encoding='utf8'))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def command(args,**kwargs):return subprocess.run([str(arg) for arg in args],check=True,**kwargs)
def duration(path):
    value=command(['ffprobe','-v','error','-show_entries','format=duration','-of','json',path],capture_output=True,text=True,encoding='utf8')
    return float(json.loads(value.stdout)['format']['duration'])
def stamp(seconds):
    ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02}.{ms%1000:03}'

def fonts(display,sans):
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools import subset
    if not display or not sans:raise ValueError('Pass --display-font and --sans-font pointing to the Noto CJK variable fonts.')
    text='子丑寅卯辰巳午未申酉戌亥'
    for name in ['index.html','composition.js','storyboard.json']:text+=(SOURCE/name).read_text(encoding='utf-8-sig')
    rows=[];(SOURCE/'assets').mkdir(exist_ok=True)
    for original,name,weight,family in [(display,'display.woff2',700,'Ziwei Tour Display'),(sans,'sans.woff2',400,'Ziwei Tour Sans')]:
        font=TTFont(original);font=instantiateVariableFont(font,{'wght':weight},inplace=True)
        missing=[char for char in set(text) if '\u4e00'<=char<='\u9fff' and ord(char) not in font.getBestCmap()]
        if missing:raise ValueError('Missing Chinese glyphs: '+''.join(sorted(missing)))
        for ident,value in [(1,family),(4,family),(6,family.replace(' ',''))]:
            font['name'].setName(value,ident,3,1,0x409);font['name'].setName(value,ident,1,0,0)
        options=subset.Options();options.flavor='woff2';job=subset.Subsetter(options=options);job.populate(text=text);job.subset(font)
        font.flavor='woff2';target=SOURCE/'assets'/name;font.save(target)
        rows.append({'file':name,'family':family,'upstream_family':original.name,'weight':weight,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    shutil.copyfile(ROOT/'web/public/fonts/OFL.txt',SOURCE/'assets/OFL.txt')
    write(SOURCE/'assets/fonts.json',{'source':'https://github.com/notofonts/noto-cjk','license':'SIL Open Font License 1.1','derivation':'Renamed static subsets for the30-second product film','files':rows})
    print(json.dumps(rows,ensure_ascii=False))

async def speech(story):
    semaphore=asyncio.Semaphore(2)
    async def one(scene):
        if not scene['speech']:return
        target=WORK/'audio'/(scene['id']+'.mp3');key=target.with_suffix('.sha256')
        identity=hashlib.sha256(json.dumps([story['voice'],story['voice_rate'],scene['speech']],ensure_ascii=False).encode()).hexdigest()
        if target.exists() and key.exists() and key.read_text()==identity:return
        async with semaphore:
            process=await asyncio.create_subprocess_exec(sys.executable,'-X','utf8','-m','edge_tts','--text',scene['speech'],
                '--voice',story['voice'],'--rate='+story['voice_rate'],'--write-media',str(target))
            if await process.wait():raise RuntimeError('Speech synthesis failed: '+scene['id'])
            key.write_text(identity,encoding='utf8');print('Speech ready: '+scene['id'],flush=True)
    await asyncio.gather(*(one(scene) for scene in story['scenes']))

def audio():
    import numpy as np
    story=read(SOURCE/'storyboard.json');(WORK/'audio').mkdir(parents=True,exist_ok=True)
    asyncio.run(speech(story));timeline=[];captions=[];offset=0.;rate=48000;beat=60/story['bpm']
    for scene in story['scenes']:
        trimmed=WORK/'audio'/(scene['id']+'.wav')
        if scene['speech']:
            trim='silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse'
            command(['ffmpeg','-v','error','-y','-i',WORK/'audio'/(scene['id']+'.mp3'),'-af',trim,'-ac','1','-ar',str(rate),trimmed])
        length=duration(trimmed) if scene['speech'] else 0.
        span=scene['beats']*beat
        if length>span-.2:raise ValueError(f"Narration exceeds fixed beat window: {scene['id']} ({length:.2f}s / {span-.2:.2f}s). Shorten the line or adjust the voice rate.")
        row={**scene,'start':round(offset,6),'duration':round(span,6),'speech_start':round(offset+.1,6),'speech_duration':length}
        timeline.append(row)
        # Stable sentence timing from the actual clip length; these are edited narration captions.
        parts=[text.strip() for text in re.split(r'(?<=[，。；！?？])',scene['speech']) if text.strip()]
        chunks=[];current=''
        for part in parts:
            if current and len(current+part)>18:chunks.append(current);current=''
            current+=part
        if current:chunks.append(current)
        weights=[len(text) for text in chunks];cursor=row['speech_start']
        for text,weight in zip(chunks,weights):
            end=cursor+length*weight/sum(weights)
            captions.append({'start':round(cursor,3),'end':round(end,3),'text':text});cursor=end
        if chunks:captions[-1]['end']=round(offset+span-.08,3)
        offset+=span
    total=round(offset,6)
    if abs(total-story['duration'])>1e-5:raise ValueError('Beat map must fill the exact film duration.')
    n=round(total*rate);time=np.arange(n,dtype=np.float64)/rate;bed=np.zeros(n,dtype=np.float32)
    rng=np.random.default_rng(140917)
    def add(at,samples,gain=1):
        start=max(0,round(at*rate));size=min(len(samples),n-start)
        if size>0:bed[start:start+size]+=(samples[:size]*gain).astype(np.float32)
    # Original140BPM hybrid score: tuned sub, kick/snare/hats, pentatonic arpeggio and chapter risers.
    for i in range(round(total/beat)):
        at=i*beat;t=np.arange(round(.32*rate))/rate
        kick=np.sin(2*np.pi*(46*t+110*.025*(1-np.exp(-t/.025))))*np.exp(-t*17)
        add(at,kick,.24 if i>=4 else .13)
        if i>=4:
            bass=[73.416,65.406,58.27,55.][(i//8)%4];t=np.arange(round(beat*.8*rate))/rate
            add(at,(np.sin(2*np.pi*bass*t)+.22*np.sin(6*np.pi*bass*t))*np.exp(-t*7)*(1-np.exp(-t*160)),.065)
        if i%4 in [1,3] and i>=8:
            t=np.arange(round(.16*rate))/rate;noise=rng.normal(0,1,len(t))
            add(at,(noise*.5+np.sin(2*np.pi*185*t)*.3)*np.exp(-t*28),.09)
        for sub in [0,.5]:
            if i<4:continue
            t=np.arange(round(.043*rate))/rate;noise=rng.normal(0,1,len(t));high=np.concatenate(([0.],np.diff(noise)))
            add(at+beat*sub,high*np.exp(-t*120),.012 if sub else .008)
    notes=[293.665,440.,523.251,391.995,349.228,587.33,523.251,440.]
    for i,at in enumerate(np.arange(8*beat,total-1,beat/2)):
        t=np.arange(round(.24*rate))/rate;frequency=notes[i%8]
        add(at,(np.sin(2*np.pi*frequency*t)+.23*np.sin(4*np.pi*frequency*t))*np.exp(-t*19)*(1-np.exp(-t*180)),.035)
    for scene in timeline[1:]:
        t=np.arange(round(.25*rate))/rate;noise=rng.normal(0,1,len(t));smooth=np.convolve(noise,np.ones(9)/9,mode='same')
        add(scene['start']-.25,smooth*(t/.25)**2,.085)
        t=np.arange(round(.65*rate))/rate
        add(scene['start'],np.sin(2*np.pi*(48*t+18*.08*(1-np.exp(-t/.08))))*np.exp(-t*9),.1)
    t=np.arange(round(2.4*rate))/rate
    gong=sum(gain*np.sin(2*np.pi*146.832*ratio*t)*np.exp(-t*decay) for ratio,gain,decay in [(1,.6,1.8),(2.02,.25,3),(2.51,.18,4.4)])
    add(timeline[-1]['start'],gong*(1-np.exp(-t*120)),.095)
    bed*=np.minimum(time/.025,1)*np.clip((total-time)/.22,0,1)
    voice=np.zeros(n,dtype=np.float32)
    duck=np.ones(n,dtype=np.float32)
    for row in timeline:
        if not row['speech']:continue
        pcm=command(['ffmpeg','-v','error','-i',WORK/'audio'/(row['id']+'.wav'),'-ac','1','-ar',str(rate),'-f','f32le','pipe:1'],capture_output=True).stdout
        samples=np.frombuffer(pcm,dtype='<f4');start=round(row['speech_start']*rate);size=min(len(samples),n-start)
        voice[start:start+size]+=samples[:size]*1.1
        low=max(0,start-round(.035*rate));high=min(n,start+size+round(.07*rate));duck[low:high]=.38
    kernel=np.ones(round(.025*rate),dtype=np.float32)/round(.025*rate);duck=np.convolve(duck,kernel,mode='same')
    bed*=duck
    stereo=np.stack([voice+bed,voice+np.roll(bed,round(.006*rate))*.95],axis=1)
    peak=float(np.abs(stereo).max());stereo/=max(1,peak/.95)
    mix=WORK/'audio/mix.wav'
    with wave.open(str(mix),'wb') as stream:
        stream.setnchannels(2);stream.setsampwidth(2);stream.setframerate(rate)
        stream.writeframes((stereo*32767).astype('<i2').tobytes())
    (SOURCE/'assets').mkdir(exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    command(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',mix,'-af','loudnorm=I=-15:TP=-1.4:LRA=6',
             '-c:a','aac','-b:a','128k','-movflags','+faststart',SOURCE/'assets/soundtrack.m4a'])
    write(SOURCE/'timing.json',{'duration':total,'fps':story['fps'],'bpm':story['bpm'],'scenes':timeline,'captions':captions})
    write(PUBLIC/'ziwei-intro.json',{'duration':total,'chapters':[{'start':row['start'],'label':row['label']} for row in timeline if row.get('chapter',True)]})
    vtt='WEBVTT\n\n'+'\n\n'.join(f"{stamp(row['start'])} --> {stamp(row['end'])}\n{row['text']}" for row in captions)+'\n'
    (PUBLIC/'ziwei-intro.zh-CN.vtt').write_text(vtt,encoding='utf8')
    print(json.dumps({'duration':total,'scenes':len(timeline),'captions':len(captions),'audio_peak_before_normalization':peak}))

def prepare(gsap):
    if not gsap or not gsap.is_file():raise ValueError('Pass --gsap-file pointing to the pinned GSAP 3.14.2 dist/gsap.min.js.')
    target=WORK/'composition';assets=target/'assets';assets.mkdir(parents=True,exist_ok=True)
    for name in ['index.html','composition.css','composition.js']:
        shutil.copyfile(SOURCE/name,target/name)
    for path in (SOURCE/'assets').iterdir():
        if path.is_file():shutil.copyfile(path,assets/path.name)
    for name in ['workbench.jpg','chat-desktop.jpg']:
        shutil.copyfile(ROOT/'docs/screenshots'/name,assets/name)
    shutil.copyfile(gsap,assets/'gsap.min.js')
    timing=read(SOURCE/'timing.json')
    page=(target/'index.html').read_text(encoding='utf8').replace('__DURATION__',str(timing['duration'])).replace('__FPS__',str(timing['fps']))
    (target/'index.html').write_text(page,encoding='utf8')
    (target/'timing.js').write_text('window.FILM = '+json.dumps(timing,ensure_ascii=False)+';\n',encoding='utf8')
    shutil.copyfile(ROOT/'DESIGN.md',target/'DESIGN.md')
    print(json.dumps({'composition':str(target),'duration':timing['duration'],'all_runtime_assets_local':True},ensure_ascii=False))

def package(render):
    if not render or not render.is_file():raise ValueError('Pass --render pointing to the HyperFrames-rendered MP4.')
    PUBLIC.mkdir(parents=True,exist_ok=True);target=PUBLIC/'ziwei-intro.mp4'
    # Two-pass H.264 keeps the complete 1080p film under the publication guard's 10 MiB limit.
    story=read(SOURCE/'storyboard.json');seconds=story['duration']
    info=json.loads(command(['ffprobe','-v','error','-show_format','-show_streams','-of','json',render],capture_output=True,text=True,encoding='utf8').stdout)
    video=next(row for row in info['streams'] if row['codec_type']=='video')
    if abs(float(info['format']['duration'])-seconds)>.1 or Fraction(video['r_frame_rate'])!=story['fps'] or (video['width'],video['height'])!=(1920,1080):
        raise ValueError('HyperFrames master does not match the fixed duration,1080p canvas and storyboard frame rate.')
    bitrate=min(6000000,int((9.2*1024**2*8/seconds)-96000))
    prefix=WORK/'encode-pass';common=['ffmpeg','-v','error','-y','-i',render,'-c:v','libx264','-b:v',str(bitrate),
        '-preset','slow','-pix_fmt','yuv420p','-g',str(story['fps']*2),'-t',str(seconds),'-passlogfile',prefix]
    command(common+['-pass','1','-an','-f','null','-'])
    command(common+['-pass','2','-c:a','aac','-b:a','80k','-movflags','+faststart',target])
    command(['ffmpeg','-v','error','-y','-ss',str(story['poster_at']),'-i',target,'-frames:v','1','-q:v','2',PUBLIC/'ziwei-intro-poster.jpg'])
    # Keep a small, GitHub-friendly poster by reusing the selected frame in README.
    shutil.copyfile(PUBLIC/'ziwei-intro-poster.jpg',ROOT/'docs/screenshots/product-tour.jpg')
    if target.stat().st_size>=10*1024**2:raise RuntimeError('Video exceeds the per-file publication budget.')
    write(SOURCE/'manifest.json',{'hyperframes':'0.9.19','gsap':'3.14.2','duration':seconds,'dimensions':[1920,1080],
        'fps':story['fps'],'bpm':story['bpm'],'video_codec':'H.264','audio_codec':'AAC','bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'footage':'Fictional examples and public workbench screenshots','soundtrack':'Edge TTS Chinese narration plus original deterministic synthesis'})
    print(json.dumps({'video':str(target),'duration':seconds,'bytes':target.stat().st_size},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['audio','fonts','prepare','package']);parser.add_argument('--gsap-file',type=Path);parser.add_argument('--render',type=Path)
    parser.add_argument('--display-font',type=Path);parser.add_argument('--sans-font',type=Path)
    args=parser.parse_args()
    {'audio':audio,'fonts':lambda:fonts(args.display_font,args.sans_font),'prepare':lambda:prepare(args.gsap_file),'package':lambda:package(args.render)}[args.action]()
