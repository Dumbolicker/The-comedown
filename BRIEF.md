# Borrowed Time: handoff brief

*Status as of 14 Nov 2026. Everything needed to pick the project up is in this folder.*

## In short

**Borrowed Time** is the owner's clean-room, Goat Simulator–style 3D physics sandbox. You play a
twitchy wreck ("the tweaker") whose life clock is always draining. Stashes of satirical, made-up
substances buy time and bend the rules. Around that are tackling, ragdolls, shapeshifting into 14
creatures, flight, horn charges, poop art, cops, slot machines with fake **dollas**, a ripperdoc
selling cyberware, and character customization.

- **Main build:** a single HTML file (`game/index.html`, about 300 KB). It uses raw WebGL2 with no
  libraries. It plays on phones (touch controls) and desktop, and it is published as a claude.ai
  artifact.
  - **Live link:** https://claude.ai/artifact/XgyMk7wJZrRtXTrLYhEusv (version 5, shared as
    "anyone with the link").
  - To update it from another chat, read it with the Artifact tool first, then publish with that
    `url`. Publishing without the `url` makes a separate artifact.
- **Desktop build:** a Tauri 2 (Rust) wrapper that bundles the same page into a Windows `.exe`. A
  GitHub Actions workflow builds it. It has not been compiled yet; this environment had no network
  or Windows target.
- **Phone build:** `pwa/` is the same game plus a manifest and an offline service worker. Host it
  anywhere static, then use "Add to Home Screen". It was verified in headless Chromium: it installs
  a service worker, caches itself and boots offline.
- **Earlier prototype:** `rust_prototype/jitters.zip` is a Rust/Bevy 0.15 version called JITTERS. It
  has 5 substances, the clock, tolerance and comedown. Borrowed Time became the main build because it
  runs on phones and as a link. The owner's original ask was a "clean room **rust** based version of
  Goat Simulator… Unity usage is permitted". The Tauri shell is the Rust part today. There is a port
  map at the end if the work moves back to Bevy.

**First thing to do in the new project:** open `game/index.standalone.html` in a desktop browser and
play for two minutes. Then read the code map below.

---

## 0. Update, 14 Nov 2026: demolition, interiors, casino

This update added the following. The plan and gap analysis are in `ROADMAP.md`, and the owner's working method is the OVERDRIVE skill in `.claude/skills/overdrive`.

- **Demolition.**
  - House walls are now breakable wood panels in two courses (≤1.5 m columns) with glass windows and two breakable roof halves. The mini-mart is brick with a glass storefront and a concrete roof. The casino has 6 glass entrance panes and 19 breakable slot machines. That's 1,508 panels in total.
  - Damage is ½·m·v²/100 from players, horn charges, giants, ragdolls, flung NPCs, thrown props, explosions (`brkBlast`, 950 at the centre), slams and dragon fire.
  - After a break, `brkStable` runs a 0-1 breadth-first search per building. Going up is free, and each sideways step costs 1, with at most 2 in a row (lintels and short spans). A roof falls when fewer than half the panels under it stand.
- **Rapier 0.21.0** (`@dimforge/rapier3d-compat`, Rust → WebAssembly, Apache-2.0).
  - It's fetched from jsdelivr at a pinned version, SHA-384-checked in `loadRapier` and imported from a blob URL. If blob imports aren't allowed, it falls back to importing the pinned URL directly.
  - It simulates falling sections (`rubSlab`) and rubble (`rubChunk`). A section breaks up on contact forces above 5 g.
  - Static colliders are added lazily around rubble (`rubEnsure`), and stepping is skipped while no rubble is live.
  - If Rapier fails, rubble becomes `chunk` props in the old solver. `physTag` on the title screen says which engine is running.
- **Interiors.** 24 walk-in houses with furniture, a wood floor, a rug and a ceiling light. The mini-mart has aisles, a cooler and a counter. `interiorAt` and `insideUpdate` cut away the roof of the building you're in: the roof is drawn only into the shadow pass (`SHO`), and the camera rises to a dollhouse view (`G.camIn`).
- **The Lucky Liver Casino** replaces the plaza kiosk (`casino()` in `gen_plaza`).
  - Inside: carpet, 19 machines (any one opens the slots, via `nearSlot`), a bar, a cashier cage, card tables, chandeliers and neon.
  - 4 gamblers and a bouncer with `home` behaviour.
  - Inside, the clock reads "??:??" until under 10 s.
  - Smashing a machine spills 16 coins worth Ð6–14 each.
  - A rooftop tri-vision billboard (`drawBillboard`) rotates 4 original ads, facing the trailer-park spawn.
