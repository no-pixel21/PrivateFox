#!/usr/bin/env bash
# Private Fox – Build-Skript
# Läuft auf macOS (Terminal) und Windows (MozillaBuild-Shell: C:\mozilla-build\start-shell.bat).
#
#   ./build.sh all        Quellcode holen, vorbereiten, Werkzeuge installieren, bauen, packen
#   ./build.sh update     auf neueste Firefox-Version springen und alles neu bauen
#   ./build.sh help       alle Befehle

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${PF_WORK_DIR:-$REPO_DIR/work}"
OUT_DIR="$REPO_DIR/out"
PYTHON="${PYTHON:-python3}"
VERSION="$(tr -d ' \r\n' < "$REPO_DIR/FIREFOX_VERSION")"
SRC_DIR="$WORK_DIR/firefox-$VERSION"
ARCHIVE_URL="https://archive.mozilla.org/pub/firefox/releases/$VERSION"
TARBALL="firefox-$VERSION.source.tar.xz"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mFEHLER:\033[0m %s\n' "$*" >&2; exit 1; }

case "$(uname -s)" in
  Darwin)               PLATFORM=mac ;;
  MINGW*|MSYS*|CYGWIN*) PLATFORM=win ;;
  Linux)                PLATFORM=linux ;;
  *)                    PLATFORM=unknown ;;
esac

need() { command -v "$1" >/dev/null 2>&1 || die "'$1' fehlt. Siehe README → Voraussetzungen."; }

sha512_of() {
  if command -v sha512sum >/dev/null 2>&1; then
    sha512sum "$1" | awk '{print $1}'
  else
    shasum -a 512 "$1" | awk '{print $1}'
  fi
}

check_paths() {
  [[ "$WORK_DIR" != *" "* ]] || die "Der Arbeitsordner enthält Leerzeichen: $WORK_DIR
Firefox lässt sich so nicht bauen. Repo nach z. B. C:/src/privatefox bzw. ~/src/privatefox verschieben
oder PF_WORK_DIR auf einen Pfad ohne Leerzeichen setzen."
}

need_src() {
  [[ -d "$SRC_DIR" ]] || die "Kein Quellcode für $VERSION gefunden. Erst './build.sh fetch' ausführen."
}

mach() {
  need_src
  (cd "$SRC_DIR" && ./mach "$@")
}

# ---------------------------------------------------------------- Befehle

cmd_latest() {
  need curl
  info "Frage neueste Firefox-Version bei Mozilla ab …"
  local latest
  latest="$(curl -fsSL https://product-details.mozilla.org/1.0/firefox_versions.json \
    | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["LATEST_FIREFOX_VERSION"])')"
  [[ -n "$latest" ]] || die "Version konnte nicht ermittelt werden."
  if [[ "$latest" == "$VERSION" ]]; then
    info "Schon aktuell: $VERSION"
  else
    echo "$latest" > "$REPO_DIR/FIREFOX_VERSION"
    info "FIREFOX_VERSION: $VERSION → $latest"
  fi
}

cmd_fetch() {
  need curl; need tar; check_paths
  mkdir -p "$WORK_DIR"
  if [[ -d "$SRC_DIR" ]]; then
    info "Quellcode für $VERSION ist schon entpackt: $SRC_DIR"
    return
  fi

  if [[ ! -f "$WORK_DIR/$TARBALL" ]]; then
    info "Lade Firefox $VERSION Quellcode (ca. 600 MB) …"
    curl -fL --retry 3 -o "$WORK_DIR/$TARBALL.part" "$ARCHIVE_URL/source/$TARBALL"
    mv "$WORK_DIR/$TARBALL.part" "$WORK_DIR/$TARBALL"
  fi

  info "Prüfe SHA-512-Prüfsumme …"
  curl -fsSL -o "$WORK_DIR/SHA512SUMS-$VERSION" "$ARCHIVE_URL/SHA512SUMS"
  local expected actual
  expected="$(awk -v f="source/$TARBALL" '$2 == f {print $1}' "$WORK_DIR/SHA512SUMS-$VERSION")"
  [[ -n "$expected" ]] || die "Keine Prüfsumme für $TARBALL in SHA512SUMS gefunden."
  actual="$(sha512_of "$WORK_DIR/$TARBALL")"
  if [[ "$expected" != "$actual" ]]; then
    rm -f "$WORK_DIR/$TARBALL"
    die "Prüfsumme stimmt NICHT. Download gelöscht, bitte erneut versuchen."
  fi
  info "Prüfsumme ok."

  info "Entpacke (dauert ein paar Minuten) …"
  tar -xJf "$WORK_DIR/$TARBALL" -C "$WORK_DIR"
  [[ -d "$SRC_DIR" ]] || die "Entpackt, aber $SRC_DIR existiert nicht. Ordnername in $WORK_DIR prüfen."
  info "Quellcode liegt in $SRC_DIR"
}

