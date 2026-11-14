import asyncio, sys
from playwright.async_api import async_playwright
import pathlib, os
GAME_URI=(pathlib.Path(__file__).resolve().parent.parent/'game'/'index.standalone.html').as_uri()
U=GAME_URI
I="(o)=>Object.assign({mx:0,my:0,sprint:false,jump:false,jumpHeld:false,tackle:false,grab:false,grabHeld:false,flop:false,holler:false,poop:false,charge:false,lookX:0,lookY:0,zoom:0},o||{})"
async def shot(b,q,name,js=None,wait=5000,after=1500,w=1280,h=720,mobile=False,dsf=2):
    ctx=await b.new_context(viewport={"width":w,"height":h},device_scale_factor=dsf,is_mobile=mobile,has_touch=mobile); page=await ctx.new_page()
    errs=[]; page.on("pageerror", lambda e: errs.append(str(e)))
    await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    await page.goto(U+q, wait_until="domcontentloaded"); await page.wait_for_timeout(wait)
    if js: print(name, await page.evaluate(js)); await page.wait_for_timeout(after)
    await page.screenshot(path=str(pathlib.Path(__file__).resolve().parent.parent/"screenshots"/(name+".png")),timeout=180000); print(name,"errs:",errs[:3],flush=True); await ctx.close()
LOOK1="{skin:4,height:1.06,build:1.0,hair:'mohawk',hairCol:8,top:'trench',topCol:1,pants:'jeans',pantsCol:1,shoeCol:2,hat:'none',hatCol:3,face:'goatee',eyes:'shades'}"
LOOK2="{skin:6,height:0.98,build:1.25,hair:'afro',hairCol:1,top:'flannel',topCol:3,pants:'shorts',pantsCol:3,shoeCol:0,hat:'none',hatCol:3,face:'beard',eyes:'round'}"
CUSTOM_JS=lambda look,tab: "()=>{ Object.assign(CUSTOM,%s); applyLook(); saveLook(); $('customBtn').click(); document.querySelector('.ctab[data-tab=\"%s\"]').click(); G.prevYaw=0.35; return JSON.stringify(CUSTOM).length; }"%(look,tab)
DOCW="""()=>{ DEMO_INPUT=null; const I=%s, P=G.player, d=W.doc.pos; G.clock=19.7; G.cyber={strips:true,lungs:true,gullet:true,liver:true,septum:true};
  P.pos=V(d.x-1.3,0,d.z+2.1); P.vel=V(); P.yaw=PI-0.5; G.cam.yaw=PI+0.32; G.cam.pitch=0.1; G.cam.dist=G.cam.cur=5.2; G.cam.focus=vadd(P.pos,V(0,1.4,0));
  G.npcs=G.npcs.filter(n=>hlen(vsub(n.pos,d))>14); G.stashes=G.stashes.filter(s=>hlen(vsub(s.pos,d))>6);
  for(let i=0;i<90;i++) update(1/60,I()); docSay('Step into my office. Mind the bucket.'); P.lineT=0; G.player.line=''; return {doc:[d.x,d.z]}; }"""%I
DOCSHOP="""()=>{ DEMO_INPUT=null; G.dollas=2140; G.cyber={strips:true,septum:true}; const P=G.player; P.pos=vadd(W.doc.pos,V(0,0,1.8)); for(let i=0;i<5;i++) update(1/60,(%s)()); syncHUD(1/60); G.nearDoc=true; openDoc(); docSay('Hold still. This will pinch. A lot.'); return G.state; }"""%I
FLY="""()=>{ DEMO_INPUT=null; const I=%s, P=G.player; transform('dragon'); P.formT=999; G.clock=17.0; P.pos=V(-18,0,10); P.vel=V(); P.yaw=0.6; G.cam.yaw=0.6+0.5; G.cam.pitch=0.22; G.cam.dist=G.cam.cur=8;
  for(let i=0;i<30;i++) update(1/60,I()); update(1/60,I({jump:true,jumpHeld:true})); for(let i=0;i<200;i++) update(1/60,I({jumpHeld:true,my:1})); for(let i=0;i<7;i++) update(1/60,I({jumpHeld:true,my:1})); P.lineT=0; return {y:+P.pos.y.toFixed(1),flying:P.flying}; }"""%I
PARADE="""()=>{ DEMO_INPUT=null; const I=%s, P=G.player; P.pos=V(0,0,-26); P.vel=V(); P.yaw=0.9; G.cam.yaw=0.9+2.4; G.cam.pitch=0.16; G.cam.dist=G.cam.cur=5.5; G.npcs=G.npcs.filter(n=>hlen(vsub(n.pos,P.pos))>10);
  doubloonRush(); const slot=30/14, tEnd=slot*12+0.32; let k=0; while(G.parade&&G.parade.t<tEnd&&k<4000){ update(1/60,I()); k++; } G.cam.yaw=P.yaw+2.5; P.lineT=0; G.player.line=''; return {form:P.form,ghost:G.parade&&G.parade.ghost&&G.parade.ghost.form,fade:G.parade&&+G.parade.fade.toFixed(2)}; }"""%I
