#!/usr/bin/env python3
"""Private Fox – sign and verify MAR update files.

Firefox's updater only installs MAR files whose signature matches the certificate built into
it (see update-signing/). Mozilla's own `mar` tool creates the unsigned file; this script adds
one RSA-PKCS#1 v1.5 / SHA-384 signature (algorithm ID 2), the format the updater checks.

MAR layout (modules/libmar/src/mar.h):
    "MAR1" | u32 offset_to_index | u64 file_size | u32 num_signatures
    per signature: u32 algorithm_id | u32 size | signature bytes
    additional blocks + file contents ...
    index: u32 index_size | entries (u32 offset, u32 size, u32 flags, name\\0)

The signature covers the whole file except the signature bytes themselves; the algorithm ID
and size fields of each signature ARE included (modules/libmar/verify/mar_verify.c).

    sign_mar.py sign   --key key.pem  --in unsigned.mar --out signed.mar [--cert cert.der]
    sign_mar.py verify --cert cert.der --in signed.mar
"""

import argparse
import struct
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

SIG_ALGO_SHA384 = 2
HEADER = struct.Struct(">4sIQI")  # id, offset_to_index, file_size, num_signatures


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def parse(data):
    """Return (index_offset, sig_end, signatures, body_start) for a MAR."""
    if data[:4] != b"MAR1":
        die("not a MAR file")
    index_offset = struct.unpack_from(">I", data, 4)[0]
    if len(data) >= 20 and struct.unpack_from(">Q", data, 8)[0] == len(data):
        num = struct.unpack_from(">I", data, 16)[0]
        pos = 20
        sigs = []
        for _ in range(num):
            algo, size = struct.unpack_from(">II", data, pos)
            sigs.append((algo, data[pos + 8:pos + 8 + size]))
            pos += 8 + size
        return index_offset, pos, sigs
    # Old format without file size / signatures
    return index_offset, 8, None


def rewrite_index(index, delta):
    size = struct.unpack_from(">I", index, 0)[0]
    out = bytearray(index[:4])
    pos = 4
    end = 4 + size
    while pos < end:
        off, sz, flags = struct.unpack_from(">III", index, pos)
        name_end = index.index(b"\0", pos + 12)
        out += struct.pack(">III", off + delta, sz, flags) + index[pos + 12:name_end + 1]
        pos = name_end + 1
    return bytes(out)


def signed_bytes_of(data):
    """The bytes the signature covers, for a MAR that has signatures."""
    _, sig_end, sigs = parse(data)
    if not sigs:
        die("MAR has no signatures")
    parts = [data[:20]]
    pos = 20
    for _algo, sig in sigs:
        parts.append(data[pos:pos + 8])
        pos += 8 + len(sig)
    parts.append(data[sig_end:])
    return b"".join(parts)


def sign(key_path, in_path, out_path, cert_path=None):
    data = open(in_path, "rb").read()
    index_offset, body_start, sigs = parse(data)
    if sigs:
        die("input MAR is already signed")
    key = serialization.load_pem_private_key(open(key_path, "rb").read(), password=None)
    sig_len = key.key_size // 8

    body = data[body_start:index_offset]
    old_index = data[index_offset:]
    new_body_start = 20 + 8 + sig_len
    delta = new_body_start - body_start
    new_index = rewrite_index(old_index, delta)
    new_index_offset = new_body_start + len(body)
    total = new_index_offset + len(new_index)

    header = HEADER.pack(b"MAR1", new_index_offset, total, 1)
    sig_head = struct.pack(">II", SIG_ALGO_SHA384, sig_len)
    to_sign = header + sig_head + body + new_index
    signature = key.sign(to_sign, padding.PKCS1v15(), hashes.SHA384())
    assert len(signature) == sig_len

    out = header + sig_head + signature + body + new_index
    assert len(out) == total
    open(out_path, "wb").write(out)
    print(f"Signed {out_path} ({len(out)} bytes, RSA-{key.key_size}/SHA-384)")
    if cert_path:
        verify(cert_path, out_path)


def verify(cert_path, in_path):
    data = open(in_path, "rb").read()
    _, _, sigs = parse(data)
    if not sigs:
        die(f"{in_path} is not signed")
    cert = x509.load_der_x509_certificate(open(cert_path, "rb").read())
    msg = signed_bytes_of(data)
    for algo, sig in sigs:
        if algo != SIG_ALGO_SHA384:
            continue
        try:
            cert.public_key().verify(sig, msg, padding.PKCS1v15(), hashes.SHA384())
            print(f"Signature OK: {in_path} matches {cert_path}")
            return
        except Exception:
            pass
    die(f"signature of {in_path} does NOT match {cert_path}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sign")
    s.add_argument("--key", required=True)
    s.add_argument("--in", dest="inp", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--cert")
    v = sub.add_parser("verify")
    v.add_argument("--cert", required=True)
    v.add_argument("--in", dest="inp", required=True)
    a = ap.parse_args()
    if a.cmd == "sign":
        sign(a.key, a.inp, a.out, a.cert)
    else:
        verify(a.cert, a.inp)


if __name__ == "__main__":
    main()
