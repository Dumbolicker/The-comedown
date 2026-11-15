# Realism pass: plan and progress

Requested on 15 Nov 2026:

- make it look realistic, using textures made from real reference images
- remake the player models (same vibe) and the cars, with more detail everywhere
- make the map 5× bigger, with new interactive events, people and items

## Ground rules

- **Images are CC0 only.** That means Poly Haven or ambientCG photo scans, so the game can ship them. Each one goes into `assets/textures/LICENSES.md`.
- **Network access:** the session runs in the personal environment "The-comedown (CC0 textures)". It allows `api.polyhaven.com`, `dl.polyhaven.org`, `ambientcg.com` and `acg-download.struffelproductions.com`.
- **The web build stays the main build:** raw WebGL2 plus Rapier, playable from the link. The Unity slice can reuse the same textures later.
- **Budgets:** logic under 8 ms per frame in a big blast on a mid-range phone, render under 8 ms on a mid-range GPU. The "Low" quality preset must keep phones smooth.

## Phases

| # | Phase | What changes | Done when |
| --- | --- | --- | --- |
| R1 | Textured world | Instanced batches get a per-instance material id. The fragment shader samples a `TEXTURE_2D_ARRAY` (512² photo layers) with world-space triplanar mapping, tinted by the instance color, so houses keep their paint colors with real grain. Materials go to ground, roads, sidewalks, house walls, brick, roofs, trailers, towers and concrete. Normal and roughness maps are a second step | Same-camera before/after screenshots; frame cost measured; feat suites pass |
| R2 | Models | Humanoids built from more, rounder parts (shoulders, hands, sneakers, hoodie folds), keeping the same silhouettes and outfits. Cars rebuilt with rounded body panels, wheel arches, rims, tinted glass, light clusters, mirrors and bumpers. Props get bevelled shapes | Side-by-side model sheet; no change in collisions |
| R3 | Map ×5 | District grid from 4×4 to 9×9 (about 5× the area), with new district types: industrial yard, boardwalk, suburbs, carnival lot. Static batches split into chunks with distance culling; nav grid and lazy Rapier colliders work per chunk; fog and draw distance retuned | Build time, memory and frame time measured at 5× |
| R4 | New content | Events: street race, fireworks show, food truck rush, police roadblock, carnival rides. New people: joggers, dog walkers, skaters, vendors. New items: skateboard, fireworks, shopping cart, traffic cone hat | Each event has a test |

## Progress

- [x] Host access for the CC0 texture sites (new environment)
- [x] Starter texture set in `assets/textures/`: asphalt, concrete, grass, brick, siding, roof, plaster, metal, pavers (Poly Haven, CC0)
- [ ] R1 renderer: material id, texture array and triplanar shader
- [ ] R1 assignment of materials across the town
- [ ] R2 models
- [ ] R3 map ×5
- [ ] R4 events, people and items
