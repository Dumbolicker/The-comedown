# Steam store page: draft

Ready-to-paste copy and a checklist for the Steamworks partner site. Asset sizes come from Steamworks' graphical assets guide (https://partner.steamgames.com/doc/store/assets). Check that page before you upload, because Valve changes the sizes now and then.

## Name and short description

**Borrowed Time**

> A physics-comedy sandbox on a draining clock. Tackle, throw and ragdoll your way through a town that breaks: walls, roofs, a water tower. Grab stashes that bend the rules, dodge the cops (and their drone) and stay ahead of the comedown.

## About this game

You wake up in a trailer park with thirty seconds on the clock and no plan. Every stash you find buys more time and bends the rules: low gravity, jelly legs, magnet hands, a body that turns into a dragon. Everything else is fair game.

- **A town that breaks.** Walls, windows and roofs are made of breakable panels with real load paths. Knock out enough supports and the roof comes down. Topple the water tower. Fire spreads through wooden frames.
- **Physics comedy.** Jointed ragdolls, props that stack and scatter, thrown cars, fences that splinter, and rubble simulated by Rapier (Rust, compiled to WebAssembly).
- **Cops with a plan.** They route around buildings to reach you. Try to escape by air and a police drone comes after you.
- **The Lucky Liver Casino.** Fake-money slots, a bouncer, no clocks inside. Or smash a machine open for the coins.
- **Runs that add up.** 27 feats (Steam achievements), outfit unlocks, three daily challenges and a chrome bank that carries part of each run's cash forward.
- **Play your way.** Controller support, rebindable keys, quality presets, and a reduced-flashing mode with a camera-shake slider.

*A cartoon satire for adults. Every effect is made up, none of it is real-world drug information, and the casino uses fake money.*

## Tags (pick up to 20 on the store page)

Physics, Sandbox, Comedy, Destruction, Funny, Third Person, Open World, Ragdoll, Indie, Action, Casual, Singleplayer, Replay Value, Colorful, Stylized, Mature

## Content survey (Mature Content)

| Question | Answer and note |
| --- | --- |
| Some Nudity or Sexual Content | No |
| Frequent Violence or Gore | No. Slapstick only: tackles and ragdolls, no blood or gore |
| Adult Only Sexual Content | No |
| General Mature Content | **Yes.** Drug and alcohol references in a cartoon-satire setting (made-up effects, parody names), plus simulated gambling with fake in-game currency that can't be bought or cashed out |

Store description note (shown to players): *"Cartoon satire with drug and alcohol references. Includes a slot machine played with fake in-game money; no real-money purchases."*

## Achievements

`achievements.csv` lists all 27 feats with their API names, so the game and Steam agree. To get them in:

1. Steamworks → App Admin → Stats & Achievements → Achievements: add each row, using **api_name** as the API Name.
2. Upload a 256×256 unlocked and locked icon for each.
3. Publish the stats schema.

The shell maps a feat name to its API name the same way (see `src-tauri/src/platform.rs`, `api_name`).

## Steam Cloud

The profile (records, unlocks, settings) is one file, `profile.json`, under 256 KB. Steamworks → App Admin → Cloud: set a byte quota of 1 MB, a file count of 4, and turn on Steam Cloud. No Auto-Cloud paths are needed, because the game writes the file through the API.

## Images to make

| Asset | Size (px) | Idea |
| --- | --- | --- |
| Header capsule | 920 × 430 | Logo over the toppling water tower |
| Small capsule | 462 × 174 | Logo only, high contrast |
| Main capsule | 1232 × 706 | Logo, ragdolled tweaker mid-air, roof caving in |
| Vertical capsule | 748 × 896 | Casino neon plus tweaker |
| Library capsule | 600 × 900 | Same as vertical, logo bigger |
| Library hero | 3840 × 1240 | Skyline at dusk, no text |
| Library logo | 1280 × 720 (transparent PNG) | Logo |
| Screenshots | 1920 × 1080, at least 5 | Demolition, fire, drone chase, casino, lobby-tower roof |

## Trailer shot list (60–75 s)

1. Wake up in the trailer, clock at 0:30 (2 s)
2. First tackle through a wall, slow-motion cave-in (6 s)
3. Stash montage: float, jelly, magnet, dragon breath setting a house on fire (12 s)
4. Water tower comes down, splash (6 s)
5. Cops chasing, jump off the lobby tower, the drone launches, zap (10 s)
6. Casino: smash a machine, coin fountain (6 s)
7. Comedown vignette, then cut to the logo and "Borrowed Time · Coming soon" (5 s)

## Release checklist

- [ ] Steam Direct fee paid, App ID created; set `BT_STEAM_APPID` or ship `steam_appid.txt` only in test builds
- [ ] Build: `python tests/sync_builds.py --vendor`, then `cargo tauri build --features steam` on Windows
- [ ] Upload with SteamPipe to a beta branch; test achievements and cloud on two PCs
- [ ] Content survey, store copy, tags, assets, trailer
- [ ] Price, regions and release date; request a review at least two weeks before launch
