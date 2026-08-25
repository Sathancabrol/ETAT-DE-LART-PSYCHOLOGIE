# -*- coding: utf-8 -*-
"""Onglet Statistiques : arbre de décision interactive + bibliothèque de tests/formules."""

STAT_TREE = {
    "name": "Question de recherche",
    "q": "Que voulez-vous savoir de vos données ?",
    "children": [
        {"name": "Comparer des groupes", "q": "Y a-t-il une différence entre groupes/conditions ?",
         "children": [
             {"name": "Combien de groupes ?", "q": "Combien de conditions ou de groupes comparez-vous ?",
              "children": [
                  {"name": "2 groupes", "q": "Les mesures sont-elles appariées (mêmes participants) ?",
                   "children": [
                       {"name": "Indépendants", "q": "Distribution ~normale dans chaque groupe ?",
                        "children": [
                            {"name": "Oui → t-test indépendant", "test": "ttest_ind"},
                            {"name": "Non → Mann-Whitney U", "test": "mannwhitney"}]},
                       {"name": "Appariés", "q": "Distribution ~normale des différences ?",
                        "children": [
                            {"name": "Oui → t-test apparié", "test": "ttest_paired"},
                            {"name": "Non → Wilcoxon signé", "test": "wilcoxon"}]}]},
                  {"name": "3+ groupes", "q": "Mesures répétées (mêmes participants) ?",
                   "children": [
                       {"name": "Groupes indépendants", "q": "Distribution ~normale + variances homogènes ?",
                        "children": [
                            {"name": "Oui → ANOVA 1 facteur", "test": "anova"},
                            {"name": "Non → Kruskal-Wallis", "test": "kruskal"}]},
                       {"name": "Mesures répétées", "q": "Distribution ~normale ?",
                        "children": [
                            {"name": "Oui → ANOVA mesures répétées", "test": "anova_rm"},
                            {"name": "Non → Friedman", "test": "friedman"}]}]}]}]},
        {"name": "Associer deux variables", "q": "Cherchez-vous un lien/corrélation ?",
         "children": [
             {"name": "Variables continues", "q": "Relation linéaire + distribution normale ?",
              "children": [
                  {"name": "Oui → Pearson", "test": "pearson"},
                  {"name": "Non → Spearman", "test": "spearman"}]},
             {"name": "Variables catégorielles", "q": "Effectifs théoriques ≥ 5 partout ?",
              "children": [
                  {"name": "Oui → Chi² d'indépendance", "test": "chi2"},
                  {"name": "Non → Test exact de Fisher", "test": "fisher"}]}]},
        {"name": "Prédire", "q": "Voulez-vous prédire une variable à partir d'autres ?",
         "children": [
             {"name": "Prédire une valeur continue", "q": "Combien de prédicteurs ?",
              "children": [
                  {"name": "1 prédicteur → Régression linéaire simple", "test": "reg_simple"},
                  {"name": "2+ prédicteurs → Régression multiple", "test": "reg_multi"}]},
             {"name": "Prédire une catégorie", "q": "Deux catégories ou plus ?",
              "children": [
                  {"name": "2 catégories → Régression logistique", "test": "logreg"}]}]},
    ]}

