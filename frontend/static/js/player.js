// 玩家端 —— 拼车广场筛选 + 千岛测本 + 角色陪伴
const app = document.getElementById('view');
let curScripts = [];
let plazaFilter = { city: '', date: '', seat: '' };
let seatTypes = ['全部','普通位','补贴位','CP位','恋陪','陪伴位'];

const views = { home:renderHome, test:renderTest, plaza:renderPlaza, find:renderFind, roles:renderRoles, mine:renderMine };
function go(name){
  document.querySelectorAll('.tabbar a').forEach(a=>a.classList.toggle('active', a.dataset.v===name));
  (views[name]||renderHome)();
  window.scrollTo(0,0);
}

// ---------- 首页 ----------
async function renderHome(){
  app.innerHTML = `<div class="hero"><h2>今天，想玩点什么本？</h2>
    <p>搜索你想玩的本，测测你适合演哪个角色</p></div>
    <div class="wrap">
      <div class="search-bar" style="margin-bottom:16px">
        <input id="home-search" placeholder="搜索剧本名称，如「流氓叙事」…" onkeydown="if(event.key==='Enter')searchAndTest(document.getElementById('home-search').value)">
        <button class="btn" onclick="searchAndTest(document.getElementById('home-search').value)">搜本测角色</button>
      </div>
      <div class="sec-title">🔥 热门拼车 <span class="more" onclick="go('plaza')">全部 ›</span></div>
      <div id="home-sessions" class="loading">加载中…</div>
      <div class="sec-title">📊 2025 高分好本 <span class="more" onclick="go('find')">全部 ›</span></div>
      <div id="home-scripts" class="loading">加载中…</div>
    </div>`;
  const ss = await API.get('/api/player/sessions');
  document.getElementById('home-sessions').innerHTML = ss.slice(0,2).map(sessionCard).join('')||'<div class="empty">暂无拼车局</div>';
  const sc = await API.get('/api/player/scripts');
  curScripts = sc;
  // 高分排序
  sc.sort((a,b)=>b.rating-a.rating);
  document.getElementById('home-scripts').innerHTML = sc.slice(0,5).map(scriptCard).join('');
}

