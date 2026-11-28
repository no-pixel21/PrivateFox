#!/usr/bin/env bash
# Private Fox – create the key pair that signs automatic updates.
#
# Run this ONCE on your own computer (macOS Terminal, Linux, or Git Bash on Windows):
#
#   ./scripts/make-update-key.sh
#
# It creates:
#   ~/privatefox-update-key/privatefox-update-key.pem   PRIVATE key  – keep secret, back it up
#   update-signing/privatefox-update.der                public cert  – goes into the repo
#
# Anyone with the private key can push "updates" to every Private Fox user.
# Losing it means existing installs can never be updated automatically again.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY_DIR="${PF_KEY_DIR:-$HOME/privatefox-update-key}"
KEY="$KEY_DIR/privatefox-update-key.pem"
CERT_PEM="$KEY_DIR/privatefox-update-cert.pem"
CERT_DER="$REPO_DIR/update-signing/privatefox-update.der"

command -v openssl >/dev/null 2>&1 || { echo "ERROR: openssl is missing." >&2; exit 1; }

if [[ -e "$KEY" ]]; then
  echo "ERROR: $KEY already exists. Refusing to overwrite your signing key." >&2
  echo "If you really want a new key, move the old one away first." >&2
  exit 1
fi

mkdir -p "$KEY_DIR" "$(dirname "$CERT_DER")"
chmod 700 "$KEY_DIR"
umask 077

echo "==> Creating 4096-bit RSA private key …"
openssl genrsa -out "$KEY" 4096 2>/dev/null
chmod 600 "$KEY"

echo "==> Creating public certificate (valid for 30 years) …"
openssl req -new -x509 -key "$KEY" -out "$CERT_PEM" -days 10950 -sha384 \
  -subj "/CN=Private Fox Update Signing" 2>/dev/null
openssl x509 -in "$CERT_PEM" -outform DER -out "$CERT_DER"
chmod 644 "$CERT_DER"

cat <<EOF

Done.

  Private key (SECRET):   $KEY
  Public certificate:     $CERT_DER

Next steps
----------
1. Back up the private key somewhere safe (password manager, encrypted USB stick).
   Never commit it, never send it to anyone.

2. Add it to GitHub as a secret:
   https://github.com/no-pixel21/PrivateFox/settings/secrets/actions
   → "New repository secret"
     Name:   UPDATE_SIGNING_KEY
     Secret: the complete contents of the key file, including the BEGIN/END lines.
   On macOS you can copy it with:   pbcopy < "$KEY"

3. Put the public certificate into the repo:
   update-signing/privatefox-update.der
   (commit it, or upload it on GitHub via "Add file → Upload files" into update-signing/).
   The certificate is public – it's fine to share.
EOF