- **Rendering.**
  - 8 nearest point lights in `FS_BODY` (`u_plp`/`u_plc`): street lamps at night, interior bulbs, neon, chandeliers.
  - A textured-surface program (`TEXP`) that reuses `FS_BODY` lighting, for the atlas (ads and signs, painted in code by `paintAtlas`) and tiled carpet, wood and tile floors.
- **New feats:** Wrecking Ball, Open Floor Plan, Beat the House (25 feats in total).
- **Tests.**
  - `tests/feat5.py` covers free-fall accuracy, charge, lintel, roof, blast, interior, casino and performance, with and without Rapier.
  - `tests/vendor_rapier.py` fetches and verifies the pinned Rapier file.
  - `tests/sync_builds.py --vendor` bundles it into the desktop build for offline play.

## 1. What's in this folder

| Path | What it is |
| --- | --- |
| `BRIEF.md` | This brief. |
| `game/index.html` | **The game.** This is exactly what gets published to the artifact. It has no `<html>`/`<head>` because claude.ai wraps it. |
| `game/index.standalone.html` | The same game wrapped as a full HTML document. Open it straight from disk. |
| `pwa/` | Installable offline phone build: `index.html`, `manifest.webmanifest`, `sw.js`, icons, and `README.md` with GitHub Pages hosting and install steps. |
| `desktop/borrowed_time_desktop/` | Tauri 2 project. `dist/index.html` is the standalone game, `.github/workflows/build-windows.yml` builds the exe, and `README.md` covers building, Discord and Steam notes. |
| `tests/make_standalone.py` | Rebuilds `game/index.standalone.html` from `game/index.html`. Run it after every edit. |
| `tests/feat3.py` | Headless checks for slot odds and pity (400k spins), the Doubloon parade, flight for all 3 winged forms, horn charge, holy and hell poop, and the laced fold. |
| `tests/feat3b.py` | A faster subset: flight, charge and poop in open road. |
| `tests/feat4.py` | Customization (48 hair×top combos), ripperdoc and all implants, the panic molar, gut reactor, and the fried-voice spectrum measured offline. |
| `tests/voicetune.py` | Sweeps fried-voice EQ settings against the reference clip's numbers. |
| `tests/shots4.py` | Staged screenshots of each feature, saved to `screenshots/`. |
| `screenshots/` | Current look (`whats_new.jpg` is an 8-shot collage) and earlier shots (title, creature zoo, party, slots on phone, wall art, salvia). |
| `rust_prototype/` | `jitters.zip` plus its README. |

**Tests need:** Python 3, `pip install playwright numpy`, then `playwright install chromium`. If a Chromium
is already installed and the Playwright versions don't match, point the tests at it with
`BT_CHROMIUM=/path/to/chrome`. They launch
Chromium with `--use-angle=swiftshader --enable-unsafe-swiftshader` so WebGL works headless. They drive
the engine directly: `update(1/60, inputObject)` in a loop, then `render()`.

---

## 2. The game, system by system

### Core loop
- The clock starts at 30 s, caps at 240 s and drains 1 s/s × modifiers.
  - At 0 the comedown wins.
  - Getting busted by cops costs 10 s and 25% of your dollas.
- **Chaos** is the score: tackles, wrecking props, booms, airtime, flops, art and so on.
  - A combo multiplier goes up to ×4.
  - Every 3,000 chaos you get +5 s ("adrenaline rush").
  - Dollas = points ÷ 8.
- **Heat** goes up to 5 stars and spawns cops. Cops chase and bust you. JUGGERNAUT, salvia objects and
  the mole rat are invisible or immune to them.
- **Tolerance:** each repeat of the same substance multiplies its time by 0.62, with a floor of 0.2×.
  One stack fades every 20 s.
