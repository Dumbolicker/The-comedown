# Performance: the lag pass (15 Nov 2026)

## How it was measured

`tests/perf_probe.py` loads the game in headless Chromium with software WebGL (SwiftShader), so GPU work becomes CPU time
on a 4-core cloud VM, a stand-in for a weak phone GPU. It looks at three views: street level in a residential block, an
aerial view over the middle of town, and a blast at a condemned house with rubble flying.

For each view it averages 35–55 frames and records:

- triangles drawn in the main pass and in the shadow pass
- JS time for `update()` and `render()`

`tests/perf_blast.py` wraps the update's parts to show where a blast frame goes.

## What was slow

- **Grass.** 21,000 blades, each drawn as a 12-sided cone (36 triangles), twice a frame: once lit and once into the
  shadow map. That was 755k of the 1.09M static triangles per pass.
- **Leaves and shrubs.** About 1,290 smooth spheres at 192 triangles each, 248k per pass.
- **Blasts.** After a big blast the physics step was 10–11 ms of a 20 ms update. Up to 320 chunks were live, panels
  split into up to 16 pieces, and every fast chunk ran continuous collision.
- **People.** About 170k triangles, mostly smooth spheres for joints, hands and heads.

## What changed

| Change | Why it is safe |
| --- | --- |
| A grass blade is one upright triangle with an upward normal (was a 36-triangle cone) | Blades are 2–6 cm wide: the shape never showed. The upward normal shades them like the lawn |
| Grass casts no shadow | A blade's shadow is a few pixels long |
| Leaves and shrubs use an 80-triangle sphere | The leaf texture hides the facets |
| People more than 16 m away use the 80-triangle sphere; faces are skipped past 25 m | Under a few pixels at that distance |
| A broken panel splits into at most 6 pieces (was up to 16); live chunks capped at 160 on desktop and 90 on phones (was 320 and 150) | The pile reads the same; fewer bodies to simulate |
| Chunks skip each other in physics; they still hit the ground, walls, slabs, props and you | A pile of 200 no longer makes thousands of chunk-to-chunk contacts |
| Continuous collision only for falling slabs and big chunks | A small chunk tunneling a few cm is invisible |
| Crack and scorch tints rebuild the panel batch at most every 0.12 s; a broken panel still updates at once | Tints change slowly anyway |

## Results

Same views and same machine. Rubble counts vary from run to run because breaking is random.

| View | Triangles per frame (main + shadow), before | After | Update JS, before | After | Render JS, before | After |
| --- | --- | --- | --- | --- | --- | --- |
| Street | 2.68M | 0.91M (−66%) | 3.9 ms | 3.0 ms | 4.2 ms | 2.9 ms |
| Aerial | 2.59M | 0.82M (−68%) | 4.5 ms | 2.5 ms | 4.7 ms | 1.6 ms |
| Blast | 2.58M | 0.73M (−72%) | 20.4 ms | 14.7 ms | 5.2 ms | 3.0 ms |

- **Static world:** 1,086,056 → 228,082 triangles per pass.
- **Physics step at a blast's peak:** 11.0 ms → 8.5 ms with the same number of awake bodies per chunk. The rest comes from
  fewer chunks being alive at once.

## Also fixed: the road flickering to grass

The town's asphalt was one 157 m plane sitting 1 cm above a 477 m grass field plane that ran under the whole map. When the
camera clips triangles that big at the near plane, depth precision can lose that 1 cm, and the road showed grass in
patches that moved as the camera moved slightly. Software GL showed it, and so can some phone GPUs. Now:

- The fields are four strips around the town and never sit under the road.
- The lawns sit 2.3 cm above the road (was 0.7 cm).

## Not measured

- A real phone or a real desktop GPU. SwiftShader is far slower than either, so read these as relative numbers.
- Battery use.

## Check after the quests and trailers batch (16 Nov 2026)

The rebuilt trailers add breakable panels (siding bands, skirting, window frames) and some furniture, and the quests went
from 21 people with a job to 5. The same probe ran twice on the build before the batch and twice on the new one, one run
at a time on the same machine. A single run varies a lot (the new build's aerial render took 2.50 ms in one run and
1.56 ms in the next), so the table shows the average of the two.

| View | Triangles (main + shadow), before | After | Update JS, before | After | Render JS, before | After |
| --- | --- | --- | --- | --- | --- | --- |
| Street | 0.79M | 0.77M | 2.84 ms | 2.60 ms | 2.91 ms | 2.35 ms |
| Aerial | 0.77M | 0.73M | 2.34 ms | 2.19 ms | 1.88 ms | 2.03 ms |
| Blast | 0.74M | 0.80M | 12.3 ms | 13.4 ms | 3.1 ms | 3.8 ms |

- **Walking around costs the same or less.** Drawing people in the aerial view went from 0.97 ms to 0.36 ms, because
  about 35 people are out instead of about 50. The quest markers and talk tag cost 0.07 ms a frame.
- **The trailers' extra panels don't show up.** One rebuild of the panel batch walks every breakable panel: 0.72 and
  0.75 ms before (2,824 and 3,000 panels), 0.54 and 0.66 ms after (3,185 and 3,192 panels).
- **The blast numbers depend on how much of the house comes down.** The new build's two blasts dropped 13 and 4 floor
  slabs, against 0 and 2 for the old build's, and rebuilt the panel batch 24 and 19 times against 9 and 14. More falling
  floors mean more physics and more rebuilds, whichever build it is.
