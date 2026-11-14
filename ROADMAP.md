# Borrowed Time: roadmap

*Written 14 Nov 2026, after the demolition, interiors and casino update. It is checked against the code and test numbers from that update. Estimates are rough and assume one developer working with Claude.*

## Where the game stands

| Area | State now | Measured |
| --- | --- | --- |
| Core loop | Draining clock, 9 stashes, tolerance, comedown, heat and cops, 25 feats | All feature suites pass, 0 errors |
| Physics | Hand-rolled props and ragdolls. Rapier 0.21 (Rust → WebAssembly) handles demolition rubble, with a built-in fallback | Free fall measures 9.810 m/s² (0.0% error, 340 samples) |
| Demolition | 1,508 breakable panels: walls, windows, roofs, 19 slot machines. Load-path collapse rules | A horn charge breaks 9–11 panels; one propane blast breaks 30–37 |
| Interiors | 24 walk-in houses, a mini-mart and the casino, with a cutaway camera inside small buildings | Camera reaches the cutaway view within 1.5 s |
| Rendering | Raw WebGL2: shadows, 8 nearest point lights, textured billboards, signs and floors | 3–5 ms render on a software rasterizer (no GPU in the test machine) |
| Platforms | Link (claude.ai), PWA (offline), Tauri desktop shell (never compiled) | Not yet tested on a real phone or GPU |

Logic cost per frame (headless, this machine): 0.8–1.3 ms idle, 1.5–2.2 ms walking through rubble, and 6.5–7 ms in the first second after a big explosion (130–160 moving pieces, of which 2.4–2.8 ms is Rapier).

## What's missing

**Must have before selling it**

- **Pause and settings menu.** Graphics quality (shadows, lights, render scale), volume sliders, look sensitivity, key rebinding, voice mode. Steam players expect it, and phones need a quality switch.
- **Photosensitivity safety.** The bust strobe, kaleidoscope, glitch bars and parade flash. Add a warning screen and a "reduce flashing and shake" option.
- **Gamepad support** through the browser Gamepad API. Steam Deck and controllers depend on it.
- **Saving.** Settings, unlocks and stats should survive a restart. Today only your look and your best score are saved.
- **Parody names for the substances** before a store release (the brief already flags Xanax and Henny). Also reword the "inspired by Goat Simulator" line for a store page.
- **Testing on a real phone and a real GPU.** All numbers so far come from headless software rendering.

**Gameplay depth**

- **Meta-progression.** A "chrome bank" that carries part of each run's dollas forward, and unlockable outfits for feats.
- **Goals beyond the clock:** missions or daily challenges ("bring down 3 roofs before sunset"), plus a short tutorial run.
- **Cops can't reach you while you fly.** They need a counter: a drone, heat that doesn't drop while airborne, or cops waiting where you land.
- **Drivable vehicles.** Cars are props today.

**Physics and world**

- **One physics engine for everything.** Props and furniture still use the old solver, so they can't stack or collide with rubble. Moving them into Rapier fixes both.
- **Articulated ragdolls** using Rapier joints, so limbs flop separately instead of the body tumbling as one piece.
- **More breakables:** trailers, fences, the gas canopy, downtown tower glass, the water tower. Fire that spreads through wood.
- **Pathfinding** for NPCs and cops (a navigation grid), so people inside buildings stop walking into walls.
- **Interiors downtown:** at least one tower lobby with stairs to the roof.

**Sound**

- Music, an ambient city soundscape, distance falloff for sound effects, and a mixer. Sounds today are procedural blips.

**Sharing and release**

- **Steam:** Steamworks through the Tauri shell (feats map to achievements, plus cloud saves), store art, a trailer, the mature-content survey.
- **Phones:** host the PWA (GitHub Pages) as the guaranteed route. An Android build through Tauri mobile is optional. App stores restrict drug themes (Apple guideline 1.4.3, Google Play's drug policy), so treat a store release as uncertain.
- **Discord:** link previews (Open Graph tags on the hosted page) right away. A Discord Activity, the game running inside a voice channel, is a bigger later project.

## Engine path: pick one

| | A. Web + Rust via WebAssembly *(recommended)* | B. Rust-only engine (Bevy) | C. Unity (C#) | D. Plain JavaScript |
| --- | --- | --- | --- | --- |
| What it means | Keep the one-file web game and move heavy systems into Rust (Rapier now, more later). Tauri wraps it for Steam. | Rewrite in Bevy with Rapier, ship native builds | Rewrite in Unity, using Rust only in native plugins | Leave it as it is |
| Rust share | Physics now, then simulation core | All of it | Plugins only | None |
| Phones / Discord link | Yes, instantly | Needs a separate web build | WebGL build possible, heavy | Yes |
| Steam | Tauri + steamworks-rs | Native, steamworks-rs | Mature tooling | Tauri |
| Rewrite cost (estimate) | None, works step by step | 6–10 weeks to match today's features | 6–10 weeks, mostly not Rust | None |
| Risk | WebView performance on low-end PCs | Mobile support is young | Moves away from Rust | Leaves the Rust goal behind |

**Recommendation: A.** The game already runs from one link on phones and in Discord. Every step moves more of it into Rust without stopping the game. The next Rust step would be props and ragdolls, followed by a small Rust crate for NPC and cop logic. If B or C appeals more, I can prototype one district in it and compare frame times before committing.

## Milestones

| # | Milestone | Done when |
| --- | --- | --- |
| M0 | **Done (this update):** demolition with Rapier, walk-in interiors, Lucky Liver Casino and billboard, point lights, textures, OVERDRIVE skill | `tests/feat5.py` passes with and without Rapier |
| M1 | Menus and safety: pause/settings, quality presets, photosensitivity option, gamepad, saving | Playable start to finish with a controller. Settings persist. Flashing can be turned off. |
| M2 | Physics unification: props and furniture in Rapier, articulated ragdolls, more breakables, fire | Props stack and collide with rubble. Explosion frames stay under 8 ms of logic on a mid-range phone. |
| M3 | World and AI: navigation grid, smarter cops (drone or landing ambush), tower lobby interior | NPCs leave buildings through doors. Cops can end a flying escape. |
| M4 | Depth: meta-progression, missions or daily challenges, outfit unlocks, music and soundscape | A second run is different from the first. Retention is measured locally. |
| M5 | Release: Steam build (achievements, cloud saves), hosted PWA with link previews, parody names, store page | A Windows build installs from Steam's beta branch. The PWA installs on iPhone and Android. |
| M6 | Optional: Discord Activity, Android package, Rust simulation core | Chosen after M5, based on how players actually use it |

## Asked for, but done differently

- **Copying Goat Simulator's look from downloaded footage** wasn't done. The game stays clean-room (original art, names and levels). It borrows only genre mechanics: physics chaos and demolition. The OVERDRIVE skill's footage pipeline only fetches footage you own (your own gameplay captures count), Creative Commons or public-domain footage, or footage used with permission.
- **Porting to Unity** isn't in the plan because it moves away from Rust. Option C above shows what it would take if you still want it.