STAT_TESTS = {
    "ttest_ind": {"name": "t-test indépendant", "when": "Comparer les moyennes de 2 groupes indépendants (ex : congruent vs incongruent entre participants).",
        "hypotheses": ["Normalité de la distribution dans chaque groupe", "Homogénéité des variances (test de Levene)", "Observations indépendantes"],
        "formula": "t = (M₁ − M₂) / √(s²p(1/n₁ + 1/n₂))", "formula_interpretation": "Écart des moyennes rapporté à l'erreur standard de la différence. |t| grand → groupes bien distincts.",
        "effect": "d de Cohen : d = (M₁ − M₂) / s_p — petit 0.2, moyen 0.5, grand 0.8", "software": "JASP : T-Tests → Classical. R : t.test(x, y, var.equal=TRUE). Python : scipy.stats.ttest_ind.",
        "report": "t(df) = X.XX, p = .XXX, d = 0.XX"},
    "ttest_paired": {"name": "t-test apparié", "when": "Comparer 2 conditions chez les mêmes participants (ex : TR avant/après entraînement).",
        "hypotheses": ["Normalité des différences appariées", "Paires ordonnées et complètes"],
        "formula": "t = M_d / (s_d / √n)", "formula_interpretation": "Moyenne des différences divisée par leur erreur standard. Robuste si n ≥ 30.",
        "effect": "d de Cohen apparié : d = M_d / s_d", "software": "JASP : T-Tests → Paired. R : t.test(après, avant, paired=TRUE). Python : scipy.stats.ttest_rel.",
        "report": "t(df) = X.XX, p = .XXX, d_z = 0.XX"},
    "mannwhitney": {"name": "Mann-Whitney U", "when": "Équivalent non paramétrique du t-test indépendant (rangs, distribution libre).",
        "hypotheses": ["Formes de distribution similaires (interprétation médiane)", "Indépendance des observations"],
        "formula": "U = n₁n₂ + n₁(n₁+1)/2 − R₁", "formula_interpretation": "R₁ = somme des rangs du groupe 1. U compare les rangs, pas les moyennes.",
        "effect": "r = Z/√N (petit 0.1, moyen 0.3, grand 0.5)", "software": "JASP : T-Tests → Mann-Whitney. R : wilcox.test(x, y). Python : scipy.stats.mannwhitneyu.",
        "report": "U = XX, p = .XXX, r = 0.XX"},
    "wilcoxon": {"name": "Wilcoxon signé", "when": "Équivalent non paramétrique du t-test apparié (rangs des différences).",
        "hypotheses": ["Différences symétriquement distribuées", "Mesures appariées"],
        "formula": "W = min(R+, R−)", "formula_interpretation": "Somme des rangs des différences positives vs négatives : W compare leur équilibre.",
        "effect": "r = Z/√N", "software": "JASP : T-Tests → Wilcoxon. R : wilcox.test(après, avant, paired=TRUE). Python : scipy.stats.wilcoxon.",
        "report": "W = XX, p = .XXX, r = 0.XX"},
    "anova": {"name": "ANOVA à 1 facteur", "when": "Comparer les moyennes de 3+ groupes indépendants (ex : 3 niveaux de charge).",
        "hypotheses": ["Normalité par groupe", "Homogénéité des variances", "Indépendance"],
        "formula": "F = MS_between / MS_within", "formula_interpretation": "Variance expliquée par le facteur rapportée à la variance résiduelle. F ≈ 1 → pas d'effet.",
        "effect": "η² : petit 0.01, moyen 0.06, grand 0.14", "software": "JASP : ANOVA → Classical. R : aov(y ~ groupe) + summary. Python : statsmodels anova_lm.",
        "report": "F(df1, df2) = X.XX, p = .XXX, η² = .XX — + post-hoc Tukey"},
    "anova_rm": {"name": "ANOVA mesures répétées", "when": "3+ conditions chez les mêmes participants (ex : 3 niveaux de congruence).",
        "hypotheses": ["Normalité des résidus", "Sphéricité (corrigée par Greenhouse-Geisser)", "Ordre contrebalancé"],
        "formula": "F = MS_condition / MS_error", "formula_interpretation": "Variance due aux conditions rapportée à l'erreur intra-sujet.",
        "effect": "η²p (partiel) : petit 0.01, moyen 0.06, grand 0.14", "software": "JASP : ANOVA → Repeated Measures. R : aov(y ~ cond + Error(suj/cond)). Python : pingouin.rm_anova.",
        "report": "F(df) = X.XX, p = .XXX, η²p = .XX, GG-corrected"},
    "kruskal": {"name": "Kruskal-Wallis", "when": "ANOVA non paramétrique (3+ groupes indépendants, rangs).",
        "hypotheses": ["Formes de distribution similaires", "Indépendance"],
        "formula": "H = (12/(N(N+1))) Σ(R_j²/n_j) − 3(N+1)", "formula_interpretation": "H mesure la dispersion des rangs moyens entre groupes ; suit χ² à k-1 ddl.",
        "effect": "ε² ou η²H", "software": "JASP : ANOVA → Kruskal-Wallis. R : kruskal.test. Python : scipy.stats.kruskal.",
        "report": "H(df) = X.XX, p = .XXX"},
    "friedman": {"name": "Friedman", "when": "ANOVA non paramétrique pour mesures répétées (rangs par sujet).",
        "hypotheses": ["Mesures appariées", "Distributions de rangs comparables"],
        "formula": "χ²_r = 12/(nk(k+1)) ΣR_j² − 3n(k+1)", "formula_interpretation": "Dispersion des rangs moyens entre conditions, par sujet.",
        "effect": "Kendall W (concordance)", "software": "JASP : Nonparametric → Friedman. R : friedman.test. Python : scipy.stats.friedmanchisquare.",
        "report": "χ²_r(df) = X.XX, p = .XXX, W = .XX"},
    "pearson": {"name": "Corrélation de Pearson", "when": "Lien linéaire entre 2 variables continues normales (ex : fréquence d'exposition vs liking).",
        "hypotheses": ["Linéarité de la relation", "Normalité bivariée", "Absence d'outliers majeurs"],
        "formula": "r = Σ((X−Mx)(Y−My)) / √(Σ(X−Mx)² Σ(Y−My)²)", "formula_interpretation": "Covariance standardisée : -1 à +1. r² = variance partagée.",
        "effect": "|r| : petit 0.1, moyen 0.3, grand 0.5", "software": "JASP : Regression → Correlation. R : cor.test(x, y). Python : scipy.stats.pearsonr.",
        "report": "r(df) = .XX, p = .XXX, IC95 [.XX, .XX]"},
    "spearman": {"name": "Corrélation de Spearman", "when": "Lien monotone entre variables ordinales ou non normales (rang-based).",
        "hypotheses": ["Relation monotone", "Observations indépendantes"],
        "formula": "ρ = 1 − 6Σd² / (n(n²−1))", "formula_interpretation": "Pearson appliqué aux rangs. Robuste aux outliers et échelles ordinales.",
        "effect": "|ρ| : petit 0.1, moyen 0.3, grand 0.5", "software": "JASP : Regression → Correlation (Spearman). R : cor.test(method='spearman'). Python : scipy.stats.spearmanr.",
        "report": "ρ = .XX, p = .XXX"},
    "chi2": {"name": "Chi² d'indépendance", "when": "Lien entre 2 variables catégorielles (ex : cadrage × choix).",
        "hypotheses": ["Effectifs théoriques ≥ 5 (80% des cases)", "Indépendance des observations"],
        "formula": "χ² = Σ (O − E)² / E", "formula_interpretation": "Écart cumulé entre observé et attendu sous l'hypothèse d'indépendance.",
        "effect": "V de Cramér : petit 0.1, moyen 0.3, grand 0.5", "software": "JASP : Frequencies → Contingency. R : chisq.test(table). Python : scipy.stats.chi2_contingency.",
        "report": "χ²(df) = X.XX, p = .XXX, V = .XX"},
    "fisher": {"name": "Test exact de Fisher", "when": "Chi² avec petits effectifs (une case < 5) — exact, sans approximation.",
        "hypotheses": ["Effectifs faibles", "Table 2×2 (ou plus par extension)"],
        "formula": "p = (a! b! c! d!) / (n! × produits des factorielles marginales)", "formula_interpretation": "Probabilité exacte d'observer cette table sous l'indépendance (hypergéométrique).",
        "effect": "Odds ratio + IC", "software": "JASP : Frequencies → Fisher. R : fisher.test(table). Python : scipy.stats.fisher_exact.",
        "report": "p = .XXX, OR = X.XX"},
    "reg_simple": {"name": "Régression linéaire simple", "when": "Prédire Y à partir d'un prédicteur X continu (droite des moindres carrés).",
        "hypotheses": ["Linéarité", "Résidus normaux et homoscédastiques", "Indépendance"],
        "formula": "Y = a + bX + ε ; b = cov(X,Y)/var(X)", "formula_interpretation": "b : variation de Y pour +1 unité de X. R² : variance de Y expliquée.",
        "effect": "R² : petit 0.02, moyen 0.13, grand 0.26", "software": "JASP : Regression → Linear. R : lm(Y ~ X). Python : statsmodels OLS.",
        "report": "b = X.XX, SE = .XX, t = X.XX, p = .XXX, R² = .XX"},
    "reg_multi": {"name": "Régression linéaire multiple", "when": "Prédire Y avec plusieurs prédicteurs (contrôle des contributions uniques).",
        "hypotheses": ["Pas de multicolinéarité sévère (VIF < 5)", "Résidus normaux, homoscédastiques", "n ≥ 10-15 par prédicteur"],
        "formula": "Y = a + b₁X₁ + … + b_kX_k + ε", "formula_interpretation": "Chaque b = effet unique du prédicteur à autres constantes. R² ajusté pénalise le nombre de prédicteurs.",
        "effect": "R² ajusté, ΔR² par bloc", "software": "JASP : Regression → Linear (plusieurs covariables). R : lm(Y ~ X1 + X2). Python : statsmodels OLS.",
        "report": "F(df) = X.XX, p = .XXX, R²aj = .XX ; β par prédicteur"},
    "logreg": {"name": "Régression logistique", "when": "Prédire une catégorie binaire (ex : aider ou non selon le nombre de témoins).",
        "hypotheses": ["Linéarité du logit", "Indépendance des observations", "Pas de séparation parfaite"],
        "formula": "log(p/(1−p)) = a + b₁X₁ + …", "formula_interpretation": "exp(b) = odds ratio : multiplicateur des cotes pour +1 unité du prédicteur.",
        "effect": "OR (IC95) ; pseudo-R² (Nagelkerke)", "software": "JASP : Regression → Logistic. R : glm(Y ~ X, family=binomial). Python : statsmodels Logit.",
        "report": "b = X.XX, SE = .XX, z = X.XX, p = .XXX, OR = X.XX"},
}

