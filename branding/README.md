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

You'll find the full list after a first `./build.sh fetch prepare` in
`work/firefox-<version>/browser/branding/privatefox/`.
As long as this folder is empty, Private Fox uses the neutral icons of Firefox's "unofficial" template.
