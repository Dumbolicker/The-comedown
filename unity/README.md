# Borrowed Time in Unity

This folder is the Unity 6 version of Borrowed Time (editor version 6000.3.8f1, Built-in Render Pipeline). It's a playable slice of one street:

- 8 walk-in houses with breakable walls, windows and roofs. Damage is ½·m·v² from whatever hits them, and a support graph decides what falls once its supports are gone.
- Rubble with real Unity physics.
- A third-person character who walks, sprints, double jumps and tackles.
- The draining clock, plus stashes that buy you time.
- First person (X, or scroll all the way in) with a crosshair. Look at a thing and it names its two verbs: rummage a trash can, sit on or search a couch, flip a table, open the fridge, honk a car or try its door, smash a crate into planks, knock on or punch a window, punch a wall. Pick up light things, put them down or throw them where you look. Everything works in third person too, within reach of you.

The web version in `game/` is still the full game. It's also the version that opens from a link on phones and Discord. The Unity version catches up milestone by milestone, following `ROADMAP.md`.

Everything is built from code. There are no hand-made scenes or assets to lose. `Assets/Editor/CiBuild.cs` creates the materials and the empty boot scene, and `Assets/Scripts/Game.cs` builds the world when the game starts.

## Get builds without installing anything (GitHub Actions)

`.github/workflows/unity-build.yml` builds a **WebGL** version and a **Windows** version on GitHub's machines whenever something under `unity/` changes. You can also start it by hand from the Actions tab.

The workflow uses your free Unity Personal license. Unity has to see that license once, so the build needs three repository secrets.

### One-time setup (about 10 minutes, needs a computer)

**No computer?** Use the free codespace instead: a Linux desktop in a browser tab with Unity Hub on it, which does steps 1 to 4 for you. Steps: [`.devcontainer/README.md`](../.devcontainer/README.md).

1. On any Windows, Mac or Linux computer, install **Unity Hub**. Sign in with your Unity account and add a **Personal** license (Hub: Preferences → Licenses → Add → Get a free personal license). You don't have to install the editor.
2. Find the license file Hub just wrote:
   - Windows: `C:\ProgramData\Unity\Unity_lic.ulf`
   - macOS: `/Library/Application Support/Unity/Unity_lic.ulf`
   - Linux: `~/.local/share/unity3d/Unity/Unity_lic.ulf`
3. On GitHub, open the repository's **Settings → Secrets and variables → Actions → New repository secret** and add:

   | Name | Value |
   | --- | --- |
   | `UNITY_LICENSE` | The whole contents of `Unity_lic.ulf`, opened in a text editor |
   | `UNITY_EMAIL` | The email you sign in to Unity with |
   | `UNITY_PASSWORD` | Your Unity password |

   You can add secrets from the GitHub website on a phone too. Only the `.ulf` file needs the computer.
4. Open **Actions → Unity build → Run workflow**. The first build takes 20 to 40 minutes, because it downloads the Unity image and imports the project. Later builds are faster, since the Library folder is cached.
5. When it finishes, download **BorrowedTime-WebGL** or **BorrowedTime-StandaloneWindows64** from the run's Artifacts section.
6. Builds on `main` also go on the web: the Pages workflow publishes the newest WebGL build at https://dumbolicker.github.io/The-comedown/unity/ (a placeholder page until the first one exists). Open it on a computer browser; Unity's WebGL runs on phones but isn't made for them.

Secrets stay encrypted inside GitHub. The workflow passes them only to the pinned GameCI builder (`game-ci/unity-builder` v4.8.2, pinned by commit). Never paste them into a chat, an issue or a commit.

Without the secrets, the workflow still runs. It skips the build and leaves a notice telling you which secrets are missing.

GameCI's activation guide: https://game.ci/docs/github/activation. Unity stopped offering manual activation for Personal licenses, which is why the Hub step is needed: https://discussions.unity.com/t/unity-no-longer-supports-manual-activation-of-personal-licenses/926760

## Open it in the Unity editor (optional)

1. In Unity Hub, install editor **6000.3.8f1** with WebGL and Windows Build Support.
2. Choose **Add → Add project from disk** and pick `unity/BorrowedTime`.
3. In the editor, run **Borrowed Time → Prepare Project** once from the menu bar. This creates the materials and `Assets/Scenes/Main.unity`.
4. Open `Assets/Scenes/Main.unity` and press Play.

## Controls

| Action | Keys |
| --- | --- |
| Move | WASD |
| Look | Mouse (click to capture it, Esc to let go) |
| Sprint | Left Shift |
| Jump, double jump | Space |
| Tackle (or throw what you hold) | F or left click |
| Use what you look at | E (main verb), G or right-click (the other one) |
| Holding something | E puts it down, G or click throws it |
| First person | X, or scroll all the way in (scroll out to leave) |
| Get up from a couch | E, move or jump |
| Zoom | Mouse wheel |
| Restart | R |

## Checking scripts without Unity

`tests/unity_compile.sh` compiles every script against Unity 6's own API libraries, using Unity's C# compiler. It takes both from GameCI's public editor image, so it needs neither a Unity license nor an install. It reports compile errors with file and line, the same way the editor would.
