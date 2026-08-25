/* ══════════ COGNITORIUM v8 — LABORATOIRE ══════════
   Moteur d'expériences : 21 simulations jouables, analyse statistique,
   projets validés, drag & drop, exports CSV/JSON et génération de code. */
window.LAB = {
  labView: 'list', labTemplates: [], labExperiments: [], labProjects: [],
  tmplSearch: '', tmplCat: 'all',
  labForm: {}, editingLabId: null,
  labSuggestions: {}, sugField: null, sugItems: [],
  play: null, analysis: null, analysisTab: 'Résumé',
  dragExpId: null, dropOver: false, treatmentProject: null, showCode: null,
  _charts: {}, _replayTimer: null,

  emptyLabForm() {
    return { title: '', category: '', hypothesis: '', iv: '', iv_levels: '', dv: '', dv_measure: '',
      design: '', population: '', n_sample: '', material: '', procedure: '', controls: '',
      ethics: 'Consentement éclairé, anonymat, droit de retrait', expected: '', analysis_plan: '',
      concepts: '', sim_type: '' };
  },

  async initLab() {
    this.labForm = this.emptyLabForm();
    try {
      const [t, s] = await Promise.all([fetch('/api/experiment-templates').then(r => r.json()), fetch('/api/lab-suggestions').then(r => r.json())]);
      this.labTemplates = t; this.labSuggestions = s;
    } catch (e) { console.error(e); }
    try { this.labExperiments = await fetch('/api/experiments').then(r => r.json()); } catch (e) {}
    document.addEventListener('keydown', (e) => this._keyDown(e));
  },

  // ─── Templates ───
  tmplCats() { return [...new Set(this.labTemplates.map(t => t.category))]; },
  labTemplatesFiltered() {
    const q = (this.tmplSearch || '').toLowerCase();
    return this.labTemplates.filter(t =>
      (this.tmplCat === 'all' || t.category === this.tmplCat) &&
      (!q || (t.title + ' ' + t.category + ' ' + t.description + ' ' + (t.concepts || '')).toLowerCase().includes(q)));
  },
  loadTemplate(t) {
    this.labForm = { title: t.title, category: t.category, hypothesis: t.hypothesis, iv: t.iv,
      iv_levels: t.iv_levels, dv: t.dv, dv_measure: t.dv_measure, design: t.design,
      population: t.population, n_sample: String(t.n), material: t.material, procedure: t.procedure,
      controls: t.controls, ethics: t.ethics, expected: t.expected, analysis_plan: '',
      concepts: t.concepts, sim_type: t.sim_type };
    this.editingLabId = null;
  },
  resetLabForm() { this.labForm = this.emptyLabForm(); this.editingLabId = null; },
  editExperiment(exp) {
    const f = this.emptyLabForm();
    Object.keys(f).forEach(k => { f[k] = exp[k] !== undefined && exp[k] !== null ? String(exp[k]) : f[k]; });
    this.labForm = f; this.editingLabId = exp.id; this.labView = 'form';
  },
  async saveExperiment() {
    if (!this.labForm.title) { alert('Donnez un nom à votre expérience.'); return; }
    const payload = { ...this.labForm };
    try {
      if (this.editingLabId) {
        await fetch('/api/experiments/' + this.editingLabId, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      } else {
        const d = await fetch('/api/experiments', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).then(r => r.json());
        this.labExperiments.unshift({ id: d.id, ...payload, status: 'draft' });
      }
      if (this.editingLabId) this.labExperiments = await fetch('/api/experiments').then(r => r.json());
      this.labView = 'list'; this.resetLabForm();
    } catch (e) { alert('Erreur de sauvegarde : ' + e.message); }
  },
  async deleteExperiment(exp) {
    if (!confirm('Supprimer « ' + exp.title + ' » ?')) return;
    await fetch('/api/experiments/' + exp.id, { method: 'DELETE' });
    this.labExperiments = this.labExperiments.filter(e => e.id !== exp.id);
    this.labProjects = this.labProjects.filter(e => e.id !== exp.id);
  },

  // ─── Projets & drag & drop ───
  addToProject(exp) {
    if (this.labProjects.find(p => p.id === exp.id)) { alert('Cette expérience est déjà dans le projet.'); return; }
    this.labProjects.push({ ...exp, analysis: exp.analysis || null });
    const src = this.labExperiments.find(e => e.id === exp.id);
    if (src) src.status = 'validated';
  },
  removeFromProject(p) {
    this.labProjects = this.labProjects.filter(x => x.id !== p.id);
    const src = this.labExperiments.find(e => e.id === p.id);
    if (src) src.status = 'draft';
  },
  handleDragStart(ev, exp) { this.dragExpId = exp.id; ev.dataTransfer.setData('text/plain', String(exp.id)); ev.dataTransfer.effectAllowed = 'move'; },
  handleDragEnd() { this.dragExpId = null; this.dropOver = false; },
  handleDrop(ev) {
    this.dropOver = false;
    const id = parseInt(ev.dataTransfer.getData('text/plain'), 10);
    const exp = this.labExperiments.find(e => e.id === id);
    if (exp) this.addToProject(exp);
  },
  viewProjectResults(p) {
    if (!p.analysis) { alert('Jouez d\u2019abord l\u2019expérience pour produire des résultats.'); return; }
    this.analysis = p.analysis; this.analysisTab = 'Résumé'; this.$nextTick(() => this.renderAnalysisCharts());
  },
  projectTreatment(p) { this.treatmentProject = p; this.showCode = null; },

  // ─── Suggestions (autocomplétion) ───
  showSug(field) {
    const map = { n: 'n' };
    const key = map[field] || field;
    const all = this.labSuggestions[key] || [];
    const q = (this.labForm[field] || '').toLowerCase();
    this.sugField = field;
    this.sugItems = (q ? all.filter(s => s.toLowerCase().includes(q)) : all).slice(0, 12);
  },
  hideSugSoon() { setTimeout(() => { this.sugField = null; }, 180); },
  pickSug(field, val) { this.labForm[field] = val; this.sugField = null; },

  // ══════════ MOTEUR DE SIMULATION ══════════
  playTemplate(t) { this.playExperiment(t); },
  playExperiment(exp) {
    const cfg = SIM_CONFIG[exp.sim_type];
    if (!cfg) { alert('Cette expérience n\u2019a pas de simulation associée.'); return; }
    this.conceptDetailView = null; this.articleView = null; this.analysis = null;
    this._stopReplay();
    const steps = cfg.steps(exp);
    const recorded = steps.filter(s => (s.buttons && s.buttons.length) || s.input).length;
    this.play = { sim: exp.sim_type, title: exp.title, category: exp.category || 'Expérience', exp,
      steps, i: -1, results: [], n: recorded, html: '', buttons: [], litKey: null,
      inputType: null, inputVal: '', inputPlaceholder: '', hint: cfg.hint || '', pending: null };
    this._advPlay();
  },
  _advPlay() {
    const p = this.play; if (!p) return;
    p.i++;
    if (p.i >= p.steps.length) { this.finishPlay(); return; }
    const s = p.steps[p.i];
    p.pending = s; p.html = s.html || ''; p.buttons = s.buttons || []; p.litKey = null;
    p.inputType = s.input ? 'number' : null; p.inputVal = ''; p.inputPlaceholder = s.placeholder || '';
    p._t0 = performance.now();
    clearTimeout(this._stepT);
    if (s.dur) {
      this._stepT = setTimeout(() => {
        if (!this.play || this.play.pending !== s) return;
        if (s.autoRecord) this._recordPlay(s.autoRecord); else this._advPlay();
      }, s.dur);
    }
  },
  _keyDown(e) {
    const p = this.play; if (!p) return;
    const s = p.pending; if (!s || !s.buttons || !s.buttons.length) return;
    const k = e.key === ' ' ? ' ' : e.key;
    const b = s.buttons.find(b => b.key === k || (b.key.length === 1 && b.key.toLowerCase() === (k || '').toLowerCase()));
    if (b) { e.preventDefault(); this.playRespond(b.key); }
  },
  playRespond(key) {
    const p = this.play, s = p && p.pending;
    if (!s || !s.buttons || !s.buttons.length) return;
    p.litKey = key;
    const row = { essai: p.results.length + 1, cond: s.cond || '', stimulus: s.label || '', reponse: key,
      correct: s.correct !== undefined ? (key === s.correct ? 1 : 0) : (s.incorrectKey !== undefined ? (key === s.incorrectKey ? 0 : 1) : undefined),
      rt_ms: s.timing ? Math.round(performance.now() - p._t0) : undefined, horodatage: Date.now() };
    this._recordPlay(row);
  },
  submitPlayInput() {
    const p = this.play, s = p && p.pending;
    if (!s || !s.input) return;
    const v = parseFloat(p.inputVal);
    if (isNaN(v)) { return; }
    this._recordPlay({ essai: p.results.length + 1, cond: s.cond || '', stimulus: s.label || '', reponse: p.inputVal, val: v, horodatage: Date.now() });
  },
  _recordPlay(row) {
    const p = this.play; if (!p) return;
    p.results.push(row);
    this._advPlay();
  },
  finishPlay(discard) {
    clearTimeout(this._stepT);
    const p = this.play;
    if (!p) return;
    if (discard && (!p.results || !p.results.length)) { this.play = null; return; }
    const cfg = SIM_CONFIG[p.sim];
    this.analysis = this.buildAnalysis(p.exp, p.results, cfg);
    this.play = null;
    this.analysisTab = 'Résumé';
    this.$nextTick(() => this.renderAnalysisCharts());
  },
  viewAnalysis() { this.finishPlay(); },
  closeAnalysis() { this.analysis = null; this.labView = 'list'; this._stopReplay(); },

  // ══════════ ANALYSE STATISTIQUE ══════════
  _groupStats(results, vf, conds) {
    return conds.map(c => {
      const rows = results.filter(r => r.cond === c);
      const vals = rows.map(r => vf === 'rt_ms' ? r.rt_ms : (vf === 'val' ? r.val : null)).filter(v => v !== undefined && v !== null);
      const n = vals.length;
      const mean = n ? vals.reduce((a, b) => a + b, 0) / n : 0;
      const sd = n > 1 ? Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1)) : 0;
      const corr = rows.filter(r => r.correct !== undefined && r.correct !== null);
      const acc = corr.length ? corr.filter(r => r.correct === 1).length / corr.length * 100 : null;
      return { cond: c, n, mean, sd, min: n ? Math.min(...vals) : 0, max: n ? Math.max(...vals) : 0, acc,
        meanF: n ? (vf === 'val' ? mean.toFixed(2) : Math.round(mean)) : '—', sdF: n ? (vf === 'val' ? sd.toFixed(2) : Math.round(sd)) : '—',
        accF: acc === null ? '—' : Math.round(acc) + '%' };
    });
  },
  buildAnalysis(exp, results, cfg) {
    const A = cfg.analysis || {};
    const vf = A.valueField;
    const conds = A.conds || [...new Set(results.map(r => r.cond))];
    const condTable = this._groupStats(results, vf, conds);
    const tests = A.tests ? A.tests(results, condTable) : [];
    const interpretation = A.interpretation ? A.interpretation(results, condTable) : 'Analyse des réponses collectées.';
    const critique = A.critique || 'Limites : N = 1 (données d\u2019un seul participant), absence de groupe contrôle, conditions non contrebalancées au niveau individuel — à considérer comme démonstration pédagogique et non comme résultat scientifique.';
    const clickCounts = (A.buttons || []).map(b => ({ key: b.key, label: b.label, color: b.color,
      count: results.filter(r => r.reponse === b.key).length })).filter(c => c.count > 0);
    return { exp: { ...exp }, title: exp.title, testLabel: A.testLabel || '', results,
      tableHeaders: A.tableHeaders || ['essai', 'cond', 'reponse', 'rt_ms'],
      condTable, tests, interpretation, critique, clickCounts,
      accLabel: A.accLabel || 'Précision', valueField: vf, unit: A.unit || 'ms',
      chart1: A.chart1 ? A.chart1(condTable, results) : null, chart2: A.chart2 ? A.chart2(condTable, results) : null,
      chart1Label: A.chart1Label || 'Moyennes par condition', chart2Label: A.chart2Label || 'Répartition',
      buttons: A.buttons || [], condColor: A.condColor || (() => '#22d3ee'),
      rtMin: results.length && vf === 'rt_ms' ? Math.min(...results.map(r => r.rt_ms).filter(v => v !== undefined)) : null };
  },
  renderAnalysisCharts() {
    if (!this.analysis) return;
    ['anChart1R', 'anChart2R', 'anChart1G', 'anChart2G'].forEach(id => {
      if (this._charts[id]) { this._charts[id].destroy(); delete this._charts[id]; }
    });
    const mk = (id, spec) => {
      const el = document.getElementById(id);
      if (!el || !spec) return;
      this._charts[id] = new Chart(el, spec);
    };
    if (this.analysisTab === 'Résumé') {
      mk('anChart1R', this.analysis.chart1); mk('anChart2R', this.analysis.chart2);
    } else if (this.analysisTab === 'Graphiques') {
      mk('anChart1G', this.analysis.chart1); mk('anChart2G', this.analysis.chart2);
      this._startReplay();
    } else this._stopReplay();
  },
  _startReplay() {
    this._stopReplay();
    const btns = this.analysis.buttons; if (!btns || !btns.length) return;
    let i = 0;
    const tick = () => {
      if (!this.analysis || this.analysisTab !== 'Graphiques') return;
      this.analysis.litKey = i < this.analysis.results.length ? this.analysis.results[i].reponse : null;
      i++;
      this._replayTimer = setTimeout(tick, 320);
    };
    tick();
  },
  _stopReplay() { clearTimeout(this._replayTimer); if (this.analysis) this.analysis.litKey = null; },

  // ══════════ EXPORTS & CODE ══════════
  _download(name, content, type) {
    const blob = new Blob([content], { type });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name; a.click(); URL.revokeObjectURL(a.href);
  },
  exportResultsJSON(exp) {
    const a = this.analysis || (exp && exp.analysis);
    if (!a) return;
    this._download((exp.title || 'experience').replace(/\W+/g, '_') + '_resultats.json',
      JSON.stringify({ experience: a.title, date: new Date().toISOString(), essais: a.results, stats: a.condTable, tests: a.tests, interpretation: a.interpretation }, null, 2), 'application/json');
  },
  exportResultsCSV(exp) {
    const a = this.analysis || (exp && exp.analysis);
    if (!a) return;
    const headers = a.tableHeaders;
    const lines = [headers.join(';')].concat(a.results.map(r => headers.map(h => r[h] !== undefined ? r[h] : '').join(';')));
    this._download((exp.title || 'experience').replace(/\W+/g, '_') + '.csv', lines.join('\n'), 'text/csv;charset=utf-8');
  },
  generateCodeR() {
    const t = this.treatmentProject; if (!t) return '';
    return `# Analyse R — ${t.title}\nlibrary(tidyverse)\n\ndonnees <- read_csv2("${t.title.replace(/\W+/g, '_')}.csv")\n\n# Statistiques descriptives\ndonnees %>% group_by(cond) %>%\n  summarise(n = n(), moyenne = mean(${this.analysis?.valueField === 'val' ? 'val' : 'rt_ms'}, na.rm = TRUE),\n            ecart_type = sd(${this.analysis?.valueField === 'val' ? 'val' : 'rt_ms'}, na.rm = TRUE))\n\n# Test statistique (adapter au plan : ${t.analysis_plan || 't-test apparié'})\n# t.test(mesure ~ cond, data = donnees, paired = TRUE)\n# anova_res <- aov(mesure ~ cond, data = donnees); summary(anova_res)\n\n# Figure\nggplot(donnees, aes(cond, ${this.analysis?.valueField === 'val' ? 'val' : 'rt_ms'}, fill = cond)) +\n  stat_summary(fun = mean, geom = "col", width = .6) +\n  stat_summary(fun.data = mean_cl_normal, geom = "errorbar", width = .2) +\n  theme_minimal() + labs(x = "Condition", y = "Mesure")`;
  },
  generateCodePy() {
    const t = this.treatmentProject; if (!t) return '';
    return `# Analyse Python — ${t.title}\nimport pandas as pd\nimport pingouin as pg\nimport seaborn as sns\nimport matplotlib.pyplot as plt\n\ndf = pd.read_csv("${t.title.replace(/\W+/g, '_')}.csv", sep=";")\n\n# Statistiques descriptives\nprint(df.groupby("cond")["${this.analysis?.valueField === 'val' ? 'val' : 'rt_ms'}"].agg(["count", "mean", "std"]))\n\n# Test statistique (adapter au plan : ${t.analysis_plan || 't-test apparié'})\n# print(pg.ttest(df[df.cond == "A"]["rt_ms"], df[df.cond == "B"]["rt_ms"], paired=True))\n# print(pg.anova(data=df, dv="rt_ms", within="cond", subject="essai"))\n\n# Figure\nsns.barplot(data=df, x="cond", y="${this.analysis?.valueField === 'val' ? 'val' : 'rt_ms'}", ci=95)\nplt.show()`;
  },
};

