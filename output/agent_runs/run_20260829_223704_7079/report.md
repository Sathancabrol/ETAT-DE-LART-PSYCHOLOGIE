# Rapport d'exécution — ♅ Uranus

- **Tâche** : valider la base, auditer le trust factor et évaluer le risque de biais
- **Statut** : ✅ succès
- **Cerveau** : regles — déterministe
- **Durée** : 0.01 s
- **Run** : `run_20260829_223704_7079`

## Plan exécuté

1. ✅ **validate_entries** — Validation PASSED : 0 erreur(s), 0 avertissement(s) sur 14 lignes (0.0 s)
2. ✅ **trust_scoring** — Trust factor audité sur 14 références (écart moyen déclaré/heuristique : -6.6) (0.0 s)
3. ✅ **bias_assessment** — Risque de biais dépisté sur 14 références : {'modéré': 7, 'incertain': 5, 'élevé': 2} (0.0 s)

## Détail par compétence

### 1. validate_entries

*Valide la base 42 champs : 28 champs obligatoires, regex DOI, triangulation ≥3, tags ≥3, trust 0-100, dates ISO, doublons, cohérences.*

→ Validation PASSED : 0 erreur(s), 0 avertissement(s) sur 14 lignes

- 14 lignes × 42 colonnes (attendu 42)
- Erreurs : 0 | Avertissements : 0
- Trust moyen : 73.2

**Artefacts :**
- `output/agent_runs/run_20260829_223704_7079/validation_rapport.json`

### 2. trust_scoring

*Audit et re-calcul heuristique du Trust Factor (M+R+O+C+T-P) avec justification détaillée par référence ; détecte les incohérences trust_niveau/trust_factor.*

→ Trust factor audité sur 14 références (écart moyen déclaré/heuristique : -6.6)

- Trust déclaré moyen : 73.2 / heuristique : 66.6
- Écarts ≥15 points : 2 — à examiner manuellement

**Artefacts :**
- `output/agent_runs/run_20260829_223704_7079/trust_rapport.md`
- `output/agent_runs/run_20260829_223704_7079/trust_rapport.json`

### 3. bias_assessment

*Dépistage heuristique du risque de biais : AMSTAR2-lite (revues/méta-analyses) et RoB2-lite (articles empiriques), rapport par référence avec justifications.*

→ Risque de biais dépisté sur 14 références : {'modéré': 7, 'incertain': 5, 'élevé': 2}

- Distribution : {'modéré': 7, 'incertain': 5, 'élevé': 2}
- Risque élevé : Tünçok et al. 2025, Knight et al. 2025

**Artefacts :**
- `output/agent_runs/run_20260829_223704_7079/biais_rapport.md`
- `output/agent_runs/run_20260829_223704_7079/biais_rapport.json`

---
*Généré automatiquement par Uranus (♅), agent chercheur du Cognitorium — traçabilité complète dans `trace.json`.*