/**
 * Laplace ✳ — widget flottant : nébuleuse rotative (image + repli CSS),
 * cliquable pour ouvrir le chat du système depuis n'importe quelle page.
 * Laplace est l'interlocuteur principal (il remplace SOL en façade) ;
 * SOL ☉ reste l'approbateur. Sert /api/cosmos/chat.
 * Écoute l'événement 'open-laplace-chat' pour être ouvert par l'UI.
 */
(function () {
  if (window.__solWidget) return;
  window.__solWidget = true;

  const CSS = `
  .solw-btn{position:fixed;bottom:22px;right:22px;width:74px;height:74px;border-radius:26%;
    cursor:pointer;z-index:9998;border:none;background:transparent;padding:0;
    transition:transform .25s cubic-bezier(.34,1.56,.64,1)}
  .solw-btn:hover{transform:scale(1.1) rotate(-3deg)}
  /* 🌀 mascot Laplace animé façon Clippy : sprite 2x2, 4 poses (idle, clin d'œil, salut, excité) */
  .solw-mascot{position:absolute;inset:0;width:100%;height:100%;border-radius:26%;
    background-image:url('/static/laplace_sprite.png');background-size:200% 200%;
    background-color:#0b0f1d;overflow:hidden;
    box-shadow:0 0 20px 4px rgba(192,132,252,.4), 0 0 48px 12px rgba(147,51,234,.2);
    animation:solw-frames 1.9s steps(1,end) infinite, solw-glow 3.6s ease-in-out infinite, solw-hello 14s ease-in-out infinite}
  @keyframes solw-frames{
    0%,24%{background-position:0% 0%}        /* pose 1 : repos */
    25%,49%{background-position:100% 0%}     /* pose 2 : clin d'œil */
    50%,74%{background-position:0% 100%}     /* pose 3 : salut */
    75%,100%{background-position:100% 100%}  /* pose 4 : excité */
  }
  @keyframes solw-hello{0%,90%,100%{transform:translateY(0) rotate(0)}
    92%{transform:translateY(-7px) rotate(-6deg)} 94%{transform:translateY(0) rotate(5deg)}
    96%{transform:translateY(-4px) rotate(-3deg)} 98%{transform:translateY(0) rotate(0)}}
  @keyframes solw-glow{0%,100%{filter:brightness(1) saturate(1.05)}
    50%{filter:brightness(1.18) saturate(1.22)}}
  /* repli si l'image ne charge pas : nébuleuse CSS */
  .solw-core{position:absolute;inset:9px;border-radius:50%;
    background:radial-gradient(circle at 36% 34%, #f5d0fe 0%, #c084fc 26%, #7c3aed 58%, #2e1065 100%);
    box-shadow:0 0 20px 5px rgba(192,132,252,.45), 0 0 50px 14px rgba(147,51,234,.22);
    animation:solw-plasma 3.6s ease-in-out infinite}
  .solw-core::after{content:'';position:absolute;inset:-9px;border-radius:50%;
    background:radial-gradient(circle at 66% 70%, rgba(232,121,249,.35), transparent 42%),
               radial-gradient(circle at 26% 78%, rgba(56,189,248,.22), transparent 38%)}
  @keyframes solw-plasma{0%,100%{filter:brightness(1)}50%{filter:brightness(1.2)}}
  .solw-star{position:absolute;width:3px;height:3px;border-radius:50%;background:#f5f3ff;
    box-shadow:0 0 6px 1px rgba(245,243,255,.9);animation:solw-tw 2.8s ease-in-out infinite}
  .solw-star.s2{animation-delay:.9s}.solw-star.s3{animation-delay:1.8s}
  @keyframes solw-tw{0%,100%{opacity:.15}50%{opacity:.95}}
  .solw-chat{position:fixed;bottom:94px;right:22px;width:min(370px,calc(100vw - 44px));height:490px;
    z-index:9999;display:none;flex-direction:column;border-radius:18px;overflow:hidden;
    background:rgba(12,10,24,.93);backdrop-filter:blur(18px);
    border:1px solid rgba(192,132,252,.22);box-shadow:0 24px 70px rgba(0,0,0,.6)}
  .solw-chat.open{display:flex;animation:solw-pop .22s ease-out}
  @keyframes solw-pop{from{opacity:0;transform:translateY(12px) scale(.97)}to{opacity:1;transform:none}}
  .solw-head{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.06);
    background:linear-gradient(90deg,rgba(192,132,252,.1),transparent)}
  .solw-dot{width:28px;height:28px;border-radius:50%;object-fit:cover;
    box-shadow:0 0 10px rgba(192,132,252,.5)}
  .solw-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
  .solw-msgs::-webkit-scrollbar{width:4px}.solw-msgs::-webkit-scrollbar-thumb{background:#334155;border-radius:2px}
  .solw-m{max-width:88%;font-size:12px;line-height:1.55;padding:8px 11px;border-radius:12px;white-space:pre-wrap}
  .solw-m.sol{background:rgba(26,21,46,.7);border:1px solid rgba(255,255,255,.05);color:#cbd5e1;border-top-left-radius:4px;align-self:flex-start}
  .solw-m.usr{background:rgba(99,102,241,.14);border:1px solid rgba(99,102,241,.3);color:#e2e8f0;border-top-right-radius:4px;align-self:flex-end}
  .solw-chips{display:flex;flex-wrap:wrap;gap:5px;padding:0 12px 8px}
  .solw-chip{font-size:10.5px;font-family:ui-monospace,monospace;padding:4px 9px;border-radius:7px;cursor:pointer;
    background:#0d1320;border:1px solid #1e293b;color:#94a3b8;transition:all .15s;white-space:nowrap}
  .solw-chip:hover{border-color:rgba(192,132,252,.55);color:#d8b4fe}
  .solw-chip.art{border-color:rgba(56,189,248,.3);color:#7dd3fc}
  .solw-in{display:flex;gap:8px;padding:10px 12px;border-top:1px solid rgba(255,255,255,.06)}
  .solw-in textarea{flex:1;background:#0d1320;border:1px solid #1e293b;border-radius:10px;color:#e2e8f0;
    font-size:12px;padding:8px 10px;resize:none;height:38px;outline:none;font-family:inherit}
  .solw-in textarea:focus{border-color:rgba(192,132,252,.5)}
  .solw-send{border:none;border-radius:10px;padding:0 13px;cursor:pointer;font-size:14px;color:#2e1065;
    background:linear-gradient(135deg,#d8b4fe,#a855f7);transition:filter .15s}
  .solw-send:hover{filter:brightness(1.12)}.solw-send:disabled{opacity:.4;cursor:default}
  `;

  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);

  // Bouton nébuleuse (image + repli CSS si elle ne charge pas)
  const btn = document.createElement('button');
  btn.className = 'solw-btn';
  btn.title = '✳ Laplace — interlocuteur principal du système';
  btn.innerHTML = `
    <div class="solw-mascot" role="img" aria-label="Laplace, l'assistant nébuleuse"></div>
    <span class="solw-star" style="top:8px;left:14px"></span>
    <span class="solw-star s2" style="bottom:10px;right:12px"></span>`;
  document.body.appendChild(btn);

  // Panneau de chat — Laplace ✳
  const chat = document.createElement('div');
  chat.className = 'solw-chat';
  chat.innerHTML = `
    <div class="solw-head">
      <img class="solw-dot" src="/static/nebula.png" alt=""
           onerror="this.outerHTML='<div class=\\'solw-dot\\' style=\\'background:radial-gradient(circle at 35% 35%,#f5d0fe,#7c3aed)\\'>✳</div>'">
      <div style="flex:1;min-width:0">
        <div style="font-size:12px;font-weight:600;color:#f1f5f9;font-family:Inter,sans-serif">✳ Laplace — créateur de nébuleuse</div>
        <div style="font-size:9.5px;color:#64748b;font-family:Inter,sans-serif">interlocuteur principal · SOL ☉ approuve · Mars ♂ forge les outils</div>
      </div>
      <span style="font-size:9px;padding:2px 7px;border-radius:99px;background:rgba(52,211,153,.1);color:#34d399;border:1px solid rgba(52,211,153,.25)">en ligne</span>
    </div>
    <div class="solw-msgs"></div>
    <div class="solw-chips"></div>
    <div class="solw-in">
      <textarea placeholder="Parlez à Laplace…"></textarea>
      <button class="solw-send">➤</button>
    </div>`;
  document.body.appendChild(chat);

  const msgs = chat.querySelector('.solw-msgs');
  const chips = chat.querySelector('.solw-chips');
  const input = chat.querySelector('textarea');
  const send = chat.querySelector('.solw-send');

  const addMsg = (text, who) => {
    const d = document.createElement('div');
    d.className = 'solw-m ' + who;
    d.textContent = text;
    msgs.appendChild(d);
    msgs.scrollTop = msgs.scrollHeight;
    return d;
  };
  const mdLite = s => s
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1');

  const addChips = (items) => {
    if (!items || !items.length) return;
    const wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:5px;padding:0 12px 8px';
    items.slice(0, 6).forEach(a => {
      const c = document.createElement('button');
      c.className = 'solw-chip art';
      c.textContent = (a.icon || '📄') + ' ' + (a.name || a);
      c.onclick = () => a.url
        ? window.open(a.url, '_blank')
        : window.open('/api/agent/artifact?path=' + encodeURIComponent(a.path), '_blank');
      wrap.appendChild(c);
    });
    chips.appendChild(wrap);
  };

  addMsg("✳ Laplace à votre écoute — je suis votre interlocuteur principal (je crée et j'améliore les agents). "
    + "Missions, dossiers, état du système… ou demandez un outil : « il me faut un outil pour calculer et visualiser "
    + "des données complexes » → Mars ♂, l'armurier, cherche d'abord l'open source, sinon Deimos ◦ conçoit la maquette "
    + "et Phobos ◂ la forge.", 'sol');
  const quick = ['état du système', 'budget', 'armurerie de Mars', 'constellation'];
  const qw = document.createElement('div');
  qw.style.cssText = 'display:flex;flex-wrap:wrap;gap:5px;padding:0 12px 8px';
  quick.forEach(q => {
    const c = document.createElement('button');
    c.className = 'solw-chip';
    c.textContent = q;
    c.onclick = () => ask(q);
    qw.appendChild(c);
  });
  chips.appendChild(qw);

  let busy = false;
  async function ask(text) {
    text = (text || input.value).trim();
    if (!text || busy) return;
    input.value = '';
    addMsg(text, 'usr');
    busy = true; send.disabled = true;
    const holder = addMsg('✳ …', 'sol');
    try {
      const r = await fetch('/api/cosmos/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await r.json();
      holder.textContent = mdLite(data.reply);
      const arts = (data.data && data.data.artifacts) || data.artifacts || [];
      if (arts.length) addChips(arts);
      // demande d'outil : proposer maquette / outil directement
      const req = data.data && data.data.request;
      if (req) {
        const items = [];
        if (req.maquette) items.push({ icon: '📐', name: 'maquette Deimos', url: '/api/mars/file?kind=maquette&id=' + encodeURIComponent(req.id) });
        if (req.outil) items.push({ icon: '⚒', name: 'outil de Phobos', url: '/api/mars/file?kind=outil&id=' + encodeURIComponent(req.id) });
        addChips(items);
      }
    } catch (e) { holder.textContent = '⚠️ ' + e.message; }
    busy = false; send.disabled = false;
    msgs.scrollTop = msgs.scrollHeight;
  }

  send.onclick = () => ask();
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
  });
  const open = () => { chat.classList.add('open'); input.focus(); };
  btn.onclick = () => chat.classList.toggle('open');
  document.addEventListener('open-laplace-chat', open);
  document.addEventListener('click', e => {
    if (!chat.classList.contains('open')) return;
    if (!chat.contains(e.target) && !btn.contains(e.target)) chat.classList.remove('open');
  });
})();
