"""M2 checks: props in Rapier (stacking, rubble vs props, thrown props break walls, prop gravity), jointed ragdolls,
new breakables and spreading fire. Runs with Rapier (vendored, hash-checked) and with it blocked (built-in fallback).
Prints JSON; "errs" should be empty.
"""
import asyncio, json, os, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  const open=()=>{ for(let t=0;t<40;t++){ const x=rand(-HALF+20,HALF-20), z=rand(-HALF+20,HALF-20); if(!W.solids.some(s=>!s.gone&&s.x0<x+4&&s.x1>x-4&&s.z0<z+4&&s.z1>z-4)&&!G.props.some(o=>Math.abs(o.pos.x-x)<5&&Math.abs(o.pos.z-z)<5)) return V(x,0,z); } return V(0,0,-HALF+ROAD/2); };
  const mk=(kind,at,vel)=>{ const o=makeProp({kind,x:at.x,z:at.z,yaw:0,y:0}); o.pos.y=at.y; if(vel){ o.vel=vel; o.asleep=false; } else o.asleep=false; G.props.push(o); return o; };
  try{ startGame(); G.life=900; const P=G.player; out.engine=RUB.state; out.propsInRapier=usePropRapier();
    // ---- stacking: a crate dropped 1.5 m above another crate should come to rest on top of it
    const c=open(); P.pos=V(c.x+12,0,c.z); const A=mk('crate',V(c.x,0.46,c.z)), B=mk('crate',V(c.x+0.05,2.4,c.z));
    step(240); out.stack={bottomY:+A.pos.y.toFixed(3),topY:+B.pos.y.toFixed(3),expectedTopY:+(A.pos.y+A.half.y+B.half.y).toFixed(3),onTop:Math.abs(B.pos.y-(A.pos.y+A.half.y+B.half.y))<0.12&&Math.hypot(B.pos.x-A.pos.x,B.pos.z-A.pos.z)<0.5,asleep:A.asleep&&B.asleep};
    // ---- prop gravity: a barrel dropped from 6 m, fit y(t) = y0 + v0 t - g t²/2 over the free part of the fall
    const c2=open(); P.pos=V(c2.x+12,0,c2.z); const Dr=mk('barrel',V(c2.x,6.5,c2.z)); const pts=[]; let t=0;
    for(let k=0;k<60;k++){ update(1/120,I()); t+=1/120; if(Dr.pos.y>1.2) pts.push([t,Dr.pos.y]); }
    if(pts.length>8){ const n=pts.length; let sx=0,sy=0,sxx=0,sxy=0,sx3=0,sx4=0,sx2y=0; for(const [a,b] of pts){ sx+=a; sy+=b; sxx+=a*a; sxy+=a*b; sx3+=a*a*a; sx4+=a*a*a*a; sx2y+=a*a*b; }
      const M=[[n,sx,sxx],[sx,sxx,sx3],[sxx,sx3,sx4]], R=[sy,sxy,sx2y]; for(let cc=0;cc<3;cc++) for(let rr=cc+1;rr<3;rr++){ const f=M[rr][cc]/M[cc][cc]; for(let kk=cc;kk<3;kk++) M[rr][kk]-=f*M[cc][kk]; R[rr]-=f*R[cc]; }
      out.propGravity={samples:n,g_measured:+(-2*R[2]/M[2][2]).toFixed(2),g_expected:22*G.mods.grav}; }
    // ---- rubble vs props: a brick block dropped onto a trash can must move it or come to rest on it
    const c3=open(); P.pos=V(c3.x+12,0,c3.z); const Tc=mk('trash',V(c3.x,0.51,c3.z)); step(30); const tc0={...Tc.pos};
    spawnChunk(V(c3.x,3.2,c3.z),V(0.3,0.3,0.3),QI,V(0,-2,0),V(),'brick',[0.6,0.3,0.25],false);
    const ch=RUB.ready?RUB.chunks[RUB.chunks.length-1]:G.props[G.props.length-1]; step(120);
    const cy=RUB.ready?(ch.t?ch.t.y:ch.body.translation().y):ch.pos.y;
    out.rubbleVsProp={canMovedM:+Math.hypot(Tc.pos.x-tc0.x,Tc.pos.y-tc0.y,Tc.pos.z-tc0.z).toFixed(2),chunkRestY:+cy.toFixed(2),interacted:Math.hypot(Tc.pos.x-tc0.x,Tc.pos.z-tc0.z)>0.05||cy>0.5};
    // ---- a thrown crate breaks a wooden wall panel
    const pan=BRK.find(b=>b.alive&&b.mat==='wood'&&!b.roof&&b.s.y0<0.1&&(b.s.z1-b.s.z0)<0.3&&(b.s.x1-b.s.x0)>1.0);
    const pc=boxCenter(pan.s), side=Math.sign((P.pos.z-pc.z)||1), Cr=mk('crate',V(pc.x,0.9,pc.z+side*2.2),V(0,1.5,-side*16)); Cr.thrown=1;
    const hp0=pan.hp; step(40); out.thrownCrate={panelHpBefore:+hp0.toFixed(1),panelAlive:pan.alive,panelHpAfter:+(pan.alive?pan.hp:0).toFixed(1),damaged:!pan.alive||pan.hp<hp0};
    // ---- explosion among props: logic cost of the busiest second
    const c4=open(); P.pos=V(c4.x+9,0,c4.z); for(let k=0;k<12;k++) mk(pick(['crate','trash','barrel','cone','bag']),V(c4.x+rand(-2,2),0.6,c4.z+rand(-2,2))); step(60);
    explode(V(c4.x,0.5,c4.z)); const ts=[]; for(let k=0;k<60;k++){ const t0=performance.now(); update(1/60,I()); ts.push(performance.now()-t0); }
    ts.sort((a,b)=>a-b); out.blastProps={meanMs:+(ts.reduce((a,b)=>a+b,0)/ts.length).toFixed(2),p95Ms:+ts[Math.floor(ts.length*0.95)].toFixed(2),propBodies:RUB.propN||0,awake:G.props.filter(o=>o.alive&&!o.asleep).length};
    // ---- idle cost with props settled
    step(400); let t0=performance.now(); step(240,()=>I({my:0.5})); out.idleUpdateMs=+((performance.now()-t0)/240).toFixed(3);
    if(typeof ragRigCount==='function'){ /* jointed ragdolls */
      const c5=open(); P.pos=V(c5.x,0,c5.z); P.vel=V(); step(10); startRagdoll(P,V(3,6,0),true); const ang0=[]; let maxSpread=0, rigs=0;
      for(let k=0;k<90;k++){ update(1/60,I()); rigs=Math.max(rigs,ragRigCount()); const Rg=P.rig; if(Rg&&Rg.pose){ const sp=Math.abs(Rg.pose.hipL-Rg.pose.hipR)+Math.abs(Rg.pose.shL-Rg.pose.shR); maxSpread=Math.max(maxSpread,sp); } }
      out.ragdoll={rigs,maxLimbSpreadRad:+maxSpread.toFixed(2),limbsIndependent:maxSpread>0.25}; step(240); out.ragdoll.rigsAfterGetUp=ragRigCount(); }
    if(typeof fireAt==='function'){ /* fire spreading through wood */
      const house=[...BRK_BY.keys()].find(k=>k>0&&BRK_BY.get(k).every(b=>b.alive)&&BRK_BY.get(k)[0].mat==='wood'); const list=BRK_BY.get(house), b0=list.find(b=>!b.roof);
      P.pos=V(b0.s.x0-8,0,b0.s.z0-8); fireAt(b0.id); let maxBurning=0; for(let k=0;k<60*25;k++){ update(1/60,I()); if(k%30===0) maxBurning=Math.max(maxBurning,BRK.filter(b=>b.burn>0).length); }
      out.fire={maxBurning,destroyedInHouse:list.filter(b=>!b.alive).length,ofPanels:list.length,stillBurning:BRK.filter(b=>b.burn>0).length}; }
    { // water tower: knock out three legs, the tank falls and splashes; gas canopy drops when three pillars go
      const legs=(W.customB||[]).filter(b=>b.kind==='wleg'), tank=(W.customB||[]).find(b=>b.kind==='wtank'); P.pos=V(tank.s.x0-25,0,tank.s.z0-25); if(P.ragdoll) getUp(P,G.evs);
      for(const l of legs.slice(0,3)) hitBrk(l.id,99999,boxCenter(l.s),V(1,0,0)); let fell=false, splashed=false; const sc0=G.score;
      for(let k=0;k<60*6;k++){ update(1/60,I()); if(tank.falling||!tank.alive) fell=true; if(G.feats[F_WATER]) splashed=true; }
      out.waterTower={legs:legs.length,tankFell:fell,splashFeat:splashed,score:G.score-sc0};
      const can=(W.customB||[]).find(b=>b.kind==='canopy'), pil=BRK_BY.get(can.bld).filter(b=>b!==can); for(const l of pil.slice(0,3)) hitBrk(l.id,99999,boxCenter(l.s),V(1,0,0));
      let cf=false; for(let k=0;k<60*3;k++){ update(1/60,I()); if(can.falling||!can.alive) cf=true; } out.canopy={pillars:pil.length,fell:cf};
      const tr=W.interiors.filter(it=>BRK_BY.get(it.bld).some(b=>b.mat==='metal'&&!b.roof)&&(it.x1-it.x0)>8); out.trailers={shells:tr.length,panels:tr.reduce((a,it)=>a+BRK_BY.get(it.bld).length,0)};
      const f=G.props.find(o=>o.alive&&o.k==='fence'); if(f){ f.vel=V(14,4,0); f.asleep=false; P.pos=V(f.pos.x-8,0,f.pos.z); let gone=false; for(let k=0;k<120;k++){ update(1/60,I()); if(!f.alive){ gone=true; break; } } out.fence={splintered:gone}; }
      out.totalPanels=BRK.length; }
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