// ══════════ STATISTIQUES INFÉRENTIELLES (JS) ══════════
function gammaln(x) {
  const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
  let x0 = x, y = x, tmp = x + 5.5;
  tmp -= (x0 + 0.5) * Math.log(tmp);
  let ser = 1.000000000190015;
  for (let j = 0; j < 6; j++) ser += c[j] / ++y;
  return -tmp + Math.log(2.5066282746310005 * ser / x0);
}
function betacf(a, b, x) {
  const MAXIT = 200, EPS = 3e-9, FPMIN = 1e-300;
  let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
  if (Math.abs(d) < FPMIN) d = FPMIN;
  d = 1 / d; let h = d;
  for (let m = 1; m <= MAXIT; m++) {
    const m2 = 2 * m;
    let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
    d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d; h *= d * c;
    aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
    d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN;
    c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN;
    d = 1 / d; const del = d * c; h *= del;
    if (Math.abs(del - 1) < EPS) break;
  }
  return h;
}
function ibeta(a, b, x) {
  if (x <= 0) return 0; if (x >= 1) return 1;
  const bt = Math.exp(gammaln(a + b) - gammaln(a) - gammaln(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
}
function tPValue(t, df) {
  const x = df / (df + t * t);
  const p = 0.5 * ibeta(df / 2, 0.5, x);
  return Math.min(1, 2 * p);
}
function welchT(rowsA, rowsB, vf) {
  const a = rowsA.map(r => vf === 'val' ? r.val : r.rt_ms).filter(v => v !== undefined);
  const b = rowsB.map(r => vf === 'val' ? r.val : r.rt_ms).filter(v => v !== undefined);
  if (a.length < 2 || b.length < 2) return null;
  const m1 = a.reduce((x, y) => x + y, 0) / a.length, m2 = b.reduce((x, y) => x + y, 0) / b.length;
  const v1 = a.reduce((x, y) => x + (y - m1) ** 2, 0) / (a.length - 1), v2 = b.reduce((x, y) => x + (y - m2) ** 2, 0) / (b.length - 1);
  const se = Math.sqrt(v1 / a.length + v2 / b.length);
  if (!se) return null;
  const t = (m1 - m2) / se;
  const df = (v1 / a.length + v2 / b.length) ** 2 / ((v1 / a.length) ** 2 / (a.length - 1) + (v2 / b.length) ** 2 / (b.length - 1));
  const sp = Math.sqrt(((a.length - 1) * v1 + (b.length - 1) * v2) / (a.length + b.length - 2));
  const d = sp ? (m1 - m2) / sp : 0;
  const p = tPValue(Math.abs(t), df);
  return { t, df: Math.round(df), p, d, m1, m2 };
}

// ══════════ CONFIGURATION DES 21 SIMULATIONS ══════════
const INK = { R: { w: 'ROUGE', c: '#ef4444' }, B: { w: 'BLEU', c: '#3b82f6' }, V: { w: 'VERT', c: '#22c55e' }, J: { w: 'JAUNE', c: '#eab308' } };
const COLOR_KEYS = ['R', 'B', 'V', 'J'];
const inkButtons = COLOR_KEYS.map(k => ({ key: k, label: k, color: INK[k].c }));
const shuffle = (arr) => arr.map(v => [Math.random(), v]).sort((a, b) => a[0] - b[0]).map(x => x[1]);
const fix = '<span style="font-size:44px;color:#475569">+</span>';
const INKCSS = (hex, txt, size) => `<span style="color:${hex};font-size:${size || 52}px;font-weight:900;letter-spacing:2px">${txt}</span>`;

const EMOWORDS = { menaçant: ['DANGER', 'CRISE', 'PEUR', 'ATTAQUE', 'MENACE', 'URGENT', 'RISQUE', 'ALARME'], neutre: ['TABLE', 'PORTE', 'LIVRE', 'CHAISE', 'FENETRE', 'MUR', 'SOL', 'PLAFOND'], positif: ['JOIE', 'AMOUR', 'REUSSITE', 'VACANCES', 'SOURIRE', 'CALME', 'ESPOIR', 'BONHEUR'] };
const BIGFIVE_ITEMS = [
  { t: 'Extraverti(e), enthousiaste', trait: 'E', rev: false }, { t: 'Critique, querelleur(se)', trait: 'A', rev: true },
  { t: 'Fiable, discipliné(e)', trait: 'C', rev: false }, { t: 'Anxieux(se), facilement perturbé(e)', trait: 'N', rev: false },
  { t: 'Ouvert(e) aux nouvelles expériences', trait: 'O', rev: false }, { t: 'Réservé(e), calme', trait: 'E', rev: true },
  { t: 'Compatissant(e), chaleureux(se)', trait: 'A', rev: false }, { t: 'Désorganisé(e), négligent(e)', trait: 'C', rev: true },
  { t: 'Calme, émotionnellement stable', trait: 'N', rev: true }, { t: 'Conventionnel(le), peu créatif(ve)', trait: 'O', rev: true }];
const DK_QUESTIONS = [
  { q: 'Quelle structure du cerveau est centralement impliquée dans la formation de nouveaux souvenirs épisodiques ?', o: ['Hippocampe', 'Cervelet', 'Bulbes olfactifs', 'Moelle épinière'], a: 0 },
  { q: 'Que mesure le coefficient alpha de Cronbach ?', o: ['La validité de contenu', 'La cohérence interne', 'La reproductibilité inter-juges', 'La normalité'], a: 1 },
  { q: 'Dans la théorie de Piaget, à quel stade apparaît la conservation ?', o: ['Sensorimoteur', 'Préopératoire', 'Opérations concrètes', 'Formel'], a: 2 },
  { q: 'Que désigne le « d de Cohen » ?', o: ['Une corrélation', 'Une taille d\u2019effet', 'Un seuil de significativité', 'Une variance'], a: 1 },
  { q: 'Quel paradigme mesure le contrôle inhibiteur par un conflit lecture/couleur ?', o: ['Go/No-Go', 'Stroop', 'Simon', 'Flanker'], a: 1 },
  { q: 'La mémoire de travail selon Baddeley comprend…', o: ['3 sous-systèmes', 'boucle phonologique, calepin, administrateur', 'uniquement un store unique', '5 modules'], a: 1 },
  { q: 'Qu\u2019est-ce qu\u2019un effet de médiation ?', o: ['Un effet modéré', 'M transmet l\u2019effet de X sur Y', 'Une corrélation faible', 'Un biais d\u2019échantillon'], a: 1 },
  { q: 'Que mesure l\u2019IRMf indirectement ?', o: ['Les champs électriques', 'Le signal BOLD (oxygénation)', 'La dopamine', 'Les ondes alpha'], a: 1 },
  { q: 'En psychométrie, la fidélité test-retest évalue…', o: ['La stabilité temporelle', 'La validité prédictive', 'La structure factorielle', 'La standardisation'], a: 0 },
  { q: 'L\u2019effet de simple exposition (Zajonc) prédit que…', o: ['La répétition augmente l\u2019appréciation', 'La répétition diminue l\u2019attention', 'La nouveauté plaît davantage', 'L\u2019exposition fatigue'], a: 0 }];
const DRM_STUDY = { CHAIRE: ['TABLE', 'SALON', 'CANAPÉ', 'BOIS', 'REPOSER', 'TABOURET'], MÉDECINE: ['DOCTEUR', 'HÔPITAL', 'SANTÉ', 'PATIENT', 'SOIN', 'CLINIQUE'] };

const SIM_CONFIG = {
  // ── RT : Stroop ──
  stroop: {
    hint: 'Répondez à la COULEUR D\u2019ENCRE du mot (R / B / V / J ou clic).',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Nommez la couleur d\u2019encre.<br>R = rouge · B = bleu · V = vert · J = jaune</p>', dur: 2200, buttons: [] }];
      const n = 21;
      for (let i = 0; i < n; i++) {
        const cond = i % 3 === 0 ? 'congruent' : i % 3 === 1 ? 'incongruent' : 'neutre';
        const ink = COLOR_KEYS[Math.floor(Math.random() * 4)];
        let word = INK[ink].w;
        if (cond === 'incongruent') { const others = COLOR_KEYS.filter(k => k !== ink); word = INK[others[Math.floor(Math.random() * 3)]].w; }
        if (cond === 'neutre') word = 'XXXX';
        steps.push({ html: fix, dur: 420 + Math.random() * 380, buttons: [] });
        steps.push({ html: INKCSS(INK[ink].c, word), buttons: inkButtons, correct: ink, cond, label: word, timing: true });
        steps.push({ html: '', dur: 240, buttons: [] });
      }
      return steps;
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['congruent', 'incongruent', 'neutre'], buttons: inkButtons,
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => ({ congruent: '#10b981', incongruent: '#f87171', neutre: '#64748b' }[r.cond] || '#22d3ee'),
      chart1Label: 'TR moyen par condition (ms)', chart2Label: 'Précision par condition (%)',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ label: 'TR (ms)', data: t.map(x => Math.round(x.mean)), backgroundColor: ['#10b981', '#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ label: 'Précision (%)', data: t.map(x => x.acc || 0), backgroundColor: ['#10b981', '#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        const inc = results.filter(r => r.cond === 'incongruent'), con = results.filter(r => r.cond === 'congruent');
        const tt = welchT(inc, con, 'rt_ms');
        if (!tt) return [];
        const out = [{ label: 'Effet Stroop (incongruent − congruent)', value: Math.round(tt.m1 - tt.m2) + ' ms', note: 'Coût d\u2019interférence classique ≈ 60-120 ms chez l\u2019adulte jeune.' }];
        out.push({ label: 't de Welch', value: `t(${tt.df}) = ${tt.t.toFixed(2)}, p = ${tt.p < 0.001 ? '< .001' : '= ' + tt.p.toFixed(3)}`, note: 'Comparaison des TR entre conditions (N=1 : valeur indicative).' });
        out.push({ label: 'd de Cohen', value: tt.d.toFixed(2), note: 'Petit 0.2 · moyen 0.5 · grand 0.8.' });
        return out;
      },
      interpretation(r, t) {
        const inc = t.find(x => x.cond === 'incongruent'), con = t.find(x => x.cond === 'congruent');
        const delta = Math.round((inc?.mean || 0) - (con?.mean || 0));
        return delta > 40
          ? `Effet Stroop observé : vos TR en condition incongruente sont de ${Math.round(inc.mean)} ms contre ${Math.round(con.mean)} ms en congruente, soit un coût d'interférence de ${delta} ms. La lecture automatique du mot a interféré avec le nommage de la couleur : votre contrôle inhibiteur a dû inhiber la réponse dominante.`
          : `Coût d'interférence faible (${delta} ms). Causes possibles : stratégie de focalisation sur l'encre, trop peu d'essais, ou conditions déséquilibrées. Réessayez en vous laissant lire le mot naturellement.`;
      } }
  },
  // ── RT : Flanker ──
  flanker: {
    hint: 'Répondez à la direction de la flèche CENTRALE (← / →).',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Flèche CENTRALE ← → (touches flèches)</p>', dur: 2000, buttons: [] }];
      const btns = [{ key: 'ArrowLeft', label: '←', color: '#818cf8' }, { key: 'ArrowRight', label: '→', color: '#818cf8' }];
      for (let i = 0; i < 21; i++) {
        const cond = i % 3 === 0 ? 'congruent' : i % 3 === 1 ? 'incongruent' : 'neutre';
        const dir = Math.random() < 0.5 ? '←' : '→';
        const other = dir === '←' ? '→' : '←';
        const fl = cond === 'congruent' ? dir : cond === 'incongruent' ? other : '–';
        const stim = `${fl}${fl}${dir}${fl}${fl}`.replace(/–/g, '–');
        steps.push({ html: fix, dur: 420 + Math.random() * 380, buttons: [] });
        steps.push({ html: `<span style="font-size:56px;font-weight:900;letter-spacing:6px;color:#e2e8f0">${stim}</span>`, buttons: btns, correct: dir === '←' ? 'ArrowLeft' : 'ArrowRight', cond, label: stim, timing: true });
        steps.push({ html: '', dur: 240, buttons: [] });
      }
      return steps;
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['congruent', 'incongruent', 'neutre'], buttons: [{ key: 'ArrowLeft', label: '←', color: '#818cf8' }, { key: 'ArrowRight', label: '→', color: '#818cf8' }],
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => ({ congruent: '#10b981', incongruent: '#f87171', neutre: '#64748b' }[r.cond] || '#22d3ee'),
      chart1Label: 'TR moyen par condition (ms)', chart2Label: 'Précision par condition (%)',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => Math.round(x.mean)), backgroundColor: ['#10b981', '#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => x.acc || 0), backgroundColor: ['#10b981', '#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        const inc = results.filter(r => r.cond === 'incongruent'), con = results.filter(r => r.cond === 'congruent');
        const tt = welchT(inc, con, 'rt_ms');
        return tt ? [{ label: 'Effet Flanker', value: Math.round(tt.m1 - tt.m2) + ' ms', note: 'Classique : 40-80 ms.' },
          { label: 't de Welch', value: `t(${tt.df}) = ${tt.t.toFixed(2)}, p = ${tt.p < 0.001 ? '< .001' : tt.p.toFixed(3)}`, note: 'Incongruent vs congruent.' }] : [];
      },
      interpretation(r, t) {
        const inc = t.find(x => x.cond === 'incongruent'), con = t.find(x => x.cond === 'congruent');
        const delta = Math.round((inc?.mean || 0) - (con?.mean || 0));
        return `Les distracteurs incompatibles (${Math.round(inc?.mean || 0)} ms) ont coûté ${delta} ms par rapport aux congruents (${Math.round(con?.mean || 0)} ms) : votre attention sélective a dû supprimer la réponse automatique déclenchée par les flèches flanquantes.`;
      } }
  },
  // ── RT : Posner ──
  posner: {
    hint: 'Un indice annonce parfois la position de la cible — répondez au côté d\u2019apparition (← / →).',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Fixez la croix centrale.<br>Indiquez le côté où apparaît le rond (← / →).</p>', dur: 2200, buttons: [] }];
      const btns = [{ key: 'ArrowLeft', label: '←', color: '#818cf8' }, { key: 'ArrowRight', label: '→', color: '#818cf8' }];
      for (let i = 0; i < 20; i++) {
        const valid = Math.random() < 0.8;
        const side = Math.random() < 0.5 ? 'L' : 'R';
        const cue = valid ? side : (side === 'L' ? 'R' : 'L');
        const boxL = `<span style="color:${cue === 'L' ? '#fbbf24' : '#334155'};font-size:40px">▮</span>`;
        const boxR = `<span style="color:${cue === 'R' ? '#fbbf24' : '#334155'};font-size:40px">▮</span>`;
        steps.push({ html: fix, dur: 500, buttons: [] });
        steps.push({ html: `<div style="display:flex;gap:120px;align-items:center">${boxL}<span style="color:#475569;font-size:22px">+</span>${boxR}</div>`, dur: 320, buttons: [] });
        const target = side === 'L' ? `<div style="display:flex;gap:120px;align-items:center"><span style="color:#22d3ee;font-size:40px">●</span><span style="color:#334155;font-size:40px">▯</span></div>` : `<div style="display:flex;gap:120px;align-items:center"><span style="color:#334155;font-size:40px">▯</span><span style="color:#22d3ee;font-size:40px">●</span></div>`;
        steps.push({ html: target, buttons: btns, correct: side === 'L' ? 'ArrowLeft' : 'ArrowRight', cond: valid ? 'valide' : 'invalide', label: 'cible ' + side, timing: true });
        steps.push({ html: '', dur: 240, buttons: [] });
      }
      return steps;
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['valide', 'invalide'], buttons: [{ key: 'ArrowLeft', label: '←', color: '#818cf8' }, { key: 'ArrowRight', label: '→', color: '#818cf8' }],
      tableHeaders: ['essai', 'cond', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => r.cond === 'valide' ? '#10b981' : '#f87171',
      chart1Label: 'TR par validité de l\u2019indice (ms)', chart2Label: 'Précision (%)',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => Math.round(x.mean)), backgroundColor: ['#10b981', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => x.acc || 0), backgroundColor: ['#10b981', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        const inv = results.filter(r => r.cond === 'invalide'), val = results.filter(r => r.cond === 'valide');
        const tt = welchT(inv, val, 'rt_ms');
        return tt ? [{ label: 'Coût d\u2019orientation (invalide − valide)', value: Math.round(tt.m1 - tt.m2) + ' ms', note: 'Classique : +30 à +60 ms.' }] : [];
      },
      interpretation(r, t) {
        const v = t.find(x => x.cond === 'valide'), i = t.find(x => x.cond === 'invalide');
        return `Les indices valides ont accéléré la détection (${Math.round(v?.mean || 0)} ms) vs les invalides (${Math.round(i?.mean || 0)} ms) : votre attention s'était orientée vers la position annoncée — bénéfice quand l'indice est fiable (80%), coût quand il trompe.`;
      } }
  },
  // ── RT : Stroop émotionnel ──
  stroop_emo: {
    hint: 'Nommez la COULEUR D\u2019ENCRE du mot (R / B / V / J).',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Version émotionnelle du Stroop : couleur d\u2019encre uniquement.</p>', dur: 2000, buttons: [] }];
      const words = shuffle([...EMOWORDS['menaçant'], ...EMOWORDS['neutre'], ...EMOWORDS['positif']]);
      words.forEach(w => {
        const ink = COLOR_KEYS[Math.floor(Math.random() * 4)];
        const val = w => EMOWORDS['menaçant'].includes(w) ? 'menaçant' : EMOWORDS['positif'].includes(w) ? 'positif' : 'neutre';
        steps.push({ html: fix, dur: 380 + Math.random() * 320, buttons: [] });
        steps.push({ html: INKCSS(INK[ink].c, w, 46), buttons: inkButtons, correct: ink, cond: val(w), label: w, timing: true });
        steps.push({ html: '', dur: 220, buttons: [] });
      });
      return steps;
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['menaçant', 'neutre', 'positif'], buttons: inkButtons,
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => ({ 'menaçant': '#f87171', neutre: '#64748b', positif: '#10b981' }[r.cond] || '#22d3ee'),
      chart1Label: 'TR par valence émotionnelle (ms)', chart2Label: 'Précision (%)',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => Math.round(x.mean)), backgroundColor: ['#f87171', '#64748b', '#10b981'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => x.acc || 0), backgroundColor: ['#f87171', '#64748b', '#10b981'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        const m = results.filter(r => r.cond === 'menaçant'), n = results.filter(r => r.cond === 'neutre');
        const tt = welchT(m, n, 'rt_ms');
        return tt ? [{ label: 'Biais attentionnel menaçant', value: Math.round(tt.m1 - tt.m2) + ' ms', note: 'Δ > 20 ms suggère une capture attentionnelle par la menace (marqueur d\u2019anxiété).' }] : [];
      },
      interpretation(r, t) {
        const m = t.find(x => x.cond === 'menaçant'), n = t.find(x => x.cond === 'neutre');
        const delta = Math.round((m?.mean || 0) - (n?.mean || 0));
        return delta > 15
          ? `Les mots menaçants ont ralenti votre nommage de ${delta} ms : leur contenu a capté votre attention de manière automatique — un marqueur classique du biais attentionnel à la menace, exacerbé en anxiété.`
          : `Pas de biais menaçant marqué (Δ = ${delta} ms) : votre traitement de la couleur est resté insensible à la valence des mots sur cet échantillon d'essais.`;
      } }
  },
  // ── Séquence : N-back ──
  nback: {
    hint: 'ESPACE si la lettre = celle d\u2019il y a 2 présentations.',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">2-back : ESPACE quand la lettre actuelle = celle d\u2019il y a 2 lettres.</p>', dur: 2400, buttons: [] }];
      const letters = 'BCDFGHJKLMNPRSTV';
      let prev2 = '', prev1 = '';
      for (let i = 0; i < 30; i++) {
        let L;
        const target = i >= 2 && Math.random() < 0.32;
        L = target ? prev2 : letters[Math.floor(Math.random() * letters.length)];
        steps.push({ html: `<span style="font-size:64px;font-weight:900;color:#e2e8f0">${L}</span>`, dur: 1500,
          buttons: [{ key: ' ', label: 'ESPACE', color: '#22d3ee' }], timing: true, cond: target ? 'cible' : 'non-cible',
          label: L, correct: target ? ' ' : undefined, incorrectKey: target ? undefined : ' ',
          autoRecord: { essai: i + 1, cond: target ? 'cible' : 'non-cible', stimulus: L, reponse: '—', correct: target ? 0 : 1 } });
        steps.push({ html: fix, dur: 350, buttons: [] });
        prev2 = prev1; prev1 = L;
      }
      return steps;
    },
    _post(results) { // géré via noRespCorrect dans _finalizeSteps
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['cible', 'non-cible'], buttons: [{ key: ' ', label: 'ESPACE', color: '#22d3ee' }],
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => r.cond === 'cible' ? '#22d3ee' : '#64748b',
      chart1Label: 'TR aux cibles vs réponses intruses (ms)', chart2Label: 'Hits / fausses alertes',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => Math.round(x.mean)), backgroundColor: ['#22d3ee', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t, results) => {
        const hits = results.filter(r => r.cond === 'cible' && r.reponse === ' ').length;
        const targets = results.filter(r => r.cond === 'cible').length || 1;
        const fa = results.filter(r => r.cond === 'non-cible' && r.reponse === ' ').length;
        const nc = results.filter(r => r.cond === 'non-cible').length || 1;
        return { type: 'bar', data: { labels: ['Hits', 'Fausses alertes'], datasets: [{ data: [Math.round(hits / targets * 100), Math.round(fa / nc * 100)], backgroundColor: ['#10b981', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      tests(results) {
        const hits = results.filter(r => r.cond === 'cible' && r.reponse === ' ').length;
        const targets = results.filter(r => r.cond === 'cible').length || 1;
        const fa = results.filter(r => r.cond === 'non-cible' && r.reponse === ' ').length;
        const nc = results.filter(r => r.cond === 'non-cible').length || 1;
        const hr = Math.max(0.01, Math.min(0.99, hits / targets)), fr = Math.max(0.01, Math.min(0.99, fa / nc));
        const dp = (Math.log(hr / (1 - hr)) - Math.log(fr / (1 - fr))) / 1.4646;
        return [{ label: 'Hits', value: `${hits}/${targets} (${Math.round(hits / targets * 100)}%)`, note: 'Cibles détectées.' },
          { label: 'Fausses alertes', value: `${fa}/${nc} (${Math.round(fa / nc * 100)}%)`, note: 'Réponses sur non-cibles.' },
          { label: "d' (sensibilité)", value: dp.toFixed(2), note: 'd\u2019 ≈ 1.5-2.5 typique en 2-back ; < 1 → charge trop élevée ou distraction.' }];
      },
      interpretation(r, t) {
        const hits = r.filter(x => x.cond === 'cible' && x.reponse === ' ').length;
        const fa = r.filter(x => x.cond === 'non-cible' && x.reponse === ' ').length;
        const targets = r.filter(x => x.cond === 'cible').length || 1;
        return `Vous avez détecté ${hits}/${targets} cibles et produit ${fa} fausses alertes. La mise à jour de la mémoire de travail exige de maintenir ET actualiser en continu les 2 dernières lettres — chaque intrusion de la lettre précédente (1-back) produit une fausse alerte.`;
      } }
  },
  // ── Séquence : Oddball (P300) ──
  oddball: {
    hint: 'ESPACE uniquement sur les cercles ROUGES (rares).',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Appuyez sur ESPACE pour chaque cercle ROUGE (20%).</p>', dur: 2000, buttons: [] }];
      for (let i = 0; i < 30; i++) {
        const target = Math.random() < 0.2;
        steps.push({ html: `<span style="width:90px;height:90px;border-radius:50%;display:inline-block;background:${target ? '#ef4444' : '#3b82f6'}"></span>`, dur: 620,
          buttons: [{ key: ' ', label: 'ESPACE', color: '#22d3ee' }], timing: true, cond: target ? 'cible (rare)' : 'standard', label: target ? 'rouge' : 'bleu',
          correct: target ? ' ' : undefined, incorrectKey: target ? undefined : ' ',
          autoRecord: { essai: i + 1, cond: target ? 'cible (rare)' : 'standard', stimulus: target ? 'rouge' : 'bleu', reponse: '—', correct: target ? 0 : 1 } });
        steps.push({ html: fix, dur: 620, buttons: [] });
      }
      return steps;
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['cible (rare)', 'standard'], buttons: [{ key: ' ', label: 'ESPACE', color: '#22d3ee' }],
      tableHeaders: ['essai', 'cond', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => r.cond.includes('cible') ? '#ef4444' : '#3b82f6',
      chart1Label: 'TR cibles (ms)', chart2Label: 'Détection / fausses alertes (%)',
      chart1: (t) => ({ type: 'bar', data: { labels: ['TR cibles'], datasets: [{ data: [Math.round((t.find(x => x.cond.includes('cible'))?.mean) || 0)], backgroundColor: ['#ef4444'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t, results) => {
        const hits = results.filter(r => r.cond.includes('cible') && r.reponse === ' ').length;
        const tg = results.filter(r => r.cond.includes('cible')).length || 1;
        const fa = results.filter(r => !r.cond.includes('cible') && r.reponse === ' ').length;
        const nc = results.filter(r => !r.cond.includes('cible')).length || 1;
        return { type: 'bar', data: { labels: ['Détections', 'Fausses alertes'], datasets: [{ data: [Math.round(hits / tg * 100), Math.round(fa / nc * 100)], backgroundColor: ['#10b981', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      tests(results) {
        const hits = results.filter(r => r.cond.includes('cible') && r.reponse === ' ').length;
        const tg = results.filter(r => r.cond.includes('cible')).length || 1;
        return [{ label: 'Détection des stimuli rares', value: `${hits}/${tg} (${Math.round(hits / tg * 100)}%)`, note: 'En EEG, chaque détection rare déclenche un pic P300 (~300 ms) sur le scalp pariétal.' }];
      },
      interpretation() { return 'Les stimuli rares et pertinents déclenchent automatiquement une orientation de l\u2019attention — en EEG, le P300 qui en résulte est l\u2019un des potentiels évoqués les plus robustes. Votre taux de détection reflète la saillance du contraste rare/fréquent.'; } }
  },
  // ── Asch ──
  asch: {
    hint: 'Comparez la ligne cible aux 3 options après les réponses du groupe.',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Des « participants » répondent avant vous.<br>Indiquez la ligne identique à la cible.</p>', dur: 2400, buttons: [] }];
      const lens = [70, 95, 120];
      const line = (w, color) => `<div style="height:12px;width:${w}px;background:${color};border-radius:4px"></div>`;
      for (let i = 0; i < 12; i++) {
        const critical = i % 3 !== 2; // 8 critiques sur 12
        const correctIdx = Math.floor(Math.random() * 3);
        const targetW = lens[correctIdx];
        const wrongIdx = (correctIdx + 1 + Math.floor(Math.random() * 2)) % 3;
        const groupPick = critical ? wrongIdx : correctIdx;
        const optsHtml = lens.map((w, j) => `<div style="display:flex;align-items:center;gap:10px;margin:8px 0"><span style="color:#94a3b8;font-size:13px;width:16px">${j + 1}.</span>${line(w, j === correctIdx ? '#334155' : '#334155')}</div>`).join('');
        steps.push({ html: `<div style="display:flex;gap:70px;align-items:center;justify-content:center">
            <div><p style="color:#64748b;font-size:9px;margin-bottom:6px">CIBLE</p>${line(targetW, '#818cf8')}</div>
            <div>${optsHtml}</div></div><p style="color:#fbbf24;font-size:12px;margin-top:14px">Le groupe répond : ${'Option ' + (groupPick + 1) + ' · '.repeat(0)}</p>`,
          dur: 1400, buttons: [] });
        const btns = [1, 2, 3].map(n => ({ key: String(n), label: String(n), color: '#818cf8' }));
        steps.push({ html: `<p style="color:#94a3b8;font-size:12px">Votre réponse ? (le groupe a dit option ${groupPick + 1})</p>`, buttons: btns,
          correct: String(correctIdx + 1), cond: critical ? 'critique' : 'neutre', label: 'groupe: ' + (groupPick + 1), timing: true });
      }
      return steps;
    },
    analysis: { valueField: null, unit: '', conds: ['critique', 'neutre'], buttons: [1, 2, 3].map(n => ({ key: String(n), label: String(n), color: '#818cf8' })),
      tableHeaders: ['essai', 'cond', 'reponse', 'correct'], accLabel: 'Indépendance',
      condColor: r => r.cond === 'critique' ? '#f87171' : '#64748b',
      chart1Label: 'Conformité par type d\u2019essai (%)', chart2Label: 'Répartition de vos réponses',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => x.acc !== null ? 100 - Math.round(x.acc) : 0), backgroundColor: ['#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t, results) => {
        const counts = [1, 2, 3].map(n => results.filter(r => r.reponse === String(n)).length);
        return { type: 'bar', data: { labels: ['Option 1', 'Option 2', 'Option 3'], datasets: [{ data: counts, backgroundColor: ['#818cf8', '#22d3ee', '#fbbf24'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      tests(results, t) {
        const crit = results.filter(r => r.cond === 'critique');
        const conform = crit.filter(r => r.correct === 0).length;
        return [{ label: 'Taux de conformité (essais critiques)', value: crit.length ? Math.round(conform / crit.length * 100) + '%' : '—', note: 'Asch (1951) : ~37% des essais critiques ; 75% des participants se conforment au moins une fois.' }];
      },
      interpretation(r, t) {
        const crit = r.filter(x => x.cond === 'critique');
        const conform = crit.filter(x => x.correct === 0).length;
        const pct = crit.length ? Math.round(conform / crit.length * 100) : 0;
        return pct > 0
          ? `Vous vous êtes conformé ${conform} fois sur ${crit.length} essais critiques (${pct}%) alors que la réponse était objectivement visible. C'est exactement le paradigme d'Asch : la majorité unanime crée un doute sur soi (« ce sont peut-être eux qui voient juste ? ») — pression normative, pas informationnelle.`
          : `Aucune conformité sur les ${crit.length} essais critiques : vous avez maintenu votre jugement perceptif face à l'unanimité — minorité indépendante (la réponse la plus fréquente chez Asch, mais jamais garantie).`;
      } }
  },
  // ── Questionnaires ──
  framing: {
    hint: 'Lisez le scénario et choisissez un programme.',
    steps(exp) {
      const gain = Math.random() < 0.5;
      const txt = gain
        ? '<p style="font-size:15px;line-height:1.7;color:#e2e8f0;max-width:560px">Une épidémie frappe 600 personnes. Deux programmes sont proposés :</p><p style="font-size:14px;line-height:1.9;color:#cbd5e1;max-width:560px;margin-top:14px"><b style="color:#10b981">Programme A</b> : 200 personnes seront sauvées.<br><b style="color:#fbbf24">Programme B</b> : 1/3 de probabilité que 600 personnes soient sauvées, 2/3 que personne ne le soit.</p>'
        : '<p style="font-size:15px;line-height:1.7;color:#e2e8f0;max-width:560px">Une épidémie frappe 600 personnes. Deux programmes sont proposés :</p><p style="font-size:14px;line-height:1.9;color:#cbd5e1;max-width:560px;margin-top:14px"><b style="color:#10b981">Programme A</b> : 400 personnes vont mourir.<br><b style="color:#fbbf24">Programme B</b> : 1/3 de probabilité que personne ne meure, 2/3 que 600 personnes meurent.</p>';
      return [{ html: txt, buttons: [{ key: 'A', label: 'Programme A', color: '#10b981' }, { key: 'B', label: 'Programme B', color: '#fbbf24' }], cond: gain ? 'gains' : 'pertes', label: 'cadrage ' + (gain ? 'gains' : 'pertes') }];
    },
    analysis: { valueField: null, unit: '', conds: ['gains', 'pertes'], buttons: [{ key: 'A', label: 'A', color: '#10b981' }, { key: 'B', label: 'B', color: '#fbbf24' }],
      tableHeaders: ['cond', 'reponse'], accLabel: 'Choix',
      condColor: () => '#818cf8',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ label: 'Choix sûr (A) %', data: t.map(x => x.acc !== null ? Math.round(x.acc) : 0), backgroundColor: ['#10b981', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t, results) => ({ type: 'bar', data: { labels: ['A (sûr)', 'B (risqué)'], datasets: [{ data: ['A', 'B'].map(k => results.filter(r => r.reponse === k).length), backgroundColor: ['#10b981', '#fbbf24'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results) {
        const r0 = results[0] || {};
        const expected = r0.cond === 'gains' ? 'A' : 'B';
        const consistent = r0.reponse === expected;
        return [{ label: 'Votre cadrage', value: r0.cond === 'gains' ? 'GAINS (200 sauvés)' : 'PERTES (400 morts)', note: 'Assigné aléatoirement — les deux textes sont logiquement identiques (200 sauvées = 400 mortes sur 600).' },
          { label: 'Votre choix', value: r0.reponse === 'A' ? 'Programme A (sûr)' : 'Programme B (risqué)', note: consistent ? 'Conforme au pattern de Kahneman & Tversky (1981) : sûr en gains, risqué en pertes (~72% vs ~22%).' : 'Inverse au pattern classique — les effets de cadrage sont probabilistes, pas déterministes.' }];
      },
      interpretation(r) {
        const r0 = r[0] || {};
        return `Vous avez reçu le cadrage « ${r0.cond} » et choisi le programme ${r0.reponse}. Dans l'expérience originale, le MÊME problème conduit à ~72% de choix sûr quand il est formulé en vies sauvées, mais ~78% de choix risqué quand il est formulé en décès. La référence (point de départ) inverse la préférence : c'est l'effet de cadrage, fondement de la prospect theory.`;
      } }
  },
  anchoring: {
    hint: 'Regardez le nombre, puis estimez le pourcentage.',
    steps(exp) {
      const anchor = Math.random() < 0.5 ? 10 : 65;
      return [
        { html: `<p style="color:#94a3b8;font-size:12px">Une roue de fortune (aléatoire) s'arrête sur :</p><p style="font-size:88px;font-weight:900;color:#fbbf24;margin:10px 0">${anchor}</p>`, dur: 2600, buttons: [], cond: anchor === 10 ? 'ancre basse (10)' : 'ancre haute (65)', label: 'ancre ' + anchor },
        { html: '<p style="font-size:14px;color:#e2e8f0">Quel pourcentage de pays africains fait-il partie de l\u2019ONU ?</p>', input: true, placeholder: 'Votre estimation en %', cond: anchor === 10 ? 'ancre basse (10)' : 'ancre haute (65)', label: 'estimation' },
        { html: `<p style="font-size:14px;color:#10b981">Valeur réelle : environ 28% (54 pays sur 193).</p><p style="font-size:12px;color:#94a3b8;margin-top:10px">Votre estimation a-t-elle été attirée vers le nombre affiché ? C'est l'ancrage.</p>`, dur: 5200, buttons: [] },
      ];
    },
    analysis: { valueField: 'val', unit: '%', conds: ['ancre basse (10)', 'ancre haute (65)'], buttons: [],
      tableHeaders: ['cond', 'reponse', 'val'], accLabel: 'Écart à 28%',
      condColor: r => r.cond.includes('haute') ? '#fbbf24' : '#22d3ee',
      chart1: (t) => ({ type: 'bar', data: { labels: ['Vérité (28)', 'Ancre basse', 'Ancre haute'], datasets: [{ data: [28, t.find(x => x.cond.includes('basse'))?.n ? Math.round(t.find(x => x.cond.includes('basse')).mean) : null, t.find(x => x.cond.includes('haute'))?.n ? Math.round(t.find(x => x.cond.includes('haute')).mean) : null], backgroundColor: ['#10b981', '#22d3ee', '#fbbf24'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: null,
      tests(results) {
        const r = results.find(x => x.val !== undefined);
        if (!r) return [];
        return [{ label: 'Votre estimation', value: r.val + ' %', note: 'Vérité ≈ 28%.' },
          { label: 'Traction d\u2019ancrage', value: (r.cond.includes('haute') ? '+' : '') + Math.round(r.val - 28) + ' pts vs vérité', note: r.cond.includes('haute') ? 'L\u2019ancre 65 a tiré votre estimation vers le haut.' : 'L\u2019ancre 10 a tiré votre estimation vers le bas.' }];
      },
      interpretation(r) {
        const est = r.find(x => x.val !== undefined);
        if (!est) return 'Pas d\u2019estimation enregistrée.';
        const dir = est.cond.includes('haute');
        const pulled = dir ? est.val > 28 : est.val < 28;
        return pulled
          ? `Votre estimation (${est.val}%) a été attirée dans la direction de l'ancre (${dir ? '65' : '10'}) alors même que vous saviez ce nombre aléatoire. L'ajustement mental part de l'ancre et s'arrête trop tôt : c'est l'ancrage-ajustement de Tversky & Kahneman.`
          : `Votre estimation (${est.val}%) n'a pas suivi la direction de l'ancre — les effets d'ancrage sont puissants mais probabilistes (en moyenne +20 points d'écart entre ancres, pas chez chacun).`;
      } }
  },
  sunkcost: {
    hint: 'Décidez pour chaque scénario.',
    steps(exp) {
      const S = [
        { h: true, txt: 'Vous avez payé 80€ un week-end organisé depuis 6 mois. La météo est exécrable et vous êtes épuisé. Partir ou annuler ?', cond: 'investissement élevé' },
        { h: false, txt: 'Un ami vous offre son billet gratuit pour la même sortie, même météo, même fatigue. Y aller ou renoncer ?', cond: 'investissement faible' },
        { h: true, txt: 'Après 4 ans d\u2019études dans une filière qui ne vous plaît plus, changer de voie signifie repartir de zéro. Continuer ou réorienter ?', cond: 'investissement élevé' },
        { h: false, txt: 'Vous venez de commencer cette filière il y a 3 semaines et vous ne vous y plaisez pas. Continuer ou réorienter ?', cond: 'investissement faible' },
        { h: true, txt: 'Votre équipe a investi 2 ans et 500 k€ dans un logiciel que le marché boude. Une pivot coûterait moins cher. Persister ou pivoter ?', cond: 'investissement élevé' },
        { h: false, txt: 'Votre équipe a démarré ce logiciel il y a 3 semaines. Le marché boude. Une pivot coûterait moins cher. Persister ou pivoter ?', cond: 'investissement faible' }];
      const btns = [{ key: 'C', label: 'Continuer', color: '#fbbf24' }, { key: 'A', label: 'Abandonner', color: '#64748b' }];
      return [{ html: '<p style="font-size:14px;color:#94a3b8">6 scénarios — décidez spontanément, sans trop réfléchir.</p>', dur: 1800, buttons: [] }]
        .concat(S.map(s => ({ html: `<p style="font-size:14.5px;line-height:1.8;color:#e2e8f0;max-width:600px">${s.txt}</p>`, buttons: btns, cond: s.cond, label: s.h ? 'investi' : 'non investi' })));
    },
    analysis: { valueField: null, unit: '', conds: ['investissement élevé', 'investissement faible'], buttons: [{ key: 'C', label: 'C', color: '#fbbf24' }, { key: 'A', label: 'A', color: '#64748b' }],
      tableHeaders: ['essai', 'cond', 'reponse'], accLabel: 'Persistance',
      condColor: r => r.cond.includes('élevé') ? '#f87171' : '#64748b',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ label: '% persistance', data: t.map(x => x.acc !== null ? Math.round(x.acc) : 0), backgroundColor: ['#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t, results) => ({ type: 'bar', data: { labels: ['Continuer', 'Abandonner'], datasets: [{ data: ['C', 'A'].map(k => results.filter(r => r.reponse === k).length), backgroundColor: ['#fbbf24', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        const hi = t.find(x => x.cond.includes('élevé')), lo = t.find(x => x.cond.includes('faible'));
        return [{ label: 'Persistance quand l\u2019investissement est saillant', value: hi && hi.acc !== null ? Math.round(hi.acc) + '%' : '—', note: 'Arkes & Blumer : la poursuite dépend du coût passé, pas du futur.' },
          { label: 'Persistance sans investissement', value: lo && lo.acc !== null ? Math.round(lo.acc) + '%' : '—', note: 'Écart hi - lo = ampleur de votre effet de coût irrécupérable.' }];
      },
      interpretation(r, t) {
        const hi = t.find(x => x.cond.includes('élevé')), lo = t.find(x => x.cond.includes('faible'));
        const d = Math.round((hi?.acc || 0) - (lo?.acc || 0));
        return d > 15
          ? `Vous persistez ${d} points de plus quand un investissement passé est saillant : les paires de scénarios étaient pourtant logiquement identiques côté futur. Seuls les bénéfices futurs devraient compter — c'est le biais des coûts irrécupérables.`
          : `Peu d'écart de persistance selon l'investissement (${d} pts) : vous décidez sur les perspectives futures — l'exception rationnelle que note aussi la littérature chez une partie des participants.`;
      } }
  },
  bystander: {
    hint: 'Décidez si vous intervenez dans chaque situation.',
    steps(exp) {
      const S = [
        { n: 0, txt: 'Seul(e) dans la rue, vous voyez quelqu\u2019un s\u2019effondrer. Personne d\u2019autre autour. Intervenir (appeler les secours) ou passer ?' },
        { n: 1, txt: 'Même scène, mais un autre passant regarde aussi, immobile. Intervenir ou passer ?' },
        { n: 4, txt: 'Même scène, mais 4 autres passants regardent, tous immobiles. Intervenir ou passer ?' },
        { n: 0, txt: 'Au bureau tard le soir, seule(e), vous remarquez une fumée suspecte. Prévenir ou supposer que quelqu\u2019un s\u2019en occupe ?' },
        { n: 1, txt: 'Au bureau, un collègue présent ne réagit pas à la fumée suspecte. Prévenir ou non ?' },
        { n: 4, txt: 'Au bureau, 4 collègues présents ne réagissent pas à la fumée. Prévenir ou non ?' }];
      const btns = [{ key: 'I', label: 'Intervenir', color: '#10b981' }, { key: 'P', label: 'Passer', color: '#64748b' }];
      return [{ html: '<p style="font-size:14px;color:#94a3b8">6 situations d\u2019urgence — première réaction spontanée.</p>', dur: 1800, buttons: [] }]
        .concat(S.map(s => ({ html: `<p style="font-size:14.5px;line-height:1.8;color:#e2e8f0;max-width:600px">${s.txt}</p>`, buttons: btns, cond: s.n === 0 ? 'seul(e)' : s.n === 1 ? '1 témoin' : '4 témoins', label: s.n + ' autres' })));
    },
    analysis: { valueField: null, unit: '', conds: ['seul(e)', '1 témoin', '4 témoins'], buttons: [{ key: 'I', label: 'I', color: '#10b981' }, { key: 'P', label: 'P', color: '#64748b' }],
      tableHeaders: ['essai', 'cond', 'reponse'], accLabel: 'Aide',
      condColor: r => ({ 'seul(e)': '#10b981', '1 témoin': '#fbbf24', '4 témoins': '#f87171' }[r.cond] || '#22d3ee'),
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ label: '% d\u2019aide', data: t.map(x => x.acc !== null ? Math.round(x.acc) : 0), backgroundColor: ['#10b981', '#fbbf24', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t, results) => ({ type: 'bar', data: { labels: ['Intervenir', 'Passer'], datasets: [{ data: ['I', 'P'].map(k => results.filter(r => r.reponse === k).length), backgroundColor: ['#10b981', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        return [{ label: 'Aide quand on est seul', value: (t.find(x => x.cond === 'seul(e)')?.acc !== null && t.find(x => x.cond === 'seul(e)') ? Math.round(t.find(x => x.cond === 'seul(e)').acc) + '%' : '—'), note: 'Darley & Latané : ~85% d\u2019aide seule, ~31% à 4+ témoins (crise simulée).' }];
      },
      interpretation(r, t) {
        const s = t.find(x => x.cond === 'seul(e)'), g = t.find(x => x.cond === '4 témoins');
        const drop = Math.round((s?.acc || 0) - (g?.acc || 0));
        return drop > 0
          ? `Votre aide baisse de ${drop} points quand 4 témoins sont présents : chacun suppose que quelqu'un d'autre agira (diffusion de responsabilité) et l'inaction des autres redéfinit la situation comme non-urgente (influence informationnelle).`
          : `Votre aide ne dépend pas du nombre de témoins dans ces scénarios — l'effet du spectateur est statistique : il apparaît en moyenne, pas systématiquement chez chacun.`;
      } }
  },
  bigfive: {
    hint: 'Répondez spontanément (1 = pas du tout … 7 = tout à fait).',
    steps(exp) {
      const btns = [1, 2, 3, 4, 5, 6, 7].map(n => ({ key: String(n), label: String(n), color: '#818cf8' }));
      return [{ html: '<p style="font-size:14px;color:#94a3b8">« Je me vois comme… » — échelle de 1 à 7.</p>', dur: 1800, buttons: [] }]
        .concat(BIGFIVE_ITEMS.map((it, i) => ({ html: `<p style="font-size:16px;color:#e2e8f0">« Je me vois comme <b style="color:#22d3ee">${it.t}</b> »</p>`, buttons: btns, cond: it.trait, label: 'item ' + (i + 1), meta: { trait: it.trait, rev: it.rev } })));
    },
    analysis: { valueField: 'val', unit: '/7', conds: ['O', 'C', 'E', 'A', 'N'], buttons: [1, 2, 3, 4, 5, 6, 7].map(n => ({ key: String(n), label: String(n), color: '#818cf8' })),
      tableHeaders: ['essai', 'cond', 'reponse', 'val'], accLabel: null,
      condColor: () => '#818cf8',
      chart1: (t) => ({ type: 'radar', data: { labels: ['Ouverture (O)', 'Conscienciosité (C)', 'Extraversion (E)', 'Agréabilité (A)', 'Stabilité émotionnelle (N inv)'], datasets: [{ label: 'Profil OCEAN', data: t.map(x => Number(x.meanF)), backgroundColor: 'rgba(129,140,248,.25)', borderColor: '#818cf8', pointBackgroundColor: '#22d3ee' }] }, options: { plugins: { legend: { display: false } }, scales: { r: { min: 1, max: 7, ticks: { color: '#64748b', stepSize: 1 }, grid: { color: '#1e2745' }, angleLines: { color: '#1e2745' }, pointLabels: { color: '#94a3b8', font: { size: 9 } } } } } }),
      chart2: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => Number(x.meanF)), backgroundColor: ['#22d3ee', '#10b981', '#fbbf24', '#f472b6', '#818cf8'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { min: 1, max: 7, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results, t) {
        const labels = { O: 'Ouverture', C: 'Conscienciosité', E: 'Extraversion', A: 'Agréabilité', N: 'Névrosisme (score = stabilité inversée)' };
        return t.filter(x => x.n).map(x => ({ label: labels[x.cond] || x.cond, value: x.meanF + ' / 7', note: 'TIPI (Gosling 2003) : 2 items par trait, fiabilité courte mais convergente.' }));
      },
      interpretation(r, t) {
        const g = c => (t.find(x => x.cond === c)?.meanF) || 0;
        const hi = t.filter(x => x.n && x.mean >= 5).map(x => x.cond);
        const lo = t.filter(x => x.n && x.mean <= 3).map(x => x.cond);
        return `Profil calculé — traits élevés : ${hi.length ? hi.join(', ') : 'aucun'} ; traits bas : ${lo.length ? lo.join(', ') : 'aucun'}. Attention : le TIPI est un instrument de dépistage très court, non diagnostique ; les scores descriptifs varient selon le contexte de réponse.`;
      } }
  },
  conservation: {
    hint: 'Regardez la transformation puis répondez.',
    steps(exp) {
      const E = [
        { txt: 'On verse la même quantité d\u2019eau dans un verre étroit et haut vs un verre large et bas. Y a-t-il la même quantité d\u2019eau ?', ill: '<div style="display:flex;gap:60px;align-items:end;justify-content:center"><div style="width:44px;height:120px;border:2px solid #22d3ee;border-radius:0 0 10px 10px;display:flex;align-items:end"><div style="width:100%;height:80px;background:#22d3ee55"></div></div><div style="width:80px;height:80px;border:2px solid #22d3ee;border-radius:0 0 10px 10px;display:flex;align-items:end"><div style="width:100%;height:60px;background:#22d3ee55"></div></div></div>', cond: 'liquide' },
        { txt: 'Deux rangées de 6 jetons sont alignées. On espace les jetons de la seconde rangée. Y a-t-il le même nombre de jetons ?', ill: '<div style="text-align:center;color:#e2e8f0;font-size:19px;letter-spacing:8px">●●●●●●<br>● &nbsp;● &nbsp;● &nbsp;● &nbsp;● &nbsp;●</div>', cond: 'nombre' },
        { txt: 'Une boule de pâte à modeler est transformée en galette plate. Y a-t-il la même quantité de pâte ?', ill: '<div style="display:flex;gap:50px;align-items:center;justify-content:center"><div style="width:64px;height:64px;border-radius:50%;background:#fbbf2466;border:2px solid #fbbf24"></div><span style="color:#64748b;font-size:24px">→</span><div style="width:120px;height:28px;border-radius:14px;background:#fbbf2466;border:2px solid #fbbf24"></div></div>', cond: 'masse' },
        { txt: 'Deux bâtons de même longueur : on décale le second vers la droite. Sont-ils toujours de même longueur ?', ill: '<div style="text-align:center;color:#e2e8f0;font-size:18px;line-height:2">━━━━━━━<br>&nbsp;&nbsp;&nbsp;━━━━━━━</div>', cond: 'longueur' }];
      const btns = [{ key: 'O', label: 'Oui, pareil', color: '#10b981' }, { key: 'N', label: 'Non, différent', color: '#f87171' }];
      return [{ html: '<p style="font-size:14px;color:#94a3b8">4 épreuves de conservation (Piaget) — répondez comme le ferait un enfant observé.</p>', dur: 2000, buttons: [] }]
        .concat(E.map(e => [{ html: `<p style="font-size:12px;color:#94a3b8;margin-bottom:14px">Transformation…</p>${e.ill}`, dur: 2000, buttons: [] },
          { html: `${e.ill}<p style="font-size:14.5px;color:#e2e8f0;margin-top:16px">${e.txt}</p>`, buttons: btns, correct: 'O', cond: e.cond, label: e.cond }] )).flat();
    },
    analysis: { valueField: null, unit: '', conds: ['liquide', 'nombre', 'masse', 'longueur'], buttons: [{ key: 'O', label: 'O', color: '#10b981' }, { key: 'N', label: 'N', color: '#f87171' }],
      tableHeaders: ['essai', 'cond', 'reponse', 'correct'], accLabel: 'Conservation',
      condColor: () => '#fbbf24',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ label: 'Réussite', data: t.map(x => x.acc === null ? 0 : Math.round(x.acc)), backgroundColor: '#fbbf24' }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: null,
      tests(results, t) {
        const ok = t.filter(x => x.acc === 100).length;
        return [{ label: 'Épreuves réussies', value: ok + '/4', note: ok === 4 ? 'Profil opératoire concret (conservation acquise, ≈ après 7 ans).' : 'Profil pré-opératoire : au moins une épreuve en échec (la quantité est jugée par l\u2019apparence).' }];
      },
      interpretation(r, t) {
        const fails = t.filter(x => x.acc === 0).map(x => x.cond);
        return fails.length
          ? `Échec sur : ${fails.join(', ')}. En jugeant la quantité sur l'apparence (haut du verre, espacement, forme), on reproduit la pensée pré-opératoire : l'enfant centre sur UN dimension (centration) et néglige la transformation réversible (décentration).`
          : 'Conservation réussie sur les 4 épreuves : les quantités sont jugées invariantes malgré les transformations — stade opératoire concret.';
      } }
  },
  tom: {
    hint: 'Suivez l\u2019histoire puis répondez aux questions.',
    steps(exp) {
      const ill = t => `<p style="font-size:14px;line-height:1.9;color:#e2e8f0;max-width:580px;text-align:left">${t}</p>`;
      const btns2 = (a, b, ca, cb) => [{ key: a, label: a, color: '#818cf8' }, { key: b, label: b, color: '#fbbf24' }];
      return [
        { html: ill('🧒 <b>Sally</b> pose sa bille dans son <b style="color:#22d3ee">panier</b>, puis sort se promener.'), dur: 3000, buttons: [] },
        { html: ill('🧒 Pendant son absence, <b>Anne</b> prend la bille du panier et la cache dans sa <b style="color:#fbbf24">boîte</b>.'), dur: 3000, buttons: [] },
        { html: ill('🧒 Sally revient. Elle veut retrouver sa bille.'), dur: 2200, buttons: [] },
        { html: ill('<b style="color:#22d3ee">Question clé :</b> où Sally va-t-elle chercher sa bille ?'), buttons: btns2('P', 'B'), correct: 'P', cond: 'fausse croyance', label: 'question clé' },
        { html: ill('Où la bille se trouve-t-elle <b>réellement</b> ?'), buttons: btns2('P', 'B'), correct: 'B', cond: 'réalité', label: 'réalité' },
        { html: ill('Où Sally avait-elle posé la bille <b>au départ</b> ?'), buttons: btns2('P', 'B'), correct: 'P', cond: 'mémoire', label: 'mémoire' },
      ];
    },
    analysis: { valueField: null, unit: '', conds: ['fausse croyance', 'réalité', 'mémoire'], buttons: [{ key: 'P', label: 'P', color: '#818cf8' }, { key: 'B', label: 'B', color: '#fbbf24' }],
      tableHeaders: ['essai', 'cond', 'reponse', 'correct'], accLabel: 'Réussite',
      condColor: () => '#a78bfa',
      chart1: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => x.acc === null ? 0 : Math.round(x.acc)), backgroundColor: '#a78bfa' }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: null,
      tests(results, t) {
        const fb = t.find(x => x.cond === 'fausse croyance');
        return [{ label: 'Attribution de fausse croyance', value: fb && fb.acc === 100 ? 'Réussie' : 'En échec', note: 'Wimmer & Perner (1983) : ~30% de réussite à 3-4 ans, ~80% à 5 ans. La réussite exige de séparer « ce que Sally croit » de « ce qui est vrai ».' }];
      },
      interpretation(r, t) {
        const fb = r.find(x => x.cond === 'fausse croyance');
        return fb && fb.reponse === 'P'
          ? 'Vous avez répondu « panier » : vous attribuez à Sally une croyance fausse mais cohérente avec SON point de vue — c\u2019est la théorie de l\u2019esprit (méta-représentation), acquise typiquement vers 4-5 ans.'
          : 'Vous avez répondu « boîte » : c\u2019est la réponse d\u2019un enfant de 3 ans — la réalité écrase la représentation d\u2019autrui (réalisme enfantin). La théorie de l\u2019esprit consiste justement à répondre selon ce que Sally CROIT.';
      } }
  },
  dunnkruger: {
    hint: 'Passez le quiz puis estimez votre percentile.',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">10 questions de culture psychologique.<br>Après le quiz, vous estimerez votre niveau vs les autres.</p>', dur: 2600, buttons: [] }];
      DK_QUESTIONS.forEach((q, i) => {
        const btns = q.o.map((o, j) => ({ key: String(j), label: String(j + 1), color: '#818cf8' }));
        steps.push({ html: `<p style="font-size:14.5px;color:#e2e8f0;max-width:580px;line-height:1.7">${q.q}</p><p style="font-size:11px;color:#64748b;margin-top:10px">${q.o.map((o, j) => `${j + 1}. ${o}`).join(' &nbsp;·&nbsp; ')}</p>`,
          buttons: btns, correct: String(q.a), cond: 'quiz', label: 'Q' + (i + 1), timing: true });
      });
      steps.push({ html: '<p style="font-size:14px;color:#e2e8f0">Comparé à l\u2019ensemble des participants, situez-vous en <b>percentile</b> (0 = dernier, 100 = premier).</p>',
        input: true, placeholder: '0 à 100', cond: 'auto-estimation', label: 'percentile estimé' });
      return steps;
    },
    analysis: { valueField: 'val', unit: '', conds: ['score', 'auto-estimation'], buttons: [1, 2, 3, 4].map(n => ({ key: String(n), label: String(n), color: '#818cf8' })),
      tableHeaders: ['essai', 'cond', 'reponse', 'correct', 'rt_ms'], accLabel: 'Exactitude',
      condColor: () => '#fbbf24',
      chart1: (t, results) => {
        const score = Math.round(results.filter(r => r.cond === 'quiz').filter(r => r.correct === 1).length / Math.max(1, results.filter(r => r.cond === 'quiz').length) * 100);
        const est = results.find(r => r.cond === 'auto-estimation');
        return { type: 'bar', data: { labels: ['Score réel (%)', 'Percentile estimé'], datasets: [{ data: [score, est ? est.val : 0], backgroundColor: ['#10b981', '#fbbf24'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      chart2: null,
      tests(results) {
        const quiz = results.filter(r => r.cond === 'quiz');
        const score = quiz.filter(r => r.correct === 1).length;
        const pct = Math.round(score / Math.max(1, quiz.length) * 100);
        const est = (results.find(r => r.cond === 'auto-estimation') || {}).val;
        return [{ label: 'Score réel', value: `${score}/10 (${pct}%)`, note: 'Culture générale psychologie.' },
          { label: 'Percentile estimé', value: est !== undefined ? est + '/100' : '—', note: 'Estimation vs les autres participants.' },
          { label: 'Écart estimation − réel', value: est !== undefined ? ((est - pct >= 0 ? '+' : '') + Math.round(est - pct) + ' pts') : '—', note: 'Écart positif → surestimation (profil DK) ; négatif → sous-estimation (profil expert modeste).' }];
      },
      interpretation(results) {
        const quiz = results.filter(r => r.cond === 'quiz');
        const pct = Math.round(quiz.filter(r => r.correct === 1).length / Math.max(1, quiz.length) * 100);
        const est = (results.find(r => r.cond === 'auto-estimation') || {}).val || 0;
        const gap = Math.round(est - pct);
        return pct <= 40 && gap > 15
          ? `Score faible (${pct}%) mais auto-estimation élevée (+${gap} pts) : profil « montagne stupide » du Dunning-Kruger — les compétences qui manquent pour réussir sont aussi celles qui serviraient à évaluer son échec.`
          : gap <= 0
            ? `Vous sous-estimez légèrement votre performance (${gap} pts) : profil classique des meilleurs (effet faux-consensus — « les autres savent comme moi »).`
            : `Sur/confiance modérée (${gap > 0 ? '+' : ''}${gap} pts). L'effet DK est une tendance moyenne de groupe, pas un destin individuel — la calibration s'améliore avec le feedback (voir la simulation JOL).`;
      } }
  },
  calibration: {
    hint: 'Mémorisez, prédisez (JOL), puis vérifiez.',
    steps(exp) {
      const PAIRS = [['CHANTEUR', 'OPÉRA'], ['VOLCAN', 'LAVE'], ['PIRATE', 'VOILE'], ['ABEILLE', 'RUCHE'], ['SATURNE', 'ANNEAUX'], ['MOULIN', 'EAU'], ['BOUSSOLE', 'NORD'], ['AMAZONE', 'FORÊT']];
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">1) Mémorisez 8 paires (4 s chacune).<br>2) Prédisez votre rappel (JOL 0-100).<br>3) Test de rappel.</p>', dur: 3000, buttons: [] }];
      PAIRS.forEach(p => steps.push({ html: `<p style="font-size:38px;font-weight:800;color:#e2e8f0;letter-spacing:2px">${p[0]} — ${p[1]}</p>`, dur: 4000, buttons: [], cond: 'étude', label: p[0] }));
      PAIRS.forEach(p => steps.push({ html: `<p style="font-size:13px;color:#94a3b8">Si on vous montre <b style="color:#22d3ee">${p[0]}</b>, quelle probabilité de rappeler la suite ?</p>`, input: true, placeholder: '0 à 100 (%)', cond: 'jol', label: p[0] }));
      const opts = (target) => shuffle([target, ...shuffle(PAIRS.filter(x => x[1] !== target[1]).map(x => x[1])).slice(0, 3)]);
      PAIRS.forEach(p => {
        const options = opts(p);
        const btns = options.map((o, j) => ({ key: String(j), label: String(j + 1), color: '#818cf8' }));
        steps.push({ html: `<p style="font-size:13px;color:#94a3b8">Rappel : <b style="color:#22d3ee">${p[0]}</b> → ?</p><p style="font-size:13px;color:#e2e8f0;margin-top:10px">${options.map((o, j) => `${j + 1}. ${o}`).join(' &nbsp;·&nbsp; ')}</p>`,
          buttons: btns, correct: String(options.indexOf(p[1])), cond: 'rappel', label: p[0], timing: true });
      });
      return steps;
    },
    analysis: { valueField: null, unit: '', conds: ['jol', 'rappel'], buttons: [1, 2, 3, 4].map(n => ({ key: String(n), label: String(n), color: '#818cf8' })),
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct'], accLabel: 'Rappel',
      condColor: r => r.cond === 'jol' ? '#fbbf24' : '#22d3ee',
      chart1Label: 'Confiance prédite vs performance réelle (%)', chart2Label: 'Calibration par paire',
      chart1: (t, results) => {
        const jols = results.filter(r => r.cond === 'jol').map(r => parseFloat(r.reponse) || 0);
        const quiz = results.filter(r => r.cond === 'rappel');
        const acc = quiz.length ? quiz.filter(r => r.correct === 1).length / quiz.length * 100 : 0;
        const cj = jols.length ? Math.round(jols.reduce((a, b) => a + b, 0) / jols.length) : 0;
        return { type: 'bar', data: { labels: ['Confiance moyenne (JOL)', 'Rappel réel'], datasets: [{ data: [cj, Math.round(acc)], backgroundColor: ['#fbbf24', '#22d3ee'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      chart2: (t, results) => {
        const items = [...new Set(results.filter(r => r.cond === 'jol').map(r => r.stimulus))].slice(0, 8);
        return { type: 'line', data: { labels: items, datasets: [
          { label: 'JOL', data: items.map(i => parseFloat((results.find(r => r.cond === 'jol' && r.stimulus === i) || {}).reponse) || 0), borderColor: '#fbbf24', tension: .3 },
          { label: 'Réussite (0/100)', data: items.map(i => (results.find(r => r.cond === 'rappel' && r.stimulus === i) || {}).correct === 1 ? 100 : 0), borderColor: '#22d3ee', tension: .3 }] },
          options: { plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#64748b', font: { size: 8 } } } } } };
      },
      tests(results) {
        const jols = results.filter(r => r.cond === 'jol').map(r => parseFloat(r.reponse) || 0);
        const quiz = results.filter(r => r.cond === 'rappel');
        const cj = jols.length ? Math.round(jols.reduce((a, b) => a + b, 0) / jols.length) : 0;
        const acc = quiz.length ? Math.round(quiz.filter(r => r.correct === 1).length / quiz.length * 100) : 0;
        return [{ label: 'Confiance moyenne (JOL)', value: cj + '%', note: 'Prédiction de rappel par paire.' },
          { label: 'Rappel réel', value: acc + '%', note: 'QCM 4 options.' },
          { label: 'Biais de calibration', value: (cj - acc >= 0 ? '+' : '') + (cj - acc) + ' pts', note: 'Positif = surconfiance ; négatif = sous-confiance ; ≈ 0 = bien calibré.' }];
      },
      interpretation(results, t) {
        const jols = results.filter(r => r.cond === 'jol').map(r => parseFloat(r.reponse) || 0);
        const quiz = results.filter(r => r.cond === 'rappel');
        const cj = jols.length ? jols.reduce((a, b) => a + b, 0) / jols.length : 0;
        const acc = quiz.length ? quiz.filter(r => r.correct === 1).length / quiz.length * 100 : 0;
        const bias = Math.round(cj - acc);
        return bias > 10
          ? `Surconfiance de ${bias} points : votre confiance (${Math.round(cj)}%) excède votre rappel (${Math.round(acc)}%). La fluence de lecture (« c'était facile à lire ») nourrit des JOL optimistes — d'où l'intérêt du testing pour recaler le jugement sur la récupération réelle.`
          : bias < -10
            ? `Sous-confiance de ${Math.abs(bias)} points : vous savez mieux que vous ne le croyez. Certains apprenants sous-estiment systématiquement — plus de tests de vérification leur éviteraient des révisions inutiles.`
            : `Calibration correcte (écart ${bias} pts) : vos jugements de learning reflètent fidèlement votre performance — la compétence métacognitive la plus utile pour réguler ses révisions.`;
      } }
  },
  drm: {
    hint: 'Mémorisez les mots puis jugez « vu / nouveau ».',
    steps(exp) {
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Phase 1 : mémorisez les mots (1 s chacun).<br>Phase 2 : reconnaissance.</p>', dur: 3000, buttons: [] }];
      const studyWords = [];
      Object.values(DRM_STUDY).forEach(list => shuffle([...list]).forEach(w => studyWords.push({ w, lureOf: list })));
      shuffle(studyWords).forEach(x => steps.push({ html: `<span style="font-size:40px;font-weight:800;color:#e2e8f0">${x.w}</span>`, dur: 1000, buttons: [], cond: 'étude', label: x.w }));
      steps.push({ html: '<p style="font-size:22px;color:#fbbf24;font-weight:700">Comptez à rebours de 30 à 0 dans votre tête…</p>', dur: 4000, buttons: [] });
      const LURES = { CHAIRE: 'CHAISE', MÉDECINE: 'INFIRMIÈRE' };
      const test = [];
      Object.keys(DRM_STUDY).forEach(k => {
        test.push({ w: DRM_STUDY[k][0], cond: 'étudié', old: true });
        test.push({ w: DRM_STUDY[k][3], cond: 'étudié', old: true });
        test.push({ w: LURES[k], cond: 'leurre critique', old: false });
        test.push({ w: DRM_STUDY[k][4] + 'S', cond: 'nouveau', old: false });
      });
      const btns = [{ key: 'V', label: 'VU', color: '#10b981' }, { key: 'N', label: 'NOUVEAU', color: '#64748b' }];
      shuffle(test).forEach(x => steps.push({ html: `<span style="font-size:40px;font-weight:800;color:#e2e8f0">${x.w}</span>`, buttons: btns, correct: x.old ? 'V' : 'N', cond: x.cond, label: x.w, timing: true }));
      return steps;
    },
    analysis: { valueField: 'rt_ms', unit: 'ms', conds: ['étudié', 'leurre critique', 'nouveau'], buttons: [{ key: 'V', label: 'V', color: '#10b981' }, { key: 'N', label: 'N', color: '#64748b' }],
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct', 'rt_ms'], accLabel: 'Précision',
      condColor: r => ({ 'étudié': '#10b981', 'leurre critique': '#f87171', nouveau: '#64748b' }[r.cond] || '#22d3ee'),
      chart1Label: 'Taux de « VU » par type d\u2019item (%)', chart2Label: 'Réponses',
      chart1: (t, results) => {
        const rates = ['étudié', 'leurre critique', 'nouveau'].map(c => {
          const rows = results.filter(r => r.cond === c);
          return rows.length ? Math.round(rows.filter(r => r.reponse === 'V').length / rows.length * 100) : 0;
        });
        return { type: 'bar', data: { labels: ['Mots étudiés', 'Leurre critique', 'Mots nouveaux'], datasets: [{ label: '% « VU »', data: rates, backgroundColor: ['#10b981', '#f87171', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      chart2: (t, results) => ({ type: 'bar', data: { labels: ['VU', 'NOUVEAU'], datasets: [{ data: ['V', 'N'].map(k => results.filter(r => r.reponse === k).length), backgroundColor: ['#10b981', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      tests(results) {
        const lure = results.filter(r => r.cond === 'leurre critique');
        const fa = lure.filter(r => r.reponse === 'V').length;
        const stu = results.filter(r => r.cond === 'étudié');
        const hit = stu.filter(r => r.reponse === 'V').length;
        return [{ label: 'Faux souvenir (leurre appelé « VU »)', value: `${fa}/${lure.length}`, note: 'Le leurre n\u2019a jamais été présenté — DRAM (Roediger & McDermott 1995) : 60-80% de fausses reconnaissances.' },
          { label: 'Reconnaissance des mots étudiés', value: `${hit}/${stu.length}`, note: 'Comparez : souvent proche du taux du leurre !' }];
      },
      interpretation(results) {
        const lure = results.find(r => r.cond === 'leurre critique');
        return lure && lure.reponse === 'V'
          ? `Vous avez « reconnu » le leurre « ${lure.stimulus} » qui n'a JAMAIS été présenté : l'activation implicite des associés du thème (table, salon, canapé…) a généré le mot non-présenté, puis son souvenir a été attribué à tort à la perception. La mémoire est reconstructive.`
          : `Vous avez résisté au leurre cette fois : le faux souvenir DRM est statistique (60-80% en moyenne), pas universel — il augmente avec la force associative des listes et les tests retardés.`;
      } }
  },
  testing: {
    hint: 'Étudiez, puis la moitié des paires sera testée, l\u2019autre relue.',
    steps(exp) {
      const PAIRS = [['VOLTAIRE', 'PHILOSOPHE'], ['KEPLER', 'ASTRONOME'], ['CURIE', 'PHYSICIENNE'], ['DARWIN', 'NATURALISTE'], ['HYPPOCRATE', 'MÉDECIN'], ['GUTENBERG', 'IMPRIMEUR']];
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Mémorisez 6 paires (3 s chacune).</p>', dur: 2400, buttons: [] }];
      PAIRS.forEach(p => steps.push({ html: `<p style="font-size:32px;font-weight:800;color:#e2e8f0">${p[0]} — ${p[1]}</p>`, dur: 3000, buttons: [], cond: 'étude', label: p[0] }));
      const testIdx = [0, 2, 4];
      steps.push({ html: '<p style="font-size:13px;color:#fbbf24">Maintenant : 3 paires seront TESTÉES, 3 seront RELUES.</p>', dur: 2200, buttons: [] });
      PAIRS.forEach((p, i) => {
        if (testIdx.includes(i)) {
          const options = shuffle([p[1], 'PEINTRE', 'COMPOSITEUR', 'EXPLORATEUR']);
          const btns = options.map((o, j) => ({ key: String(j), label: String(j + 1), color: '#818cf8' }));
          steps.push({ html: `<p style="font-size:14px;color:#94a3b8">Test : ${p[0]} → ?</p><p style="font-size:13px;color:#e2e8f0;margin-top:8px">${options.map((o, j) => `${j + 1}. ${o}`).join(' &nbsp;·&nbsp; ')}</p>`, buttons: btns, correct: String(options.indexOf(p[1])), cond: 'test (récupération)', label: p[0] });
        } else {
          steps.push({ html: `<p style="font-size:26px;font-weight:700;color:#e2e8f0">Relecture : ${p[0]} — ${p[1]}</p>`, dur: 2600, buttons: [], cond: 'relecture', label: p[0] });
        }
      });
      steps.push({ html: '<p style="font-size:13px;color:#22d3ee;font-weight:700">Test final sur les 6 paires :</p>', dur: 1800, buttons: [] });
      PAIRS.forEach(p => {
        const options = shuffle([p[1], 'CARTOGRAPHE', 'ORFÈVRE', 'ARCHITECTE']);
        const btns = options.map((o, j) => ({ key: String(j), label: String(j + 1), color: '#818cf8' }));
        steps.push({ html: `<p style="font-size:14px;color:#94a3b8">Final : ${p[0]} → ?</p><p style="font-size:13px;color:#e2e8f0;margin-top:8px">${options.map((o, j) => `${j + 1}. ${o}`).join(' &nbsp;·&nbsp; ')}</p>`, buttons: btns, correct: String(options.indexOf(p[1])), cond: testIdx.includes(PAIRS.indexOf(p)) ? 'final-testé' : 'final-relu', label: p[0] });
      });
      return steps;
    },
    analysis: { valueField: null, unit: '', conds: ['final-testé', 'final-relu'], buttons: [1, 2, 3, 4].map(n => ({ key: String(n), label: String(n), color: '#818cf8' })),
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct'], accLabel: 'Rappel',
      condColor: r => r.cond === 'final-testé' ? '#10b981' : '#64748b',
      chart1: (t) => ({ type: 'bar', data: { labels: ['Paires testées', 'Paires relues'], datasets: [{ label: 'Rappel final (%)', data: t.map(x => x.acc === null ? 0 : Math.round(x.acc)), backgroundColor: ['#10b981', '#64748b'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: null,
      tests(results, t) {
        const a = t.find(x => x.cond === 'final-testé'), b = t.find(x => x.cond === 'final-relu');
        return [{ label: 'Testing effect (testé − relu)', value: a && b ? '+' + Math.round((a.acc || 0) - (b.acc || 0)) + ' pts' : '—', note: 'Roediger & Karpicke (2006) : +15-30% au retard long. Récupérer consolide plus que relire.' }];
      },
      interpretation(r, t) {
        const a = t.find(x => x.cond === 'final-testé'), b = t.find(x => x.cond === 'final-relu');
        const d = Math.round((a?.acc || 0) - (b?.acc || 0));
        return d > 0
          ? `Rappel final : ${Math.round(a?.acc || 0)}% pour les paires testées vs ${Math.round(b?.acc || 0)}% pour les relues. L'acte de récupération est un modificateur de mémoire : se tester (même sans succès) reconsolide davantage que ré-exposer.`
          : `Pas d'avantage du test dans cette session (${d} pts) — l'effet est plus robuste à long retard (48 h+) qu'immédiatement ; retestez-vous demain !`;
      } }
  },
  generation: {
    hint: 'Complétez ou lisez les mots, puis test de reconnaissance.',
    steps(exp) {
      const WORDS = [['C__N', 'CHIEN'], ['T_B_E', 'TABLE'], ['P_O_T', 'PRINTE'], ['É__LE', 'ÉCOLE'], ['M_ASON', 'MAISON'], ['F_EUR', 'FLEUR']];
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">6 mots : la moitié à GÉNÉRER (choisir parmi 4), la moitié à LIRE.</p>', dur: 2400, buttons: [] }];
      WORDS.forEach((wd, i) => {
        const generate = i % 2 === 0;
        if (generate) {
          const options = shuffle([wd[1], 'VOYAGE', 'JARDIN', 'BATEAU']);
          const btns = options.map((o, j) => ({ key: String(j), label: String(j + 1), color: '#22d3ee' }));
          steps.push({ html: `<p style="font-size:13px;color:#94a3b8">Générez le mot :</p><p style="font-size:38px;font-weight:800;color:#22d3ee;letter-spacing:4px">${wd[0]}</p><p style="font-size:13px;color:#e2e8f0;margin-top:10px">${options.map((o, j) => `${j + 1}. ${o}`).join(' &nbsp;·&nbsp; ')}</p>`, buttons: btns, correct: String(options.indexOf(wd[1])), cond: 'généré', label: wd[1] });
        } else {
          steps.push({ html: `<p style="font-size:13px;color:#94a3b8">Lisez :</p><p style="font-size:38px;font-weight:800;color:#94a3b8;letter-spacing:4px">${wd[1]}</p>`, dur: 2200, buttons: [], cond: 'lu', label: wd[1] });
        }
      });
      steps.push({ html: '<p style="font-size:13px;color:#fbbf24">Comptez à rebours de 20 à 0…</p>', dur: 3000, buttons: [] });
      const test = [...WORDS.map(w => ({ w: w[1], old: true })), { w: 'SOLEIL', old: false }, { w: 'MONTAGNE', old: false }];
      const btns = [{ key: 'V', label: 'VU', color: '#10b981' }, { key: 'N', label: 'NOUVEAU', color: '#64748b' }];
      shuffle(test).forEach(x => {
        const cond = x.old ? (WORDS.find(w => w[1] === x.w) ? (WORDS.indexOf(WORDS.find(w => w[1] === x.w))) % 2 === 0 ? 'généré' : 'lu' : 'lu') : 'nouveau';
        steps.push({ html: `<span style="font-size:36px;font-weight:800;color:#e2e8f0">${x.w}</span>`, buttons: btns, correct: x.old ? 'V' : 'N', cond, label: x.w });
      });
      return steps;
    },
    analysis: { valueField: null, unit: '', conds: ['généré', 'lu', 'nouveau'], buttons: [{ key: 'V', label: 'V', color: '#10b981' }, { key: 'N', label: 'N', color: '#64748b' }],
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct'], accLabel: 'Reconnaissance',
      condColor: r => ({ 'généré': '#22d3ee', lu: '#64748b', nouveau: '#f87171' }[r.cond] || '#818cf8'),
      chart1: (t, results) => {
        const rates = ['généré', 'lu', 'nouveau'].map(c => {
          const rows = results.filter(r => r.cond === c);
          return rows.length ? Math.round(rows.filter(r => r.reponse === 'V').length / rows.length * 100) : 0;
        });
        return { type: 'bar', data: { labels: ['Mots générés', 'Mots lus', 'Nouveaux'], datasets: [{ label: '% « VU »', data: rates, backgroundColor: ['#22d3ee', '#64748b', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      chart2: null,
      tests(results, t) {
        const g = results.filter(r => r.cond === 'généré' && r.correct !== undefined);
        const l = results.filter(r => r.cond === 'lu' && r.correct !== undefined);
        const gOk = g.filter(r => r.correct === 1).length, lOk = l.filter(r => r.correct === 1).length;
        return [{ label: 'Reconnaissance des mots générés', value: `${gOk}/${g.length}`, note: 'Générer = produire l\u2019information depuis un indice partiel.' },
          { label: 'Reconnaissance des mots lus', value: `${lOk}/${l.length}`, note: 'Lire = recevoir l\u2019information toute faite (Slamecka & Graf 1978 : +15-25% pour la génération).' }];
      },
      interpretation() {
        return 'Le mot que vous avez GÉNÉRÉ (choisi depuis le fragment) laisse en général une trace plus forte que le mot simplement lu : la production engage un traitement sémantique profond et un effort de récupération — c\u2019est l\u2019effet de génération, pilier de l\u2019apprentissage actif.';
      } }
  },
  spaced: {
    hint: 'Mémorisez deux listes (une massée, une espacée) puis test.',
    steps(exp) {
      const A = [['ALPAGA', 'LANAGE'], ['BOURG', 'VILLAGE'], ['COMTE', 'NOBLE']];
      const B = [['DUNES', 'SABLE'], ['EKLOGUE', 'POÈME'], ['FLAMME', 'BÛCHE']];
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Liste 1 : paires répétées CONSÉCUTIVEMENT (massé).</p>', dur: 2200, buttons: [] }];
      A.forEach(p => [0, 1, 2].forEach(() => steps.push({ html: `<p style="font-size:30px;font-weight:800;color:#e2e8f0">${p[0]} — ${p[1]}</p>`, dur: 1600, buttons: [], cond: 'études', label: p[0] })));
      steps.push({ html: '<p style="font-size:14px;color:#94a3b8">Liste 2 : paires répétées AVEC INTERVALLES (espacé).</p>', dur: 2200, buttons: [] });
      for (let r = 0; r < 3; r++) B.forEach(p => steps.push({ html: `<p style="font-size:30px;font-weight:800;color:#e2e8f0">${p[0]} — ${p[1]}</p>`, dur: 1200, buttons: [], cond: 'études', label: p[0] }));
      steps.push({ html: '<p style="font-size:13px;color:#fbbf24">Test final — reconnaître les mots étudiés :</p>', dur: 1800, buttons: [] });
      const test = [...A.map(p => ({ w: p[0], cond: 'massé', old: true })), ...B.map(p => ({ w: p[0], cond: 'espacé', old: true })), { w: 'GROTESQUE', cond: 'nouveau', old: false }, { w: 'HIVER', cond: 'nouveau', old: false }];
      const btns = [{ key: 'V', label: 'VU', color: '#10b981' }, { key: 'N', label: 'NOUVEAU', color: '#64748b' }];
      shuffle(test).forEach(x => steps.push({ html: `<span style="font-size:36px;font-weight:800;color:#e2e8f0">${x.w}</span>`, buttons: btns, correct: x.old ? 'V' : 'N', cond: x.cond, label: x.w }));
      return steps;
    },
    analysis: { valueField: null, unit: '', conds: ['espacé', 'massé', 'nouveau'], buttons: [{ key: 'V', label: 'V', color: '#10b981' }, { key: 'N', label: 'N', color: '#64748b' }],
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'correct'], accLabel: 'Reconnaissance',
      condColor: r => ({ 'espacé': '#10b981', massé: '#64748b', nouveau: '#f87171' }[r.cond] || '#22d3ee'),
      chart1: (t, results) => {
        const rates = ['espacé', 'massé', 'nouveau'].map(c => {
          const rows = results.filter(r => r.cond === c);
          return rows.length ? Math.round(rows.filter(r => r.reponse === 'V').length / rows.length * 100) : 0;
        });
        return { type: 'bar', data: { labels: ['Liste espacée', 'Liste massée', 'Nouveaux'], datasets: [{ label: '% « VU »', data: rates, backgroundColor: ['#10b981', '#64748b', '#f87171'] }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } };
      },
      chart2: null,
      tests(results, t) {
        const e = t.find(x => x.cond === 'espacé'), m = t.find(x => x.cond === 'massé');
        return [{ label: 'Rappel liste espacée', value: e ? Math.round(e.acc || 0) + '%' : '—', note: 'Chaque répétition arrive quand le tracé commence à s\u2019estomper : effet d\u2019encodage variable.' },
          { label: 'Rappel liste massée', value: m ? Math.round(m.acc || 0) + '%' : '—', note: 'Répétitions consécutives = fluence illusoire de maîtrise (Cepeda et al. 2006 : +10-25% pour l\u2019espacé).' }];
      },
      interpretation() {
        return 'La liste espacée est en général mieux reconnue : chaque répétition espacée rencontre un contexte légèrement différent, ce qui enrichit les pistes de récupération. La liste massée donne une impression de facilité (« je l\u2019ai déjà vu 3 fois d\u2019affilée ») mais s\u2019efface plus vite — illusion de maîtrise.';
      } }
  },
  exposure: {
    hint: 'Regardez les formes défiler, puis évaluez-les.',
    steps(exp) {
      const shapes = ['▲', '●', '◆', '■', '★', '⬢'];
      const freqs = [0, 1, 2, 5, 10, 25];
      const seq = [];
      shapes.forEach((s, i) => { for (let k = 0; k < freqs[i]; k++) seq.push(i); });
      shuffle(seq);
      const steps = [{ html: '<p style="font-size:14px;color:#94a3b8">Phase 1 — regardez simplement défiler les formes.</p>', dur: 2200, buttons: [] }];
      seq.slice(0, 40).forEach(idx => steps.push({ html: `<span style="font-size:74px;color:${['#ef4444', '#3b82f6', '#22c55e', '#eab308', '#a78bfa', '#f472b6'][idx]}">${shapes[idx]}</span>`, dur: 550, buttons: [], cond: 'exposition', label: shapes[idx] }));
      steps.push({ html: '<p style="font-size:14px;color:#94a3b8">Phase 2 — à quel point chacune vous PLAÎT-elle ? (1 → 7)</p>', dur: 2200, buttons: [] });
      const btns = [1, 2, 3, 4, 5, 6, 7].map(n => ({ key: String(n), label: String(n), color: '#818cf8' }));
      shapes.forEach((s, i) => steps.push({ html: `<span style="font-size:64px;color:${['#ef4444', '#3b82f6', '#22c55e', '#eab308', '#a78bfa', '#f472b6'][i]}">${s}</span><p style="font-size:11px;color:#64748b;margin-top:8px">présentée ${freqs[i]} fois</p>`, buttons: btns, cond: 'freq ' + freqs[i], label: s }));
      return steps;
    },
    analysis: { valueField: 'val', unit: '/7', conds: ['freq 0', 'freq 1', 'freq 2', 'freq 5', 'freq 10', 'freq 25'], buttons: [1, 2, 3, 4, 5, 6, 7].map(n => ({ key: String(n), label: String(n), color: '#818cf8' })),
      tableHeaders: ['essai', 'cond', 'stimulus', 'reponse', 'val'], accLabel: null,
      condColor: () => '#f472b6',
      chart1Label: 'Liking moyen par fréquence d\u2019exposition', chart2Label: 'Vos évaluations',
      chart1: (t) => ({ type: 'line', data: { labels: [0, 1, 2, 5, 10, 25], datasets: [{ label: 'Liking /7', data: [0, 1, 2, 5, 10, 25].map(f => { const row = t.find(x => x.cond === 'freq ' + f); return row && row.n ? Number(row.meanF) : null; }), borderColor: '#f472b6', backgroundColor: 'rgba(244,114,182,.15)', fill: true, tension: .35 }] }, options: { plugins: { legend: { display: false } }, scales: { y: { min: 1, max: 7, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8' } } } } }),
      chart2: (t) => ({ type: 'bar', data: { labels: t.map(x => x.cond), datasets: [{ data: t.map(x => Number(x.meanF) || 0), backgroundColor: '#f472b6' }] }, options: { plugins: { legend: { display: false } }, scales: { y: { min: 1, max: 7, ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#64748b', font: { size: 8 } } } } } }),
      tests(results, t) {
        const pts = results.filter(r => r.cond.startsWith('freq')).map(r => ({ f: parseInt(r.cond.split(' ')[1]), v: r.val })).filter(p => !isNaN(p.v));
        const n = pts.length;
        let rho = null;
        if (n >= 3) {
          const ranks = arr => arr.map(v => arr.filter(x => x < v).length + arr.filter(x => x === v).length / 2 - 0.5);
          const rf = ranks(pts.map(p => p.f)), rv = ranks(pts.map(p => p.v));
          const mf = rf.reduce((a, b) => a + b, 0) / n, mv = rv.reduce((a, b) => a + b, 0) / n;
          const num = rf.reduce((a, r, i) => a + (r - mf) * (rv[i] - mv), 0);
          const den = Math.sqrt(rf.reduce((a, r) => a + (r - mf) ** 2, 0) * rv.reduce((a, r) => a + (r - mv) ** 2, 0));
          rho = den ? num / den : 0;
        }
        return [{ label: 'Corrélation fréquence-liking (Spearman ρ)', value: rho === null ? '—' : 'ρ = ' + rho.toFixed(2), note: 'Zajonc (1968) : ρ positif = effet de simple exposition (la familiarité engendre la préférence).' }];
      },
      interpretation(results, t) {
        const f0 = t.find(x => x.cond === 'freq 0'), f25 = t.find(x => x.cond === 'freq 25');
        const d = (f25?.mean || 0) - (f0?.mean || 0);
        return d > 0
          ? `La forme vue 25 fois est mieux notée (+${d.toFixed(1)} pt) que celle jamais montrée : la simple répétition suffit à créer de la préférence — sans aucune récompense associée. Attention à la limite : au-delà d'un certain point, la satiété peut inverser l'effet.`
          : `Pas de gradient de préférence avec la fréquence dans votre session : l'effet de simple exposition est moyen et dépend du stimulus (des formes trop simples ou trop complexes peuvent ne rien donner).`;
      } }
  },
};

