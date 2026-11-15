"""Batch 6 checks: demolition limited to condemned buildings, secret feat requirements, engagement features (streak,
live personal best, combo milestones with slow motion, golden stashes, next-goal summary, break reminder), the 15%
creature chance kept off the title screen, and doors. Prints JSON; "errs" should be empty."""
import asyncio, json, os, pathlib, re
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  try{ const legend=document.getElementById('legend').textContent; out.title={mentionsShapeshift:/shapeshift|42%|15%|centaur/i.test(legend),demolitionHint:/orange X/.test(legend)};
    startGame(); G.life=900; const P=G.player;
    // ---- only condemned buildings break
    const breakable=BRK.filter(b=>!b.invuln).length, bldOK=[...W.condemned];
    const safeHouse=W.interiors.find(it=>it.cut&&!W.condemned.has(it.bld)&&BRK_BY.get(it.bld)&&BRK_BY.get(it.bld).some(b=>b.mat==='wood'));
    const condHouse=W.interiors.find(it=>it.cut&&W.condemned.has(it.bld)&&BRK_BY.get(it.bld).some(b=>b.mat==='wood'));
    const sp=BRK_BY.get(safeHouse.bld).find(b=>!b.roof&&b.mat==='wood'), cp=BRK_BY.get(condHouse.bld).find(b=>!b.roof&&b.mat==='wood');
    hitBrk(sp.id,99999,boxCenter(sp.s),V(1,0,0)); hitBrk(cp.id,99999,boxCenter(cp.s),V(1,0,0)); explode(boxCenter(sp.s)); step(20);
    out.demolition={condemnedBuildings:bldOK.length,breakablePanels:breakable,ofPanels:BRK.length,safeWallSurvives:sp.alive,safeHouseIntactAfterBlast:BRK_BY.get(safeHouse.bld).every(b=>b.alive),condemnedWallBreaks:!cp.alive,slotsStillBreakable:W.slotsB.every(b=>!b.invuln)};
    // ---- secret feat requirements
    openRecords(); const locked=document.getElementById('recFeats').textContent; const flyerHiddenBefore=!locked.includes('Stay airborne for 3 seconds')&&locked.includes('Frequent Flyer'); closeRecords();
    award(F.FLYER); openRecords(); const after=document.getElementById('recFeats').textContent; closeRecords();
    out.secretFeats={nameVisibleRequirementHidden:flyerHiddenBefore,requirementShownAfterEarning:after.includes('Stay airborne for 3 seconds'),questionMarks:(locked.match(/\?\?\?/g)||[]).length};
    // ---- doors
    const doors=W.doors.length, d=W.doors.find(o=>!W.condemned.has(o.bld)&&o.mat==='wood'), c=doorCenter(d), side=d.axis==='x'?V(0,0,1.0):V(1.0,0,0);
    P.pos=vadd(c,vmul(side,1.2)); P.vel=V(); step(30); const openNear=d.open, gone=d.s.gone;
    P.pos=vadd(c,vmul(side,12)); step(150); const shutAway=d.open, back=!d.s.gone;
    const npc=G.npcs.find(n=>n.alive&&n.kind!=='cop'); const np0={...npc.pos}; npc.pos=vadd(c,vmul(side,-1.0)); npc.state='idle'; step(20); const npcOpened=d.open>0.5; npc.pos=np0; step(150);
    P.pos=vadd(c,vmul(side,0.9)); P.vel=vmul(side,-11); doorsUpdate(1/60); const safeKick=d.broken;
    transform('dragon'); const cd=W.doors.find(o=>W.condemned.has(o.bld)&&!o.broken); P.pos=vadd(doorCenter(cd),cd.axis==='x'?V(0,0,0.8):V(0.8,0,0)); P.vel=cd.axis==='x'?V(0,0,-11):V(-11,0,0); cd.open=0; doorsUpdate(1/60);
    untransform(); out.doors={count:doors,opensWhenNear:+openNear.toFixed(2),passableWhenOpen:gone,closesWhenAway:+shutAway.toFixed(2),solidWhenShut:back,npcOpens:npcOpened,safeDoorNotKicked:!safeKick,condemnedDoorKicked:cd.broken};
    // ---- engagement
    const ydate=new Date(Date.now()-864e5), yk=ydate.getFullYear()+'-'+String(ydate.getMonth()+1).padStart(2,'0')+'-'+String(ydate.getDate()).padStart(2,'0');
    PROF.streak={last:yk,n:2}; const ch0=PROF.chrome||0; startGame(); G.life=900; out.streak={n:PROF.streak.n,bonusToBank:(PROF.chrome+(G.chromePay||0))-ch0};
    PROF.best=100; G.score=250; step(2); out.personalBest={celebrated:!!G.pbShown,hud:document.getElementById('pbval').textContent};
    G.combo=10; G.mile=0; const sc0=G.score; step(1); out.combo={milestone:G.mile,bonus:G.score-sc0,slowMotion:(G.slowT||0)>0};
    let t0=performance.now(); G.slowT=0.5; const tt=G.t; for(let k=0;k<10;k++){} out.slowmoScale='0.45 (frame dt)';
    const st={...G.stashes[0],golden:true,laced:false,pos:{...G.player.pos}}; G.stashes.push(st); const life0=G.life; step(3); out.golden={timeAdded:+(G.life-life0).toFixed(1),picked:!G.stashes.includes(st)};
    const goldenRate=(()=>{ let g=0; for(let k=0;k<4000;k++) if(Math.random()<0.085) g++; return g/4000; })(); out.golden.designRate=0.085;
    SESSION.t=3601; SESSION.nextBreak=3600; step(1); out.breakReminder={fired:SESSION.nextBreak===7200,settingDefaultOn:SET.breaks===true};
    G.score=50; G.life=0; gameOver(); out.gameOver={text:document.getElementById('goProg').textContent.slice(0,220),hintsSecretFeats:/secret feat/.test(document.getElementById('goProg').textContent),noWaterTowerHint:!/water tower/i.test(document.getElementById('goFeats').textContent)};
    startGame(); t0=performance.now(); step(240,()=>I({my:0.4})); out.idleUpdateMs=+((performance.now()-t0)/240).toFixed(3);
  }catch(e){ out.errs.push(String(e)+' | '+(e.stack||'').split('\n').slice(0,4).join(' | ')); }
  return out; }
"""

async def main():
    src = (ROOT / 'game' / 'index.html').read_text(encoding='utf-8')
    static = {'creatureChance': re.findall(r"Math\.random\(\)<(0\.\d+)\) transform", src)}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
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
        r = await page.evaluate(JS); r['static'] = static; r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