- **Comedown:** 5 s of slow, grey, faster drain after the last effect ends.
- **Overamped:** 3 or more effects at once drains 1.6× faster.
- **The Shakes:** clock under 8 s with nothing active gives wobbly controls and heavy shake.

### Substances (all satire; effects are invented)
| Stash | Category | Effect (fx id) | Time | Duration | Use animation |
| --- | --- | --- | --- | --- | --- |
| COKE | Stimulant | FAST FORWARD (`FFWD`): you ×1.85 speed, world ×0.32, harder hits | +12s | 8s | sniff (looks like baking soda) |
| XANAX | Depressant | JELLY LEGS (`JELLY`): bump things and you ragdoll-spiral, slower drain | +10s | 9s | pill with "XAN" imprint |
| BLOTTER | Hallucinogen | KALEIDOSCOPE (`KALEI`): hue shift, wobble, fake labels | +11s | 10s | square tab placed in the mouth |
| SALTS | Inhalant | BALLOON FLOAT (`FLOAT`): 0.2× gravity, bouncy, squeaky voice | +9s | 9s | bag poured into the mouth |
| HENNY | Numbing | JUGGERNAUT (`JUGG`): plow through anything, no busts, drunk sway and stumbles | +10s | 7s | bottle you drink |
| BADDERALL | Energy-crash | GLITCH STUTTER (`GLITCH`): freeze, then snap ahead | +10s | 8s | capsule pill |
| ECSTASY | Euphoric | MAGNET HANDS (`MAGNET`): pulsing town, rainbows, wandering unicorns | +11s | 9s | pill with "MDMA" imprint |
| SALVIA | Dissociative | INANIMATE (`OBJECT`): you become a random object, frozen, world ×2.6, time-lapse sky | +13s | 15s | smoke |
| JOINT | Cannabis | TUNNEL VISION (`FOCUS`): green tint, narrower FOV, auto-aim lock on what you look at | +10s | 14s | smoke |

- The owner typed "ECSTACY"; the game spells it ECSTASY.
- Salvia objects: armchair, lamp, fridge, toaster, cone, grandfather clock, plant, toilet, duck,
  cabinet, TV, beanbag.
- **Laced:** 8% of spawned stashes (never the first one) are "cut with fent". After the use animation
  you **fold in half repeatedly for 10 s and can't move**. The screen darkens and desaturates, and NPCs
  react ("Buddy? You good?").
  - Measured rate: 8.5% across 300 spawns.
  - Counters from the ripperdoc: Test Strip Optics (laced stashes glow red and get labeled) and
    Naloxone Gland (the fold lasts 3 s).

### Shapeshifting (42% per dose, 25 s, not on salvia)
| Form | Body | Ability |
| --- | --- | --- |
| Centaur | horse plus human rider | fast, harder kicks |
| Minotaur | bull-headed humanoid | **horn CHARGE** |
| Dragon | quadruped with wings | **fly**, TACKLE breathes fire, **horn CHARGE** |
| Sloth | quadruped | very slow, clock drains 0.55× |
| Raccoon | quadruped | trash scores triple |
| Panda | quadruped | bouncy and heavy |
| Mole rat | small quadruped | cops can't see you |
| Ferret | small quadruped | fast, hopping |
| Dog | quadruped | YELL barks and scatters people |
| Cat | quadruped | huge jumps, always lands on its feet |
| Skinwalker | gaunt humanoid with skull and pelt | people and cops flee |
| Giant | 2.3× humanoid | landings shake the block |
| Angel | robed, feathered wings, halo | **fly**, floaty, holy poop |
| Demon | red skin, bat wings, horns, tail | **fly**, **horn CHARGE**, fiery tackles, hellish poop |

- **Flight:** hold jump in the air to climb at 6.5–8 m/s. The ceiling is about 64 m. Let go to glide
  down at 2.6–5 m/s. Air speed is 1.4×. Flying doesn't earn AIRTIME points, but 3 s of flight earns
  Frequent Flyer.
- **Horn charge:** the C key, or a CHARGE button that only appears for horned forms.
  - 0.3 s head-down wind-up, then 0.95 s at 20 m/s (about 20–24 m; a tackle is about 4.5 m).
  - You can steer it.
  - It gores people (GORED +320 base) and launches props.
  - Hitting a wall gets your horns stuck for 0.8 s.
  - Cooldown 2.4 s.
