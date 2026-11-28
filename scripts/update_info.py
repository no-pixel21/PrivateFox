#!/usr/bin/env python3
"""Private Fox – update feed helpers.

    update_info.py info --mar FILE --app DIR --platform win64 --out info.json
        Collect what the update feed needs about one MAR (version, build ID, size, SHA-512).
        DIR is the packaged app (Windows: the folder with privatefox.exe,
        macOS: "Private Fox.app").

    update_info.py xml --info info.json --mar-url URL --details-url URL --out update.xml
        Write the update.xml that Private Fox fetches from AppUpdateURL.
"""

import argparse
import configparser
import hashlib
import json
import os
import sys
from pathlib import Path
from xml.sax.saxutils import quoteattr


def read_app_ini(app: Path) -> configparser.ConfigParser:
    for cand in (app / "application.ini", app / "Contents" / "Resources" / "application.ini"):
        if cand.exists():
            cp = configparser.ConfigParser(interpolation=None)
            cp.read(cand, encoding="utf-8")
            return cp
    sys.exit(f"ERROR: application.ini not found in {app}")


def cmd_info(a):
    ini = read_app_ini(Path(a.app))
    mar = Path(a.mar)
    sha = hashlib.sha512()
    with open(mar, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    info = {
        "platform": a.platform,
        "version": ini["App"]["Version"],
        "buildID": ini["App"]["BuildID"],
        "mar": mar.name,
        "size": mar.stat().st_size,
        "sha512": sha.hexdigest(),
    }
    Path(a.out).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(info, indent=2))


def cmd_xml(a):
    info = json.loads(Path(a.info).read_text(encoding="utf-8"))
    v = info["version"]
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<updates>\n"
        f'  <update type="minor" displayVersion={quoteattr(v)} appVersion={quoteattr(v)}'
        f' platformVersion={quoteattr(v)} buildID={quoteattr(info["buildID"])}'
        f' detailsURL={quoteattr(a.details_url)}>\n'
        f'    <patch type="complete" URL={quoteattr(a.mar_url)} size="{info["size"]}"'
        f' hashFunction="sha512" hashValue="{info["sha512"]}"/>\n'
        "  </update>\n"
        "</updates>\n"
    )
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    Path(a.out).write_text(xml, encoding="utf-8")
    print(xml)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("info")
    i.add_argument("--mar", required=True)
    i.add_argument("--app", required=True)
    i.add_argument("--platform", required=True)
    i.add_argument("--out", required=True)
    x = sub.add_parser("xml")
    x.add_argument("--info", required=True)
    x.add_argument("--mar-url", required=True)
    x.add_argument("--details-url", required=True)
    x.add_argument("--out", required=True)
    a = ap.parse_args()
    cmd_info(a) if a.cmd == "info" else cmd_xml(a)


if __name__ == "__main__":
    main()
