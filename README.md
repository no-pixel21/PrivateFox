# 🦊 Private Fox

Ein Browser auf Firefox-Basis mit eingebautem Werbe- und Trackerblocker (uBlock Origin)
und einer **Schutzstufe von 0 bis 4**, die du mit einem Klick umschaltest.
Keine Telemetrie, keine Werbung auf der Startseite, keine Datensammlung.

## ⬇️ Herunterladen

### **[→ Neueste Version herunterladen](https://github.com/no-pixel21/PrivateFox/releases/latest)**

Unter „Assets“ die passende Datei wählen:

| System | Datei |
|---|---|
| **Windows** (64 Bit) | `…win64.installer.exe` zum Installieren, oder die `…win64.zip` als portable Version |
| **macOS** (Apple M1/M2/M3/M4) | `…mac.dmg` |

> Für Macs mit Intel-Prozessor gibt es derzeit keine Version.

## Installieren

### Windows

1. Die `.exe` herunterladen und starten.
2. Windows zeigt „Der Computer wurde durch Windows geschützt“, weil Private Fox nicht signiert ist.
   Auf **Weitere Informationen → Trotzdem ausführen** klicken.
3. Den Installer durchklicken, fertig.

Portable Version: Die `.zip` entpacken und im Ordner `privatefox.exe` starten.

### macOS

1. Die `.dmg` öffnen und **Private Fox** in den Ordner **Programme** ziehen.
2. Einmal das Terminal öffnen und diesen Befehl einfügen:
   ```
   xattr -cr "/Applications/Private Fox.app"
   ```
   Ohne diesen Schritt meldet macOS, die App sei „beschädigt“. Sie ist es nicht, nur nicht bei Apple signiert.
3. Private Fox ganz normal starten.

Beim ersten Start lädt Private Fox automatisch uBlock Origin und das deutsche Sprachpaket.
Das dauert ein paar Sekunden.

## Schutzstufe einstellen

Rechts in der Symbolleiste sitzt ein **Schild mit einer Zahl**. Draufklicken, Stufe wählen,
Private Fox startet neu.

| Stufe | Name | Für wen |
|---|---|---|
| 0 | Aus | Nichts wird blockiert (Telemetrie bleibt trotzdem aus). |
| 1 | Ausgewogen | Werbung und Tracker weg, alle Seiten funktionieren. |
| 2 | **Stark** (Standard) | Zusätzlich Schutz vor Malware- und Phishing-Seiten, verschlüsseltes DNS, deine IP bleibt bei Videoanrufen verborgen, Tracking-Anhängsel werden aus Links entfernt. |
| 3 | Extrem | Zusätzlich keine Cookie-Banner, nur verschlüsselte Seiten (HTTPS), Schutz gegen Fingerprinting, Kamera und Mikrofon gesperrt. Manche Seiten zicken. |
| 4 | Paranoid | Blockiert alles, was nicht direkt von der besuchten Seite kommt. Cookies werden beim Beenden gelöscht. Viele Seiten gehen kaputt. |

**Eine Seite funktioniert nicht?** Auf das uBlock-Symbol (rotes Schild) klicken und den großen
blauen Power-Knopf drücken. Dann wird nur diese eine Seite nicht mehr gefiltert.

## Updates

Private Fox aktualisiert sich **nicht von selbst**. Jeden Montag erscheint automatisch eine neue
Version mit den aktuellen Firefox-Sicherheitsupdates. Lade sie regelmäßig herunter und
installiere sie über die alte drüber. Deine Lesezeichen und Einstellungen bleiben erhalten.

**Tipp:** Oben auf dieser Seite auf **Watch → Custom → Releases** klicken. Dann schickt dir
GitHub bei jeder neuen Version eine Benachrichtigung.

---

Selbst etwas ändern oder lokal bauen? → [ENTWICKLUNG.md](ENTWICKLUNG.md)

Private Fox basiert auf Mozilla Firefox und steht wie Firefox unter der Mozilla Public License 2.0.
Private Fox ist kein Produkt von Mozilla.
