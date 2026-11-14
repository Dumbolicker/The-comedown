import asyncio, json, numpy as np
from playwright.async_api import async_playwright
import pathlib, os
GAME_URI=(pathlib.Path(__file__).resolve().parent.parent/'game'/'index.standalone.html').as_uri()
JS = r"""
async () => { const out={errs:[]}; const I=(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++){ update(1/60,f?f(k):I()); if(k%15===0){ FDT=1/60; windUpdate(G.t); render(); drawOverlay(); if(G.state!=='title') syncHUD(1/60); } } };
  try{
    // ---- customization on the title screen
    $('customBtn').click(); out.customOpen={custom:!!G.custom,shown:!$('custom').hidden,rows:$('cBody').children.length};
    let combos=0; for(const hair of LOOK_OPTS.hair) for(const top of LOOK_OPTS.top){ CUSTOM.hair=hair[0]; CUSTOM.top=top[0]; CUSTOM.hat=pick(LOOK_OPTS.hat)[0]; CUSTOM.face=pick(LOOK_OPTS.face)[0]; CUSTOM.eyes=pick(LOOK_OPTS.eyes)[0]; CUSTOM.pants=pick(LOOK_OPTS.pants)[0]; applyLook(); G.player.cloth={}; step(3); combos++; }
    for(const tab of ['hair','fit','body']){ document.querySelector(`.ctab[data-tab="${tab}"]`).click(); out['tab_'+tab]=$('cBody').children.length; }
    CUSTOM.height=1.14; CUSTOM.build=1.45; applyLook(); step(10); out.custom={combos,playerY:+G.player.pos.y.toFixed(2),viewOK:!!G.view,PH:+PH.toFixed(2)};
    $('cRandom').click(); out.randomized=JSON.stringify(CUSTOM).length>20; $('cDone').click(); out.customClosed={custom:!!G.custom,title:!$('title').hidden};
    // ---- ripperdoc
    startGame(); G.life=900; const P=G.player; out.doc={exists:!!W.doc,pos:W.doc&&[+W.doc.pos.x.toFixed(1),+W.doc.pos.z.toFixed(1)],spawnDist:+hlen(vsub(W.doc.pos,W.spawn)).toFixed(1)};
    P.pos=vadd(W.doc.pos,V(0,0,1.8)); P.vel=V(); step(5); syncHUD(1/60); out.near={nearDoc:G.nearDoc,prompt:$('promptmsg').textContent,grabLabel:$('bGrab').textContent};
    step(1,()=>I({grab:true})); out.shop={state:G.state,cards:$('implants').children.length,line:$('docLine').textContent};
    G.dollas=99999; for(const c of CYBER) buyCyber(c); buyCyber(KIDNEY); out.bought={n:Object.keys(G.cyber).length,dollas:G.dollas,chromeFeat:G.feats[F_CHROME]};
    $('leaveDoc').click(); out.left=G.state;
    const m=mods(); out.drain=+m.drain.toFixed(3);
    const life0=G.life; pickup({sub:SUB('coke'),pos:{...P.pos},life:9,seed:1}); out.cokeGain=+(G.life-life0).toFixed(1); out.useMax=+P.useMax.toFixed(2);
    step(120); G.stashes.forEach(s=>s.laced=true); step(20); out.lacedRing=true;
    G.life=2.5; step(5); out.molar={life:+G.life.toFixed(1),left:!!G.cyber.molar};
    G.life=900; P.poopCd=0; step(1,()=>I({poop:true})); step(60); out.gut={cd:+P.poopCd.toFixed(2),size:P.poop&&+P.poop.size.toFixed(2)};
    // chrome renders on the player
    step(30);
    // ---- deep-fried voice rendered offline, measured like the reference clip
    const sr=22050, oc=new OfflineAudioContext(1,sr*4,sr); const dur=friedSpeak('Hey! What are you doing with that poop? Somebody call somebody!',120,1,1,0,oc,oc.destination);
    const buf=await oc.startRendering(); const x=buf.getChannelData(0); let n=Math.min(x.length,Math.ceil((dur+0.3)*sr)); out.voice={dur:+dur.toFixed(2),samples:Array.from(x.slice(0,n)).map(v=>Math.round(v*10000)/10000)};
    // live voice path
    unlock(); say(G.npcs[0],'Did you just see that?!',2); playerSay('Yo! What is up!',2,true); step(30); out.voiceMode=VOICE.mode;
  }catch(e){ out.errs.push(String(e)+' | '+(e.stack||'').split('\n').slice(0,4).join(' | ')); }
  return out; }
"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist","--autoplay-policy=no-user-gesture-required"])
        ctx=await b.new_context(viewport={"width":960,"height":540}); page=await ctx.new_page(); errs=[]
        page.on("pageerror", lambda e: errs.append(str(e))); page.on("console", lambda m: errs.append('console:'+m.text) if m.type=='error' else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        await page.goto(GAME_URI, wait_until="domcontentloaded"); await page.wait_for_timeout(2500)
        r=await page.evaluate(JS); v=r.pop('voice',None); print(json.dumps(r,indent=1)); print("pageerrors:",errs[:6])
        if v:
            x=np.array(v['samples'],dtype=np.float64); sr=22050; rms=np.sqrt((x**2).mean()); pk=np.abs(x).max()
            X=np.abs(np.fft.rfft(x))**2; f=np.fft.rfftfreq(len(x),1/sr); tot=X.sum()
            print('fried voice: dur %.2fs peak %.3f rms %.1f dBFS crest %.1f dB, >=95%% of peak: %.1f%%'%(v['dur'],pk,20*np.log10(rms),20*np.log10(pk/rms),100*(np.abs(x)>=0.95*pk).mean()))
            for lo,hi in [(0,150),(150,500),(500,2000),(2000,5000),(5000,11025)]: print('  band %5d-%5d Hz: %5.1f%%'%(lo,hi,100*X[(f>=lo)&(f<hi)].sum()/tot))
        await b.close()
asyncio.run(main())
