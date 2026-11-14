# Borrowed Time on your phone (installable, works offline)

This folder is the same game as the shareable link, plus three small things that let a phone
install it like an app: `manifest.webmanifest` (name, icon, full screen), `sw.js` (keeps a copy
on the phone so it runs offline) and two icons. It has to be served from a website. Opening
`index.html` straight from the Files app will not install it.

## 1. Put it online for free (GitHub Pages)

1. Sign in at github.com and make a new **public** repository, for example `borrowed-time`.
2. Choose **Add file → Upload files** and upload every file in this folder
   (`index.html`, `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`).
3. Go to **Settings → Pages**. Under "Build and deployment", set Source to
   **Deploy from a branch**, branch **main**, folder **/ (root)**, then **Save**.
4. After a minute or two the page shows your link, like
   `https://YOUR-NAME.github.io/borrowed-time/`.

Any static host works the same way (Netlify, Cloudflare Pages, itch.io as an HTML game).

## 2. Install it

- **iPhone or iPad (Safari):** open the link, tap **Share**, then **Add to Home Screen**.
- **Android (Chrome):** open the link, tap the **⋮** menu, then **Install app** or **Add to Home screen**.

Open it from the new icon. It runs full screen. Turn the phone sideways for the best view.
After the first launch it also works with no signal.

## 3. Updating it

When the game changes, replace `index.html` in the repository and change the first line of `sw.js`
from `borrowed-time-v1` to `borrowed-time-v2` (and so on). Phones pick up the new version the next
time the game is opened online.

## Notes

- Saved settings (your character's look, voice mode, best score) stay on each phone.
- Anyone with the link can play, no Claude account needed, so this is also the easiest way to share it on Discord.
- The two web fonts load once while online and are cached after that. Without them the game falls back to system fonts.
