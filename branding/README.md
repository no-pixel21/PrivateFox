# Custom icons

Everything in this folder is copied over `browser/branding/privatefox/` in the Firefox source
during `./build.sh prepare`. File names and subfolders must match exactly.

The most important ones:

| File | Used for |
|---|---|
| `default16.png` … `default256.png` | window and taskbar icons (16, 22, 24, 32, 48, 64, 128, 256 px) |
| `firefox.ico` | Windows: program icon |
| `firefox.icns` | macOS: app icon |
| `document.ico` / `document.icns` | icon for .html files |
| `content/about-logo.png`, `content/about-logo@2x.png` | logo in the "About" window |
| `wizWatermark.bmp` (164×314) | Windows installer: welcome and finish page |
| `wizHeader.bmp`, `wizHeaderRTL.bmp` (150×57) | Windows installer: header on the other pages |
| `disk.icns` | macOS: icon of the mounted .dmg |

You'll find the full list after a first `./build.sh fetch prepare` in
`work/firefox-<version>/browser/branding/privatefox/`.
The source drawings are in `assets/` (`privatefox-icon.svg` for 48 px and up, `privatefox-icon-small.svg` for 16–32 px).
Any file you don't provide falls back to the neutral icons of Firefox's "unofficial" template.
