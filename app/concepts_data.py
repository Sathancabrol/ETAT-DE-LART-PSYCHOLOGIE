# -*- coding: utf-8 -*-
"""Données pour l'onglet Concepts : biais cognitifs, grands concepts, outils.
Chaque item : fiche complète (histoire, mécanismes, expériences, applications, débiaisage,
timeline historique, ressources DOI, résultats clés, schéma SVG, simulation labo)."""

# ─────────────── SVG helpers ───────────────
def _svg(inner, bg="#0b1020"):
    return ('<svg viewBox="0 0 420 230" style="width:100%;max-height:230px" xmlns="http://www.w3.org/2000/svg">'
            f'<rect width="420" height="230" rx="12" fill="{bg}"/>' + inner + '</svg>')

def schema_svg(steps, title="Mécanisme", reject=None):
    """Diagramme de flux horizontal : steps = [(texte, couleur_hex)], reject = texte rejeté."""
    n = len(steps)
    w = min(92, int(360 / max(n, 1)) - 8)
    parts = [f'<text x="210" y="24" fill="#818cf8" font-size="12" font-weight="bold" text-anchor="middle">{title}</text>']
    for i, (txt, col) in enumerate(steps):
        x = 24 + i * (w + 18)
        parts.append(f'<rect x="{x}" y="70" width="{w}" height="64" rx="10" fill="{col}22" stroke="{col}" stroke-width="1.5"/>')
        words, line, lines = txt.split(), "", []
        for wd in words:
            if len(line) + len(wd) > 12:
                lines.append(line); line = wd
            else:
                line = (line + " " + wd).strip()
        lines.append(line)
        for j, ln in enumerate(lines[:4]):
            parts.append(f'<text x="{x + w//2}" y="{96 + j*13}" fill="#e2e8f0" font-size="9" text-anchor="middle">{ln}</text>')
        if i < n - 1:
            parts.append(f'<path d="M{x+w+3} 102 L{x+w+15} 102" stroke="#64748b" stroke-width="2" marker-end="url(#arr)"/>')
    parts.append('<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#64748b"/></marker></defs>')
    if reject:
        parts.append(f'<text x="210" y="175" fill="#f87171" font-size="10" text-anchor="middle">✗ rejeté : {reject}</text>')
    return _svg("".join(parts))

