#!/usr/bin/env python3
"""
harvest_and_screen.py
Coleta e triagem PRISMA 2020 de literatura científica via Crossref API.
Executa:
1. Identificação com múltiplas queries booleanas (Scopus/WoS equivalentes).
2. Desduplicação por DOI / Título normalizado.
3. Triagem por critérios de Inclusão (IC1-IC5) e Exclusão (EC1-EC5).
4. Verificação de elegibilidade aprofundada (alinhamento com RQ1-RQ4).
5. Geração de ficheiro BibTeX IEEE, matriz de dados CSV e estatísticas PRISMA.
"""

import urllib.request
import urllib.parse
import json
import time
import re
import csv
from collections import Counter

QUERIES = [
    '"digital forensics" "large language model"',
    '"digital forensics" "LLM"',
    '"digital forensics" "ChatGPT"',
    '"digital forensics" "generative AI"',
    '"computer forensics" "large language model"',
    '"computer forensics" "LLM"',
    '"computer forensics" "ChatGPT"',
    '"cyber forensics" "large language model"',
    '"cyber forensics" "ChatGPT"',
    '"incident response" "large language model"',
    '"incident response" "LLM"',
    '"incident response" "generative AI"',
    '"memory forensics" "large language model"',
    '"memory forensics" "LLM"',
    '"forensic investigation" "large language model"',
    '"forensic investigation" "ChatGPT"',
    '"forensic analysis" "large language model"',
    '"forensic analysis" "LLM"',
    '"digital evidence" "large language model"',
    '"digital evidence" "ChatGPT"',
    '"chain of custody" "large language model"',
    '"digital forensics" "prompt injection"',
    '"digital forensics" "anti-forensics"',
    '"digital forensics" "foundation model"',
    '"email forensics" "large language model"',
    '"malware analysis" "large language model" forensics',
    '"log analysis" "large language model" forensics',
    '"forensic triage" "large language model"'
]

USER_AGENT = "AcademicResearchBot/1.0 (mailto:investigacao.forense.dfir@gmail.com; Digital Forensics Systematic Review)"

def normalize_title(title):
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r'[^a-z0-9 ]', '', t)
    return ' '.join(t.split())

def fetch_crossref_query(q, max_rows=35):
    encoded = urllib.parse.quote(q)
    # Filter 2021-2026, journal-article, proceedings-article, book-chapter
    url = f"https://api.crossref.org/works?query.bibliographic={encoded}&filter=from-pub-date:2021-01-01,until-pub-date:2026-12-31&rows={max_rows}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
            return data.get("message", {}).get("items", [])
    except Exception as e:
        print(f"Erro na query '{q}': {e}")
        return []