cmd_prepare() {
  need "$PYTHON"; need_src
  info "Baue Private Fox in den Firefox-Quellcode ein …"
  "$PYTHON" "$REPO_DIR/scripts/prepare_tree.py" --src "$SRC_DIR" --repo "$REPO_DIR" --version "$VERSION"
}

cmd_bootstrap() {
  info "Installiere Build-Werkzeuge (Rust, Clang, SDKs …) – nur beim ersten Mal nötig …"
  mach --no-interactive bootstrap --application-choice=browser
}

cmd_build() {
  check_paths
  info "Baue Private Fox $VERSION – das dauert je nach Rechner 30 Minuten bis mehrere Stunden …"
  mach build
}

cmd_package() {
  info "Packe Private Fox …"
  mach package
  if [[ "$PLATFORM" == win ]]; then
    info "Baue Windows-Installer …"
    mach build installer
  fi
  mkdir -p "$OUT_DIR"
  local dist="$SRC_DIR/obj-privatefox/dist"
  local found=0 f
  shopt -s nullglob
  for f in "$dist"/privatefox-*.dmg "$dist"/privatefox-*.zip "$dist"/install/sea/*.exe; do
    cp -f "$f" "$OUT_DIR/"
    info "→ out/$(basename "$f")"
    found=1
  done
  shopt -u nullglob
  [[ $found -eq 1 ]] || warn "Keine Pakete gefunden. Inhalt von $dist prüfen."
}

cmd_run() {
  mach run
}

cmd_clean() {
  need_src
  info "Lösche Build-Ordner (Quellcode bleibt) …"
  rm -rf "$SRC_DIR/obj-privatefox"
}

cmd_all() {
  cmd_fetch
  cmd_prepare
  cmd_bootstrap
  cmd_build
  cmd_package
  info "Fertig. Pakete liegen in $OUT_DIR"
}

cmd_update() {
  cmd_latest
  # Mit der neuen Version neu starten, damit alle Pfade stimmen
  exec "$REPO_DIR/build.sh" all
}

usage() {
  cat <<EOF
Private Fox – Build-Skript (Firefox $VERSION, Plattform: $PLATFORM)

Befehle:
  all        fetch + prepare + bootstrap + build + package
  update     neueste Firefox-Version eintragen und 'all' ausführen
  latest     nur FIREFOX_VERSION auf die neueste Version setzen
  fetch      Firefox-Quellcode laden, Prüfsumme checken, entpacken
  prepare    Private-Fox-Änderungen einbauen (beliebig oft wiederholbar)
  bootstrap  Build-Werkzeuge installieren (einmalig)
  build      kompilieren
  package    .dmg (macOS) bzw. .zip + Installer (Windows) nach out/ legen
  run        frisch gebauten Browser starten
  clean      Build-Ordner löschen

Umgebungsvariablen:
  PF_WORK_DIR  Arbeitsordner (Standard: ./work), keine Leerzeichen!
  PYTHON       Python-Befehl (Standard: python3)
EOF
}

case "${1:-help}" in
  all)       cmd_all ;;
  update)    cmd_update ;;
  latest)    cmd_latest ;;
  fetch)     cmd_fetch ;;
  prepare)   cmd_prepare ;;
  bootstrap) cmd_bootstrap ;;
  build)     cmd_build ;;
  package)   cmd_package ;;
  run)       cmd_run ;;
  clean)     cmd_clean ;;
  help|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
