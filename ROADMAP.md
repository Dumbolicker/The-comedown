# Borrowed Time: roadmap

*Updated 15 Nov 2026, after milestones M1 to M5. Every "done" line is backed by a test in `tests/` that passes with 0 errors. The test numbers come from headless Chromium with software rendering, so they show relative cost, not phone performance.*

## Where the game stands

| Area | State now | Measured (test) |
| --- | --- | --- |
| Menus and safety | Pause (Esc, II button, Start, auto-pause on tab or focus loss). Settings: quality presets with an auto-resolution governor, three volume buses, look speed, invert, key rebinding, rumble. First-launch flashing warning, reduced-flashing mode, shake slider | `feat6`: clock frozen while paused, rebinding with conflict swap, settings survive a reload |
| Controllers | Gamepad API (standard mapping) in play and in every menu | `feat6`: stick moves 4 m in 0.75 s, Start pauses, B resumes |
| Saving | Profile (runs, totals, feats, chrome bank, dailies) in local storage, mirrored to the desktop shell or Steam Cloud | `feat6`, `feat9` |
| Physics | Props and furniture in Rapier: they stack and collide with rubble. Jointed ragdolls (ball hips and shoulders, hinged knees and elbows) | `feat7`: top crate rests 2 mm from the expected height; prop gravity 21.9 vs 22 m/s²; rubble free fall 9.81 m/s² |
| Destruction | Limited to five condemned structures per town, each marked with an orange-X sign: three houses, one trailer and the water tower (288 of 1,991 panels). `?wreck=all` makes everything breakable. Fences splinter, fire spreads through wood, and doors in condemned buildings can be kicked in | `feat5`, `feat7`: tank falls and splashes, canopy drops after 3 of 4 pillars |
| Doors | 32 doorways get doors: single, double, or glass in the lobby and shop. They open for whoever walks up and close behind | `feat10` |
| AI | 0.5 m navigation grid with A*. Cops route around buildings; people leave buildings by the door. A police drone answers flying escapes | `feat8`: grid builds in about 1 ms; cop closes 19.5 m to 0.7 m around a house; resident exits in 0.62 s |
| Depth | Chrome bank, six feat-locked outfit items, daily challenges and a daily streak, first-run tutorial, 27 secret feats (requirements hidden until earned), golden stashes, a live personal best, streak milestones with slow motion, and an hourly break reminder. Design and sources are in `docs/ENGAGEMENT.md` | `feat9`, `feat10` |
| Quests | Five people with a gold ! and a three- or four-step quest each: Marisol's lost parcel, Grandma Lupe's runaway gnome, Raj's shoplifter, Vinny's collection and Inspector Lowe's condemned house. They stand their ground, an E · Talk tag shows who you can talk to, and the corner panel tracks the step | `feat12`: all five finish and pay, a real E key press starts one, sprinting at a giver leaves them standing |
| First person | X, scrolling all the way in, R3 or the 1P button puts the camera in your eyes. Everything from third person still works, and a crosshair picks what you look at: E does its main thing, G the other (two verbs for every prop kind, people, doors, windows, walls, furniture and machines; sit, lie down, hold things in view). Field of view, head bob and your body are in Settings | `feat13`: 138 verbs across 39 prop kinds and 20 other targets, 0 failures; throws land within 9° of where you look |
| Sound | Procedural music (94 BPM, follows heat and the comedown), ambience (traffic, birds, crickets), distance falloff and panning | `feat9`: sounds at 60 m play at 14% |
| Release | GitHub Pages workflow with link previews. Tauri shell with Steam achievements and Steam Cloud (`--features steam`), store-page draft. Unity 6 slice with a GameCI build | Desktop shell `cargo check` passes for both builds; `cargo test` passes; Unity scripts compile against Unity 6 libraries |