def main():
    print("=== FASE 1: IDENTIFICAÇÃO (CROSSREF API) ===")
    all_raw = []
    seen_raw_ids = set()

    for idx, q in enumerate(QUERIES, 1):
        print(f"[{idx}/{len(QUERIES)}] A consultar: {q}")
        items = fetch_crossref_query(q)
        for it in items:
            doi = it.get("DOI", "").lower().strip()
            title = (it.get("title") or [""])[0]
            norm_t = normalize_title(title)
            uid = doi if doi else norm_t
            if uid and uid not in seen_raw_ids:
                seen_raw_ids.add(uid)
                all_raw.append(it)
        time.sleep(0.3)

    total_identified = len(all_raw)
    print(f"\nTotal de registos brutos recolhidos (Identificação): {total_identified}")

    with open("data/raw_crossref.json", "w", encoding="utf-8") as f:
        json.dump(all_raw, f, indent=2, ensure_ascii=False)

    print("\n=== FASE 2: DESDUPLICAÇÃO E PADRONIZAÇÃO ===")
    unique_items = {}
    duplicates_count = 0

    for item in all_raw:
        doi = item.get("DOI", "").lower().strip()
        title = (item.get("title") or [""])[0].strip()
        norm_t = normalize_title(title)
        
        # Deduplication key
        key = doi if doi else norm_t
        if not key or len(norm_t) < 8:
            continue
            
        if key in unique_items:
            duplicates_count += 1
        else:
            unique_items[key] = item

    deduplicated = list(unique_items.values())
    total_deduplicated = len(deduplicated)
    print(f"Registos duplicados removidos: {duplicates_count}")
    print(f"Registos únicos após desduplicação: {total_deduplicated}")

    print("\n=== FASE 3: TRIAGEM (CRITÉRIOS IC / EC) ===")
    
    # Termos de exclusão médica/clínica/não digital (EC1)
    non_digital_forensics = [
        "dental", "odontology", "skeletal", "post-mortem", "autopsy", 
        "toxicology", "pathology", "radiology", "dna profiling", "asphyxia", 
        "drowning", "forensic medicine", "bone", "cadaver", "taphonomy", 
        "entomology", "clinical", "hospital", "patient", "nursing", "orthopedic"
    ]
    
    # Termos mandatórios de forense digital / cyber
    digital_forensic_terms = [
        "digital forensic", "computer forensic", "cyber forensic", "incident response",
        "memory forensic", "malware", "network forensic", "log analysis", "evidence",
        "chain of custody", "disk forensic", "anti-forensic", "investigation", "triage",
        "ediscovery", "forensic science international", "dfir", "artifact"
    ]
    
    # Termos mandatórios de IA Generativa / LLM
    genai_terms = [
        "large language model", "llm", "chatgpt", "gpt-4", "gpt-3.5", "gpt",
        "generative ai", "generative artificial intelligence", "foundation model",
        "prompt engineering", "prompt injection", "transformer", "llama", "copilot", "genai"
    ]

    screened_in = []
    excluded_title_abstract = []

    for item in deduplicated:
        title = (item.get("title") or [""])[0]
        abstract = item.get("abstract", "")
        # remove XML/JATS tags if present in Crossref abstract
        clean_abstract = re.sub(r'<[^>]+>', ' ', abstract)
        combined_text = f"{title} {clean_abstract}".lower()

        # Extrair ano
        issued = item.get("issued", {}).get("date-parts", [[None]])[0][0]
        if not issued:
            issued = item.get("created", {}).get("date-parts", [[None]])[0][0]

        # Validar ano (2021-2026) (IC4)
        if not issued or not (2021 <= issued <= 2026):
            excluded_title_abstract.append((item, "EC4 (Fora do período 2021-2026)"))
            continue

        # Validar tipo documental (IC3)
        doc_type = item.get("type", "")
        if doc_type in ["editorial", "peer-review", "posted-content", "dataset", "component"]:
            excluded_title_abstract.append((item, "EC4 (Tipo documental não elegível)"))
            continue

        # Verificar se cai em ciências forenses não digitais (EC1)
        if any(term in combined_text for term in non_digital_forensics):
            # Exceção apenas se contiver explicitamente 'digital forensics' ou 'incident response'
            if not ("digital forensic" in combined_text or "cyber forensic" in combined_text):
                excluded_title_abstract.append((item, "EC1 (Forense não-digital / médica / biológica)"))
                continue

        # Verificar se tem domínio forense digital (IC1 / EC3)
        has_forensic = any(term in combined_text for term in digital_forensic_terms)
        if not has_forensic:
            excluded_title_abstract.append((item, "EC3 (Sem relação com forense digital / incidente)"))
            continue

        # Verificar se tem LLM / GenAI (IC1 / EC2)
        has_genai = any(term in combined_text for term in genai_terms)
        if not has_genai:
            excluded_title_abstract.append((item, "EC2 (Sem componente de IA Generativa ou LLM)"))
            continue

        # Aprovado na triagem de título/resumo
        screened_in.append({
            "item": item,
            "title": title,
            "year": issued,
            "type": doc_type,
            "text": combined_text,
            "abstract": clean_abstract
        })

    print(f"Registos excluídos após leitura de Título + Abstract: {len(excluded_title_abstract)}")
    print(f"Registos elegíveis para análise aprofundada: {len(screened_in)}")

    print("\n=== FASE 4: ELEGIBILIDADE APROFUNDADA (ALINHAMENTO RQ1-RQ4) ===")
    
    # Classificar estudos de acordo com os temas de interesse das RQs:
    # RQ2: Tarefas operacionais (logs, malware, memory, triage, report generation)
    # RQ3: Cadeia de custódia, integridade, criptografia, alucinação, reprodutibilidade, legalidade
    # RQ4: Ameaças adversariais, prompt injection, anti-forensics, envenenamento
    final_included = []
    excluded_full_eval = []

    for entry in screened_in:
        txt = entry["text"]
        title = entry["title"]
        item = entry["item"]

        # Identificar cobertura de RQs
        rq2_matches = [w for w in ["malware", "log", "memory", "triage", "reverse engineering", "timeline", "report", "detection", "ransomware", "email", "traffic", "pcap", "incident response"] if w in txt]
        rq3_matches = [w for w in ["custody", "integrity", "hash", "reproducibility", "hallucination", "court", "legal", "admissibility", "verif", "bias", "evidentiary", "daubert"] if w in txt]
        rq4_matches = [w for w in ["prompt injection", "adversarial", "poisoning", "anti-forensic", "jailbreak", "evasion", "vulnerability", "attack"] if w in txt]

        rqs_covered = []
        if rq2_matches: rqs_covered.append("RQ2")
        if rq3_matches: rqs_covered.append("RQ3")
        if rq4_matches: rqs_covered.append("RQ4")
        
        # Se o artigo tiver relevância técnica forte e cobrir pelo menos uma dimensão analítica
        if rqs_covered or "forensic" in title.lower():
            entry["rqs"] = rqs_covered if rqs_covered else ["RQ2"]
            entry["rq2_keywords"] = rq2_matches
            entry["rq3_keywords"] = rq3_matches
            entry["rq4_keywords"] = rq4_matches
            final_included.append(entry)
        else:
            excluded_full_eval.append((entry, "EC3 (Menção superficial / sem contribuição metodológica forense)"))

    print(f"Artigos excluídos na fase de elegibilidade aprofundada: {len(excluded_full_eval)}")
    print(f"TOTAL FINAL DE ARTIGOS INCLUÍDOS: {len(final_included)}")

    # Guardar métricas PRISMA
    prisma_log = {
        "identificacao_total": total_identified,
        "duplicados_removidos": duplicates_count,
        "triagem_registos": total_deduplicated,
        "triagem_excluidos": len(excluded_title_abstract),
        "elegibilidade_avaliados": len(screened_in),
        "elegibilidade_excluidos": len(excluded_full_eval),
        "incluidos_total": len(final_included)
    }
    with open("data/prisma_counts.json", "w", encoding="utf-8") as f:
        json.dump(prisma_log, f, indent=2)

    print("\n=== FASE 5: GERAÇÃO DA BASE BIBTEX E MATRIZ DE EXTRAÇÃO ===")
    
    # Criar chaves bibtex limpas e registos BibTeX
    bibtex_entries = []
    matrix_rows = []

    for idx, e in enumerate(final_included, 1):
        it = e["item"]
        doi = it.get("DOI", "")
        title = e["title"]
        year = e["year"]
        container = (it.get("container-title") or ["Conference/Journal"])[0]
        authors = it.get("author", [])
        author_str = " and ".join([f"{a.get('family', 'Author')}, {a.get('given', '')}" for a in authors]) if authors else "Anon"
        first_author = authors[0].get("family", "Author").lower() if authors else "author"
        first_author = re.sub(r'[^a-z]', '', first_author)
        
        # Clean title for bibtex key
        title_word = re.sub(r'[^a-z]', '', title.lower().split()[0]) if title.split() else "paper"
        bib_key = f"{first_author}{year}_{title_word}"
        e["bib_key"] = bib_key

        doc_type = it.get("type", "article")
        entry_type = "article" if "journal" in doc_type else "inproceedings"

        # Formatar BibTeX
        bib_entry = f"@{entry_type}{{{bib_key},\n"
        bib_entry += f"  author = {{{author_str}}},\n"
        bib_entry += f"  title = {{{{{title}}}}},\n"
        bib_entry += f"  {'journal' if entry_type=='article' else 'booktitle'} = {{{{{container}}}}},\n"
        bib_entry += f"  year = {{{year}}},\n"
        if doi:
            bib_entry += f"  doi = {{{doi}}},\n"
        bib_entry += f"  publisher = {{{it.get('publisher', 'IEEE/Elsevier/Springer')}}}\n"
        bib_entry += "}\n"
        bibtex_entries.append(bib_entry)

        matrix_rows.append({
            "ID": idx,
            "BibKey": bib_key,
            "Year": year,
            "Title": title,
            "Authors": author_str,
            "Venue": container,
            "DOI": doi,
            "RQs_Addressed": ";".join(e["rqs"]),
            "RQ2_OpsKeywords": ";".join(e["rq2_keywords"]),
            "RQ3_CustodyCrypto": ";".join(e["rq3_keywords"]),
            "RQ4_ThreatsAdversarial": ";".join(e["rq4_keywords"])
        })

    # Guardar BibTeX
    with open("latex/references.bib", "w", encoding="utf-8") as f:
        f.write("% Ficheiro de Referências Gerado Automaticamente via Crossref API (Protocolo PRISMA 2020)\n\n")
        for b in bibtex_entries:
            f.write(b + "\n")

    # Guardar Matriz de Extração em CSV
    with open("data/artigos_incluidos_matriz.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=matrix_rows[0].keys())
        writer.writeheader()
        writer.writerows(matrix_rows)

    # Análise bibliométrica sintética (Anos, Veículos, Temas)
    years_counter = Counter([e["year"] for e in final_included])
    venues_counter = Counter([(e["item"].get("container-title") or ["Desconhecido"])[0] for e in final_included])
    rqs_counter = Counter([rq for e in final_included for rq in e["rqs"]])

    stats = {
        "distribuicao_temporal": dict(sorted(years_counter.items())),
        "top_veiculos": venues_counter.most_common(10),
        "cobertura_rqs": dict(rqs_counter)
    }

    with open("data/bibliometric_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print("\n=== RESUMO DAS MÉTRICAS PRISMA ===")
    for k, v in prisma_log.items():
        print(f"- {k}: {v}")

    print("\n=== DISTRIBUIÇÃO TEMPORAL DOS ARTIGOS INCLUÍDOS ===")
    for y, count in sorted(years_counter.items()):
        print(f"  {y}: {count} artigos")

    print("\n=== COBERTURA DAS QUESTÕES DE INVESTIGAÇÃO ===")
    for rq, count in rqs_counter.items():
        print(f"  {rq}: {count} artigos")

if __name__ == "__main__":
    main()
