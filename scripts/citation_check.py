#!/usr/bin/env python3
"""Deterministic claim-source referential and release-status checks; no semantic proof."""

import argparse
import json
from pathlib import Path


def check(sources, claims):
    byid = {s["id"]: s for s in sources}
    errs = []
    for c in claims:
        ids = c.get("source_ids", [])
        if c["kind"] != "synthetic" and not ids:
            errs.append(f"{c['id']}: non-synthetic claim has no source")
        if c["kind"] == "synthetic" and c.get("status") != "synthetic":
            errs.append(f"{c['id']}: synthetic example must be labeled synthetic")
        elif c["kind"] != "synthetic" and c.get("status") != "verified":
            errs.append(f"{c['id']}: claim is not verified")
        for sid in ids:
            s = byid.get(sid)
            if not s:
                errs.append(f"{c['id']}: missing source {sid}")
                continue
            if s.get("status") != "verified":
                errs.append(f"{c['id']}: source {sid} is not verified")
            if s.get("retraction_status") == "retracted":
                errs.append(f"{c['id']}: source {sid} is retracted")
            if s.get("type") == "local_document" and not s.get("sha256"):
                errs.append(f"{c['id']}: local document {sid} has no hash")
            if not any(s.get(k) for k in ("url", "doi", "pmid", "local_path")) and s.get("type") != "synthetic":
                errs.append(f"{c['id']}: source {sid} has no locator")
    return {"passed": not errs, "errors": errs, "semantic_support_reviewed": False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    a = ap.parse_args()
    r = check(json.loads((a.project / "sources.json").read_text()), json.loads((a.project / "claims.json").read_text()))
    print(json.dumps(r, ensure_ascii=False, indent=2))
    raise SystemExit(0 if r["passed"] else 1)


if __name__ == "__main__":
    main()
