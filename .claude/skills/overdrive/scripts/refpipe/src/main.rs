//! refpipe: reference-footage pipeline for frame-by-frame motion study.
//!
//! It drives two external programs, yt-dlp (fetching) and ffmpeg/ffprobe (decoding),
//! and does the measuring itself: motion scores, bright/dark blob tracking,
//! least-squares parabola fits and coefficients of restitution.
//! There are no third-party crates, so auditing it means reading this file.

use std::env;
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{exit, Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

/// Footage is fetched only under one of these. Anything else is refused (see reference-media.md).
const LICENSES: &[&str] = &["own", "cc0", "cc-by", "cc-by-sa", "public-domain", "permission"];
const BOOL_FLAGS: &[&str] = &["invert"];
const CACHE: &str = ".refcache";

const USAGE: &str = "refpipe: reference-footage pipeline (fetch, frames, sheets, motion, tracking, fits)

  refpipe check
  refpipe fetch <url> --license <own|cc0|cc-by|cc-by-sa|public-domain|permission> --note <why> [--cache dir]
  refpipe frames <video> [--fps 30] [--start s] [--dur s] [--out dir]
  refpipe sheet  <video> [--fps 8] [--cols 6] [--rows 4] [--width 320] [--start s] [--dur s] [--out dir]
  refpipe motion <video> [--fps n] [--width 320] [--start s] [--dur s]          > t,score
  refpipe track  <video> [--threshold 200] [--invert] [--roi x,y,w,h] [--min-area 3]
                         [--fps n] [--width 320] [--start s] [--dur s]       > t,x,y,area
  refpipe fit <track.csv> [--axis y|x] [--px-per-m k] [--from t0] [--to t1]
  refpipe bounce <h1> <h2> [h3 ...]

Media stays in .refcache/ (it gets its own .gitignore). Never commit or ship footage.
";

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() || matches!(args[0].as_str(), "-h" | "--help" | "help") {
        print!("{USAGE}");
        return;
    }
    let result = Opts::parse(&args[1..]).and_then(|o| run(&args[0], &o));
    if let Err(e) = result {
        eprintln!("refpipe: {e}");
        exit(1);
    }
}

fn run(cmd: &str, o: &Opts) -> Result<(), String> {
    match cmd {
        "check" => check(),
        "fetch" => fetch(o),
        "frames" => frames(o),
        "sheet" => sheet(o),
        "motion" => motion(o),
        "track" => track(o),
        "fit" => fit_cmd(o),
        "bounce" => bounce_cmd(o),
        _ => Err(format!("unknown command '{cmd}' (try --help)")),
    }
}

/* ---------- arguments ---------- */

#[derive(Debug, Default)]
struct Opts {
    pos: Vec<String>,
    kv: Vec<(String, String)>,
}

impl Opts {
    fn parse(a: &[String]) -> Result<Opts, String> {
        let mut o = Opts::default();
        let mut i = 0;
        while i < a.len() {
            if let Some(k) = a[i].strip_prefix("--") {
                if BOOL_FLAGS.contains(&k) {
                    o.kv.push((k.to_string(), "1".to_string()));
                } else {
                    let v = a.get(i + 1).ok_or_else(|| format!("--{k} needs a value"))?;
                    o.kv.push((k.to_string(), v.clone()));
                    i += 1;
                }
            } else {
                o.pos.push(a[i].clone());
            }
            i += 1;
        }
        Ok(o)
    }
    fn get(&self, k: &str) -> Option<&str> {
        self.kv.iter().rev().find(|(a, _)| a == k).map(|(_, v)| v.as_str())
    }
    fn has(&self, k: &str) -> bool {
        self.get(k).is_some()
    }
    fn opt_num(&self, k: &str) -> Result<Option<f64>, String> {
        match self.get(k) {
            None => Ok(None),
            Some(v) => match v.parse::<f64>() {
                Ok(x) if x.is_finite() => Ok(Some(x)),
                _ => Err(format!("--{k} must be a number, got '{v}'")),
            },
        }
    }
    fn num(&self, k: &str, def: f64) -> Result<f64, String> {
        Ok(self.opt_num(k)?.unwrap_or(def))
    }
    fn first(&self, what: &str) -> Result<&str, String> {
        self.pos.first().map(|s| s.as_str()).ok_or_else(|| format!("missing {what}"))
    }
}

