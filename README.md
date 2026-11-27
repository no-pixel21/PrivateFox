# 🦊 Private Fox

A Firefox-based browser with a built-in ad and tracker blocker (uBlock Origin)
and a **protection level from 0 to 4** that you switch with one click.
No telemetry, no ads on the new tab page, no data collection.

## ⬇️ Download

### **[→ Download the latest version](https://github.com/no-pixel21/PrivateFox/releases/latest)**

Pick the right file under "Assets":

| System | File |
|---|---|
| **Windows** (64-bit) | `…win64.installer.exe` to install, or `…win64.zip` for the portable version |
| **macOS** (Apple M1/M2/M3/M4) | `…mac.dmg` |

> There is currently no build for Intel Macs.

## Installation

### Windows

1. Download the `.exe` and run it.
2. Windows shows "Windows protected your PC" because Private Fox is not code-signed.
   Click **More info → Run anyway**.
3. Click through the installer. Done.

Portable version: unzip the `.zip` and run `privatefox.exe` inside the folder.

### macOS

1. Open the `.dmg` and drag **Private Fox** into your **Applications** folder.
2. Open Terminal once and paste this command:
   ```
   xattr -cr "/Applications/Private Fox.app"
   ```
   Without this step macOS claims the app is "damaged". It isn't, it's just not signed by Apple.
3. Start Private Fox as usual.

On first launch Private Fox automatically installs uBlock Origin. This takes a few seconds.

## Choosing a protection level

There's a **shield with a number** on the right side of the toolbar. Click it, pick a level,
and Private Fox restarts.

| Level | Name | What it does |
|---|---|---|
| 0 | Off | Nothing is blocked (telemetry stays off anyway). |
| 1 | Balanced | Ads and trackers gone, every site works. |
| 2 | **Strong** (default) | Also blocks malware and phishing sites, encrypted DNS, hides your IP in video calls, strips tracking parameters from links. |
| 3 | Extreme | Also removes cookie banners, HTTPS-only, fingerprinting protection, camera and microphone blocked. Some sites may misbehave. |
| 4 | Paranoid | Blocks everything that doesn't come from the site you're visiting. Cookies are deleted on exit. Many sites will break. |

**A site doesn't work?** Click the uBlock icon (red shield) and hit the big blue power button.
That turns filtering off for that one site only.

## Language

Private Fox ships in English. To use another language, install the matching
language pack in Private Fox: `about:addons` → search for e.g. "German language pack",
then pick the language under Settings → Language.

## Updates

Private Fox does **not update itself**. A new version with the latest Firefox security fixes
is published automatically every Monday. Download it regularly and install it over the old one.
Your bookmarks and settings are kept.

**Tip:** Click **Watch → Custom → Releases** at the top of this page and GitHub will notify you
about every new version.

---

Want to change something or build it yourself? → [DEVELOPMENT.md](DEVELOPMENT.md)

Private Fox is based on Mozilla Firefox and, like Firefox, licensed under the Mozilla Public License 2.0.
Private Fox is not a Mozilla product.