def get_stat_tree():
    return STAT_TREE

def get_stat_tests():
    return STAT_TESTS

# ─────────────── OUTILS DE TRAITEMENT DE DONNÉES ───────────────
DATA_TOOLS = [
    {"id": "jasp", "name": "JASP", "difficulty": "Facile", "icon": "mouse-pointer-click", "color": "#38bdf8",
     "desc": "Logiciel statistique gratuit et open source, interface point-and-click type SPSS. Sorties APA prêtes, analyses bayésiennes (facteur de Bayes).",
     "tags": ["t-tests", "ANOVA", "Régressions", "Bayésien"], "url": "https://jasp-stats.org/",
     "usage": "Import CSV/SPSS → choisir l'analyse dans le menu → interpréter les tableaux formatés APA.", "local": False},
    {"id": "jamovi", "name": "jamovi", "difficulty": "Facile", "icon": "layout-dashboard", "color": "#34d399",
     "desc": "Alternative moderne à SPSS, construite sur la même base que JASP. Modules communautaires (GAMLj, medmod).",
     "tags": ["Descriptives", "ANOVA", "Modules"], "url": "https://www.jamovi.org/",
     "usage": "Ouvrir le CSV → analyses via menus → syntaxe R générée en direct (viewable).", "local": False},
    {"id": "r", "name": "R / RStudio", "difficulty": "Avancé", "icon": "code", "color": "#60a5fa",
     "desc": "Langage statistique de référence scientifique : 19 000+ packages (tidyverse, lme4, brms). Standard des publications.",
     "tags": ["tidyverse", "ggplot2", "Modèles mixtes"], "url": "https://posit.co/download/rstudio-desktop/",
     "usage": "read_csv() → dplyr pour manipuler → ggplot2 pour figurer → lme4 pour modèles mixtes.", "local": False},
    {"id": "python", "name": "Python scientifique", "difficulty": "Moyen", "icon": "terminal", "color": "#fbbf24",
     "desc": "Écosystème pandas + scipy.stats + statsmodels + pingouin + seaborn. Idéal pour automatiser le traitement et le EEG (MNE).",
     "tags": ["pandas", "scipy", "pingouin", "seaborn"], "url": "https://www.anaconda.com/download",
     "usage": "df = pd.read_csv() → pingouin.ttest() → seaborn.barplot(). Notebooks Jupyter pour le workflow.", "local": False},
    {"id": "gpower", "name": "G*Power", "difficulty": "Moyen", "icon": "gauge", "color": "#f87171",
     "desc": "Calcul de puissance statistique : taille d'échantillon requise, puissance a priori/post-hoc, tailles d'effet.",
     "tags": ["Puissance", "Taille d'effet", "Planification"], "url": "https://www.psychologie.hhu.de/arbeitsgruppen/allgemeine-psychologie-und-arbeitspsychologie/gpower.html",
     "usage": "Choisir le test (t, ANOVA…) → entrer d/η², alpha, puissance → obtenir N requis.", "local": False},
    {"id": "csv", "name": "CSV / Excel", "difficulty": "Facile", "icon": "table", "color": "#94a3b8",
     "desc": "Format universel d'échange de données tabulaires. Nettoyage simple, TCD, vérifications de base avant analyse.",
     "tags": ["Import/Export", "Nettoyage", "Universel"], "url": "https://en.wikipedia.org/wiki/Comma-separated_values",
     "usage": "1 ligne = 1 observation, 1 colonne = 1 variable, en-têtes propres, sans fusions de cellules.", "local": True},
    {"id": "eeglab", "name": "EEGLAB (MATLAB)", "difficulty": "Avancé", "icon": "activity", "color": "#a78bfa",
     "desc": "Boîte à outils MATLAB pour EEG : prétraitement, ICA (artefacts), ERPs, analyse temps-fréquence.",
     "tags": ["EEG", "ICA", "ERPs"], "url": "https://sccn.ucsd.edu/eeglab/",
     "usage": "Import .set/.edf → filtrage 0.1-40 Hz → ICA pour artefacts → epoching → moyennes ERP.", "local": False},
    {"id": "mne", "name": "MNE-Python", "difficulty": "Avancé", "icon": "brain-circuit", "color": "#22d3ee",
     "desc": "Bibliothèque Python MEG/EEG : pipeline complet open source, visualisations riches, source estimation.",
     "tags": ["EEG/MEG", "Python", "Open source"], "url": "https://mne.tools/",
     "usage": "mne.io.read_raw() → filter → find_events → Epochs → evoked.plot().", "local": False},
    {"id": "fieldtrip", "name": "FieldTrip (MATLAB)", "difficulty": "Avancé", "icon": "orbit", "color": "#f472b6",
     "desc": "Toolbox MATLAB avancée MEG/EEG/iEEG : analyses de connectivité, statistiques par cluster, ECoG.",
     "tags": ["Connectivité", "Clusters", "MEG"], "url": "https://www.fieldtriptoolbox.org/",
     "usage": "ft_read_data → ft_preprocessing → ft_freqanalysis → ft_statistics (permutation clusters).", "local": False},
    {"id": "openai_stat", "name": "Assistant IA statistique", "difficulty": "Facile", "icon": "sparkles", "color": "#818cf8",
     "desc": "GPT-4/Claude pour : générer le code d'analyse, expliquer une sortie statistique, rédiger le rapport APA. Toujours vérifier les calculs !",
     "tags": ["Code", "Explication", "Rédaction"], "url": "https://chat.openai.com/",
     "usage": "Coller le CSV (structure) + la question → demander le code R/Python + interprétation → vérifier.", "local": False},
]

def get_data_tools():
    return DATA_TOOLS
