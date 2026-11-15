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
- [x] R1 renderer: material id packed into the instance glow, a 9-layer texture array, one fetch along the dominant axis
- [x] R1 materials on ground, roads, lots, sidewalks, house siding, roofs, brick and plaster towers, trailers (before/after in `screenshots/b7/textures_before_after.jpg`)
- [x] Grass stays off paving: every flat gray decal (driveways, walks, slabs) and every mulch bed is recorded as paved, and blades skip it (21,200 blades, 0 on paving in `tests/feat12.py`)
- [x] Houses rebuilt from real references (below)
- [x] Street details: cobra-head street lights over the road, stop signs at residential corners, continental crosswalks around downtown, lane dashes at the real 10 ft / 30 ft rhythm, and car paint in real proportions
- [ ] R2 models (character style previews are in: try all 15 styles with K, see below)
- [ ] R3 map ×5
- [ ] R4 events, people and items

## Houses, from real references (15 Nov 2026)

The old houses were one shape: a pastel box with a steep triangular roof in roof material, gable ends included. Real streets
vary from house to house, and real roofs are thin planes with overhangs, with the gable triangles clad like the walls.

**What we looked at.** 28 openly licensed photos from Wikimedia Commons (CC BY-SA 3.0/4.0 and public domain; record in
`.refcache/houserefs/licenses.json`, not shipped): ranch houses in California and Texas, split-levels, California
bungalows, houses in Phoenix and Colonial Revival houses in Ohio. What they share: low roofs in grays and browns (clay tile
on stucco), white trim, visible eaves with fascia and gutters, foundation shrubs, a walk to the door, a driveway to a garage.

**Numbers used.**

| What | Value | Source |
| --- | --- | --- |
| Roof pitch | 4/12 (18.4°) on ranches, 6/12 (26.6°) on two-story colonials, most homes 4/12–8/12 | [This Old House](https://www.thisoldhouse.com/roofing/common-roof-pitches), [Angi](https://www.angi.com/articles/common-roof-pitch.htm) |
| Eave overhang | 12–18 in (0.30–0.46 m); deeper on bungalows | [GAF](https://www.gaf.com/en-us/blog/your-home/how-roof-overhangs-can-protect-your-home-from-water-damage-281474980206747) |
| Garage doors | 8–9 × 7 ft single, 16 × 7 ft double | [Clopay](https://www.clopaydoor.com/residential/buyingguide/what-is-the-average-garage-door-size), [Angi](https://angi.com/articles/standard-garage-door-sizes.htm) |
| Wall colors | 2026 repaints: beige 24%, white 14%, gray 12%, green 9%, black 8%, brown 7% | [Houzz via Apartment Therapy](https://www.apartmenttherapy.com/outdoor-trend-report-2026-beige-colors-37689821) |
| Shingles | Charcoal, Weathered Wood, Pewter Gray, Barkwood are the top sellers | [GAF](https://www.gaf.com/en-us/blog/your-home/2025-shingle-color-trends-by-region-3cdf0e23-631d-46b4-ba62-3f8238a1fbe7) |
| One vs two stories | roughly half and half in new homes | [NAHB Eye on Housing](https://eyeonhousing.org/2026/07/two-or-more-story-home-starts-pull-back-in-2025/) |
| Car colors | North America 2025: white 31%, black 26%, then gray, silver, blue, red | [Axalta via European Coatings](https://www.european-coatings.com/news/axaltas-global-automotive-colour-report-white-remains-top-choice/) |

**What the generator builds now.** Five styles: ranch (1 story, hip or side gable at 4/12–5/12, often an attached garage),
two-story colonial (side gable at 6/12–8/12, symmetric windows, shutters, sometimes a portico or a garage wing), craftsman
bungalow (front gable, deep eaves, full porch on brick piers, side driveway), garage-forward tract home (two stories over a
single or double garage, hip or gable, often stucco) and flat-roof modern (parapet with rooftop AC, or a deep slab overhang).
Walls are wood-framed panels clad in lap siding, brick veneer (the brick photo tinted by the paint color) or stucco. Pitched
roofs are thin shingle planes with fascia, soffits, gutters and downspouts; hip roofs are one panel whose surface is exact
(height rises with distance from the nearest eave). Garages get sectional doors with panel grooves, driveways and walks are
paved, and yards get foundation shrubs in mulch, trees, bins, AC units and the odd gnome. Upper floors hide while you're
inside so the cutaway camera still works. Measured on one seed: 24 houses, 5 styles, roofs 8 side-gable / 5 front-gable /
7 hip / 4 flat, 12 siding / 5 brick / 7 stucco, 13 garages, 9 two-story; world generation 104 ms.

## Character style previews (15 Nov 2026)

All 15 rows of the Character Style Picker sheet can be tried in game, for this session only: press **K** (Shift+K goes
back), pick one under Settings → "Characters (preview, not saved)", or open the game with `#id` in the link (combine with a
world look: `#cinematic+film`). Ids: `real`, `film`, `upgraded`, `dolls`, `vinyl`, `claymen`, `ink`, `felt`, `caricature`,
`anime`, `faceted`, `retro`, `voxels`, `paperfolk`, `shadows`. The previews restyle today's characters at draw time
(proportions, faces, materials, outlines, shape swaps, stop-motion poses); the full remodel for the style you choose is R2.
