"""Every character style preview, in game: one staged scene (you, three neighbors, a cop and a unicorn in the park), re-rendered
in each style from the Character Style Picker sheet. Writes screenshots/characters/<id>.png and prints render time per style.
Usage: python tests/shots_characters.py [scale]"""
import asyncio, json, os, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
OUT = ROOT / 'screenshots' / 'characters'
I = "(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{})"
STAGE = r"""() => { DEMO_INPUT=null; const I=%s, P=G.player, C=V(-HALF+ROAD/2+2*(BLOCK+ROAD),0,-HALF+ROAD/2+2*(BLOCK+ROAD)); G.clock=16.2;
  G.npcs=G.npcs.filter(n=>hlen(vsub(n.pos,C))>20); G.stashes=[]; G.props=G.props.filter(o=>hlen(vsub(o.pos,C))>6); const hud=document.getElementById('hud'); if(hud) hud.style.visibility='hidden';
  const mk=(dx,dz,yaw,kind)=>{ const n=makeNpc(0,0,kind||'civ'); n.pos=V(C.x+dx,0,C.z+dz); n.state='idle'; n.idleFor=1e9; n.startleCd=1e9; n.talkCd=1e9; n.yaw=yaw; n.home={p:{...n.pos},yaw}; G.npcs.push(n); return n; };
  const a=mk(-1.05,1.3,PI+0.3); a.shirt=hex(0xb8322c); a.pants=hex(0x3e4a61); a.style='none'; a.hat=0;
  const c=mk(0.05,1.75,PI); c.shirt=hex(0xe2ddd0); c.pants=hex(0x1c1c22); c.style='tie'; c.tieCol=hex(0x1c3a8a); c.hat=2;
  const d=mk(1.1,1.3,PI-0.3); d.shirt=hex(0x2aa7a0); d.pants=hex(0x6b5a45); d.style='skirt'; d.skirtCol=hex(0x7a4fa0); d.hat=3;
  const cop=mk(2.05,2.1,PI-0.5,'cop'); cop.state='idle';
  const uni={pos:V(C.x-2.3,0,C.z+2.4),yaw:PI*0.72,turn:0,speed:0,phase:0.6,size:0.9,fade:1,leaving:false,sparkT:0,poof:false}; G.unicorns.length=0; G.unicorns.push(uni); window.__uni=uni;
  P.pos=V(C.x+0.15,0,C.z-0.1); P.vel=V(); P.yaw=PI+0.25; G.cam.yaw=0; G.cam.pitch=0.07; G.cam.dist=G.cam.cur=3.1; G.cam.focus=vadd(P.pos,V(0,1.25,0));
  for(let i=0;i<30;i++){ update(1/60,I()); uni.pos=V(C.x-2.3,0,C.z+2.4); uni.yaw=PI*0.72; uni.fade=1; uni.speed=0; P.yaw=PI+0.25; }
  return {npcs:G.npcs.length,unicorns:G.unicorns.length}; }""" % I
SHOW = r"""(id) => { setCharStyle(id,true); const I=%s, u=window.__uni; for(let i=0;i<6;i++){ update(1/60,I()); if(u){ u.fade=1; u.speed=0; if(!G.unicorns.includes(u)) G.unicorns.push(u); } } G.pops=[]; for(const n of G.npcs) n.bubbleT=0;
  const t=performance.now(); render(); const ms=performance.now()-t;   /* one frame: every extra render() queues a full software-rendered frame before the screenshot */ return {id,name:CSTYLES[id].name,ms:+ms.toFixed(1),inst:Object.values(DYN).reduce((a,b)=>a+b.n,0)}; }""" % I


async def main():
    scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await (await b.new_context(viewport={"width": 960, "height": 540}, device_scale_factor=scale)).new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000)
        for _ in range(120):
            if await page.evaluate("typeof G!=='undefined'&&G&&G.player&&RUB.state!=='loading'"): break
            await page.wait_for_timeout(500)
        print(await page.evaluate(STAGE))
        ids = await page.evaluate("CST_IDS")
        pick = sys.argv[2:]
        rows = []
        for cid in ids:
            if pick and cid not in pick: continue
            info = await page.evaluate(SHOW, cid); rows.append(info)
            await page.wait_for_timeout(500)
            await page.screenshot(path=str(OUT / f"{ids.index(cid):02d}_{cid}.png"), timeout=240000)
            print(json.dumps(info), flush=True)
        # the settings row and the K key
        out = await page.evaluate("""() => { setCharStyle('current',true); const k0=CST_ID; window.dispatchEvent(new KeyboardEvent('keydown',{key:'k'})); const k1=CST_ID;
          location.hash='#cinematic+film'; return {k0,k1}; }""")
        await page.wait_for_timeout(600)
        out['hash'] = await page.evaluate("[LOOK_ID,CST_ID]")
        await page.evaluate("()=>{ G.state='paused'; openSettings&&openSettings(); }")
        await page.wait_for_timeout(400)
        out['settingsRow'] = await page.evaluate("[...document.querySelectorAll('#settings *')].some(e=>e.textContent==='Characters (preview, not saved)')")
        print('keys/hash/settings:', out)
        print('errors:', errs[:5]); await b.close()

asyncio.run(main())
