"""Frame cost probe: triangles and instances per pass, JS time for update() and render(), and the full frame with the GPU
work finished (gl.finish) at three views: street level, aerial, and a demolition blast with rubble. Software GL (SwiftShader)
turns GPU work into CPU time, so the finish time stands in for a weak phone GPU. Prints JSON. Usage: python tests/perf_probe.py"""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?demo=shot&freeze=0.05'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'
I = "(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{})"
JS = r"""async () => { DEMO_INPUT=null; const I=%s, P=G.player, out={};
  const tri=k=>MESH[k]?MESH[k].count/3:0, sum=(S,cnt)=>BATCH_KEYS.reduce((a,k)=>a+cnt(S,k)*tri(k),0);
  const stat=()=>{ const st={}; for(const k of BATCH_KEYS) st[k]=staticCounts[k]||0; return st; };
  const measure=async(label,frames=40)=>{ let up=0, rd=0, fin=0, n=0;
    for(let i=0;i<frames;i++){ const t0=performance.now(); update(1/60,I()); const t1=performance.now(); render(); const t2=performance.now(); gl.finish(); const t3=performance.now();
      if(i>=5){ up+=t1-t0; rd+=t2-t1; fin+=t3-t1; n++; } await new Promise(r=>setTimeout(r,0)); }
    const sTris=sum(null,(S,k)=>k==='arc'?0:(staticCounts[k]||0)), bTris=sum(BRKB,(S,k)=>BRKB[k].n), hTris=sum(SHO,(S,k)=>SHO[k].n), dTris=sum(DYN,(S,k)=>DYN[k].n), tTris=sum(TRN,(S,k)=>TRN[k].n);
    out[label]={updateMs:+(up/n).toFixed(2),renderJsMs:+(rd/n).toFixed(2),frameWithGpuMs:+(fin/n).toFixed(1),
      tris:{static:Math.round(sTris),panels:Math.round(bTris),dynamic:Math.round(dTris),transparent:Math.round(tTris),mainPass:Math.round(sTris+bTris+dTris+tTris),shadowPass:SH.on?Math.round(sTris+bTris+hTris+dTris):0},
      instances:{dynamic:Object.values(DYN).reduce((a,b)=>a+b.n,0),panels:Object.values(BRKB).reduce((a,b)=>a+b.n,0)},shadows:SH.on,dyn:+QUAL.dyn.toFixed(2)}; };
  out.static=stat(); out.staticTrisByMesh=Object.fromEntries(BATCH_KEYS.map(k=>[k,Math.round((staticCounts[k]||0)*tri(k))]));
  QUAL.dyn=1; const lockDyn=()=>{ QUAL.dyn=1; };
  // street level in a residential block
  const H=W.houses[0]; G.clock=15.5; P.pos=V(H.x+2,0,H.front+H.out*7); P.vel=V(); G.cam.yaw=Math.atan2(0,-H.out); G.cam.pitch=0.1; G.cam.dist=G.cam.cur=6; lockDyn(); await measure('street');
  // aerial over the middle of town
  P.pos=V(0,0,0); G.cam.yaw=0.6; G.cam.pitch=0.75; G.cam.dist=G.cam.cur=26; lockDyn(); await measure('aerial');
  // a blast at a condemned house: panels break, rubble and chunks fly, fire starts
  const it=W.interiors.find(i=>i.house&&W.condemned.has(i.bld)), c=V((it.x0+it.x1)/2,1,(it.z0+it.z1)/2); P.pos=V(c.x+8,0,c.z+8); G.cam.yaw=Math.atan2(c.x-P.pos.x,c.z-P.pos.z); G.cam.pitch=0.2; G.cam.dist=G.cam.cur=7;
  let rebuilds=0; const rb=rebuildBrk; window.rebuildBrk=function(){ rebuilds++; return rb.apply(this,arguments); };
  brkBlast(c,6,2600); explode&&explode(c,1.2); lockDyn(); await measure('blast',60); out.blast.rebuildsPer55Frames=rebuilds; window.rebuildBrk=rb;
  out.blast.rubble={slabs:RUB.slabs.length,chunks:RUB.chunks.length,props:G.props.filter(p=>p.alive&&p.k==='chunk').length};
  return out; }""" % I


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
        r = await page.evaluate(JS); r['errors'] = errs[:4]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
