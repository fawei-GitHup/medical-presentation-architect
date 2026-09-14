#!/usr/bin/env python3
"""Optionally confirm PubMed identifiers via NCBI E-utilities (call only when online research is authorized)."""

import argparse
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def pubmed(pmid, email=None):
    if not pmid.isdigit():
        raise ValueError("PMID must be numeric")
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}
    if email:
        params["email"] = email
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "medical-presentation-architect/1.0 (user-authorized citation metadata check)"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    art = root.find(".//PubmedArticle")
    if art is None:
        return {"pmid": pmid, "exists": False, "title": None, "doi": None}
    title = (
        " ".join("".join(art.find(".//ArticleTitle").itertext()).split())
        if art.find(".//ArticleTitle") is not None
        else ""
    )
    dois = [x.text for x in art.findall(".//ArticleId") if x.attrib.get("IdType") == "doi" and x.text]
    return {
        "pmid": pmid,
        "exists": True,
        "title": title,
        "doi": dois[0] if dois else None,
        "metadata_only": True,
        "retrieved_from": "NCBI E-utilities",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("project", type=Path)
    p.add_argument("pmid")
    p.add_argument("--email")
    a = p.parse_args()
    brief = json.loads((a.project / "intake" / "design_brief.json").read_text(encoding="utf-8"))
    policy = brief["fields"]["network_policy"]
    if (
        policy["status"] not in ("provided", "confirmed")
        or not isinstance(policy["value"], dict)
        or policy["value"].get("allow_public_web") is not True
    ):
        raise SystemExit("Network access is blocked: the current brief does not explicitly allow public web research.")
    print(json.dumps(pubmed(a.pmid, a.email), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
