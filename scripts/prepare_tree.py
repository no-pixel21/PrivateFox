#!/usr/bin/env python3
"""Private Fox – baut die eigenen Änderungen in einen frischen Firefox-Quellcode ein.

Jeder Schritt prüft, ob er schon erledigt ist. Das Skript kann also beliebig oft laufen.
Findet es eine Stelle im Firefox-Code nicht (weil Mozilla etwas umgebaut hat), bricht es
mit einer klaren Meldung ab, statt still etwas Falsches zu bauen.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from levels import build_policies  # noqa: E402

MARK = "Private Fox"
LEVEL_COUNT = 5


def die(msg: str) -> None:
    print(f"FEHLER: {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    print(f"  · {msg}")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ 1. Eigene Dateien


def install_overlay(src: Path, repo: Path, version: str) -> None:
    target = src / "browser" / "privatefox"
    target.mkdir(parents=True, exist_ok=True)
    for f in (repo / "overlay" / "browser" / "privatefox").iterdir():
        if f.is_file():
            shutil.copy2(f, target / f.name)
    for level in range(LEVEL_COUNT):
        data = build_policies(level, version)
        write(target / f"policies-level{level}.json", json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    info("Eigene Dateien + 5 Richtlinien-Dateien nach browser/privatefox kopiert")


def register_dir(src: Path) -> None:
    mb = src / "browser" / "moz.build"
    if not mb.exists():
        die(f"{mb} nicht gefunden")
    text = read(mb)
    if '"privatefox"' in text:
        info("browser/moz.build: schon eingetragen")
        return
    text += f'\n# {MARK}\nDIRS += ["privatefox"]\n'
    write(mb, text)
    info("browser/moz.build: Ordner privatefox eingetragen")


def extend_package_manifest(src: Path) -> None:
    pm = src / "browser" / "installer" / "package-manifest.in"
    if not pm.exists():
        die(f"{pm} nicht gefunden")
    text = read(pm)
    if f"; {MARK}" in text:
        info("package-manifest.in: schon erweitert")
        return
    lines = [f"\n; {MARK}"]
    lines += [f"@RESPATH@/distribution/policies-level{n}.json" for n in range(LEVEL_COUNT)]
    lines += ["@RESPATH@/defaults/pref/autoconfig.js", "@RESPATH@/privatefox.cfg", ""]
    write(pm, text + "\n".join(lines))
    info("package-manifest.in: Dateien für den Installer eingetragen")


# ------------------------------------------------------------------ 2. Richtlinien je Stufe

POLICY_NEEDLE = 'const POLICIES_FILENAME = "policies.json";'
POLICY_PATCH = """// Private Fox: Richtlinien-Datei je nach gewählter Schutzstufe laden.
// Die Stufe steht in <Benutzer-App-Ordner>/privatefox-level (0–4, Standard 2).
const POLICIES_FILENAME = (() => {
  try {
    const file = Services.dirsvc.get("UAppData", Ci.nsIFile);
    file.append("privatefox-level");
    let level = 2;
    if (file.exists()) {
      const fis = Cc["@mozilla.org/network/file-input-stream;1"].createInstance(
        Ci.nsIFileInputStream
      );
      fis.init(file, -1, 0, 0);
      const sis = Cc["@mozilla.org/scriptableinputstream;1"].createInstance(
        Ci.nsIScriptableInputStream
      );
      sis.init(fis);
      const n = parseInt(sis.read(16), 10);
      sis.close();
      fis.close();
      if (n >= 0 && n <= 4) {
        level = n;
      }
    }
    return `policies-level${level}.json`;
  } catch (e) {
    return "policies-level2.json";
  }
})();"""


def patch_policies_loader(src: Path) -> None:
    f = src / "toolkit" / "components" / "enterprisepolicies" / "EnterprisePoliciesParent.sys.mjs"
    if not f.exists():
        die(f"{f} nicht gefunden – Mozilla hat die Richtlinien-Engine verschoben. Patch anpassen.")
    text = read(f)
    if "Private Fox: Richtlinien-Datei" in text:
        info("Richtlinien-Engine: schon gepatcht")
        return
    if POLICY_NEEDLE not in text:
        die(
            "In EnterprisePoliciesParent.sys.mjs fehlt die Zeile\n"
            f"    {POLICY_NEEDLE}\n"
            "Mozilla hat den Code geändert. Bitte die Datei ansehen und POLICY_NEEDLE in "
            "scripts/prepare_tree.py anpassen."
        )
    write(f, text.replace(POLICY_NEEDLE, POLICY_PATCH, 1))
    info("Richtlinien-Engine: lädt jetzt policies-level<N>.json")


# ------------------------------------------------------------------ 3. Branding

BRAND = {
    "shorter": "Private Fox",
    "short": "Private Fox",
    "full": "Private Fox",
    "product": "Private Fox",
}


def setup_branding(src: Path, repo: Path) -> None:
    base = src / "browser" / "branding"
    dst = base / "privatefox"
    if not dst.exists():
        shutil.copytree(base / "unofficial", dst)
        info("Branding: Vorlage 'unofficial' kopiert")

    # configure.sh: Anzeigename + macOS-Bundle-ID
    cfg = dst / "configure.sh"
    text = read(cfg) if cfg.exists() else ""
    text = re.sub(r"^MOZ_APP_DISPLAYNAME=.*$\n?", "", text, flags=re.M)
    text = re.sub(r"^MOZ_MACBUNDLE_ID=.*$\n?", "", text, flags=re.M)
    text = text.rstrip("\n") + '\nMOZ_APP_DISPLAYNAME="Private Fox"\nMOZ_MACBUNDLE_ID=privatefox\n'
    write(cfg, text)

    # Markennamen in allen Sprachdateien des Brandings
    for ftl in dst.rglob("brand.ftl"):
        t = read(ftl)
        for key, val in BRAND.items():
            t = re.sub(rf"^(-brand-{key}-name\s*=).*$", rf"\1 {val}", t, flags=re.M)
        write(ftl, t)
    for props in dst.rglob("brand.properties"):
        t = read(props)
        t = re.sub(r"^(brandShorterName\s*=).*$", r"\1Private Fox", t, flags=re.M)
        t = re.sub(r"^(brandShortName\s*=).*$", r"\1Private Fox", t, flags=re.M)
        t = re.sub(r"^(brandFullName\s*=).*$", r"\1Private Fox", t, flags=re.M)
        write(props, t)

    # Eigene Icons aus branding/ im Repo drüberkopieren (gleiche Dateinamen wie in der Vorlage)
    own = [p for p in (repo / "branding").rglob("*") if p.is_file() and p.name != "README.md"]
    for p in own:
        rel = p.relative_to(repo / "branding")
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst / rel)
    info(f"Branding: Name 'Private Fox' gesetzt, {len(own)} eigene Datei(en) übernommen")


# ------------------------------------------------------------------ 4. mozconfig


def copy_mozconfig(src: Path, repo: Path) -> None:
    shutil.copy2(repo / "mozconfig", src / "mozconfig")
    info("mozconfig kopiert")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()

    src, repo = a.src.resolve(), a.repo.resolve()
    if not (src / "mach").exists():
        die(f"{src} sieht nicht wie ein Firefox-Quellcode aus (mach fehlt)")

    install_overlay(src, repo, a.version)
    register_dir(src)
    extend_package_manifest(src)
    patch_policies_loader(src)
    setup_branding(src, repo)
    copy_mozconfig(src, repo)
    print("Private Fox ist eingebaut.")


if __name__ == "__main__":
    main()
