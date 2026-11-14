"""Copy the game into the desktop and phone (PWA) builds after an edit. Run make_standalone.py first.

- desktop/borrowed_time_desktop/dist/index.html = game/index.standalone.html
- pwa/index.html = the standalone page plus the manifest/home-screen tags and the service-worker registration
- pwa/sw.js gets a new cache VERSION so installed phones pick up the update
"""
import pathlib, re, shutil, sys, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
std = (ROOT / 'game' / 'index.standalone.html').read_text()

# --vendor: bundle the hash-checked Rapier file into the desktop build so demolition physics works offline (Steam)
desk = ROOT / 'desktop' / 'borrowed_time_desktop' / 'dist'
desk_html = std
if '--vendor' in sys.argv:
    ver = re.search(r"RAPIER_VER='([^']+)'", std).group(1)
    src = ROOT / '.refcache' / 'vendor' / f'rapier-{ver}.mjs'
    if not src.exists(): sys.exit('run python tests/vendor_rapier.py first')
    (desk / 'vendor').mkdir(exist_ok=True); shutil.copy(src, desk / 'vendor' / src.name)
    shutil.copy(ROOT / '.refcache' / 'vendor' / 'RAPIER-LICENSE.txt', desk / 'vendor' / 'RAPIER-LICENSE.txt')
    desk_html = std.replace('<body>\n', f"<body>\n<script>window.BT_RAPIER_URL='vendor/{src.name}';</script>\n", 1)
(desk / 'index.html').write_text(desk_html)

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
