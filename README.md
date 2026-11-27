# 🦊 Private Fox

Ein Firefox-Fork mit fest eingebautem **uBlock Origin**, gehärteten Einstellungen und einer
**Schutzstufe von 0 bis 4**, die man mit einem Klick in der Symbolleiste umschaltet.

Das Repo enthält nur die Änderungen. Den Firefox-Quellcode (mehrere GB) lädt `build.sh`
direkt von Mozilla und prüft dabei die SHA-512-Prüfsumme.

## Die Schutzstufen

| Stufe | Name | Was passiert |
|---|---|---|
| 0 | Aus | uBlock bleibt installiert, filtert aber nichts. Telemetrie ist trotzdem aus. |
| 1 | Ausgewogen | uBlock mit EasyList, EasyPrivacy, EasyList Germany und uBlock-Filtern. Tracking-Schutz „Streng“, Global Privacy Control, keine Pings/Beacons, kein Vorabladen. |
| 2 | **Stark** (Standard) | + Malware-Listen (URLhaus, Peter Lowe) · DNS-over-HTTPS über Quad9 mit Rückfall · WebRTC verrät die IP nicht · Tracking-Parameter werden aus Links entfernt · Referrer an Dritte gekürzt · Punycode sichtbar (gegen Phishing-Domains) · HTTPS bevorzugt |
| 3 | Extrem | + Cookie-Banner- und Ärgernis-Listen · **nur HTTPS** · DoH ohne Rückfall · Fingerprinting-Schutz · kein Referrer an fremde Domains · Schriften/Plugins von Drittanbietern blockiert · Kamera/Mikro/Autoplay blockiert · kein Firefox-Konto, kein Formularverlauf |
| 4 | Paranoid | + **alle Skripte und Frames von Drittanbietern blockiert** · `resistFingerprinting` mit Letterboxing · WebGL und WebRTC aus · nur Cookies der besuchten Seite · Cookies/Cache beim Beenden gelöscht |

**Umschalten:** Schild-Knopf in der Symbolleiste anklicken, Stufe wählen, Private Fox startet neu.
**Seite kaputt?** Im uBlock-Popup den großen Power-Knopf drücken. Dann wird diese Seite nicht
gefiltert. Ab Stufe 3 kannst du dort im erweiterten Modus auch einzelne Drittanbieter erlauben.

Alles Einstellbare steht an zwei Stellen:

- `scripts/levels.py`: uBlock-Listen, uBlock-Filter und Firefox-Richtlinien je Stufe
- `overlay/browser/privatefox/privatefox.cfg`: Browser-Einstellungen je Stufe und der Schutz-Knopf

## Fertig gebaut herunterladen

GitHub baut Private Fox automatisch für Windows (x64) und macOS (Apple Silicon):
bei jeder Änderung am Build-Code, jeden Montag und auf Knopfdruck
(**Actions → „Private Fox bauen“ → Run workflow**). Ein Durchlauf dauert mehrere Stunden.

Die fertigen Dateien liegen danach unter **Releases** (rechts auf der Repo-Startseite):

- **Windows:** `.exe` installieren oder `.zip` entpacken und `privatefox.exe` starten.
  SmartScreen warnt, weil der Build nicht signiert ist: „Weitere Informationen → Trotzdem ausführen“.
- **macOS:** `.dmg` öffnen, Private Fox nach „Programme“ ziehen, dann einmal im Terminal
  `xattr -cr "/Applications/Private Fox.app"` ausführen. Sonst behauptet macOS, die App sei beschädigt.

Selbst bauen musst du nur, wenn du etwas ausprobieren willst, ohne auf GitHub zu warten.

## Voraussetzungen (nur zum Selbstbauen)

Rechne mit **mindestens 40 GB freiem Platz** und **16 GB RAM**. Der erste Build dauert je nach
Rechner 30 Minuten bis mehrere Stunden, spätere gehen schneller.

### Windows

1. **MozillaBuild** installieren: <https://ftp.mozilla.org/pub/mozilla/libraries/win32/MozillaBuild-Setup.exe>
2. `C:\mozilla-build\start-shell.bat` starten. **Alle Befehle laufen in diesem Fenster.**
3. Das Repo in einen Pfad **ohne Leerzeichen** klonen, z. B. `C:\src\privatefox`.
4. Tipp: Den Ordner in Windows Defender als Ausnahme eintragen, das macht den Build deutlich schneller.

