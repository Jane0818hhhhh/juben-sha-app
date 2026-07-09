// 共享工具
const API = {
  get: (u) => fetch(u).then(r => r.json()),
  post: (u, body) => fetch(u, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body || {})
  }).then(r => r.json()),
};
function stars(n){ n=Math.round(n||0); return '★'.repeat(n)+'☆'.repeat(5-n); }
function esc(s){ return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function initAiBadge(){
  fetch('/api/system/info').then(r=>r.json()).then(d=>{
    const b=document.getElementById('ai-badge'); if(!b)return;
    if(d.llm_ready){b.textContent='AI · '+d.model;b.className='badge on';}
    else{b.textContent='AI 降级模式';}
  });
}
