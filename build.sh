#!/usr/bin/env bash
# Private Fox – build script
# Runs on macOS (Terminal) and Windows (MozillaBuild shell: C:\mozilla-build\start-shell.bat).
#
#   ./build.sh all        download source, prepare, install toolchains, build, package
#   ./build.sh update     jump to the latest Firefox version and rebuild everything
#   ./build.sh help       all commands

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${PF_WORK_DIR:-$REPO_DIR/work}"
OUT_DIR="$REPO_DIR/out"
PYTHON="${PYTHON:-$(command -v python3 || command -v python || echo python3)}"
VERSION="$(tr -d ' \r\n' < "$REPO_DIR/FIREFOX_VERSION")"
SRC_DIR="$WORK_DIR/firefox-$VERSION"
ARCHIVE_URL="https://archive.mozilla.org/pub/firefox/releases/$VERSION"
TARBALL="firefox-$VERSION.source.tar.xz"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

case "$(uname -s)" in
  Darwin)               PLATFORM=mac ;;
  MINGW*|MSYS*|CYGWIN*) PLATFORM=win ;;
  Linux)                PLATFORM=linux ;;
  *)                    PLATFORM=unknown ;;
esac

need() { command -v "$1" >/dev/null 2>&1 || die "'$1' is missing. See DEVELOPMENT.md → Building locally."; }

sha512_of() {
  if command -v sha512sum >/dev/null 2>&1; then
    sha512sum "$1" | awk '{print $1}'
  else
    shasum -a 512 "$1" | awk '{print $1}'
  fi
}

check_paths() {
  [[ "$WORK_DIR" != *" "* ]] || die "The work directory contains spaces: $WORK_DIR
Firefox can't be built there. Move the repo to e.g. C:/src/privatefox or ~/src/privatefox,
or set PF_WORK_DIR to a path without spaces."
}

need_src() {
  [[ -d "$SRC_DIR" ]] || die "No source found for $VERSION. Run './build.sh fetch' first."
}

mach() {
  need_src
  (cd "$SRC_DIR" && ./mach "$@")
}

# ---------------------------------------------------------------- commands

cmd_latest() {
  need curl
  info "Asking Mozilla for the latest Firefox version …"
  local latest
  latest="$(curl -fsSL https://product-details.mozilla.org/1.0/firefox_versions.json \
    | "$PYTHON" -c 'import json,sys; print(json.load(sys.stdin)["LATEST_FIREFOX_VERSION"])')"
  [[ -n "$latest" ]] || die "Could not determine the version."
  if [[ "$latest" == "$VERSION" ]]; then
    info "Already up to date: $VERSION"
  else
    echo "$latest" > "$REPO_DIR/FIREFOX_VERSION"
    info "FIREFOX_VERSION: $VERSION → $latest"
  fi
}

cmd_fetch() {
  need curl; need tar; check_paths
  mkdir -p "$WORK_DIR"
  if [[ -d "$SRC_DIR" ]]; then
    info "Source for $VERSION is already unpacked: $SRC_DIR"
    return
  fi

  if [[ ! -f "$WORK_DIR/$TARBALL" ]]; then
    info "Downloading Firefox $VERSION source (about 600 MB) …"
    curl -fL --retry 3 -o "$WORK_DIR/$TARBALL.part" "$ARCHIVE_URL/source/$TARBALL"
    mv "$WORK_DIR/$TARBALL.part" "$WORK_DIR/$TARBALL"
  fi

  info "Verifying SHA-512 checksum …"
  curl -fsSL -o "$WORK_DIR/SHA512SUMS-$VERSION" "$ARCHIVE_URL/SHA512SUMS"
  local expected actual
  expected="$(awk -v f="source/$TARBALL" '$2 == f {print $1}' "$WORK_DIR/SHA512SUMS-$VERSION")"
  [[ -n "$expected" ]] || die "No checksum for $TARBALL found in SHA512SUMS."
  actual="$(sha512_of "$WORK_DIR/$TARBALL")"
  if [[ "$expected" != "$actual" ]]; then
    rm -f "$WORK_DIR/$TARBALL"
    die "Checksum does NOT match. Download deleted, please try again."
  fi
  info "Checksum ok."

  info "Unpacking (takes a few minutes) …"
  tar -xJf "$WORK_DIR/$TARBALL" -C "$WORK_DIR"
  [[ -d "$SRC_DIR" ]] || die "Unpacked, but $SRC_DIR doesn't exist. Check the folder name in $WORK_DIR."
  info "Source is in $SRC_DIR"
}

cmd_prepare() {
  need "$PYTHON"; need_src
  info "Applying Private Fox to the Firefox source …"
  "$PYTHON" "$REPO_DIR/scripts/prepare_tree.py" --src "$SRC_DIR" --repo "$REPO_DIR" --version "$VERSION"
}

cmd_bootstrap() {
  info "Installing build toolchains (Rust, Clang, SDKs …) – only needed the first time …"
  mach --no-interactive bootstrap --application-choice=browser
}

cmd_build() {
  check_paths
  info "Building Private Fox $VERSION – takes 30 minutes to several hours depending on the machine …"
  mach build
}

cmd_package() {
  info "Packaging Private Fox …"
  mach package
  if [[ "$PLATFORM" == win ]]; then
    info "Building Windows installer …"
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
  [[ $found -eq 1 ]] || warn "No packages found. Check the contents of $dist."
}

cmd_run() {
  mach run
}

cmd_clean() {
  need_src
  info "Deleting build directory (source stays) …"
  rm -rf "$SRC_DIR/obj-privatefox"
}

cmd_all() {
  cmd_fetch
  cmd_prepare
  cmd_bootstrap
  cmd_build
  cmd_package
  info "Done. Packages are in $OUT_DIR"
}

cmd_update() {
  cmd_latest
  # Restart with the new version so all paths are right
  exec "$REPO_DIR/build.sh" all
}

usage() {
  cat <<EOF
Private Fox – build script (Firefox $VERSION, platform: $PLATFORM)

Commands:
  all        fetch + prepare + bootstrap + build + package
  update     set the latest Firefox version and run 'all'
  latest     only set FIREFOX_VERSION to the latest version
  fetch      download Firefox source, verify checksum, unpack
  prepare    apply Private Fox changes (safe to repeat)
  bootstrap  install build toolchains (once)
  build      compile
  package    put .dmg (macOS) or .zip + installer (Windows) into out/
  run        start the freshly built browser
  clean      delete the build directory

Environment variables:
  PF_WORK_DIR  work directory (default: ./work), no spaces!
  PYTHON       python command (default: python3, else python)
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
