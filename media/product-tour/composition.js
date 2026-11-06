/*30 seconds /140BPM: all motion belongs to one reversible GSAP timeline.*/
(() => {
 const film=window.FILM,B=60/film.bpm,NS='http://www.w3.org/2000/svg';
 function svg(tag,attrs){const node=document.createElementNS(NS,tag);Object.entries(attrs).forEach(function(pair){node.setAttribute(pair[0],pair[1]);});return node;}
 let seed=140917;function random(){seed=seed*16807%2147483647;return(seed-1)/2147483646;}
 const field=document.querySelector('#star-field');
 for(let i=0;i<96;i++)field.append(svg('circle',{cx:50+random()*1820,cy:50+random()*980,r:.5+random()*1.2,fill:i%4===0?'#93bbac':'#d5b77b',opacity:.13+random()*.35}));
 function makeOrbit(node){
   const view=svg('svg',{viewBox:'0 0 1000 1000',fill:'none'}),turn=svg('g',{class:'orbit-turn'}),tilt=svg('g',{class:'orbit-tilt'});
   [450,433,380,320,230].forEach(function(r,i){turn.append(svg('circle',{cx:500,cy:500,r:r,stroke:i===2?'#93bbac':'#d5b77b','stroke-width':i===0?1.7:1,opacity:i===3?.3:.75,'stroke-dasharray':i===2?'1 10':'none'}));});
   for(let i=0;i<100;i++){const a=i*Math.PI/50,r=i%5===0?408:421;turn.append(svg('path',{d:'M'+(500+Math.sin(a)*r)+' '+(500-Math.cos(a)*r)+'L'+(500+Math.sin(a)*433)+' '+(500-Math.cos(a)*433),stroke:'#d5b77b','stroke-width':1,opacity:.7}));}
   turn.append(svg('path',{d:'M500 50L890 725L110 725Z',stroke:'#93bbac','stroke-width':1.2,opacity:.5}));
   turn.append(svg('path',{d:'M500 950L110 275L890 275Z',stroke:'#d5b77b','stroke-width':1,opacity:.35}));
   const branches='子丑寅卯辰巳午未申酉戌亥';
   for(let i=0;i<12;i++){const a=i*Math.PI/6;const label=svg('text',{x:500+Math.sin(a)*475,y:510-Math.cos(a)*475,fill:'#d5b77b','text-anchor':'middle',style:'font:700 29px TourDisplay'});label.textContent=branches[i];view.append(label);}
   tilt.append(svg('ellipse',{cx:500,cy:500,rx:470,ry:170,stroke:'#93bbac','stroke-width':1,opacity:.55,transform:'rotate(-32 500 500)'}));
   tilt.append(svg('ellipse',{cx:500,cy:500,rx:470,ry:170,stroke:'#d5b77b','stroke-width':1,opacity:.5,transform:'rotate(32 500 500)'}));
   const star=svg('path',{class:'orbit-star',d:'M500 285L541 459L715 500L541 541L500 715L459 541L285 500L459 459Z',stroke:'#e5cb94','stroke-width':2,fill:'#d5b77b09'});
   view.append(turn);view.append(tilt);view.append(star);node.append(view);
 }
 document.querySelectorAll('.orbit').forEach(makeOrbit);
 film.captions.forEach(function(row,i){const box=document.createElement('div'),text=document.createElement('span');box.className='subtitle';box.id='caption-'+i;text.textContent=row.text;box.append(text);document.querySelector('#captions').append(box);});
 const tl=gsap.timeline({paused:true});
 tl.to('.aura',{x:-200,y:100,scale:1.15,duration:30,ease:'none'},0);
 tl.to('.jade-aura',{x:220,y:-80,duration:30,ease:'none'},0);
 tl.to('.film-progress>span',{scaleX:1,duration:30,ease:'none'},0);
 tl.to('.hook-orbit .orbit-turn',{rotation:120,duration:4*B,ease:'power1.in'},0);
 tl.from('.film-brand',{opacity:0,x:-25,duration:.26,ease:'power4.out'},.08);
 tl.from('.edition-label',{opacity:0,x:20,duration:.3,ease:'power3.out'},.12);
 tl.from('.hook-first',{opacity:0,y:72,scale:.94,duration:.32,ease:'expo.out'},.07);
 tl.from('.hook-stroke',{scaleX:0,duration:.32,ease:'power3.out'},.25);
 //A second question lands on the next beat while the first stays readable.

 tl.fromTo('.hook-second',{opacity:0,y:60,x:45},{opacity:1,y:0,x:0,duration:.28,ease:'expo.out'},.32);
 tl.to('.hook-ghost',{x:-110,rotation:-5,duration:4*B,ease:'none'},0);

 function transition(scene,index){
   const start=scene.start,id='#'+scene.id,old='#'+film.scenes[index-1].id,kind=scene.id==='brand'?'iris':scene.id==='outro'?'zoom':'swipe';
   tl.set(id,{zIndex:index+2},start);
   if(kind==='iris'){
     tl.set(id,{opacity:1},start);
     tl.fromTo(id,{clipPath:'circle(0% at 50% 50%)',scale:1.15},{clipPath:'circle(80% at 50% 50%)',scale:1,duration:.36,ease:'expo.out'},start);
     tl.set(old,{opacity:0},start+.36);
   }else if(kind==='zoom'){
     tl.to(old,{scale:1.13,opacity:0,duration:.25,ease:'power3.in'},start);
     tl.fromTo(id,{opacity:0,scale:1.3},{opacity:1,scale:1,duration:.39,ease:'expo.out'},start+.02);
   }else{
     const direction=index%2?1:-1;
     tl.to(old,{x:-direction*180,opacity:0,duration:.24,ease:'power3.in'},start);
     tl.fromTo(id,{opacity:1,x:direction*340,clipPath:direction>0?'inset(0 0 0 100%)':'inset(0 100% 0 0)'},{x:0,clipPath:'inset(0 0 0 0)',duration:.29,ease:'expo.out'},start+.015);
     tl.fromTo('.transition-band i',{x:direction>0?0:2500,opacity:.7},{x:direction>0?2500:0,opacity:0,duration:.34,ease:'power3.inOut'},start-.03);
   }
 }
 film.scenes.forEach(function(scene,index){
   const start=scene.start,id='#'+scene.id,at=start+.17;
   if(index)transition(scene,index);
   if(scene.id!=='hook'){
     tl.from(id+' .kicker',{opacity:0,y:15,duration:.28,ease:'power3.out'},at);
     const heading=document.querySelector(id+' h1,'+id+' h2');
     if(heading)tl.from(heading,{opacity:0,y:65,scale:.96,duration:.42,ease:'expo.out'},at+.05);
   }
   if(scene.id==='brand'){
     tl.from('.brand-orbit',{scale:.48,rotation:-32,opacity:0,duration:.72,ease:'expo.out'},start+.02);
     tl.to('.brand-orbit .orbit-turn',{rotation:80,duration:scene.duration,ease:'power2.out'},start);
     tl.from('.brand-line',{opacity:0,y:25,duration:.33,ease:'power2.out'},start+.53);
     tl.from('.brand-seal',{opacity:0,scale:1.7,rotation:20,duration:.25,ease:'power4.out'},start+.6);
   }
   if(scene.id==='chart'){
     tl.from('.chart-panel',{opacity:0,x:170,rotationY:-18,rotationZ:2,scale:.9,duration:.6,ease:'expo.out'},at);
     tl.fromTo('#chart-image',{x:-75,y:-20,scale:.82},{x:-250,y:-250,scale:1.18,duration:scene.duration-.5,ease:'power2.inOut'},at+.2);
     tl.from('.feature-line',{opacity:0,x:-22,duration:.32,ease:'sine.out'},at+.32);
     tl.from('.period-track span',{opacity:0,y:22,stagger:.1,duration:.3,ease:'power3.out'},at+.53);
     document.querySelectorAll('.period-track span').forEach(function(node,i){tl.to(node,{color:'#e5cb94',duration:.12},start+.6+i*.7);});
     tl.fromTo('.scan-ring',{opacity:0,scale:1.8},{opacity:.85,scale:1,duration:.48,ease:'power3.out'},start+4*B);
     tl.to('.scan-ring',{rotation:90,scale:1.12,duration:.65,ease:'sine.inOut'},start+5*B);
   }
   if(scene.id==='sources'){
     tl.from('.search-command',{opacity:0,x:110,scale:.95,duration:.4,ease:'expo.out'},at);
     const query='三方四正，有哪些依据？';tl.set('#search-typed',{textContent:''},start);
     for(let i=1;i<=query.length;i++)tl.set('#search-typed',{textContent:query.slice(0,i)},start+.27+i*.045);
     tl.from('.paper-course',{opacity:0,x:180,y:90,rotationY:-30,rotationZ:-18,duration:.55,ease:'power3.out'},start+2*B);
     tl.from('.paper-classic',{opacity:0,x:200,y:-90,rotationY:-20,rotationZ:20,duration:.55,ease:'expo.out'},start+3*B);
     tl.from('.evidence-chain span',{opacity:0,y:30,scale:.9,stagger:.2,duration:.3,ease:'power4.out'},start+4.5*B);
     tl.from('.evidence-chain i',{opacity:0,x:-22,stagger:.2,duration:.25,ease:'sine.out'},start+5*B);
     tl.to('.paper-course',{y:-16,rotationZ:-2,duration:1.7,ease:'sine.inOut'},start+3.8*B);
     tl.to('.paper-classic',{y:15,rotationZ:2,duration:1.35,ease:'sine.inOut'},start+4.5*B);
   }
   if(scene.id==='chat'){
     tl.from('.chat-panel',{opacity:0,x:160,rotationY:-12,duration:.45,ease:'expo.out'},at);
     tl.fromTo('#chat-image',{y:15,scale:1},{y:-260,scale:1.08,duration:scene.duration-.6,ease:'power2.inOut'},at+.2);
     tl.from('.question-prompt',{opacity:0,x:100,scale:.94,duration:.4,ease:'power3.out'},start+.5);
     tl.from('.citation-card',{opacity:0,y:70,rotationZ:3,scale:.9,duration:.35,ease:'expo.out'},start+4.5*B);
     tl.from('.feature-line',{opacity:0,x:-30,duration:.35,ease:'sine.out'},at+.35);
   }
   if(scene.id==='tools'){
     const cards=Array.from(document.querySelectorAll('.tool-card')),tabs=Array.from(document.querySelectorAll('.tool-index span'));
     cards.forEach(function(card,i){
       const t=start+i*2*B+.15;
       if(i)tl.to(cards[i-1],{opacity:0,y:-100,rotationX:9,duration:.22,ease:'power3.in'},t);
       tl.fromTo(card,{opacity:0,y:180,rotationX:-12,scale:.96},{opacity:1,y:0,rotationX:0,scale:1,duration:.3,ease:'expo.out'},t);
       tl.to(tabs[i],{color:'#e5cb94',borderColor:'#d5b77b',duration:.1},t);
       if(i)tl.to(tabs[i-1],{color:'#acb5b0',borderColor:'#2b383b',duration:.1},t);
     });
     tl.from('.tool-index',{opacity:0,y:18,duration:.32,ease:'sine.out'},at+.25);
     tl.from('.feature-line',{opacity:0,x:-20,duration:.25,ease:'power2.out'},at+.35);
   }
   if(scene.id==='setup'){
     tl.from('.setup-track',{opacity:0,y:75,rotationX:7,duration:.48,ease:'expo.out'},at+.1);
     tl.from('.setup-step',{opacity:0,y:30,stagger:.08,duration:.34,ease:'power3.out'},at+.25);
     tl.from('.setup-note',{opacity:0,y:20,duration:.3,ease:'sine.out'},at+.5);
     for(let i=0;i<4;i++){
       const t=start+.6+i*4*B;
       tl.to('.step-light',{x:i*430,duration:.24,ease:'power4.inOut'},t);
       tl.fromTo('.setup-step:nth-child('+(i+2)+') .step-number',{scale:1},{scale:1.14,duration:.22,yoyo:true,repeat:1,ease:'power2.inOut'},t+.02);
     }
   }
   if(scene.id==='entries'){
     tl.from('.entry-tags',{opacity:0,y:20,duration:.3,ease:'power3.out'},at+.1);
     const shots=Array.from(document.querySelectorAll('.entry-shot')),tabs=Array.from(document.querySelectorAll('.entry-tags span'));
     shots.forEach(function(shot,i){
       const t=start+.2+i*(8*B/3);
       if(i)tl.to(shots[i-1],{opacity:0,y:-100,duration:.19,ease:'power3.in'},t);
       tl.fromTo(shot,{opacity:0,y:85,scale:.96},{opacity:1,y:0,scale:1,duration:.27,ease:'expo.out'},t);
       tl.to(tabs[i],{color:'#e5cb94',borderColor:'#d5b77b',duration:.12},t);
       if(i)tl.to(tabs[i-1],{color:'#acb5b0',borderColor:'#2b383b',duration:.12},t);
     });
   }
   if(scene.id==='outro'){
     tl.from('.end-orbit',{opacity:0,scale:1.7,rotation:-32,duration:.65,ease:'expo.out'},start);
     tl.to('.end-orbit .orbit-turn',{rotation:40,duration:scene.duration,ease:'power1.out'},start);
     tl.from('.end-promise',{opacity:0,y:30,duration:.38,ease:'power3.out'},start+.48);
     tl.from('.end-rule',{scaleX:0,duration:.35,ease:'power4.out'},start+.65);
     tl.from('.end-link',{opacity:0,y:12,duration:.24,ease:'power3.out'},start+.17);
   }
 });
 film.captions.forEach(function(row,i){tl.to('#caption-'+i,{opacity:1,duration:.07,ease:'sine.out'},row.start);tl.to('#caption-'+i,{opacity:0,duration:.07,ease:'sine.in'},row.end-.07);});
 window.__timelines=window.__timelines||{};window.__timelines['ziwei-intro']=tl;
})();
