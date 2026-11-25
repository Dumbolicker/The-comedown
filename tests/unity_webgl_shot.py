"""Plays the Unity WebGL build of Borrowed Time in headless Chromium and takes screenshots.

Serves the build folder on 127.0.0.1, waits for Unity to start, then holds W (walk), Space (jump) and F (tackle)
and saves screenshots/unity_webgl_<n>.png. Prints the browser console's errors and the frame rate Unity reports.

Usage: python tests/unity_webgl_shot.py <build-dir> [seconds-to-wait-for-load]
(BT_CHROMIUM=/path/to/chrome picks the browser, like the other tests.)
"""
import asyncio
import functools
import http.server
import os
import pathlib
import sys
import threading

from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'screenshots'


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      '.wasm': 'application/wasm', '.js': 'application/javascript', '.data': 'application/octet-stream'}

    def log_message(self, *args):
        pass


def serve(directory):
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(directory)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def main():
    build = pathlib.Path(sys.argv[1]).resolve()
    load_wait = float(sys.argv[2]) if len(sys.argv) > 2 else 120
    if not (build / 'index.html').exists():
        sys.exit(f'No index.html in {build}')
    OUT.mkdir(exist_ok=True)
    httpd = serve(build)
    url = f'http://127.0.0.1:{httpd.server_address[1]}/index.html'
    logs, errors = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get('BT_CHROMIUM') or None,
                                          args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        page = await (await browser.new_context(viewport={'width': 1280, 'height': 720})).new_page()
        page.on('console', lambda m: (errors if m.type == 'error' else logs).append(m.text))
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(url, wait_until='load', timeout=120000)
        # Unity's loader replaces the loading bar with the running canvas; the game logs its first frame.
        started = False
        for _ in range(int(load_wait)):
            if any('Borrowed Time' in t or 'unityInstance' in t for t in logs) or await page.evaluate(
                    "() => !!document.querySelector('#unity-loading-bar') && getComputedStyle(document.querySelector('#unity-loading-bar')).display === 'none'"):
                started = True
                break
            await page.wait_for_timeout(1000)
        print('started:', started, '| console lines:', len(logs), '| errors:', len(errors), flush=True)
        await page.wait_for_timeout(8000)
        await page.screenshot(path=str(OUT / 'unity_webgl_1.png'))
        canvas = page.locator('canvas').first
        await canvas.click()
        await page.keyboard.down('w')
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(OUT / 'unity_webgl_2.png'))
        await page.keyboard.press('Space')
        await page.wait_for_timeout(600)
        await page.keyboard.press('f')
        await page.wait_for_timeout(2500)
        await page.keyboard.up('w')
        await page.screenshot(path=str(OUT / 'unity_webgl_3.png'))
        counts = {}
        for t in errors:
            key = t.strip().splitlines()[0][:160] if t.strip() else t
            counts[key] = counts.get(key, 0) + 1
        for key, n in sorted(counts.items(), key=lambda kv: -kv[1])[:12]:
            print(f'error x{n}:', key)
        for t in [t for t in logs if 'fps' in t.lower() or 'Borrowed Time' in t][:6]:
            print('log:', t[:200])
        await browser.close()
    httpd.shutdown()


asyncio.run(main())
