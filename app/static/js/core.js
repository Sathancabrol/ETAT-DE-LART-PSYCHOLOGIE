/* ══════════ COGNITORIUM v8 — NOYAU ══════════ */
window.CORE = {
  activeTab: 'dashboard', navOpen: '',
  stats: {}, nodes: [], filteredNodes: [], uniqueDomains: [],
  searchQuery: '', filterDomain: 'all', filterType: 'all', compareList: [],
  showCompare: false, showNodeModal: false, selectedNode: {},
  domains: [], prisma: {}, research: [], researchFilter: 'all',
  concepts: [], conceptCatFilter: 'all', toolSubFilter: 'all', conceptSearch: '', toolSubcats: [],
  conceptDetailView: null, conceptDetailData: null, conceptDetailTab: 'Histoire',
  articleView: null, articleTab: 'Résumé', articleData: null,
  graphData: { nodes: [], links: [] }, _linksRaw: [], graphSearch: '', groupFilter: 'all', groups: [],
  selectedObsNode: null, graph3d: null,
  nodeFilters: [
    { type: 'study', label: 'Études', color: '#818cf8', active: true },
    { type: 'concept', label: 'Concepts', color: '#22d3ee', active: true },
    { type: 'method', label: 'Méthodes', color: '#34d399', active: true },
    { type: 'theorist', label: 'Théoriciens', color: '#fbbf24', active: true },
    { type: 'source', label: 'Sources OER', color: '#f472b6', active: true }],
  taxSearch: '', selectedTaxNode: null, _taxRoot: null, _taxSvg: null,
  statsTreeData: null, statTests: {}, selectedTest: null,
  dataTools: [],
  srlStep: 0,
  srlSteps: [{ phase: 'Phase 1', title: 'Planification' }, { phase: 'Phase 2', title: 'Contraintes' }, { phase: 'Phase 3', title: 'Requête IA' }, { phase: 'Phase 4', title: 'Évaluation' }, { phase: 'Phase 5', title: 'Plan d\u2019action' }],
  srlData: { session_id: 's-' + Math.random().toString(36).slice(2, 8), objective: '', criteria: '', constraints: '', ai_query: '', ai_response: '', evaluation: '', confidence: 75, action_plan: '' },
  _charts: {},

  async init() {
    this.labForm = this.emptyLabForm();
    await Promise.all([this.loadStats(), this.loadNodes(), this.loadDomains(), this.loadPrisma(), this.loadResearch(), this.loadConcepts(), this.initLab(),
      fetch('/api/data-tools').then(r => r.json()).then(d => this.dataTools = d).catch(() => {}),
      fetch('/api/stat-tests').then(r => r.json()).then(d => this.statTests = d).catch(() => {}),
      fetch('/api/stats-tree').then(r => r.json()).then(d => this.statsTreeData = d).catch(() => {}),
      fetch('/api/concept-subcats').then(r => r.json()).then(d => this.toolSubcats = d).catch(() => {})]);
    this.$nextTick(() => { lucide.createIcons(); this.renderCharts(); });
  },
  async loadStats() { try { this.stats = await (await fetch('/api/stats')).json(); } catch (e) {} },
  async loadNodes() {
    try {
      this.nodes = await (await fetch('/api/nodes')).json();
      this.filteredNodes = [...this.nodes];
      this.uniqueDomains = [...new Set(this.nodes.map(n => n.sous_domaine).filter(Boolean))];
    } catch (e) {}
  },
  async loadDomains() { try { this.domains = await (await fetch('/api/domains')).json(); } catch (e) {} },
  async loadPrisma() { try { this.prisma = await (await fetch('/api/prisma')).json(); } catch (e) {} },
  async loadResearch() { try { this.research = await (await fetch('/api/research-program')).json(); } catch (e) {} },
  async loadConcepts() { try { this.concepts = await (await fetch('/api/concepts')).json(); } catch (e) {} },

  switchTab(t) {
    this.activeTab = t; this.navOpen = '';
    this.$nextTick(() => {
      lucide.createIcons();
      if (t === 'dashboard') this.renderCharts();
      if (t === 'graph') setTimeout(() => this.initGraph3D(), 250);
      if (t === 'taxonomy') setTimeout(() => this.initTaxonomy(), 250);
      if (t === 'stats') setTimeout(() => this.initStatsTree(), 250);
    });
  },

  // ══════════ Dashboard ══════════
  renderCharts() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = '#64748b';
    Chart.defaults.borderColor = '#1e2745';
    Chart.defaults.font.size = 9;
    const mk = (id, cfg) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (this._charts[id]) this._charts[id].destroy();
      this._charts[id] = new Chart(el, cfg);
    };
    const preuve = this.stats.preuve_distribution || {};
    const pubs = this.stats.publication_distribution || {};
    const subd = this.stats.subdomain_distribution || {};
    mk('ch1', { type: 'bar', data: { labels: Object.keys(preuve), datasets: [{ data: Object.values(preuve), backgroundColor: '#818cf8' }] }, options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { precision: 0 } }, x: { ticks: { font: { size: 8 } } } } } });
    mk('ch2', { type: 'doughnut', data: { labels: Object.keys(pubs), datasets: [{ data: Object.values(pubs), backgroundColor: ['#818cf8', '#22d3ee', '#34d399', '#fbbf24', '#f472b6'] }] }, options: { plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 9 } } } } } });
    mk('ch3', { type: 'bar', data: { labels: Object.keys(subd), datasets: [{ data: Object.values(subd), backgroundColor: '#22d3ee' }] }, options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { ticks: { precision: 0 } }, y: { ticks: { font: { size: 8 } } } } } });
  },

  // ══════════ Base de données ══════════
  filterNodes() {
    const q = (this.searchQuery || '').toLowerCase();
    this.filteredNodes = this.nodes.filter(n => {
      const s = !q || [n.reference_courte, n.theme, n.tags, n.question_scientifique].some(x => (x || '').toLowerCase().includes(q));
      const d = this.filterDomain === 'all' || n.sous_domaine === this.filterDomain;
      const t = this.filterType === 'all' || n.type_publication === this.filterType;
      return s && d && t;
    });
  },
  getBadgeClass(t) { return { meta_analyse: 'badge-meta', revue_systematique: 'badge-revue', article_empirique: 'badge-exp', theorique: 'badge-theo', preprint: 'badge-preprint', perspective: 'badge-neuro' }[t] || 'bg-white/5 text-slate-500'; },
  openNodeDetail(n) { this.selectedNode = n; this.showNodeModal = true; this.$nextTick(() => lucide.createIcons()); },
  toggleCompare(id) { this.compareList = this.compareList.includes(id) ? this.compareList.filter(i => i !== id) : (this.compareList.length < 3 ? [...this.compareList, id] : this.compareList); },

  // ══════════ Domaines / Recherche ══════════
  coverageColor(c) { return { Fort: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', Partiel: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20', Insuffisant: 'text-amber-400 bg-amber-500/10 border-amber-500/20', Absent: 'text-rose-400 bg-rose-500/10 border-rose-500/20', Indirect: 'text-slate-400 bg-slate-500/10 border-slate-500/20' }[c] || 'text-slate-400 bg-white/5 border-white/10'; },
  researchFiltered() { return this.researchFilter === 'all' ? this.research : this.research.filter(r => r.domains.some(d => d.toLowerCase().includes(this.researchFilter.toLowerCase()))); },
  startResearchExperiment(r) {
    this.labForm = this.emptyLabForm();
    this.labForm.title = 'Étude — ' + r.gap;
    this.labForm.hypothesis = r.question;
    this.labForm.design = r.design;
    this.labForm.expected = r.expected;
    this.labForm.concepts = r.domains.join(', ');
    this.labForm.analysis_plan = 'À préciser (voir onglet Statistiques)';
    this.switchTab('lab');
    this.$nextTick(() => { this.labView = 'form'; });
  },

  // ══════════ Timeline ══════════
  timelineFiltered() { return [...this.nodes].sort((a, b) => (a.annee || 0) - (b.annee || 0)); },

  // ══════════ GRAPHE 3D ══════════
  typeColor(t) { return { study: '#818cf8', concept: '#22d3ee', method: '#34d399', theorist: '#fbbf24', source: '#f472b6' }[t] || '#64748b'; },
  async initGraph3D() {
    const el = document.getElementById('graph3d');
    if (!el || typeof ForceGraph3D === 'undefined') return;
    if (!this.graphData.nodes.length) {
      try { this.graphData = await (await fetch('/api/obsidian-graph')).json(); } catch (e) { return; }
      this._linksRaw = this.graphData.links.map(l => ({ ...l }));
      this.groups = [...new Set(this.graphData.nodes.map(n => n.group).filter(Boolean))].sort();
    }
    el.innerHTML = '';
    const W = el.clientWidth || 900, H = el.clientHeight || 560;
    const g = ForceGraph3D()(el).width(W).height(H).backgroundColor('#070a14')
      .nodeLabel(d => `<div style="background:#0c1120;border:1px solid #1e2745;border-radius:8px;padding:5px 9px;font-size:11px;color:#e2e8f0;font-family:Inter"><b style="color:${this.typeColor(d.type)}">${d.label}</b><br><span style="color:#64748b;font-size:9px">${d.group || ''} · trust ${d.trust ?? '—'}</span></div>`)
      .nodeThreeObject(d => {
        const r = d.type === 'study' ? 3.4 + (d.trust || 60) / 60 : d.type === 'concept' ? 2.6 : d.type === 'source' ? 2.2 : 2.4;
        const mesh = new THREE.Mesh(new THREE.SphereGeometry(r, 14, 14), new THREE.MeshBasicMaterial({ color: this.typeColor(d.type), transparent: true, opacity: 0.95 }));
        const halo = new THREE.Mesh(new THREE.SphereGeometry(r * 1.7, 12, 12), new THREE.MeshBasicMaterial({ color: this.typeColor(d.type), transparent: true, opacity: 0.10 }));
        const grp = new THREE.Group(); grp.add(mesh); grp.add(halo); return grp;
      })
      .linkColor(() => 'rgba(148,163,184,0.22)').linkWidth(0.7).linkOpacity(0.28)
      .linkDirectionalParticles(l => 1.2).linkDirectionalParticleWidth(1.4).linkDirectionalParticleSpeed(0.006)
      .d3Force('charge').strength(-95);
    g.graphData(JSON.parse(JSON.stringify({ nodes: this.graphData.nodes, links: this.graphData.links })));
    g.onNodeClick(d => { this.selectedObsNode = { ...d }; this.$nextTick(() => lucide.createIcons()); g.cameraPosition({ x: d.x * 1.9, y: d.y * 1.9, z: d.z * 1.9 }, d, 900); });
    g.onBackgroundClick(() => { this.selectedObsNode = null; });
    this.graph3d = g;
    this.applyGraphVisibility();
  },
  applyGraphVisibility() {
    const g = this.graph3d; if (!g) return;
    const active = new Set(this.nodeFilters.filter(f => f.active).map(f => f.type));
    const q = (this.graphSearch || '').toLowerCase();
    g.nodeVisibility(d => active.has(d.type) && (this.groupFilter === 'all' || d.group === this.groupFilter) && (!q || (d.label || '').toLowerCase().includes(q)));
    g.linkVisibility(l => active.has((l.source.id !== undefined ? l.source.type : l.source)) || false);
  },
  graphFilter() {
    if (!this.graph3d) return;
    const g = this.graph3d;
    const active = new Set(this.nodeFilters.filter(f => f.active).map(f => f.type));
    const q = (this.graphSearch || '').toLowerCase();
    g.nodeVisibility(d => active.has(d.type) && (this.groupFilter === 'all' || d.group === this.groupFilter) && (!q || (d.label || '').toLowerCase().includes(q)));
    g.linkVisibility(l => {
      const s = l.source, t = l.target;
      const vis = n => active.has(n.type) && (this.groupFilter === 'all' || n.group === this.groupFilter) && (!q || (n.label || '').toLowerCase().includes(q));
      return vis(s) && vis(t);
    });
  },
  nodeConnections(node) {
    const byId = {}; this.graphData.nodes.forEach(n => byId[n.id] = n);
    const out = [];
    this._linksRaw.forEach(l => {
      if (l.source === node.id) { const t = byId[l.target]; if (t) out.push({ id: t.id, label: t.label, type: t.type, rel: '→ ' + l.type }); }
      if (l.target === node.id) { const s = byId[l.source]; if (s) out.push({ id: s.id, label: s.label, type: s.type, rel: '← ' + l.type }); }
    });
    return out.slice(0, 20);
  },
  focusGraphNode(id) {
    const g = this.graph3d; if (!g) return;
    const n = g.graphData().nodes.find(x => x.id === id);
    if (!n) return;
    this.selectedObsNode = { ...n };
    this.$nextTick(() => lucide.createIcons());
    g.cameraPosition({ x: n.x * 1.9, y: n.y * 1.9, z: n.z * 1.9 }, n, 900);
  },

  // ══════════ TAXONOMIE ══════════
  async initTaxonomy() {
    const el = document.getElementById('taxTree');
    if (!el) return;
    if (!this._taxRoot) { try { this._taxRoot = await (await fetch('/api/taxonomy')).json(); } catch (e) { return; } }
    if (this._taxBuilt) return;
    this._taxBuilt = true;
    el.innerHTML = '';
    this._taxH = d3.hierarchy(this._taxRoot);
    this._taxH.x0 = 0; this._taxH.y0 = 0;
    if (this._taxH.children) this._taxH.children.forEach(c => { if (c.children) { c._children = c.children; c.children = null; } });
    const W = Math.max(el.clientWidth || 900, 700), H = Math.max(el.clientHeight || 540, 500);
    const svg = d3.select(el).append('svg').attr('width', W).attr('height', H);
    const gAll = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.4, 2.5]).on('zoom', e => gAll.attr('transform', e.transform)));
    const tree = d3.tree().nodeSize([16, 175]);
    const dur = 320;
    const diag = (s, d) => `M${s.y},${s.x}C${(s.y + d.y) / 2},${s.x} ${(s.y + d.y) / 2},${d.x} ${d.y},${d.x}`;
    const update = (source) => {
      const root = this._taxH;
      tree(root);
      const nodes = root.descendants(), links = root.links();
      const node = gAll.selectAll('g.node').data(nodes, d => d.id || (d.id = ++this._taxNodeId));
      const nEnter = node.enter().append('g').attr('class', 'tree-node')
        .attr('transform', `translate(${source.y0},${source.x0})`).attr('opacity', 0)
        .on('click', (e, d) => {
          this.selectedTaxNode = d; lucide.createIcons();
          if (d.children) { d._children = d.children; d.children = null; }
          else if (d._children) { d.children = d._children; d._children = null; }
          update(d);
        });
      nEnter.append('circle').attr('r', 4.5)
        .attr('fill', d => d._children ? '#818cf8' : d.children ? '#22d3ee' : '#334155')
        .attr('stroke', '#070a14').attr('stroke-width', 1.5);
      nEnter.append('text').attr('dy', '0.32em').attr('x', d => d.children || d._children ? -10 : 10)
        .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
        .style('fill', d => d.depth === 0 ? '#e2e8f0' : d.depth === 1 ? '#a5b4fc' : '#cbd5e1')
        .style('font-size', d => d.depth === 0 ? '12px' : d.depth === 1 ? '11px' : '10px')
        .style('font-weight', d => d.depth <= 1 ? 700 : 400)
        .text(d => d.data.name);
      nEnter.transition().duration(dur).attr('transform', d => `translate(${d.y},${d.x})`).attr('opacity', 1);
      node.transition().duration(dur).attr('transform', d => `translate(${d.y},${d.x})`).attr('opacity', 1);
      node.exit().transition().duration(dur).attr('transform', `translate(${source.y},${source.x})`).attr('opacity', 0).remove();
      const link = gAll.selectAll('path.link').data(links, d => d.target.id);
      link.enter().append('path').attr('class', 'link').attr('fill', 'none').attr('stroke', '#1e2745').attr('stroke-width', 1)
        .attr('d', () => diag({ x: source.x0, y: source.y0 }, { x: source.x0, y: source.y0 }))
        .transition().duration(dur).attr('d', d => diag(d.source, d.target));
      link.transition().duration(dur).attr('d', d => diag(d.source, d.target));
      link.exit().transition().duration(dur).attr('d', () => diag({ x: source.x, y: source.y }, { x: source.x, y: source.y })).remove();
      nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
    };
    this._taxUpdate = update;
    update(this._taxH);
  },
  taxPath(node) {
    const path = []; let d = node;
    while (d) { path.unshift(d.data.name); d = d.parent; }
    return path;
  },
  taxSearchFn() {
    const q = (this.taxSearch || '').toLowerCase().trim();
    if (!q || !this._taxH) return;
    let target = null;
    this._taxH.each(d => { if (!target && (d.data.name || '').toLowerCase().includes(q)) target = d; });
    if (!target) return;
    let a = target.parent;
    while (a) { if (a._children) { a.children = a._children; a._children = null; } a = a.parent; }
    this.selectedTaxNode = target;
    lucide.createIcons();
    this._taxUpdate(target);
  },

  // ══════════ CONCEPTS ══════════
  conceptsFiltered() {
    const q = (this.conceptSearch || '').toLowerCase();
    return this.concepts.filter(c => {
      const cat = this.conceptCatFilter === 'all' || c.cat === this.conceptCatFilter;
      const sub = this.conceptCatFilter !== 'outil' || this.toolSubFilter === 'all' || c.subcat === this.toolSubFilter;
      const s = !q || (c.name + ' ' + c.tagline + ' ' + c.definition).toLowerCase().includes(q);
      return cat && sub && s;
    });
  },
  catBadge(cat) { return { biais: 'bg-rose-500/15 text-rose-300 border border-rose-500/30', concept: 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30', outil: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' }[cat] || ''; },
  catLabel(cat) { return { biais: 'Biais cognitif', concept: 'Grand concept', outil: 'Outil' }[cat] || cat; },
  conceptName(id) { const c = this.concepts.find(x => x.id === id); return c ? c.name : id; },
  initials(name) {
    return (name || '?').split(/[\s&]+/).filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase();
  },
  ficheTabs(cat) {
    if (cat === 'outil') return ['Histoire', 'Mécanismes', 'Illustration', 'Débiaisage', 'Ressources', 'Résultats'];
    return ['Histoire', 'Mécanismes', 'Expériences', 'Illustration', 'Applications', 'Débiaisage', 'Historique', 'Ressources', 'Résultats'];
  },
  async openConceptDetail(cid) {
    try {
      this.conceptDetailData = await (await fetch('/api/concepts/' + cid)).json();
      this.conceptDetailView = cid;
      this.conceptDetailTab = 'Histoire';
      this.articleView = null;
      this.$nextTick(() => lucide.createIcons());
    } catch (e) { alert('Fiche indisponible.'); }
  },
  async openArticle(aid) {
    try {
      this.articleData = await (await fetch('/api/articles/' + aid)).json();
      this.articleView = aid;
      this.articleTab = 'Résumé';
      this.conceptDetailView = null;
      this.$nextTick(() => { lucide.createIcons(); this.renderArticleChart(); });
    } catch (e) { alert('Article indisponible.'); }
  },
  renderArticleChart() {
    if (!this.articleData || this.articleTab !== 'Résultats' || typeof Chart === 'undefined') return;
    this.$nextTick(() => {
      const el = document.getElementById('articleChart');
      if (!el) return;
      if (this._charts.article) this._charts.article.destroy();
      const r = this.articleData.results || {};
      this._charts.article = new Chart(el, {
        type: 'bar',
        data: { labels: Object.keys(r.data || {}), datasets: [{ label: r.unit || '', data: Object.values(r.data || {}), backgroundColor: ['#f87171', '#fbbf24', '#22d3ee', '#34d399', '#818cf8'] }] },
        options: { plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#64748b' }, grid: { color: '#1e2745' } }, x: { ticks: { color: '#94a3b8', font: { size: 9 } } } } }
      });
    });
  },
  launchSim(simType) {
    const t = this.labTemplates.find(x => x.sim_type === simType);
    if (!t) { alert('Pas de simulation pour ce concept.'); return; }
    this.conceptDetailView = null; this.articleView = null;
    this.switchTab('lab');
    setTimeout(() => this.playExperiment(t), 380);
  },

  // ══════════ STATISTIQUES ══════════
  initStatsTree() {
    const el = document.getElementById('statsTree');
    if (!el || !this.statsTreeData) return;
    el.innerHTML = '';
    const root = d3.hierarchy(this.statsTreeData);
    root.x0 = 0; root.y0 = 0;
    root.descendants().forEach((d, i) => { d.id = i; d._children = d.children; if (d.depth > 1) d.children = null; });
    const W = el.clientWidth || 700, H = el.clientHeight || 530;
    const svg = d3.select(el).append('svg').attr('width', W).attr('height', H);
    const gAll = svg.append('g').attr('transform', 'translate(24,24)');
    svg.call(d3.zoom().scaleExtent([0.45, 2.2]).on('zoom', e => gAll.attr('transform', e.transform)));
    const tree = d3.tree().nodeSize([34, 195]);
    const color = d => d.depth === 0 ? '#818cf8' : d.data.test ? '#34d399' : '#22d3ee';
    const update = (source) => {
      tree(root);
      const nodes = root.descendants(), links = root.links();
      const node = gAll.selectAll('g.sn').data(nodes, d => d.id);
      const ent = node.enter().append('g').attr('class', 'sn tree-node')
        .attr('transform', `translate(${source.y0},${source.x0})`).attr('opacity', 0)
        .on('click', (e, d) => {
          if (d.data.test) { this.selectedTest = this.statTests[d.data.test]; this.$nextTick(() => lucide.createIcons()); return; }
          if (d.children) { d._children = d.children; d.children = null; }
          else if (d._children) { d.children = d._children; d._children = null; }
          update(d);
        });
      ent.append('circle').attr('r', d => d.data.test ? 6 : 4).attr('fill', d => d.data.test ? '#34d399' : d._children ? '#818cf8' : '#22d3ee').attr('stroke', '#070a14').attr('stroke-width', 1.5);
      ent.append('text').attr('dy', '0.32em').attr('x', d => d.children || d._children ? -9 : 9)
        .attr('text-anchor', d => d.children || d._children ? 'end' : 'start')
        .text(d => d.data.name + (d.data.test ? ' ★' : ''))
        .attr('fill', d => d.data.test ? '#6ee7b7' : '#cbd5e1').style('font-weight', d => d.data.test ? 700 : 400);
      ent.transition().duration(300).attr('transform', d => `translate(${d.y},${d.x})`).attr('opacity', 1);
      node.transition().duration(300).attr('transform', d => `translate(${d.y},${d.x})`).attr('opacity', 1);
      node.exit().transition().duration(300).attr('transform', `translate(${source.y},${source.x})`).attr('opacity', 0).remove();
      const link = gAll.selectAll('path.sl').data(links, d => d.target.id);
      link.enter().append('path').attr('class', 'sl').attr('fill', 'none').attr('stroke', '#1e2745').attr('stroke-width', 1.1)
        .attr('d', () => { const o = { x: source.x0, y: source.y0 }; return dg(o, o); })
        .transition().duration(300).attr('d', d => dg(d.source, d.target));
      link.transition().duration(300).attr('d', d => dg(d.source, d.target));
      link.exit().transition().duration(300).attr('d', () => { const o = { x: source.x, y: source.y }; return dg(o, o); }).remove();
      nodes.forEach(d => { d.x0 = d.x; d.y0 = d.y; });
      function dg(s, d) { return `M${s.y},${s.x}C${(s.y + d.y) / 2},${s.x} ${(s.y + d.y) / 2},${d.x} ${d.y},${d.x}`; }
    };
    update(root);
  },

  // ══════════ SRL ══════════
  simulateAI() {
    this.srlData.ai_response = "Analyse fondée sur l'état de l'art (base Cognitorium) : le contrôle attentionnel explique l'essentiel du pouvoir prédictif de la mémoire de travail (Lee & Engle 2026, r 0.63 → 0.40 une fois l'AC contrôlé). En contexte d'apprentissage, le monitoring métacognitif prédit mieux la réussite que la seule planification. Recommandation : formuler 2 critères de succès mesurables, segmenter la session en blocs de 25 min, et auto-évaluer à chaque bloc (JOL).";
  },
  async submitTrace() {
    try {
      const r = await fetch('/api/metacognitive-traces', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...this.srlData, phase: this.srlSteps[this.srlStep].phase }) });
      const d = await r.json();
      if (d.status === 'success') { alert('✓ Trace enregistrée !'); this.srlStep = 0; this.srlData = { ...this.srlData, objective: '', criteria: '', constraints: '', ai_query: '', ai_response: '', evaluation: '', action_plan: '' }; }
    } catch (e) { alert('Erreur'); }
  },
};

function app() { return Object.assign({}, window.LAB, window.CORE); }
