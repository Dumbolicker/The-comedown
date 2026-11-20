# Notes for AI agents in this repository

## Unity in the GitHub Codespace (`.devcontainer/`)

These apply when you run inside the codespace (the environment variable `CODESPACES` is `true`).

- The codespace has a desktop in a browser tab (noVNC on port 6080; `bt-desktop` prints its link), Unity Hub,
  Firefox, the Unity CLI (`unity`) and Claude Code. Guide for people: `.devcontainer/README.md`.
- Unity's sign-in sends the browser back to 127.0.0.1 on the machine that started it. Sign the Unity CLI in with
  `bt-unity-sign-in`, which opens the page in Firefox on the desktop, and tell the user to finish it in the desktop
  tab. A plain `unity auth login` from a codespace terminal opens the user's own browser tab, and the return can't
  reach the codespace.
- The Unity project is `unity/BorrowedTime` (Unity 6000.3.8f1, Built-in Render Pipeline; the world is built from code,
  see `unity/README.md`). `bt-unity-editor` installs that editor version and opens the project on the desktop.
- The cloud builds (`.github/workflows/unity-build.yml`) need the `UNITY_LICENSE`, `UNITY_EMAIL` and `UNITY_PASSWORD`
  secrets; `bt-license-to-github` sets them from the user's own terminal. Never read, print or commit a license file or
  a password.
