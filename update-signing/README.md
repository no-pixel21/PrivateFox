# Update signing

`privatefox-update.der` is the **public** certificate of the key that signs Private Fox's
automatic updates. `scripts/prepare_tree.py` builds it into the updater, which then only
installs update files (`.mar`) signed with the matching private key.

- Create the key pair with `scripts/make-update-key.sh` (once).
- The **private** key is stored only as the GitHub secret `UPDATE_SIGNING_KEY` and in your
  own backup. It must never be committed.
- If this certificate is missing, builds still work, but no update files are produced.