CHARGE="""()=>{ DEMO_INPUT=null; const I=%s, P=G.player; transform('minotaur'); P.formT=999; G.clock=17.2; P.pos=V(0,0,-30); P.vel=V(); P.yaw=0; G.cam.yaw=0; G.cam.pitch=0.1; G.cam.dist=G.cam.cur=7; G.npcs=G.npcs.filter(n=>hlen(vsub(n.pos,P.pos))>16);
  const mk=(dx,dz)=>{ const n=makeNpc(0,0,'civ'); n.pos=V(dx,0,-30+dz); n.state='idle'; n.idleFor=99; n.startleCd=99; n.talkCd=99; n.yaw=PI; G.npcs.push(n); return n; }; const a=mk(0.2,6.2), b=mk(-0.9,9.5);
  for(let i=0;i<20;i++) update(1/60,I()); update(1/60,I({charge:true})); let hit=-1; for(let i=0;i<70;i++){ update(1/60,I()); if(hit<0&&a.state==='rag') hit=i; if(hit>=0&&i>=hit+9) break; } G.cam.yaw=-1.25; P.lineT=0; return {npc:a.state,hit,horn:P.horn,z:+(P.pos.z+30).toFixed(1),ay:+a.pos.y.toFixed(2)}; }"""%I
POOP="""()=>{ DEMO_INPUT=null; const I=%s, P=G.player; G.clock=19.4; P.pos=V(0,0,-24); P.vel=V(); P.yaw=0.25; G.cam.yaw=0.25+2.75; G.cam.pitch=0.16; G.cam.dist=G.cam.cur=3.6; G.npcs=G.npcs.filter(n=>hlen(vsub(n.pos,P.pos))>12);
  transform('demon'); P.formT=999; for(let i=0;i<150;i++) update(1/60,I()); P.poopCd=0; update(1/60,I({poop:true})); for(let i=0;i<60;i++) update(1/60,I()); dropPoop(); for(let i=0;i<200;i++) update(1/60,I());
  const hp=G.props[G.props.length-1]; hp.pos=V(P.pos.x+0.9,hp.pos.y,P.pos.z+0.5);
  untransform(); transform('angel'); P.formT=999; for(let i=0;i<200;i++) update(1/60,I()); P.poopCd=0; update(1/60,I({poop:true})); for(let i=0;i<120;i++) update(1/60,I()); G.parts=G.parts.filter(q=>q.kind!=='confetti'&&q.kind!=='smoke'); G.pops=[]; G.cam.dist=G.cam.cur=2.6; G.cam.pitch=0.1; P.lineT=0; return {held:P.poop&&P.poop.kind,ground:hp.pkind}; }"""%I
FOLD="""()=>{ DEMO_INPUT=null; const I=%s, P=G.player; G.clock=18.4; P.pos=V(0,0,-22); P.vel=V(); P.yaw=0.4; G.cam.yaw=0.4+2.3; G.cam.pitch=0.14; G.cam.dist=G.cam.cur=4.6; G.npcs=G.npcs.filter(n=>hlen(vsub(n.pos,P.pos))>12);
  const n=makeNpc(0,0,'civ'); n.pos=V(P.pos.x+1.6,0,P.pos.z+1.9); n.state='idle'; n.idleFor=99; n.startleCd=99; n.talkCd=99; n.yaw=PI+0.6; G.npcs.push(n);
  pickup({sub:SUB('henny'),pos:{...P.pos},life:9,seed:1,laced:true}); let k=0; while(!(P.foldT>0)&&k<300){ update(1/60,I()); k++; } for(let i=0;i<64;i++) update(1/60,I());
  n.talkCd=0; say(n,'Buddy? You good?',3); P.lineT=0; P.line=''; return {foldT:+P.foldT.toFixed(1),k:+foldK(P).toFixed(2)}; }"""%I
async def main():
    only=sys.argv[1:]
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
        jobs=[("custom_desktop","",CUSTOM_JS(LOOK1,'fit'),dict(wait=3500,after=2500)),
              ("custom_phone","",CUSTOM_JS(LOOK2,'hair'),dict(wait=3500,after=2500,w=390,h=844,mobile=True)),
              ("doc_world","?demo=shot&freeze=0.05",DOCW,{}),
              ("doc_shop","?demo=shot&freeze=0.05",DOCSHOP,dict(after=1200)),
              ("fly","?demo=shot&freeze=0.05",FLY,{}),
              ("parade","?demo=shot&freeze=0.05",PARADE,{}),
              ("charge","?demo=shot&freeze=0.05",CHARGE,{}),
              ("poop_kinds","?demo=shot&freeze=0.05",POOP,{}),
              ("fold","?demo=shot&freeze=0.05",FOLD,{})]
        for name,q,js,kw in jobs:
            if only and name not in only: continue
            await shot(b,q,name,js=js,**kw)
        await b.close()
asyncio.run(main())
