"""Screenshots of the trailer park (outside, deck and stoop, inside) and the quest UI (a giver's marker and talk tag, the
search ring), all from one page load. Writes screenshots/trailers_*.png and quest_*.png.
Usage: python tests/shots_trailers.py [scale] [names...]   (env: BT_GAME=<page>, BT_PREFIX=<prefix>)"""
import asyncio, os, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
# BT_GAME renders another build (e.g. an older one for a before/after); BT_PREFIX prefixes the file names
GAME_URI = pathlib.Path(os.environ.get('BT_GAME') or ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
PREFIX = os.environ.get('BT_PREFIX', '')
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
OUT = ROOT / 'screenshots'
I = "(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{})"
# put the player at (px,pz) relative to the trailer lot's centre and look at (lx,lz); the camera sits behind the player
TRAILER = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player, [px,pz,lx,lz,dist,pitch,clock,fy]=arg, L=W.blocks.find(b=>b.kind==='trailer'), cx=(L.x0+L.x1)/2, cz=(L.z0+L.z1)/2;
  G.clock=clock; P.pos=V(cx+px,fy||0,cz+pz); P.vel=V(); P.ragdoll=false; RUB.teleport=true;
  const yaw=Math.atan2(cx+lx-P.pos.x,cz+lz-P.pos.z); P.yaw=yaw; G.cam.yaw=yaw; G.cam.pitch=pitch; G.cam.dist=G.cam.cur=dist; G.cam.focus=vadd(P.pos,V(0,1.4,0));
  G.npcs=G.npcs.filter(n=>n.role==='quest'||hlen(vsub(n.pos,P.pos))>14); G.stashes=G.stashes.filter(s=>hlen(vsub(s.pos,P.pos))>10); G.pops=[];
  for(let i=0;i<40;i++) update(1/60,I()); P.lineT=0; P.line=''; return {inside:!!G.inside,at:[+(P.pos.x-cx).toFixed(2),+(P.pos.z-cz).toFixed(2)],lot:[+(L.x1-L.x0).toFixed(1),+(L.z1-L.z0).toFixed(1)]}; }""" % I
GIVER = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player, [id,side,back,dist,pitch,clock]=arg, n=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id===id); G.clock=clock;
  G.quest=null; P.pos=vadd(n.pos,V(side,0,back)); P.vel=V(); RUB.teleport=true; const yaw=Math.atan2(n.pos.x-P.pos.x,n.pos.z-P.pos.z); P.yaw=yaw; G.cam.yaw=yaw+0.3;
  G.cam.pitch=pitch; G.cam.dist=G.cam.cur=dist; G.cam.focus=vadd(P.pos,V(0,1.4,0)); G.pops=[]; for(let i=0;i<30;i++) update(1/60,I()); syncHUD(1/60);
  return {who:QUESTS[n.qi].who,near:!!G.nearQuest,prompt:document.getElementById('promptmsg').textContent}; }""" % I
SEARCH = r"""(arg) => { DEMO_INPUT=null; const I=%s, P=G.player, n=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id==='ernesto'); G.clock=arg[0]; G.questDone.delete('ernesto');
  P.pos=vadd(n.pos,V(1.2,0,0.4)); P.vel=V(); RUB.teleport=true; for(let i=0;i<5;i++) update(1/60,I()); questTalk(n); for(let i=0;i<5;i++) update(1/60,I());
  const Q=G.quest; let k=0; while(Q&&Q.k<Q.steps.length&&!/Ernesto around/.test(Q.steps[Q.k].text)&&k++<8){ if(Q.nb) for(const nb of Q.nb){ P.pos=vadd(nb.pos,V(1.1,0,0)); RUB.teleport=true; for(let i=0;i<3;i++) update(1/60,I()); update(1/60,I({grab:true})); } for(let i=0;i<3;i++) update(1/60,I()); }
  const a=Q&&Q.area||n.pos; P.pos=vadd(a,V(-7.5,0,6.5)); P.vel=V(); RUB.teleport=true; const yaw=Math.atan2(a.x-P.pos.x,a.z-P.pos.z); P.yaw=yaw; G.cam.yaw=yaw; G.cam.pitch=0.62; G.cam.dist=G.cam.cur=10;
  G.cam.focus=vadd(P.pos,V(0,1.4,0)); for(let i=0;i<30;i++) update(1/60,I()); syncHUD(1/60); return {step:Q?Q.steps[Q.k].text:null,hud:document.getElementById('quest').textContent.slice(0,120)}; }""" % I

CHASE = r"""() => { DEMO_INPUT=null; const I=%s, P=G.player, n=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id==='shoplifter'); G.clock=17.6; G.questDone.delete('shoplifter');
  if(G.quest){ questCleanup(G.quest); G.quest=null; } P.pos=vadd(n.pos,V(1.2,0,0.4)); P.vel=V(); RUB.teleport=true; for(let i=0;i<5;i++) update(1/60,I()); questTalk(n); for(let i=0;i<100;i++) update(1/60,I());
  const Q=G.quest, t=Q&&Q.thief; if(!t) return {thief:false}; const yaw=Math.atan2(t.pos.x-P.pos.x,t.pos.z-P.pos.z); P.yaw=yaw; G.cam.yaw=yaw; G.cam.pitch=0.3; G.cam.dist=G.cam.cur=6.5;
  G.cam.focus=vadd(P.pos,V(0,1.4,0)); for(let i=0;i<10;i++) update(1/60,I()); syncHUD(1/60); return {thief:t.state,d:+hlen(vsub(t.pos,P.pos)).toFixed(1),hud:document.getElementById('quest').textContent.slice(0,90)}; }""" % I

SHOTS = [
    ('trailers_yard', TRAILER, [0.2, -3.0, -8.0, -5.8, 6.5, 0.24, 16.2, 0]),
    ('trailers_deck', TRAILER, [-6.0, -3.9, -8.0, -5.8, 3.6, 0.2, 15.4, 0]),
    ('trailers_back', TRAILER, [0.0, 12.6, -1.0, 8.4, 7.0, 0.2, 17.0, 0]),
    ('trailers_doc', TRAILER, [5.2, -2.2, 5.6, -5.8, 4.8, 0.14, 19.4, 0]),
    ('trailers_inside', TRAILER, [-8.0, -7.44, -8.0, -8.6, 5.5, 0.62, 15.0, 0.75]),
    ('trailers_inside2', TRAILER, [-5.3, -7.3, -9.0, -7.5, 4.5, 0.85, 15.0, 0.75]),
    ('quest_giver', GIVER, ['ernesto', 2.0, 1.4, 4.8, 0.16, 15.8]),
    ('quest_giver2', GIVER, ['collections', -2.2, 1.6, 5.2, 0.16, 20.4]),
    ('quest_search', SEARCH, [16.6]),
    ('quest_chase', CHASE, None),
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
            await page.screenshot(path=str(OUT / (PREFIX + name + '.png')), timeout=180000)
            print(name, info, flush=True)
        print('errors:', errs[:4]); await b.close()

asyncio.run(main())
