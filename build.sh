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

extract_tarball() {
  if [[ "$PLATFORM" == win ]]; then
    # On Windows, tar has to fork xz, which MSYS2 does unreliably. Python extracts without forking.
    "$PYTHON" - "$1" "$2" <<'PYEOF'
import sys, tarfile
src, dest = sys.argv[1], sys.argv[2]
kwargs = {"filter": "fully_trusted"} if hasattr(tarfile, "fully_trusted_filter") else {}
with tarfile.open(src, "r:xz") as t:
    t.extractall(dest, **kwargs)
PYEOF
  else
    tar -xJf "$1" -C "$2"
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
  extract_tarball "$WORK_DIR/$TARBALL" "$WORK_DIR"
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
  if [[ -n "${PF_JOBS:-}" ]]; then
    info "Limiting to $PF_JOBS parallel jobs (PF_JOBS)"
    mach build -j"$PF_JOBS"
  else
    mach build
  fi
}

cmd_package() {
  info "Packaging Private Fox …"
  mach package
  # On Windows, 'mach package' also builds the installer (dist/privatefox-*.installer.exe).
  mkdir -p "$OUT_DIR"
  local dist="$SRC_DIR/obj-privatefox/dist"
  local found=0 f
  shopt -s nullglob
  for f in "$dist"/privatefox-*.dmg "$dist"/privatefox-*.zip "$dist"/privatefox-*.installer.exe "$dist"/install/sea/*.exe; do
    case "$f" in *xpt_artifacts*) continue ;; esac   # internal build artifact, not for users
    cp -f "$f" "$OUT_DIR/"
    info "→ out/$(basename "$f")"
    found=1
  done
  shopt -u nullglob
  [[ $found -eq 1 ]] || warn "No packages found. Check the contents of $dist."
}

cmd_update_mar() {
  # Build the complete update file (.mar) from the packaged app, sign it with the key in
  # PF_UPDATE_KEY (PEM text, e.g. from the UPDATE_SIGNING_KEY secret) and write the
  # metadata the update feed needs. Without a key no update file is produced.
  need_src
  local obj="$SRC_DIR/obj-privatefox" dist plat app mar_bin out cert
  dist="$obj/dist"
  case "$PLATFORM" in
    win)   plat=win64;   app="$dist/privatefox" ;;
    mac)   plat=mac;     app="$(ls -d "$dist"/privatefox/*.app 2>/dev/null | head -1)" ;;
    *)     plat=linux64; app="$dist/privatefox" ;;
  esac
  cert="$REPO_DIR/update-signing/privatefox-update.der"

  if [[ -z "${PF_UPDATE_KEY:-}" ]]; then
    warn "PF_UPDATE_KEY not set – skipping the update file (see DEVELOPMENT.md → Automatic updates)."
    return 0
  fi
  [[ -f "$cert" ]] || die "update-signing/privatefox-update.der missing – run scripts/make-update-key.sh"
  [[ -n "$app" && -d "$app" ]] || die "Packaged app not found in $dist/privatefox – run './build.sh package' first."
  mar_bin="$dist/host/bin/mar"
  [[ -f "$mar_bin.exe" ]] && mar_bin="$mar_bin.exe"
  [[ -f "$mar_bin" ]] || die "Mozilla's mar tool not found at $dist/host/bin/mar"

  mkdir -p "$OUT_DIR/meta"
  out="$OUT_DIR/privatefox-$VERSION.$plat.complete.mar"
  info "Creating update file $(basename "$out") …"
  rm -f "$out" "$out.unsigned"
  MAR="$mar_bin" MOZ_PRODUCT_VERSION="$VERSION" MAR_CHANNEL_ID=privatefox-release \
    bash "$SRC_DIR/tools/update-packaging/make_full_update.sh" "$out.unsigned" "$app"

  info "Signing update file …"
  "$PYTHON" -c 'import cryptography' 2>/dev/null \
    || "$PYTHON" -m pip install --quiet --user cryptography \
    || die "Could not install the Python 'cryptography' package."
  local keyfile
  keyfile="$(mktemp)"
  chmod 600 "$keyfile"
  printf '%s\n' "$PF_UPDATE_KEY" > "$keyfile"
  "$PYTHON" "$REPO_DIR/scripts/sign_mar.py" sign --key "$keyfile" --in "$out.unsigned" --out "$out" --cert "$cert" \
    || { rm -f "$keyfile"; die "Signing failed."; }
  rm -f "$keyfile" "$out.unsigned"

  "$PYTHON" "$REPO_DIR/scripts/update_info.py" info --mar "$out" --app "$app" --platform "$plat" \
    --out "$OUT_DIR/meta/update-info-$plat.json"
  info "→ out/$(basename "$out")"
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
  update-mar build + sign the automatic-update file (needs PF_UPDATE_KEY)
  run        start the freshly built browser
  clean      delete the build directory

Environment variables:
  PF_WORK_DIR  work directory (default: ./work), no spaces!
  PF_UPDATE_KEY  PEM private key for signing update files (update-mar)
  PF_JOBS      max parallel compile jobs (default: all cores); lower it if you run out of RAM
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
  update-mar) cmd_update_mar ;;
  run)       cmd_run ;;
  clean)     cmd_clean ;;
  help|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
