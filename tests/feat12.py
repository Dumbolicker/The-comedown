"""Batch 9 checks: houses built like real ones (styles, roofs, garages, second floors), no grass on paving, the 21 odd jobs
(placement, talking to a neighbor with the grab button, every job type finishing and paying, a timed job failing, repeat pay),
the quest HUD and prompt, and street details. Prints JSON; "errs" and "pageerrors" should be empty."""
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
    // ---- odd jobs: placement
    startGame(); G.life=200; const P=G.player, givers=G.npcs.filter(n=>n.role==='quest');
    let minGap=1e9; for(let a=0;a<givers.length;a++) for(let b=a+1;b<givers.length;b++) minGap=Math.min(minGap,hlen(vsub(givers[a].pos,givers[b].pos)));
    out.quests={n:QUESTS.length,spots:W.questSpots.length,givers:givers.length,minGap:+minGap.toFixed(1),blocked:W.questSpots.filter(s=>questBlocked(s.p)).length,kinds:cnt(W.questSpots,s=>W.blocks.find(b=>s.p.x>=b.x0&&s.p.x<=b.x1&&s.p.z>=b.z0&&s.p.z<=b.z1).kind)};
    const giver=id=>givers.find(n=>QUESTS[n.qi].id===id), goTo=n=>{ P.pos=vadd(n.home.p,V(1.2,0,0.4)); P.vel=V(); RUB.teleport=true; step(3); };
    const res={};
    // talk with the grab button
    const coach=giver('coach'); goTo(coach); step(2); syncHUD(1/60); out.prompt=document.getElementById('promptmsg').textContent; const d0=G.dollas;
    update(1/60,I({grab:true})); step(2); out.accepted=!!G.quest&&G.quest.q.id==='coach'; syncHUD(1/60); out.hud=document.getElementById('quest').textContent;
    G.stats.tackled+=5; step(3); res.coach={done:!G.quest,paid:G.dollas-d0,saved:PROF.quests.coach};
    out.repeatPay=questPay(QUESTS.find(q=>q.id==='coach'));
    const run=(id,act,frames=4)=>{ const n=giver(id); goTo(n); questTalk(n); const Q=G.quest, d=G.dollas; let r={started:!!Q&&Q.q.id===id}; try{ act(Q,n); }catch(e){ r.err=String(e); } step(frames); r.done=!G.quest&&G.questDone.has(id); r.paid=G.dollas-d; res[id]=r; return r; };
    run('hoa',Q=>{ let k=0; for(const o of G.props) if(o.alive&&['flamingo','gnome'].includes(o.k)&&!o.knocked&&k<3){ o.knocked=true; k++; } });
    run('mail',Q=>{ let k=0; for(const o of G.props) if(o.alive&&o.k==='mailbox'&&!o.knocked&&k<4){ o.knocked=true; k++; } });
    run('nurse',()=>{ G.stats.alarms+=3; });
    run('gnome',(Q,n)=>{ const g=G.props.find(o=>o.alive&&o.k==='gnome'&&!Q.seen.has(o)); g.pos=vadd(n.pos,V(0.8,0.3,0)); g.asleep=false; });
    run('bins',(Q,n)=>{ const g=G.props.find(o=>o.alive&&(o.k==='trash'||o.k==='wheelie')&&!Q.seen.has(o)); const i=G.props.indexOf(g); P.pos=vadd(n.pos,V(1.0,0,0)); P.held=i; g.held=true; });
    run('cart',(Q,n)=>{ const g=G.props.find(o=>o.alive&&o.k==='cart'&&!Q.seen.has(o)); g.pos=vadd(n.pos,V(-0.9,0.4,0)); g.asleep=false; });
    run('preach',()=>{ G.stats.hollered=(G.stats.hollered||0)+8; });
    run('tramp',()=>{ G.stats.bounces=(G.stats.bounces||0)+5; });
    run('air',()=>{ G.qAir=3.2; });
    run('propane',()=>{ G.stats.booms+=1; });
    run('drone',()=>{ G.stats.drones=(G.stats.drones||0)+1; });
    run('demo',()=>{ G.stats.wrecked+=12; });
    run('roof',()=>{ G.stats.roofs=(G.stats.roofs||0)+1; });
    run('chaos',()=>{ G.score+=5000; });
    run('fire',()=>{ G.stats.fires=(G.stats.fires||0)+1; });
    run('parcel',Q=>{ res.parcelHeld=P.held>=0&&G.props[P.held]===Q.parcel; res.destDist=Math.round(hlen(vsub(Q.dest,P.pos))); P.held=-1; Q.parcel.held=false; Q.parcel.pos=vadd(Q.dest,V(0.5,0.3,0.3)); Q.parcel.asleep=false; });
    run('bounty',Q=>{ res.markDist=Math.round(hlen(vsub(Q.target.pos,P.pos))); knockNpc(Q.target,V(4,3,0)); });
    run('tower',()=>{ const w=W.tower; P.pos=V((w.x0+w.x1)/2,w.y+0.05,(w.z0+w.z1)/2); P.vel=V(); });
    run('race',Q=>{ res.cps=Q.cps.length; for(const c of Q.cps){ P.pos=V(c.x,c.y,c.z); P.vel=V(); step(2); } },2);
    run('hydrant',()=>{ const h=G.props.find(o=>o.alive&&o.k==='hydrant'&&!o.knocked); h.knocked=true; });
    // a timed job running out of time
    const doug=giver('race'); G.questDone.delete('race'); goTo(doug); questTalk(doug); const t0=G.t; G.t+=46; step(2); out.timeout={failed:!G.quest&&!G.questDone.has('race'),hud:document.getElementById('quest').hidden};
    out.jobs=res; out.allDone=Object.values(res).filter(r=>r.done).length; out.paidTotal=Object.values(res).reduce((a,r)=>a+(r.paid||0),0);
    out.prof=Object.keys(PROF.quests).length;
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
        r = await page.evaluate(JS); r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
