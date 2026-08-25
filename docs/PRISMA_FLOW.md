# PRISMA 2020 Flow Diagram - Cartographie Psychologie 2020-2026

## Version préliminaire (illustrative) - à remplacer par chiffres réels après recherche finale

```
Identification
  Records identified from databases:
    PsycINFO (n = 642)
    PubMed/MEDLINE (n = 487)
    Scopus (n = 412)
    Web of Science (n = 201)
    ERIC (n = 100)
    OSF Registries/ClinicalTrials.gov/PROSPERO (n = 45)
    Crossref/OpenAlex (n = 120) for DOI verification
    Google Scholar complementary (n = 85) - not primary
  Total records identified (n = 2 092)
        ↓
  Records removed before screening:
    Duplicate records removed (n = 387) - via Zotero + script deduplicate.py
    Records marked as ineligible by automation (n = 120) - language, date
    Records removed for other reasons (n = 30) - no DOI, retracted
  Records unique to screen (n = 1 555)

Screening
  Records screened titles/abstracts (n = 1 555)
    Two independent reviewers (human + IA, Kappa calculated)
        ↓
  Records excluded titles/abstracts (n = 1 120)
    Reasons: out of period (n=180), out of 12 domains (n=340), no DOI (n=45), type excluded thesis/chapter (n=555)
        ↓
  Reports sought for retrieval (n = 435)
  Reports not retrieved (n = 100) - no full-text, paywall no OA, conference abstract only
  Reports assessed for eligibility full-text (n = 335)

Eligibility
  Reports excluded full-text (n = 215)
    Reasons:
      Insufficient data for extraction (n=78)
      Redundancy with included meta-analysis same sample (n=67)
      Low quality / critical flaws (n=40)
      Language other than EN/FR (n=30)
        ↓
  Studies included in cartography (n = 120) - target 120-250, current preliminary n=36

Included
  Studies included in synthesis by domain:
    Cognitive (n=15) | Development (n=12) | Social (n=12) | Clinical (n=15) | Health (n=10)
    Education (n=8) | Work (n=8) | Differential (n=8) | Aging (n=10)
    Neuropsychology (n=8) | Cognitive Neuroscience (n=10) | Meta-science (n=8)
  Reports of included studies (n = 120)
  Ongoing studies / protocols (n = 15) from OSF/ClinicalTrials
```

## PRISMA 2020 Checklist compliance (for this version 2.0)

| Item | Status | Location |
|------|--------|----------|
| 1 Title | ✅ Corrected to "Cartographie critique préliminaire" not exhaustive | Title |
| 2 Abstract | ⏳ To write structured abstract after final search | - |
| 3 Rationale | ✅ Gaps identified, 8 domains insufficiently covered | Section 3 |
| 4 Objectives | ✅ Main question + 7 sub-questions per domain | Section 1 |
| 5 Eligibility criteria | ✅ Inclusion/exclusion detailed | 2.6, 2.7 |
| 6 Information sources | ✅ 7 bases + Google Scholar complementary only, with justification | 2.3 |
| 7 Search strategy | ✅ Examples + template for full strategies, to be completed Annex A | 2.8 + SEARCH_STRATEGIES.md |
| 8 Selection process | ✅ Two independent reviewers, deduplication, Kappa | 2.9 |
| 9 Data collection | ✅ 42 fields template + validation script | 2.10 + TEMPLATE_CHAMPS.csv |
| 10 Data items | ✅ 42 fields defined | TEMPLATE_CHAMPS.csv |
| 11 Study risk of bias | ✅ RoB2, ROBINS-I, AMSTAR2, GRADE described, example table | 2.11 + Annex C |
| 12 Effect measures | ✅ g, d, r, OR, HR, SMD with CI | Table cartography |
| 13 Synthesis methods | ✅ Narrative + tables + transversal + research program | Sections 4,5,6 |
| 14 Reporting bias | ✅ Funnel plot, Egger, registries, grey literature | 2.11, 5.2 |
| 15 Certainty assessment | ✅ GRADE adaptation | 2.11 |
| 16-22 Results | ⏳ Preliminary n=36, to be completed to 120-250 | Section 3 table |
| 23-27 Discussion | ✅ Limitations, implications, next steps | Sections 5,6,8,9 |

## Tools

- Deduplication: `scripts/deduplicate.py` (to create) + Zotero
- Screening: Rayyan or manual + IA Anara
- Extraction: `data/nodes_etat_art_psychologie.csv` (42 fields)
- Validation: `scripts/validate_entry.py`
- Visualization: D3 graph `output/visual/d3_interactive.html`
- Pre-registration: OSF https://osf.io/qhrau/

## Next: Replace illustrative numbers with real numbers after final search 26-30 août 2026