- When standing still, tackle and charge aim where the camera looks.

### Poop (P key / POOP button)
- Squat for 0.85 s.
  - Humanoids hold it: TACKLE throws it, and holding GRAB at a wall paints with it (60 "ink" dots).
  - Quadrupeds drop it behind them.
- Its 4 layers take the colors of the last 4 doses, newest on top (70% substance color, 30% brown).
  Size depends on the form, from 0.2× for a mole rat to 2.3× for the giant.
- **Angel poop:** pearl and gold, glowing, with a tiny halo and flapping wings. Plays a choir chord.
  Splats glow gold, nearby people stop and say "BLESSED".
- **Demon poop:** black and crimson with an ember top and tiny horns. Gives off smoke and sparks.
  Splats knock nearby people over ("HELLFIRE") and light propane.
- Feats: Street Artist (80 strokes) and Special Delivery (hit a cop).

### Slots ("Lucky Liver Slots", any machine in the Lucky Liver Casino, bets Ð10–250)
- Base odds per spin: triple 1.7%, pair 6.1%, Cursed Doubloon 1 in 137,000.
- Payouts: triple pays 10× the bet, a pair 2×, and three livers give +20 s.
- **Pity:** after 19 dry spins the 20th is forced to pay a pair (70%) or three livers (30%). It never
  forces the jackpot or the Doubloon. A pip meter on the machine shows progress.
- Measured over 400k spins: jackpot 1.50%, three livers 0.77%, pairs 7.44%, any prize 9.71%, pity
  fired on 2.08% of spins, longest dry streak 19.
- **Cursed Doubloon:** an original coin. It replaced a request for Fortnite's pirate token. It gives:
  - +Ð100,000, +60 s and a pirate hat
  - **30 s of every substance effect at once**, with salvia's freeze left out so you can still move
  - a **parade through all 14 creatures**, 2.14 s each, with a 0.7 s gold crossfade between them
- The machine auto-closes 3.2 s after a Doubloon win.

### Ripperdoc: Doc Suture's Chrome & Cures
The clinic is a trailer in the trailer park, about 6.5 m from spawn. It has a neon RIPPERDOC sign, an
operating chair, a surgical lamp and a cart of glowing vials. The doc stands out front. He's an
original character in a blood-spattered coat, with a red cyber-eye, goggles, a chrome skull plate and
a drill hand. Press E or tap DOC to open the shop.

Implants are bought with dollas, last the run and show as chrome on your body.

| Implant | Slot | Price | Effect |
| --- | --- | --- | --- |
| Septum Turbine | nose | 400 | COKE +50% time, snorting takes half as long |
| Iron Gullet | throat | 450 | SALTS and HENNY +50% time, pours and chugs twice as fast |
| Pill Crusher | stomach | 600 | XANAX, BADDERALL, ECSTASY +50% time, effects last 30% longer |
| Tab Tongue | tongue | 300 | BLOTTER +50% time, tripping pays 1.5× chaos |
| Iron Lungs | lungs | 450 | JOINT and SALVIA +50% time, salvia freeze halved |
| Chrome Liver | liver | 750 | clock drains 15% slower |
| Receptor Scrubber | brain | 650 | tolerance builds half as fast and fades twice as fast |
| Test Strip Optics | eyes | 350 | laced stashes glow red and get labeled |
| Naloxone Gland | blood | 500 | the laced fold lasts 3 s instead of 10 |
| Panic Molar | jaw | 500 | at 3 s left it pops for +15 s (one use, can be rebought) |
| Stash Sniffer | sinus | 350 | off-screen stash arrows name the substance, and one extra stash is always out |
| Gut Reactor | colon | 300 | poop cooldown 0.4 s, poop 60% bigger |
| *Sell a kidney* | back | +800 | instant dollas, clock drains 10% faster afterwards |

- Installing 3 implants earns the Chrome Addict feat.
- The doc greets you within 8 m and talks with his own deep voice.

