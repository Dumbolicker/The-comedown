# A free computer in your browser (GitHub Codespaces)

This repository's **codespace** is a Linux computer on GitHub's servers that you open in a browser tab. It has a
desktop with **Unity Hub** and **Firefox** on it, plus the whole project. You don't install anything on your own device.
It works in any browser. A computer, Chromebook or tablet is easiest; a phone works, but the screen is cramped.

Use it for two things:

1. **The one-time Unity license step** for the cloud builds (about 10 minutes). This is the step that needs "a real
   computer": the codespace is that computer.
2. **Optional:** opening the game in the real Unity editor (needs the bigger 4-core machine, and it's slow, because
   there's no graphics card).

## What's free

- Every free GitHub account gets **120 core hours and 15 GB-months of storage a month** for codespaces. A 2-core
  codespace runs about **60 hours** a month on that; a 4-core one about **30 hours**.
  ([GitHub's billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-codespaces))
- **If you haven't added a payment method, GitHub doesn't charge you:** it blocks codespaces once the free allowance is
  used up, until next month. ([GitHub's docs](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage))
  GitHub emails you at 75%, 90% and 100%.
- A codespace stops by itself after 30 minutes without use. A stopped one uses no hours, but its disk still counts
  toward storage, so **delete it when you're done** (github.com/codespaces, the **...** menu, **Delete**).
- The Unity builds on GitHub Actions cost nothing, because this repository is public.

## Get your Unity license into GitHub (one time)

1. **Create the codespace.** Open
   **https://codespaces.new/Dumbolicker/The-comedown/tree/claude/game-refinement-9ofmk8** and press **Create codespace**.
   (Or on the repository page: switch to the `claude/game-refinement-9ofmk8` branch, then **Code**, **Codespaces**,
   **Create codespace on claude/game-refinement-9ofmk8**.) The first start takes about 5 minutes. A terminal shows the
   setup working; wait until it prints the desktop link.
2. **Open the desktop.** In that terminal type `bt-desktop` and press Enter. It opens the desktop in a new tab.
   (Or open the **Ports** tab, find **Desktop**, and click the globe icon.) Unity Hub is already open on it.
3. **Sign in to Unity.** In Unity Hub, click **Sign in**. Firefox opens on the desktop with Unity's sign-in page. Sign
   in, or create a free Unity account there. When Firefox asks whether to open Unity Hub, choose **Open link**. Hub
   now shows you as signed in.
4. **Get the free license.** In Hub: the gear icon (**Preferences**), **Licenses**, **Add**, **Get a free personal
   license**, **Agree**.
5. **Send it to GitHub.** Go back to the codespace tab (the one with the terminal, not the desktop) and run
   `bt-license-to-github`. It:
   - finds the license Hub just saved;
   - asks you to sign in to GitHub with a one-time code (it opens github.com/login/device for you);
   - saves the license as the `UNITY_LICENSE` secret;
   - asks for your Unity email and password, which you type into your own codespace, and saves them as the
     `UNITY_EMAIL` and `UNITY_PASSWORD` secrets;
   - starts the Unity build again so it can use them.
6. **Watch the build** under the repository's **Actions** tab, **Unity build** (20 to 40 minutes the first time). Tell
   Claude when it's finished or failed: Claude can read the build logs and fix what broke.
7. **Delete the codespace**, unless you want the Unity editor (below).

## Open the game in the Unity editor (optional)

- Use a **4-core** codespace. For a new one, choose the machine type under **Change options** (or the **...** menu)
  before creating it. For an existing one: github.com/codespaces, **...**, **Change machine type**.
- Desktop menu, **Unity editor: install and open the game**, or in the terminal: `bt-unity-editor`. It installs the
  editor version the project uses through Unity Hub, opens the project, and opens the game scene; press **Play**.
- The editor download is a few GB and takes about 9 GB of the codespace's disk, which counts toward the 15 GB-months.
- With no graphics card, the editor draws on the processor, so expect a low frame rate. The builds that GitHub makes
  run at normal speed.
- Unity Personal's own terms apply (it's free under Unity's revenue limit).

## On a phone

- Open the codespaces.new link in your browser, not in the GitHub app. If the page looks squashed, switch the browser to
  its desktop site.
- On the desktop tab, the noVNC side panel (the small tab at the left edge) has a keyboard button for typing.

## Keeping it private

- The codespace and its desktop belong to your GitHub account alone. Leave port 6080 **Private** (the default).
- Your Unity password only goes from your codespace into GitHub's encrypted secrets. Don't paste it into a chat, an
  issue or a commit. Claude never sees it.
- The GitHub sign-in that `bt-license-to-github` uses is deleted when it finishes. To cancel it on GitHub's side too:
  github.com, **Settings**, **Applications**, **Authorized OAuth Apps**, **GitHub CLI**, **Revoke**.

## If something goes wrong

- **Signing in doesn't come back to Hub:** on Unity's page in Firefox, click **Open Unity Hub** if it's there, and pick
  **Unity Hub** if Firefox asks which app to use. If nothing happens, close Hub, open it again from the desktop menu
  (bottom-left button, or right-click the desktop), and sign in again.
- **The setup stopped with an error:** run `bash .devcontainer/setup.sh` in the terminal to try again.
- **`bt-license-to-github` says Hub saved `UnityEntitlementLicense.xml` instead:** tell Claude. Don't paste the file.
- **Lost the desktop tab:** run `bt-desktop` again.

## How it's put together

| File | What it does |
| --- | --- |
| `devcontainer.json` | Ubuntu 22.04 (pinned), the desktop (Fluxbox, TigerVNC, noVNC on port 6080) and the GitHub CLI |
| `setup.sh` | Installs Unity Hub from Unity's apt repository and Firefox from Mozilla's, sets which app opens which link, writes the desktop menu, starts Hub |
| `bin/unity-hub` | Starts Hub the way a container needs (no Chromium sandbox, the sign-in kept on the desktop, a keyring for it) |
| `bin/bt-desktop` | Prints and opens the desktop link |
| `bin/bt-license-to-github` | Sends the license, email and password to GitHub's secrets and restarts the build |
| `bin/bt-unity-editor` | Installs the project's Unity version through Hub and opens the project |

`.github/workflows/codespace-check.yml` builds this exact codespace on GitHub's machines whenever it changes, then
runs `tests/codespace_check.sh`: the desktop page, Unity Hub's window, Firefox opening links, the unityhub:// sign-in
handoff, and the editor install, with screenshots.
