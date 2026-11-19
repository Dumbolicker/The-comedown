"""Fetch the pinned Rapier build into .refcache/vendor and refuse it unless its SHA-384 matches the hash in the game.

Used by the tests (they serve it in place of the CDN) and by sync_builds.py --vendor (offline desktop/PWA builds).
    python tests/vendor_rapier.py
"""
import base64, hashlib, pathlib, re, shutil, subprocess, sys, tarfile, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
game = (ROOT / 'game' / 'index.html').read_text()
VER = re.search(r"RAPIER_VER='([^']+)'", game).group(1)
SHA = re.search(r"RAPIER_SHA384='([^']+)'", game).group(1)
OUT = ROOT / '.refcache' / 'vendor'
DEST = OUT / f'rapier-{VER}.mjs'

def sha384(b): return base64.b64encode(hashlib.sha384(b).digest()).decode()

if DEST.exists() and sha384(DEST.read_bytes()) == SHA:
    print('ok', DEST); sys.exit(0)
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(['npm', 'pack', f'@dimforge/rapier3d-compat@{VER}', '--silent'], cwd=tmp, check=True, stdout=subprocess.DEVNULL)
    tgz = next(pathlib.Path(tmp).glob('*.tgz'))
    with tarfile.open(tgz) as t:
        data = t.extractfile('package/dist/rapier.mjs').read()
        lic = t.extractfile('package/LICENSE').read()
if sha384(data) != SHA:
    sys.exit(f'REFUSED: rapier {VER} hash {sha384(data)} does not match the pinned {SHA}')
DEST.write_bytes(data); (OUT / 'RAPIER-LICENSE.txt').write_bytes(lic)
print('fetched and verified', DEST)
