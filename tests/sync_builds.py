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
# Tauri bridge: lets the game save its profile through the shell (Steam Cloud in the Steam build) and unlock achievements
BRIDGE = ("<script>(function(){ var T=window.__TAURI__; if(!T||!T.core) return; var inv=T.core.invoke;"
  " window.BT_PLATFORM={name:'desktop',saveProfile:function(p){ inv('save_profile',{json:JSON.stringify(p)}).catch(function(){}); },"
  " loadProfile:function(){ return inv('load_profile'); }, achievement:function(f){ inv('unlock_achievement',{feat:f}).catch(function(){}); }};"
  " inv('platform_name').then(function(n){ window.BT_PLATFORM.name=n; }).catch(function(){}); })();</script>\n")
desk_html = desk_html.replace('<body>\n', '<body>\n' + BRIDGE, 1)
(desk / 'index.html').write_text(desk_html)

HEAD = '''<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#0b0a12">
<link rel="apple-touch-icon" href="icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Borrowed Time">
<meta name="description" content="A 3D physics-comedy sandbox on a draining clock. Wreck the town, dodge the cops, beat the comedown. Plays in the browser, no install.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Borrowed Time">
<meta property="og:title" content="Borrowed Time">
<meta property="og:description" content="A 3D physics-comedy sandbox on a draining clock. Wreck the town, dodge the cops, beat the comedown. Tap to play.">
<meta property="og:url" content="https://dumbolicker.github.io/The-comedown/">
<meta property="og:image" content="https://dumbolicker.github.io/The-comedown/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#ff4fd8">
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
