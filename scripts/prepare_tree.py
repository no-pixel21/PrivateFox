#!/usr/bin/env python3
"""Private Fox – applies our changes to a fresh Firefox source tree.

Every step checks whether it has already been done, so the script can run any number of times.
If it can't find a spot in the Firefox code (because Mozilla refactored something), it stops
with a clear message instead of silently building something wrong.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from levels import build_policies  # noqa: E402

MARK = "Private Fox"
LEVEL_COUNT = 5

_TARGETS = {"win": "win64", "mac": "mac", "linux": "linux64"}
if os.environ.get("PF_TARGET") in _TARGETS:
    PLATFORM = _TARGETS[os.environ["PF_TARGET"]]
elif sys.platform.startswith("win") or sys.platform in ("cygwin", "msys"):
    PLATFORM = "win64"
elif sys.platform == "darwin":
    PLATFORM = "mac"
else:
    PLATFORM = "linux64"
CROSS_MAC = PLATFORM == "mac" and sys.platform != "darwin"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    print(f"  · {msg}")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ 1. Own files


def install_overlay(src: Path, repo: Path, version: str) -> None:
    target = src / "browser" / "privatefox"
    target.mkdir(parents=True, exist_ok=True)
    for f in (repo / "overlay" / "browser" / "privatefox").iterdir():
        if f.is_file():
            shutil.copy2(f, target / f.name)
    for level in range(LEVEL_COUNT):
        data = build_policies(level, version, PLATFORM)
        write(target / f"policies-level{level}.json", json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    info("Copied own files + 5 policy files to browser/privatefox")


def register_dir(src: Path) -> None:
    mb = src / "browser" / "moz.build"
    if not mb.exists():
        die(f"{mb} not found")
    text = read(mb)
    if '"privatefox"' in text:
        info("browser/moz.build: already registered")
        return
    text += f'\n# {MARK}\nDIRS += ["privatefox"]\n'
    write(mb, text)
    info("browser/moz.build: registered privatefox directory")


def extend_package_manifest(src: Path) -> None:
    pm = src / "browser" / "installer" / "package-manifest.in"
    if not pm.exists():
        die(f"{pm} not found")
    text = read(pm)
    if f"; {MARK}" in text:
        info("package-manifest.in: already extended")
        return
    lines = [f"\n; {MARK}"]
    lines += [f"@RESPATH@/distribution/policies-level{n}.json" for n in range(LEVEL_COUNT)]
    lines += ["@RESPATH@/privatefox.cfg", ""]
    write(pm, text + "\n".join(lines))
    info("package-manifest.in: added files for the installer")


AUTOCONFIG_MARK = "// Private Fox: load privatefox.cfg"
AUTOCONFIG_PREFS = f"""
{AUTOCONFIG_MARK} on startup (with full privileges)
pref("general.config.filename", "privatefox.cfg");
pref("general.config.obscure_value", 0);
pref("general.config.sandbox_enabled", false);
"""


def add_autoconfig_prefs(src: Path) -> None:
    # Appended to Firefox's own GRE default prefs instead of shipping a separate
    # defaults/pref/autoconfig.js: that file is always packaged and loaded early.
    # Must be a GRE default pref file (greprefs.js in omni.ja): autoconfig ignores
    # general.config.filename when it only comes from the app's firefox.js.
    candidates = [
        src / "modules" / "libpref" / "init" / "all.js",
    ]
    for f in candidates:
        if f.exists():
            text = read(f)
            if AUTOCONFIG_MARK in text:
                info(f"Autoconfig prefs: already in {f.relative_to(src)}")
                return
            write(f, text.rstrip("\n") + "\n" + AUTOCONFIG_PREFS)
            info(f"Autoconfig prefs: appended to {f.relative_to(src)}")
            return
    die("modules/libpref/init/all.js not found. "
        "Mozilla moved the default prefs; update add_autoconfig_prefs in scripts/prepare_tree.py.")


# ------------------------------------------------------------------ 2. Policies per level

POLICY_NEEDLE = 'const POLICIES_FILENAME = "policies.json";'
POLICY_MARK = "Private Fox: load the policies file"
POLICY_PATCH = """// Private Fox: load the policies file for the selected protection level.
// The level is stored in <user app folder>/privatefox-level (0–4, default 2).
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
        die(f"{f} not found – Mozilla moved the policy engine. The patch needs updating.")
    text = read(f)
    if POLICY_MARK in text:
        info("Policy engine: already patched")
        return
    if POLICY_NEEDLE not in text:
        die(
            "EnterprisePoliciesParent.sys.mjs no longer contains the line\n"
            f"    {POLICY_NEEDLE}\n"
            "Mozilla changed the code. Look at the file and update POLICY_NEEDLE in "
            "scripts/prepare_tree.py."
        )
    write(f, text.replace(POLICY_NEEDLE, POLICY_PATCH, 1))
    info("Policy engine: now loads policies-level<N>.json")