Logic cost per frame on the test machine: about 0.4–0.7 ms walking around, 2–3.5 ms on average in the second after a blast among props, with spikes up to 6–10 ms. Rendering takes 3 ms on a software rasterizer.

## Done in this pass

- **M1 Menus and safety:** pause/settings, quality presets, photosensitivity warning and reduced-flashing mode, gamepad support, saved settings and records, parody names (BARS, HOOCH), store-safe title text.
- **M2 Physics unification:**
  - props and furniture in Rapier, with the built-in solver kept as a fallback
  - jointed ragdolls
  - water tower, canopy, trailers and fences as breakables
  - fire that spreads
- **M3 World and AI:** navigation grid with A*, smarter cops (drone plus a landing ambush, and heat holds while you're airborne), downtown lobby tower with stairs to the roof.
- **M4 Depth:** chrome bank, outfit unlocks, daily challenges, tutorial, music and soundscape with distance falloff (the mixer arrived in M1).
- **M5 Release, the parts that don't need your accounts:**
  - Pages workflow, Open Graph and Twitter link previews (`pwa/og.jpg`)
  - Steam achievements and cloud saves in the Tauri shell
  - `steam/achievements.csv` and `steam/STORE_PAGE.md`
- **Unity:**
  - a Unity 6 project in `unity/` with a GameCI workflow that builds WebGL and Windows
  - `tests/unity_compile.sh`, which compile-checks the C# against Unity's own libraries without a license

## Needs you (accounts, money or hardware)

| Step | Where | Why I can't do it |
| --- | --- | --- |
| Turn on Pages | Repository Settings → Pages → Source: GitHub Actions, then run "Pages (web and phone build)" on `main` | Repository setting; the Pages environment deploys from the default branch |
| Unity builds | Add `UNITY_LICENSE`, `UNITY_EMAIL`, `UNITY_PASSWORD` secrets (steps in `unity/README.md`) | Needs your Unity account and a computer for the one-time Unity Hub activation |
| Steam | Steamworks partner account, the Steam Direct fee, an App ID, achievements and cloud setup (`steam/STORE_PAGE.md`) | Your account and payment |
| Windows build | `cargo tauri build --features steam` on a Windows PC, or a CI runner | No Windows machine here |
| Real-device testing | iPhone, Android, a low-end PC, a Steam Deck | All numbers so far come from headless software rendering |

## Still open

- **Unity port parity.** The Unity slice covers one street: walk-in houses, demolition, the player, the clock and stashes. Porting M1–M4 into it takes several weeks. It goes milestone by milestone, and each GameCI build checks the result.
- **Discord Activity** (the game inside a voice channel): needs a Discord app and the Embedded App SDK. Link previews work already.
- **Android package** through Tauri mobile, if a store listing is wanted (Google Play's drug policy makes that uncertain).
- **Tuning on real hardware:** spikes after explosions, the auto-quality thresholds and the drone's difficulty.
- **Store art and trailer:** the shot list is in `STORE_PAGE.md`.

## Engine path

You chose Unity, so the Unity project lives in `unity/` and builds in the cloud with GameCI. The web build stays the instant-play version: one link on phones and in Discord, and the Tauri shell for Steam. Rust stays where it pays off: Rapier physics through WebAssembly in the web build, and the Tauri shell with Steamworks. In Unity, Rust can join later as a native plugin if a system needs it.

## Milestones

| # | Milestone | Status |
| --- | --- | --- |
| M0 | Demolition with Rapier, interiors, casino, lights, textures | Done |
| M1 | Menus, safety, gamepad, saving | Done (`feat6`) |
| M2 | Physics unification, breakables, fire | Done (`feat7`) |
| M3 | Navigation, smarter cops, tower lobby | Done (`feat8`) |
| M4 | Progression, dailies, tutorial, music | Done (`feat9`) |
| M5 | Release routes | Code done; waiting on Pages, Steam and Unity accounts (table above) |
| M6 | Discord Activity, Android, Unity parity | Open |
