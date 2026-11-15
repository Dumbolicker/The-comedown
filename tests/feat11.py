"""Batch 7 checks: original substance names, the wall rule (only explosions, HENNY's juggernaut or a dragon break
walls), six new creatures, aim assist, hit-stop, mercy stash, and the new shading compiling and rendering.
Prints JSON; "errs" should be empty."""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  try{ startGame(); G.life=200; const P=G.player;
    out.names=[SUB('xanax').name,SUB('henny').name];
    // ---- the wall rule, on a condemned house
    const it=W.interiors.find(q=>q.cut&&W.condemned.has(q.bld)&&BRK_BY.get(q.bld).some(b=>b.mat==='wood'&&!b.roof)), L=BRK_BY.get(it.bld).filter(b=>b.mat==='wood'&&!b.roof&&b.alive);
    const n3=V(0,0,1), r={};
    r.plainTackle=bodyHitsPanel(L[0].id,14,n3,true); r.plainWallAlive=L[0].alive; r.hintShown=(G.wallHintT||0)>G.t;
    addEffect(SUB('henny')); for(let k=0;k<300&&!G.mods.jugg;k++) step(1); r.juggOn=!!G.mods.jugg; r.juggBreaks=bodyHitsPanel(L[1].id,14,n3,true)||!L[1].alive;
    G.effects=[]; step(3); transform('dragon'); step(3); r.dragonBreaks=bodyHitsPanel(L[2].id,14,n3,true)||!L[2].alive; untransform(); step(3);
    const tw=L[0], tc=boxCenter(tw.s), crate=makeProp({kind:'crate',x:tc.x,z:tc.z+2.2,yaw:0,y:0}); crate.pos.y=1; crate.vel=V(0,0,-16); crate.asleep=false; crate.thrown=1; G.props.push(crate); const hp0=tw.hp; step(30);
    r.thrownCrateNoDamage=tw.alive&&tw.hp===hp0;
    const L3=L.find(b=>b.alive&&b!==tw); explode(boxCenter(L3.s)); step(10); r.explosionBreaks=!L3.alive; out.wallRule=r;
    // ---- creatures
    const NEW=['tiger','bear','pig','frog','rhino','llama'], cr={total:Object.keys(FORMS).length,rendered:[]};
    for(const k of NEW){ transform(k); step(20,()=>I({my:1})); render(); cr.rendered.push(k+(QSPEC[k]?'':'(no spec)')); untransform(); step(2); }
    out.creatures=cr; out.creatureChance='15% per dose (static check in tests/feat10.py)';
    // ---- aim assist + hit-stop
    if(P.ragdoll) getUp(P,G.evs); P.pos=V(-HALF+30,0,-HALF+ROAD/2); P.yaw=0; P.vel=V(); step(5); const f=fwd(P.yaw), side=V(f.z,0,-f.x);
    const npc=G.npcs.find(n=>n.alive&&n.kind!=='cop'); npc.pos=vadd(P.pos,vadd(vmul(f,3),vmul(side,1.2))); npc.state='idle';
    const pickT=assistPick(f,4.5,0.62), far=G.npcs.find(n=>n.alive&&n!==npc&&n.kind!=='cop'); far.pos=vadd(P.pos,vadd(vmul(fwd(G.cam.yaw),11),vmul(V(fwd(G.cam.yaw).z,0,-fwd(G.cam.yaw).x),1.5))); far.state='idle';
    const thr=assistThrow(19); out.aimAssist={tacklePicksNpc:pickT===npc,throwSolution:!!thr,settingOn:SET.assist!==false};
    G.hitStop=0; knockNpcG(G.npcs.indexOf(npc),V(4,3,0),true,false,''); out.hitStop=+(G.hitStop||0).toFixed(3);
    // ---- mercy stash
    G.stashes.length=0; G.life=5; G.mercyT=0; step(2); out.mercyStash={spawned:G.stashes.length>0,count:G.stats.mercy||0};
    let t0=performance.now(); for(let k=0;k<10;k++) render(); out.renderMs=+((performance.now()-t0)/10).toFixed(2);
    G.life=200; t0=performance.now(); step(240,()=>I({my:0.4})); out.idleUpdateMs=+((performance.now()-t0)/240).toFixed(3);
  }catch(e){ out.errs.push(String(e)+' | '+(e.stack||'').split('\n').slice(0,4).join(' | ')); }
  return out; }
"""

async def main():
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
        r = await page.evaluate(JS); r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