fn existing(path: &str) -> Result<&str, String> {
    if Path::new(path).is_file() {
        Ok(path)
    } else {
        Err(format!("no such file: {path}"))
    }
}

fn now_unix() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

/// Minimal JSON string escaping for the manifest.
fn js(s: &str) -> String {
    let mut o = String::with_capacity(s.len() + 2);
    o.push('"');
    for ch in s.chars() {
        match ch {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' => o.push_str("\\n"),
            '\r' => o.push_str("\\r"),
            '\t' => o.push_str("\\t"),
            c if (c as u32) < 0x20 => o.push_str(&format!("\\u{:04x}", c as u32)),
            c => o.push(c),
        }
    }
    o.push('"');
    o
}

/* ---------- external tools ---------- */

fn first_line(bin: &str, flag: &str) -> Option<String> {
    let out = Command::new(bin).arg(flag).output().ok()?;
    String::from_utf8_lossy(&out.stdout).lines().next().map(|l| l.trim().to_string())
}

fn check() -> Result<(), String> {
    for (bin, flag) in [("yt-dlp", "--version"), ("ffmpeg", "-version"), ("ffprobe", "-version")] {
        println!("{bin:8} {}", first_line(bin, flag).unwrap_or_else(|| "MISSING".into()));
    }
    Ok(())
}

fn ffmpeg(args: &[String]) -> Result<(), String> {
    let st = Command::new("ffmpeg")
        .args(["-hide_banner", "-loglevel", "error", "-y"])
        .args(args)
        .status()
        .map_err(|e| format!("could not start ffmpeg: {e}"))?;
    if st.success() {
        Ok(())
    } else {
        Err(format!("ffmpeg failed ({st})"))
    }
}

/// `-ss start -i input -t dur`, with fast input seeking.
fn range_args(o: &Opts, input: &str) -> Result<Vec<String>, String> {
    let mut v = Vec::new();
    if let Some(s) = o.opt_num("start")? {
        v.extend(["-ss".to_string(), s.to_string()]);
    }
    v.extend(["-i".to_string(), input.to_string()]);
    if let Some(d) = o.opt_num("dur")? {
        v.extend(["-t".to_string(), d.to_string()]);
    }
    Ok(v)
}

fn ensure_cache(dir: &Path) -> Result<(), String> {
    fs::create_dir_all(dir).map_err(|e| format!("cannot create {}: {e}", dir.display()))?;
    let gi = dir.join(".gitignore");
    if !gi.exists() {
        fs::write(&gi, "# reference media never goes into git\n*\n").map_err(|e| format!("cannot write {}: {e}", gi.display()))?;
    }
    Ok(())
}

fn out_dir(o: &Opts, input: &str, kind: &str) -> Result<PathBuf, String> {
    let dir = match o.get("out") {
        Some(d) => PathBuf::from(d),
        None => {
            ensure_cache(Path::new(CACHE))?;
            let stem = Path::new(input).file_stem().map(|s| s.to_string_lossy().into_owned()).unwrap_or_else(|| "clip".into());
            Path::new(CACHE).join(kind).join(stem)
        }
    };
    fs::create_dir_all(&dir).map_err(|e| format!("cannot create {}: {e}", dir.display()))?;
    Ok(dir)
}

/* ---------- fetch (license-gated) ---------- */

