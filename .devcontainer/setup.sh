#!/usr/bin/env bash
# Runs once when the codespace is created (postCreateCommand). Safe to run again by hand: bash .devcontainer/setup.sh
#
# Installs, from each vendor's own signed apt repository:
#   - Unity Hub (hub.unity3d.com), the steps in Unity's "Install the Unity Hub on Linux" guide
#   - Firefox (packages.mozilla.org): Ubuntu's own Firefox is a snap, and snaps can't run in a codespace
# Then sets the desktop up: Firefox opens web links, Unity Hub opens unityhub:// sign-in links, a keyring holds Hub's
# sign-in, and the desktop menu gets the Borrowed Time entries. Finally it starts Unity Hub on the desktop.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
say() { printf '\n== %s\n' "$*"; }

MOZILLA_KEY_FPR=35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3   # from Mozilla's "Install Firefox .deb package" instructions

say "Adding Unity's and Mozilla's apt repositories"
sudo install -d -m 0755 /usr/share/keyrings /etc/apt/keyrings
curl -fsSL https://hub.unity3d.com/linux/keys/public | gpg --dearmor | sudo tee /usr/share/keyrings/Unity_Technologies_ApS.gpg >/dev/null
echo "Unity Hub signing key: $(gpg --show-keys --with-colons /usr/share/keyrings/Unity_Technologies_ApS.gpg | awk -F: '/^fpr/{print $10; exit}')"
echo "deb [signed-by=/usr/share/keyrings/Unity_Technologies_ApS.gpg] https://hub.unity3d.com/linux/repos/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/unityhub.list >/dev/null

curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg | sudo tee /etc/apt/keyrings/packages.mozilla.org.asc >/dev/null
fpr="$(gpg --show-keys --with-colons /etc/apt/keyrings/packages.mozilla.org.asc | awk -F: '/^fpr/{print $10; exit}')"
if [ "$fpr" != "$MOZILLA_KEY_FPR" ]; then
  echo "Mozilla's signing key has fingerprint $fpr, not $MOZILLA_KEY_FPR. Stopping." >&2
  sudo rm -f /etc/apt/keyrings/packages.mozilla.org.asc; exit 1
fi
echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" \
  | sudo tee /etc/apt/sources.list.d/mozilla.list >/dev/null
printf 'Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000\n' | sudo tee /etc/apt/preferences.d/mozilla >/dev/null

say "Installing Unity Hub, Firefox and what the Unity editor needs to draw without a graphics card"
sudo apt-get update -q
# libgl1-mesa-dri is Mesa's software renderer (llvmpipe); the rest are libraries the Unity editor loads on Linux.
sudo apt-get install -y -q --no-install-recommends \
  unityhub firefox \
  libgl1 libgl1-mesa-dri libglu1-mesa mesa-utils libvulkan1 \
  libgtk-3-0 libnss3 libasound2 libxtst6 libxrandr2 libxcursor1 libxi6 libxinerama1 libcanberra-gtk3-module \
  cpio p7zip-full xz-utils unzip desktop-file-utils
sudo rm -rf /var/lib/apt/lists/*

say "Linking the helper commands"
for f in "$HERE"/bin/*; do sudo ln -sf "$f" "/usr/local/bin/$(basename "$f")"; done

say "Desktop: default browser, the unityhub:// link handler, the menu"
apps="$HOME/.local/share/applications"; mkdir -p "$apps"
cat > "$apps/unityhub-codespace.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Unity Hub
Comment=Sign in to Unity and manage licenses and editors
Exec=/usr/local/bin/unity-hub %U
Icon=unityhub
Terminal=false
Categories=Development;
MimeType=x-scheme-handler/unityhub;
EOF
update-desktop-database "$apps" 2>/dev/null || true
xdg-mime default unityhub-codespace.desktop x-scheme-handler/unityhub
xdg-mime default firefox.desktop x-scheme-handler/http x-scheme-handler/https text/html
xdg-settings set default-web-browser firefox.desktop 2>/dev/null || true

mkdir -p "$HOME/.fluxbox"
cat > "$HOME/.fluxbox/menu" <<EOF
[begin] (  Borrowed Time  )
    [exec] (Unity Hub: sign in, free license) { /usr/local/bin/unity-hub } <>
    [exec] (Send the license to GitHub) { tilix -t "License to GitHub" -e bash -lc 'bt-license-to-github; read -rp "Press Enter to close. "' } <>
    [exec] (Unity editor: install and open the game) { tilix -t "Unity editor" -e bash -lc 'bt-unity-editor; read -rp "Press Enter to close. "' } <>
    [separator]
    [exec] (Web browser) { firefox } <>
    [exec] (Terminal) { tilix -w $ROOT } <>
    [exec] (Files) { nautilus $ROOT } <>
    [submenu] (System) {}
        [exec] (Passwords and Keys) { seahorse } <>
        [exec] (Top Processes) { tilix -t "Top" -e htop } <>
        [exec] (Disk Use) { tilix -t "Disk Use" -e ncdu $HOME } <>
    [end]
    [config] (Configuration)
[end]
EOF

# The first terminal you open shows this once (the devcontainers base image prints this file).
sudo install -d /usr/local/etc/vscode-dev-containers
bash "$HERE/bin/bt-desktop" --print | sudo tee /usr/local/etc/vscode-dev-containers/first-run-notice.txt >/dev/null

say "Starting Unity Hub on the desktop"
if [ -n "${DISPLAY:-}" ] && ! pgrep -f '/opt/unityhub/unityhub' >/dev/null; then
  setsid /usr/local/bin/unity-hub >/tmp/unity-hub.log 2>&1 < /dev/null &
fi

bash "$HERE/bin/bt-desktop" --print
