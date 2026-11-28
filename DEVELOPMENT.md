# Private Fox – Development

Only for people who want to change the browser or build it locally.
To just use it, download the finished version from **Releases** (see the [README](README.md)).

## How it's built

GitHub Actions (`.github/workflows/build.yml`) builds Private Fox for Windows (x64) and macOS
(Apple Silicon) and publishes the files as a release. This happens:

- on every change to the build code on `main`,
- once a day, but only if Mozilla released a new Firefox version (security fixes reach users within about a day),
- on demand: **Actions → "Build Private Fox" → Run workflow** (optionally with a fixed Firefox version).

It always builds the latest Firefox release. A run takes several hours.

## Repository layout

```
.github/workflows/build.yml   cloud build for Windows + macOS, release upload
build.sh                      downloads Firefox, runs prepare_tree.py and mach
scripts/prepare_tree.py       applies Private Fox to the Firefox source tree
scripts/levels.py             policies + uBlock configuration per level
scripts/sign_mar.py           signs / verifies automatic-update files
scripts/update_info.py        update feed (update.xml) helpers
scripts/make-update-key.sh    creates the update signing key (once)
update-signing/               public certificate of the update key
docs/update/<platform>/       update feed served by GitHub Pages
overlay/browser/privatefox/
  privatefox.cfg              startup script: prefs per level + shield button
  moz.build                   ships the files with the build
branding/                     custom icons (see branding/README.md)
mozconfig                     build options (name, own update channel, no crash reporter)
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
   and adds the shield button. `prepare_tree.py` appends the `general.config.*` prefs that
   load it to Firefox's GRE default prefs (`modules/libpref/init/all.js`).

The Firefox source code is not part of this repo. `build.sh` downloads it straight from Mozilla
and verifies the SHA-512 checksum. If `prepare` aborts with "Mozilla changed the code", a spot
in the Firefox source that we patch has moved. The message names the file.

## Automatic updates

Private Fox uses Firefox's own updater, pointed at our feed instead of Mozilla's:

1. **Build:** `mozconfig` enables the updater (`--enable-update-channel=release`, MAR channel
   `privatefox-release`). `prepare_tree.py` replaces Mozilla's update certificates in
   `toolkit/mozapps/update/updater/` with `update-signing/privatefox-update.der`, and writes
   `AppUpdateURL` into the policies (`https://no-pixel21.github.io/PrivateFox/update/<platform>/update.xml`).
2. **Update file:** after packaging, `./build.sh update-mar` builds the complete update
   (`privatefox-<version>.<platform>.complete.mar`) with Mozilla's `make_full_update.sh`, signs it
   with the private key from `PF_UPDATE_KEY` (`scripts/sign_mar.py`, RSA-4096 / SHA-384) and
   verifies the signature against the certificate.
3. **Feed:** the release job uploads the `.mar` files to the GitHub release and writes
   `docs/update/<platform>/update.xml` (version, build ID, download URL, SHA-512) to `main`,
   which GitHub Pages serves.

Private Fox checks the feed, downloads the update in the background and installs it on the next
restart. It only accepts files signed with our key, and never an older version.

**One-time setup:**

```bash
./scripts/make-update-key.sh
```

Then add the private key as the repository secret `UPDATE_SIGNING_KEY` and commit
`update-signing/privatefox-update.der`. Without the secret, builds still work but produce no
update files. Only builds made *after* the certificate is in the repo can update themselves.

**Keep the private key safe.** Whoever has it can ship updates to every user; losing it means
existing installs can't be updated automatically anymore.

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
