"""Where a blast's frame time goes: wraps the update's parts and times them over 60 frames after a big explosion at a
condemned house. Prints JSON (milliseconds per frame, averaged). Usage: python tests/perf_blast.py"""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
I = "(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{})"
JS = r"""async () => { DEMO_INPUT=null; const I=%s, P=G.player, T={}, C={};
  const names=['rubStep','propStep','npcUpdate','demoUpdate','gridBuild','navBuild','navReady','brkCheck','brkStable','fireUpdate','partsUpdate','questUpdate','doorsUpdate','droneUpdate','engageUpdate','cameraUpdate','syncHUD','rebuildBrk','fracture','detachPanel','breakPanel','slabFracture','propSyncIn','ragRigSync','coinUpdate','playerUpdate','updatePlayer'];
  for(const n of names){ const f=window[n]; if(typeof f!=='function') continue; window[n]=function(...a){ const t=performance.now(); try{ return f.apply(this,a); } finally{ T[n]=(T[n]||0)+performance.now()-t; C[n]=(C[n]||0)+1; } }; }
  const it=W.interiors.find(i=>i.house&&W.condemned.has(i.bld)), c=V((it.x0+it.x1)/2,1,(it.z0+it.z1)/2); P.pos=V(c.x+8,0,c.z+8); G.cam.yaw=Math.atan2(c.x-P.pos.x,c.z-P.pos.z); G.cam.pitch=0.2; G.cam.dist=G.cam.cur=7;
  for(let i=0;i<5;i++) update(1/60,I()); for(const k in T){ T[k]=0; C[k]=0; }
  brkBlast(c,6,2600); explode(c); let up=0; const F=60;
  for(let i=0;i<F;i++){ const t0=performance.now(); update(1/60,I()); up+=performance.now()-t0; render(); await new Promise(r=>setTimeout(r,0)); }
  const per=Object.fromEntries(Object.entries(T).filter(([k,v])=>v>0.05).sort((a,b)=>b[1]-a[1]).map(([k,v])=>[k,{msPerFrame:+(v/F).toFixed(2),calls:C[k]}]));
  return {updateMsPerFrame:+(up/F).toFixed(2),parts:per,rubble:{slabs:RUB.slabs.length,chunks:RUB.chunks.length},fires:FIRE.list.length}; }""" % I


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await (await b.new_context(viewport={"width": 480, "height": 270})).new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000)
        for _ in range(120):
            if await page.evaluate("typeof G!=='undefined'&&G&&G.player&&RUB.state!=='loading'"): break
            await page.wait_for_timeout(500)
        await page.wait_for_timeout(1000)
        r = await page.evaluate(JS); r['errors'] = errs[:4]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
