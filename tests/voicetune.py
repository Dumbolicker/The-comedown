import asyncio, json, numpy as np
from playwright.async_api import async_playwright
import pathlib, os
GAME_URI=(pathlib.Path(__file__).resolve().parent.parent/'game'/'index.standalone.html').as_uri()
JS = r"""
async (eq) => { Object.assign(FRY_EQ,eq); const res=[];
  for(const [txt,f0] of [['Hey! What are you doing with that poop? Somebody call somebody!',120],['Is that... glowing? I can hear a choir!',230],['Step into my office. Mind the bucket.',105]]){
    const sr=22050, oc=new OfflineAudioContext(1,sr*5,sr); const dur=friedSpeak(txt,f0,1,1,0,oc,oc.destination); const buf=await oc.startRendering(); const x=buf.getChannelData(0); const n=Math.min(x.length,Math.ceil((dur+0.3)*sr));
    res.push(Array.from(x.slice(0,n)).map(v=>Math.round(v*10000)/10000)); } return res; }
"""
def stats(x,sr=22050):
    x=np.array(x); rms=np.sqrt((x**2).mean()); pk=np.abs(x).max(); X=np.abs(np.fft.rfft(x))**2; f=np.fft.rfftfreq(len(x),1/sr); t=X.sum()
    b=[100*X[(f>=lo)&(f<hi)].sum()/t for lo,hi in [(0,150),(150,500),(500,2000),(2000,5000),(5000,11025)]]
    return 'crest %4.1f dB | <150 %4.1f%% | 150-500 %4.1f%% | 0.5-2k %4.1f%% | 2-5k %3.1f%% | 5k+ %3.1f%%'%(20*np.log10(pk/rms),*b)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=os.environ.get("BT_CHROMIUM") or None, args=["--use-angle=swiftshader","--enable-unsafe-swiftshader"])
        page=await b.new_page(); await page.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        await page.goto(GAME_URI, wait_until="domcontentloaded"); await page.wait_for_timeout(1500)
        print('reference clip    : crest  7.3 dB | <150 61.5% | 150-500 18.1% | 0.5-2k 16.4% | 2-5k 2.4% | 5k+ 1.5%')
        for eq in [dict(low=12,sub=4,mid=7,drive=9),dict(low=10,sub=3,mid=8,drive=9),dict(low=9,sub=2,mid=9,drive=7),dict(low=8,sub=2,mid=10,drive=6)]:
            r=await page.evaluate(JS,eq); allx=np.concatenate([np.array(a) for a in r])
            print(json.dumps(eq), '\n   ', stats(allx))
        await b.close()
asyncio.run(main())
