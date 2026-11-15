import asyncio, json
from playwright.async_api import async_playwright
import pathlib, os
GAME_URI=(pathlib.Path(__file__).resolve().parent.parent/'game'/'index.standalone.html').as_uri()
JS = r"""
() => { const out={errs:[]}; const I=(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++){ update(1/60,f?f(k):I()); if(k%15===0){ FDT=1/60; windUpdate(G.t); render(); drawOverlay&&drawOverlay(); syncHUD(1/60); } } };
  try{ startGame(); G.life=900; const P=G.player;
    // ---- slots: odds + pity, simulated with the real rollOutcome
    { let pity=0, tri=0, pair=0, liv=0, forced=0, none=0, dbl=0, maxDry=0, dry=0; const N=400000;
      for(let i=0;i<N;i++){ const o=rollOutcome(pity>=PITY-1); if(o.pity) forced++; if(o.kind==='none'){ none++; pity++; dry++; maxDry=Math.max(maxDry,dry); } else { pity=0; dry=0; if(o.kind==='triple'){ if(o.res[0]===SLOT.length-1) liv++; else tri++; } else if(o.kind==='pair') pair++; else dbl++; } }
      out.slots={N,jackpotPct:+(tri/N*100).toFixed(3),liverTriplePct:+(liv/N*100).toFixed(3),pairPct:+(pair/N*100).toFixed(3),prizePct:+((N-none)/N*100).toFixed(2),pityPct:+(forced/N*100).toFixed(2),maxDry,doubloons:dbl}; }
    G.pity=19; const po=rollOutcome(true); settle(po,po.res.map(i=>SLOT[i])); out.pitySettle={kind:po.kind,pityAfter:G.pity,msg:$('slotmsg').textContent.slice(0,40)};
    // ---- doubloon rush
    settle({kind:'doubloon'},[DOUBLOON,DOUBLOON,DOUBLOON]); const seq=[]; let worldMin=9, fadeFrames=0;
    for(let k=0;k<31*60;k++){ update(1/60,I({my:k%240<120?1:0,mx:Math.sin(k*0.02)*0.5,jumpHeld:k%300<60})); if(G.parade&&G.parade.fade<0.7) fadeFrames++; if(k%10===0){ FDT=1/60; render(); drawOverlay(); syncHUD(1/60); }
      if(seq[seq.length-1]!==P.form) seq.push(P.form); if(G.mods.all) worldMin=Math.min(worldMin,G.mods.world); }
    out.doubloon={seq:seq.join(','),count:new Set(seq.filter(Boolean)).size,paradeAfter:!!G.parade,formAfter:P.form,effects:G.effects.map(e=>e.name),world:+worldMin.toFixed(2),fadeFrames,pirate:P.pirate};
    // ---- flight
    for(const f of ['dragon','angel','demon']){ if(P.ragdoll) getUp(P,G.evs); P.pos={...W.spawn}; P.vel=V(); transform(f); P.formT=99; step(20);
      step(1,()=>I({jump:true,jumpHeld:true})); step(180,()=>I({jumpHeld:true,my:1})); const top=P.pos.y; step(60,()=>I({my:1})); const vy=P.vel.y;
      let landed=false; for(let k=0;k<1200&&!P.grounded;k++) update(1/60,I({my:0})); out['fly_'+f]={top:+top.toFixed(1),glideVy:+vy.toFixed(2),grounded:P.grounded,ragdoll:P.ragdoll}; }
    untransform();
    // ---- horn charge
    if(P.ragdoll) getUp(P,G.evs); transform('minotaur'); P.formT=99; P.pos={...W.spawn}; P.vel=V(); step(10);
    const dir=fwd(P.yaw), n=G.npcs[1]; n.pos=vadd(P.pos,vmul(dir,9)); n.state='idle'; n.idleFor=99; const s0={...P.pos}, sc0=G.score;
    step(1,()=>I({charge:true})); let maxD=0; for(let k=0;k<100;k++){ update(1/60,I()); maxD=Math.max(maxD,hlen(vsub(P.pos,s0))); if(k%10===0) render(); }
    out.charge={dist:+maxD.toFixed(1),npc:n.state,gored:G.pops.some(q=>/GORED/.test(q.text)),cd:+P.hornCd.toFixed(2)};
    // ---- holy + hell poop
    untransform(); transform('angel'); P.formT=99; P.poopCd=0; step(1,()=>I({poop:true})); step(60); out.holy={kind:P.poop&&P.poop.kind,col:P.poop&&P.poop.cols[3].map(x=>+x.toFixed(2))};
    const n2=G.npcs[2]; n2.pos=vadd(P.pos,vmul(fwd(G.cam.yaw),5)); n2.state='idle'; n2.idleFor=99; G.focusT={kind:'npc',i:2,pos:npcCenter(n2)}; step(1,()=>I({tackle:true})); step(80);
    out.holyHit={npc:n2.state,pops:G.pops.map(q=>q.text).filter(t=>/BLESS|DIVINE/.test(t))};
    untransform(); transform('demon'); P.formT=99; P.poopCd=0; step(1,()=>I({poop:true})); step(60); out.hell={kind:P.poop&&P.poop.kind}; step(1,()=>I({tackle:true})); step(90);
    out.hellSplat={glowDecals:G.decals.filter(d=>d.g>0.3).length,fire:G.parts.filter(q=>q.kind==='fire').length};
    // ---- laced: fold
    untransform(); if(P.ragdoll) getUp(P,G.evs); P.pos={...W.spawn}; P.vel=V(); step(10); pickup({sub:SUB('coke'),pos:{...P.pos},life:9,seed:1,laced:true}); step(70);
    const f0={...P.pos}; let kmax=0, kmin=1; for(let k=0;k<300;k++){ update(1/60,I({my:1,sprint:true,jump:k%30===0,charge:true,tackle:k%40===0})); if(k>60){ const kk=foldK(P); kmax=Math.max(kmax,kk); kmin=Math.min(kmin,kk); } if(k%20===0) render(); }
    out.fold={foldT:+P.foldT.toFixed(1),moved:+hlen(vsub(P.pos,f0)).toFixed(2),kmax:+kmax.toFixed(2),kmin:+kmin.toFixed(2),sat:+G.mods.sat.toFixed(2)};
    step(500,()=>I({my:1})); out.foldEnd={foldT:P.foldT,moved:+hlen(vsub(P.pos,f0)).toFixed(1)};
    // stashes get a laced flag
    for(let i=0;i<300;i++) spawnStash(); out.lacedRate=+(G.stashes.filter(s=>s.laced).length/G.stashes.length).toFixed(3);
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