fn fetch(o: &Opts) -> Result<(), String> {
    let url = o.first("URL")?;
    if !(url.starts_with("https://") || url.starts_with("http://")) {
        return Err("the URL must start with http:// or https://".into());
    }
    let lic = o.get("license").ok_or(
        "--license is required (own | cc0 | cc-by | cc-by-sa | public-domain | permission). Footage without one of these is not fetched.",
    )?;
    if !LICENSES.contains(&lic) {
        return Err(format!("--license '{lic}' is not one of: {}", LICENSES.join(", ")));
    }
    let note = o.get("note").ok_or("--note is required: say what the footage is for")?;
    let cache = PathBuf::from(o.get("cache").unwrap_or(CACHE));
    ensure_cache(&cache)?;
    let template = cache.join("%(extractor)s_%(id)s.%(ext)s");
    let out = Command::new("yt-dlp")
        .args(["--no-playlist", "--restrict-filenames", "--no-simulate"])
        .args(["-f", "bv*[height<=720]+ba/b[height<=720]/b"])
        .args(["--print", "after_move:filepath", "-o"])
        .arg(&template)
        .arg(url)
        .output()
        .map_err(|e| format!("could not start yt-dlp (is it installed?): {e}"))?;
    if !out.status.success() {
        let err = String::from_utf8_lossy(&out.stderr);
        return Err(format!("yt-dlp failed: {}", err.lines().last().unwrap_or("no output")));
    }
    let file = String::from_utf8_lossy(&out.stdout).lines().last().unwrap_or("").trim().to_string();
    let rec = format!(
        "{{\"url\":{},\"license\":{},\"note\":{},\"file\":{},\"fetched_unix\":{}}}\n",
        js(url),
        js(lic),
        js(note),
        js(&file),
        now_unix()
    );
    let mpath = cache.join("manifest.jsonl");
    OpenOptions::new()
        .create(true)
        .append(true)
        .open(&mpath)
        .and_then(|mut f| f.write_all(rec.as_bytes()))
        .map_err(|e| format!("cannot write {}: {e}", mpath.display()))?;
    println!("{file}");
    Ok(())
}

/* ---------- frames and contact sheets ---------- */

fn frames(o: &Opts) -> Result<(), String> {
    let input = existing(o.first("video file")?)?;
    let fps = o.num("fps", 30.0)?;
    let dir = out_dir(o, input, "frames")?;
    let mut a = range_args(o, input)?;
    a.extend(["-vf".into(), format!("fps={fps}"), dir.join("f_%05d.png").to_string_lossy().into_owned()]);
    ffmpeg(&a)?;
    println!("{}", dir.display());
    Ok(())
}

fn sheet(o: &Opts) -> Result<(), String> {
    let input = existing(o.first("video file")?)?;
    let fps = o.num("fps", 8.0)?;
    let cols = o.num("cols", 6.0)?.max(1.0) as u32;
    let rows = o.num("rows", 4.0)?.max(1.0) as u32;
    let width = o.num("width", 320.0)?.max(16.0) as u32;
    let offset = o.num("start", 0.0)?;
    let dir = out_dir(o, input, "sheets")?;
    let pattern = dir.join("sheet_%02d.png").to_string_lossy().into_owned();
    let base = format!("fps={fps},scale={width}:-2");
    let tile = format!("tile={cols}x{rows}:padding=2:margin=2:color=0x101010");
    // Each frame is stamped with its source time. If drawtext or fonts are missing, fall back to plain tiles.
    let label = format!("drawtext=text='%{{pts\\:flt\\:{offset}}}':x=4:y=4:fontsize=13:fontcolor=white:box=1:boxcolor=black@0.6");
    let mut with_label = range_args(o, input)?;
    with_label.extend(["-vf".into(), format!("{base},{label},{tile}"), pattern.clone()]);
    if ffmpeg(&with_label).is_err() {
        let mut plain = range_args(o, input)?;
        plain.extend(["-vf".into(), format!("{base},{tile}"), pattern]);
        ffmpeg(&plain)?;
        eprintln!("refpipe: sheets written without timestamps (drawtext unavailable)");
    }
    println!("{}", dir.display());
    Ok(())
}

/* ---------- raw grayscale decoding ---------- */

struct Probe {
    w: u32,
    h: u32,
    fps: f64,
}

fn parse_rate(r: &str) -> Option<f64> {
    let v = match r.split_once('/') {
        Some((a, b)) => {
            let (a, b) = (a.parse::<f64>().ok()?, b.parse::<f64>().ok()?);
            if b == 0.0 {
                return None;
            }
            a / b
        }
        None => r.parse::<f64>().ok()?,
    };
    (v.is_finite() && v > 0.0).then_some(v)
}

