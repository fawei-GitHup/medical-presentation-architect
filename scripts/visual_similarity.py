#!/usr/bin/env python3
"""Find exact and approximate duplicate rendered pages for human review."""

import argparse
import json
from pathlib import Path
from PIL import Image


def dhash(path, size=8):
    im = Image.open(path).convert("L").resize((size + 1, size))
    pix = list(im.getdata())
    bits = []
    for y in range(size):
        for x in range(size):
            i = y * (size + 1) + x
            bits.append(pix[i] > pix[i + 1])
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def scan(folder, max_distance=5):
    files = sorted(Path(folder).glob("*.png"))
    vals = {p: dhash(p) for p in files}
    pairs = []
    for i, a in enumerate(files):
        for b in files[i + 1 :]:
            distance = (vals[a] ^ vals[b]).bit_count()
            if distance <= max_distance:
                pairs.append({"a": a.name, "b": b.name, "hamming": distance})
    return {"pages": len(files), "candidate_duplicates": pairs, "passed": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--threshold", type=int, default=5)
    a = ap.parse_args()
    print(json.dumps(scan(a.folder, a.threshold), indent=2))
    print("Duplicates are review flags, not automatic proof of a defect.")


if __name__ == "__main__":
    main()