def art_svg(key):
    """Illustrations stylisées réutilisables."""
    art = {
        "anchor": _svg('<line x1="210" y1="50" x2="210" y2="150" stroke="#22d3ee" stroke-width="6"/>'
            '<circle cx="210" cy="42" r="12" fill="none" stroke="#22d3ee" stroke-width="6"/>'
            '<path d="M160 120 Q210 190 260 120" fill="none" stroke="#22d3ee" stroke-width="6"/>'
            '<line x1="180" y1="70" x2="240" y2="70" stroke="#22d3ee" stroke-width="5"/>'
            '<text x="60" y="100" fill="#475569" font-size="16">10</text><text x="330" y="100" fill="#475569" font-size="16">90</text>'
            '<text x="120" y="140" fill="#fbbf24" font-size="22" font-weight="bold">65</text>'
            '<circle cx="130" cy="133" r="16" fill="none" stroke="#fbbf24" stroke-width="2"/>'
            '<text x="210" y="205" fill="#64748b" font-size="10" text-anchor="middle">L\'ancre attire toutes les estimations</text>'),
        "bubble": _svg('<circle cx="210" cy="115" r="78" fill="#10b98115" stroke="#10b981" stroke-dasharray="6 5"/>'
            '<circle cx="210" cy="112" r="16" fill="#818cf8"/><rect x="196" y="130" width="28" height="34" rx="8" fill="#818cf8"/>'
            '<text x="255" y="85" fill="#10b981" font-size="15">✓</text><text x="150" y="80" fill="#10b981" font-size="15">✓</text>'
            '<text x="262" y="150" fill="#10b981" font-size="15">✓</text><text x="152" y="152" fill="#10b981" font-size="15">✓</text>'
            '<text x="40" y="60" fill="#f87171" font-size="13">✗</text><text x="365" y="70" fill="#f87171" font-size="13">✗</text>'
            '<text x="372" y="170" fill="#f87171" font-size="13">✗</text><text x="30" y="175" fill="#f87171" font-size="13">✗</text>'
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">La bulle ne laisse entrer que ce qui confirme</text>'),
        "media": _svg('<path d="M150 40 Q110 115 150 190 L195 190 L195 40 Z" fill="#f8717130" stroke="#f87171"/>'
            '<path d="M270 40 Q310 115 270 190 L225 190 L225 40 Z" fill="#33415560" stroke="#475569"/>'
            '<text x="172" y="120" fill="#f87171" font-size="26" font-weight="bold" text-anchor="middle">✈</text>'
            '<text x="247" y="120" fill="#94a3b8" font-size="16" text-anchor="middle">📊</text>'
            '<text x="172" y="150" fill="#f87171" font-size="9" text-anchor="middle">VIVANT</text>'
            '<text x="247" y="150" fill="#94a3b8" font-size="9" text-anchor="middle">statistique</text>'
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">Ce qui frappe l\'esprit semble plus fréquent</text>'),
        "mountain": _svg('<path d="M40 190 L120 70 L200 190 Z" fill="#fbbf2430" stroke="#fbbf24"/>'
            '<path d="M150 190 L250 130 L380 190 Z" fill="#10b98130" stroke="#10b981"/>'
            '<circle cx="120" cy="62" r="7" fill="#fbbf24"/><circle cx="250" cy="122" r="7" fill="#10b981"/>'
            '<text x="120" y="45" fill="#fbbf24" font-size="10" text-anchor="middle">confiance ↑</text>'
            '<text x="300" y="115" fill="#10b981" font-size="10" text-anchor="middle">compétence réelle</text>'
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">Le sommet de la montagne stupide</text>'),
        "halo": _svg('<circle cx="210" cy="95" r="38" fill="none" stroke="#fbbf24" stroke-width="3"/>'
            '<circle cx="210" cy="80" r="13" fill="#818cf8"/><rect x="192" y="96" width="36" height="46" rx="10" fill="#818cf8"/>')
            .replace('</svg>', ''.join(f'<line x1="{x1}" y1="95" x2="{x2}" y2="{y2}" stroke="#fbbf2488" stroke-width="2"/>'
            f'<text x="{x2}" y="{y2+4}" fill="#fbbf24" font-size="9">{t}</text>'
            for x1, y1, x2, y2, t in [(255,80,320,55,"Intelligence"),(258,105,330,105,"Leadership"),(250,130,320,158,"Confiance"),(170,80,95,55,"Honnêteté"),(162,105,92,105,"Beauté"),(170,130,100,158,"Humour")]) +
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">Un trait positif illumine tous les autres</text></svg>'),
        "mirror": _svg('<rect x="240" y="55" width="90" height="120" rx="45" fill="#818cf818" stroke="#818cf8"/>'
            '<circle cx="170" cy="110" r="13" fill="#22d3ee"/><rect x="152" y="126" width="36" height="48" rx="10" fill="#22d3ee"/>'
            '<circle cx="285" cy="95" r="20" fill="#fbbf24"/><rect x="255" y="118" width="60" height="72" rx="16" fill="#fbbf24"/>'
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">Le reflet est plus grand que la réalité</text>'),
        "stroop": _svg('<text x="120" y="70" fill="#ef4444" font-size="26" font-weight="bold">ROUGE</text>'
            '<text x="120" y="110" fill="#3b82f6" font-size="26" font-weight="bold">ROUGE</text>'
            '<text x="120" y="150" fill="#22c55e" font-size="26" font-weight="bold">XXXX</text>'
            '<text x="345" y="70" fill="#10b981" font-size="11" text-anchor="middle">congruent ✓</text>'
            '<text x="345" y="110" fill="#f87171" font-size="11" text-anchor="middle">conflit ✗</text>'
            '<text x="345" y="150" fill="#64748b" font-size="11" text-anchor="middle">neutre</text>'
            '<text x="210" y="200" fill="#64748b" font-size="10" text-anchor="middle">Lire est automatique — nommer la couleur demande du contrôle</text>'),
        "nback": _svg(''.join(f'<rect x="{30+i*46}" y="85" width="38" height="52" rx="8" fill="{"#10b98130" if i in (2,5) else "#1e293b"}" stroke="{"#10b981" if i in (2,5) else "#334155"}"/>'
            f'<text x="{49+i*46}" y="118" fill="#e2e8f0" font-size="20" font-weight="bold" text-anchor="middle">{c}</text>'
            for i, c in enumerate("BKBM RRT".replace(" ", ""))) +
            '<path d="M49 152 Q90 190 141 152" fill="none" stroke="#10b981" stroke-dasharray="4 3"/>'
            '<path d="M187 152 Q228 190 271 152" fill="none" stroke="#10b981" stroke-dasharray="4 3"/>'
            '<text x="210" y="205" fill="#64748b" font-size="10" text-anchor="middle">2-back : comparer à 2 positions en arrière</text>'),
        "pavlov": _svg('<text x="80" y="55" fill="#94a3b8" font-size="10">1. Avant</text><text x="240" y="55" fill="#94a3b8" font-size="10">2. Association</text>'
            '<text x="80" y="90" fill="#e2e8f0" font-size="15">🔔 → 😐</text><text x="240" y="90" fill="#e2e8f0" font-size="15">🔔+🍖 → 🤤</text>'
            '<text x="80" y="130" fill="#94a3b8" font-size="10">3. Après (appris)</text>'
            '<text x="80" y="165" fill="#22d3ee" font-size="16">🔔 → 🤤</text>'
            '<text x="210" y="210" fill="#64748b" font-size="10" text-anchor="middle">Le neutre devient signal : conditionnement classique</text>'),
        "skinner": _svg(
            '<rect x="40" y="45" width="88" height="60" rx="9" fill="#10b98120" stroke="#10b981"/>'
            '<text x="84" y="72" fill="#10b981" font-size="9.5" text-anchor="middle">Renforcement +</text>'
            '<text x="84" y="90" fill="#10b981" font-size="9" text-anchor="middle">comportement ↑</text>'
            '<rect x="135" y="45" width="88" height="60" rx="9" fill="#f8717120" stroke="#f87171"/>'
            '<text x="179" y="72" fill="#f87171" font-size="9.5" text-anchor="middle">Punition +</text>'
            '<text x="179" y="90" fill="#f87171" font-size="9" text-anchor="middle">comportement ↓</text>'
            '<rect x="40" y="115" width="88" height="60" rx="9" fill="#22d3ee20" stroke="#22d3ee"/>'
            '<text x="84" y="142" fill="#22d3ee" font-size="9.5" text-anchor="middle">Renforcement −</text>'
            '<text x="84" y="160" fill="#22d3ee" font-size="9" text-anchor="middle">comportement ↑</text>'
            '<rect x="135" y="115" width="88" height="60" rx="9" fill="#fbbf2420" stroke="#fbbf24"/>'
            '<text x="179" y="142" fill="#fbbf24" font-size="9.5" text-anchor="middle">Punition −</text>'
            '<text x="179" y="160" fill="#fbbf24" font-size="9" text-anchor="middle">comportement ↓</text>'
            '<text x="305" y="80" fill="#94a3b8" font-size="9" text-anchor="middle">+ = on ajoute</text>'
            '<text x="305" y="100" fill="#94a3b8" font-size="9" text-anchor="middle">− = on retire</text>'
            '<text x="210" y="205" fill="#64748b" font-size="10" text-anchor="middle">La conséquence sculpte le comportement</text>'),
        "quadrant": _svg('<line x1="70" y1="190" x2="360" y2="190" stroke="#475569" stroke-width="2"/>'
            '<line x1="70" y1="190" x2="70" y2="35" stroke="#475569" stroke-width="2"/>'
            '<text x="215" y="208" fill="#94a3b8" font-size="9" text-anchor="middle">Compétence →</text>'
            '<text x="52" y="110" fill="#94a3b8" font-size="9" text-anchor="middle" transform="rotate(-90 52 110)">Défi →</text>'
            '<line x1="70" y1="190" x2="360" y2="35" stroke="#22d3ee" stroke-width="26" opacity="0.25"/>'
            '<text x="240" y="85" fill="#22d3ee" font-size="15" font-weight="bold" text-anchor="middle">FLOW</text>'
            '<text x="120" y="65" fill="#f87171" font-size="10" text-anchor="middle">Anxiété</text>'
            '<text x="300" y="175" fill="#fbbf24" font-size="10" text-anchor="middle">Ennui</text>'
            '<text x="110" y="178" fill="#64748b" font-size="10" text-anchor="middle">Apathie</text>'),
        "waves": _svg('<circle cx="210" cy="80" r="14" fill="#fbbf24"/><rect x="190" y="98" width="40" height="50" rx="12" fill="#fbbf24"/>'
            '<circle cx="130" cy="160" r="11" fill="#22d3ee"/><rect x="116" y="172" width="28" height="36" rx="9" fill="#22d3ee"/>'
            '<path d="M145 155 Q175 115 196 108" fill="none" stroke="#22d3ee88" stroke-width="2" stroke-dasharray="5 4"/>'
            '<path d="M225 108 Q260 130 268 150" fill="none" stroke="#22d3ee88" stroke-width="2" stroke-dasharray="5 4"/>'
            '<text x="300" y="165" fill="#94a3b8" font-size="13">🧸⚽📚</text>'
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">Base sécure → exploration → retour</text>'),
        "radar": _svg(
            '<line x1="210" y1="115" x2="305" y2="115" stroke="#334155"/>'
            '<line x1="210" y1="115" x2="239" y2="205" stroke="#334155"/>'
            '<line x1="210" y1="115" x2="133" y2="171" stroke="#334155"/>'
            '<line x1="210" y1="115" x2="133" y2="59" stroke="#334155"/>'
            '<line x1="210" y1="115" x2="239" y2="25" stroke="#334155"/>'
            '<text x="322" y="119" fill="#94a3b8" font-size="10" text-anchor="middle">O</text>'
            '<text x="252" y="222" fill="#94a3b8" font-size="10" text-anchor="middle">C</text>'
            '<text x="116" y="184" fill="#94a3b8" font-size="10" text-anchor="middle">E</text>'
            '<text x="116" y="50" fill="#94a3b8" font-size="10" text-anchor="middle">A</text>'
            '<text x="252" y="18" fill="#94a3b8" font-size="10" text-anchor="middle">N</text>'
            '<polygon points="268,112 236,185 158,160 162,80 234,55" fill="#818cf840" stroke="#818cf8" stroke-width="2"/>'
            '<text x="210" y="215" fill="#64748b" font-size="10" text-anchor="middle">Big Five — profil OCEAN</text>'),
        "line": _svg('<line x1="40" y1="115" x2="380" y2="115" stroke="#475569" stroke-width="2"/>'
            ''.join(f'<line x1="{40+i*34}" y1="110" x2="{40+i*34}" y2="120" stroke="#475569"/>' for i in range(11))
            + '<circle cx="261" cy="115" r="13" fill="#fbbf24"/><text x="261" y="95" fill="#fbbf24" font-size="12" font-weight="bold" text-anchor="middle">ancre : 65</text>'
            '<circle cx="228" cy="115" r="8" fill="#818cf8"/><text x="228" y="145" fill="#818cf8" font-size="10" text-anchor="middle">estimation</text>'
            '<circle cx="106" cy="115" r="8" fill="#10b981"/><text x="106" y="145" fill="#10b981" font-size="10" text-anchor="middle">vérité ≈ 28</text>'),
        "clock": _svg('<circle cx="210" cy="110" r="62" fill="none" stroke="#f87171" stroke-width="4"/>'
            '<line x1="210" y1="110" x2="210" y2="62" stroke="#e2e8f0" stroke-width="4"/><line x1="210" y1="110" x2="252" y2="126" stroke="#f87171" stroke-width="4"/>'
            '<text x="140" y="200" fill="#94a3b8" font-size="12">deadline ⏰</text>'
            '<text x="270" y="60" fill="#fbbf24" font-size="12">« demain… »</text>'),
        "neurons": _svg(''.join(f'<circle cx="{70+i*70}" cy="115" r="14" fill="{"#22d3ee" if i in (0,2,3) else "#334155"}"/>' for i in range(5))
            + ''.join(f'<line x1="{84+i*70}" y1="115" x2="{126+i*70}" y2="115" stroke="#475569" stroke-width="2"/>' for i in range(4))
            + '<path d="M70 115 Q140 60 210 115 Q280 170 350 115" fill="none" stroke="#22d3ee55" stroke-width="2" stroke-dasharray="4 4"/>'
            '<text x="210" y="205" fill="#64748b" font-size="10" text-anchor="middle">« Les neurones qui s\'activent ensemble se lient » — Hebb</text>'),
        "scale": _svg('<line x1="210" y1="60" x2="210" y2="160" stroke="#94a3b8" stroke-width="5"/>'
            '<line x1="120" y1="70" x2="300" y2="70" stroke="#94a3b8" stroke-width="4"/>'
            '<path d="M120 70 L95 115 L145 115 Z" fill="#22d3ee33" stroke="#22d3ee"/>'
            '<path d="M300 70 L275 105 L325 105 Z" fill="#f8717133" stroke="#f87171"/>'
            '<text x="120" y="135" fill="#22d3ee" font-size="9" text-anchor="middle">gains : sûr</text>'
            '<text x="300" y="125" fill="#f87171" font-size="9" text-anchor="middle">pertes : risqué</text>'),
    }
    return art.get(key, _svg(f'<text x="210" y="120" fill="#475569" font-size="12" text-anchor="middle">{key}</text>'))

# ─────────────── ARTICLES SCIENTIFIQUES ───────────────
SCIENTIFIC_ARTICLES = {
    "tversky1974": {"title": "Judgment under Uncertainty: Heuristics and Biases", "authors": "Tversky, A. & Kahneman, D.", "year": 1974,
        "journal": "Science, 185(4157), 1124-1131", "doi": "10.1126/science.185.4157.1124", "citations": 45000, "svg": "line",
        "abstract": "Cet article fondateur décrit trois heuristiques — représentativité, disponibilité, ancrage-ajustement — utilisées pour juger probabilités et fréquences, et systématiquement source de biais prévisibles.",
        "intro": "Les jugements probabilistes quotidiens dépassent les capacités computationnelles intuitives. Tversky & Kahneman émettent l'hypothèse que des heuristiques réductionnelles remplacent les évaluations statistiques, produisant des erreurs systématiques (biais) plutôt qu'aléatoires.",
        "method": "Série d'études expérimentales avec questionnaires à des populations diverses (étudiants, professionnels, médecins). Manipulation d'indices heuristiques et mesure des jugements numériques (estimations de fréquences, proportions, probabilités conditionnelles).",
        "results": {"desc": "Estimation du % de pays africains à l'ONU selon l'ancre (roue de fortune truquée 10 vs 65).", "data": {"Ancre basse (10)": 25, "Ancre haute (65)": 45}, "unit": "% estimé", "note": "Écart moyen ≈ 20 points induit par une information reconnue comme aléatoire par les participants."},
        "discussion": "L'ajustement à partir d'une valeur initiale est systématiquement insuffisant : l'ancre contamine l'estimation même quand sa source est aléatoire ou explicitement non informative. Le jugement humain repose sur des processus d'évaluation séquentiels compatibles avec les modèles d'ancrage (Sherif, Parducci).",
        "conclusion": "Les heuristiques sont économiques mais productive de biais graves et récurrents. Cet article fonde le programme de recherche sur les biais cognitifs (45 000+ citations) et débouche sur la Prospect Theory (1979)."},
    "wason1960": {"title": "On the failure to eliminate hypotheses in a conceptual task", "authors": "Wason, P. C.", "year": 1960,
        "journal": "Quarterly Journal of Experimental Psychology, 12(3), 129-140", "doi": "10.1080/17470216008416717", "citations": 5200, "svg": "bubble",
        "abstract": "Dans une tâche de découverte de règle (triplets 2-4-6), les participants testent presque exclusivement des exemples conformes à leur hypothèse, échouant à chercher les cas qui pourraient la falsifier.",
        "intro": "Popper a souligné que la science progresse par falsification. Wason teste si le raisonnement quotidien suit ce principe : les participants reçoivent le triplet 2-4-6 (règle : nombres croissants) et doivent découvrir la règle en proposant des triplets.",
        "method": "Tâche de formation de concepts : N=29 participants proposent librement des triplets et annoncent la règle. Cotations des triplets selon qu'ils peuvent falsifier (varier deux dimensions) ou seulement confirmer (varier une dimension) l'hypothèse tenue.",
        "results": {"desc": "Performance à la tâche 2-4-6 (règle correcte annoncée du 1er coup).", "data": {"Échec (1ère annonce)": 21, "Succès": 8}, "unit": "participants (N=29)", "note": "21/29 annoncent une règle plus étroite (ex : +2) après n'avoir testé que des cas confirmants."},
        "discussion": "La confirmation est une stratégie par défaut : les participants cherchent à vérifier « que leur règle marche », pas « où elle échoue ». Ce biais de confirmation est renforcé par la nature conservatrice du test d'hypothèses.",
        "conclusion": "Le raisonnement spontané viole le principe de falsification. Implications majeures pour la méthodologie scientifique, le diagnostic clinique et l'analyse de données."},
    "lord1979": {"title": "Biased Assimilation and Attitude Polarization", "authors": "Lord, C., Ross, L. & Lepper, M.", "year": 1979,
        "journal": "Journal of Personality and Social Psychology, 37(11), 2098-2109", "doi": "10.1037/0022-3514.37.11.2098", "citations": 7800, "svg": "scale",
        "abstract": "Des adversaires sur la peine de mort évaluant la même mixture d'études probantes et contre-probantes voient toutes deux renforcer leur position initiale : assimilation biaisée et polarisation.",
        "intro": "Deux hypothèses : (1) les partisans évaluent différemment la qualité méthodologique des études selon leur conclusion ; (2) ils attribuent une asymétrie de preuve (« il faudrait plus d'études pour me convaincre du contraire »).",
        "method": "N=48 partisans et opposants à la peine de mort lisent 2 études « probantes » et 2 « contre-probantes » (identiques pour tous, conclusions manipulées). Mesures : changement d'attitude, évaluation méthodologique, perception de l'asymétrie de preuve.",
        "results": {"desc": "Moyenne du changement d'attitude après lecture du même corpus mixte.", "data": {"Partisans (renforcement)": 5.1, "Opposants (renforcement)": 4.7, "Contrôle neutre": 0.2}, "unit": "points (échelle attitude)", "note": "Les deux camps se polarisent avec les mêmes données."},
        "discussion": "L'assimilation biaisée opère sur l'évaluation des procédures, pas seulement des conclusions. La mixité des preuves renforce la confiance de chacun, expliquant la persistance des controverses publiques malgré des données partagées.",
        "conclusion": "Exposer des adversaires à un corpus équilibré peut accroître la polarisation. Le débiaisage demande de déconnecter l'évaluation de la validité de la désirabilité des conclusions."},
    "kruger1999": {"title": "Unskilled and Unaware of It", "authors": "Kruger, J. & Dunning, D.", "year": 1999,
        "journal": "Journal of Personality and Social Psychology, 77(6), 1121-1134", "doi": "10.1037/0022-3514.77.6.1121", "citations": 12000, "svg": "mountain",
        "abstract": "Les moins compétents surestiment doublement leur performance : leurs erreurs les privent de l'expertise métacognitive pour les reconnaître ; les meilleurs tendent à se sous-estimer (effet faux consensus).",
        "intro": "Quatre études (humour, grammaire, logique) testent la prédiction : l'incompétence engendre une double charge — produire des réponses mauvaises ET être incapable de les détecter comme telles.",
        "method": "Les participants passent un test puis estiment leur performance absolue et relative (percentile vs pairs). Comparaison quartiles : bottom vs top performers. Manipulation : formation brève (étude 4) avant ré-estimation.",
        "results": {"desc": "Percentile estimé vs réel par quartile de performance (test de logique).", "data": {"Faibles - estimé": 62, "Faibles - réel": 12, "Forts - estimé": 78, "Forts - réel": 86}, "unit": "percentile", "note": "Écart estimé-réalité de +50 points pour les faibles ; -8 pour les forts."},
        "discussion": "La surconfiance des faibles provient d'une erreur de type régression vers la moyenne amplifiée par le déficit métacognitif. La formation réduit l'écart de ~50 à ~13 points : la compétence améliore à la fois la performance et sa calibration.",
        "conclusion": "L'incompétence s'auto-masque. Enjeux : formation des évaluateurs, feedback objectif, calibration métacognitive dans l'éducation."},
    "stroop1935": {"title": "Studies of interference in serial verbal reactions", "authors": "Stroop, J. R.", "year": 1935,
        "journal": "Journal of Experimental Psychology, 18(6), 643-662", "doi": "10.1037/h0054651", "citations": 18000, "svg": "stroop",
        "abstract": "Nommer la couleur d'encre d'un mot-coloré incongruent (« ROUGE » en bleu) est plus lent et errorneux que lire le mot : la lecture est un processus automatique qui interfère avec le nommage.",
        "intro": "La question : la lecture est-elle si automatisée qu'elle résiste à l'instruction de l'ignorer ? Stroop compare trois conditions : lecture de mots noirs, nommage de carrés colorés, nommage d'encre de mots incongruents.",
        "method": "Design intra-sujet, 100 stimuli par condition, mesure du temps total de lecture/nommage et des erreurs. Participants : 70 étudiants (expérience 1 : lecture ; expérience 2 : nommage).",
        "results": {"desc": "Temps moyen par série de 100 stimuli (expérience 2 : nommage de la couleur).", "data": {"Carrés (neutre)": 63.3, "Mots congruents": 74.0, "Mots incongruents": 110.3}, "unit": "secondes /100 stimuli", "note": "Coût d'interférence ≈ 47 s (≈ 470 ms/stimulus) vs condition neutre."},
        "discussion": "La force d'habitude de lecture (S-R bien apprise) crée une compétition de réponses que le contrôle attentionnel doit inhiber. Fondement des modèles d'automatisme (Posner & Snyder, Logan) et des mesures d'efficacité inhibitrice.",
        "conclusion": "Preuve canonique du traitement automatique vs contrôlé ; le Stroop devient paradigme standard de l'inhibition et du contrôle exécutif (18 000+ citations)."},
    "thorndike1920": {"title": "A constant error in psychological ratings", "authors": "Thorndike, E. L.", "year": 1920,
        "journal": "Journal of Applied Psychology, 4(1), 25-29", "doi": "10.1037/h0071663", "citations": 3800, "svg": "halo",
        "abstract": "L'analyse de ratings d'officiers et de professeurs révèle des corrélations élevées entre traits supposés indépendants : une impression globale (« halo ») contamine chaque évaluation spécifique.",
        "intro": "Thorndike interroge la validité des évaluations hiérarchiques : si les juges notaient chaque trait indépendamment, les corrélations inter-traits refléteraient la réalité, pas un halo.",
        "method": "Analyses de matrices de corrélations inter-traits sur deux datasets : ratings d'officiers (physique, intelligence, leadership, caractère) par supérieurs ; ratings d'enseignants par directeurs (N variable selon items).",
        "results": {"desc": "Corrélations moyennes observées entre traits indépendants (attendues ≈ 0.3-0.5 par validité réelle).", "data": {"Officiers (r moyen)": 0.62, "Enseignants (r moyen)": 0.71, "Attendu sans halo": 0.40}, "unit": "corrélation r", "note": "Redondance massive : le jugement global précède et colore les jugements partiels."},
        "discussion": "Le jugement humain est holistique : l'impression générale sert de substitut à l'analyse dimensionnelle. Effet documenté depuis (Landy & Sigall 1974 : CV identiques notés +30% avec photo attractive).",
        "conclusion": "Fonde l'effet de halo. Recommandations : évaluations structurées, critères explicites, évaluateurs multiples et anonymisation."},
}

# ─────────────── TIMELINES HISTORIQUES ───────────────
TIMELINES = {
    "c_classique": [
        {"y": 1897, "t": "création", "txt": "Twitmyer décrit la réponse conditionnelle au son (précurseur méconnu)"},
        {"y": 1903, "t": "création", "txt": "Pavlov formalise le conditionnement classique (Nobel 1904)"},
        {"y": 1927, "t": "publication", "txt": "Pavlov, « Les réflexes conditionnels »"},
        {"y": 1920, "t": "jalon", "txt": "Watson & Rayner : petit Albert — conditionnement émotionnel"},
        {"y": 1949, "t": "jalon", "txt": "Hebb : règle d'apprentissage neuronal"},
        {"y": 1968, "t": "extension", "txt": "Rescorla : nature de la contingence"},
        {"y": 1972, "t": "publication", "txt": "Rescorla & Wagner : modèle formel de l'association"},
        {"y": 1997, "t": "extension", "txt": "Conditionnement de la peur chez l'humain (LeDoux, amygdale)"},
        {"y": 2020, "t": "extension", "txt": "Apprentissage par renforcement computationnel (IA)"}],
    "c_operant": [
        {"y": 1898, "t": "création", "txt": "Thorndike : loi de l'effet (boîtes à problèmes)"},
        {"y": 1938, "t": "publication", "txt": "Skinner, « The Behavior of Organisms »"},
        {"y": 1953, "t": "jalon", "txt": "« Science and Human Behavior » — application sociale"},
        {"y": 1957, "t": "publication", "txt": "Programmes d'enseignement programmé"},
        {"y": 1971, "t": "jalon", "txt": "« Beyond Freedom and Dignity »"},
        {"y": 1986, "t": "extension", "txt": "Renforcement intermittent & addiction numérique"},
        {"y": 2023, "t": "extension", "txt": "Économie comportementale appliquée (nudges)"}],
    "c_flow": [
        {"y": 1975, "t": "création", "txt": "Csikszentmihalyi : « Beyond Boredom and Anxiety »"},
        {"y": 1990, "t": "publication", "txt": "« Flow » — modèle canalisé défi/compétence"},
        {"y": 1996, "t": "jalon", "txt": "Echelle Flow State (FS-2)"},
        {"y": 2003, "t": "extension", "txt": "Flow & jeux vidéo (Sweetser & Wyeth)"},
        {"y": 2014, "t": "publication", "txt": "Méta-analyse flow & performance (revue)"},
        {"y": 2018, "t": "extension", "txt": "Neurosciences du flow (transitoire hypofrontalité)"},
        {"y": 2021, "t": "extension", "txt": "Flow en télétravail & gamification"}],
    "c_attachement": [
        {"y": 1944, "t": "jalon", "txt": "Bowlby : 44 voleurs juvéniles — carence maternelle"},
        {"y": 1951, "t": "publication", "txt": "Rapport OMS « Maternal Care and Mental Health »"},
        {"y": 1958, "t": "jalon", "txt": "Harlow : singes à régime de fer"},
        {"y": 1969, "t": "publication", "txt": "« Attachment and Loss, Vol.1 »"},
        {"y": 1978, "t": "création", "txt": "Ainsworth : Strange Situation (3 styles)"},
        {"y": 1985, "t": "extension", "txt": "Main : attachement désorganisé"},
        {"y": 1987, "t": "extension", "txt": "Hazan & Shaver : attachement adulte romantique"},
        {"y": 2000, "t": "publication", "txt": "Mikulincer & Shaver : attachement dans le système de soin"},
        {"y": 2016, "t": "extension", "txt": "Neurosciences de l'attachement (ocytocine)"}],
    "c_stroop": [
        {"y": 1886, "t": "jalon", "txt": "Cattell : temps de nommage des couleurs"},
        {"y": 1935, "t": "création", "txt": "Stroop : « Studies of interference »"},
        {"y": 1970, "t": "jalon", "txt": "MacLeod : revue et consolidation"},
        {"y": 1991, "t": "extension", "txt": "Stroop émotionnel (clinique, anxiété)"},
        {"y": 2005, "t": "publication", "txt": "MacLeod : « Half a century of research » (méta-revue)"},
        {"y": 2012, "t": "extension", "txt": "Stroop numérique & spatial (variantes)"},
        {"y": 2020, "t": "extension", "txt": "Stroop en IA cognitive & interfaces"}],
    "c_bigfive": [
        {"y": 1936, "t": "jalon", "txt": "Allport & Odbert : 4500 termes trait (lexique)"},
        {"y": 1949, "t": "création", "txt": "Fiske : structure factorielle préliminaire"},
        {"y": 1961, "t": "jalon", "txt": "Tupes & Christal : 5 facteurs répliqués"},
        {"y": 1963, "t": "publication", "txt": "Norman : réplication et nomination"},
        {"y": 1981, "t": "jalon", "txt": "Goldberg : « Big Five » label"},
        {"y": 1990, "t": "publication", "txt": "McCrae & Costa : NEO-PI"},
        {"y": 1992, "t": "jalon", "txt": "NEO-PI-R (facettes)"},
        {"y": 2003, "t": "publication", "txt": "IPIP : versions libres et open source"},
        {"y": 2017, "t": "extension", "txt": "Universalité cross-culturelle confirmée (50+ pays)"}],
    "c_resilience": [
        {"y": 1979, "t": "création", "txt": "Rutter : protection vs vulnérabilité"},
        {"y": 1982, "t": "jalon", "txt": "Garmezy : études longitudinales à risque"},
        {"y": 1990, "t": "publication", "txt": "Werner & Smith : Kauai Longitudinal Study"},
        {"y": 2001, "t": "jalon", "txt": "APA : définition et facteurs de résilience"},
        {"y": 2007, "t": "publication", "txt": "Cyrulnik : résilience comme processus"},
        {"y": 2011, "t": "extension", "txt": "Masten : « ordinary magic » — systèmes de base"},
        {"y": 2020, "t": "extension", "txt": "Résilience pendant le COVID-19"}],
    "c_growth": [
        {"y": 1988, "t": "création", "txt": "Dweck : théories implicites de l'intelligence"},
        {"y": 1998, "t": "jalon", "txt": "Dweck & Leggett : modèle social-cognitif"},
        {"y": 2006, "t": "publication", "txt": "« Mindset » — vulgarisation massive"},
        {"y": 2010, "t": "extension", "txt": "Interventions growth mindset en classe"},
        {"y": 2014, "t": "jalon", "txt": "Paunesku : méta-intervention en ligne"},
        {"y": 2018, "t": "extension", "txt": "Yeager : étude nationale US N=12 490"},
        {"y": 2022, "t": "extension", "txt": "Réplicabilité : effets modestes mais réels (g≈0.1)"}],
    "c_dissonance": [
        {"y": 1957, "t": "création", "txt": "Festinger : « A Theory of Cognitive Dissonance »"},
        {"y": 1959, "t": "publication", "txt": "Festinger & Carlsmith : 1$ / 20$"},
        {"y": 1966, "t": "jalon", "txt": "Aronson : justification d'effort"},
        {"y": 1984, "t": "extension", "txt": "Cooper & Fazio : nouveaux regards (conséquences aversives)"},
        {"y": 1997, "t": "extension", "txt": "Modèle d'action (Harmon-Jones)"},
        {"y": 2007, "t": "extension", "txt": "Neurosciences : cortex cingulaire antérieur (van Veen)"},
        {"y": 2010, "t": "extension", "txt": "Dissonance chez le jeune enfant et les primates"}],
    "c_charge": [
        {"y": 1988, "t": "création", "txt": "Sweller : théorie de la charge cognitive"},
        {"y": 1998, "t": "jalon", "txt": "Effet exemple résolu (worked example)"},
        {"y": 2005, "t": "publication", "txt": "Instrument Paas : mesure subjective"},
        {"y": 2011, "t": "jalon", "txt": "Effet d'alignement fonctionnel"},
        {"y": 2019, "t": "extension", "txt": "CLT & multimédia (Mayer)"},
        {"y": 2022, "t": "extension", "txt": "Charge cognitive & GenAI (scaffolds)"}],
    "c_zpd": [
        {"y": 1930, "t": "création", "txt": "Vygotsky : zone proximale de développement"},
        {"y": 1934, "t": "publication", "txt": "« Pensée et langage »"},
        {"y": 1978, "t": "publication", "txt": "Traduction anglaise « Mind in Society »"},
        {"y": 1985, "t": "jalon", "txt": "Bruner : scaffolding"},
        {"y": 1995, "t": "extension", "txt": "Évaluation dynamique"},
        {"y": 2015, "t": "extension", "txt": "ZPD en environnements numériques adaptatifs"}],
    "c_metacognition": [
        {"y": 1976, "t": "jalon", "txt": "Flavell : métamémoire"},
        {"y": 1979, "t": "création", "txt": "Flavell : « Metacognition and cognitive monitoring »"},
        {"y": 1984, "t": "publication", "txt": "MAI (Schraw & Dennison)"},
        {"y": 1994, "t": "jalon", "txt": "Nelson & Narens : framework monitoring/contrôle"},
        {"y": 2004, "t": "extension", "txt": "Métacognition des décisions (cortex préfrontal)"},
        {"y": 2016, "t": "publication", "txt": "Fleming : méta-analyse signal detection (confidence)"},
        {"y": 2025, "t": "extension", "txt": "Métacognition en IA éducative (GenAI)"}],
}

# ─────────────── BIAIS COGNITIFS (15) ───────────────
def _bias(id, name, tagline, author, year, definition, impact, examples, histoire, mecanismes, experiences, applications, debias, related, svg, steps, sim, article, tl=None):
    return {"id": id, "cat": "biais", "name": name, "tagline": tagline, "author": author, "year": year,
            "definition": definition, "impact": impact, "examples": examples,
            "detail": {"histoire": histoire, "mecanismes": mecanismes, "experiences": experiences,
                       "applications": applications, "debias": debias, "related": related,
                       "timeline": TIMELINES.get(tl, []), "svg": art_svg(svg), "schema": schema_svg(steps, title="Mécanisme du biais", reject="évidence contradictoire"),
                       "simulation": sim, "article": article}}

BIASES = [
    _bias("b_confirmation", "Biais de confirmation", "On ne voit que ce qu'on veut voir.", "Wason (1960)", 1960,
        "Tendance à rechercher, interpréter et mémoriser préférentiellement les informations qui confirment nos croyances préexistantes, en négligeant les preuves contradictoires.",
        "Diagnostic médical erroné, bulles informationnelles, stratégies d'investissement aveugles, entretiens de recrutement orientés.",
        ["Un recruteur convaincu lit le CV « à travers » ses hypothèses", "Un élève ne teste que les cas où sa règle marche (2-4-6)", "Un investor ne lit que les analyses positives de son action"],
        "Wason (1960) démontre expérimentalement l'échec de falsification avec la tâche 2-4-6. Lord, Ross & Lepper (1979) montrent l'assimilation biaisée : mêmes preuves, polarisation accrue. Nickerson (1998) publie la revue de référence.",
        ["Recherche sélective d'information (on ne cherche que +)", "Interprétation asymétrique (pour = preuve, contre = bruit)", "Mémoire sélective (on se souvient des confirmations)", "Sentiment de objectivité (biais de biais)"],
        [{"ref": "Wason (1960) — Tâche 2-4-6", "article": "wason1960"}, {"ref": "Lord, Ross & Lepper (1979) — Assimilation biaisée", "article": "lord1979"}, {"ref": "Nickerson (1998) — Revue du biais de confirmation", "article": None}],
        [{"d": "Réseaux sociaux", "ex": "Bulles de filtres algorithmiques : on ne voit que des avis similaires."}, {"d": "Médecine", "ex": "Ancrage diagnostique : on cherche les symptômes qui confirment la première hypothèse."}, {"d": "Investissement", "ex": "On lit les analyses de l'action qu'on détient, pas les shorts."}, {"d": "Recrutement", "ex": "On pose des questions orientées vers le candidat pressenti."}],
        ["Chercher activement les preuves contraires (« qu'est-ce qui réfuterait ma croyance ? »)", "Se demander : quelle donnée me ferait changer d'avis ?", "Pré-mortem : supposer l'échec et en chercher les causes", "Diables avocats institutionnalisés (réunion, comité)"],
        ["b_ancrage", "b_disponibilite", "b_illusion_validite"], "bubble",
        [("Croyance préexistante", "#fbbf24"), ("Recherche sélective", "#22d3ee"), ("Interprétation biaisée", "#a78bfa"), ("Renforcement", "#10b981")],
        None, "wason1960", "c_metacognition"),
    _bias("b_ancrage", "Biais d'ancrage", "Le premier chiffre piège tous les suivants.", "Tversky & Kahneman (1974)", 1974,
        "Dépendance excessive à une information initiale (l'ancre) lors de la prise de décision numérique : l'ajustement à partir de l'ancre est systématiquement insuffisant.",
        "Négociation (première offre), prix barrés en commerce, estimation en justice (demandes de peine), diagnostic (valeur de labo initiale).",
        ["« Était 299€ » → 149€ paraît une affaire", "Roue de fortune truquée → estimation du % de pays africains décalée", "Premier salaire proposé en entretien → fourchette finale"],
        "Études pionnières : roue de fortune truquée (Kahneman & Tversky, 1974), estimation du nombre de pays africains à l'ONU. Englich et al. (2006) : même un lancer de dé influence les verdicts de juges. Furgeson (2021) : revue méta-analytique.",
        ["Activation automatique de la valeur (Système 1)", "Ajustement insuffisant (on s'écarte trop peu de l'ancre)", "Amorçage sélectif : l'ancre rend les infos conformes plus accessibles", "Sentiment que l'estimation « vient de soi »"],
        [{"ref": "Tversky & Kahneman (1974) — Heuristiques et biais", "article": "tversky1974"}, {"ref": "Englich, Mussweiler & Strack (2006) — Dé & verdicts judiciaires", "article": None}],
        [{"d": "Retail", "ex": "Prix barrés : l'ancien prix fabrique la valeur perçue."}, {"d": "Justice", "ex": "Requêtes de peine du procureur ancrent le verdict."}, {"d": "Immobilier", "ex": "Prix affiché en vitrine ancre la négociation."}, {"d": "Santé", "ex": "Premier chiffre de tension ancre le diagnostic."}],
        ["Considérer plusieurs ancres contradictoires avant d'estimer", "Estimer d'abord une fourchette, puis la valeur centrale", "Séparer la recherche d'information de la décision", "Ancres aléatoires conscientisées (on sait qu'on est ancré → corriger plus)"],
        ["b_framing", "b_disponibilite", "b_confirmation"], "anchor",
        [("Ancre externe", "#fbbf24"), ("Activation Système 1", "#a78bfa"), ("Ajustement insuffisant", "#22d3ee"), ("Estimation biaisée", "#f87171")],
        "anchoring", "tversky1974", "c_metacognition"),
    _bias("b_disponibilite", "Biais de disponibilité", "Ce qui frappe l'esprit semble plus fréquent.", "Tversky & Kahneman (1973)", 1973,
        "Estimer la fréquence ou la probabilité d'un événement selon la facilité avec laquelle des exemples viennent à l'esprit — facilité qui dépend de la vivacité, la récence et la couverture médiatique.",
        "Peurs mal calibrées (avion vs voiture), décisions médicales (maladie médiatisée), gestion des risques en entreprise.",
        ["Crash d'avion médiatisé → on surestime ce risque", "Après un accident rapporté, on surestime sa probabilité de recommencer", "Une maladie célèbre paraît plus fréquente qu'une plus mortelle mais silencieuse"],
        "Tversky & Kahneman (1973) : les mots en K plus faciles à générer sont jugés plus fréquents. Slovic et al. documentent la perception des risques. Schwarz et al. (1991) : la facilité elle-même (pas seulement le contenu) informe le jugement.",
        ["Récupération en mémoire guidée par la vivacité", "Couverture médiatique asymétrique", "Substitution d'attribut : facilité → fréquence", "Rôle des émotions (vividness → affect)"],
        [{"ref": "Tversky & Kahneman (1973) — Availability", "article": "tversky1974"}, {"ref": "Schwarz et al. (1991) — Ease of retrieval", "article": None}],
        [{"d": "Assurance", "ex": "On sur-assure contre les risques médiatisés et sous-assure les vrais."}, {"d": "Santé publique", "ex": "Paniques sanitaires sur des risques faibles."}, {"d": "Sécurité routière", "ex": "Craindre l'avion plus que la voiture."}, {"d": "Management", "ex": "Le dernier incident planifie tout le plan d'action."}],
        ["Consulter les statistiques de base avant de juger", "Se demander : ai-je des exemples ou des chiffres ?", "Base rates explicites (Fréquence réelle vs cas médiatisés)", "Check-lists de risques calibrées"],
        ["b_ancrage", "b_negativite", "b_survivant"], "media",
        [("Événement médiatisé", "#f87171"), ("Trace mnésique vive", "#a78bfa"), ("Facilité de rappel", "#22d3ee"), ("Surestimation", "#fbbf24")],
        None, "tversky1974", "c_metacognition"),
    _bias("b_dunning_kruger", "Effet Dunning-Kruger", "Moins on sait, plus on croit savoir.", "Kruger & Dunning (1999)", 1999,
        "Les individus les moins compétents dans un domaine surestiment fortement leur performance (l'incompétence les prive de la capacité de la reconnaître), tandis que les experts tendent à se sous-estimer légèrement.",
        "Auto-évaluation erronée en formation, confiance injustifiée dans les opinions (santé, finances), évaluation de recrutement.",
        ["Le novice à 12e percentile s'estime à 62e", "L'étudiant qui échoue attribue à la « chance »", "Le Dr Google surdiagnostique sa compétence médicale"],
        "Kruger & Dunning (1999), 4 études (humour, grammaire, logique). Répliques : Ehrlinger et al. (2008) ; Schlösser et al. (2013) ; Jarry et al. (2020) en français. Critique méthodologique : Nuhfer et al. (2017) sur l'artefact de régression.",
        ["Déficit métacognitif : les mêmes compétences servent à faire ET à évaluer", "Erreur de régression vers la moyenne", "Faux consensus des experts (les autres savent comme moi)", "Boucle : sans feedback, pas de recalibration"],
        [{"ref": "Kruger & Dunning (1999) — Unskilled and Unaware", "article": "kruger1999"}, {"ref": "Ehrlinger et al. (2008) — Pourquoi les faibles ne se voient pas", "article": None}],
        [{"d": "Éducation", "ex": "L'élève qui se surestime ne révise pas."}, {"d": "Médecine", "ex": "Le patient non-formé juge les protocoles inutiles."}, {"d": "Tech", "ex": "Le développeur junior se croit senior (échelle Dreyfus)."}, {"d": "Réseaux", "ex": "Commentaires confiants sur des sujets mal maîtrisés."}],
        ["Formation ciblée : apprendre à reconnaître ses erreurs", "Feedback objectif et fréquent (calibration)", "Tests de vérification après lecture", "Comparaison à un standard externe, pas à l'intuition"],
        ["b_surconfiance", "b_confirmation", "b_haloeffet"], "mountain",
        [("Tâche réalisee", "#818cf8"), ("Auto-évaluation", "#fbbf24"), ("Déficit métacognitif", "#f87171"), ("Sur/confiance", "#22d3ee")],
        "dunnkruger", "kruger1999", "c_metacognition"),
    _bias("b_haloeffet", "Effet de halo", "Une qualité éclaire toutes les autres.", "Thorndike (1920)", 1920,
        "Une caractéristique positive (ou négative — effet de corne) d'une personne ou d'un objet influence les jugements sur ses autres caractéristiques, créant une redondance artificielle entre dimensions indépendantes.",
        "Recrutement (photo, école), évaluation scolaire (propreté → intelligence), marketing (ambassadeur), justice (apparence physique).",
        ["CV identique : +30% avec une photo attractive (Landy & Sigall 1974)", "L'élève bien habillé est jugé plus intelligent", "Le produit d'une marque premium paraît de meilleure qualité"],
        "Thorndike (1920) analyse les ratings d'officiers : corrélations inter-traits massives (r≈0.6-0.7) pour des dimensions supposées indépendantes. Landy & Sigall (1974) : photo × note d'essai. Nisbett & Wilson (1977) : le halo sans conscience.",
        ["Jugement global précède les jugements analytiques", "Induction affective (j'aime → il est compétent)", "Attente confirmatoire (on voit ce qu'on attend)", "Contagion d'évaluation (un bon item rehausse tous les autres)"],
        [{"ref": "Thorndike (1920) — Constant error in ratings", "article": "thorndike1920"}, {"ref": "Landy & Sigall (1974) — Beauté vs note d'essai", "article": None}],
        [{"d": "Recrutement", "ex": "Le diplôme prestigieux halo toutes les compétences."}, {"d": "École", "ex": "La note de rédaction influence la note de sciences."}, {"d": "Marketing", "ex": "Le célebrité endorser : confiance transférée."}, {"d": "Justice", "ex": "Accusé attirant : peine plus légère (Stewart 1980)."}],
        ["Évaluations structurées, critères explicites et séparés", "Anonymisation des dossiers (CV anonymes)", "Évaluateurs multiples indépendants", "Noter item par item avant impression globale"],
        ["b_autocomplaisance", "b_confirmation", "b_disponibilite"], "halo",
        [("Trait positif observé", "#fbbf24"), ("Généralisation", "#a78bfa"), ("Toutes dimensions ↑", "#22d3ee"), ("Évaluation biaisée", "#10b981")],
        None, "thorndike1920", "c_bigfive"),
    _bias("b_surconfiance", "Biais de surconfiance", "On se croit meilleurs qu'on ne l'est.", "Lichtenstein & Fischhoff (1977)", 1977,
        "Surestimation systématique de la précision de ses connaissances, de sa performance ou de ses prédictions : la confiance déclarée excède l'exactitude réelle (overestimation, overplacement, overprecision).",
        "Projets sur-optimistes (planning fallacy), trading perdant, diagnostic médical trop sûr, engagement sans marge de sécurité.",
        ["90% de confiance pour 60% de réponses justes", "Chantier estimé 6 mois, durée réelle 14 (planning fallacy)", "93% des conducteurs se jugent au-dessus de la moyenne"],
        "Lichtenstein & Fischhoff (1977) : calibration des jugements de connaissance. Alpert & Raiffa (1982) : intervalles trop étroits. Moore & Healy (2008) : distinguent 3 formes de surconfiance. Kahneman : « planning fallacy » et « inside view ».",
        ["Confiance générée par la facilité (fluence)", "Biais de motivationnel (image de soi)", "Mémoire sélective des succès", "Absence de feedback immédiat"],
        [{"ref": "Lichtenstein & Fischhoff (1977) — Calibration", "article": None}, {"ref": "Moore & Healy (2008) — Trois surconfiances", "article": None}],
        [{"d": "Gestion de projet", "ex": "Underestimate systematically : planning fallacy."}, {"d": "Finance", "ex": "Traders fréquents = moins performants (Barber & Odean)."}, {"d": "Conduite", "ex": "Illusion de contrôle au volant."}, {"d": "Santé", "ex": "Diagnostic trop sûr : errer en médecine."}],
        ["Calibration par feedback : prédire, vérifier, ajuster", "Référence extérieure (outside view : taux de base de projets similaires)", "Pre-mortem (Klein)", "Intervalles plus larges et explicitement probabilistes"],
        ["b_dunning_kruger", "b_ancrage", "b_groupthink"], "mirror",
        [("Tâche prédiction", "#818cf8"), ("Confiance élevée", "#fbbf24"), ("Feedback décalé", "#f87171"), ("Sur/confiance", "#22d3ee")],
        "dunnkruger", None, "c_metacognition"),
    _bias("b_framing", "Effet de cadrage", "Le contenant change le contenu.", "Tversky & Kahneman (1981)", 1981,
        "Des formulations logiquement équivalentes d'un même problème produisent des préférences différentes : cadré en gains, on est réticent au risque ; cadré en pertes, on cherche le risque.",
        "Communication médicale (survie vs mortalité), marketing (90% sans gras vs 10% de gras), politique (chômage vs emploi).",
        ["« 90% de survie » rassure, « 10% de mortalité » inquiète", "« Viande 75% maigre » vend mieux que « 25% grasse »", "Programme médical : 200 sauvés (sûr) vs 600 morts (risqué)"],
        "Tversky & Kahneman (1981) : « Asian disease problem ». Levin et al. (1998) : typologie (risky choice, attribute, goal framing). Kühberger (1998) : méta-analyse (effet moyen d≈0.2-0.3).",
        ["Reformulation en termes de pertes active l'aversion aux pertes", "Référence (point de départ) détermine le domaine gain/perte", "Système 1 : évaluation affective du cadre", "Sensibilité marginale décroissante (prospect theory)"],
        [{"ref": "Tversky & Kahneman (1981) — Framing of decisions", "article": "tversky1974"}, {"ref": "Kühberger (1998) — Méta-analyse du framing", "article": None}],
        [{"d": "Médecine", "ex": "Le choix chirurgical dépend du framing survie/mortalité (McNeil 1982)."}, {"d": "Marketing", "ex": "« 95% sans OGM » vs « 5% avec »."}, {"d": "Finance", "ex": "Framing des fonds : performance vs perte."}, {"d": "Politique", "ex": "« Impôt sur les successions » vs « taxe sur la mort »."}],
        ["Reformuler chaque option dans les deux cadres (gain ET perte)", "Se demander : quelle est l'information identique derrière ?", "Décider selon un critère fixé avant le cadrage", "Utiliser des tableaux de fréquences naturelles (Gigerenzer)"],
        ["b_ancrage", "b_statu_quo", "b_survivant"], "scale",
        [("Options équivalentes", "#818cf8"), ("Cadrage gain/perte", "#fbbf24"), ("Préférence inversée", "#a78bfa"), ("Décision biaisée", "#f87171")],
        "framing", "tversky1974", "c_dissonance"),
    _bias("b_statu_quo", "Biais de statu quo", "Le confort du connu coûte cher.", "Samuelson & Zeckhauser (1988)", 1988,
        "Préférence disproportionnée pour la situation actuelle : tout changement est perçu comme une perte (aversion aux pertes) et le défaut devient un choix par défaut.",
        "Épargne (fonds par défaut), abonnements non résiliés, politique (immobilisme), santé (non-adhésion au traitement).",
        ["Stickiness des plans d'épargne par défaut (Madrian & Shea 2001)", "On garde son assurance malgré une meilleure offre", "Résistance au changement organisationnel"],
        "Samuelson & Zeckhauser (1988) : études expérimentales et terrain (choix de fonds de pension, lits d'hôpitaux). Madrian & Shea (2001) : auto-enrollment. Kahneman, Knetsch & Thaler (1991) : endowment effect.",
        ["Changement = pertes saillantes, continuité = gains implicites", "Coût cognitif de l'évaluation des alternatives", "Regret anticipé plus fort pour l'action", "Attachement au possédé (endowment)"],
        [{"ref": "Samuelson & Zeckhauser (1988) — Status quo bias", "article": None}, {"ref": "Madrian & Shea (2001) — Default 401(k)", "article": None}],
        [{"d": "Épargne", "ex": "Auto-enrollment : la participation explose."}, {"d": "Tech", "ex": "Paramètres par défaut jamais modifiés."}, {"d": "Santé", "ex": "Don d'organes : opt-in vs opt-out (Johnson & Goldstein 2003)."}, {"d": "Business", "ex": "Kodak reste sur le film."}],
        ["Fixer des dates de revue obligatoires des choix", "Faire du meilleur choix le défaut (nudge)", "Chiffrer le coût de l'inaction", "Décisions par lots pour réduire la friction"],
        ["b_sunk_cost", "b_framing", "b_ancrage"], "clock",
        [("Situation actuelle", "#818cf8"), ("Alternatives équivalentes", "#94a3b8"), ("Friction du changement", "#fbbf24"), ("Statu quo maintenu", "#f87171")],
        None, None, "c_dissonance"),
    _bias("b_sunk_cost", "Coûts irrécupérables", "On persiste parce qu'on a déjà investi.", "Arkes & Blumer (1985)", 1985,
        "Continuer un projet ou une action en fonction des ressources déjà engagées (argent, temps, effort) plutôt que des bénéfices futurs attendus — pourtant seuls les coûts/opportunités futurs comptent rationnellement.",
        "Projets en échec prolongés (Concorde), relations toxiques, études mal choisies « puisque j'ai déjà fait 3 ans ».",
        ["On finit un film ennuyeux « puisqu'on a payé »", "On continue de réparer une vieille voiture", "Guerres prolongées « pour ne pas avoir perdu les sacrifices »"],
        "Arkes & Blumer (1985) : 8 expériences (tickets de saison, réacteurs). Staw (1976) : escalation of commitment. Garland (1990) : la « décomposition » du coût saisi renforce l'effet.",
        ["Le coût passé est saisi comme à « récupérer »", "Justification de soi (je ne peux pas avoir perdu)", "Responsabilité perçue → escalade (Staw)", "Aversion au regret anticipé"],
        [{"ref": "Arkes & Blumer (1985) — Sunk cost effect", "article": None}, {"ref": "Staw (1976) — Escalation of commitment", "article": None}],
        [{"d": "Business", "ex": "Effet Concorde : poursuite d'un projet déficitaire."}, {"d": "Personnel", "ex": "Rester dans un métier « par rapport aux années passées »."}, {"d": "Gaming", "ex": "Loot boxes : continuer pour « rentabiliser »."}, {"d": "IT", "ex": "Refonte d'un système inefficace poursuivie."}],
        ["Se demander : « si je recommençais à zéro, que ferais-je ? »", "Séparer coût passé (irrécupérable) et bénéfices futurs", "Fixer des seuils d'abandon AVANT de commencer", "Révision par une personne non impliquée"],
        ["b_statu_quo", "b_surconfiance", "b_groupthink"], "clock",
        [("Investissement passé", "#fbbf24"), ("Perspective future négative", "#f87171"), ("Justification de soi", "#a78bfa"), ("Persistance irrationnelle", "#f87171")],
        "sunkcost", None, "c_dissonance"),
    _bias("b_negativite", "Biais de négativité", "Le négatif pèse plus lourd que le positif.", "Baumeister et al. (2001)", 2001,
        "Les événements, informations et émotions négatifs ont un impact psychologique plus fort que les positifs équivalents (« bad is stronger than good »).",
        "Relations (ratio 5:1 de Gottman), feedback managérial, réputation en ligne, couverture médiatique.",
        ["Un commentaire négatif annule plusieurs positifs", "L'e-esthetic d'un produit plombée par 1 avis 1★", "Les pertes pèsent ~2x plus que les gains (aversion aux pertes)"],
        "Baumeister et al. (2001) : revue « Bad is stronger than good ». Kahneman & Tversky (1979) : pertes ≈ 2× gains. Rozin & Royzman (2001) : mécanismes (negativity dominance, contágion). Gottman : ratio magique 5:1.",
        ["Attention orientée vers la menace (survie)", "Encodage plus profond du négatif", "Généralisation rapide du mauvais", "Contagion : le négatif « tache » (mélange)"],
        [{"ref": "Baumeister et al. (2001) — Bad is stronger than good", "article": None}, {"ref": "Rozin & Royzman (2001) — Negativity bias", "article": None}],
        [{"d": "Management", "ex": "Feedback : il faut 5 positifs pour 1 négatif."}, {"d": "Couple", "ex": "Ratio de Gottman : 5 interactions positives / 1 négative."}, {"d": "Presse", "ex": "Biais de la mauvaise nouvelle."}, {"d": "e-commerce", "ex": "Gestion des avis négatifs."}],
        ["Ratio feedback : viser 5:1 (positif : correctif)", "Formuler les correctifs avec une piste d'action", "Journal des réussites (contre-poids attentionnel)", "Reformulation en gains (framing positif)"],
        ["b_disponibilite", "b_framing", "b_haloeffet"], "scale",
        [("Événements ± équivalents", "#818cf8"), ("Encodage asymétrique", "#f87171"), ("Poids négatif x2", "#a78bfa"), ("Bilan faussé", "#22d3ee")],
        None, None, "c_dissonance"),
    _bias("b_autocomplaisance", "Biais d'auto-complaisance", "Les succès sont à moi, les échecs au hasard.", "Miller & Ross (1975)", 1975,
        "Attribution causale asymétrique : on s'attribute la responsabilité des succès (causes internes) et on impute les échecs à des facteurs externes (chance, difficulté de la tâche, les autres).",
        "Apprentissage (pas de révision si « malchance »), management (le succès = moi, l'échec = l'équipe), sport, conduite.",
        ["« J'ai réussi grâce à mes compétences, j'ai échoué à cause de la chance »", "L'étudiant attribue la note au correcteur", "Le chauffeur : « les autres conduisent mal »"],
        "Miller & Ross (1975) : revue fondatrice. Zuckerman (1979) : méta-analyse du biais d'attribution. Mezulis et al. (2004) : prévalence cross-culturelle (forte aux USA, plus faible en Asie).",
        ["Protection de l'estime de soi", "Attente de succès → attribution interne des confirmations", "Salience : nos intentions sont visibles, les circonstances le sont moins", "Acteur-observateur : asymétrie de perspective"],
        [{"ref": "Miller & Ross (1975) — Self-serving biases", "article": None}, {"ref": "Mezulis et al. (2004) — Méta-analyse", "article": None}],
        [{"d": "Éducation", "ex": "L'échec à l'examen = « le prof est injuste »."}, {"d": "Entreprise", "ex": "Bonus individuels, pertes collectives."}, {"d": "Sport", "ex": "Victoire = talent ; défaite = arbitre."}, {"d": "Conduite", "ex": "On se juge « prudent », les autres « dangereux »."}],
        ["Feedback 360° (plusieurs perspectives)", "Analyser les échecs comme les succès (post-mortem neutre)", "Attributions vérifiables : données avant explications", "Culture de la faute sans blâme (blameless postmortem)"],
        ["b_dunning_kruger", "b_surconfiance", "b_groupthink"], "mirror",
        [("Résultat obtenu", "#818cf8"), ("Succès → moi", "#10b981"), ("Échec → contexte", "#f87171"), ("Estime préservée", "#fbbf24")],
        None, None, "c_bigfive"),
    _bias("b_groupthink", "Pensée de groupe", "L'harmonie du groupe tue la qualité de la décision.", "Janis (1972)", 1972,
        "Priorité donnée au consensus et à la cohésion au détriment de l'évaluation réaliste des alternatives : autocensure, illusion d'invulnérabilité, pression sur les dissidents.",
        "Décisions politiques (baie des Cochons, Challenger), réunions d'entreprise, jury, comités de direction.",
        ["Baie des Cochons (1961) : personne n'exprime ses doutes", "Challenger (1986) : les alertes ingénieurs écartées", "Réunion : le silence vaut accord"],
        "Janis (1972) « Victims of Groupthink » : analyse de fiascos politiques. Esser (1998) : revue et modèle. Baron (2005) : reformulation en « biais de consensus enhardi » (concurrence d'opinions).",
        ["Cohésion + leader directif + isolement informationnel", "Illusion d'invulnérabilité et d'unanimité", "Autocensure (doute ≠ exprimé)", "Mindguards (auto-gardiens du consensus)"],
        [{"ref": "Janis (1972) — Victims of Groupthink", "article": None}, {"ref": "Esser (1998) — Revue critique", "article": None}],
        [{"d": "Politique", "ex": "Baie des Cochons, Vietnam."}, {"d": "Aérospatial", "ex": "Challenger, Columbia."}, {"d": "Entreprise", "ex": "Lancement produit sans voix critiques."}, {"d": "Jury", "ex": "Polarisation de groupe après délibération."}],
        ["Désigner un avocat du diable (critique mandatée)", "Avis écrits et individuels AVANT la réunion", "Leader exprime son opinion en dernier", "Secondes réunions de confirmation (Wise 2003)"],
        ["b_surconfiance", "b_autocomplaisance", "b_statu_quo"], "bubble",
        [("Cohésion forte", "#10b981"), ("Pression au consensus", "#fbbf24"), ("Autocensure", "#a78bfa"), ("Décision dégradée", "#f87171")],
        None, None, "c_dissonance"),
    _bias("b_survivant", "Biais du survivant", "On n'entend que les survivants.", "Wald (1943)", 1943,
        "Erreur logique consistant à se concentrer sur les éléments ayant « survécu » à un processus de sélection, en négligeant ceux qui ont disparu (données manquantes invisibles).",
        "Histoires de succès entrepreneurial, conseils d'investissement, bâtiments de guerre, influenceurs « qui ont réussi ».",
        ["Wald : blinder les avions LÀ OÙ il n'y a PAS de traces d'impacts", "« Bill Gates a quitté les études » (et les milliers qui ont échoué ?)", "Les fonds qui ont survécu 10 ans semblent brillants"],
        "Wald (1943) : analyse du blindage des bombardiers (survivance visuelle des impacts). Brown (1957) : « survivorship psychology ». Malkiel (1973) : biais de survie dans les fonds d'investissement.",
        ["Échantillon biaisé par la sélection (les perdants sont sortis)", "Visibilité asymétrique (médias, mémoire)", "Confusion correlation-causation sur données filtrées", "Négation du dénominateur (combien ont essayé ?)"],
        [{"ref": "Wald (1943) — A method of estimating plane vulnerability", "article": None}, {"ref": "Malkiel (1973) — A Random Walk Down Wall Street", "article": None}],
        [{"d": "Finance", "ex": "Performance des fonds : les fermés disparaissent des stats."}, {"d": "Entrepreneuriat", "ex": "Success stories vs cimetière des startups."}, {"d": "Santé", "ex": "« Mon grand-père fumait et a fait 95 ans »."}, {"d": "Éducation", "ex": "Les méthodes des « grands hommes » (sans les échecs)."}],
        ["Se demander : qui a DISPARU de l'échantillon ?", "Chercher le taux de base (dénominateur complet)", "Données de cohortes plutôt que de cas célèbres", "Méfiance face aux best-sellers de « méthodes »"],
        ["b_disponibilite", "b_confirmation", "b_surconfiance"], "media",
        [("Processus de sélection", "#818cf8"), ("Survivants visibles", "#10b981"), ("Perdus invisibles", "#f87171"), ("Conclusion biaisée", "#fbbf24")],
        None, None, "c_metacognition"),
    _bias("b_recence", "Biais de récence", "Le dernier pèse plus que l'ensemble.", "Murdock (1962)", 1962,
        "Dans le rappel libre et le jugement, les éléments les plus récents sont mieux mémorisés et pèsent plus dans la décision (position sérielle), aux dépens de l'information plus ancienne ou centrale.",
        "Entretiens (dernier candidat avant la pause), notation de performance (dernier trimestre), audiologie de réunions.",
        ["On se souvient surtout de la fin d'une présentation", "Le candidat passé en dernier est favorisé", "On juge une année sur son dernier mois"],
        "Murdock (1962) : courbe de position sérielle (rappel libre). Glanzer & Cunitz (1966) : dissociation primauté/récence (tâche distractive supprime la récence). Atkinson & Shiffrin (1968) : modèle MDT.",
        ["Récence : items encore en mémoire de travail", "Primauté : premiers items plus répétés/encodés", "Effet de bulle : le milieu souffre", "Application décisionnelle : le dernier événement pèse (anchoring temporel)"],
        [{"ref": "Murdock (1962) — Serial position effect", "article": None}, {"ref": "Glanzer & Cunitz (1966) — Two storage", "article": None}],
        [{"d": "Recrutement", "ex": "Ordre de passage des candidats (effet de contraste)."}, {"d": "Management", "ex": "Entretien annuel basé sur les 6 dernières semaines."}, {"d": "Presse", "ex": "Couverture du « dernier » événement vs tendance longue."}, {"d": "Marketing", "ex": "Placement en fin de liste (effet d'ordre)."}],
        ["Notation continue plutôt que retrospective", "Randomiser l'ordre (candidats, évaluations)", "Structurer les présentations (début & fin forts)", "Référentiel écrit consulté pendant le jugement"],
        ["b_disponibilite", "b_ancrage", "b_haloeffet"], "line",
        [("Items consécutifs", "#818cf8"), ("Mémoire de travail", "#a78bfa"), ("Derniers saillants", "#22d3ee"), ("Rappel asymétrique", "#10b981")],
        None, None, "c_metacognition"),
    _bias("b_illusion_validite", "Illusion de validité", "Le pattern perçu semble prédictif.", "Kahneman & Tversky (1973)", 1973,
        "Confiance excessive dans la capacité prédictive d'un pattern perçu dans les données (cohérence interne, bonne histoire), alors que la validité prédictive réelle est faible.",
        "Recrutement (entretien classique vs tests validés), prédictions financières, projections d'entreprise, pronostics.",
        ["L'entretien non structuré prédit mal (Schmidt & Hunter)", "L'analyste « voit » une tendance dans du bruit", "Le business plan convaincant par sa cohérence"],
        "Kahneman & Tversky (1973) : prédiction par représentativité (Tom W.). Meehl (1954) : formule clinique vs actuarielle. Schmidt & Hunter (1998) : validité des méthodes de sélection (entretien non structuré r≈0.38 vs tests GMA r≈0.51).",
        ["Substitution : « est-ce cohérent ? » remplace « est-ce prédictif ? »", "Insensibilité à la qualité des données (bruit perçu comme signal)", "Narrativité : bonne histoire = bonne prédiction", "Ignorance des taux de base et de la régression"],
        [{"ref": "Kahneman & Tversky (1973) — On the psychology of prediction", "article": "tversky1974"}, {"ref": "Meehl (1954) — Clinical vs statistical prediction", "article": None}],
        [{"d": "Recrutement", "ex": "Entretiens structurés > impression d'entretien."}, {"d": "Finance", "ex": "Prédiction des analystes vs indice passif."}, {"d": "Sport", "ex": "Scouting intuitif vs data-analytics (Moneyball)."}, {"d": "Consulting", "ex": "Projets convaincants par storytelling."}],
        ["Utiliser des modèles actuariels quand ils existent", "Valider la prédiction sur des données tenues à l'écart", "Structurer les décisions (rubrics, scoring)", "Demander : quelle est la validité prédictive documentée ?"],
        ["b_surconfiance", "b_survivante" if False else "b_survivant", "b_ancrage"], "line",
        [("Pattern perçu", "#818cf8"), ("Histoire cohérente", "#a78bfa"), ("Confiance élevée", "#fbbf24"), ("Validité réelle faible", "#f87171")],
        None, "tversky1974", "c_metacognition"),
]
# fix typo id ref
for _b in BIASES:
    _b["detail"]["related"] = [r if r != "b_survivante" else "b_survivant" for r in _b["detail"]["related"]]
    _b["detail"]["related"] = [r if r != "b_haloeffet" else "b_haloeffet" for r in _b["detail"]["related"]]

# ─────────────── GRANDS CONCEPTS (13) ───────────────
def _concept(id, name, tagline, author, year, definition, impact, examples, histoire, mecanismes, applications, debias, svg, steps, sim, tl, results=None, doi=None):
    return {"id": id, "cat": "concept", "name": name, "tagline": tagline, "author": author, "year": year,
            "definition": definition, "impact": impact, "examples": examples,
            "detail": {"histoire": histoire, "mecanismes": mecanismes,
                       "experiences": [{"ref": f"{author} ({year}) — travail fondateur", "article": None}],
                       "applications": applications, "debias": debias, "related": [],
                       "timeline": TIMELINES.get(tl, []), "svg": art_svg(svg), "schema": schema_svg(steps, title="Modèle"),
                       "simulation": sim, "article": None,
                       "results": results or {"desc": f"Résultats clés : {name}", "stats": [f"Effet documenté depuis {year}", "Répliqué dans de nombreuses études"]},
                       "doi": doi, "seminal": f"{author} ({year})"}}

CONCEPTS = [
    _concept("c_classique", "Conditionnement classique", "Le neutre devient signal.", "Pavlov", 1903,
        "Apprentissage associatif : un stimulus neutre (cloche), associé répétitivement à un stimulus inconditionnel (nourriture), finit par déclencher seul la réponse (salivation).",
        "Phobies et leur traitement (exposition), aversions alimentaires, marketing (associer marque/émotion), addiction (signaux de consommation).",
        ["L'alarme de téléphone déclenche du stress", "Publicité : musique + produit = émotion conditionnée", "Exposition graduée désamorce les phobies"],
        "Pavlov (1903-1927) : travaux sur la digestion (Nobel 1904). Watson & Rayner (1920) : petit Albert. Rescorla & Wagner (1972) : modèle formel de la contingence.",
        ["Acquisition : association CS-US répétée", "Contingence et saillance (Rescorla)", "Extinction : CS seul → réponse décline", "Rétablissement spontané (l'extinction n'efface pas)"],
        [{"d": "Clinique", "ex": "Thérapies d'exposition pour phobies et PTSD."}, {"d": "Marketing", "ex": "Jingles et packaging conditionnants."}, {"d": "Éducation", "ex": "Rituels de classe (signal → comportement)."}, {"d": "Addictologie", "ex": "Signaux de consommation → craving."}],
        ["Varier les contextes d'apprentissage (généralisation contrôlée)", "Renforcement intermittent pour la robustesse", "Expliciter l'association pour limiter les conditionnements parasites"],
        "pavlov", [("Stimulus neutre", "#94a3b8"), ("Association CS-US", "#fbbf24"), ("Nouveau signal", "#22d3ee"), ("Réponse apprise", "#10b981")],
        None, "c_classique", {"desc": "Courbe d'acquisition et d'extinction typique", "stats": ["Acquisition en 5-10 essais typiques", "Extinction 2x plus lente que l'acquisition"]}, "10.1037/h0054651"),
    _concept("c_operant", "Conditionnement opérant", "Le comportement est sculpté par ses conséquences.", "Skinner", 1938,
        "Mode d'apprentissage où le comportement est modulé par ses conséquences : renforcement (augmente) ou punition (diminue), positifs (ajout) ou négatifs (retrait).",
        "Éducation (renforcement positif), thérapies comportementales, gamification, management, addiction (renforcement variable).",
        ["Renforcement variable des réseaux sociaux (scroll infini)", "Token economy en psychiatrie", "Économie comportementale des nudges"],
        "Thorndike (1898) : loi de l'effet. Skinner (1938) : opérant, programmes de renforcement (ratio/intervalles, fixes/variables). Ferster & Skinner (1957) : schedules.",
        ["Comportement → conséquence → probabilité modifiée", "Renforcement variable = très résistant à l'extinction", "Punition : efficace à court terme, effets secondaires", "Extinction et burst d'extinction"],
        [{"d": "Éducation", "ex": "Louanges descriptives vs punitions."}, {"d": "Tech", "ex": "Notifications variables (slot machine)."}, {"d": "Clinique", "ex": " token economy (sociétés thérapeutiques)."}, {"d": "Sport", "ex": "Renforcement des bons gestes."}],
        ["Préférer le renforcement positif à la punition", "Renforcer immédiatement et explicitement", "Programmer l'intermittence une fois acquis", "Éviter la punition physique (effets iatrogènes)"],
        "skinner", [("Comportement émis", "#818cf8"), ("Conséquence (±)", "#fbbf24"), ("Probabilité modifiée", "#22d3ee"), ("Apprentissage", "#10b981")],
        None, "c_operant", {"desc": "Performance selon le programme de renforcement", "stats": ["Variable ratio → plus résistant à l'extinction", "Réponse 5-10x supérieure vs renforcement fixe"]}, "10.1037/h0043668"),
    _concept("c_maslow", "Pyramide de Maslow", "On monte quand la base tient.", "Maslow", 1943,
        "Hiérarchisation motivationnelle en 5 niveaux : besoins physiologiques, sécurité, appartenance, estime, accomplissement — un niveau inférieur insatisfait domine la motivation.",
        "Management (QVT), éducation (climat scolaire), santé publique, orientation professionnelle.",
        ["Un salarié en insécurité (contrat) n'investit pas la créativité", "École : sécurité et appartenance avant performance", "Produits « d'accomplissement » (formations, sports)"],
        "Maslow (1943) « A Theory of Human Motivation ». Critiques : Wahba & Bridwell (1976) — faible validation empirique de la stricte hiérarchie ; Hofstede (1984) — biais culturel individualiste.",
        ["Prépotence relative des niveaux inférieurs", "Satisfaction → émergence du niveau suivant", "Rareté des atteintes simultanées", "Hiérarchie souple selon contexte et culture"],
        [{"d": "Management", "ex": "Sécurité de l'emploi avant innovation."}, {"d": "Éducation", "ex": "Petit-déjeuner avant apprentissage."}, {"d": "Design produit", "ex": "Usabilité avant fonctionnalités avancées."}, {"d": "Santé", "ex": "Soins de base avant rééducation cognitive."}],
        ["Diagnostiquer le niveau dominant avant d'intervenir", "Ne pas exiger le sommet si la base est fragile", "Réévaluer régulièrement (les besoins évoluent)"],
        None, [("Besoins de base", "#f87171"), ("Sécurité/Appartenance", "#fbbf24"), ("Estime", "#22d3ee"), ("Accomplissement", "#10b981")],
        None, None, {"desc": "Hiérarchie et prépotence des besoins", "stats": ["Validation empirique partielle (Wahba & Bridwell 1976)", "Utilité heuristique reconnue en management"]}, "10.1037/h0054346"),
    _concept("c_autodetermination", "Théorie de l'autodétermination", "Autonomie, compétence, relation.", "Deci & Ryan", 1985,
        "Théorie de la motivation : trois besoins psychologiques fondamentaux (autonomie, compétence, relation à autrui) ; la motivation intrinsèque s'épanouit quand ils sont nourris.",
        "Éducation (classe, évaluation), travail (engagement), sport, jeux vidéo, santé (adhésion thérapeutique).",
        ["Récompenses extrinsèques peuvent éroder l'intrinsèque (surrexertion justification)", "Feedback informatif renforce la compétence", "Choix offerts → autonomie perçue"],
        "Deci (1971) : effet des récompenses. Deci & Ryan (1985) : SDT formelle. Deci, Koestner & Ryan (1999) : méta-analyse des récompenses. Ryan & Deci (2000) : synthèse.",
        ["Besoins psychologiques → motivation (intrinsèque > identifiée > introjectée > externe)", "Événements sociaux nourrissent/frustrent les besoins", "Internalisation progressive des régulations", "Effet de sapience des récompenses tangibles"],
        [{"d": "Éducation", "ex": "Choix de sujets, feedback descriptif."}, {"d": "Management", "ex": "Autonomie sur les méthodes, objectifs partagés."}, {"d": "Santé", "ex": "Motivational interviewing."}, {"d": "Jeux", "ex": "Maîtrise progresser (compétence) + liberté (autonomie)."}],
        ["Offrir du choix dans le COMMENT", "Feedback orienté tâche (pas jugement de la personne)", "Minimiser les contrôles tangibles et deadlines arbitraires"],
        None, [("Environnement social", "#818cf8"), ("Besoins nourris", "#22d3ee"), ("Motivation intrinsèque", "#10b981"), ("Engagement durable", "#fbbf24")],
        None, None, {"desc": "Méta-analyse Deci, Koestner & Ryan (1999) : 128 études", "stats": ["Récompenses tangibles attendues ↓ motivation intrinsèque (d≈-0.36)", "Feedback positif ↑ (d≈+0.30)"]}, "10.1037/0003-066X.55.1.68"),
    _concept("c_flow", "État de Flow", "Défi et compétence en équilibre.", "Csikszentmihalyi", 1975,
        "État d'immersion optimale où défi et compétence s'équilibrent, avec absorption attentionnelle totale, perte du sentiment du temps et expérience autotélique.",
        "Sport de haut niveau, travail profond (deep work), design de jeux vidéo, éducation (défi ajusté).",
        ["Musicien absorbé, temps qui disparaît", "Game design : courbe de difficulté progressive", "Travail : tâches trop faciles = ennui, trop dures = anxiété"],
        "Csikszentmihalyi (1975) : « Beyond Boredom and Anxiety » (expérience échantillonnage). Nakamura & Csikszentmihalyi (2009) : modèle affiné. Peifer & Engeser (2021) : revue des mesures.",
        ["Équilibre défi/compétence (canal de flow)", "Buts clairs + feedback immédiat", "Fusion action-conscience (perte de métacognition)", "Sensation de contrôle + perte du temps"],
        [{"d": "Sport", "ex": "État de performance optimale (zone)."}, {"d": "Design", "ex": "Difficulté ajustée (DynamiDifficulty)."}, {"d": "Travail", "ex": "Blocs de deep work sans interruption."}, {"d": "Éducation", "ex": "Défis gradués (ZPD + flow)."}],
        ["Ajuster le défi à la compétence (notamment +10%)", "Supprimer les interruptions (notifications)", "Buts clairs et feedback immédiat", "Protéger le temps long (deep work)"],
        "quadrant", [("Tâche proposée", "#818cf8"), ("Défi ↔ compétence", "#22d3ee"), ("Absorption", "#a78bfa"), ("Flow", "#10b981")],
        None, "c_flow", {"desc": "Modèle canalisé : zones anxiété/ennui/flow", "stats": ["Expérience échantillonnage : flow ~10-20% du temps éveillé", "Corrélé avec bien-être et performance"]}, "10.1037/0003-066X.55.1.68"),
    _concept("c_attachement", "Théorie de l'attachement", "La base sécure permet d'explorer.", "Bowlby", 1969,
        "Système comportemental d'attachement : le jeune cherche la proximité d'une figure de care en cas de menace ; la qualité de la réponse façonne un style (sécurisé, anxieux, évitant, désorganisé).",
        "Clinique enfant et adulte, parentalité, relations amoureuses, soin (alliance thérapeutique), crèche et école.",
        ["Enfant qui explore puis revient vérifier sa base", "Styles adultes : anxious → sur-activation ; évitant → désactivation", "Caregiving en crèche : référent stable"],
        "Bowlby (1944-1969) : 44 voleurs, volume I. Harlow (1958) : singes. Ainsworth (1978) : Strange Situation. Main & Solomon (1986) : désorganisé. Hazan & Shaver (1987) : adulte.",
        ["Signal de menace → activation du système d'attachement", "Réponse du caregiver → internalisation (modèle interne opérant)", "Styles : sécure / anxieux / évitant / désorganisé", "Continuité (mais modifiable) des modèles internes"],
        [{"d": "Clinique", "ex": "Thérapie attachement-informed, parent-infant psychothérapie."}, {"d": "Crèche/école", "ex": "Référent secure, rituels de séparation."}, {"d": "Couple", "ex": "Emotionally Focused Therapy (Johnson)."}, {"d": "RH", "ex": "Leadership secure-base (Kohlrieser)."}],
        ["Répondre de façon contingente et prévisible", "Stabilité des référents chez le jeune enfant", "Travail sur les modèles internes à l'âge adulte (ECT)"],
        "waves", [("Menace/stress", "#f87171"), ("Signal d'attachement", "#fbbf24"), ("Réponse du caregiver", "#22d3ee"), ("Modèle interne", "#10b981")],
        None, "c_attachement", {"desc": "Distribution des styles (Strange Situation, USA)", "stats": ["Sécurisé ~65%, évitant ~21%, anxieux ~14%", "Désorganisé : 15% (80% en populations à risque)"]}, "10.1037/h0043668"),
    _concept("c_resilience", "Résilience", "Pas une armure : un processus.", "Rutter / Cyrulnik", 1979,
        "Processus dynamique d'adaptation positive face à l'adversité significative, mobilisant des facteurs de protection individuels, familiaux et communautaires — et non un trait fixe.",
        "Clinique du trauma, éducation prioritaire, gestion de crise, prévention en entreprise (burn-out).",
        ["L'enfant « invincible » a souvent un adulte-référence stable", "Post-traumatic growth après épreuves", "Organisations résilientes (learning culture)"],
        "Rutter (1979) : protection vs vulnérabilité. Werner & Smith (1992) : Kauai Longitudinal (1/3 résilients). Masten (2001) : « ordinary magic ». Cyrulnik (1999) : popularisation francophone.",
        ["Exposition au risque + issue positive = résilience", "Facteurs : attachement sécure, sens de l'agentivité, soutien social", "Trajectoires non linéaires (rebond, résiduels)", "Ordinary magic : systèmes de base (Masten)"],
        [{"d": "Clinique", "ex": "Thérapies EMDR, TCC focus trauma."}, {"d": "Éducation", "ex": "Un adulte de référence par enfant."}, {"d": "Entreprise", "ex": "Résilience organisationnelle (post-mortem sans blâme)."}, {"d": "Santé publique", "ex": "Programmes de prévention précoce."}],
        ["Cultiver les facteurs de protection (pas seulement réduire les risques)", "Sens de l'agentivité : offrir des zones de contrôle", "Soutien social comme levier principal", "Narration de sens (Cyrulnik)"],
        None, [("Adversité", "#f87171"), ("Facteurs de protection", "#22d3ee"), ("Adaptation", "#10b981"), ("Croissance", "#fbbf24")],
        None, "c_resilience", {"desc": "Kauai Study : 1/3 des enfants à haut risque développent bien", "stats": ["Prédicteur n°1 : relation stable avec un adulte", "Résilience modifiable (interventions efficaces)"]}, None),
    _concept("c_growth", "Growth Mindset", "Le talent se cultive.", "Dweck", 1988,
        "Croyance que les capacités (intelligence, talent) sont malléables par l'effort et les stratégies (théorie incrémentale), vs vision fixe (entity theory).",
        "Éducation (feedback sur le processus), management (culture d'apprentissage), sport, neuro-réhabilitation.",
        ["Élève « je suis nul en maths » vs « pas encore »", "Feedback « ton effort a payé » vs « tu es doué »", "Entreprises learning-oriented (Microsoft Nadella)"],
        "Dweck (1988-1999) : théories implicites. Blackwell, Trzesniewski & Dweck (2007) : trajectoires scolaires. Yeager et al. (2019) : étude nationale US (N=12 490), effets modestes mais réels (g≈0.1). Sisk et al. (2018) : méta-analyse nuancée.",
        ["Croyance incrémentale → persistance face à l'échec", "Feedback sur processus > sur la personne", "Neuronal : plasticité comme métaphore opérante", "Modération : contexte pédagogique crucial"],
        [{"d": "École", "ex": "Le pouvoir du « pas encore » (not yet)."}, {"d": "Management", "ex": "Feedback développemental, culture d'apprentissage."}, {"d": "Sport", "ex": "Coaching orienté progression."}, {"d": "Parentalité", "ex": "Louer la stratégie, pas le talent."}],
        ["Louer l'effort et la stratégie, pas le trait", "Encadrer l'échec comme information", "Éviter les interventions « mindset-only » sans changement de contexte", "Attention : ne pas masquer les inégalités structurelles"],
        None, [("Croyance incrémentale", "#818cf8"), ("Effout + stratégie", "#22d3ee"), ("Persistance", "#10b981"), ("Progression", "#fbbf24")],
        None, "c_growth", {"desc": "Yeager et al. (2019) : National Study of Learning Mindsets", "stats": ["GPA : g≈0.10 pour élèves à bas revenus", "Effets modestes mais répliqués à grande échelle"]}, "10.1037/a0012831"),
    _concept("c_charge", "Charge cognitive", "La tête n'a pas de RAM infinie.", "Sweller", 1988,
        "Théorie de la charge cognitive : la mémoire de travail est limitée ; l'apprentissage dépend de la gestion des charges intrinsèque (complexité), extrinsèque (parasite) et germane (construction).",
        "Pédagogie (worked examples, séquencement), design d'interfaces (Bastien-Scapin), formation professionnelle, multimédia (Mayer).",
        ["Une slide surchargée sabote l'apprentissage", "Exemples résolus avant problèmes ouverts (novices)", "Split-attention : éviter de séparer l'info connexe"],
        "Sweller (1988) : CLT. Paas & Van Merriënboer (1994) : mesure subjective. Sweller, Ayres & Kalyuga (2011) : synthèse. Mayer (2009) : principes multimédias.",
        ["Charge intrinsèque : interactivité des éléments", "Charge extrinsèque : à réduire (design)", "Charge germane : à investir (schémas)", "Effet expertise inversé (les experts n'ont plus besoin d'exemples)"],
        [{"d": "Pédagogie", "ex": "Worked examples pour novices."}, {"d": "UX", "ex": "Réduire la charge extrinsèque des interfaces."}, {"d": "Multimédia", "ex": "Principe de contiguïté spatiale/temporelle."}, {"d": "Formation", "ex": "Séquencement complexité simple → intégrée."}],
        ["Réduire le superflu (principe de cohérence)", "Intégrer l'info connexe (pas de split-attention)", "Exemples résolus puis fading vers l'autonomie", "Mesurer la charge (Paas) pour calibrer"],
        None, [("Matériel pédagogique", "#818cf8"), ("Charges I/E/G", "#fbbf24"), ("MdT limitée", "#f87171"), ("Schémas en MLT", "#10b981")],
        None, "c_charge", {"desc": "Worked example effect : novices apprennent mieux avec exemples résolus", "stats": ["g≈0.5-0.8 pour worked examples (novices)", "Effet inversé chez experts (expertise reversal)"]}, "10.1037/0003-066X.43.6.483"),
    _concept("c_procrastination", "Procrastination", "Le « demain » qui coûte cher.", "Steel", 2007,
        "Retardement volontaire d'une tâche prévue malgré la conscience que ce délai sera nuisible — modélisée par Steel (2007) via motivation (attente × valeur) / (impulsivité × délai).",
        "Éducation (révisions), travail (deadlines), santé (différer les dépistages), finances (épargne).",
        ["Réviser la veille de l'examen", "Reporter le rendez-vous médical", "Snooze des tâches importantes mais vagues"],
        "Steel (2007) : « The Nature of Procrastination » (formule temporelle de motivation). Sirois & Pychyl (2013) : régulation émotionnelle à court terme. Ariely & Wertenbroch (2002) : deadlines pré-commitment.",
        ["Émotion de la tâche (aversion) > valeur future", "Hyperbolic discounting : le présent domine", "Auto-régulation défaillante (impulsivité)", "Honte entretient la boucle"],
        [{"d": "Éducation", "ex": "Deadlines intermédiaires auto-imposées."}, {"d": "Travail", "ex": "Découpage en micro-tâches concrètes."}, {"d": "Santé", "ex": "Rappels et pré-commitment (vaccins)."}, {"d": "Finance", "ex": "Épargne automatique (pay yourself first)."}],
        ["Découper la tâche en première micro-action de 5 min", "Pré-commitment : deadlines intermédiaires engageantes", "Réduire l'aversion : rendre le début agréable/facile", "Self-compassion plutôt que culpabilisation (Wohl 2010)"],
        "clock", [("Tâche aversive", "#f87171"), ("Émotion négative", "#fbbf24"), ("Évitement", "#a78bfa"), ("Soulagement court terme", "#22d3ee")],
        None, None, {"desc": "Formule de motivation temporelle (Steel 2007)", "stats": ["80-95% des étudiants procrastinent", "Corrélée négativement avec conscience (r≈-0.6)"]}, "10.1037/1089-2680.11.2.170"),
    _concept("c_dissonance", "Dissonance cognitive", "Nos actes dérangent nos croyances.", "Festinger", 1957,
        "Inconfort psychologique provoqué par l'incohérence entre cognitions (croyances, attitudes, comportements) ; motivation à la réduire en changeant croyances, attitudes ou en justifiant.",
        "Marketing (post-achat), santé (fumeurs), idéologies (prophétie déçue), éducation (effort justifié).",
        ["Fumeur : « ça aide à ne pas prendre de poids »", "Après achat : on valorise ce qu'on a acheté", "1$ vs 20$ : moins payé → plus convaincu"],
        "Festinger (1957). Festinger & Carlsmith (1959) : 1$/20$. Aronson & Mills (1959) : justification d'effort. Cooper & Fazio (1984) : nouveaux regards. Harmon-Jones : modèle d'action. van Veen (2009) : CCA.",
        ["Incohérence perçue → arousal désagréable (CCA)", "Réduction : changer croyance, ajouter cognition, minimiser", "Justification d'effort : je souffre donc ça vaut", "Conséquences aversives + responsabilité (Cooper & Fazio)"],
        [{"ref": ""}] if False else [{"d": "Marketing", "ex": "Reassurance post-achat (reviews request)."}, {"d": "Santé", "ex": "Effort justifié : plus on a souffert, plus on valorise."}, {"d": "Cults", "ex": "Prophétie déçue : foi renforcée (When Prophecy Fails)."}, {"d": "Organisation", "ex": "On défend son outil après y avoir investi."}],
        ["Accepter l'inconfort informationnel (débat contraint)", "Évaluer les décisions AVANT l'engagement irréversible", "Cultures d'entreprise tolérantes à la dissonance (blameless)"],
        "clock", [("Croyance A", "#818cf8"), ("Acte incompatible", "#fbbf24"), ("Inconfort (CCA)", "#f87171"), ("Rationalisation", "#22d3ee")],
        "framing", "c_dissonance", {"desc": "Festinger & Carlsmith (1959) : évaluation de la tâche ennuyeuse", "stats": ["Groupe 1$ : évaluation bien plus positive que 20$", "Effet répliqué des centaines de fois"]}, "10.1037/h0041593"),
    _concept("c_neuroplasticite", "Neuroplasticité", "Le cerveau se recâble par l'usage.", "Hebb", 1949,
        "Capacité du système nerveux à réorganiser ses connexions en fonction de l'expérience : renforcement (LTP), affaiblissement (LTD), néogenèse synaptique et, dans une moindre mesure, neurogenèse adulte.",
        "Rééducation post-AVC, apprentissage moteur et musical, douleur chronique (central sensitization), vieillissement cognitif.",
        ["Musiciens : cortex digital agrandi (Elbert 1995)", "Taxi drivers londoniens : hippocampe postérieur (Maguire 2000)", "Rééducation motrice : thérapie contraite (CIT)"],
        "Hebb (1949) : règle de Hebb. Maguire et al. (2000) : taxi drivers. Draganski et al. (2004) : juggling & matière grise. Merzenich : cortical plasticity.",
        ["« Cells that fire together wire together » (Hebb)", "Use it or lose it + use it and improve it (Kleim & Jones)", "Spécificité : l'entraînement moulé sur la tâche cible", "Salience & répétition : conditions de la plasticité"],
        [{"d": "Rééducation", "ex": "Thérapie par contrainte induite du mouvement (CIMT)."}, {"d": "Musique", "ex": "Pratique intensive → cartographie digitale."}, {"d": "Seniors", "ex": "Entraînement cognitif et activité physique."}, {"d": "Douleur", "ex": "Désensibilisation graduelle (neurotags)."}],
        ["Pratique répétée, spécifique, motivante (salience)", "Intensité suffisante mais fractionnée", "Sommeil : consolidation plastique", "Environnement enrichi > exercices isolés"],
        "neurons", [("Expérience répétée", "#818cf8"), ("Coactivation (Hebb)", "#22d3ee"), ("Renforcement synaptique", "#10b981"), ("Réorganisation corticale", "#fbbf24")],
        None, None, {"desc": "Maguire (2000) : hippocampe des taxi drivers londoniens", "stats": ["Volume postérieur ∝ années d'expérience", "Draganski (2004) : matière grise ↑ après 3 mois de jonglage"]}, "10.1038/35006003"),
    _concept("c_zpd", "Zone proximale de développement", "Apprendre avec un tutoriel au bon niveau.", "Vygotsky", 1934,
        "Écart entre ce que l'apprenant sait faire seul (développement effectif) et ce qu'il peut réaliser avec un étayage approprié (développement potentiel) — espace optimal d'enseignement.",
        "Pédagogie différenciée, tutoring pair-à-pair, adaptive learning, évaluation dynamique, parentalité.",
        ["Le maître donne des indices décroissants (scaffolding)", "Apps adaptatives : difficulté ajustée en temps réel", "Tutorat entre pairs : le tuteur consolide aussi"],
        "Vygotsky (1934) « Pensée et langage ». Traduction anglaise 1978 (« Mind in Society »). Bruner (1976) : scaffolding. Brown et al. (1985) : évaluation dynamique.",
        ["ZPD : espace entre seul et avec aide", "Étayage : soutien puis retrait progressif (fading)", "Langage intérieur comme outil de régulation", "Apprentissage socialement situé"],
        [{"d": "École", "ex": "Étayage puis autonomie (fading)."}, {"d": "Adaptive learning", "ex": "Khan Academy, Duolingo : zone ajustée."}, {"d": "Tutorat", "ex": "Pairs : double bénéfice (tuteur/tutoré)."}, {"d": "Parentalité", "ex": "Scaffolding langagier (Expansion)."}],
        ["Diagnostiquer le « seul » avant d'étayer", "Retirer l'aide dès que possible (fading)", "Cibler la zone : ni trop facile, ni hors d'atteinte"],
        None, [("Niveau actuel", "#818cf8"), ("Étayage ajusté", "#22d3ee"), ("Réussite assistée", "#fbbf24"), ("Nouveau niveau autonome", "#10b981")],
        None, None, {"desc": "Méta-analyses du tutoring : l'un des effets pédagogiques les plus robustes", "stats": ["Tutorat pair-à-pair : g≈0.4-0.6", "Effet supérieur aux classes réduites seules"]}, None),
]

# ─────────────── OUTILS (12) ───────────────
def _tool(id, name, tagline, subcat, definition, how_to, advantages, limitations, url, svg, sim=None):
    return {"id": id, "cat": "outil", "name": name, "tagline": tagline, "author": "", "year": "",
            "definition": definition, "impact": "", "examples": [],
            "detail": {"subcat": subcat, "histoire": f"{name} — {definition}", "mecanismes": how_to,
                       "experiences": [], "applications": [], "debias": limitations, "related": [],
                       "timeline": [], "svg": art_svg(svg), "schema": schema_svg([(s, "#22d3ee") for s in how_to[:3]], title="Utilisation"),
                       "simulation": sim, "article": None,
                       "results": {"desc": f"Points forts : {', '.join(advantages[:2])}", "stats": advantages},
                       "url": url}}

OUTILS = [
    _tool("o_stroop", "Test de Stroop", "Le conflit automatisme/contrôle en 2 minutes.", "paradigme",
        "Paradigme d'interférence : nommer la couleur d'encre de mots incongruents mesure le contrôle inhibiteur.",
        ["Présenter mots colorés (congruent/incongruent/neutre)", "Mesurer TR et erreurs par condition", "Calculer le coût d'interférence (ΔTR)"],
        ["Rapide, standardisé, sensibilise à l'inhibition", "Répliqué des milliers de fois", "Versions numériques gratuites (PsyToolkit)"],
        ["Sensible à la vitesse motrice (confondant)", "Effets faibles chez enfants très jeunes", "Pas spécifique : plusieurs processus contribuent"],
        "https://www.psytoolkit.org/experiment-library/stroop.html", "stroop", "stroop"),
    _tool("o_nback", "Tâche N-back", "La mise à jour de la mémoire de travail en temps réel.", "paradigme",
        "Tâche de mise à jour : indiquer si le stimulus actuel correspond à celui présenté N positions avant.",
        ["Paramétrer N (1, 2, 3)", "Présenter lettres/positions séquentiellement", "Compter hits, fausses alertes, calculer d'"],
        ["Charge de mise à jour graduée", "Corrélé avec le fluide (modérément)", "Adaptatif (dN-back)"],
        ["Validité de construit débattue (Huang 2025)", "Progrès = stratégies (chunking) parfois", "Fatigant, peu écologique"],
        "https://www.psytoolkit.org/experiment-library/nback.html", "nback", "nback"),
    _tool("o_wais4", "WAIS-IV", "Le QI de référence adulte, 4 indices.", "test_standard",
        "Échelle d'intelligence de Wechsler pour adultes : QI Total + 4 indices (CV, IRP, MT, Vitesse de traitement).",
        ["Passation standardisée par psychologue", "Cotation sous-tests → indices → QI", "Interprétation par profil (forces/faiblesses)"],
        ["Standard de référence, normes solides", "Profil multidimensionnel", "Très étudié cliniquement"],
        ["Payant, réservé aux psychologues", "Sensible à la culture et au niveau d'éducation", "QI ≠ potential (réification)"],
        "https://www.pearsonclinical.fr/wais-iv", "radar", None),
    _tool("o_mai", "MAI", "L'inventaire de conscience métacognitive.", "questionnaire",
        "Metacognitive Awareness Inventory (Schraw & Dennison, 1994) : 52 items, 2 facteurs — connaissances et régulation métacognitives.",
        ["Passation auto-rapportée (~15 min)", "Scoring : 8 sous-composantes", "Interprétation profil monitoring/contrôle"],
        ["Gratuit, très utilisé en éducation", "Deux dimensions théoriquement fondées", "Versions courtes validées"],
        ["Auto-rapport (biais de désirabilité)", "Corrélation modeste avec la performance réelle", "Pas un diagnostic"],
        "https://files.eric.ed.gov/fulltext/ED390191.pdf", "scale", None),
    _tool("o_bigfive", "Big Five / IPIP-NEO", "Les 5 grands traits en accès libre.", "questionnaire",
        "Modèle OCEAN (Ouverture, Conscienciosité, Extraversion, Agréabilité, Névrosisme) mesuré par des inventaires libres (IPIP) ou commerciaux (NEO-PI-R).",
        ["Questionnaire 50-120 items Likert 1-5", "Scoring par facteur (avec items inversés)", "Interprétation dimensionnelle (pas de typologie)"],
        ["Modèle le plus répliqué de la psychologie des traits", "Versions open source (IPIP)", "Prédictif de résultats académiques/pro (conscienciosité)"],
        ["Auto-rapport façonné par la désirabilité", "Descriptif, pas causal", "Attention aux réifications en recrutement"],
        "https://ipip.ori.org/", "radar", "bigfive"),
    _tool("o_likert", "Échelle de Likert", "Mesurer l'opinion, avec méthode.", "echelle",
        "Format de réponse ordinal (accord 1-7) pour attitudes ; apparié à des construits via échelles multi-items.",
        ["Rédiger items proches du construit", "Combiner 4-10 items (cohérence alpha)", "Attention aux items inversés"],
        ["Simple, rapide, flexible", "Analyses connues (alpha, omega)", "Standard des enquêtes"],
        ["Ordinal : prudence avec les moyennes", "Biais d'acquiescement (tout d'accord)", "Interprétation interculturelle délicate"],
        "https://www.qualtrics.com/experience-management/research/likert-scale/", "scale", None),
    _tool("o_iat", "IAT (associations implicites)", "Mesurer l'association automatique.", "implicite",
        "Implicit Association Test (Greenwald et al., 1998) : mesure la force d'association entre catégories via des latences de classification.",
        ["Classification rapide de stimuli (touches E/I)", "Comparaison des blocs associés/inversés", "Score D de latence différentielle"],
        ["Accès aux processus automatiques", "Version en ligne Harvard (démo publique)", "Très utilisé en recherche sociale"],
        ["Fiabilité test-retest modérée", "Valeur prédictive individuelle débattue", "Ne mesure pas « le préjugé » au sens littéral"],
        "https://implicit.harvard.edu/implicit/", "line", None),
    _tool("o_ems", "EMS (Young)", "Les schémas précoces inadaptés.", "questionnaire",
        "Young Schema Questionnaire : 18 schémas précoces inadaptés (abandon, défaut, droits…), versions 90/75/200 items.",
        ["Passation clinique guidée", "Scoring par schéma (seuils)", "Intégration à la thérapie des schémas"],
        ["Riche pour la thérapie des schémas", "Bien articulé au modèle de Young", "Versions courtes disponibles"],
        ["Long (200 items complet)", "Auto-rapport en détresse (biais)", "Nécessite une formation à la thérapie"],
        "https://www.schematherapy.com/", "scale", None),
    _tool("o_irmf", "IRMf", "Voir le cerveau penser (hémodynamique).", "neuroimagerie",
        "Imagerie par résonance magnétique fonctionnelle : mesure le signal BOLD (oxygénation) comme indice indirect d'activité neuronale.",
        ["Protocole bloc/événement", "Prétraitement (mouvement, dérive)", "Analyses GLM, cartes d'activation"],
        ["Résolution spatiale excellente (1-3 mm)", "Toute la voûte crânienne", "Designs complexes possibles"],
        ["Résolution temporelle faible (~2 s)", "Cher, contraignant (mouvement, bruit)", "BOLD ≠ décharge neuronale directe"],
        "https://surfer.nmr.mgh.harvard.edu/", "waves", None),
    _tool("o_eeg", "EEG / Potentiels évoqués", "La temporalité du cerveau en direct.", "neuroimagerie",
        "Électroencéphalographie : rythmes corticaux (delta, alpha, bêta, gamma) et PEs (P300, N170, ERN) avec une résolution milliseconde.",
        ["Casque d'électrodes (32-256)", "Filtrage + moyennage des essais (ERPs)", "Analyse temps-fréquence, connectivité"],
        ["Résolution temporelle imbattable (ms)", "Portable, silencieux, adapté aux enfants", "Coût modéré vs IRM"],
        ["Résolution spatiale faible (volume de conduction)", "Sensible aux artefacts (mouvement, sueur)", "Structures profondes invisibles"],
        "https://mne.tools/", "waves", "oddball"),
    _tool("o_prisma", "PRISMA 2020", "La rigueur des revues systématiques.", "protocole",
        "Guide de reporting des revues systématiques et méta-analyses : flux (27 items), diagramme, checklist.",
        ["Définir question PICO + critères", "Stratégie de recherche documentée (2+ bases)", "Diagramme de flux + checklist publiée"],
        ["Standard international des revues", "Reproductibilité accrue", "Gratuit, check-lists open access"],
        ["Exigeant en temps (2 évaluateurs)", "Ne garantit pas la qualité des études incluses", "À adapter aux revues narratives"],
        "https://www.prisma-statement.org/", "funnel", None),
    _tool("o_bastien", "Critères Bastien & Scapin", "L'ergonomie IHM à la française.", "grille",
        "18 critères ergonomiques (INRIA, 1993) : guidage, charge de travail, contrôle explicite, adaptabilité, gestion des erreurs, cohérence, signifiance des codes.",
        ["Inspection experte écran par écran", "Cotation de chaque critère (0-3 + exemples)", "Plan de correction priorisé"],
        ["Gratuit, francophone, opérationnel", "Couvre large (18 critères, 79 sous-critères)", "Bien adapté aux inspections rapides"],
        ["Inspection experte (pas usagers réels)", "Dépend de l'expertise de l'évaluateur", "À compléter par tests utilisateurs"],
        "https://hal.inria.fr/inria-00070012", "scale", None),
]

# ─────────────── SUB-CATEGORIES for tools ───────────────
TOOL_SUBCATS = [
    {"id": "all", "label": "Tous", "icon": "grid"},
    {"id": "questionnaire", "label": "Questionnaires", "icon": "clipboard-list"},
    {"id": "echelle", "label": "Échelles de mesure", "icon": "ruler"},
    {"id": "test_standard", "label": "Tests standardisés", "icon": "file-check"},
    {"id": "implicite", "label": "Tests implicites", "icon": "scan-eye"},
    {"id": "paradigme", "label": "Paradigmes expérimentaux", "icon": "flask-conical"},
    {"id": "neuroimagerie", "label": "Neuroimagerie", "icon": "brain"},
    {"id": "protocole", "label": "Protocoles recherche", "icon": "list-checks"},
    {"id": "grille", "label": "Grilles d'évaluation", "icon": "table"},
]

def get_all_concepts():
    return BIASES + CONCEPTS + OUTILS

def get_concept_detail(cid):
    for c in get_all_concepts():
        if c["id"] == cid:
            d = dict(c)
            d["detail"] = dict(c["detail"])
            d["detail"]["svg_html"] = c["detail"].get("svg", "")
            d["detail"]["schema_html"] = c["detail"].get("schema", "")
            return d
    return None

def get_article(aid):
    return SCIENTIFIC_ARTICLES.get(aid)

def get_timeline(cid):
    return TIMELINES.get(cid, [])
