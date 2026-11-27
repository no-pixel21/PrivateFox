# Private Fox – Entwicklung

Nur für Leute, die selbst etwas am Browser ändern oder ihn lokal bauen wollen.
Zum Benutzen einfach die fertige Version unter **Releases** herunterladen (siehe [README](README.md)).

## Wie gebaut wird

GitHub Actions (`.github/workflows/build.yml`) baut Private Fox für Windows (x64) und macOS
(Apple Silicon) und veröffentlicht die Dateien als Release. Das passiert:

- bei jeder Änderung am Build-Code auf `main`,
- jeden Montag automatisch (damit Firefox-Sicherheitsupdates reinkommen),
- auf Knopfdruck: **Actions → „Private Fox bauen“ → Run workflow** (optional mit fester Firefox-Version).

Gebaut wird immer die neueste Firefox-Version. Ein Durchlauf dauert mehrere Stunden.

## Was wo steht

```
.github/workflows/build.yml   Cloud-Build für Windows + macOS, Release-Upload
build.sh                      lädt Firefox, ruft prepare_tree.py und mach auf
scripts/prepare_tree.py       baut Private Fox in den Firefox-Quellcode ein
scripts/levels.py             Richtlinien + uBlock-Konfiguration je Stufe
overlay/browser/privatefox/
  privatefox.cfg              Startskript: Einstellungen je Stufe + Schutz-Knopf
  autoconfig.js               sorgt dafür, dass privatefox.cfg geladen wird
  moz.build                   liefert die Dateien mit aus
branding/                     eigene Icons (siehe branding/README.md)
mozconfig                     Build-Optionen (Name, kein Updater, kein Crashreporter)
FIREFOX_VERSION               Firefox-Version für lokale Builds
```

Die Stufen änderst du in `scripts/levels.py` (uBlock-Listen, Filter, Firefox-Richtlinien)
und in `overlay/browser/privatefox/privatefox.cfg` (about:config-Werte).

## So funktionieren die Stufen

Die gewählte Stufe steht als Zahl in der Datei `privatefox-level` im Benutzer-App-Ordner
(Windows: `%APPDATA%\Mozilla\PrivateFox`, macOS: `~/Library/Application Support/PrivateFox`).
Beim Start lesen zwei Stellen diese Zahl:

1. Die **Richtlinien-Engine** von Firefox. Sie ist so gepatcht, dass sie
   `distribution/policies-level<N>.json` statt `policies.json` lädt. Darüber werden uBlock Origin
   installiert und vorkonfiguriert sowie DoH, HTTPS-Only, Cookies und Berechtigungen gesetzt.
2. Das **Startskript** `privatefox.cfg`. Es setzt die passenden about:config-Werte
   und fügt den Schutz-Knopf ein.

Der Firefox-Quellcode liegt nicht im Repo. `build.sh` lädt ihn direkt von Mozilla und prüft die
SHA-512-Prüfsumme. Bricht `prepare` mit „Mozilla hat den Code geändert“ ab, hat sich eine Stelle
im Firefox-Code verschoben, die wir patchen. Die Meldung nennt die Datei.

## Lokal bauen

Rechne mit **mindestens 40 GB freiem Platz** und **16 GB RAM**.

**Windows:** [MozillaBuild](https://ftp.mozilla.org/pub/mozilla/libraries/win32/MozillaBuildSetup-Latest.exe)
installieren, `C:\mozilla-build\start-shell.bat` starten und alle Befehle dort ausführen.
Das Repo muss in einem Pfad **ohne Leerzeichen** liegen, z. B. `C:\src\privatefox`.
Offizielle Anleitung: <https://firefox-source-docs.mozilla.org/setup/windows_build.html>

**macOS:** `xcode-select --install` (falls `bootstrap` meckert: volles Xcode).
Offizielle Anleitung: <https://firefox-source-docs.mozilla.org/setup/macos_build.html>

```bash
git clone https://github.com/no-pixel21/PrivateFox.git
cd PrivateFox
./build.sh all       # laden, einbauen, Werkzeuge, kompilieren, packen → out/
./build.sh run       # frisch gebauten Browser starten
./build.sh update    # auf neueste Firefox-Version springen und neu bauen
./build.sh help      # alle Befehle
```

## Grenzen

- Die Builds sind nicht signiert, deshalb warnen Windows SmartScreen und macOS Gatekeeper.
  Für echte Signaturen braucht es ein Code-Signing-Zertifikat bzw. ein Apple-Developer-Konto.
- „Firefox“ darf nicht im Produktnamen stehen. Icon-Dateinamen wie `firefox.ico` sind nur technisch.
- Gebaut wird die englische Grundversion, Deutsch kommt über das automatisch installierte Sprachpaket.