fn probe(input: &str) -> Result<Probe, String> {
    let out = Command::new("ffprobe")
        .args(["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,avg_frame_rate", "-of", "csv=p=0:s=x"])
        .arg(input)
        .output()
        .map_err(|e| format!("could not start ffprobe: {e}"))?;
    let text = String::from_utf8_lossy(&out.stdout);
    let line = text.lines().next().ok_or("ffprobe found no video stream")?;
    let p: Vec<&str> = line.trim().split('x').collect();
    if p.len() < 3 {
        return Err(format!("unexpected ffprobe output '{line}'"));
    }
    let w = p[0].parse::<u32>().map_err(|_| "bad width from ffprobe")?;
    let h = p[1].parse::<u32>().map_err(|_| "bad height from ffprobe")?;
    let fps = parse_rate(p[2]).unwrap_or(30.0);
    if w == 0 || h == 0 {
        return Err("video has zero size".into());
    }
    Ok(Probe { w, h, fps })
}

/// Scaled size used for analysis: an even width (default 320, never upscaled), height keeps the aspect.
fn target_dims(o: &Opts, p: &Probe) -> Result<(u32, u32, f64), String> {
    let want = o.num("width", 320.0)?.max(16.0).min(p.w as f64);
    let w = ((want as u32) / 2 * 2).max(2);
    let h = (((p.h as f64 * w as f64 / p.w as f64) / 2.0).round() as u32 * 2).max(2);
    Ok((w, h, w as f64 / p.w as f64))
}

fn read_full(r: &mut impl Read, buf: &mut [u8]) -> Result<bool, String> {
    let mut got = 0;
    while got < buf.len() {
        let k = r.read(&mut buf[got..]).map_err(|e| format!("read error: {e}"))?;
        if k == 0 {
            return if got == 0 { Ok(false) } else { Err("truncated frame from ffmpeg".into()) };
        }
        got += k;
    }
    Ok(true)
}

/// Decodes the selected range to w×h grayscale frames and calls `f(index, pixels)` for each.
/// Returns the number of frames.
fn decode_gray(o: &Opts, input: &str, w: u32, h: u32, fps: f64, mut f: impl FnMut(usize, &[u8])) -> Result<usize, String> {
    let mut args = range_args(o, input)?;
    args.extend([
        "-vf".into(),
        format!("fps={fps},scale={w}:{h},format=gray"),
        "-f".into(),
        "rawvideo".into(),
        "-pix_fmt".into(),
        "gray".into(),
        "-".into(),
    ]);
    let mut child = Command::new("ffmpeg")
        .args(["-hide_banner", "-loglevel", "error"])
        .args(&args)
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| format!("could not start ffmpeg: {e}"))?;
    let mut out = child.stdout.take().ok_or("no ffmpeg stdout")?;
    let mut buf = vec![0u8; (w * h) as usize];
    let mut i = 0;
    while read_full(&mut out, &mut buf)? {
        f(i, &buf);
        i += 1;
    }
    let st = child.wait().map_err(|e| format!("ffmpeg wait: {e}"))?;
    if !st.success() {
        return Err(format!("ffmpeg failed while decoding ({st})"));
    }
    Ok(i)
}

/* ---------- motion and tracking ---------- */

fn mean_abs_diff(a: &[u8], b: &[u8]) -> f64 {
    let s: u64 = a.iter().zip(b).map(|(x, y)| x.abs_diff(*y) as u64).sum();
    s as f64 / (a.len().max(1) as f64 * 255.0)
}

fn motion(o: &Opts) -> Result<(), String> {
    let input = existing(o.first("video file")?)?;
    let p = probe(input)?;
    let (w, h, _) = target_dims(o, &p)?;
    let fps = o.num("fps", p.fps)?;
    let start = o.num("start", 0.0)?;
    let mut prev: Vec<u8> = Vec::new();
    let mut rows = Vec::new();
    decode_gray(o, input, w, h, fps, |i, fr| {
        rows.push((i, if prev.is_empty() { 0.0 } else { mean_abs_diff(&prev, fr) }));
        prev.clear();
        prev.extend_from_slice(fr);
    })?;
    println!("t,score");
    for (i, s) in rows {
        println!("{:.4},{:.5}", start + i as f64 / fps, s);
    }
    Ok(())
}

