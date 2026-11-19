import asyncio, json
from playwright.async_api import async_playwright
import pathlib, os
GAME_URI=(pathlib.Path(__file__).resolve().parent.parent/'game'/'index.standalone.html').as_uri()
JS = r"""
() => { const out={errs:[]}; const I=(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++){ update(1/60,f?f(k):I()); if(k%15===0){ FDT=1/60; windUpdate(G.t); render(); drawOverlay&&drawOverlay(); syncHUD(1/60); } } };
  try{ startGame(); G.life=900; const P=G.player;
    // ---- flight
    for(const f of ['dragon','angel','demon']){ if(P.ragdoll) getUp(P,G.evs); P.pos={...W.spawn}; P.vel=V(); transform(f); P.formT=99; step(20);
      step(1,()=>I({jump:true,jumpHeld:true})); step(180,()=>I({jumpHeld:true,my:1})); const top=P.pos.y; step(60,()=>I({my:1})); const vy=P.vel.y;
      let landed=false; for(let k=0;k<1200&&!P.grounded;k++) update(1/60,I({my:0})); out['fly_'+f]={top:+top.toFixed(1),glideVy:+vy.toFixed(2),grounded:P.grounded,ragdoll:P.ragdoll}; }
    untransform();
    // ---- horn charge
    if(P.ragdoll) getUp(P,G.evs); transform('minotaur'); P.formT=99; P.pos=V(0,0,-20); P.vel=V(); P.yaw=0; G.cam.yaw=0; step(10);
    const dir=fwd(P.yaw), n=G.npcs[1]; n.pos=vadd(P.pos,vmul(dir,9)); n.state='idle'; n.idleFor=99; const s0={...P.pos}, sc0=G.score;
    step(1,()=>I({charge:true})); let maxD=0; for(let k=0;k<100;k++){ update(1/60,I()); maxD=Math.max(maxD,hlen(vsub(P.pos,s0))); if(k%10===0) render(); }
    out.charge={dist:+maxD.toFixed(1),npc:n.state,gored:G.pops.some(q=>/GORED/.test(q.text)),cd:+P.hornCd.toFixed(2)};
    P.pos={...W.spawn}; P.yaw=PI; P.vel=V(); P.hornCd=0; step(10); step(1,()=>I({charge:true})); let stuck=0; for(let k=0;k<90;k++){ update(1/60,I()); stuck=Math.max(stuck,P.stuckT||0); } out.stuck=+stuck.toFixed(2);
    // ---- holy + hell poop
    untransform(); transform('angel'); P.formT=99; P.pos=V(0,0,-20); P.vel=V(); P.yaw=0; G.cam.yaw=0; G.cam.pitch=0.3; step(5); P.poopCd=0; step(1,()=>I({poop:true})); step(60); out.holy={kind:P.poop&&P.poop.kind,col:P.poop&&P.poop.cols[3].map(x=>+x.toFixed(2))};
    const n2=G.npcs[2]; n2.pos=vadd(P.pos,vmul(fwd(G.cam.yaw),5)); n2.state='idle'; n2.idleFor=99; G.focusT={kind:'npc',i:2,pos:npcCenter(n2)}; step(1,()=>I({tackle:true})); step(80);
    out.holyHit={npc:n2.state,pops:G.pops.map(q=>q.text).filter(t=>/BLESS|DIVINE/.test(t))};
    untransform(); transform('demon'); P.formT=99; P.poopCd=0; P.pos=V(0,0,-30); step(5); step(1,()=>I({poop:true})); step(60); out.hell={kind:P.poop&&P.poop.kind}; step(1,()=>I({tackle:true})); step(90);
    out.hellSplat={glowDecals:G.decals.filter(d=>d.g>0.3).length,fire:G.parts.filter(q=>q.kind==='fire').length};
  }catch(e){ out.errs.push(String(e)+' | '+(e.stack||'').split('\n').slice(0,4).join(' | ')); }
  return out; }
"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
        ctx=await b.new_context(viewport={"width":960,"height":540}); page=await ctx.new_page(); errs=[]
        page.on("pageerror", lambda e: errs.append(str(e))); page.on("console", lambda m: errs.append('console:'+m.text) if m.type=='error' else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000); await page.wait_for_timeout(2500)
        r=await page.evaluate(JS); print(json.dumps(r,indent=1)); print("pageerrors:",errs[:6]); await b.close()
asyncio.run(main())
