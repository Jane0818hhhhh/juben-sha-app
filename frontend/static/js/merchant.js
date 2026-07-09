// 店家端逻辑（默认店铺 id=1, owner id=1）
const app=document.getElementById('view');
const SHOP_ID=1;
const views={dash:renderDash,schedule:renderSchedule,scripts:renderScripts,dms:renderDMs};
function go(name){document.querySelectorAll('.tabbar a').forEach(a=>a.classList.toggle('active',a.dataset.v===name));(views[name]||renderDash)();window.scrollTo(0,0);}

async function renderDash(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">📊 经营看板</div><div id="dash" class="loading">加载中…</div></div>`;
  const d=await API.get(`/api/merchant/shops/${SHOP_ID}/dashboard`);
  document.getElementById('dash').innerHTML=`
    <div class="stat-grid">
      <div class="stat"><div class="num">${d.total_sessions}</div><div class="lbl">总场次</div></div>
      <div class="stat"><div class="num">${d.fill_rate}%</div><div class="lbl">满场率</div></div>
      <div class="stat"><div class="num">${d.total_players}</div><div class="lbl">累计玩家</div></div>
      <div class="stat"><div class="num">¥${d.revenue}</div><div class="lbl">预估流水</div></div>
    </div>
    <div class="sec-title">🔥 热门剧本</div>
    ${(d.hot_scripts||[]).map(h=>`<div class="card row" style="justify-content:space-between"><b>${esc(h.title)}</b><span class="gold">${h.count}场</span></div>`).join('')||'<div class="empty">暂无数据</div>'}`;
}

async function renderSchedule(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">📅 排期管理 <span class="more" onclick="openNew()">＋ 开场</span></div><div id="sch" class="loading">加载中…</div></div>`;
  const list=await API.get(`/api/merchant/shops/${SHOP_ID}/schedule`);
  document.getElementById('sch').innerHTML=list.map(s=>`
    <div class="card">
      <div class="row" style="justify-content:space-between"><b>${esc(s.script_title)}</b>
        <span class="status ${s.status}">${statusText(s.status)}</span></div>
      <div class="meta">🕐 ${s.start_time} · DM ${esc(s.dm_name)} · ¥${s.price}</div>
      <div class="progress"><i style="width:${Math.round(s.joined_players/s.need_players*100)}%"></i></div>
      <div class="row" style="justify-content:space-between;align-items:center">
        <span class="muted" style="font-size:13px">${s.joined_players}/${s.need_players} 人</span>
        <div>
          <button class="btn ghost" style="padding:5px 12px;font-size:12px" onclick="setStatus(${s.id},'confirmed')">确认成团</button>
          <button class="btn ghost" style="padding:5px 12px;font-size:12px" onclick="setStatus(${s.id},'cancelled')">取消</button>
        </div>
      </div>
    </div>`).join('')||'<div class="empty">暂无排期，点右上角开场</div>';
}
function statusText(s){return {recruiting:'招募中',full:'已满',confirmed:'已成团',finished:'已结束',cancelled:'已取消'}[s]||s;}
async function setStatus(id,st){await API.post(`/api/merchant/schedule/${id}/status`,{status:st});renderSchedule();}

async function openNew(){
  const scripts=await API.get('/api/player/scripts');
  const dms=await API.get(`/api/merchant/shops/${SHOP_ID}/dms`);
  app.innerHTML=`<div class="wrap"><div class="sec-title">＋ 新开场次</div>
    <div class="field"><label>剧本</label><select id="f-script">${scripts.map(s=>`<option value="${s.id}" data-p="${s.player_max}">${esc(s.title)}</option>`).join('')}</select></div>
    <div class="field"><label>DM</label><select id="f-dm"><option value="">未派单</option>${dms.map(d=>`<option value="${d.id}">${esc(d.nickname)}</option>`).join('')}</select></div>
    <div class="field"><label>开场时间</label><input id="f-time" type="datetime-local"></div>
    <div class="field"><label>人数</label><input id="f-need" type="number" value="6"></div>
    <div class="field"><label>价格</label><input id="f-price" type="number" value="198"></div>
    <button class="btn block" onclick="submitNew()">发布场次</button>
    <button class="btn block ghost" style="margin-top:8px" onclick="renderSchedule()">取消</button></div>`;
}
async function submitNew(){
  const t=document.getElementById('f-time').value;
  if(!t){alert('请选择开场时间');return;}
  const time=t.replace('T',' ');
  const r=await API.post('/api/merchant/schedule',{
    shop_id:SHOP_ID, script_id:+document.getElementById('f-script').value,
    dm_id:document.getElementById('f-dm').value?+document.getElementById('f-dm').value:null,
    start_time:time, need_players:+document.getElementById('f-need').value,
    price:+document.getElementById('f-price').value});
  if(r.error)alert(r.error);else{alert('场次已发布，玩家可在拼车广场看到并上车');renderSchedule();}
}

async function renderScripts(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">📚 剧本库</div><div id="sl" class="loading">加载中…</div></div>`;
  const list=await API.get('/api/player/scripts');
  document.getElementById('sl').innerHTML=list.map(s=>`<div class="card script-card">
    <img class="cover" src="${s.cover}" onerror="this.style.opacity=.3">
    <div class="info"><h3>${esc(s.title)} <span class="rate" style="font-size:13px">★${s.rating}</span></h3>
    <div class="meta">${s.category} · ${s.player_min}-${s.player_max}人 · 玩过${s.play_count}次</div>
    <div>${(s.tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div></div></div>`).join('');
}

async function renderDMs(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">🎙️ DM 花名册</div><div id="dl" class="loading">加载中…</div></div>`;
  const list=await API.get(`/api/merchant/shops/${SHOP_ID}/dms`);
  document.getElementById('dl').innerHTML=list.map(d=>`<div class="card">
    <div class="row" style="align-items:center"><div style="width:44px;height:44px;border-radius:50%;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:20px">🎙️</div>
    <div style="flex:1"><h3 style="font-size:15px">${esc(d.nickname)} <span class="rate" style="font-size:12px">★${d.rating}</span></h3>
    <div class="meta">擅长：${esc(d.good_at)} · ${d.fans}粉丝</div></div>
    <span class="status ${d.available?'recruiting':'full'}">${d.available?'可接单':'休息中'}</span></div></div>`).join('');
}

initAiBadge(); go('dash');
