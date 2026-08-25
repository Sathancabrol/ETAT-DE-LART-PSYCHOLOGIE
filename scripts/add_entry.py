#!/usr/bin/env python3
"""
Add new entry via DOI
Usage: python scripts/add_entry.py --doi 10.1038/s41467-025-12345-6
"""
import argparse, requests, datetime, csv, os, re
def get_crossref(doi):
    r=requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
    r.raise_for_status()
    return r.json()['message']

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--doi", required=True)
    p.add_argument("--file", default="data/nodes_etat_art_psychologie.csv")
    args=p.parse_args()
    doi=args.doi
    msg=get_crossref(doi)
    title=msg['title'][0] if isinstance(msg['title'], list) else msg['title']
    year=msg['published']['date-parts'][0][0]
    authors=msg.get('author',[])
    first=authors[0]['family'].lower() if authors else "unknown"
    journal=msg.get('container-title',[''])[0] if msg.get('container-title') else ""
    # generate id
    keyword=re.sub(r'[^a-z0-9]+','_', title.lower().split()[0])[:15]
    id_val=f"{first}{year}_{keyword}"
    id_val=re.sub(r'[^a-z0-9_]+','', id_val)
    print(f"Found: {title} ({year}) in {journal}")
    print(f"Suggested id: {id_val}")
    print(f"DOI: {doi}")
    # create minimal row with mandatory fields placeholder
    row={
        "id":id_val,
        "grand_domaine":"Psychologie",
        "domaine":"Psychologie cognitive",
        "sous_domaine":"Attention",
        "theme":title[:80],
        "question_scientifique":f"Quelle est la contribution de {title} ?",
        "reference_courte":f"{first.capitalize()} et al. {year}",
        "reference_complete":f"{', '.join([a.get('family','') for a in authors])} ({year}). {title}. {journal}. https://doi.org/{doi}",
        "doi":doi,
        "annee":year,
        "type_publication":"article_empirique",
        "journal":journal,
        "url":f"https://doi.org/{doi}",
        "niveau_preuve":"modere",
        "sources_triangulation":"Semantic Scholar + OpenAlex + Crossref",
        "citations_google_scholar":"",
        "citations_crossref":msg.get('is-referenced-by-count',''),
        "citations_openalex":"",
        "citations_semantic_scholar":"",
        "citations_web_of_science":"",
        "date_releve_citations":datetime.date.today().isoformat(),
        "altmetric_score":"",
        "peer_reviewed":"TRUE",
        "open_access":"TRUE",
        "data_open":"FALSE",
        "code_open":"FALSE",
        "preregistration":"FALSE",
        "sample_size":"",
        "sample_type":"humain adulte",
        "study_design":"experimental_controle",
        "consensus_actuel":f"{title[:150]}",
        "gap_actuel":"À compléter depuis discussion",
        "last_gap":f"{datetime.date.today().isoformat()} | Gap initial",
        "trust_factor":"60",
        "trust_niveau":"eleve",
        "trust_justification":"M=20 R=10 O=5 C=10 T=10 P=0 Total 60 - à affiner",
        "tags":"a completer, psychologie cognitive",
        "relations":"",
        "date_ajout":datetime.date.today().isoformat(),
        "date_mise_a_jour":datetime.date.today().isoformat(),
        "ajoute_par":"IA_Anara",
        "notes_internes":"Auto-généré via add_entry.py - à vérifier"
    }
    # append if file exists
    file_exists=os.path.exists(args.file)
    with open(args.file, 'a', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"✅ Added to {args.file} - now run validation")

if __name__=="__main__":
    main()
