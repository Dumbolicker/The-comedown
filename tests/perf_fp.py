"""What first person costs: update() and render() JS time at the same spots in third and first person (a street, inside a
house, the casino), and the crosshair pick on its own. Software GL, so treat the numbers as relative. Prints JSON."""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
JS = r"""async () => { DEMO_INPUT=null; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0,view:false,alt:false},o||{});
  const P=G.player, out={}; QUAL.dyn=1;
  const go=(p,yaw,pitch)=>{ P.pos=V(p.x,groundAt(p.x,p.z,0.3,1.2),p.z); P.vel=V(); RUB.teleport=true; G.cam.yaw=yaw; G.cam.pitch=pitch; for(let i=0;i<40;i++) update(1/60,I()); };
  const measure=async n=>{ let up=0, rd=0, k=0; for(let i=0;i<n;i++){ const t0=performance.now(); update(1/60,I()); const t1=performance.now(); render(); const t2=performance.now(); if(i>=5){ up+=t1-t0; rd+=t2-t1; k++; } await new Promise(r=>setTimeout(r,0)); }
    return {updateMs:+(up/k).toFixed(2),renderMs:+(rd/k).toFixed(2)}; };
  const H=W.houses.find(h=>!W.condemned.has(h.bld)), it=W.interiors.find(i=>i.bld===H.bld), ci=W.interiors.find(i=>i.casino), L=W.blocks.find(b=>b.kind==='res');
  const spots={street:[V(L.x0-1.0,0,(L.z0+L.z1)/2),PI/2,0.05],house:[V((it.x0+it.x1)/2,0,(it.z0+it.z1)/2),0.6,0.1],casino:[V((ci.x0+ci.x1)/2,0,(ci.z0+ci.z1)/2),0.4,0.05]};
  for(const [name,[p,yaw,pitch]] of Object.entries(spots)){ const r={};
    setView(false,true); go(p,yaw,0.3); r.third=await measure(45);
    setView(true,true); go(p,yaw,pitch); r.first=await measure(45); out[name]=r; }
  // the pick alone, at the busiest spot
  setView(true,true); go(spots.house[0],0.6,0.1); let t0=performance.now(); for(let i=0;i<500;i++) fpPick(); out.pickMs=+((performance.now()-t0)/500).toFixed(3);
  out.props=G.props.filter(o=>o.alive).length; out.solids=W.solids.length; return out; }"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await (await b.new_context(viewport={"width": 960, "height": 540})).new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000)
        for _ in range(120):
            if await page.evaluate("typeof G!=='undefined'&&G&&G.player&&RUB.state!=='loading'"): break
            await page.wait_for_timeout(500)
        await page.wait_for_timeout(1500)
        r = await page.evaluate(JS); r['errors'] = errs[:4]
        print(json.dumps(r, indent=1)); await b.close()

asyncio.run(main())
