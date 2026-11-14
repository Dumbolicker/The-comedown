"""Wrap game/index.html (the artifact body) in the same document skeleton claude.ai adds when it publishes,
so the game opens straight from disk and the tests can load it. Run after every edit to game/index.html."""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
SKELETON='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n</head><body>\n'
body=(ROOT/'game'/'index.html').read_text()
(ROOT/'game'/'index.standalone.html').write_text(SKELETON+body+'\n</body></html>')
print('wrote game/index.standalone.html')