/// Centroid of pixels at or above `thr` (at or below it with `invert`) inside roi (x0,y0,x1,y1) in frame pixels.
fn centroid(fr: &[u8], w: u32, h: u32, thr: u8, invert: bool, roi: (u32, u32, u32, u32)) -> Option<(f64, f64, u64)> {
    let (x0, y0) = (roi.0.min(w), roi.1.min(h));
    let (x1, y1) = (roi.2.min(w), roi.3.min(h));
    let (mut sx, mut sy, mut n) = (0u64, 0u64, 0u64);
    for y in y0..y1 {
        let row = &fr[(y * w) as usize..((y + 1) * w) as usize];
        for x in x0..x1 {
            let v = row[x as usize];
            if (!invert && v >= thr) || (invert && v <= thr) {
                sx += x as u64;
                sy += y as u64;
                n += 1;
            }
        }
    }
    // +0.5 puts the centroid at pixel centers.
    (n > 0).then(|| (sx as f64 / n as f64 + 0.5, sy as f64 / n as f64 + 0.5, n))
}

fn parse_roi(s: &str) -> Result<(f64, f64, f64, f64), String> {
    let v: Vec<f64> = s.split(',').map(|x| x.trim().parse::<f64>()).collect::<Result<_, _>>().map_err(|_| "--roi must be x,y,w,h")?;
    if v.len() != 4 || v[2] <= 0.0 || v[3] <= 0.0 {
        return Err("--roi must be x,y,w,h with positive w and h".into());
    }
    Ok((v[0], v[1], v[2], v[3]))
}

fn track(o: &Opts) -> Result<(), String> {
    let input = existing(o.first("video file")?)?;
    let p = probe(input)?;
    let (w, h, scale) = target_dims(o, &p)?;
    let fps = o.num("fps", p.fps)?;
    let start = o.num("start", 0.0)?;
    let invert = o.has("invert");
    let thr = o.num("threshold", if invert { 55.0 } else { 200.0 })?.clamp(0.0, 255.0) as u8;
    let min_area = o.num("min-area", 3.0)?.max(1.0) as u64;
    let roi = match o.get("roi") {
        Some(r) => {
            let (x, y, rw, rh) = parse_roi(r)?;
            let f = |v: f64| (v * scale).round().max(0.0) as u32;
            (f(x), f(y), f(x + rw), f(y + rh))
        }
        None => (0, 0, w, h),
    };
    let mut rows = Vec::new();
    let n = decode_gray(o, input, w, h, fps, |i, fr| {
        if let Some((cx, cy, a)) = centroid(fr, w, h, thr, invert, roi) {
            if a >= min_area {
                rows.push((start + i as f64 / fps, cx / scale, cy / scale, a));
            }
        }
    })?;
    println!("t,x,y,area");
    for (t, x, y, a) in &rows {
        println!("{t:.4},{x:.2},{y:.2},{a}");
    }
    eprintln!("refpipe: tracked {} of {n} frames at {w}x{h} (scale {scale:.3})", rows.len());
    Ok(())
}

/* ---------- fitting ---------- */

#[derive(Debug)]
struct Fit {
    a: f64,
    b: f64,
    c: f64,
    r2: f64,
    rms: f64,
}

fn solve3(mut m: [[f64; 3]; 3], mut r: [f64; 3]) -> Option<[f64; 3]> {
    for col in 0..3 {
        let piv = (col..3).max_by(|&a, &b| m[a][col].abs().total_cmp(&m[b][col].abs()))?;
        if m[piv][col].abs() < 1e-12 {
            return None;
        }
        m.swap(col, piv);
        r.swap(col, piv);
        let (pivot_row, pivot_r) = (m[col], r[col]);
        for (row, (mrow, rv)) in m.iter_mut().zip(r.iter_mut()).enumerate() {
            if row != col {
                let k = mrow[col] / pivot_row[col];
                for (dst, src) in mrow.iter_mut().zip(pivot_row.iter()).skip(col) {
                    *dst -= k * src;
                }
                *rv -= k * pivot_r;
            }
        }
    }
    Some([r[0] / m[0][0], r[1] / m[1][1], r[2] / m[2][2]])
}

