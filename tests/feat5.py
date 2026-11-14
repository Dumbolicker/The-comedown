"""Demolition, interiors and casino checks, with numbers.

Runs the game twice in headless Chromium: once with Rapier (served from the pinned, hash-checked copy in
.refcache/vendor, fetched with `python tests/vendor_rapier.py`) and once with Rapier blocked, to prove the
built-in fallback. Prints JSON; every section should be free of errors ("errs": []).
"""
import asyncio, json, os, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  try{ startGame(); G.life=900; const P=G.player; out.rapier=RUB.state; out.how=RUB.how;
    out.world={panels:BRK.length,glass:W.glass.length,slots:W.slotsB.length,interiors:W.interiors.length,lights:W.lights.length,solids:W.solids.length};
    // ---- idle cost (no rubble yet)
    let t0=performance.now(); step(300,()=>I({my:1,sprint:true,lookX:0.01})); out.idleUpdateMs=+((performance.now()-t0)/300).toFixed(3);
    // ---- free fall: one rubble block dropped 10 m onto open road, sampled every step
    if(RUB.ready){ const x=0, z=-HALF+ROAD/2+0.0, y0=10.5; P.pos=V(x+30,0,z); spawnChunk(V(x,y0,z),V(0.25,0.25,0.25),QI,V(),V(),'brick',[1,0,0],false);
      const r=RUB.chunks[RUB.chunks.length-1], pts=[]; let t=0, land=-1;
      for(let k=0;k<1200;k++){ RUB.world.timestep=1/240; RUB.world.gravity={x:0,y:-9.81,z:0}; RUB.world.step(RUB.eq); t+=1/240; const y=r.body.translation().y; if(y>0.6) pts.push([t,y]); else if(land<0) land=t; if(land>0) break; }
      const n=pts.length; let sx=0,sy=0,sxx=0,sxy=0,sx3=0,sx4=0,sx2y=0; for(const [a,b] of pts){ sx+=a; sy+=b; sxx+=a*a; sxy+=a*b; sx3+=a*a*a; sx4+=a*a*a*a; sx2y+=a*a*b; }
      const M=[[n,sx,sxx],[sx,sxx,sx3],[sxx,sx3,sx4]], R=[sy,sxy,sx2y]; for(let c=0;c<3;c++){ for(let rr=c+1;rr<3;rr++){ const f=M[rr][c]/M[c][c]; for(let k=c;k<3;k++) M[rr][k]-=f*M[c][k]; R[rr]-=f*R[c]; } }
      const cc=R[2]/M[2][2]; const g=-2*cc, drop=y0-0.25-0.0, tTheory=Math.sqrt(2*(y0-0.25)/9.81);
      out.freefall={samples:n,g_measured:+g.toFixed(4),g_expected:9.81,error_pct:+((g/9.81-1)*100).toFixed(3),landing_s:+land.toFixed(3),landing_theory_s:+tTheory.toFixed(3)};
      rubRemove(r); }
    // ---- horn charge through a house wall (front wall, lower course)
    if(P.ragdoll) getUp(P,G.evs); transform('minotaur'); P.formT=999;
    const pick1=BRK.find(b=>b.alive&&b.mat==='wood'&&!b.roof&&b.s.y0<0.1&&(b.s.z1-b.s.z0)<0.3&&(b.s.x1-b.s.x0)>1.2&&b.bld>0);
    const s=pick1.s, c=boxCenter(s), it=W.interiors.find(q=>q.bld===pick1.bld), outside=(c.z<(it.z0+it.z1)/2)?-1:1;
    P.pos=V(c.x,0,c.z+outside*6); P.vel=V(); P.yaw=outside>0?PI:0; G.cam.yaw=P.yaw; step(5);
    let broken0=BRK.filter(b=>!b.alive).length; step(1,()=>I({charge:true})); step(120);
    out.charge={panelsBroken:BRK.filter(b=>!b.alive).length-broken0,rubbleBodies:RUB.chunks.length+G.props.filter(o=>o.alive&&o.k==='chunk').length,throughWall:!!G.inside||Math.sign(P.pos.z-c.z)!==outside};
    t0=performance.now(); step(120,()=>I({my:0.4,sprint:true})); out.activeRubbleUpdateMs=+((performance.now()-t0)/120).toFixed(3);
    // ---- structure: two lower panels gone -> uppers held by neighbours; five gone -> the middle of the span drops
    const wall=[...BRK_BY.values()].map(list=>list.filter(b=>b.alive&&!b.roof&&b.mat==='wood'&&b.s.y0<0.06&&(b.s.x1-b.s.x0)>0.5&&(b.s.z1-b.s.z0)<0.3)).find(l=>l.length>=6&&l[0].bld!==pick1.bld);
    wall.sort((a,b)=>a.s.x0-b.s.x0); const zz=wall[0].s.z0, row=wall.filter(b=>Math.abs(b.s.z0-zz)<0.01);
    const upper=b=>BRK.find(u=>u.alive&&u.bld===b.bld&&Math.abs(u.s.y0-b.s.y1)<0.06&&Math.abs(u.s.x0-b.s.x0)<0.01&&Math.abs(u.s.z0-b.s.z0)<0.01);
    const ups=row.map(upper); hitBrk(row[1].id,9999); hitBrk(row[2].id,9999); step(40);
    out.lintel={upperAliveAfter2:ups.slice(1,3).filter(u=>u&&u.alive).length,of:ups.slice(1,3).filter(Boolean).length};
    // ---- roof cave-in: take out every top-course panel under one roof half
    const roof=BRK.find(b=>b.roof&&b.alive&&b.bld!==pick1.bld&&b.bld!==wall[0].bld&&b.s.ramp); const sc0=G.score;
    for(const i of roof.sup) hitBrk(i,9999); step(150);
    out.roof={fell:!roof.alive,slabs:RUB.slabs.length,feat:G.feats[F_ROOF],cavein:G.score>sc0};
    // ---- explosion next to an untouched house
    const tgt=[...BRK_BY.keys()].find(k=>k>0&&BRK_BY.get(k).every(b=>b.alive)&&BRK_BY.get(k)[0].mat==='wood'); const hb=BRK_BY.get(tgt)[0].s;
    const blastAt=V(hb.x0-1.2,0.5,(hb.z0+hb.z1)/2); const before=BRK_BY.get(tgt).filter(b=>!b.alive).length; explode(blastAt); step(30);
    out.blast={panelsBroken:BRK_BY.get(tgt).filter(b=>!b.alive).length-before};
    // ---- interior camera: stand in the middle of a house
    const ih=W.interiors.find(q=>q.cut&&BRK_BY.get(q.bld).every(b=>b.alive)); if(P.ragdoll) getUp(P,G.evs); untransform();
    P.pos=V((ih.x0+ih.x1)/2,0,(ih.z0+ih.z1)/2); P.vel=V(); step(90); render();
    out.interior={inside:!!G.inside,cutBld:G.cutBld===ih.bld,camIn:+G.camIn.toFixed(2),roofInShadowOnlyBatch:SHO.wedge.n+SHO.cube.n>=1};
    // ---- casino: slots proximity, clock gag, smash a machine, collect coins
    const m=W.slotsB.find(b=>b.alive&&b.yaw===0), mc=boxCenter(m.s); P.pos=V(mc.x,0,mc.z+0.75); P.vel=V(); P.yaw=PI; step(5); syncHUD(1/60);
    out.casino={nearSlots:G.nearSlots,clockText:document.getElementById('clock').textContent,label:document.getElementById('clockLbl').textContent};
    step(1,()=>I({grab:true})); out.casino.opened=G.state==='slots'; closeSlots();
    const d0=G.dollas; hitBrk(m.id,9999,mc,V(0,0,1)); const coins=G.props.filter(o=>o.alive&&o.k==='coin').length; step(60);
    for(const o of G.props.filter(o=>o.alive&&o.k==='coin')){ P.pos=V(o.pos.x,0,o.pos.z); step(2); }
    out.casino.coinsSpilled=coins; out.casino.dollasFromCoins=G.dollas-d0; out.casino.featBeatTheHouse=G.feats[F_SLOT];
    // ---- render with everything going on
    t0=performance.now(); for(let k=0;k<10;k++) render(); out.renderMs=+((performance.now()-t0)/10).toFixed(2);
    out.wreckFeat=G.feats[F_WRECK]; out.panelsBrokenTotal=BRK.filter(b=>!b.alive).length;
  }catch(e){ out.errs.push(String(e)+' | '+(e.stack||'').split('\n').slice(0,4).join(' | ')); }
  return out; }
"""

async def run(rapier):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None,
                                    args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await (await b.new_context(viewport={"width": 960, "height": 540})).new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if rapier:
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded")
        for _ in range(60):
            if await page.evaluate("RUB.state") != 'loading': break
            await page.wait_for_timeout(250)
        r = await page.evaluate(JS); r['pageerrors'] = errs[:6]; await b.close(); return r

async def main():
    if not VENDOR.exists():
        sys.exit("missing " + str(VENDOR) + ": run python tests/vendor_rapier.py first")
    res = {"with_rapier": await run(True), "builtin_fallback": await run(False)}
    print(json.dumps(res, indent=1))

asyncio.run(main())
