"""First person: the camera at your eyes, everything you could do in third person still working (moving, jumping, tackling,
throwing where you look, holding, flopping and coming back), the toggles (X, scroll, the 1P button, Settings), and every
verb in the catalogue run against a real target: each prop kind, people (talking, giving, shoving, helping up), Doc, doors,
slot machines, windows and walls, furniture (bed, counter, bar, cashier cage, pumps, cooler, register, Doc's chair),
the trampoline, stashes and the ground. Prints JSON; "errs" and "pageerrors" should be empty and "failed" should be []."""
import asyncio, json, os, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME_URI = (ROOT / 'game' / 'index.standalone.html').as_uri() + '?freeze=0.0001&demo=none'
VENDOR = ROOT / '.refcache' / 'vendor' / 'rapier-0.21.0.mjs'

JS = r"""
() => { const out={errs:[],failed:[],verbs:{}}; const I=o=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0,view:false,alt:false},o||{});
  const step=(n,f)=>{ for(let k=0;k<n;k++) update(1/60,f?f(k):I()); };
  const fail=(what,info)=>out.failed.push(what+(info!==undefined?' '+JSON.stringify(info):''));
  const ang=(a,b)=>Math.acos(clamp(vdot(vnorm(a),vnorm(b)),-1,1))*180/PI;
  try{
    startGame(); G.life=900; G.dollas=2000; setView(true,true); step(40); const P=G.player;
    // a clear patch of ground away from everything, for the props we drop in
    const clearAt=(x,z,r)=>!W.solids.some(s=>!s.gone&&s.y1>0.25&&s.x0<x+r&&s.x1>x-r&&s.z0<z+r&&s.z1>z-r)&&!G.props.some(o=>o.alive&&Math.abs(o.pos.x-x)<r&&Math.abs(o.pos.z-z)<r)&&!G.npcs.some(n=>n.alive&&Math.abs(n.pos.x-x)<r&&Math.abs(n.pos.z-z)<r);
    let OPEN=null; for(let t=0;t<400&&!OPEN;t++){ const x=rand(-HALF+20,HALF-20), z=rand(-HALF+20,HALF-20); if(clearAt(x,z,6)&&groundAt(x,z,0.3,1)<0.2) OPEN=V(x,0,z); }
    out.open=!!OPEN;
    const reset=()=>{ P.cone=false; if(P.seat) fpStand(); if(P.held>=0) dropHeld(V()); if(P.ragdoll){ P.ragdoll=false; P.noGetup=false; } P.getupT=0; P.charge=0; P.strikeT=0; G.fpTimers=[]; G.geysers=[]; G.life=900; G.dollas=Math.max(G.dollas,2000); G.state='play'; };
    const standAt=(pos)=>{ reset(); P.pos=V(pos.x,groundAt(pos.x,pos.z,0.3,(pos.y||0)+1.2),pos.z); P.vel=V(); RUB.teleport=true; step(2); };
    const aimAt=(pt)=>{ for(let k=0;k<4;k++){ const e=fpEye(), dx=pt.x-e.x, dy=pt.y-e.y, dz=pt.z-e.z; G.cam.yaw=Math.atan2(dx,dz); G.cam.pitch=clamp(-Math.atan2(dy,Math.hypot(dx,dz)),-1.45,1.45); } step(1); };   /* the eye leans forward as you look down, so settle it */
    const spawn=(kind,at,yaw)=>{ const o=makeProp({kind,x:at.x,y:0,z:at.z,yaw:yaw||0}); G.props.push(o); return o; };
    const run=(name,slot)=>{ const t=G.fpT, vb=fpVerbs(t), id=vb[slot]; const r=fpUse(slot); return {id,r}; };

    // ---- the view
    const v=G.view; out.view={fp:!!v.fp,near:+(v.near||0).toFixed(3),eye:+(v.pos.y-P.pos.y).toFixed(2),pitchRange:null};
    if(!v.fp||Math.abs(v.pos.y-P.pos.y-PH*0.92)>0.12) fail('eye height',out.view);
    step(1,()=>I({lookY:3})); const pmax=G.cam.pitch; step(1,()=>I({lookY:-6})); const pmin=G.cam.pitch; out.view.pitchRange=[+pmin.toFixed(2),+pmax.toFixed(2)]; G.cam.pitch=0;
    if(pmax<1.4||pmin>-1.4) fail('pitch range',out.view.pitchRange);

    // ---- moving, facing, jumping
    standAt(OPEN); G.cam.yaw=0.7; G.cam.pitch=0; const p0={...P.pos}; step(40,()=>I({my:1})); const mv=vsub(P.pos,p0);
    out.move={dir:+ang(V(mv.x,0,mv.z),fwd(0.7)).toFixed(1),faces:+Math.abs(P.yaw-0.7).toFixed(3)}; if(out.move.dir>8||out.move.faces>0.01) fail('walk where you look',out.move);
    step(1,()=>I({jump:true})); out.jump=+P.vel.y.toFixed(1); if(!(P.vel.y>5)) fail('jump',out.jump); step(60);

    // ---- holding and throwing where you look
    standAt(OPEN); const cr=spawn('crate',vadd(OPEN,V(1.4,0,0))); step(2); aimAt(cr.pos); const tk=run('take',0); step(2);
    const e=fpEye(), d=fpDir(); out.hold={took:P.held>=0&&G.props[P.held]===cr,inFront:+ang(vsub(cr.pos,e),d).toFixed(1),dist:+vlen(vsub(cr.pos,e)).toFixed(2)};
    if(!out.hold.took||out.hold.inFront>40||out.hold.dist>1.8) fail('hold in view',out.hold);
    G.cam.pitch=-0.45; step(2); const look=fpDir(); step(1,()=>I({tackle:true})); out.throw={released:P.held<0,angle:+ang(cr.vel,vadd(look,V(0,0.1,0))).toFixed(1),speed:+vlen(cr.vel).toFixed(1)};
    if(!out.throw.released||out.throw.angle>20) fail('throw where you look',out.throw);
    // tackle (charge) along the look
    standAt(OPEN); G.cam.yaw=-1.2; G.cam.pitch=0.1; step(1); step(1,()=>I({tackle:true})); out.tackle={charge:+P.charge.toFixed(2),dir:+ang(P.cdir,fwd(-1.2)).toFixed(1)}; if(!(P.charge>0)||out.tackle.dir>5) fail('tackle',out.tackle); step(40);
    // flop: the camera steps out while you're down and comes back when you're up
    standAt(OPEN); step(1,()=>I({flop:true})); step(30); out.flop={ragdoll:!!P.ragdoll,fpWhileDown:!!G.view.fp}; let k=0; while((P.ragdoll||P.getupT>0)&&k++<600) step(1); step(40); out.flop.fpAfter=!!G.view.fp;
    if(!out.flop.ragdoll||out.flop.fpWhileDown||!out.flop.fpAfter) fail('flop and come back',out.flop);
    // your head isn't drawn in first person (count instances in one render, first person vs third)
    standAt(OPEN); G.cam.pitch=0; step(40); render(); const cnt=()=>Object.values(DYN).reduce((a,b)=>a+b.n,0), v0=G.view;   /* only what drawing the player adds */
    G.view={...v0,fp:true}; let c0=cnt(); drawPlayer(DYN,P,1); const n1=cnt()-c0; G.view={...v0,fp:false}; c0=cnt(); drawPlayer(DYN,P,1); const n3=cnt()-c0; G.view=v0;
    out.headHidden={fp:n1,tp:n3}; if(!(n3-n1>=8)) fail('head hidden',out.headHidden);

    // ---- toggles: X through the keyboard handler, scrolling, the button, Settings rows
    out.toggles={};
    window.dispatchEvent(new KeyboardEvent('keydown',{key:'x'})); update(1/60,gatherInput(1/60)); window.dispatchEvent(new KeyboardEvent('keyup',{key:'x'})); out.toggles.keyX=G.fp===false;
    G.cam.dist=2.5; step(1,()=>I({zoom:0.8})); out.toggles.scrollIn=G.fp===true; step(1,()=>I({zoom:-0.8})); out.toggles.scrollOut=G.fp===false;
    $('viewBtn').click(); out.toggles.button=G.fp===true&&$('viewBtn').textContent==='3P';
    sTab='ctrl'; renderSettings(); const rows=[...document.querySelectorAll('#setBody .sl')].map(e=>e.textContent); sTab='comfort'; renderSettings(); rows.push(...[...document.querySelectorAll('#setBody .sl')].map(e=>e.textContent));
    out.toggles.settings=['Camera','First-person field of view','First-person head bob','Your body in first person','First / third person','Other action'].map(l=>rows.some(r=>r.startsWith(l)));
    if(Object.values(out.toggles).some(x=>x===false)||out.toggles.settings.includes(false)) fail('toggles',out.toggles);
    setView(true,true); step(40);

    // ---- every prop kind: both verbs on a fresh one
    const kinds=Object.keys(PROPV).filter(k=>PK[k]);
    for(const kind of kinds){ const res={};
      for(const slot of [0,1]){ const n0=G.props.length; standAt(OPEN); const o=spawn(kind,vadd(OPEN,V(1.15+Math.max(PK[kind].h[0],PK[kind].h[2]),0,0)),PI/2); step(3); o.asleep=true; o.vel=V(); o.ang=V();
        aimAt(V(o.pos.x,o.pos.y+(kind==='car'?0.2:0),o.pos.z)); const t=G.fpT; res.targeted=t&&t.k==='prop'&&t.o===o; res.verbs=fpVerbs(t);
        const r=run(kind,slot); res['r'+slot]=r.r; if(slot===0&&kind==='potty'){ step(1,()=>I({tackle:true})); res.pottyTackle=!(P.charge>0)&&!!P.seat; step(170); res.potty={stood:!P.seat,life:+G.life.toFixed(1)}; if(!res.pottyTackle||!res.potty.stood) fail('potty',res); }
        step(3); render(); o.alive=false; o.fuse=-1; o.jet=0; reset(); for(let i=n0;i<G.props.length;i++){ G.props[i].alive=false; G.props[i].fuse=-1; G.props[i].jet=0; } }
      out.verbs[kind]=res; if(!res.targeted||res.r0===null||res.r0==='far'||res.r0==='error'||(res.verbs[1]&&(res.r1===null||res.r1==='far'||res.r1==='error'))) fail('prop '+kind,res); }

    // ---- held things: use, place, give, bin, drop
    { const r={}; standAt(OPEN); const b=spawn('bottle',vadd(OPEN,V(1.2,0,0))); step(2); aimAt(b.pos); fpUse(0); r.holding=P.held>=0;
      G.cam.pitch=0.1; step(1); r.useheld=fpUse(1); G.cam.pitch=1.1; step(2); r.verbsDown=fpVerbs(G.fpT); r.place=fpUse(0); step(2); r.placed=P.held<0&&b.alive&&Math.abs(b.pos.y-groundAt(b.pos.x,b.pos.z,0.1,b.pos.y+0.5)-extY(b.rot,b.half))<0.2;
      const can=spawn('trash',vadd(OPEN,V(-1.4,0,0))); step(2); aimAt(b.pos); fpUse(0); aimAt(V(can.pos.x,can.pos.y+0.3,can.pos.z)); r.verbsCan=fpVerbs(G.fpT); r.bin=fpUse(0); r.binned=!b.alive;
      can.alive=false; out.verbs.held=r; if(!r.holding||r.place!=='placed'||!r.placed||r.bin!=='binned'||!r.binned) fail('held verbs',r); reset(); }

    // ---- people
    { const r={}; const civ=G.npcs.find(n=>n.alive&&npcUp(n)&&n.kind==='civ'&&!n.role); standAt(OPEN);
      civ.pos=vadd(P.pos,V(1.6,0,0)); civ.state='idle'; civ.idleFor=30; civ.vel=V(); civ.talkCd=0; step(2); aimAt(vadd(civ.pos,V(0,1.3,0))); r.target=G.fpT&&G.fpT.k; r.verbs=fpVerbs(G.fpT);
      r.talk=fpUse(0); civ.talkCd=0; const c0={...civ.pos}; aimAt(vadd(civ.pos,V(0,1.3,0))); r.shove=fpUse(1); r.moved=+hlen(vsub(civ.pos,c0)).toFixed(2);
      civ.pos=vadd(P.pos,V(1.6,0,0)); civ.state='idle'; const b=spawn('bottle',vadd(P.pos,V(-1.0,0,0.3))); step(2); aimAt(b.pos); fpUse(0); aimAt(vadd(civ.pos,V(0,1.3,0))); r.giveVerbs=fpVerbs(G.fpT); r.give=fpUse(0); r.gave=!b.alive;
      knockNpc(civ,V(0,2,0)); let k=0; while(civ.state==='rag'&&civ.still<0.5&&k++<300) step(1); aimAt(npcCenter(civ)); r.downVerbs=fpVerbs(G.fpT); r.pockets=fpUse(1); aimAt(npcCenter(civ)); r.help=fpUse(0); step(4); r.gotUp=civ.state!=='rag';
      out.verbs.people=r; if(r.target!=='npc'||!r.talk||r.shove!=='shoved'||!(r.moved>0.3)||r.give!=='gave'||r.pockets===null||r.help!=='helped'||!r.gotUp) fail('people',r); reset(); }
    { const r={}; const cop=makeNpc(-1,0,'cop'); G.npcs.push(cop); standAt(OPEN); cop.pos=vadd(P.pos,V(1.6,0,0)); cop.state='idle'; cop.idleFor=30; step(2); aimAt(vadd(cop.pos,V(0,1.3,0)));
      r.verbs=fpVerbs(G.fpT); r.talk=fpUse(0); const h0=G.heat; r.shove=fpUse(1); r.heatUp=+(G.heat-h0).toFixed(2); cop.alive=false; out.verbs.cop=r; if(r.talk!=='cop'||r.shove!=='shoved'||!(r.heatUp>=0.9)) fail('cop',r); G.heat=0; reset(); }
    { const r={}; const lupe=G.npcs.find(n=>n.role==='quest'&&QUESTS[n.qi].id==='ernesto'); G.questDone.delete('ernesto'); standAt(vadd(lupe.pos,vmul(fwd(lupe.home.yaw),1.8))); aimAt(vadd(lupe.pos,V(0,1.2,0)));
      r.verbs=fpVerbs(G.fpT); r.wave=fpUse(1); r.talk=fpUse(0); r.quest=G.quest?G.quest.q.id:null; if(G.quest){ questCleanup(G.quest); G.quest=null; } out.verbs.quest=r; if(r.talk!=='quest'||r.quest!=='ernesto'||r.wave!=='waved') fail('quest giver',r); reset(); }
    { const r={}; const c=W.doc.pos; standAt(vadd(c,V(0,0,1.9))); aimAt(vadd(c,V(0,1.2,0))); r.target=G.fpT&&G.fpT.k; r.verbs=fpVerbs(G.fpT); r.chat=fpUse(1); r.shop=fpUse(0); r.state=G.state; closeDoc(); G.state='play';
      out.verbs.doc=r; if(r.target!=='doc'||r.shop!=='doc'||r.state!=='doc'||r.chat!=='chat') fail('doc',r); reset(); }

    // ---- doors
    { const r={}; const d=W.doors.find(d=>!d.broken&&!(d.yb>0.5)&&W.houses.some(h=>h.bld===d.bld)&&!W.condemned.has(d.bld)), c=doorCenter(d), nrm=d.axis==='x'?V(0,0,1):V(1,0,0);
      const sides=[vadd(c,vmul(nrm,1.6)),vadd(c,vmul(nrm,-1.6))].filter(p=>!W.interiors.some(i=>p.x>i.x0&&p.x<i.x1&&p.z>i.z0&&p.z<i.z1)); standAt(sides[0]||vadd(c,vmul(nrm,1.6))); aimAt(V(c.x,(d.yb||0)+1.1,c.z));
      r.target=G.fpT&&G.fpT.k; r.verbs=fpVerbs(G.fpT); r.knock=fpUse(1); step(80); r.startOpen=+d.open.toFixed(2); r.first=fpUse(0); step(60); r.after1=+d.open.toFixed(2); aimAt(V(c.x,(d.yb||0)+1.1,c.z)); r.second=fpUse(0); step(60); r.after2=+d.open.toFixed(2);
      const shutThen=r.first==='closed'?r.after1:r.after2, openThen=r.first==='opened'?r.after1:r.after2; r.shutWhileNear=shutThen; r.openAfter=openThen;
      out.verbs.door=r; if(r.target!=='door'||r.knock!=='knocked'||![r.first,r.second].includes('closed')||![r.first,r.second].includes('opened')||!(shutThen<0.2)||!(openThen>0.5)) fail('door',r); reset(); }

    // ---- slot machine, a window, a wall, a condemned wall
    const frontOf=(b,dist)=>{ const s=b.s, c=boxCenter(s), thin=(s.x1-s.x0)<(s.z1-s.z0)?'x':'z', n=thin==='x'?V(1,0,0):V(0,0,1);
      const cands=[vadd(c,vmul(n,dist)),vadd(c,vmul(n,-dist))].map(p=>V(p.x,0,p.z)); return cands.find(p=>!W.interiors.some(i=>p.x>i.x0&&p.x<i.x1&&p.z>i.z0&&p.z<i.z1))||cands[0]; };
    { const r={}; const sb=W.slotsB.find(b=>b.alive), c=boxCenter(sb.s), f=fwd(sb.yaw); standAt(vadd(V(c.x,0,c.z),vmul(f,1.5))); aimAt(c); r.target=G.fpT&&G.fpT.k; r.verbs=fpVerbs(G.fpT);
      r.play=fpUse(0); r.state=G.state; closeSlots(); G.state='play'; aimAt(c); r.kick=fpUse(1); out.verbs.slot=r; if(r.play!=='slots'||r.state!=='slots'||!r.kick||r.kick==='far') fail('slot',r); reset(); }
    for(const [name,find] of [['window',b=>b.mat==='glass'&&W.houses.some(h=>h.bld===b.bld)&&!W.condemned.has(b.bld)],['wall',b=>b.mat==='wood'&&!b.roof&&W.houses.some(h=>h.bld===b.bld)&&!W.condemned.has(b.bld)&&b.s.y0<0.1],['condemned wall',b=>!b.roof&&W.condemned.has(b.bld)&&W.houses.some(h=>h.bld===b.bld)&&b.s.y0<0.1&&b.mat!=='glass']]){
      const r={}; const b=BRK.find(x=>x.alive&&find(x)); if(!b){ fail(name+' missing'); continue; } const c=boxCenter(b.s); standAt(frontOf(b,1.3)); aimAt(c); r.target=G.fpT&&G.fpT.k; r.same=!!(G.fpT&&G.fpT.b===b); r.verbs=fpVerbs(G.fpT);
      const hp0=b.hp; r.a=fpUse(0); aimAt(c); r.b=fpUse(1); r.damaged=b.hp<hp0||!b.alive; out.verbs[name]=r;
      if(r.target!=='panel'||!r.a||r.a==='far'||!r.b||r.b==='far'||(name==='condemned wall'&&!r.damaged)||(name==='wall'&&r.damaged)) fail(name,r); reset(); }

    // ---- furniture and machines
    for(const tag of ['bed','counter','bar','cage','pump','cooler','register','docchair','vials','tvstand','nightstand','trampoline']){
      const S=W.solids.find(s=>tag==='trampoline'?s.bouncy:s.fp===tag); if(!S){ fail('no '+tag); continue; } const c=V((S.x0+S.x1)/2,0,(S.z0+S.z1)/2), hx=(S.x1-S.x0)/2, hz=(S.z1-S.z0)/2;
      const cands=[];
      for(const dd of [0.6,0.75,1.1,1.5]) for(const [ux,uz] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]) cands.push(V(c.x+ux*(hx+dd),S.y0,c.z+uz*(hz+dd)));
      const ok=cands.filter(p=>{ const g=groundAt(p.x,p.z,0.3,S.y0+0.6); return Math.abs(g-S.y0)<0.5&&!W.solids.some(s=>!s.gone&&!s.hidden&&s!==S&&s.y1>g+0.3&&s.y0<g+1.6&&p.x>s.x0-0.22&&p.x<s.x1+0.22&&p.z>s.z0-0.22&&p.z<s.z1+0.22); }); cands.length=0; cands.push(...ok);
      const r={}; const face=p=>V(clamp(p.x,S.x0+0.02,S.x1-0.02),Math.min(S.y1-0.08,S.y0+0.75),clamp(p.z,S.z0+0.02,S.z1-0.02)); let at=null;
      for(const q of cands){ standAt(q); aimAt(face(q)); if(G.fpT&&G.fpT.s===S){ at=q; break; } } if(!at){ fail('no line of sight to '+tag,cands.length); continue; }
      r.target=G.fpT&&G.fpT.k; r.same=!!(G.fpT&&G.fpT.s===S); r.verbs=fpVerbs(G.fpT);
      const tA=G.fpT; r.a=fpUse(0); const seat=P.seat?{kind:P.seat.kind,lie:!!P.seat.lie,eyeAbove:+(fpEye().y-S.y1).toFixed(2)}:null; if(seat) r.seat=seat; if(G.state==='doc'){ closeDoc(); G.state='play'; } reset(); standAt(at);
      aimAt(face(at)); r.b=fpUse(1); if(P.seat) r.seatB=P.seat.kind; out.verbs[tag]=r; reset();
      if(r.target!=='solid'||!r.same||!r.a||r.a==='far'||r.a==='error'||(r.verbs[1]&&(!r.b||r.b==='far'||r.b==='error'))) fail(tag,r); }

    // ---- a stash, the ground, sitting and standing back up
    { const r={}; const s=G.stashes[0]; let seen=false; for(let a=0;a<16&&!seen;a++){ const q=vadd(s.pos,V(Math.cos(a*0.3927)*2.2,0,Math.sin(a*0.3927)*2.2)); standAt(q); aimAt(vadd(s.pos,V(0,0.85,0))); seen=!!(G.fpT&&G.fpT.k==='stash'); } r.verbs=fpVerbs(G.fpT); const n0=G.stashes.length; r.take=fpUse(0); r.took=G.stashes.length<n0||!G.stashes.includes(s);
      out.verbs.stash=r; if(r.take!=='stash'||!r.took) fail('stash',r); reset(); }
    { const r={}; standAt(OPEN); G.cam.pitch=1.1; step(2); r.verbs=fpVerbs(G.fpT); r.sit=fpUse(0); r.seated=!!P.seat; r.eye=+(fpEye().y-P.pos.y).toFixed(2); step(10,()=>I({my:1})); r.stood=!P.seat;
      standAt(OPEN); G.cam.pitch=1.1; step(2); r.lie=fpUse(1); r.lying=!!(P.seat&&P.seat.lie); render(); out.verbs.ground=r; if(!r.seated||!r.stood||!r.lying||r.eye>1.1) fail('ground',r); reset(); }
    { const r={}; standAt(OPEN); const ch=spawn('couch',vadd(OPEN,V(1.8,0,0)),-PI/2); step(4); ch.asleep=true; aimAt(ch.pos); r.verbs=fpVerbs(G.fpT); r.sit=fpUse(0); step(30); r.seat=P.seat&&P.seat.kind;
      r.couchStill=+hlen(vsub(ch.pos,vadd(OPEN,V(1.8,0,0)))).toFixed(2); r.eye=+(fpEye().y-ch.pos.y).toFixed(2); render(); step(5,()=>I({jump:true})); r.stood=!P.seat; ch.alive=false;
      out.verbs.couchSit=r; if(r.seat!=='couch'||!(r.couchStill<0.3)||!r.stood) fail('couch',r); reset(); }
    // seated: what you can reach from the seat still works (the TV from the couch); looking at nothing, E gets you up
    { const r={}; standAt(OPEN); const ch=spawn('couch',vadd(OPEN,V(1.8,0,0)),-PI/2), tv=spawn('tv',vadd(OPEN,V(0.4,0,1.5)),PI/2); step(4); ch.asleep=true; tv.asleep=true; aimAt(ch.pos); fpUse(0); step(20);
      aimAt(tv.pos); r.verbs=fpVerbs(G.fpT); const off0=!!tv.fpOff; step(1,()=>I({grab:true})); r.toggled=!!tv.fpOff!==off0; r.stillSeated=!!P.seat;
      G.cam.pitch=-1.3; step(2); r.upVerbs=fpVerbs(G.fpT); step(1,()=>I({grab:true})); r.stood=!P.seat; ch.alive=false; tv.alive=false;
      out.verbs.seated=r; if(r.verbs[0]!=='power'||!r.toggled||!r.stillSeated||r.upVerbs[0]!=='getup'||!r.stood) fail('seated verbs',r); reset(); }
    { const r={}; standAt(OPEN); const c=spawn('cone',vadd(OPEN,V(1.2,0,0))); step(2); aimAt(c.pos); r.wear=fpUse(1); r.cone=!!P.cone; step(1,()=>I({flop:true})); step(20); r.fell=!P.cone&&G.props.some(o=>o.alive&&o.k==='cone'&&hlen(vsub(o.pos,P.pos))<7);
      out.verbs.coneHat=r; if(!r.cone||!r.fell) fail('cone hat',r); let k=0; while((P.ragdoll||P.getupT>0)&&k++<600) step(1); reset(); }
    out.fpVerbs=G.stats.fpVerbs||0; out.kinds=kinds.length;
    step(30);
  }catch(e){ out.errs.push(String(e&&e.stack||e).slice(0,700)); }
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
        r['pageerrors'] = errs[:6]; await b.close()
    print(json.dumps(r, indent=1))

asyncio.run(main())
