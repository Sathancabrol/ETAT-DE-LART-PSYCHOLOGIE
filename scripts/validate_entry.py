#!/usr/bin/env python3
"""
Validation script for nodes_etat_art_psychologie.csv
Checks 28 mandatory fields, DOI regex, triangulation >=3 sources, tags >=3, trust 0-100, dates YYYY-MM-DD, coherence, duplicates.
Usage: python scripts/validate_entry.py --file data/nodes_etat_art_psychologie.csv
"""

import csv
import re
import sys
import argparse
from datetime import datetime
from collections import Counter

DOI_REGEX = re.compile(r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$', re.IGNORECASE)
ID_REGEX = re.compile(r'^[a-z0-9_]+$')
DATE_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}$')

MANDATORY_FIELDS = [
    "id","grand_domaine","domaine","sous_domaine","theme",
    "question_scientifique","reference_courte","reference_complete","doi",
    "annee","type_publication","journal","niveau_preuve","sources_triangulation",
    "peer_reviewed","open_access","data_open","code_open","preregistration",
    "consensus_actuel","gap_actuel","last_gap",
    "trust_factor","trust_niveau",
    "tags","date_ajout","date_mise_a_jour","ajoute_par"
]

VALID_TYPE_PUBLICATION = {"article_empirique","revue_systematique","meta_analyse","perspective","theorique","preprint","chapitre","these","conference"}
VALID_NIVEAU_PREUVE = {"theorique","faible","faible_modere","modere","modere_eleve","eleve","tres_eleve"}
VALID_TRUST_NIVEAU = {"faible","modere","eleve","tres_eleve"}

def parse_args():
    p = argparse.ArgumentParser(description="Validate etat art CSV")
    p.add_argument("--file", required=True, help="Path to CSV")
    return p.parse_args()

def check_date(s):
    if not DATE_REGEX.match(s or ""):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except:
        return False

def validate_row(row, idx, seen_dois, seen_ids):
    errors = []
    warnings = []

    # 1. Mandatory filled
    for f in MANDATORY_FIELDS:
        if f not in row or row[f] is None or str(row[f]).strip() == "":
            errors.append(f"Row {idx}: mandatory field '{f}' empty")

    # 2. ID format
    id_val = row.get("id","")
    if id_val:
        if not ID_REGEX.match(id_val):
            errors.append(f"Row {idx} id '{id_val}' invalid regex ^[a-z0-9_]+$")
        if len(id_val) > 50:
            errors.append(f"Row {idx} id too long >50")
        if id_val in seen_ids:
            errors.append(f"Row {idx} duplicate id '{id_val}'")
        else:
            seen_ids.add(id_val)

    # 3. DOI valid
    doi = row.get("doi","")
    if doi:
        if not DOI_REGEX.match(doi):
            errors.append(f"Row {idx} doi '{doi}' invalid regex")
        if doi in seen_dois:
            errors.append(f"Row {idx} duplicate doi '{doi}'")
        else:
            seen_dois.add(doi)

    # 4. annee 1900-2030
    annee = row.get("annee","")
    try:
        y = int(annee)
        if not (1900 <= y <= 2030):
            errors.append(f"Row {idx} annee {y} out of range 1900-2030")
    except:
        errors.append(f"Row {idx} annee '{annee}' not integer")

    # 5. type_publication
    tp = row.get("type_publication","")
    if tp and tp not in VALID_TYPE_PUBLICATION:
        errors.append(f"Row {idx} type_publication '{tp}' not in {VALID_TYPE_PUBLICATION}")

    # 6. niveau_preuve
    np = row.get("niveau_preuve","")
    if np and np not in VALID_NIVEAU_PREUVE:
        errors.append(f"Row {idx} niveau_preuve '{np}' not in {VALID_NIVEAU_PREUVE}")

    # 7. sources_triangulation min 3 sources separated by +
    st = row.get("sources_triangulation","")
    if st:
        parts = [p.strip() for p in st.split("+")]
        if len(parts) < 3:
            errors.append(f"Row {idx} sources_triangulation '{st}' <3 sources, need min 3 separated by +")

    # 8. tags min 3
    tags = row.get("tags","")
    if tags:
        tparts = [t.strip() for t in tags.split(",") if t.strip()]
        if len(tparts) < 3:
            errors.append(f"Row {idx} tags '{tags}' <3 tags, need min 3 separated by ,")

    # 9. trust_factor 0-100
    tf = row.get("trust_factor","")
    try:
        tfi = int(tf)
        if not (0 <= tfi <= 100):
            errors.append(f"Row {idx} trust_factor {tfi} out of 0-100")
        # coherence trust_niveau
        tn = row.get("trust_niveau","")
        if tn:
            if tn not in VALID_TRUST_NIVEAU:
                errors.append(f"Row {idx} trust_niveau '{tn}' invalid")
            else:
                # check coherence
                if tfi <=29 and tn!="faible":
                    warnings.append(f"Row {idx} trust_factor {tfi} should be faible but got {tn}")
                elif 30 <= tfi <=59 and tn!="modere":
                    warnings.append(f"Row {idx} trust_factor {tfi} should be modere but got {tn}")
                elif 60 <= tfi <=84 and tn!="eleve":
                    warnings.append(f"Row {idx} trust_factor {tfi} should be eleve but got {tn}")
                elif 85 <= tfi <=100 and tn!="tres_eleve":
                    warnings.append(f"Row {idx} trust_factor {tfi} should be tres_eleve but got {tn}")
    except:
        errors.append(f"Row {idx} trust_factor '{tf}' not integer")

    # 10. Dates YYYY-MM-DD
    for df in ["date_ajout","date_mise_a_jour","date_releve_citations"]:
        dv = row.get(df,"")
        if dv and dv.strip():
            if not check_date(dv.strip()):
                errors.append(f"Row {idx} {df} '{dv}' invalid format YYYY-MM-DD")

    # 11. Boolean fields
    for bf in ["peer_reviewed","open_access","data_open","code_open","preregistration"]:
        bv = row.get(bf,"")
        if bv and str(bv).strip() not in {"TRUE","FALSE","PARTIAL",""}:
            # allow case-insensitive true/false
            if str(bv).upper() not in {"TRUE","FALSE","PARTIAL"}:
                errors.append(f"Row {idx} {bf} '{bv}' should be TRUE|FALSE|PARTIAL")

    # 12. question_scientifique ends with ?
    qs = row.get("question_scientifique","")
    if qs and not qs.strip().endswith("?"):
        errors.append(f"Row {idx} question_scientifique '{qs}' should end with ?")

    # 13. relations format if present
    rel = row.get("relations","")
    if rel and rel.strip():
        # format source:TYPE->cible;
        parts = [p.strip() for p in rel.split(";") if p.strip()]
        for part in parts:
            if "->" not in part or ":" not in part:
                errors.append(f"Row {idx} relations part '{part}' invalid format expected id:TYPE->id")
            else:
                # check TYPE
                try:
                    left, target = part.split("->")
                    src, typ = left.split(":")
                    if typ not in {"operationalization","converging","synthesis","falsification","revision","belongs"}:
                        warnings.append(f"Row {idx} relations TYPE '{typ}' unusual, expected operationalization|converging|synthesis|falsification|revision|belongs")
                except:
                    errors.append(f"Row {idx} relations part '{part}' parsing failed")

    # 14. Coherence domaine/sous_domaine/theme
    sd = row.get("sous_domaine","").lower()
    th = row.get("theme","").lower()
    if sd and th:
        if "attention" in sd and "attention" not in th and "attent" not in th:
            warnings.append(f"Row {idx} sous_domaine contains attention but theme '{th}' does not")
        if "mémoire" in sd or "memoire" in sd:
            if not any(k in th for k in ["mémoire","memoire","wmc","controle"]):
                warnings.append(f"Row {idx} sous_domaine memoire but theme doesn't contain memoire/WMC/controle")

    return errors, warnings

