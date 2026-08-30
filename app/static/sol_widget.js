/**
 * SOL ☉ — widget flottant : petit soleil rotatif avec éruptions solaires,
 * cliquable pour ouvrir le chat du système (n'importe quelle page).
 * Autonome (vanilla JS + CSS), sert /api/cosmos/chat.
 */
(function () {
  if (window.__solWidget) return;
  window.__solWidget = true;

  const CSS = `
  .solw-btn{position:fixed;bottom:22px;right:22px;width:58px;height:58px;border-radius:50%;
    cursor:pointer;z-index:9998;border:none;background:transparent;
    transition:transform .25s cubic-bezier(.34,1.56,.64,1)}
  .solw-btn:hover{transform:scale(1.12)}
  .solw-core{position:absolute;inset:11px;border-radius:50%;
    background:radial-gradient(circle at 38% 35%, #fef9c3 0%, #fcd34d 32%, #f59e0b 62%, #b45309 100%);
    box-shadow:0 0 18px 4px rgba(251,191,36,.45), 0 0 44px 12px rgba(251,146,60,.18);
    animation:solw-plasma 3.2s ease-in-out infinite}
  @keyframes solw-plasma{0%,100%{box-shadow:0 0 16px 3px rgba(251,191,36,.4),0 0 40px 10px rgba(251,146,60,.15);filter:brightness(1)}
    50%{box-shadow:0 0 24px 7px rgba(252,211,77,.6),0 0 60px 18px rgba(251,146,60,.28);filter:brightness(1.18)}}
  .solw-rays{position:absolute;inset:0;border-radius:50%;
    background:repeating-conic-gradient(rgba(252,211,77,.34) 0deg 3deg, transparent 3deg 22.5deg);
    -webkit-mask-image:radial-gradient(circle, transparent 46%, #000 52%, transparent 74%);
    mask-image:radial-gradient(circle, transparent 46%, #000 52%, transparent 74%);
    animation:solw-spin 26s linear infinite}
  @keyframes solw-spin{to{transform:rotate(360deg)}}
  .solw-flare{position:absolute;width:7px;height:7px;border-radius:50%;
    background:radial-gradient(circle,#fde68a 0%,#f59e0b 55%,transparent 75%);
    opacity:0;animation:solw-erupt 4.6s ease-out infinite}
  .solw-flare.f2{animation-delay:1.5s}.solw-flare.f3{animation-delay:3s}
  @keyframes solw-erupt{0%{opacity:0;transform:translate(24px,24px) scale(.4)}
    8%{opacity:.95}45%{opacity:.55}100%{opacity:0;transform:translate(46px,10px) scale(1.5)}}
  .solw-chat{position:fixed;bottom:92px;right:22px;width:min(360px,calc(100vw - 44px));height:480px;
    z-index:9999;display:none;flex-direction:column;border-radius:18px;overflow:hidden;
    background:rgba(10,15,28,.92);backdrop-filter:blur(18px);
    border:1px solid rgba(251,191,36,.18);box-shadow:0 24px 70px rgba(0,0,0,.6)}
  .solw-chat.open{display:flex;animation:solw-pop .22s ease-out}
  @keyframes solw-pop{from{opacity:0;transform:translateY(12px) scale(.97)}to{opacity:1;transform:none}}
  .solw-head{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.06);
    background:linear-gradient(90deg,rgba(251,191,36,.08),transparent)}
  .solw-dot{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-size:14px;background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.3);color:#fcd34d}
  .solw-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
  .solw-msgs::-webkit-scrollbar{width:4px}.solw-msgs::-webkit-scrollbar-thumb{background:#334155;border-radius:2px}
  .solw-m{max-width:88%;font-size:12px;line-height:1.55;padding:8px 11px;border-radius:12px;white-space:pre-wrap}
  .solw-m.sol{background:rgba(21,29,46,.7);border:1px solid rgba(255,255,255,.05);color:#cbd5e1;border-top-left-radius:4px;align-self:flex-start}
  .solw-m.usr{background:rgba(99,102,241,.14);border:1px solid rgba(99,102,241,.3);color:#e2e8f0;border-top-right-radius:4px;align-self:flex-end}
  .solw-chips{display:flex;flex-wrap:wrap;gap:5px;padding:0 12px 8px}
  .solw-chip{font-size:10.5px;font-family:ui-monospace,monospace;padding:4px 9px;border-radius:7px;cursor:pointer;
    background:#0d1320;border:1px solid #1e293b;color:#94a3b8;transition:all .15s;white-space:nowrap}
  .solw-chip:hover{border-color:rgba(251,191,36,.5);color:#fcd34d}
  .solw-chip.art{border-color:rgba(56,189,248,.3);color:#7dd3fc}
  .solw-in{display:flex;gap:8px;padding:10px 12px;border-top:1px solid rgba(255,255,255,.06)}
  .solw-in textarea{flex:1;background:#0d1320;border:1px solid #1e293b;border-radius:10px;color:#e2e8f0;
    font-size:12px;padding:8px 10px;resize:none;height:38px;outline:none;font-family:inherit}
  .solw-in textarea:focus{border-color:rgba(251,191,36,.5)}
  .solw-send{border:none;border-radius:10px;padding:0 13px;cursor:pointer;font-size:14px;color:#78350f;
    background:linear-gradient(135deg,#fcd34d,#f59e0b);transition:filter .15s}
  .solw-send:hover{filter:brightness(1.1)}.solw-send:disabled{opacity:.4;cursor:default}
  `;

  const style = document.createElement('style');
  style.textContent = CSS;
  document.head.appendChild(style);

  // Bouton soleil
  const btn = document.createElement('button');
  btn.className = 'solw-btn';
  btn.title = '☉ SOL — chat du système';
  btn.innerHTML = `
    <div class="solw-rays"></div>
    <div class="solw-core"></div>
    <span class="solw-flare" style="top:6px;left:24px"></span>
    <span class="solw-flare f2" style="bottom:8px;left:12px"></span>
    <span class="solw-flare f3" style="top:20px;right:4px"></span>`;
  document.body.appendChild(btn);

  // Panneau de chat
  const chat = document.createElement('div');
  chat.className = 'solw-chat';
  chat.innerHTML = `
    <div class="solw-head">
      <div class="solw-dot">☉</div>
      <div style="flex:1;min-width:0">
        <div style="font-size:12px;font-weight:600;color:#f1f5f9;font-family:Inter,sans-serif">SOL — orchestrateur</div>
        <div style="font-size:9.5px;color:#64748b;font-family:Inter,sans-serif">le système vous écoute · toutes les interactions sont approuvées</div>
      </div>
      <span style="font-size:9px;padding:2px 7px;border-radius:99px;background:rgba(52,211,153,.1);color:#34d399;border:1px solid rgba(52,211,153,.25)">en ligne</span>
    </div>
    <div class="solw-msgs"></div>
    <div class="solw-chips"></div>
    <div class="solw-in">
      <textarea placeholder="Parlez à SOL…"></textarea>
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

  const addChips = (label, items, artifact) => {
    if (!items || !items.length) return;
    const wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:5px;padding:0 12px 8px';
    items.slice(0, 6).forEach(a => {
      const c = document.createElement('button');
      c.className = 'solw-chip' + (artifact ? ' art' : '');
      c.textContent = (a.icon || '📄') + ' ' + (a.name || a);
      c.onclick = () => window.open('/api/agent/artifact?path=' + encodeURIComponent(a.path), '_blank');
      wrap.appendChild(c);
    });
    chips.appendChild(wrap);
  };

  addMsg("☉ SOL à l'écoute. Vues rapides ci-dessous — ou posez votre question, lancez une mission (« mission : méta-analyse attention ») ou un dossier (« je veux améliorer le BTP avec l'IA »).", 'sol');
  const quick = ['état du système', 'budget', 'interactions', 'constellation'];
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
    const holder = addMsg('☉ …', 'sol');
    try {
      const r = await fetch('/api/cosmos/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await r.json();
      holder.textContent = data.reply;
      const arts = (data.data && data.data.artifacts) || data.artifacts || [];
      if (arts.length) addChips('artifacts', arts, true);
    } catch (e) { holder.textContent = '⚠️ ' + e.message; }
    busy = false; send.disabled = false;
    msgs.scrollTop = msgs.scrollHeight;
  }

  send.onclick = () => ask();
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
  });
  btn.onclick = () => chat.classList.toggle('open');
  document.addEventListener('click', e => {
    if (!chat.classList.contains('open')) return;
    if (!chat.contains(e.target) && !btn.contains(e.target)) chat.classList.remove('open');
  });
})();
