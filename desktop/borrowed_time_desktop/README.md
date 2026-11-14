# Borrowed Time (desktop build)

A small Rust app (Tauri 2) that opens the game in its own window. The game is the same
WebGL page as the shareable link, saved at `dist/index.html`, and gets bundled inside the exe.

## Get the .exe without installing anything (GitHub Actions)

1. Make a new GitHub repository and upload everything in this folder, including the hidden `.github` folder.
2. Open the repository's **Actions** tab, pick **Build Windows exe**, and press **Run workflow**.
3. When it finishes (about 10 minutes the first time), open the run and download **BorrowedTime-windows**.
   Inside are `borrowed-time.exe` (runs on its own) and an installer ending in `-setup.exe`.

## Build it yourself on Windows

1. Install Rust from https://rustup.rs (accept the Visual Studio Build Tools prompt).
2. `cargo install tauri-cli --version "^2.0" --locked`
3. In this folder: `cargo tauri dev` to play right away, or `cargo tauri build` for the exe.
4. Output: `src-tauri\target\release\borrowed-time.exe` and the installer in `src-tauri\target\release\bundle\nsis\`.

## Sending it to friends on Discord

Send `borrowed-time.exe`. It needs Microsoft's WebView2, which ships with Windows 11 and current Windows 10.
Unsigned apps trigger a SmartScreen warning ("More info", then "Run anyway"). Code signing removes it but costs money.

## Steam

The exe is a normal Windows build you can upload with SteamPipe once you have a Steamworks partner account
and pay the Steam Direct fee for the app. Achievements and the Steam overlay are not wired up; that needs the
Steamworks SDK (for example the `steamworks` crate), and the overlay may not draw over WebView2 windows.
Steam also asks for a mature-content disclosure for drug and alcohol references, and real brand names
(Xanax, "Henny") are a trademark risk in a commercial release, so swap in parody names before selling it.

## Hardening before you ship

- Pin the GitHub Actions to commit SHAs instead of version tags.
- Run `cargo audit` and `cargo deny check` on the Rust side.
- The page loads two Google Fonts when online and falls back to system fonts offline.
