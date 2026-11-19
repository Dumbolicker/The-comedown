"""M3 checks: navigation grid + A*, cops routing around buildings, people leaving buildings by the door, the police
drone (spawn, zap, radio, shoot-down), and the lobby tower stairs. Prints JSON; "errs" should be empty."""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none&wreck=all'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  try{ startGame(); G.life=900; const P=G.player;
    // ---- grid build and A* cost
    let t0=performance.now(); navBuild(); out.navBuildMs=+(performance.now()-t0).toFixed(2); out.navCells=NAV.n*NAV.n; out.blockedPct=+(100*NAV.blk.reduce((a,b)=>a+b,0)/NAV.blk.length).toFixed(1);
    const it=W.interiors.find(q=>q.cut&&BRK_BY.get(q.bld)&&BRK_BY.get(q.bld)[0].mat==='wood'), mid=V((it.x0+it.x1)/2,0,(it.z0+it.z1)/2);
    const outside=V(mid.x,0,it.z1+7), outside2=V(mid.x,0,it.z0-7);
    t0=performance.now(); const path=navPath(outside,mid); const ms=performance.now()-t0; let ok=!!path&&path.length>0, len=0, prev=outside;
    if(ok){ for(const q of path){ if(!navClear(prev,q)) ok=false; len+=Math.hypot(q.x-prev.x,q.z-prev.z); prev=q; } }
    out.pathIntoHouse={found:ok,waypoints:path?path.length:0,lengthM:+len.toFixed(1),straightM:+Math.hypot(mid.x-outside.x,mid.z-outside.z).toFixed(1),endsInside:ok&&Math.hypot(prev.x-mid.x,prev.z-mid.z)<1,ms:+ms.toFixed(2)};
    const ts=[]; for(let k=0;k<20;k++){ const a=V(rand(-HALF+10,HALF-10),0,rand(-HALF+10,HALF-10)), b=V(rand(-HALF+10,HALF-10),0,rand(-HALF+10,HALF-10)); t0=performance.now(); navPath(a,b); ts.push(performance.now()-t0); }
    ts.sort((a,b)=>a-b); out.randomPaths={n:20,medianMs:+ts[10].toFixed(2),maxMs:+ts[19].toFixed(2)};
    // ---- a cop on the far side of a house must route round it (no line of sight)
    for(let k=0;k<6;k++) spawnCop(); const cop=G.npcs.find(n=>n.kind==='cop'&&n.alive); G.heat=3;
    P.pos=V(outside.x,0,outside.z); P.vel=V(); cop.pos=V(outside2.x,0,outside2.z); cop.state='chase'; cop.seeT=0; cop.lastSeen={...P.pos}; cop.losT=0;
    const d0=Math.hypot(cop.pos.x-P.pos.x,cop.pos.z-P.pos.z); let minD=d0; for(let k=0;k<60*8;k++){ update(1/60,I()); P.pos=V(outside.x,0,outside.z); P.vel=V(); cop.seeT=0; cop.lastSeen={...P.pos}; minD=Math.min(minD,Math.hypot(cop.pos.x-P.pos.x,cop.pos.z-P.pos.z)); if(G.state!=='play') break; }
    out.copRouting={startM:+d0.toFixed(1),closestM:+minD.toFixed(1),reached:minD<2.5,state:G.state}; if(G.state!=='play'){ G.state='play'; } P.bust=0;
    for(const n of G.npcs) if(n.kind==='cop') n.alive=false;
    // ---- a scared resident inside a house walks out through the door
    const civ=G.npcs.find(n=>n.alive&&n.kind!=='cop'&&!n.home)||G.npcs.find(n=>n.alive&&n.kind!=='cop'); civ.pos=V(mid.x,0,mid.z); civ.vel=V(); civ.state='flee'; civ.st=0; civ.fleeFrom=V(mid.x+0.5,0,mid.z+0.5);
    P.pos=V(mid.x+40,0,mid.z+40); let outAt=-1; for(let k=0;k<60*10;k++){ update(1/60,I()); if(civ.state==='flee') civ.st=Math.min(civ.st,3); if(!interiorAt(civ.pos)){ outAt=k/60; break; } }
    out.fleeExit={leftBuilding:outAt>=0,seconds:+outAt.toFixed(2)};
    // ---- drone: hover 12 m up with heat on, it launches, zaps, holds heat, radios cops; then knock it down
    G.heat=2; let spawnedAt=-1, zapped=false, heatMin=9; const life0=G.life;
    for(let k=0;k<60*12;k++){ if(!P.ragdoll){ P.pos.y=12; P.vel.y=0; P.grounded=false; } update(1/60,I()); if(G.drone&&spawnedAt<0) spawnedAt=k/60; if(G.drone) heatMin=Math.min(heatMin,G.heat); if(P.ragdoll&&G.drone){ zapped=true; break; } }
    out.drone={spawnedAfterS:+spawnedAt.toFixed(2),zapped,heatHeld:heatMin>=1};
    if(G.drone){ droneDown(true); for(let k=0;k<60*5;k++) update(1/60,I()); out.drone.downFeat=!!G.feats[F_DRONE]; out.drone.cleared=!G.drone; }
    // ---- lobby tower: storefront is breakable glass, and the first flight of stairs can be walked
    const L=W.lobby; out.lobby={exists:!!L};
    if(L){ const panes=BRK_BY.get(L.bld).filter(b=>b.mat==='glass').length; if(P.ragdoll) getUp(P,G.evs);
      P.pos=V((L.sx0+L.cx)/2,0,L.zA-0.6); P.vel=V(); G.cam.yaw=0; P.yaw=0; step(5); const y0=P.pos.y; let ymax=y0;
      for(let k=0;k<60*4;k++){ G.cam.yaw=0; update(1/60,I({my:1})); ymax=Math.max(ymax,P.pos.y); }
      const topY=groundAt((L.sx0+L.sx1)/2,L.zB+0.6,0.1,L.rise+1);
      out.lobby={exists:true,flights:L.nF,riseM:+L.rise.toFixed(2),towerH:+L.h.toFixed(1),glassPanes:panes,walkedUpM:+(ymax-y0).toFixed(2),firstLandingY:+topY.toFixed(2),
        roofLandingY:+groundAt(L.nF%2?(L.sx0+L.sx1)/2:(L.sx0+L.sx1)/2,L.nF%2?L.zB+0.6:L.zA-0.6,0.1,L.h+1).toFixed(2)}; }
    let t1=performance.now(); step(240,()=>I({my:0.4})); out.idleUpdateMs=+((performance.now()-t1)/240).toFixed(3); out.navSearches=NAV.searches;
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
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000)
        for _ in range(60):
            if await page.evaluate("RUB.state") != 'loading': break
            await page.wait_for_timeout(250)
        r = await page.evaluate(JS); r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
