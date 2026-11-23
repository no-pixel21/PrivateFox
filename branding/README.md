# Eigene Icons

Alles, was hier liegt, wird beim `./build.sh prepare` über `browser/branding/privatefox/`
im Firefox-Quellcode kopiert. Dateinamen und Unterordner müssen genau wie dort heißen.

Am wichtigsten:

| Datei               | Wofür                              |
|---------------------|------------------------------------|
| `default16.png` … `default256.png` | Fenster- und Taskleisten-Icons (16, 22, 24, 32, 48, 64, 128, 256 px) |
| `firefox.ico`       | Windows: Programm-Icon             |
| `firefox.icns`      | macOS: App-Icon                    |
| `document.ico` / `document.icns` | Icon für .html-Dateien |
| `content/about-logo.png`, `content/about-logo@2x.png` | Logo im „Über“-Fenster |

Die vollständige Liste siehst du nach dem ersten `./build.sh fetch prepare` in
`work/firefox-<version>/browser/branding/privatefox/`.
Solange hier nichts liegt, nutzt Private Fox die neutralen Icons der Firefox-Vorlage „unofficial“.