### Character customization (title screen → "Customize your tweaker")
- **Body:** 10 skin tones (8 realistic, plus zombie green and cold blue), height 0.88–1.14 (shown as
  5'2"–6'8"; this also scales the collision height), and build 0.8–1.45.
- **Hair & face:** 8 hairstyles (messy, buzz, mohawk, long and mullet with cloth physics, afro, bun,
  bald) and 10 hair colors. Facial hair: clean, stubble, mustache, goatee or beard. Eyewear: none,
  shades or round specs.
- **Clothes:**
  - Tops: hoodie (hood and strings), tee, tank, open flannel (flapping tails), bomber, trench coat
    (5 cloth tails).
  - Pants: jeans, shorts or sweats.
  - Shoes, plus headwear: backwards cap, beanie, bucket hat, headband or none.
  - Colors: 12 for tops and headwear, 7 for pants, 6 for shoes.
- The look applies to the human, giant, angel, demon and centaur rider.
- The preview is live 3D: a slow orbit you can drag, with a lens-shifted camera so the character
  clears the panel.
- Saved in `localStorage` under `bt_look`.

### Voices
- **Deep-fried (default):** characters "speak" procedural cartoon gibberish. It's built from syllables
  of the line, with vowel formants, consonant noise ticks and question/exclamation intonation. The
  speech bubbles still show the real text.
  - Signal chain: low shelf +12 dB at 160 Hz → peak +4 dB at 70 Hz → peak +7 dB at 1.1 kHz → tanh
    clipper with drive 9 → low-pass 4.8 kHz → 10:1 compressor.
  - **Tuned to the owner's reference meme clip.** The clip measured 61.5% of energy below 150 Hz,
    7.3 dB crest factor and 5% of samples pinned at full scale. The fried voice measures 58.7% and
    7.3 dB averaged over 3 phrases.
  - Nothing from the clip ships in the game. It contains a real person's photo and someone else's
    audio.
- **Text-to-speech:** the device's built-in voices, ranked to prefer natural/neural/premium ones, each
  NPC getting a voice by sex and seed. Web Speech output can't be run through Web Audio, which is why
  the fried mode is synthesized.
- **Off.**
- The title button or the V key cycles the modes. Saved as `bt_voice2`.

### Feats (25)
Each gives bonus seconds:
- Frequent Flyer, Bowling Night, Polypharmacy, Full Medicine Cabinet (all 9 stashes), Pyromaniac,
  People Person, Thin Blue Linebacker, Top of the World (water tower)
- Lawn Darts, High Roller, Marathon, Hang Time, Car Trouble, Hydro Therapy, Rookie Mistake
- Gnome Away, Bounce House, Shapeshifter, Against All Odds (Doubloon, +60 s), Street Artist, Special
  Delivery, Chrome Addict

### Controls
| Desktop | Action |
| --- | --- |
| WASD | move |
| mouse | look (pointer lock in play) |
| Shift | sprint |
| Space | jump (double jump; hold to fly) |
| Click or F | tackle, or throw what you're holding |
| E | grab, slots, ripperdoc; hold at a wall to paint |
| Q | flop |
| H | holler |
| P | poop |
| C | horn charge |
| V | voice mode |
| R | restart |
| Esc | closes slots, shop or customization |

**Touch:** left thumb is a floating stick, right thumb looks. Buttons are TACKLE, JUMP (hold to fly),
GRAB, FLOP, YELL, POOP and CHARGE (only when you have horns). Landscape plays best.

`localStorage` keys: `bt_best`, `bt_voice` (legacy), `bt_voice2`, `bt_look`. Every access is wrapped
in try/catch.

---

## 3. Code map (`game/index.html`, about 2,500 lines)

The sections are marked with `/* ---------------- name ---------------- */` comments. Line numbers are
approximate and drift with edits.

| ~Line | Section | Key names |
| --- | --- | --- |
| 1–260 | markup and CSS | HUD (`#hud`), touch buttons (`#touch`), screens `#title`, `#gameover`, `#slots`, `#custom`, `#doc` |
| 270 | utils and math | `V`, `vadd`, `qrot`, `qyaw`, `clamp`, `smooth`, `angDamp`, `hex`, `mixc`, `tone` |
| 316 | WebGL renderer | shaders `VS_BODY`/`FS_BODY` (tone curve, AO, rim, YIQ hue, tint, fog), `SKY_FS` (supports `view.lens`), `initGL` (shadow FBO), `bpush` with globals `AMUL`/`GADD`/`CMIX` (alpha, glow and gold tint for the Doubloon crossfade); batches `STATIC`/`DYN`/`TRN` × meshes `cube`, `sph`, `cyl`, `cone`, `wedge`, `arc` |
| 512 | world | `W`, `LAYOUT` (4×4 blocks), `gen_res`/`down`/`gas`/`plaza`/`park`/`trailer`/`tower`/`constr`, `solid`, `rampS`, `GRID`, `pushOut`, `groundInfo`, `raycast`; the clinic is built in `gen_trailer`, the slots kiosk in `gen_plaza` |
| 746 | props | `PK` table (incl. `poop`), `makeProp`, `propStep`, `drawProp` |
| 851 | substances and effects | `SUBS`, `addEffect`, `fxMatch`/`hasFx`/`fxK` (the `ALL` effect counts as every fx except OBJECT), `mods()` (every modifier is computed here each frame) |
| 892–965 | characters, NPCs, player | `makeNpc`, `npcUpdate`, `makePlayer`, `playerUpdate` (coyote time, jump buffer, double jump, flight, horn wind-up and steering, fold, stuck, glitch, jelly), `ragUpdate`, `playerPose` |
| 1053 | game state | `FEATS`, `newGame`, `spawnStash` (rolls laced), `toast`, `pop`, `addScore`, `award` |
| 1096 | interactions | `actions` (input → tackle, throw, fire, horn charge, grab, slots, doc, holler), `interactions` (charge and horn hits), `knockNpcG(i,v,byPlayer,thrown,label)`, `explode` |
| 1198 | main update | `update(dt,inp)` order: effects → clock → camera → actions → `playerUpdate` → use, poop, focus, form, parade, fold, doc → props, NPCs, party → events → HUD feats |
| 1249–1340 | uses, party, shapeshifting | `USE_TIME`, `startUse`, `pickup`, `partyStart`/`End`, `FORMS`, `transform`, `fireUpdate` |
| 1339–1430 | voices | `VOICE`, `toggleVoice`, `speak` (routes to fried or TTS), `makeFryBus`, `FRY_EQ`, `gibberish`, `friedSpeak(text,f0,rate,vol,pan,ctx?,dest?)` (renders offline for tests), `friedSay` |
| 1424 | poop | `poopCols`, `drawPoopModel(…,kind)`, `poopActions`, `poopUpdate`, `throwPoop`, `dropPoop`, `splatPoop`, `addDecal(pos,n,col,r,glow)`, `rayHitN` |
| 1477–1530 | joint, salvia, TTS ranking | `findFocus`, `focusAim`, `OBJECTS`, `becomeObject`, `endObject`, `loadVoices`, `pickVoice` |
| 1537–1600 | Doubloon, laced, horns and holy poop | `PARADE`, `doubloonRush`, `paradeUpdate`, `endParade`, `drawPlayerFX` (crossfade), `foldK`, `startFold`, `foldUpdate`, `HORN_LINES`/`GORE_LINES`, `HOLY_COLS`/`HELL_COLS`, `poopFanfare`, `poopAura`, `poopSplatFX` |
| 1639 | rendering | `render()` (lens shift via `PM[8]`/`PM[9]`), `drawOverlay()` (stash labels and arrows, bubbles including the doc's, popups, vignettes), `cameraUpdate` |
| 1721 | characters | `drawHuman` (rig, IK, `poseBlend`, `out.B`), `playerHead`, `customHair`, `topCloth`, `coatTails`, `cyberBody`, wings (`fanWing`), `angelExtras`/`demonExtras`/`minoExtras`/`skinExtras`, `drawPlayer`, `drawPlayerHuman`, `drawCreature`, `centaurRider`, `drawNpc`, `drawQuad` (`headDown`), `QSPEC` species |
| 1789 | customization | `SKIN_TONES`, `HAIR_COLS`, `CLOTH_COLS`, `PANTS_COLS`, `SHOE_COLS`, `LOOK_OPTS`, `CUSTOM`, `applyLook`, `customPreview`, `CTABS`, `renderCustomTab`, `randomLook`, `openCustom`/`closeCustom` |
| 1896 | ripperdoc | `CYBER`, `KIDNEY`, `cyberBoost`, `cyberDur`, `docSay`, `openDoc`/`closeDoc`, `renderDoc`, `buyCyber`, `docUpdate` (greeting, molar), `neonText` and `SIGNFONT`, `docHead`, `drawDoc` |
| 2229 | pickup models | `drawItem` (pills with imprints via `GLYPH`/`textRuns`, tab, bag, bottle, joint, salvia), `drawStash` |
| 2313 | HUD | `syncHUD` (prompts, effect pills, CHARGE button visibility, near-slots and near-doc) |
| 2345 | audio | `SFX` table, `sfx`, `noise` (kinds: sniff, pour, shatter, stumble, wing, snort, drill, rumble) |
| 2358 | slots | `SLOT`, `ODDS`, `PITY`, `rollOutcome(force)`, `spin`, `syncPity`, `settle` |
| 2414 | input | `keys`/`pressed`, touch stick and look, `bindT`, `gatherInput` |
| 2446 | flow | `startGame`, `gameOver`, title legend, button wiring |
| 2467 | boot and loop | `frame()` (≤12 fixed substeps at ≥45 Hz; `G.state` is title, play, slots, doc or over; `G.custom` for the dressing room), demo URL params |

**Demo URL params** (for screenshots and debugging):
- `?demo=shot` stages a plaza scene. Other values: `zoo`, `kalei`, `magnet`, `jugg`, `float`
  (comma-separated).
- `&form=dragon` starts in a form. `&freeze=0.05` stops the auto-updates so a script can pose
  things. `&cam=`, `&pitch=` and `&dist=` set the camera.

---

## 4. Working on it

1. Edit `game/index.html`.
2. Run `python tests/make_standalone.py`. It regenerates the standalone page that tests and desktop use.
3. Run `node --check` on the extracted script, or just load the standalone page and watch the console.
4. Run `python tests/feat3.py`, `python tests/feat4.py` and `python tests/feat5.py` (after `python tests/vendor_rapier.py`). All should finish with `"errs": []`.
5. Publish: with the Artifact tool, publish `game/index.html` with `url`
   `https://claude.ai/artifact/XgyMk7wJZrRtXTrLYhEusv`. Read the artifact first in a new chat.
6. Run `python tests/sync_builds.py`. It copies the standalone page to
   `desktop/borrowed_time_desktop/dist/index.html`, rebuilds `pwa/index.html` with the manifest and
   service-worker lines, and bumps `VERSION` in `pwa/sw.js`.

**Artifact rules that matter here:**
- No `<!doctype>`/`<html>`/`<head>`/`<body>`; `<title>` goes at the top.
- Google Fonts are the only allowed external stylesheet. No service workers in the artifact build.
- `localStorage` must be wrapped in try/catch.
- `alert`/`confirm` don't work; use in-page UI.

**Testing tips:**
- SwiftShader is slow. Screenshots of heavy scenes, like the Doubloon parade, can take more than 30 s,
  so tests use a 180 s screenshot timeout.
- Drive the game with `update(1/60, I({...}))`, where `I` fills defaults for `mx, my, sprint, jump,
  jumpHeld, tackle, grab, grabHeld, flop, holler, poop, charge, lookX, lookY, zoom`.
- Set `G.cam.yaw` before tackling or charging from standstill, because they aim along the camera.
- Spawn sits near the trailer cluster. Test in open road, e.g. `V(0,0,-20)` facing +z, so charges
  don't hit trailers.

---

## 5. Decisions and boundaries to keep

- **Clean room.** The code and the primitive-built art are original. The title says "inspired by the
  slapstick of Goat Simulator". Don't bring in Goat Simulator code, assets or names.
- **No third-party IP.** These were replaced with originals:
  - Fortnite pirate token → Cursed Doubloon
  - Cyberpunk ripperdoc → Doc Suture with original implant names (no Sandevistan, Mantis Blades and
    so on)
  - Keep new requests that name brands or franchises on the same footing.
- **Declined:** an ecstasy "dildo sword" modeled on an adult-toy company's products. It's sexual
  content and copies a company's designs. An offered alternative was not built: a glowing rave sword
  whose shape changes with each animal.
- **Voices:**
  - Real people's voices were not scraped from YouTube or elsewhere.
  - The reference meme clip was used only as a measurement target.
  - Don't put real people's photos or voices in the game.
- **Satire framing.** The effects are invented, and there's no real-world drug information (doses,
  sourcing, methods). The title screen carries an 18+ disclaimer.
  - The laced/fent mechanic is a punishment.
  - Its counters (test strips, naloxone) are harm-reduction flavored.
  - Keep it non-instructional.
- **Commercial release:** real brand-like names ("Xanax", "Henny") are a trademark risk on Steam. Swap
  in parody names before selling. The desktop README covers this.

---

## 6. Known issues and loose ends

- Not yet tested on a real phone or real GPU. Everything was verified in headless Chromium with mobile
  viewport and touch emulation. Touch devices render at up to 1.5× DPR. Low-end phone performance is
  unknown.
- The Windows `.exe` workflow has never actually run. Run it once, and pin the actions to commit SHAs
  before relying on it.
- Fried voices can't be applied to TTS, which is a Web Speech limitation.
- Dollas and implants reset every run. There is no meta-progression yet.
- Cops can't reach a flying player, so flight is a strong escape.
- Fixed 14 Nov 2026:
  - The "edge of the world" seen from high up was a shader-order bug: fog was mixed in after the
    hue/saturation grade, so far ground stayed blue while the graded sky went grey or hue-shifted.
    `FS_BODY` now applies tint, then fog, then the grade.
  - The Doubloon parade now uses a gold tint, a quarter-strength JOINT vignette and a capped hue spin
    (`m.all` block in `mods()`, `m.focusVig`).
  - The controls hint hides on screens under 1100 px wide while effect pills are showing, so the two
    no longer overlap.

## 7. Ideas already on the table

- The rave glow-stick sword per animal, offered as the alternative above.
- An Android APK via Tauri 2 mobile (`cargo tauri android init/build`) in CI. iPhone needs an Apple
  developer account, so the PWA is the practical iPhone route.
- Steam: Steamworks SDK (`steamworks` crate) for achievements, which would map to the feats. The
  overlay may not draw over WebView2.
- Meta-progression: carry dollas or a "chrome bank" between runs.
- Recorded voice packs, from the owner's own recordings or licensed packs, as a fourth voice mode.

## 8. If the work moves back to Rust/Bevy (JITTERS)

JITTERS (in `rust_prototype/`) already has:
- the life clock, 5 fictional substances, tolerance, comedown and overload
- stash beacons with a compass, and tackle/flop
- sphere-vs-AABB physics

It's laid out as `main.rs`, `state.rs`, `substances.rs`, `world.rs`, `player.rs`, `pickups.rs`,
`hud.rs` and `util.rs`.

| Port this from Borrowed Time | Into JITTERS |
| --- | --- |
| `SUBS`, `mods()`, `addEffect`, `fxK` | `substances.rs` (data plus a per-frame modifier struct) |
| `playerUpdate`, `ragUpdate`, flight, horns, fold | `player.rs` |
| `FORMS`, `QSPEC`, `drawHuman`, `drawQuad`, cloth chains | a new `forms.rs`; procedural meshes per part, or a skinned rig |
| `spawnStash`, laced, `pickup`, tolerance, `cyberBoost` | `pickups.rs` |
| slots, ripperdoc, customization UI | `bevy_ui` or `bevy_egui` screens |
| `sfx`, `noise`, `friedSpeak` | `bevy_kira_audio` or `fundsp` for synthesis |
| `LAYOUT` and the `gen_*` builders | `world.rs` |
| prop physics and ragdolls | Avian or Rapier instead of hand-rolled |

Bevy can target iOS and Android, but the web build or Tauri mobile is the faster route to phones.

## 9. Working with the owner

- They send quick feature requests, often several while work is underway. Fold them into the running
  batch and confirm each one.
- They want to see progress. Send screenshots after each batch; `tests/shots4.py` has staged scenes
  to copy.
- They play on their phone and share builds on Discord, so keep both the link and the downloadable
  builds working.
- They asked for an account skill called **OVERDRIVE**. Its standing expectations:
  - audit code and dependencies for safety
  - do a final performance pass
  - back claims with data
  - offer renditions to pick from for design choices
  - use solid references
