#!/usr/bin/env bash
# End-to-end check that refpipe measures motion correctly. Needs ffmpeg and a built refpipe.
#   cargo build --release && ./selftest.sh
# It renders synthetic clips with known physics, then measures them:
#   1. free fall: a square falling at 490 px/s² (9.8 m/s² at 50 px/m) -> track + fit must land within 2%
#   2. bounce: peaks of 1.0, 0.64 and 0.4096 m -> restitution must read 0.800
#   3. license gate: fetch without a valid --license must be refused
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="${REFPIPE:-$HERE/target/release/refpipe}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
fail=0
pass() { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; fail=1; }

# 1. free fall
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "color=c=black:s=320x480:r=60:d=1.2" \
  -f lavfi -i "color=c=white:s=16x16:r=60:d=1.2" \
  -filter_complex "[0][1]overlay=x=152:y='20+245*t*t':eval=frame" \
  -c:v ffv1 "$WORK/fall.mkv"
"$BIN" track "$WORK/fall.mkv" > "$WORK/fall.csv" 2>/dev/null
FIT="$("$BIN" fit "$WORK/fall.csv" --px-per-m 50)"
G=$(awk '/^accel_m_s2/ {print $2}' <<<"$FIT")
R2=$(awk '/^r2/ {print $2}' <<<"$FIT")
ERR=$(awk -v g="$G" 'BEGIN { e=(g-9.8)/9.8*100; if (e<0) e=-e; printf "%.2f", e }')
if awk -v e="$ERR" 'BEGIN { exit !(e < 2) }'; then pass "free fall: measured $G m/s² (expected 9.80, error $ERR%, r² $R2)"; else bad "free fall: measured $G m/s² (expected 9.80, error $ERR%)"; fi

# 2. restitution
E=$("$BIN" bounce 1.0 0.64 0.4096 | awk '/^e_mean/ {print $2}')
[ "$E" = "0.800" ] && pass "restitution: e = $E (expected 0.800)" || bad "restitution: e = $E (expected 0.800)"

# 3. sheets and motion produce output
( cd "$WORK" && "$BIN" sheet fall.mkv --fps 10 --cols 4 --rows 3 >/dev/null 2>&1 )
SHEETS=$(find "$WORK/.refcache/sheets" -name 'sheet_*.png' | wc -l)
[ "$SHEETS" -ge 1 ] && pass "contact sheets: $SHEETS written" || bad "contact sheets: none written"
ROWS=$("$BIN" motion "$WORK/fall.mkv" 2>/dev/null | tail -n +2 | wc -l)
[ "$ROWS" -ge 60 ] && pass "motion scores: $ROWS frames" || bad "motion scores: only $ROWS frames"

# 4. license gate
if "$BIN" fetch https://example.com/clip.mp4 --note test >/dev/null 2>&1; then bad "fetch without --license was allowed"; else pass "fetch without --license refused"; fi
if "$BIN" fetch https://example.com/clip.mp4 --license whatever --note test >/dev/null 2>&1; then bad "fetch with an unknown license was allowed"; else pass "fetch with an unknown license refused"; fi

exit $fail
