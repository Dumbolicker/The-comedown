# Stack choice and release readiness

Read this before choosing or changing an engine, and before any release to Steam, phone stores or Discord. Facts here were checked in November 2026. Re-verify prices and policies on the official pages before relying on them.

## Stack decision table

| Path | Rust share | Phones | Steam | Discord | Effort for an existing web game |
| --- | --- | --- | --- | --- | --- |
| **A. Web build + Rust via WASM** (e.g. Rapier physics) + Tauri shell for desktop | Physics, desktop shell and new systems | Instant through a link or PWA | Through the Tauri shell plus Steamworks | Link embeds; Activities possible | Low. It grows a piece at a time. |
| **B. Bevy (all Rust)** | Everything | Possible but young on iOS/Android | Native, through the `steamworks` crate | No instant link unless a WASM build is also kept | High: a rewrite |
| **C. Unity (C#)** + Rust native plugins | Only the plugins | Mature | Mature | WebGL build possible | High: a rewrite, and mostly not Rust |
| **D. Stay on plain JS** | None | Instant | Through Tauri | Link | None, but it misses the Rust goal |

Default to **A** for a web game that is already working. It keeps the one-link sharing that phones and Discord rely on, and moves the heavy parts into Rust. Reach for B when a native-only feature is needed (heavy simulation, modding, controller-first Steam Deck), and for C only when a requirement can't be met otherwise (for example, a console port with an existing Unity pipeline).

For reference, Goat Simulator 3 is built on Unreal Engine 4 (C++). Knowing a genre leader's stack informs the scale of effort; it is not a reason to copy the game.

## Steam readiness checklist

- [ ] Steamworks partner account plus the Steam Direct fee (reported as $100 per app and returned once the game passes $1,000 in revenue; confirm at partner.steamgames.com)
- [ ] Builds uploaded with SteamPipe; desktop shell signed if possible; a clean install tested on a fresh machine
- [ ] Achievements mapped to in-game feats, plus cloud saves
- [ ] Settings menu (graphics, audio, controls, rebinding), a pause menu, and a save system
- [ ] Controller support through Steam Input, plus the Steam Deck basics: 1280×800, readable text, no keyboard-only steps
- [ ] Store page: capsule art, screenshots, trailer, a mature-content survey answered honestly
- [ ] No trademarked brand names in the game or store listing (swap in parody names)
- [ ] EULA and privacy text; crash and log reporting

## Mobile readiness checklist

- [ ] Touch controls, safe areas, landscape lock, 30+ fps on a mid-range phone, thermal check after 10 minutes
- [ ] PWA: manifest, offline service worker, icons. Installs from a link, with no store review.
- [ ] Android APK/AAB through Tauri 2 mobile or Capacitor. iOS needs an Apple Developer account and App Review.
- [ ] **Content policy risk for drug themes.** Apple's guidelines (1.4.3) don't allow apps that *encourage* consumption of illegal drugs or excessive alcohol. Google Play bars depicting or encouraging drug use by minors, depictions of illicit drug use in store listings, and instructions for making drugs, and it rates drug content through IARC. Satire may still be rejected, so plan for the PWA as the guaranteed phone route and treat store releases as uncertain.

## Discord readiness checklist

- [ ] A hosted HTTPS page (GitHub Pages works) with Open Graph tags (`og:title`, `og:description`, `og:image`) so links unfurl with a preview
- [ ] Optional **Discord Activity**: a web app in an iframe that uses the Embedded App SDK (`@discord/embedded-app-sdk`), registered in the Developer Portal with URL mappings. It can run the web build inside a voice channel. Multiplayer still needs your own netcode or server.
- [ ] Check Discord's content rules for age-restricted themes before listing it publicly

## Sources

- [Steam Direct fee, PC Gamer (2017)](https://www.pcgamer.com/valve-reveals-steam-direct-fee-upcoming-changes-to-the-store)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/Guidelines/) and [2021 update coverage, iClarified](https://www.iclarified.com/79555/apple-updates-app-store-review-guidelines-with-app-tracking-transparency-requirement-more)
- [Google Play content ratings](https://support.google.com/googleplay/answer/6209544?hl=en) and [Google Play developer policy](https://support.google.com/googleplay/android-developer/answer/9878877)
- [Discord Activities overview](https://docs.discord.com/developers/activities/overview) and [Embedded App SDK](https://github.com/discord/embedded-app-sdk)
- [Goat Simulator 3 (engine listed as Unreal Engine 4), Wikipedia mirror](https://wiki.riteme.site/wiki/Goat_Simulator_3)
