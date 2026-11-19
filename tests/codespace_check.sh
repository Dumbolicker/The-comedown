#!/usr/bin/env bash
# Runs inside the codespace's container on GitHub's machines (.github/workflows/codespace-check.yml).
#   bash tests/codespace_check.sh          the desktop, Unity Hub, Firefox and the link handlers, with screenshots
#   bash tests/codespace_check.sh editor   the optional Unity editor install (bt-unity-editor --install)
# Screenshots go to .ci-shots/ and are also printed as base64 between ===SHOT markers, so they can be read from the log.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/.ci-shots"; mkdir -p "$OUT"
export DISPLAY=:1 DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-autolaunch:}"
fails=0
check() { local name="$1"; shift; if "$@" >/tmp/check.out 2>&1; then echo "PASS  $name"; else echo "FAIL  $name"; sed 's/^/      /' /tmp/check.out | tail -n 8; fails=$((fails+1)); fi; }
shot() {
  import -display :1 -window root "$OUT/$1.png" && convert "$OUT/$1.png" -resize 720x -quality 50 "$OUT/$1.jpg" || return
  echo "===SHOT $1 BEGIN"; base64 "$OUT/$1.jpg"; echo "===SHOT $1 END"
}
windows() { xdotool search --onlyvisible --name . 2>/dev/null | while read -r w; do printf '      window: %s\n' "$(xdotool getwindowname "$w" 2>/dev/null)"; done | sort -u | head -n 30; }

if [ "${1:-}" = editor ]; then
  VERSION="$(sed -n 's/^m_EditorVersion: *//p' "$ROOT/unity/BorrowedTime/ProjectSettings/ProjectVersion.txt")"
  df -h "$HOME" | tail -n 1
  check "bt-unity-editor --install puts Unity $VERSION in place" timeout 2400 bt-unity-editor --install
  B="$HOME/Unity/Hub/Editor/$VERSION/Editor/Unity"
  check "the editor finds every library it links to" bash -c "[ -x '$B' ] && ! ldd '$B' | grep 'not found'"
  du -sh "$HOME/Unity/Hub/Editor" 2>/dev/null; df -h "$HOME" | tail -n 1
  echo "editor checks failed: $fails"; exit "$fails"
fi

sudo apt-get update -q >/dev/null && sudo apt-get install -y -q --no-install-recommends imagemagick xdotool >/dev/null   # check-only tools

for _ in $(seq 60); do curl -fsS http://localhost:6080/vnc.html >/dev/null 2>&1 && break; sleep 2; done
check "noVNC serves the desktop page on 6080" bash -c 'curl -fsS http://localhost:6080/vnc.html | grep -qi novnc'
check "the desktop (X display :1) is up" xdpyinfo -display :1
check "Unity Hub is installed" bash -c 'test -x /opt/unityhub/unityhub && dpkg-query -W unityhub'
check "Firefox is Mozilla's deb, not Ubuntu's snap stub" bash -c 'firefox --version && dpkg-query -W -f "\${Version}\n" firefox | grep -vq snap'
check "unityhub:// links open Unity Hub" bash -c '[ "$(xdg-mime query default x-scheme-handler/unityhub)" = unityhub-codespace.desktop ]'
check "web links open Firefox" bash -c '[ "$(xdg-mime query default x-scheme-handler/https)" = firefox.desktop ]'
check "the helper commands are on PATH" bash -c 'command -v unity-hub bt-desktop bt-license-to-github bt-unity-editor gh'
check "bt-desktop prints the desktop link" bash -c 'bt-desktop --print | grep -q "6080/vnc.html"'
check "bt-license-to-github --check says there's no license yet" bash -c '! bt-license-to-github --check && bt-license-to-github --check | grep -q "no Unity license"'
check "the desktop menu has the Unity entries" grep -q 'unity-hub' "$HOME/.fluxbox/menu"
check "Unity Hub's command line answers" bash -c 'timeout 180 unity-hub --headless help 2>&1 | tee /tmp/hub-help.txt | grep -qi install'
head -n 40 /tmp/hub-help.txt | sed 's/^/      hub: /'

pgrep -f /opt/unityhub/unityhub >/dev/null || (setsid unity-hub >/tmp/unity-hub.log 2>&1 </dev/null &)
for _ in $(seq 90); do xdotool search --onlyvisible --name 'Unity Hub' >/dev/null 2>&1 && break; sleep 2; done
check "a Unity Hub window is on the desktop" xdotool search --onlyvisible --name 'Unity Hub'
sleep 20; windows; shot hub

setsid xdg-open https://id.unity.com/ >/dev/null 2>&1 </dev/null &
for _ in $(seq 60); do xdotool search --onlyvisible --class firefox >/dev/null 2>&1 && break; sleep 2; done
check "a web link opens Firefox on the desktop (how Hub's Sign in works)" xdotool search --onlyvisible --class firefox
sleep 25; windows; shot firefox

: > /tmp/unity-hub-links.log
xdg-open 'unityhub://v1/ci-check' >/dev/null 2>&1 || true
sleep 8
check "a unityhub:// link reaches Unity Hub" grep -q 'unityhub://' /tmp/unity-hub-links.log
check "Unity Hub is still running" pgrep -f /opt/unityhub/unityhub
check "the keyring's secret service answers" bash -c 'busctl --user list 2>/dev/null | grep -q org.freedesktop.secrets || dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep -q org.freedesktop.secrets'

if [ "$fails" -gt 0 ]; then
  echo "--- unity-hub.log"; tail -n 40 /tmp/unity-hub.log 2>/dev/null
  echo "--- container-init.log"; tail -n 20 /tmp/container-init.log 2>/dev/null
fi
echo "desktop checks failed: $fails"; exit "$fails"
