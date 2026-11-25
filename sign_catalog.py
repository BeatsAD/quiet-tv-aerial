#!/usr/bin/env python3
"""Verify the published files and sign the catalogue with an offline RSA key."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parent


def identity(file):
    digest = hashlib.sha256()
    with file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"bytes": file.stat().st_size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", type=Path, required=True)
    arguments = parser.parse_args()
    public = subprocess.check_output(["openssl", "pkey", "-in", str(arguments.key), "-pubout", "-outform", "DER"])
    if public != (ROOT / "public-key.der").read_bytes():
        raise ValueError("The signing key does not match this repository")
    catalog = json.loads((ROOT / "catalog.json").read_text())
    if catalog["version"] != 1 or not 1 <= catalog["revision"] <= 2**53 - 1 or not 1 <= len(catalog["clips"]) <= 32:
        raise ValueError("Invalid catalogue version, revision or count")
    seen = set()
    for clip in catalog["clips"]:
        identifier = clip["id"]
        if not re.fullmatch(r"aerial-[a-z0-9-]{1,48}", identifier) or identifier in seen:
            raise ValueError(f"Invalid or repeated ID: {identifier}")
        seen.add(identifier)
        if (not 1 <= len(clip["zh"].strip()) <= 80 or not 1 <= len(clip["en"].strip()) <= 120
                or not 1 <= clip["width"] <= 1920 or not 1 <= clip["height"] <= 1080
                or not 0 < clip["fps"] <= 60 or clip["durationMs"] <= 0
                or not clip["credit"].strip() or not clip["sourcePage"].startswith("https://")):
            raise ValueError(f"Invalid video metadata: {identifier}")
        original = clip.get("url", "")
        if original and not re.fullmatch(
            r"https://d34w7g4gy10iej\.cloudfront\.net/video/[0-9]+/DOD_[0-9]+/DOD_[0-9]+\.mp4", original
        ):
            raise ValueError(f"Invalid original DVIDS address: {identifier}")
        media = identity(ROOT / "docs" / "media" / f"{identifier}.mp4")
        if not 0 < media["bytes"] <= 100 * 1024**2 or any(clip[field] != value for field, value in media.items()):
            raise ValueError(f"Video does not match the catalogue: {identifier}")
        poster = ROOT / "docs" / "posters" / f"{identifier}.png"
        with poster.open("rb") as source:
            header = source.read(24)
        if len(header) != 24 or header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" or struct.unpack(">II", header[16:24]) != (720, 405):
            raise ValueError(f"Expected a 720 × 405 PNG: {identifier}")
        clip["poster"] = identity(poster)
        if not 0 < clip["poster"]["bytes"] <= 1024**2:
            raise ValueError(f"Poster exceeds 1 MiB: {identifier}")
    destination = ROOT / "docs" / "catalog.signed.json"
    if destination.exists():
        previous = json.loads(base64.b64decode(json.loads(destination.read_text())["payload"], validate=True))
        if catalog["revision"] < previous["revision"] or (
            catalog != previous and catalog["revision"] == previous["revision"]
        ):
            raise ValueError("A catalogue change requires a higher revision")
        current = {clip["id"]: clip for clip in catalog["clips"]}
        if any(current.get(clip["id"]) != clip for clip in previous["clips"]):
            raise ValueError("Existing catalogue entries are immutable")
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":")).encode()
    signature = subprocess.check_output(["openssl", "dgst", "-sha256", "-sign", str(arguments.key)], input=payload)
    envelope = {
        "keyId": "quiettv-aerial-1",
        "payload": base64.b64encode(payload).decode(),
        "signature": base64.b64encode(signature).decode(),
    }
    destination.write_text(json.dumps(envelope, indent=2) + "\n")


if __name__ == "__main__":
    main()