function searchAndTest(kw){
  if(!kw.trim()){alert('请输入剧本名称');return;}
  const found = curScripts.filter(s=>s.title.includes(kw.trim()));
  if(found.length===0){alert('未找到匹配的剧本，试试搜索其他关键词');return;}
  if(found.length===1){openRoleTest(found[0]);return;}
  // 多个匹配：展示选择列表
  app.innerHTML = `<div class="wrap"><div class="sec-title">🔍 搜索「${esc(kw)}」</div>
    <p class="muted" style="margin:0 0 14px">找到 ${found.length} 个匹配剧本，点击进入测角色</p>
    ${found.map(s=>`<div class="card script-card" onclick="openRoleTest(curScripts.find(x=>x.id===${s.id}))">
      <img class="cover" src="${s.cover}" onerror="this.style.opacity=.3">
      <div class="info"><h3>${esc(s.title)} <span class="rate">★${s.rating}</span></h3>
      <div class="meta">${s.category} · ${s.player_min}-${s.player_max}人</div>
      <div>${(s.tags||[]).slice(0,3).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
      <button class="btn ghost" style="margin-top:6px;padding:5px 12px;font-size:12px">测适合角色 ›</button></div></div>`).join('')}</div>`;
}

// ---------- 千岛模式：测角色 ----------
let roleQuiz=[], roleAnswers={}, roleData=null;
async function openRoleTest(script){
  roleData = script;
  roleQuiz = []; roleAnswers = {};
  const r = await API.get('/api/player/scripts/'+script.id+'/role-quiz');
  roleQuiz = r.questions || [];
  roleData.roles = r.roles || [];
  app.innerHTML = `<div class="wrap">
    <div class="sec-title">🎭 测适合角色</div>
    <div class="card" style="text-align:center;padding:18px">
      <h3>${esc(r.script_title)}</h3>
      <div class="meta">${script.category} · ${script.player_min}-${script.player_max}人 · ★${script.rating}</div>
      <div style="margin-top:8px">${(script.tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
      <p class="muted" style="font-size:13px;margin-top:8px">${(r.roles||[]).map(r=>r.name).join(' · ')}</p>
    </div>
    <div id="role-quiz"></div>
    <button class="btn block" id="submit-role" onclick="submitRoleTest()" disabled>完成测试 · 匹配我的角色</button>
  </div>`;
  renderRoleQuiz();
}
function renderRoleQuiz(){
  const box=document.getElementById('role-quiz');
  if(!box)return;
  box.innerHTML = roleQuiz.map(q=>`<div class="q-block"><h3>${esc(q.title)}</h3>
    ${q.options.map(o=>`<div class="opt" data-q="${q.id}" data-k="${o.key}"
       onclick="pickRole('${q.id}','${o.key}',this)"><span class="k">${o.key}</span>${esc(o.text)}</div>`).join('')}
    </div>`).join('');
}
function pickRole(qid,k,el){
  roleAnswers[qid]=k;
  el.parentElement.querySelectorAll('.opt').forEach(o=>o.classList.remove('sel'));
  el.classList.add('sel');
  const btn=document.getElementById('submit-role');
  if(btn) btn.disabled = Object.keys(roleAnswers).length<roleQuiz.length;
}
async function submitRoleTest(){
  const btn=document.getElementById('submit-role'); btn.textContent='AI 匹配中…'; btn.disabled=true;
  const r = await API.post('/api/player/scripts/'+roleData.id+'/test-role',{answers:roleAnswers});
  app.innerHTML = `<div class="wrap">
    <div class="card" style="background:linear-gradient(160deg,#2a2140,#1a1526);text-align:center;padding:24px">
      <div class="muted" style="font-size:13px">《${esc(r.script_title)}》· 你的角色</div>
      <h2 class="gold" style="margin:8px 0">${esc(r.primary)}</h2>
      <p style="font-size:14px">${esc(r.primary_reason)}</p>
      <div class="divider"></div>
      <div style="font-size:13px;color:var(--muted)">次推荐：<b>${esc(r.secondary||'')}</b> — ${esc(r.secondary_reason||'')}</div>
      <div class="divider"></div>
      <p style="font-size:13px">${esc(r.analysis||'')}</p>
      <div class="tag purple" style="margin-top:8px">💡 ${esc(r.play_tip||'')}</div>
    </div>
    <button class="btn block" style="margin-top:12px" onclick="go('plaza')">去拼这个本 ›</button>
    <button class="btn block ghost" style="margin-top:8px" onclick="renderHome()">搜其他本</button>
  </div>`;
}

// ---------- 拼车广场（城市+日期+补位类型筛选）----------
async function renderPlaza(){
  app.innerHTML = `<div class="wrap">
    <div class="sec-title">🚗 拼车广场</div>
    <div class="filter-bar">
      <select id="f-city" onchange="applyPlazaFilter()"><option value="">全部城市</option><option value="成都">成都</option><option value="北京">北京</option></select>
      <input id="f-date" type="date" onchange="applyPlazaFilter()" placeholder="选择日期">
      <select id="f-seat" onchange="applyPlazaFilter()">${seatTypes.map(t=>`<option value="${t==='全部'?'':t}">${t}</option>`).join('')}</select>
    </div>
    <div id="plaza-list" class="loading">加载中…</div>
  </div>`;
  await loadPlaza();
}
async function applyPlazaFilter(){
  plazaFilter.city = document.getElementById('f-city')?.value||'';
  plazaFilter.date = document.getElementById('f-date')?.value||'';
  plazaFilter.seat = document.getElementById('f-seat')?.value||'';
  loadPlaza();
}
async function loadPlaza(){
  const box = document.getElementById('plaza-list'); if(!box)return;
  box.innerHTML='<div class="loading">加载中…</div>';
  let ss = await API.get('/api/player/sessions');
  // 前端筛选
  if(plazaFilter.city) ss = ss.filter(s=>s.city===plazaFilter.city);
  if(plazaFilter.date) ss = ss.filter(s=>s.start_time&&s.start_time.startsWith(plazaFilter.date));
  if(plazaFilter.seat) ss = ss.filter(s=>s.seat_type===plazaFilter.seat);
  box.innerHTML = ss.map(sessionCard).join('')||'<div class="empty">暂无匹配的拼车局<br><span style="font-size:12px">试试放宽筛选条件</span></div>';
}

// ---------- 卡片模板 ----------
function scriptCard(s){
  return `<div class="card script-card" onclick="openRoleTest(curScripts.find(x=>x.id===${s.id}))">
    <img class="cover" src="${s.cover}" onerror="this.style.opacity=.3">
    <div class="info"><h3>${esc(s.title)} <span class="rate">★${s.rating}</span></h3>
      <div class="meta">${s.category} · ${s.player_min}-${s.player_max}人 · ${Math.round(s.duration/60)}h · 难度${'●'.repeat(s.difficulty)}</div>
      <div>${(s.tags||[]).slice(0,3).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
      <button class="btn ghost" style="margin-top:6px;padding:5px 12px;font-size:12px">测适合角色 ›</button>
    </div></div>`;
}
function sessionCard(s){
  const pct = Math.round(s.joined_players/s.need_players*100);
  const av = (s.members||[]).map(m=>`<span>${esc((m.nickname||'?')[0])}</span>`).join('');
  const seatColor = s.seat_type==='CP位'?'rose':s.seat_type==='恋陪'?'purple':s.seat_type==='补贴位'?'tag':s.seat_type==='陪伴位'?'purple':'';
  return `<div class="card session-card" onclick="sessionDetail(${s.id})">
    <div class="head">
      <div><h3 style="font-size:16px">${esc(s.script_title)}
        <span class="tag ${seatColor}" style="font-size:10px">${esc(s.seat_type||'普通位')}</span></h3>
        <div class="meta">${esc(s.shop_name)} · ${s.start_time} · ${esc(s.city||'')}</div></div>
      <span class="status ${s.status}">${s.status==='full'?'已满':'招募中'}</span>
    </div>
    <div class="progress"><i style="width:${pct}%"></i></div>
    <div class="row" style="justify-content:space-between;align-items:center">
      <div class="avatars">${av}<span style="color:var(--muted)">${s.joined_players}/${s.need_players}</span></div>
      <div><span class="gold" style="font-weight:700">¥${s.price}</span> <span class="muted" style="font-size:12px">DM ${esc(s.dm_name)}</span></div>
    </div>
    <div class="meta" style="margin-top:6px">💬 ${esc(s.note||'')}</div>
  </div>`;
}

// ---------- 大问卷推本（保留在 test tab 作为辅助入口）----------
let qList=[], answers={};
async function renderTest(){
  app.innerHTML = `<div class="wrap">
    <div class="sec-title">🔮 大问卷推本（辅助入口）</div>
    <p class="muted" style="margin:0 0 16px">不确定玩什么？答题让 AI 给你推本。</p>
    <p class="muted" style="margin:0 0 16px;font-size:12px">💡 推荐用首页「搜索→测角色」功能，更精准</p>
    <div id="quiz"></div></div>`;
  qList = await API.get('/api/player/test/questionnaire');
  answers={};
  renderQuiz();
}
function renderQuiz(){
  const box=document.getElementById('quiz'); if(!box)return;
  box.innerHTML = qList.map(q=>`<div class="q-block"><h3>${esc(q.title)}</h3>
    ${q.options.map(o=>`<div class="opt" data-q="${q.id}" data-k="${o.key}" onclick="pick('${q.id}','${o.key}',this)"><span class="k">${o.key}</span>${esc(o.text)}</div>`).join('')}</div>`).join('')+
    `<button class="btn block" id="submit-test" onclick="submitTest()" disabled>完成测试 · 生成推荐</button>`;
}
function pick(qid,k,el){answers[qid]=k;el.parentElement.querySelectorAll('.opt').forEach(o=>o.classList.remove('sel'));el.classList.add('sel');document.getElementById('submit-test').disabled=Object.keys(answers).length<qList.length;}
async function submitTest(){
  const btn=document.getElementById('submit-test'); btn.textContent='AI 分析中…'; btn.disabled=true;
  const r=await API.post('/api/player/test/submit',{answers});
  app.innerHTML=`<div class="wrap">
    <div class="card" style="background:linear-gradient(160deg,#2a2140,#1a1526);text-align:center;padding:24px">
      <div class="muted" style="font-size:13px">你的玩家人设</div>
      <h2 class="gold" style="margin:8px 0">${esc(r.persona_title)}</h2>
      <div>${(r.tags||[]).map(t=>`<span class="tag purple">${esc(t)}</span>`).join('')}</div>
      <p style="margin-top:12px;font-size:14px">${esc(r.analysis)}</p></div>
    <div class="sec-title">为你推荐</div>
    ${(r.recommend_scripts||[]).map(rec=>`<div class="card script-card" onclick="openRoleTest(curScripts.find(x=>x.id===${rec.id}))">
      <img class="cover" src="${rec.cover||''}" onerror="this.style.opacity=.3">
      <div class="info"><h3>${esc(rec.title)} <span class="rate">★${rec.rating||''}</span></h3>
      <p class="muted" style="font-size:13px">${esc(rec.reason)}</p>
      <button class="btn ghost" style="margin-top:8px;padding:6px 14px;font-size:13px">进入测角色 ›</button></div></div>`).join('')}
    <button class="btn block ghost" onclick="renderTest()">重新测一次</button></div>`;
}

// ---------- 找店找本（高分好本用真实数据）----------
async function renderFind(){
  app.innerHTML = `<div class="wrap"><div class="sec-title">🔍 找本 · 找店 · 找 DM</div></div>
    <div class="pill-row" id="cats"></div>
    <div class="pill-row">
      <span class="pill active" onclick="findTab('script',this)">剧本</span>
      <span class="pill" onclick="findTab('shop',this)">门店</span>
      <span class="pill" onclick="findTab('dm',this)">DM</span>
    </div>
    <div id="find-list" class="wrap loading">加载中…</div>`;
  const cats=['全部','推理','情感','机制','欢乐','恐怖'];
  document.getElementById('cats').innerHTML = cats.map((c,i)=>`<span class="pill ${i===0?'active':''}" onclick="filterCat('${c}',this)">${c}</span>`).join('');
  findTab('script');
}
let findMode='script', findCat='全部';
function filterCat(c,el){findCat=c;el.parentElement.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));el.classList.add('active');loadFind();}
function findTab(m,el){findMode=m;if(el){el.parentElement.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));el.classList.add('active');}loadFind();}
async function loadFind(){
  const box=document.getElementById('find-list'); box.innerHTML='<div class="loading">加载中…</div>';
  if(findMode==='script'){
    const q = findCat==='全部'?'':'?category='+encodeURIComponent(findCat);
    const sc = await API.get('/api/player/scripts'+q);
    sc.sort((a,b)=>b.rating-a.rating);
    box.innerHTML = sc.map(s=>`<div class="card script-card" onclick="openRoleTest(s)">
      <img class="cover" src="${s.cover}" onerror="this.style.opacity=.3">
      <div class="info"><h3>${esc(s.title)} <span class="rate">★${s.rating}</span> <span class="muted" style="font-size:11px">${s.play_count}人玩过</span></h3>
      <div class="meta">${s.category} · ${s.player_min}-${s.player_max}人 · ${Math.round(s.duration/60)}h</div>
      <div>${(s.tags||[]).slice(0,3).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
      <p class="muted" style="font-size:12px;margin-top:4px">${esc(s.intro||'').substring(0,60)}…</p>
      <button class="btn ghost" style="margin-top:4px;padding:4px 10px;font-size:11px">测适合角色 ›</button></div></div>`).join('');
  }else if(findMode==='shop'){
    const sh=await API.get('/api/player/shops');
    box.innerHTML=sh.map(s=>`<div class="card" onclick="shopDetail(${s.id})">
      <div class="row"><img class="cover" style="width:70px;height:70px;border-radius:10px;object-fit:cover" src="${s.cover}" onerror="this.style.opacity=.3">
      <div><h3 style="font-size:16px">${esc(s.name)} <span class="rate">★${s.rating}</span></h3>
      <div class="meta">${esc(s.city)} · ${s.room_count}间房</div>
      <p class="muted" style="font-size:12px">${esc(s.intro)}</p></div></div></div>`).join('');
  }else{
    const dms=await API.get('/api/player/dms');
    box.innerHTML=dms.map(d=>`<div class="card"><div class="row" style="align-items:center">
      <div style="width:48px;height:48px;border-radius:50%;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:22px">🎙️</div>
      <div style="flex:1"><h3 style="font-size:15px">${esc(d.nickname)} <span class="rate" style="font-size:12px">★${d.rating}</span></h3>
      <div class="meta">${esc(d.shop_name)} · ${d.fans}粉丝</div>
      <div>${(d.good_at||'').split(',').map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div></div></div>
      <p class="muted" style="font-size:12px;margin-top:6px">${esc(d.intro)}</p></div>`).join('');
  }
}

