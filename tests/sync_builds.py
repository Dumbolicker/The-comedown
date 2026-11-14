"""Copy the game into the desktop and phone (PWA) builds after an edit. Run make_standalone.py first.

- desktop/borrowed_time_desktop/dist/index.html = game/index.standalone.html
- pwa/index.html = the standalone page plus the manifest/home-screen tags and the service-worker registration
- pwa/sw.js gets a new cache VERSION so installed phones pick up the update
"""
import pathlib, re, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
std = (ROOT / 'game' / 'index.standalone.html').read_text()

(ROOT / 'desktop' / 'borrowed_time_desktop' / 'dist' / 'index.html').write_text(std)

HEAD = '''<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#0b0a12">
<link rel="apple-touch-icon" href="icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Borrowed Time">
'''
SW = "<script>if('serviceWorker' in navigator) addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));</script>\n"
lines = std.split('\n')
lines.insert(2, HEAD.rstrip('\n'))           # right after the skeleton's <style> line, as in the original PWA build
pwa = '\n'.join(lines)
pwa = pwa.replace('\n</body></html>', '\n' + SW + '</body></html>')
(ROOT / 'pwa' / 'index.html').write_text(pwa)

sw = ROOT / 'pwa' / 'sw.js'
ver = 'borrowed-time-' + time.strftime('%Y%m%d-%H%M')
sw.write_text(re.sub(r"VERSION='[^']*'", f"VERSION='{ver}'", sw.read_text(), count=1))
print('synced desktop + pwa builds, sw cache', ver)
