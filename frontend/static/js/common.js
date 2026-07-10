// 共享工具
// ---- 登录态（localStorage）----
const Auth = {
  get token(){ return localStorage.getItem('juben_token') || ''; },
  get user(){ try{ return JSON.parse(localStorage.getItem('juben_user')||'null'); }catch(e){ return null; } },
  get uid(){ const u=Auth.user; return u ? u.id : null; },
  set(token, user){ localStorage.setItem('juben_token', token); localStorage.setItem('juben_user', JSON.stringify(user)); },
  clear(){ localStorage.removeItem('juben_token'); localStorage.removeItem('juben_user'); },
  get isLogin(){ return !!Auth.token; },
};
function _authHeaders(extra){
  const h = Object.assign({}, extra||{});
  if(Auth.token) h['Authorization'] = 'Bearer ' + Auth.token;
  return h;
}
const API = {
  get: (u) => fetch(u, {headers:_authHeaders()}).then(r => r.json()),
  post: (u, body) => fetch(u, {
    method: 'POST', headers: _authHeaders({'Content-Type': 'application/json'}),
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
