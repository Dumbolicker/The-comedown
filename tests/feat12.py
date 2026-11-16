"""Checks for the rebuilt houses (styles, roofs, garages, second floors), no grass on paving, the five quests (givers placed
clear of walls, slot machines and the ripperdoc; looks that match their names; standing their ground when you sprint at
them; every quest's steps to the payout; a timed step failing; a real E key press starting one), the trailers (raised
doors, awnings, furniture, walking into every one of them), street details and the character style previews.
Prints JSON; "errs" and "pageerrors" should be empty."""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[]}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  const cnt=(a,f)=>a.reduce((m,x)=>{ const k=f(x); m[k]=(m[k]||0)+1; return m; },{});
  try{
    // ---- houses
    const H=W.houses; out.houses={n:H.length,styles:cnt(H,h=>h.style),roofs:cnt(H,h=>h.roof),cladding:cnt(H,h=>h.fin),garages:cnt(H,h=>h.gar),twoStory:H.filter(h=>h.two).length,
      interiors:W.interiors.filter(i=>i.house).length,hipPanels:BRK.filter(b=>b.s.ramp===5).length,gableWithParts:BRK.filter(b=>b.roof&&b.parts&&b.s.ramp&&b.s.ramp<5).length,
      hiddenUpper:BRK.filter(b=>b.hideIn).length,garageDoors:W.trims.filter(t=>BRK[t.a]&&BRK[t.a].tex===7&&BRK[t.a].s.y0===0&&(BRK[t.a].s.x1-BRK[t.a].s.x0>2||BRK[t.a].s.z1-BRK[t.a].s.z0>2)).length,
      stopSigns:0,condemnedHouses:[...W.condemned].filter(b=>W.interiors.some(i=>i.house&&i.bld===b)).length};
    // every house roof rests on its walls (nothing falls at the start) and the hip surface matches its formula
    const hip=BRK.find(b=>b.s.ramp===5), hs=hip.s; out.hipTop={edge:+topAt(hs,hs.x0,(hs.z0+hs.z1)/2).toFixed(2),y0:+hs.y0.toFixed(2),mid:+topAt(hs,(hs.x0+hs.x1)/2,(hs.z0+hs.z1)/2).toFixed(2),y1:+hs.y1.toFixed(2)};
    // ---- no grass on paving: every grass blade (a static cone below 0.25 m) checked against the paved rectangles
    const C=STATIC.blade||STATIC.cone, P_=W.paved; let blades=0, onPave=0;
    for(let i=0;i<C.n;i++){ const o=i*IF, x=C.data[o], y=C.data[o+1], z=C.data[o+2]; if(y>0.25) continue; blades++; if(P_.some(q=>x>q[0]&&x<q[2]&&z>q[1]&&z<q[3])) onPave++; }
    out.grass={blades,onPave,pavedRects:P_.length};
    // ---- quests: five givers, placed clear of walls, who stand their ground
    startGame(); G.life=200; const P=G.player, givers=G.npcs.filter(n=>n.role==='quest');
    let minGap=1e9; for(let a=0;a<givers.length;a++) for(let b=a+1;b<givers.length;b++) minGap=Math.min(minGap,hlen(vsub(givers[a].pos,givers[b].pos)));
    out.quests={n:QUESTS.length,givers:givers.length,minGap:+minGap.toFixed(1),blocked:W.questSpots.filter(s=>questBlocked(s.p)).length,who:givers.map(n=>QUESTS[n.qi].who),
      bald:givers.filter(n=>n.hat===2).map(n=>n.qname),voices:givers.map(n=>n.vsex).join(''),
      nearSlot:givers.filter(n=>(W.slotsB||[]).some(b=>hlen(vsub(boxCenter(b.s),n.pos))<4)).map(n=>n.qname),nearDoc:givers.filter(n=>W.doc&&hlen(vsub(W.doc.pos,n.pos))<5).map(n=>n.qname),
      insideBuilding:givers.filter(n=>W.interiors.some(i=>n.pos.x>i.x0&&n.pos.x<i.x1&&n.pos.z>i.z0&&n.pos.z<i.z1)).map(n=>n.qname)};
    const giver=id=>givers.find(n=>QUESTS[n.qi].id===id), goTo=n=>{ P.pos=vadd(n.pos,V(1.3,0,0.4)); P.vel=V(); RUB.teleport=true; step(3); };
    // sprinting straight at a giver: they don't flee and aren't knocked over
    { const n=giver('ernesto'); P.pos=vadd(n.pos,V(-9,0,0)); P.vel=V(9.5,0,0); RUB.teleport=true; const seen=new Set(); for(let i=0;i<70;i++){ update(1/60,I({my:1,sprint:true})); seen.add(n.state); } out.sprintAtGiver=[...seen]; }
    // talking with the grab button works, even while carrying something
    const raj=giver('shoplifter'); goTo(raj); const crate=makeProp({kind:'crate',x:P.pos.x,y:0,z:P.pos.z,yaw:0}); G.props.push(crate); P.held=G.props.length-1; crate.held=true; step(2); syncHUD(1/60);
    out.prompt=document.getElementById('promptmsg').textContent; update(1/60,I({grab:true})); step(2); out.acceptedWhileHolding=!!G.quest&&G.quest.q.id==='shoplifter'; syncHUD(1/60); out.hud=document.getElementById('quest').textContent;
    if(P.held>=0){ G.props[P.held].held=false; P.held=-1; }
    const res={}, d0=()=>G.dollas, logStep=(Q,arr)=>arr.push((Q&&G.quest===Q?Q.k:'end'));
    const run=(id,fn)=>{ const n=giver(id); goTo(n); if(!G.quest||G.quest.q.id!==id) questTalk(n); const Q=G.quest, d=d0(), r={started:!!Q&&Q.q.id===id,steps:Q?Q.steps.length:0,path:[]}; try{ fn(Q,n,r); }catch(e){ r.err=String(e).slice(0,160); } step(4); r.done=!G.quest&&G.questDone.has(id); r.paid=G.dollas-d; res[id]=r; return r; };
    const hold=o=>{ const i=G.props.indexOf(o); P.pos=V(o.pos.x+0.6,0,o.pos.z); RUB.teleport=true; step(2); P.held=i; o.held=true; step(3); };
    const carryTo=(o,p)=>{ P.pos=V(p.x+0.9,0,p.z); RUB.teleport=true; o.pos=V(p.x+0.4,1,p.z); step(4); };
    run('shoplifter',(Q,n,r)=>{ r.path.push(Q.k); const t=Q.thief; r.thiefFled=t.state; knockNpc(t,V(3,3,0)); step(3); r.path.push(Q.k); hold(Q.bag); r.path.push(Q.k); carryTo(Q.bag,n.pos); });
    run('parcel',(Q,n,r)=>{ r.path.push(Q.k); r.areaShown=!!Q.steps[0].area(Q); hold(Q.parcel); r.path.push(Q.k); carryTo(Q.parcel,Q.dest); P.held=-1; Q.parcel.held=false; step(4); r.path.push(Q.k); P.pos=vadd(Q.res.pos,V(1.2,0,0)); RUB.teleport=true; step(3); r.nearRes=G.nearQuest===Q.res; update(1/60,I({grab:true})); step(3); r.path.push(Q.k); goTo(n); update(1/60,I({grab:true})); step(3); });
    run('ernesto',(Q,n,r)=>{ r.path.push(Q.k); for(const nb of Q.nb){ P.pos=vadd(nb.pos,V(1.1,0,0)); RUB.teleport=true; step(3); update(1/60,I({grab:true})); step(2); } r.path.push(Q.k); hold(Q.ern); r.path.push(Q.k); carryTo(Q.ern,n.pos); });
    run('collections',(Q,n,r)=>{ r.path.push(Q.k); const park=W.blocks.find(b=>b.kind==='park'); P.pos=V((park.x0+park.x1)/2+2,0,(park.z0+park.z1)/2+2); RUB.teleport=true; step(4); r.path.push(Q.k); knockNpc(Q.mark,V(3,3,0)); step(3); r.path.push(Q.k);
      for(const c of Q.coins){ c.alive=false; } step(3); r.path.push(Q.k); goTo(n); questTalk(n); step(2); });
    run('condemned',(Q,n,r)=>{ r.path.push(Q.k); P.pos=V(Q.door.x+0.5,0,Q.door.z); RUB.teleport=true; step(4); r.path.push(Q.k); r.junk=Q.junk.length; for(const j of Q.junk.slice(0,3)) j.o.pos=vadd(j.o.pos,V(3,0,0)); step(3); r.path.push(Q.k);
      const roof=BRK_BY.get(Q.it.bld).find(b=>b.roof&&b.alive); detachPanel(roof); step(4); r.path.push(Q.k); goTo(n); questTalk(n); step(2); });
    // a timed step running out, and the HUD going away
    { const rj=giver('shoplifter'); G.questDone.delete('shoplifter'); goTo(rj); questTalk(rj); G.t+=80; step(2); out.timeout={failed:!G.quest&&!G.questDone.has('shoplifter'),hud:document.getElementById('quest').hidden}; }
    // a real key press (the keyboard handler, not a test shortcut) starts a quest
    out.jobs=res; out.allDone=Object.values(res).filter(r=>r.done).length; out.paidTotal=Object.values(res).reduce((a,r)=>a+(r.paid||0),0); out.prof=Object.keys(PROF.quests).length;
    // trailers
    { const T=W.interiors.filter(i=>i.trailer); out.trailers={n:T.length,raisedDoors:W.doors.filter(d=>(d.yb||0)>0.5).length,awnings:W.trims.filter(t=>t.p.some(p=>p[6]&&p[6]!==QI&&p[7]&&Math.abs(p[4]-0.012)<1e-6)).length,condemnedTrailer:T.some(i=>W.condemned.has(i.bld))};
      out.trailers.walkIn=T.map(it=>{ const d=W.doors.find(d=>d.bld===it.bld); if(!d) return 'no door'; const c=doorCenter(d); P.pos=V(c.x,0,c.z+3.4); RUB.teleport=true; P.vel=V(); P.yaw=PI; G.cam.yaw=PI; step(3);
        let was=false; for(let i=0;i<120;i++){ G.cam.yaw=PI; update(1/60,I({my:1})); if(G.inside===it) was=true; } return was?'in':'blocked at '+(P.pos.z-c.z).toFixed(2); });
      out.trailers.furniture=T.map(it=>G.props.filter(o=>o.pos.x>it.x0&&o.pos.x<it.x1&&o.pos.z>it.z0&&o.pos.z<it.z1&&o.pos.y>0.75).length);
      const tr=W.solids.find(s=>s.bouncy); out.trailers.trampolineClear=!W.solids.some(s=>s!==tr&&!s.gone&&s.y1>0.3&&s.x1>tr.x0-0.4&&s.x0<tr.x1+0.4&&s.z1>tr.z0-0.4&&s.z0<tr.z1+0.4);
      const v=giver('collections'); P.pos=vadd(v.pos,V(0.9,0,0.6)); P.vel=V(); RUB.teleport=true; step(3); syncHUD(1/60); out.vinnyPrompt=document.getElementById('promptmsg').textContent; out.touchLabel=document.getElementById('bGrab').textContent; }
    // ---- street details
    out.street={lamps:W.lamps.length,lights:W.lights.length,carColors:cnt(G.props.filter(o=>o.k==='car'),o=>o.tint.map(c=>Math.round(c*9)).join(''))};
    // ---- character style previews: every style renders, K cycles, the Settings row switches, a link picks one
    const cs={}; for(const id of CST_IDS){ setCharStyle(id,true); render(); cs[id]=Object.values(DYN).reduce((a,b)=>a+b.n,0); } setCharStyle('current',true);
    window.dispatchEvent(new KeyboardEvent('keydown',{key:'k'})); const kCycled=CST_ID; setCharStyle('current',true);
    let rowTab=null; for(const [tid] of STABS){ sTab=tid; renderSettings(); if([...document.querySelectorAll('#setBody .sl')].some(e=>e.textContent.startsWith('Characters (preview'))){ rowTab=tid; break; } }
    const btn=[...document.querySelectorAll('#setBody .opt')].find(b=>b.textContent==='Anime Cel Style'); if(btn) btn.click(); const clicked=CST_ID; setCharStyle('current',true);
    out.charStyles={n:CST_IDS.length,instances:cs,kCycled,rowTab,clicked,saved:JSON.stringify(store.get('bt_settings',{})).includes('anime')};
    step(30);
  }catch(e){ out.errs.push(String(e&&e.stack||e).slice(0,500)); }
  return out; }