// ---------- 角色陪伴 ----------
async function renderRoles(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">💬 角色陪伴</div>
    <p class="muted" style="margin:0 0 14px">意犹未尽？和剧本里的角色继续聊聊</p>
    <div id="role-list" class="loading">加载中…</div></div>`;
  const rs=await API.get('/api/player/roles');
  document.getElementById('role-list').innerHTML=rs.map(r=>`<div class="card" onclick="openChat('${esc(r.name)}','${esc(r.script)}')">
    <div class="row" style="align-items:center">
    <div style="width:54px;height:54px;border-radius:14px;background:linear-gradient(135deg,var(--purple),var(--rose));display:flex;align-items:center;justify-content:center;font-size:26px">🎭</div>
    <div style="flex:1"><h3 style="font-size:16px">${esc(r.name)}</h3><div class="meta">${esc(r.script)}</div>
    <p class="muted" style="font-size:12px">${esc(r.tagline)}</p></div>
    <div class="gold" style="font-size:20px">›</div></div></div>`).join('');
}
let chatHistory=[], chatRole='';
function openChat(name,script){
  chatRole=name; chatHistory=[];
  document.querySelector('.tabbar').style.display='none';
  app.innerHTML=`<div class="topbar" style="position:sticky"><h1 style="font-size:16px">🎭 ${esc(name)} <span class="muted" style="font-size:12px;font-weight:400">${esc(script)}</span></h1>
    <span class="badge" onclick="closeChat()" style="cursor:pointer">返��</span></div>
    <div class="chat-list" id="chat" style="padding-bottom:80px">
      <div class="msg ai">（${esc(name)}正静静看着你……说点什么吧）</div></div>
    <div class="chat-input"><input id="chat-in" placeholder="对 ${esc(name)} 说…" onkeydown="if(event.key==='Enter')sendChat()">
      <button class="btn" onclick="sendChat()">发送</button></div>`;
}
function closeChat(){document.querySelector('.tabbar').style.display='flex';go('roles');}
async function sendChat(){
  const inp=document.getElementById('chat-in'); const msg=inp.value.trim(); if(!msg)return;
  const box=document.getElementById('chat'); box.innerHTML+=`<div class="msg me">${esc(msg)}</div>`; inp.value=''; box.scrollTop=box.scrollHeight;
  chatHistory.push({role:'user',content:msg});
  const tip=document.createElement('div'); tip.className='msg ai'; tip.textContent='…'; box.appendChild(tip); box.scrollTop=box.scrollHeight;
  const r=await API.post('/api/player/roles/chat',{role_name:chatRole,message:msg,history:chatHistory});
  tip.textContent=r.reply||'（信号中断）'; chatHistory.push({role:'assistant',content:r.reply||''}); box.scrollTop=box.scrollHeight;
}

function renderMine(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">👤 我的</div>
    <div class="card" style="text-align:center;padding:24px">
    <div style="width:64px;height:64px;border-radius:50%;background:var(--card2);margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:30px">🕵️</div>
    <h3>情感玩家Nana</h3><div class="muted" style="font-size:13px">成都 · 情感/沉浸/爱BE</div></div>
    <div class="card"><b>我的局</b><p class="muted" style="font-size:13px;margin-top:6px">· 《流氓叙事》CP位（明天18:00）<br>· 《如故》（已满员）</p></div>
    <div class="card"><b>测本记录</b><p class="muted" style="font-size:13px;margin-top:6px">《流氓叙事》→ 推荐角色：程走柳</p></div>
    <button class="btn block ghost" onclick="location.href='/'">切换身份</button></div>`;
}

async function scriptDetail(id){const s=await API.get('/api/player/scripts/'+id);openRoleTest(s);}
async function sessionDetail(id){
  const s=await API.get('/api/player/sessions/'+id);
  const ok=s.status==='recruiting';
  if(confirm(`《${s.script_title}》\n${s.shop_name} · ${s.start_time} · ${s.city}\nDM ${s.dm_name} · ¥${s.price} · ${s.seat_type}\n${s.joined_players}/${s.need_players}\n${s.note}\n\n${ok?'点确定上车拼局':'该局已满员'}`)){
    if(ok){const r=await API.post('/api/player/sessions/'+id+'/join',{user_id:5});if(r.error)alert(r.error);else{alert('上车成功！');go('plaza');}}
  }
}
async function shopDetail(id){
  const s=await API.get('/api/player/shops/'+id);
  alert(`${s.name}\n${s.address}\n评分 ★${s.rating}\n\n${s.intro}\n\nDM：${(s.dms||[]).map(d=>d.nickname).join('、')}`);
}

initAiBadge(); go('home');
