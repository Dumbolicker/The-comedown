"""M1 checks: safety warning, pause, settings and quality presets, key rebinding, gamepad (play and menus),
saved profile and records, reduced flashing, audio buses, parody names. Prints JSON; "errs" should be empty.

A fake standard-mapping gamepad is injected before the page loads (window.__pad), so the real Gamepad API code
path runs: navigator.getGamepads() -> padInput() -> gameplay input or menu navigation.
"""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = (ROOT / 'game' / 'index.standalone.html').as_uri()
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

FAKE_PAD = r"""
window.__pad={axes:[0,0,0,0],buttons:new Array(17).fill(0),on:false};
navigator.getGamepads=()=>[window.__pad.on?{id:'Test pad (STANDARD GAMEPAD)',index:0,connected:true,mapping:'standard',axes:window.__pad.axes.slice(),
  buttons:window.__pad.buttons.map(v=>({pressed:v>0.5,touched:v>0,value:v})),vibrationActuator:{playEffect:(t,o)=>{ (window.__rumbles=window.__rumbles||[]).push(o.strongMagnitude); return Promise.resolve('complete'); }}}:null];
"""

# helpers shared by the in-page checks
H = r"""
const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
const vis=id=>!document.getElementById(id).hidden;
const tap=(b,v=1)=>{ __pad.buttons[b]=v; padInput(1/60); __pad.buttons[b]=0; padInput(1/60); };
const px=(x,y)=>{ const d=ov.getImageData(Math.floor(x*DPR),Math.floor(y*DPR),1,1).data; return [d[0],d[1],d[2],d[3]]; };
"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None,
                                    args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 960, "height": 540})
        await ctx.add_init_script(FAKE_PAD)
        page = await ctx.new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        out = {}

        # 1. first visit: warning shows; choosing "reduce" saves the choice and turns on calm mode
        await page.goto(GAME, wait_until="load", timeout=180000); await page.wait_for_timeout(800)
        out['warning'] = await page.evaluate("()=>({shown:!document.getElementById('warn').hidden, titleBehind:!document.getElementById('title').hidden})")
        await page.click('#warnCalm')
        out['warning'].update(await page.evaluate("()=>({flash:SET.flash,shake:SET.shake,calmClass:document.body.classList.contains('calm'),saved:JSON.parse(localStorage.getItem('bt_settings')).warned})"))

        # 2. quality presets + persistence across a reload
        await page.click('#settingsBtn'); await page.click('#setBody .opt:has-text("Low")')
        q = await page.evaluate("()=>{ render(); render(); let lit=0; for(let i=0;i<8;i++) if(PL.c[i*4]+PL.c[i*4+1]+PL.c[i*4+2]>0) lit++; return {quality:SET.quality,scale:QUAL.scale,canvasW:glc.width,expectedW:Math.floor(innerWidth*DPR*0.6),shadowsOn:SH.on,lightsUsed:lit,lightsCap:QUAL.lights}; }")
        await page.click('#setDone')
        await page.reload(wait_until="load"); await page.wait_for_timeout(600)
        q.update(await page.evaluate("()=>({afterReload:SET.quality,canvasWAfterReload:glc.width,warnShownAgain:!document.getElementById('warn').hidden})"))
        await page.evaluate("()=>{ SET.quality='high'; Object.assign(SET,QUALITY.high); setChanged(); }")
        q['highCanvasW'] = await page.evaluate("glc.width")
        out['quality'] = q

        # 3. pause: Esc stops the clock, Esc again resumes; the on-screen II button pauses too
        await page.evaluate("()=>{ startGame(); G.life=60; }"); await page.wait_for_timeout(500)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(100)
        a = await page.evaluate("()=>({state:G.state,shown:!document.getElementById('pause').hidden,life:G.life})")
        await page.wait_for_timeout(1500)
        a['lifeAfter1500ms'] = await page.evaluate("G.life"); a['clockFrozen'] = a['life'] == a['lifeAfter1500ms']
        await page.wait_for_timeout(350); await page.keyboard.press('Escape'); await page.wait_for_timeout(100)
        a['afterSecondEsc'] = await page.evaluate("G.state")
        await page.click('#pauseBtn'); a['pauseButton'] = await page.evaluate("G.state")
        await page.click('#resumeBtn'); a['resumeButton'] = await page.evaluate("G.state")
        out['pause'] = a

        # 4. key rebinding with conflict swap, then the new key drives the action
        out['rebind'] = await page.evaluate("()=>{ " + H + r"""
          openSettings('pause'); sTab='ctrl'; renderSettings();
          const btn=[...document.querySelectorAll('#setBody .sr')].find(r=>r.querySelector('.sl').textContent.startsWith('Jump')).querySelector('.opt'); btn.click();
          const waiting=REBIND; dispatchEvent(new KeyboardEvent('keydown',{key:'e'})); const jumpNow=SET.binds.jump[0], grabNow=SET.binds.grab.slice();
          closeSettings(); G.state='play';
          dispatchEvent(new KeyboardEvent('keydown',{key:'e'})); const r1=gatherInput(1/60); dispatchEvent(new KeyboardEvent('keyup',{key:'e'}));
          dispatchEvent(new KeyboardEvent('keydown',{key:' '})); const r2=gatherInput(1/60); dispatchEvent(new KeyboardEvent('keyup',{key:' '}));
          const res={waiting,jumpKey:jumpNow,grabKeys:grabNow,eJumps:r1.jump,eGrabs:r1.grab,spaceGrabs:r2.grab,spaceJumps:r2.jump};
          SET.binds=JSON.parse(JSON.stringify(BIND_DEF)); saveSettings(); return res; }""")

        # 5. gamepad: menus (title -> start with A), play (stick moves, A jumps, Start pauses, B resumes), hints
        out['gamepad'] = await page.evaluate("async ()=>{ " + H + r"""
          const res={}; quitToTitle(); __pad.on=true; tap(13); res.lastInput=LAST_INPUT; const f=document.activeElement; res.focusedOnTitle=f&&f.id;
          if(document.activeElement.id!=='startBtn'){ padFocus(document.getElementById('startBtn')); }
          tap(0); res.startedWithA=G.state==='play'; G.life=60;
          const P=G.player, z0=P.pos.z, x0=P.pos.x, yaw0=G.cam.yaw;
          __pad.axes=[0,-1,0,0]; for(let k=0;k<45;k++){ const inp=gatherInput(1/60); update(1/60,inp); } __pad.axes=[0,0,0,0];
          res.movedMeters=+Math.hypot(P.pos.x-x0,P.pos.z-z0).toFixed(2);
          __pad.axes=[0,0,1,0]; for(let k=0;k<30;k++){ const inp=gatherInput(1/60); update(1/60,inp); } __pad.axes=[0,0,0,0];
          res.yawTurnedRad=+Math.abs(wrapA(G.cam.yaw-yaw0)).toFixed(2);
          step(30); __pad.buttons[0]=1; let inp=gatherInput(1/60); res.aGivesJump=inp.jump; update(1/60,inp); __pad.buttons[0]=0; gatherInput(1/60);
          for(let k=0;k<10;k++) update(1/60,I()); res.airborneAfterA=P.pos.y>0.2||!P.grounded;
          res.hint=document.getElementById('hint').textContent.slice(0,40);
          __pad.buttons[9]=1; gatherInput(1/60); __pad.buttons[9]=0; gatherInput(1/60); res.startPauses=G.state;
          await new Promise(r=>setTimeout(r,350)); tap(1); res.bResumes=G.state;
          G.shake=0; PAD.shake=0; G.shake=1.2; syncHUD(1/60); if(G.shake>PAD.shake+0.2) rumble(1,0.5,140); res.rumbleCalls=(window.__rumbles||[]).length;
          __pad.on=false; padInput(1/60); res.lastInputAfterUnplug=LAST_INPUT; return res; }""")

        # 6. profile: feats and runs are saved and survive a reload; records screen lists them
        await page.evaluate("()=>{ startGame(); G.life=40; G.score=4321; G.alive=95; award(F.FLYER); award(F.HYDRO); G.life=0; gameOver(); }")
        prof = await page.evaluate("()=>({runs:PROF.runs,best:PROF.best,feats:Object.keys(PROF.feats),goProg:document.getElementById('goProg').textContent})")
        await page.reload(wait_until="load"); await page.wait_for_timeout(600)
        prof.update(await page.evaluate("()=>{ openRecords(); const r={runsAfterReload:PROF.runs,featsAfterReload:Object.keys(PROF.feats).length,recordsText:document.getElementById('recStats').textContent.slice(0,120),unlockedRows:document.querySelectorAll('#recFeats .on').length}; closeRecords(); return r; }"))
        out['profile'] = prof

        # 7. reduced flashing: the bust strobe is a steady tint in calm mode and alternates in full mode
        out['flashing'] = await page.evaluate("()=>{ " + H + r"""
          startGame(); G.life=60; const r={}; const sample=()=>{ const a=[]; for(const t of [10.0,10.13,10.26,10.39]){ G.t=t; G.bustFlash=1.2; drawOverlay(); a.push(px(innerWidth/2,innerHeight/2).join(',')); } return a; };
          SET.flash='reduced'; r.calm=new Set(sample()).size; SET.flash='full'; r.full=new Set(sample()).size; G.bustFlash=0; SET.flash='reduced'; saveSettings();
          SET.shake=0; G.shake=2; cameraUpdate(1/60); const a=G.view.pos; cameraUpdate(1/60); r.noShakeWhenZero=Math.hypot(G.view.pos.x-a.x,G.view.pos.y-a.y)<0.05; SET.shake=0.25; return r; }""")

        # 8. quality governor, audio buses, names, wording
        out['misc'] = await page.evaluate("()=>{ " + H + r"""
          const r={}; SET.quality='auto'; setChanged(); startGame(); const w0=glc.width; for(let k=0;k<80;k++) qualityGovernor(1/20); r.autoDropped=glc.width<w0; r.dyn=QUAL.dyn;
          for(let k=0;k<1000;k++) qualityGovernor(1/90); r.autoRecovered=QUAL.dyn===1;
          unlock(); r.buses=!!(SFXB&&VOXB&&MUSB); SET.master=0.5; applyAudio(); r.masterGain=+MASTER.gain.value.toFixed(3); SET.master=0.8; applyAudio();
          r.names=[SUB('xanax').name,SUB('henny').name]; const txt=document.body.innerText+' '+[...document.querySelectorAll('#legend .row,.disc,#implants')].map(e=>e.textContent).join(' ')+' '+CYBER.map(c=>c.desc).join(' ');
          r.oldNamesVisible=/Goat Simulator/i.test(txt); r.idleUpdateMs=(()=>{ const t0=performance.now(); step(240,()=>I({my:1})); return +((performance.now()-t0)/240).toFixed(3); })(); return r; }""")
        out['errs'] = errs[:8]
        await b.close()
    print(json.dumps(out, indent=1))

asyncio.run(main())
