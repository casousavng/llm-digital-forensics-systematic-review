# Generative AI and Large Language Models in Digital Forensics: PRISMA 2020 Replication Package

Public replication repository accompanying the IEEE systematic review and bibliometric analysis:

> **Carlos André Sousa**, *"Generative Artificial Intelligence and Large Language Models in Digital Forensics: A Systematic Review and Bibliometric Analysis,"* M.Sc. in Cybersecurity and Computer Systems Auditing, Polytechnic Institute of Gaya (ISPGAYA), 2026/2027.

## Repository Contents

- `latex/` — Complete IEEEtran journal LaTeX manuscript (`main.tex`, `sections/*.tex`, native TikZ `figures/*.tex`, `references.bib`, and compiled `main.pdf`).
- `data/raw_crossref.json` — Raw Crossref REST API bibliographic snapshot executed on **November 10, 2026** across 28 targeted query strings (`rows=35`, 2021–2026).
- `data/openalex_enrichment_44.json` — OpenAlex metadata cross-validation and enrichment for all **44/44 DOIs** (97.7% institutional/geographic coverage, 88.6% OpenAlex abstracts, cross-database citation counts).
- `data/orthogonal_coding_matrix_44.csv` — Complete decoupled orthogonal coding matrix for the $N=44$ core corpus (Direction, Study Type, 6 Subdomains, Deployment Locality, Agentic Scope, Crossref/OpenAlex citations, countries, and institutions).
- `data/qa_audit_oa_empirical_6.csv` — Auditable full-text forensic quality appraisal (QA1–QA4) across the open-access empirical full-text subset ($n=6$).
- `data/prisma_counts.json` & `data/replication_summary.json` — PRISMA 2020 flow counts and deterministic dual-pass coding verification ($\kappa=0.821$ on dedicated local deployment).
- `scripts/` — Reproducible Python harvesting, OpenAlex enrichment, dual-pass audit, and LaTeX compilation scripts.

## Key Summary Metrics ($N=44$)

| Indicator | Value |
| :--- | :--- |
| Validated Core Corpus ($N$) | 44 (22 journal articles, 22 proceedings) |
| Temporal Surge (2025–2026 YTD, Nov 10) | 84.1% ($n=37$) |
| OpenAlex DOI Cross-Validation | 44/44 (100.0%) |
| Affiliation / Abstract+Text Coverage | 43/44 (97.7%) / 40/44 (90.9%) |
| Forensic Direction | 88.6% ($n=39$) LLMs for DFIR \| 11.4% ($n=5$) Forensics of LLMs |
| Empirical LLM-for-DFIR Tools ($n=34$) | 23.5% ($n=8$) Dedicated Local \| 8.8% ($n=3$) Cross-Model Open \| 67.6% ($n=23$) Cloud/Unspec. |
| Agentic Scope ($N=44$) | 18.2% ($n=8$: 6 multi-agent tools, 2 agentic forensic targets) |

## Licensing Notice

Scripts and structured replication data are released under the MIT / CC-BY-4.0 open research licenses. Third-party publisher PDFs are deliberately excluded in compliance with publisher copyright terms.