/// Least-squares v(t) = a + b t + c t². Time is centered first for numerical stability.
fn fit_parabola(t: &[f64], v: &[f64]) -> Option<Fit> {
    if t.len() != v.len() || t.len() < 3 {
        return None;
    }
    let n = t.len() as f64;
    let tm = t.iter().sum::<f64>() / n;
    let (mut s, mut r) = ([0.0f64; 5], [0.0f64; 3]);
    for (&ti, &vi) in t.iter().zip(v) {
        let u = ti - tm;
        let mut pw = 1.0;
        for (k, sk) in s.iter_mut().enumerate() {
            *sk += pw;
            if k < 3 {
                r[k] += pw * vi;
            }
            pw *= u;
        }
    }
    let x = solve3([[s[0], s[1], s[2]], [s[1], s[2], s[3]], [s[2], s[3], s[4]]], r)?;
    let vm = v.iter().sum::<f64>() / n;
    let (mut ssr, mut sst) = (0.0, 0.0);
    for (&ti, &vi) in t.iter().zip(v) {
        let u = ti - tm;
        let pred = x[0] + x[1] * u + x[2] * u * u;
        ssr += (vi - pred).powi(2);
        sst += (vi - vm).powi(2);
    }
    Some(Fit {
        a: x[0] - x[1] * tm + x[2] * tm * tm,
        b: x[1] - 2.0 * x[2] * tm,
        c: x[2],
        r2: if sst > 0.0 { 1.0 - ssr / sst } else { 1.0 },
        rms: (ssr / n).sqrt(),
    })
}

fn fit_cmd(o: &Opts) -> Result<(), String> {
    let path = existing(o.first("CSV file (t,x,y,...)")?)?;
    let text = fs::read_to_string(path).map_err(|e| format!("cannot read {path}: {e}"))?;
    let col = match o.get("axis").unwrap_or("y") {
        "x" => 1,
        "y" => 2,
        other => return Err(format!("--axis must be x or y, got '{other}'")),
    };
    let (from, to) = (o.opt_num("from")?, o.opt_num("to")?);
    let (mut ts, mut vs) = (Vec::new(), Vec::new());
    for line in text.lines() {
        let f: Vec<&str> = line.split(',').collect();
        if f.len() <= col {
            continue;
        }
        let (Ok(t), Ok(v)) = (f[0].trim().parse::<f64>(), f[col].trim().parse::<f64>()) else { continue };
        if from.is_some_and(|a| t < a) || to.is_some_and(|b| t > b) {
            continue;
        }
        ts.push(t);
        vs.push(v);
    }
    if ts.len() < 4 {
        return Err(format!("need at least 4 points in range, got {}", ts.len()));
    }
    let f = fit_parabola(&ts, &vs).ok_or("fit failed (points are degenerate)")?;
    let acc = 2.0 * f.c;
    println!("points       {}", ts.len());
    println!("accel_px_s2  {acc:.2}   (image y grows downward, so falling is positive)");
    println!("v0_px_s      {:.2}", f.b);
    println!("p0_px        {:.2}", f.a);
    if let Some(k) = o.opt_num("px-per-m")? {
        if k <= 0.0 {
            return Err("--px-per-m must be positive".into());
        }
        let g = acc / k;
        println!("accel_m_s2   {g:.3}");
        println!("vs_standard  {:+.2}%  (standard gravity 9.80665 m/s²)", (g / 9.80665 - 1.0) * 100.0);
    }
    println!("r2           {:.5}", f.r2);
    println!("rms_px       {:.3}", f.rms);
    Ok(())
}

/// e = sqrt(h_next / h) for each pair of successive bounce peaks (heights above the floor).
fn restitution(h: &[f64]) -> Result<Vec<f64>, String> {
    if h.len() < 2 || h.iter().any(|x| !(x.is_finite() && *x > 0.0)) {
        return Err("give at least two positive peak heights".into());
    }
    Ok(h.windows(2).map(|w| (w[1] / w[0]).sqrt()).collect())
}

