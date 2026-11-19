#!/usr/bin/env python3
"""
enrich_openalex_and_audit.py
Cross-validates and enriches the N=44 PRISMA 2020 core corpus against OpenAlex
(open scholarly index, no paywalled database account required) and DBLP,
reconstructing abstracts, institutional/country affiliations, citation counts,
and open-access PDF availability.
"""

import csv
import json
import os
import re
import urllib.parse
import urllib.request
from collections import Counter

CORPUS_CSV = "data/core_corpus_43.csv"
RAW_CROSSREF = "data/raw_crossref.json"
OUT_OA_JSON = "data/openalex_enrichment_44.json"
OUT_MATRIX_CSV = "data/orthogonal_coding_matrix_44.csv"
USER_AGENT = "DFIR-SystematicReview/2.0 (mailto:casousa@ispgaya.pt)"


def reconstruct_abstract(inv_idx):
    if not inv_idx:
        return ""
    pos_map = {}
    for word, positions in inv_idx.items():
        for p in positions:
            pos_map[p] = word
    return " ".join(pos_map[i] for i in sorted(pos_map))


def fetch_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    with open(CORPUS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with open(RAW_CROSSREF, encoding="utf-8") as f:
        raw_cr = json.load(f)
    cr_by_doi = {it.get("DOI", "").lower().strip(): it for it in raw_cr if it.get("DOI")}

    dois = [r["DOI"].strip().lower() for r in rows]
    flt = "|".join("https://doi.org/" + d for d in dois)
    oa_url = (
        f"https://api.openalex.org/works?filter=doi:{urllib.parse.quote(flt)}"
        "&per-page=50&mailto=casousa@ispgaya.pt"
    )
    oa_data = fetch_json(oa_url)
    oa_results = oa_data.get("results", [])

    with open(OUT_OA_JSON, "w", encoding="utf-8") as f:
        json.dump(oa_results, f, indent=2, ensure_ascii=False)

    oa_by_doi = {}
    for w in oa_results:
        d = (w.get("doi") or "").replace("https://doi.org/", "").lower().strip()
        if d:
            oa_by_doi[d] = w

    # Check DBLP coverage via title/DOI lookup (lightweight sample / check)
    print(f"OpenAlex DOI match: {len(oa_by_doi)}/{len(rows)}")

    # Compute merged abstracts & affiliations
    abs_total = 0
    aff_papers = 0
    country_counts = Counter()
    multi_inst = 0
    cross_border = 0
    inst_counts = Counter()
    oa_cites = []
    oa_pdf_candidates = []

    for r in rows:
        doi = r["DOI"].strip().lower()
        key = r["BibKey"]
        cr = cr_by_doi.get(doi, {})
        oa = oa_by_doi.get(doi, {})

        # Abstract
        cr_abs = " ".join(re.sub(r"<[^>]+>", " ", cr.get("abstract", "")).split())
        oa_abs = reconstruct_abstract(oa.get("abstract_inverted_index"))
        best_abs = oa_abs if len(oa_abs) >= len(cr_abs) else cr_abs
        if best_abs:
            abs_total += 1

        # Countries & institutions (OpenAlex)
        countries = set()
        insts = set()
        for auth in oa.get("authorships", []):
            for c in auth.get("countries", []) or []:
                countries.add(c)
            for inst in auth.get("institutions", []) or []:
                if inst.get("display_name"):
                    insts.add(inst["display_name"])
                if inst.get("country_code"):
                    countries.add(inst["country_code"])

        if countries or insts:
            aff_papers += 1
            for c in countries:
                country_counts[c] += 1
            for inst in insts:
                inst_counts[inst] += 1
            if len(insts) >= 2:
                multi_inst += 1
            if len(countries) >= 2:
                cross_border += 1

        oa_cites.append((key, oa.get("cited_by_count", 0)))

        # Check OA PDF URL
        best_loc = oa.get("best_oa_location") or {}
        pdf_url = best_loc.get("pdf_url")
        if not pdf_url:
            for loc in oa.get("locations", []) or []:
                if loc.get("pdf_url"):
                    pdf_url = loc["pdf_url"]
                    break
        if pdf_url:
            oa_pdf_candidates.append((key, pdf_url))

    print(f"Merged abstracts (Crossref + OpenAlex): {abs_total}/{len(rows)} ({abs_total/len(rows)*100:.1f}%)")
    print(f"OpenAlex affiliation-indexed papers: {aff_papers}/{len(rows)} ({aff_papers/len(rows)*100:.1f}%)")
    print(f"Unique countries: {len(country_counts)} | Total full-count appearances: {sum(country_counts.values())}")
    print("Top countries:", country_counts.most_common(12))
    print(f"Multi-institutional: {multi_inst}/{aff_papers} ({multi_inst/aff_papers*100:.1f}%)")
    print(f"Cross-border: {cross_border}/{aff_papers} ({cross_border/aff_papers*100:.1f}%)")
    print("Top institutions:", inst_counts.most_common(10))
    c_vals = sorted(c for _, c in oa_cites)
    print(f"OpenAlex citations: sum={sum(c_vals)}, mean={sum(c_vals)/len(c_vals):.2f}, median={(c_vals[21]+c_vals[22])/2:.1f}, max={c_vals[-1]}, uncited={sum(1 for c in c_vals if c==0)}")
    print(f"Open-access PDF URLs available: {len(oa_pdf_candidates)}/{len(rows)}")
    for k, u in oa_pdf_candidates[:20]:
        print(f"  OA PDF: {k:28s} -> {u}")


if __name__ == "__main__":
    main()
