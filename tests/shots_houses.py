"""Screenshots of the rebuilt houses, the street details and a quest, all from one page load (Rapier takes a while to
compile in CI). Writes screenshots/houses_*.png. Usage: python tests/shots_houses.py [scale]"""
import asyncio, os, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
OUT = ROOT / 'screenshots'
I = "(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{})"
# stage(h, side, back, height, pitch): put the player in front of house h and the camera behind, looking at it
STAGE = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player, [sel,side,back,dist,pitch,clock]=arg;
  const H=W.houses.filter(h=>sel.style?h.style===sel.style:true).filter(h=>sel.roof?h.roof===sel.roof:true).filter(h=>sel.gar===undefined||(!!h.gar)===sel.gar)[sel.i||0]||W.houses[0];
  G.clock=clock; const fx=H.x+side, fz=H.front+H.out*back; P.pos=V(fx,0,fz); P.vel=V(); P.ragdoll=false;
  const yaw=Math.atan2(H.x-fx,(H.z)-fz); P.yaw=yaw; G.cam.yaw=yaw; G.cam.pitch=pitch; G.cam.dist=G.cam.cur=dist; G.cam.focus=vadd(P.pos,V(0,1.4,0));
  G.npcs=G.npcs.filter(n=>n.role==='quest'||hlen(vsub(n.pos,P.pos))>14); G.stashes=G.stashes.filter(s=>hlen(vsub(s.pos,P.pos))>10); G.pops=[];
  for(let i=0;i<40;i++) update(1/60,I()); P.lineT=0; P.line=''; return {style:H.style,roof:H.roof,fin:H.fin,gar:H.gar,two:H.two}; }""" % I
AERIAL = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player, b=W.blocks.filter(b=>b.kind==='res')[arg[0]]; G.clock=arg[1];
  P.pos=V(b.x0-2,0,(b.z0+b.z1)/2); P.vel=V(); P.yaw=PI/2; G.cam.yaw=PI/2+0.35; G.cam.pitch=0.62; G.cam.dist=G.cam.cur=17; G.cam.focus=vadd(P.pos,V(0,1.4,0));
  for(let i=0;i<40;i++) update(1/60,I()); return 'aerial'; }""" % I
STREET = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player; G.clock=arg[0]; const b=W.blocks.find(b=>b.kind==='down'); P.pos=V(b.x0-1.0,0,b.z0-7.5); P.vel=V(); P.yaw=0.75;
  G.cam.yaw=0.75; G.cam.pitch=0.16; G.cam.dist=G.cam.cur=6; G.cam.focus=vadd(P.pos,V(0,1.4,0)); for(let i=0;i<40;i++) update(1/60,I()); return 'street'; }""" % I
JOB = r"""() => { DEMO_INPUT=null; const I=%s, P=G.player; G.clock=16.2; const n=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id==='ernesto'); P.pos=vadd(n.home.p,V(2.4,0,1.6)); P.vel=V();
  const yaw=Math.atan2(n.pos.x-P.pos.x,n.pos.z-P.pos.z); P.yaw=yaw; G.cam.yaw=yaw+0.25; G.cam.pitch=0.18; G.cam.dist=G.cam.cur=4.6; G.cam.focus=vadd(P.pos,V(0,1.4,0));
  for(let i=0;i<20;i++) update(1/60,I()); questTalk(n); for(let i=0;i<30;i++) update(1/60,I()); syncHUD(1/60); return document.getElementById('quest').textContent; }""" % I

SHOTS = [
    ('houses_ranch_hip', STAGE, [{'style': 'ranch', 'roof': 'hip'}, 2.5, 7.5, 6.5, 0.12, 15.6]),
    ('houses_ranch_gable', STAGE, [{'style': 'ranch', 'roof': 'gx'}, -2.0, 7.5, 6.5, 0.12, 15.6]),
    ('houses_colonial', STAGE, [{'style': 'colonial'}, 2.0, 8.0, 8.0, 0.14, 16.4]),
    ('houses_bungalow', STAGE, [{'style': 'bungalow'}, -1.5, 7.0, 6.5, 0.12, 16.0]),
    ('houses_tract', STAGE, [{'style': 'tract'}, 2.5, 6.5, 7.5, 0.16, 15.2]),
    ('houses_tract2', STAGE, [{'style': 'tract', 'i': 1}, -2.5, 6.5, 7.5, 0.16, 16.8]),
    ('houses_modern', STAGE, [{'style': 'modern'}, -2.5, 7.5, 6.5, 0.12, 17.2]),
    ('houses_aerial', AERIAL, [0, 15.8]),
    ('houses_aerial2', AERIAL, [3, 16.6]),
    ('houses_street', STREET, [16.0]),
    ('houses_job', JOB, None),
]


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
        for name, js, arg in SHOTS:
            if len(sys.argv) > 2 and name not in sys.argv[2:]: continue
            info = await page.evaluate(js, arg) if arg is not None else await page.evaluate(js)
            await page.wait_for_timeout(900)
            await page.screenshot(path=str(OUT / (name + '.png')), timeout=180000)
            print(name, info, flush=True)
        print('errors:', errs[:4]); await b.close()

asyncio.run(main())
