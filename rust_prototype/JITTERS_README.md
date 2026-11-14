# JITTERS

A physics-chaos sandbox in Rust (Bevy 0.15). You play a wired, wide-eyed wreck
whose life clock is always running out. Hunt down stashes of fictional
substances to buy more time. Each one bends the rules differently, and your
body gets used to them if you keep going back to the same thing.

Everything is primitive shapes and original code. No third-party assets.

## Run

```
cargo run --release
```

First build takes a while (Bevy). Linux needs the usual Bevy system packages:

```
sudo apt install g++ pkg-config libx11-dev libasound2-dev libudev-dev \
  libxkbcommon-x11-0 libwayland-dev libxkbcommon-dev
```

## Controls

| Key | Action |
| --- | --- |
| WASD | Move (relative to camera) |
| Mouse | Orbit camera |
| Space | Jump |
| Shift | Sprint |
| Left click / F | Tackle (launches junk, scores chaos points) |
| Q | Flop (ragdoll-ish faceplant) |
| R | Restart after the comedown |
| Esc | Release mouse (click to grab again) |

## The loop

- Your life clock drains at 1 second per second. At zero, the comedown wins.
- Glowing beacons mark stashes. HUD shows the nearest one and which way to look.
- Stashes despawn after ~50 seconds. Some sit on low rooftops (Moon Chew helps).
- Tackle junk for chaos points. Chained hits build a combo.

## Substances (all fictional)

| Name | Life | Effect |
| --- | --- | --- |
| Go-Go Powder | +12s | 1.7x speed, camera twitch, wider FOV |
| Blue Slurp | +10s | Slow and floaty, life drains at 35% |
| Giggle Caps | +11s | Sky and junk cycle colors, junk hops around, 1.5x points |
| Moon Chew | +9s | Quarter gravity, bigger jumps |
| Crunch Rock | +10s | 3x tackle force, 2x points |

Rules that tie them together:

- **Tolerance:** each recent use of the same substance cuts its next life gain
  (x0.65 per use, floor of 2s). Tolerance fades by one use per 25 seconds.
  Variety keeps you alive.
- **Comedown:** when an effect ends you crash for a few seconds (slower, faster
  drain). Grabbing another stash cancels it.
- **Overload:** three or more active at once drains life 1.6x faster.

## Layout

```
src/main.rs        app wiring, restart
src/state.rs       Life, Run, Toast resources
src/substances.rs  substance data, effect timers, modifiers
src/world.rs       town generation, prop physics, hallucination visuals
src/player.rs      character, controller, camera
src/pickups.rs     stash spawning, collection, tolerance
src/hud.rs         life bar, score, effects, stash compass
src/util.rs        RNG, sphere-vs-box collision
```

Physics is hand-rolled (sphere vs axis-aligned boxes) to keep the dependency
list to Bevy alone. Swap in Avian or Rapier if you want real rigid bodies.

## Using Unity instead

Unity scripts are C#, so a Rust core would live in a native plugin (`cdylib`
called through P/Invoke). The systems here (substance modifiers, tolerance,
life clock) are plain data and math and would port to that setup cleanly. For
a game this size, staying in Bevy is simpler.

## Ideas

- Real rigid-body physics and a proper ragdoll
- A grapple-tongue-style gadget on the flop or tackle
- Dealer NPCs, police-chase heat meter, interiors
- Audio: heartbeat that speeds up as life drops, muffled sound during Blue Slurp