def main():
    args = parse_args()
    path = args.file
    errors_all = []
    warnings_all = []
    seen_dois = set()
    seen_ids = set()
    rows = []

    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # check header contains mandatory
            missing_headers = [h for h in MANDATORY_FIELDS if h not in reader.fieldnames]
            if missing_headers:
                print(f"❌ Missing mandatory headers: {missing_headers}")
                sys.exit(1)
            if len(reader.fieldnames) != 42:
                print(f"⚠️  Expected 42 columns, got {len(reader.fieldnames)}: {reader.fieldnames}")
            for idx, row in enumerate(reader, start=2): # 1 header
                rows.append(row)
                e,w = validate_row(row, idx, seen_dois, seen_ids)
                errors_all.extend(e)
                warnings_all.extend(w)
    except FileNotFoundError:
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"📊 Checked {len(rows)} rows from {path}")
    print(f"   Unique DOIs: {len(seen_dois)} | Unique IDs: {len(seen_ids)}")
    print(f"   Columns: {len(reader.fieldnames)} (expected 42)")

    if warnings_all:
        print(f"\n⚠️  Warnings ({len(warnings_all)}):")
        for w in warnings_all[:30]:
            print(f"  - {w}")
        if len(warnings_all) > 30:
            print(f"  ... and {len(warnings_all)-30} more warnings")

    if errors_all:
        print(f"\n❌ Errors ({len(errors_all)}):")
        for e in errors_all:
            print(f"  - {e}")
        print(f"\nValidation FAILED")
        sys.exit(1)
    else:
        print(f"\n✅ Validation PASSED - All 28 mandatory fields filled, DOI valid, triangulation >=3, tags >=3, trust 0-100, dates ISO, no duplicates")
        # Additional stats
        trust_vals = [int(r['trust_factor']) for r in rows if r['trust_factor'].isdigit()]
        if trust_vals:
            print(f"   Trust factor avg: {sum(trust_vals)/len(trust_vals):.1f} min:{min(trust_vals)} max:{max(trust_vals)}")
        # Count by niveau_preuve
        np_counter = Counter([r['niveau_preuve'] for r in rows])
        print(f"   Niveau preuve: {dict(np_counter)}")
        tp_counter = Counter([r['type_publication'] for r in rows])
        print(f"   Type publication: {dict(tp_counter)}")

if __name__ == "__main__":
    main()
