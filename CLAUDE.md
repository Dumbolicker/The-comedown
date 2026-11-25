# Notes for AI agents in this repository

## Unity in the GitHub Codespace (`.devcontainer/`)

These apply when you run inside the codespace (the environment variable `CODESPACES` is `true`).

- The codespace has a desktop in a browser tab (noVNC on port 6080; `bt-desktop` prints its link), Unity Hub,
  Firefox, the Unity CLI (`unity`) and Claude Code. Guide for people: `.devcontainer/README.md`.
- Ask the user before signing in to Unity or activating a license, and never handle their Unity password. Sign the
  Unity CLI in with `bt-unity-sign-in`: it unlocks the desktop's keyring, where the CLI saves the sign-in, and opens
  Unity's page in Firefox on the desktop. It also prints a sign-in link the user can open on any device instead; the
  CLI waits until they finish.
- The Unity project is `unity/BorrowedTime` (Unity 6000.3.8f1, Built-in Render Pipeline; the world is built from code,
  see `unity/README.md`). `bt-unity-editor` installs that editor version and opens the project on the desktop.
- The cloud builds (`.github/workflows/unity-build.yml`) need the `UNITY_LICENSE`, `UNITY_EMAIL` and `UNITY_PASSWORD`
  secrets; `bt-license-to-github` sets them from the user's own terminal. Never read, print or commit a license file or
  a password.
