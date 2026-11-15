"""Embed assets/textures/*.jpg (CC0, see LICENSES.md) into game/index.html as data URIs between the TEXDATA markers.
Data URIs keep the single-file game working everywhere (claude.ai link, file://, PWA, Tauri) and stay WebGL-safe.
Run after changing a texture: python tests/embed_textures.py"""
import base64, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYERS = ['asphalt', 'concrete', 'grass', 'brick', 'siding', 'roof', 'plaster', 'metal', 'pavers']
game = ROOT / 'game' / 'index.html'
src = game.read_text(encoding='utf-8')
parts = []
for k in LAYERS:
    b64 = base64.b64encode((ROOT / 'assets' / 'textures' / f'{k}.jpg').read_bytes()).decode()
    parts.append(f"{k}:'data:image/jpeg;base64,{b64}'")
block = '/*TEXDATA-BEGIN*/const TEXDATA={' + ','.join(parts) + '};/*TEXDATA-END*/'
new, n = re.subn(r'/\*TEXDATA-BEGIN\*/.*?/\*TEXDATA-END\*/', lambda m: block, src, flags=re.S)
assert n == 1, 'TEXDATA markers not found'
game.write_text(new, encoding='utf-8')
print(f'embedded {len(LAYERS)} textures, game/index.html is now {len(new.encode())//1024} KB')