"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await (await b.new_context(viewport={"width": 960, "height": 540})).new_page(); errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: errs.append('console:' + m.text) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
        await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        if VENDOR.exists():
            await page.route("https://cdn.jsdelivr.net/**", lambda r: r.fulfill(path=str(VENDOR), content_type="text/javascript", headers={"access-control-allow-origin": "*"}))
        await page.goto(GAME_URI, wait_until="domcontentloaded", timeout=180000)
        for _ in range(60):
            if await page.evaluate("RUB.state") != 'loading': break
            await page.wait_for_timeout(250)
        r = await page.evaluate(JS)
        # a real key press through the keyboard handler starts a quest
        await page.evaluate("""()=>{ G.questDone.delete('ernesto'); if(G.quest) questEnd(false,'test'); const P=G.player; if(P.ragdoll) getUp(P,G.evs); P.held=-1; const lu=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id==='ernesto'); P.pos=vadd(lu.pos,V(1.3,0,0.4)); P.vel=V(); RUB.teleport=true; }""")
        await page.evaluate("()=>{ for(let i=0;i<4;i++) update(1/60,gatherInput(1/60)); }")
        await page.keyboard.down('e')
        r['keyE'] = await page.evaluate("()=>{ const near=G.nearQuest?G.nearQuest.qname:null; for(let i=0;i<2;i++) update(1/60,gatherInput(1/60)); return [!!G.quest&&G.quest.q.id==='ernesto',G.state,near]; }")
        await page.keyboard.up('e')
        r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
