# Reference media: pictures, video and frame-by-frame study

Read this before you download any picture or video, or when you need to measure motion (gravity, bounce, friction, timing) from footage.

## 1. The rights gate (before anything is downloaded)

| Footage | OK to fetch? | Notes |
| --- | --- | --- |
| The user's own recordings, including captures of a game they own (OBS, console capture) | Yes | Private study only. The game's art still belongs to its publisher: study the motion, never reproduce the look. |
| Creative Commons (CC0, CC-BY, CC-BY-SA) or public domain | Yes | Record the license and the author. If anything derived is ever shown, follow the license's attribution terms. |
| The rights holder gave permission | Yes | Record who gave permission and where. |
| Anything else (random uploads, trailers, other people's let's-plays) | No | Watch it in the browser instead and take notes. Ask the user for a capture they own, or find a licensed alternative. |

Good licensed sources include Wikimedia Commons, NASA media (mostly public domain), the Internet Archive (check each item), and YouTube's "Creative Commons" search filter.

Two rules always hold:

- Media lives in `.refcache/` (gitignored). It is never committed, bundled, shipped or re-uploaded.
- Only measurements, notes and your own sketches leave the cache.

## 2. Tools

- **ffmpeg / ffprobe:** install them with the system package manager.
- **yt-dlp:** pin the version (`pip install yt-dlp==<version>`) and update it deliberately, because sites change.
- **refpipe:** this skill's Rust CLI in `scripts/refpipe`. It has no third-party crates, so the audit is just its own source. Build it with `cargo build --release --manifest-path <skill>/scripts/refpipe/Cargo.toml`; the binary lands in `target/release/refpipe`.

If cargo isn't available (on claude.ai, for example), the equivalent ffmpeg commands are given in section 5.

## 3. refpipe commands

```
refpipe check                                   versions of yt-dlp, ffmpeg and ffprobe
refpipe fetch <url> --license <kind> --note "<why>" [--cache .refcache]
        kind: own | cc0 | cc-by | cc-by-sa | public-domain | permission
        Without a valid --license it refuses. It appends to .refcache/manifest.jsonl.
refpipe frames <video> --fps 30 [--start 12.5] [--dur 2] [--out dir]
refpipe sheet  <video> --fps 8 [--cols 6 --rows 4] [--width 320] [--start s --dur d]
        Contact sheets with timestamps. Open them with your image reader.
refpipe motion <video> [--start s --dur d]      CSV t,score: per-frame change, where peaks are impacts and cuts
refpipe track  <video> [--threshold 200] [--invert] [--roi x,y,w,h] [--start s --dur d] [--fps n]
        Tracks the centroid of the brightest blob (darkest with --invert), as CSV t,x,y,area.
refpipe fit <track.csv> [--axis y] [--px-per-m K] [--from t0 --to t1]
        Least-squares parabola. Gives acceleration in px/s² (and m/s² if a scale is given) plus R².
refpipe bounce <h1> <h2> [h3 ...]               Coefficient of restitution from successive peak heights
```

## 4. Frame-by-frame physics study

1. **Pick a clean clip.** Look for a static camera, an object with good contrast against the background, and something of known size in frame for the scale (a person is about 1.7 m tall, a door about 2.0 m).
2. **Survey it.** Run `refpipe sheet` at 8–12 fps, look at the sheets, and note the time ranges of interest.
3. **Find events.** `refpipe motion` shows a spike at each impact. Use them to time impact-to-rest, hit-stop and debris settle times.
4. **Measure trajectories.** Run `refpipe track` on the range of interest. If tracking is noisy, narrow the `--roi`, adjust `--threshold`, or annotate positions by hand from the frames into a CSV.
5. **Fit.** `refpipe fit --px-per-m K` gives the acceleration. Compare it with 9.81 m/s² to check the scale, then reuse that scale for other measurements.
6. **Derive the rest.**
   - Restitution: e = √(h₂/h₁) from successive bounce peaks (`refpipe bounce`).
   - Friction: the deceleration of a sliding object (fit along x) divided by g gives μ.
   - Spread: the radius of the debris field over the drop height.
7. **Write it up.** Save `notes.md` in the cache with a table of what you measured, the clip, the license and the method. Copy only that table into the project docs.

Perspective and lens distortion bias measurements. Prefer motion roughly parallel to the image plane, and treat values within about 10% as a match.

## 5. Without refpipe (raw ffmpeg)

```
ffmpeg -ss 12.5 -t 2 -i in.mp4 -vf fps=30 frames/f_%05d.png
ffmpeg -ss 0 -t 6 -i in.mp4 -vf "fps=8,scale=320:-1,tile=6x4" -frames:v 4 sheet_%02d.png
ffmpeg -i in.mp4 -vf "select='gte(scene,0)',metadata=print:file=scores.txt" -f null -
```