# ------------------------------------------------------------------ 2b. Update signing certificate

UPDATER_CERTS = [
    "release_primary.der",
    "release_secondary.der",
    "nightly_aurora_level3_primary.der",
    "nightly_aurora_level3_secondary.der",
    "dep1.der",
    "dep2.der",
]


def install_update_cert(src: Path, repo: Path) -> None:
    cert = repo / "update-signing" / "privatefox-update.der"
    if not cert.exists():
        info("Update certificate: update-signing/privatefox-update.der missing – "
             "automatic updates will NOT verify (run scripts/make-update-key.sh)")
        return
    d = src / "toolkit" / "mozapps" / "update" / "updater"
    if not d.is_dir():
        die(f"{d} not found – Mozilla moved the updater. Update install_update_cert.")
    replaced = 0
    for name in UPDATER_CERTS:
        target = d / name
        if target.exists():
            shutil.copy2(cert, target)
            replaced += 1
    if not replaced:
        die(f"No known updater certificates found in {d}. Update UPDATER_CERTS.")
    info(f"Update certificate: replaced {replaced} Mozilla certificate(s) with ours")


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
        info("Branding: copied 'unofficial' template")

    # configure.sh: display name + macOS bundle ID
    cfg = dst / "configure.sh"
    text = read(cfg) if cfg.exists() else ""
    text = re.sub(r"^MOZ_APP_DISPLAYNAME=.*$\n?", "", text, flags=re.M)
    text = re.sub(r"^MOZ_MACBUNDLE_ID=.*$\n?", "", text, flags=re.M)
    text = text.rstrip("\n") + '\nMOZ_APP_DISPLAYNAME="Private Fox"\nMOZ_MACBUNDLE_ID=privatefox\n'
    write(cfg, text)

    # Brand names in all branding locale files
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

    # Copy custom icons from branding/ in the repo on top (same file names as the template)
    own = [p for p in (repo / "branding").rglob("*") if p.is_file() and p.name != "README.md"]
    for p in own:
        rel = p.relative_to(repo / "branding")
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst / rel)
    info(f"Branding: name set to 'Private Fox', {len(own)} custom file(s) applied")


# ------------------------------------------------------------------ 4. mozconfig


def copy_mozconfig(src: Path, repo: Path) -> None:
    text = read(repo / "mozconfig")
    if CROSS_MAC:
        # Same as Mozilla's own macOS builds: cross-compile on Linux. --enable-bootstrap lets
        # configure download the macOS SDK and the DMG tools from Mozilla's toolchain archive.
        text += (
            "\n# Private Fox: cross-compile the macOS (Apple Silicon) version on Linux\n"
            "ac_add_options --target=aarch64-apple-darwin\n"
            "ac_add_options --enable-bootstrap\n"
        )
    write(src / "mozconfig", text)
    info("Copied mozconfig" + (" (cross-compiling for macOS)" if CROSS_MAC else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--version", required=True)
    a = ap.parse_args()

    src, repo = a.src.resolve(), a.repo.resolve()
    if not (src / "mach").exists():
        die(f"{src} doesn't look like a Firefox source tree (mach is missing)")

    install_overlay(src, repo, a.version)
    register_dir(src)
    extend_package_manifest(src)
    add_autoconfig_prefs(src)
    patch_policies_loader(src)
    install_update_cert(src, repo)
    setup_branding(src, repo)
    copy_mozconfig(src, repo)
    print("Private Fox applied.")


if __name__ == "__main__":
    main()
