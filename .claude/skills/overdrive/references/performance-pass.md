# Final pass: performance, storage and caching

Run this at the end of every project or milestone. It's a measuring exercise first and an optimizing exercise second.

## 1. Performance

**Measure the baseline first, with the same scene and settings each time.**

| What | How |
| --- | --- |
| Frame time | p50/p95 in ms over at least 600 frames. Split CPU time (update/simulation) from GPU/render time where you can. |
| Startup | Time to first interactive frame, cold and warm cache. |
| Memory | JS heap or process RSS after 2 minutes of play. Look for growth, which means a leak. |
| Size | Bundle/download size and largest assets. Report compressed sizes. |
| Device | Use a real phone when possible. Headless and software rendering only show *relative* change. |

Then fix the top offenders, one at a time, and re-measure each:

- Allocation in hot loops (per-frame objects and closures). Reuse buffers.
- O(n²) work that grew. Add spatial grids, sleeping and early-outs.
- Draw calls and instances. Batch, cull, and add LOD.
- Overdraw and expensive shaders on phones. Cap DPR, shadow resolution and light count.
- Work done every frame that could run on change: DOM writes, buffer uploads, text measurement.

Rust builds: `--release`, `lto = true`, `codegen-units = 1`, `strip = true`, and `opt-level = "s"` for size-sensitive targets (WASM, mobile).

## 2. Storage

- `git count-objects -vH` for the repo size. List the largest tracked files (`git ls-files -z | xargs -0 du -h | sort -h | tail`).
- Remove dead files, unused assets and stale build output. Gitignore build dirs and caches (`target/`, `node_modules/`, `.refcache/`, `__pycache__/`).
- Compress assets: images to WebP/AVIF (or KTX2 for GPU textures), audio to Ogg/Opus, and recompress screenshots to JPEG for docs.
- Binary assets over a few MB belong in Git LFS or release artifacts, not in history.

## 3. Caching

- **Web/PWA:** bump the service-worker cache version on every release, cache the app shell and pinned dependencies offline, and give versioned files long `Cache-Control` lifetimes.
- **CDN dependencies:** pin exact versions, add SRI, and mirror them locally for offline builds.
- **Builds/CI:** use `Swatinem/rust-cache` or `sccache` for Rust and the npm cache in CI, and keep `Cargo.lock` committed so caches hit.
- **Runtime:** memoize pure hot computations (text layout, glyph runs), and precompute static geometry and collision grids.

## Report template

| Metric | Before | After | Change | Method |
| --- | --- | --- | --- | --- |
