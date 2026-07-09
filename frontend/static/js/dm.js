// DM 端逻辑（默认 DM 用户 id=2）
const app=document.getElementById('view');
const UID=2;
const views={orders:renderOrders,market:renderMarket,profile:renderProfile};
function go(name){document.querySelectorAll('.tabbar a').forEach(a=>a.classList.toggle('active',a.dataset.v===name));(views[name]||renderOrders)();window.scrollTo(0,0);}

async function renderOrders(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">🎬 我的场次</div><div id="ol" class="loading">加载中…</div></div>`;
  const list=await API.get('/api/dm/orders/'+UID);
  document.getElementById('ol').innerHTML=list.map(s=>`<div class="card">
    <div class="row" style="justify-content:space-between"><b>${esc(s.script_title)}</b>
      <span class="status ${s.status}">${statusText(s.status)}</span></div>
    <div class="meta">🏪 ${esc(s.shop_name)} · 🕐 ${s.start_time}</div>
    <div class="meta">${s.joined_players}/${s.need_players} 人 · ¥${s.price}</div></div>`).join('')||'<div class="empty">暂无带本场次</div>';
}
function statusText(s){return {recruiting:'招募中',full:'已满',confirmed:'已成团',finished:'已结束',cancelled:'已取消'}[s]||s;}

async function renderMarket(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">📢 接单市场</div>
    <p class="muted" style="margin:0 0 14px">这些场次还没派 DM，抢单接活</p><div id="ml" class="loading">加载中…</div></div>`;
  const list=await API.get('/api/dm/market');
  document.getElementById('ml').innerHTML=list.map(s=>`<div class="card">
    <div class="row" style="justify-content:space-between"><b>${esc(s.script_title)}</b><span class="tag">${esc(s.script_category)}</span></div>
    <div class="meta">🏪 ${esc(s.shop_name)} · 🕐 ${s.start_time} · ¥${s.price}</div>
    <button class="btn block" style="margin-top:8px" onclick="take(${s.id})">抢单接本</button></div>`).join('')||'<div class="empty">暂无可接场次（都已派单）</div>';
}
async function take(id){
  const r=await API.post('/api/dm/market/'+id+'/take',{user_id:UID});
  if(r.error)alert(r.error);else{alert('接单成功！已加入我的场次');go('orders');}
}

async function renderProfile(){
  const d=await API.get('/api/dm/profile/'+UID);
  app.innerHTML=`<div class="wrap"><div class="sec-title">👤 我的主页</div>
    <div class="card" style="text-align:center;padding:24px">
    <div style="width:64px;height:64px;border-radius:16px;background:linear-gradient(135deg,var(--purple),var(--rose));margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:30px">🎙️</div>
    <h3>${esc(d.nickname)} <span class="rate" style="font-size:14px">★${d.rating}</span></h3>
    <div class="muted" style="font-size:13px">${esc(d.shop_name)} · ${d.fans} 粉丝</div>
    <div style="margin-top:10px">${(d.good_at||'').split(',').map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
    <div style="margin-top:6px">${(d.style||'').split(',').map(t=>`<span class="tag purple">${esc(t)}</span>`).join('')}</div>
    <p style="margin-top:12px;font-size:14px">${esc(d.intro)}</p></div>
    <div class="card row" style="justify-content:space-between;align-items:center">
      <div><b>接单状态</b><div class="muted" style="font-size:12px">开启后玩家可在市场找到你</div></div>
      <button class="btn ${d.available?'':'ghost'}" id="av-btn" onclick="toggleAv(${d.available})">${d.available?'接单中':'已休息'}</button>
    </div></div>`;
}
async function toggleAv(cur){
  const r=await API.post('/api/dm/profile/'+UID+'/available',{available:!cur});
  renderProfile();
}

initAiBadge(); go('orders');
