# Private Fox – Development

Only for people who want to change the browser or build it locally.
To just use it, download the finished version from **Releases** (see the [README](README.md)).

## How it's built

GitHub Actions (`.github/workflows/build.yml`) builds Private Fox for Windows (x64) and macOS
(Apple Silicon) and publishes the files as a release. This happens:

- on every change to the build code on `main`,
- automatically every Monday (to pick up Firefox security updates),
- on demand: **Actions → "Build Private Fox" → Run workflow** (optionally with a fixed Firefox version).

It always builds the latest Firefox release. A run takes several hours.

## Repository layout

```
.github/workflows/build.yml   cloud build for Windows + macOS, release upload
build.sh                      downloads Firefox, runs prepare_tree.py and mach
scripts/prepare_tree.py       applies Private Fox to the Firefox source tree
scripts/levels.py             policies + uBlock configuration per level
overlay/browser/privatefox/
  privatefox.cfg              startup script: prefs per level + shield button
  autoconfig.js               makes Firefox load privatefox.cfg
  moz.build                   ships the files with the build
branding/                     custom icons (see branding/README.md)
mozconfig                     build options (name, no updater, no crash reporter)
FIREFOX_VERSION               Firefox version for local builds
```

To change what a level does, edit `scripts/levels.py` (uBlock lists, filters, Firefox policies)
and `overlay/browser/privatefox/privatefox.cfg` (about:config values).

## How the levels work

The selected level is stored as a number in the file `privatefox-level` in the user app folder
(Windows: `%APPDATA%\Mozilla\PrivateFox`, macOS: `~/Library/Application Support/PrivateFox`).
Two places read it on startup:

1. Firefox's **policy engine**, patched to load `distribution/policies-level<N>.json`
   instead of `policies.json`. This installs and configures uBlock Origin and sets DoH,
   HTTPS-Only, cookie behavior and permissions.
2. The **startup script** `privatefox.cfg`. It sets the matching about:config values
   and adds the shield button.

The Firefox source code is not part of this repo. `build.sh` downloads it straight from Mozilla
and verifies the SHA-512 checksum. If `prepare` aborts with "Mozilla changed the code", a spot
in the Firefox source that we patch has moved. The message names the file.

## Building locally

Plan for **at least 40 GB of free disk space** and **16 GB of RAM**.

**Windows:** install [MozillaBuild](https://ftp.mozilla.org/pub/mozilla/libraries/win32/MozillaBuildSetup-Latest.exe),
start `C:\mozilla-build\start-shell.bat` and run all commands in that window.
The repo must be in a path **without spaces**, e.g. `C:\src\privatefox`.
Official guide: <https://firefox-source-docs.mozilla.org/setup/windows_build.html>

**macOS:** `xcode-select --install` (if `bootstrap` complains, install full Xcode).
Official guide: <https://firefox-source-docs.mozilla.org/setup/macos_build.html>

```bash
git clone https://github.com/no-pixel21/PrivateFox.git
cd PrivateFox
./build.sh all       # download, prepare, toolchains, compile, package → out/
./build.sh run       # start the freshly built browser
./build.sh update    # jump to the latest Firefox version and rebuild
./build.sh help      # all commands
```

## Limitations

- Builds are not code-signed, so Windows SmartScreen and macOS Gatekeeper show warnings.
  Real signing requires a code-signing certificate or an Apple Developer account.
- "Firefox" must not appear in the product name (Mozilla trademark). Icon file names like
  `firefox.ico` are purely technical.
- The build is English (en-US). Other languages can be added via language packs.