fn bounce_cmd(o: &Opts) -> Result<(), String> {
    let h: Vec<f64> = o.pos.iter().map(|s| s.parse::<f64>()).collect::<Result<_, _>>().map_err(|_| "heights must be numbers")?;
    let e = restitution(&h)?;
    for (i, v) in e.iter().enumerate() {
        println!("e{}            {v:.3}", i + 1);
    }
    println!("e_mean        {:.3}", e.iter().sum::<f64>() / e.len() as f64);
    Ok(())
}

/* ---------- tests ---------- */

#[cfg(test)]
mod tests {
    use super::*;

    fn s(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    #[test]
    fn parses_flags_and_positionals() {
        let o = Opts::parse(&s(&["clip.mp4", "--fps", "12", "--invert", "--roi", "1,2,3,4"])).unwrap();
        assert_eq!(o.pos, vec!["clip.mp4"]);
        assert_eq!(o.num("fps", 0.0).unwrap(), 12.0);
        assert!(o.has("invert"));
        assert_eq!(o.get("roi"), Some("1,2,3,4"));
        assert!(Opts::parse(&s(&["--fps"])).is_err());
        assert!(Opts::parse(&s(&["--fps", "abc"])).unwrap().num("fps", 1.0).is_err());
    }

    #[test]
    fn escapes_json() {
        assert_eq!(js("a\"b\\c\nd\u{1}"), "\"a\\\"b\\\\c\\nd\\u0001\"");
    }

    #[test]
    fn fit_recovers_gravity_with_noise() {
        // y = 20 + 3 t + 0.5 * 490 t² sampled at 60 fps, with ±0.5 px deterministic noise.
        let mut seed: u64 = 12345;
        let (mut t, mut y) = (Vec::new(), Vec::new());
        for i in 0..72 {
            let ti = i as f64 / 60.0;
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let noise = ((seed >> 33) as f64 / (1u64 << 31) as f64 - 0.5) * 1.0;
            t.push(ti);
            y.push(20.0 + 3.0 * ti + 245.0 * ti * ti + noise);
        }
        let f = fit_parabola(&t, &y).unwrap();
        let g = 2.0 * f.c;
        assert!((g - 490.0).abs() / 490.0 < 0.01, "g = {g}");
        assert!((f.b - 3.0).abs() < 1.0, "v0 = {}", f.b);
        assert!(f.r2 > 0.9999);
    }

    #[test]
    fn fit_rejects_degenerate_input() {
        assert!(fit_parabola(&[1.0, 1.0, 1.0, 1.0], &[1.0, 2.0, 3.0, 4.0]).is_none());
        assert!(fit_parabola(&[0.0, 1.0], &[0.0, 1.0]).is_none());
    }

    #[test]
    fn centroid_finds_bright_and_dark_blobs() {
        let (w, h) = (10u32, 8u32);
        let mut fr = vec![0u8; (w * h) as usize];
        for y in 2..4 {
            for x in 6..8 {
                fr[(y * w + x) as usize] = 255;
            }
        }
        let (cx, cy, n) = centroid(&fr, w, h, 200, false, (0, 0, w, h)).unwrap();
        assert_eq!(n, 4);
        assert!((cx - 7.0).abs() < 1e-9 && (cy - 3.0).abs() < 1e-9);
        assert!(centroid(&fr, w, h, 200, false, (0, 0, 5, 8)).is_none());
        let inv: Vec<u8> = fr.iter().map(|v| 255 - v).collect();
        assert_eq!(centroid(&inv, w, h, 55, true, (0, 0, w, h)).unwrap().2, 4);
    }

    #[test]
    fn restitution_from_peaks() {
        let e = restitution(&[1.0, 0.64, 0.4096]).unwrap();
        assert!(e.iter().all(|v| (v - 0.8).abs() < 1e-9));
        assert!(restitution(&[1.0]).is_err());
        assert!(restitution(&[1.0, -2.0]).is_err());
    }

    #[test]
    fn rates_and_rois() {
        assert_eq!(parse_rate("30000/1001").map(|v| (v * 1000.0).round()), Some(29970.0));
        assert_eq!(parse_rate("0/0"), None);
        assert!(parse_roi("1,2,3").is_err());
        assert!(parse_roi("1,2,0,4").is_err());
    }
}