Mozillas offizielle Anleitung, falls `bootstrap` etwas vermisst:
<https://firefox-source-docs.mozilla.org/setup/windows_build.html>

### macOS

1. Xcode Command Line Tools: `xcode-select --install`. Falls `bootstrap` meckert, das volle Xcode aus dem App Store installieren.
2. Python 3 ist danach vorhanden (`python3 --version`).

Mozillas offizielle Anleitung: <https://firefox-source-docs.mozilla.org/setup/macos_build.html>

## Bauen

```bash
git clone https://github.com/<dein-name>/privatefox.git
cd privatefox
./build.sh all
```

`all` macht nacheinander: Quellcode laden → Private Fox einbauen → Build-Werkzeuge installieren
→ kompilieren → packen. Die fertigen Pakete landen in `out/`:

- **Windows:** `privatefox-<version>.en-US.win64.zip` (portabel) und ein Installer `.exe`
- **macOS:** `privatefox-<version>.en-US.mac.dmg`

Zum Ausprobieren ohne Packen: `./build.sh run`.

## Aktualisieren – wichtig!

Firefox bekommt alle paar Wochen ein neues Release und dazwischen Sicherheitsupdates.
Private Fox hat **keine automatischen Updates**. Ein alter Build ist ein unsicherer Browser.

```bash
./build.sh update
```

Das trägt die neueste Firefox-Version ein und baut alles neu. Bricht `prepare` mit
„Mozilla hat den Code geändert“ ab, hat sich eine Stelle im Firefox-Code verschoben, die wir patchen.
Die Meldung sagt dir, welche Datei es ist.

## Wie es funktioniert

```
build.sh                  lädt Firefox, ruft prepare_tree.py und mach auf
scripts/prepare_tree.py   baut Private Fox in den Firefox-Quellcode ein
scripts/levels.py         Richtlinien + uBlock-Konfiguration je Stufe
overlay/browser/privatefox/
  privatefox.cfg          Startskript: Einstellungen je Stufe + Schutz-Knopf
  autoconfig.js           sorgt dafür, dass privatefox.cfg geladen wird
  moz.build               liefert die Dateien mit aus
branding/                 eigene Icons (optional)
mozconfig                 Build-Optionen (Name, kein Updater, kein Crashreporter)
```

Die gewählte Stufe steht als Zahl in der Datei `privatefox-level` im Benutzer-App-Ordner
(Windows: `%APPDATA%\Mozilla\PrivateFox`, macOS: `~/Library/Application Support/PrivateFox`).
Beim Start lesen zwei Stellen diese Zahl:

1. Die **Richtlinien-Engine** von Firefox. Sie ist so gepatcht, dass sie
   `distribution/policies-level<N>.json` statt `policies.json` lädt. Darüber werden uBlock Origin
   installiert und vorkonfiguriert sowie DoH, HTTPS-Only, Cookies und Berechtigungen gesetzt.
2. Das **Startskript** `privatefox.cfg`. Es setzt die passenden `about:config`-Werte
   und fügt den Schutz-Knopf ein.

uBlock Origin und das deutsche Sprachpaket werden beim ersten Start automatisch geladen.
Das Sprachpaket kommt passend zur Version direkt von Mozilla.

## Bekannte Grenzen

- **Noch nie gebaut:** Dieses Repo wurde ohne echten Firefox-Build erstellt. Rechne beim ersten
  Durchlauf mit kleinen Anpassungen, vor allem im Branding und bei `package-manifest.in`.
- **Nicht signiert:** macOS-Gatekeeper und Windows SmartScreen warnen. macOS: Rechtsklick → Öffnen.
  Für echte Signaturen brauchst du ein Apple-Developer-Konto bzw. ein Code-Signing-Zertifikat.
- **Name „Firefox“:** Er darf nicht im Produktnamen stehen. Die Dateinamen der Icons
  (`firefox.ico`) sind nur technische Namen und unproblematisch.
- **Sprache:** Gebaut wird die englische Grundversion, Deutsch kommt über das Sprachpaket.
  Falls an einzelnen Stellen „Firefox“ statt „Private Fox“ erscheint, stammt das aus dem Sprachpaket.

## Lizenz

Firefox steht unter der Mozilla Public License 2.0, dieser Fork ebenso.
