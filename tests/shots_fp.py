"""Screenshots of first person: a door, the TV and the couch in a house, holding a crate, Grandma Lupe, the casino bar,
a trailer kitchen, a car, looking down at yourself, and lying in a trailer bed. One page load. Writes screenshots/fp_*.png.
Usage: python tests/shots_fp.py [scale] [names...]"""
import asyncio, os, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
OUT = ROOT / 'screenshots'
I = "(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0,view:false,alt:false},o||{})"
SCENE = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player, [what,clock]=arg; G.clock=clock; G.pops=[]; if(P.seat) fpStand(); if(P.held>=0) dropHeld(V()); setView(true,true);
  const aim=pt=>{ const e=fpEye(), dx=pt.x-e.x, dy=pt.y-e.y, dz=pt.z-e.z; G.cam.yaw=Math.atan2(dx,dz); G.cam.pitch=clamp(-Math.atan2(dy,Math.hypot(dx,dz)),-1.45,1.45); };
  const go=p=>{ P.pos=V(p.x,groundAt(p.x,p.z,0.3,(p.y||0)+1.2),p.z); P.vel=V(); RUB.teleport=true; for(let i=0;i<3;i++) update(1/60,I()); };
  const out=(p,i)=>!W.interiors.some(q=>p.x>q.x0&&p.x<q.x1&&p.z>q.z0&&p.z<q.z1);
  const H=W.houses.find(h=>!W.condemned.has(h.bld)&&G.props.some(o=>o.alive&&o.k==='tv'&&W.interiors.some(q=>q.bld===h.bld&&o.pos.x>q.x0&&o.pos.x<q.x1&&o.pos.z>q.z0&&o.pos.z<q.z1)));
  const inH=o=>W.interiors.some(q=>q.bld===H.bld&&o.pos.x>q.x0&&o.pos.x<q.x1&&o.pos.z>q.z0&&o.pos.z<q.z1);
  if(what==='door'){ const d=W.doors.find(d=>!d.broken&&!(d.yb>0.5)&&d.bld===H.bld)||W.doors.find(d=>!d.broken&&!(d.yb>0.5)&&W.houses.some(h=>h.bld===d.bld)), c=doorCenter(d), n=d.axis==='x'?V(0,0,1):V(1,0,0);
    const s=[vadd(c,vmul(n,2.3)),vadd(c,vmul(n,-2.3))].find(out); go(V(s.x+0.4,0,s.z+0.3)); aim(V(c.x,(d.yb||0)+1.15,c.z)); }
  else if(what==='tv'||what==='couch'){ const tv=G.props.find(o=>o.alive&&o.k==='tv'&&inH(o)), f=qrot(tv.rot,V(0,0,1)); go(vadd(tv.pos,vmul(f,2.0))); aim(tv.pos);
    if(what==='couch'){ const ch=G.props.find(o=>o.alive&&o.k==='couch'&&inH(o)); if(ch){ go(vadd(ch.pos,vmul(qrot(ch.rot,V(0,0,1)),1.4))); aim(ch.pos); for(let i=0;i<2;i++) update(1/60,I()); fpUse(0); aim(V(tv.pos.x,tv.pos.y+0.1,tv.pos.z)); } } }
  else if(what==='hold'){ const L=W.blocks.find(b=>b.kind==='res'), c=V(L.x0-1.2,0,(L.z0+L.z1)/2); go(c); G.cam.yaw=PI/2; G.cam.pitch=0.1; const cr=makeProp({kind:'crate',x:c.x,y:0,z:c.z+1.2,yaw:0}); G.props.push(cr);
    for(let i=0;i<3;i++) update(1/60,I()); aim(cr.pos); for(let i=0;i<2;i++) update(1/60,I()); fpUse(0); G.cam.yaw=0.2; G.cam.pitch=0.05; }
  else if(what==='lupe'){ const n=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id==='ernesto'); go(vadd(n.pos,vmul(fwd(n.home.yaw),2.2))); aim(vadd(n.pos,V(0,1.25,0))); }
  else if(what==='bar'){ const S=W.solids.find(s=>s.fp==='bar'), c=V(S.x1+1.5,0,(S.z0+S.z1)/2+0.6); go(c); aim(V(S.x1-0.05,0.85,(S.z0+S.z1)/2)); }
  else if(what==='trailer'){ const S=W.solids.find(s=>s.fp==='counter'), c=V((S.x0+S.x1)/2,0,S.z0>S.z1?S.z0:S.z1); const toRoom=V(0,0,1), at=V(c.x+0.3,S.y0,S.z1+1.05); go(at); aim(V((S.x0+S.x1)/2,S.y1-0.02,S.z1-0.1)); }
  else if(what==='car'){ const car=G.props.find(o=>o.alive&&o.k==='car'&&out(o.pos)), r=qrot(car.rot,V(1,0,0)); go(vadd(car.pos,vadd(vmul(r,2.6),V(0,0,0.4)))); aim(V(car.pos.x,car.pos.y+0.15,car.pos.z)); }
  else if(what==='down'){ const L=W.blocks.find(b=>b.kind==='res'), c=V(L.x0-1.0,0,(L.z0+L.z1)/2+3); go(c); G.cam.yaw=PI/2+0.4; G.cam.pitch=1.15; }
  else if(what==='bed'){ const S=W.solids.find(s=>s.fp==='bed'), c=V((S.x0+S.x1)/2,0,(S.z0+S.z1)/2); go(V(c.x,0,S.z1+0.55)); aim(V(c.x,S.y1,c.z)); for(let i=0;i<2;i++) update(1/60,I()); fpUse(0); G.cam.yaw=Math.atan2(-S.head.x,-S.head.z); G.cam.pitch=-0.15; }
  G.npcs.forEach(n=>{ if(n.role!=='quest'&&hlen(vsub(n.pos,P.pos))<6) n.pos=vadd(n.pos,V(0,0,30)); }); G.stashes=G.stashes.filter(s=>hlen(vsub(s.pos,P.pos))>8);
  for(let i=0;i<50;i++) update(1/60,I(what==='hold'?{}:{})); P.lineT=0; syncHUD(1/60); const e=fpEye(); return {target:G.fpT?fpName(G.fpT):null,verbs:fpVerbs(G.fpT),seat:P.seat?P.seat.kind:null,held:P.held>=0,near:G.props.filter(o=>o.alive&&vlen(vsub(o.pos,e))<1.8).map(o=>o.k+'@'+vlen(vsub(o.pos,e)).toFixed(1)+(o.knocked?'*':''))}; }""" % I

SHOTS = [('fp_door', ['door', 15.6]), ('fp_couch', ['couch', 16.0]), ('fp_tv', ['tv', 16.0]),   # the couch first, before anyone walks into the lamp
         ('fp_hold', ['hold', 15.2]), ('fp_lupe', ['lupe', 16.4]),
         ('fp_bar', ['bar', 20.0]), ('fp_trailer', ['trailer', 15.4]), ('fp_car', ['car', 16.8]), ('fp_down', ['down', 15.8]), ('fp_bed', ['bed', 15.0])]


async def main():
    scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        ctx = await b.new_context(viewport={"width": 1280, "height": 720}, device_scale_factor=scale); page = await ctx.new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000)
        for _ in range(120):
            if await page.evaluate("typeof G!=='undefined'&&G&&G.player&&RUB.state!=='loading'"): break
            await page.wait_for_timeout(500)
        await page.wait_for_timeout(1500)
        for name, arg in SHOTS:
            if len(sys.argv) > 2 and name not in sys.argv[2:]: continue
            try:
                info = await page.evaluate(SCENE, arg)
            except Exception as e:
                print(name, 'FAILED', str(e)[:200], flush=True); continue
            await page.wait_for_timeout(900)
            await page.screenshot(path=str(OUT / (name + '.png')), timeout=180000)
            print(name, info, flush=True)
        print('errors:', errs[:4]); await b.close()

asyncio.run(main())
