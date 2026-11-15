"""M4 checks: chrome bank (deposit and payout), feat-unlocked outfit items, daily challenges (deterministic per day,
rewards), first-run tutorial, procedural music running, distance falloff for sounds. Prints JSON; "errs" empty."""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
async () => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  try{ // ---- tutorial on a first run
    startGame(); G.life=900; const P=G.player; out.tutorial={startsOnFirstRun:!!G.tut,shown:!document.getElementById('tut').hidden,firstText:document.getElementById('tut').textContent.slice(0,40)};
    G.cam.yaw=P.yaw; step(60,()=>I({my:1})); const s1=G.tut&&G.tut.step;
    step(2,k=>I({jump:k===0,jumpHeld:true})); step(40); const s2=G.tut&&G.tut.step;
    LAST_INP=I({tackle:true}); step(1,()=>I({tackle:true})); LAST_INP=null; step(30); const s3=G.tut&&G.tut.step;
    const f=fwd(P.yaw), o=makeProp({kind:'crate',x:P.pos.x+f.x*1.0,z:P.pos.z+f.z*1.0,yaw:0,y:0}); G.props.push(o); step(3);
    step(1,()=>I({grab:true,grabHeld:true})); step(5,()=>I({grabHeld:true})); const held=P.held>=0, s4=G.tut&&G.tut.step;
    LAST_INP=I({tackle:true}); step(1,()=>I({tackle:true})); LAST_INP=null; step(20); const s5=G.tut&&G.tut.step;
    G.stats.doses=1; step(2); out.tutorial.stepsSeen=[s1,s2,s3,s4,s5]; out.tutorial.grabbed=held; out.tutorial.finished=!G.tut&&PROF.tut===true;
    // ---- chrome bank: 10% of dollas in, up to 250 out at the next start
    G.dollas=1000; G.score=500; G.alive=60; G.life=0; gameOver(); const bank=PROF.chrome; startGame(); out.chrome={afterRun:bank,startDollas:G.dollas,bankAfterPayout:PROF.chrome,goProg:document.getElementById('goProg').textContent.slice(-48)};
    // ---- unlocks: the pirate hat needs High Roller; colors need their feats
    initUnlocks(); const before=isLocked('hat','pirate'), lockedCols=CLOTH_COLS.length-CLOTH_BASE; award(F.ROLLER); const after=isLocked('hat','pirate');
    G.state='title'; G.attract=true; openCustom(); cTab='fit'; renderCustomTab(); const chips=[...document.querySelectorAll('#cBody .chip')], pir=chips.find(c=>c.textContent.includes('Pirate'));
    const disabledSw=[...document.querySelectorAll('#cBody .sw2')].filter(b=>b.disabled).length; closeCustom();
    out.unlocks={pirateLockedBefore:before,pirateLockedAfter:after,pirateChipEnabled:!!pir&&!pir.disabled,extraColors:lockedCols,lockedSwatchesShown:disabledSw};
    // ---- daily challenges: same three all day, rewards paid once
    startGame(); const a=dailyList().map(c=>c.txt).join('|'), b=dailyList().map(c=>c.txt).join('|'); const c0=PROF.chrome;
    Object.assign(G.stats,{wrecked:1e6,roofs:1e6,tackled:1e6,fires:1e6,doses:1e6,booms:1e6,alarms:1e6,drones:1e6}); G.score=1e8; G.alive=1e5; G.feats[F_WATER]=true; dailyCheck(); dailyCheck();
    out.daily={items:dailyList().map(c=>c.txt),stable:a===b,allDone:PROF.daily.items.every(i=>i.done),chromeReward:PROF.chrome-c0,titleBox:document.getElementById('dailyBox').textContent.slice(0,40)};
    // ---- music + ambience on the music bus; world sounds fall off with distance
    unlock(); await new Promise(r=>setTimeout(r,1200)); out.music={on:MUS.on,stepsScheduled:MUS.step,ctx:AC&&AC.state};
    const g1=AC.createGain(), g2=AC.createGain(); const near=sfxOut(g1,vadd(G.view.pos,V(1,0,0))), far=sfxOut(g2,vadd(G.view.pos,V(60,0,0))); g1.disconnect(); g2.disconnect();
    out.falloff={nearGain:+near.toFixed(2),at60m:+far.toFixed(3)};
    let t0=performance.now(); step(240,()=>I({my:0.4})); out.idleUpdateMs=+((performance.now()-t0)/240).toFixed(3);
  }catch(e){ out.errs.push(String(e)+' | '+(e.stack||'').split('\n').slice(0,4).join(' | ')); }
  return out; }
"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"])
        page = await (await b.new_context(viewport={"width": 960, "height": 540})).new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded")
        for _ in range(60):
            if await page.evaluate("RUB.state") != 'loading': break
            await page.wait_for_timeout(250)
        r = await page.evaluate(JS); r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
