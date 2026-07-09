// 玩家端逻辑
const app = document.getElementById('view');
let curScripts = [];

// ---------- 视图路由 ----------
const views = {
  home: renderHome, test: renderTest, plaza: renderPlaza,
  find: renderFind, roles: renderRoles, mine: renderMine,
};
function go(name){
  document.querySelectorAll('.tabbar a').forEach(a=>a.classList.toggle('active', a.dataset.v===name));
  (views[name]||renderHome)();
  window.scrollTo(0,0);
}

// ---------- 首页 ----------
async function renderHome(){
  app.innerHTML = `
    <div class="hero"><h2>今天，想玩点什么本？</h2>
      <p>测一测你适合的本，或直接上车拼局</p></div>
    <div class="wrap">
      <button class="btn block" onclick="go('test')" style="margin-bottom:14px">🔮 智能测本 · 找到你的本命本</button>
      <div class="sec-title">🔥 热门拼车局 <span class="more" onclick="go('plaza')">全部 ›</span></div>
      <div id="home-sessions" class="loading">加载中…</div>
      <div class="sec-title">🎭 高分好本 <span class="more" onclick="go('find')">全部 ›</span></div>
      <div id="home-scripts" class="loading">加载中…</div>
    </div>`;
  const ss = await API.get('/api/player/sessions');
  document.getElementById('home-sessions').innerHTML = ss.slice(0,2).map(sessionCard).join('') || '<div class="empty">暂无拼车局</div>';
  const sc = await API.get('/api/player/scripts');
  curScripts = sc;
  document.getElementById('home-scripts').innerHTML = sc.slice(0,3).map(scriptCard).join('');
}

// ---------- 卡片模板 ----------
function scriptCard(s){
  return `<div class="card script-card" onclick="scriptDetail(${s.id})">
    <img class="cover" src="${s.cover}" onerror="this.style.opacity=.3">
    <div class="info">
      <h3>${esc(s.title)} <span class="rate" style="font-size:13px">★${s.rating}</span></h3>
      <div class="meta">${s.category} · ${s.player_min}-${s.player_max}人 · ${Math.round(s.duration/60)}h · 难度${'●'.repeat(s.difficulty)}</div>
      <div>${(s.tags||[]).slice(0,3).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>
      ${s.is_be?'<span class="tag rose">BE</span>':''}${s.has_horror?'<span class="tag rose">恐怖</span>':''}
    </div></div>`;
}
function sessionCard(s){
  const pct = Math.round(s.joined_players/s.need_players*100);
  const av = (s.members||[]).map(m=>`<span>${esc(m.nickname[0]||'?')}</span>`).join('');
  return `<div class="card session-card" onclick="sessionDetail(${s.id})">
    <div class="head">
      <div><h3 style="font-size:16px">${esc(s.script_title)}</h3>
        <div class="meta">${esc(s.shop_name)} · ${s.start_time}</div></div>
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

// ---------- 测本 ----------
let qList=[], answers={};
async function renderTest(){
  app.innerHTML = `<div class="wrap"><div class="sec-title">🔮 智能测本</div>
    <p class="muted" style="margin:0 0 16px">回答几个问题，AI 帮你匹配本命本和角色</p>
    <div id="quiz"></div></div>`;
  qList = await API.get('/api/player/test/questionnaire');
  answers={};
  renderQuiz();
}
function renderQuiz(){
  const box=document.getElementById('quiz');
  box.innerHTML = qList.map(q=>`
    <div class="q-block"><h3>${esc(q.title)}</h3>
    ${q.options.map(o=>`<div class="opt" data-q="${q.id}" data-k="${o.key}"
       onclick="pick('${q.id}','${o.key}',this)"><span class="k">${o.key}</span>${esc(o.text)}</div>`).join('')}
    </div>`).join('') +
    `<button class="btn block" id="submit-test" onclick="submitTest()" disabled>完成测试 · 生成推荐</button>`;
}
function pick(qid,k,el){
  answers[qid]=k;
  el.parentElement.querySelectorAll('.opt').forEach(o=>o.classList.remove('sel'));
  el.classList.add('sel');
  document.getElementById('submit-test').disabled = Object.keys(answers).length<qList.length;
}
async function submitTest(){
  const btn=document.getElementById('submit-test');
  btn.textContent='AI 分析中…'; btn.disabled=true;
  const r=await API.post('/api/player/test/submit',{answers});
  app.innerHTML=`<div class="wrap">
    <div class="card" style="background:linear-gradient(160deg,#2a2140,#1a1526);text-align:center;padding:24px">
      <div style="font-size:13px" class="muted">你的玩家人设</div>
      <h2 class="gold" style="margin:8px 0">${esc(r.persona_title)}</h2>
      <div>${(r.tags||[]).map(t=>`<span class="tag purple">${esc(t)}</span>`).join('')}</div>
      <p style="margin-top:12px;font-size:14px">${esc(r.analysis)}</p>
      <div class="divider"></div>
      <div class="muted" style="font-size:13px">🎭 适合角色：${esc(r.suggest_role||'')}</div>
    </div>
    <div class="sec-title">为你推荐（可直接找局）</div>
    ${(r.recommend_scripts||[]).map(rec=>`
      <div class="card script-card" onclick="scriptDetail(${rec.id})">
        <img class="cover" src="${rec.cover||''}" onerror="this.style.opacity=.3">
        <div class="info"><h3>${esc(rec.title)} <span class="rate" style="font-size:13px">★${rec.rating||''}</span></h3>
        <p class="muted" style="font-size:13px">${esc(rec.reason)}</p>
        <button class="btn ghost" style="margin-top:8px;padding:6px 14px;font-size:13px">去拼这个本 ›</button></div>
      </div>`).join('')}
    <button class="btn block ghost" onclick="renderTest()" style="margin-top:8px">重新测一次</button>
    </div>`;
}

// ---------- 拼本广场 ----------
async function renderPlaza(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">🚗 拼车广场</div></div>
    <div id="plaza-list" class="wrap loading">加载中…</div>
    <div class="fab" onclick="alert('发起拼局：选本→选店→选时间→设置人数（Demo 已支持后端 API）')">＋</div>`;
  const ss=await API.get('/api/player/sessions');
  document.getElementById('plaza-list').innerHTML = ss.map(sessionCard).join('')||'<div class="empty">暂无拼车局</div>';
}

// ---------- 找店找本 ----------
async function renderFind(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">🔍 找本 · 找店 · 找 DM</div></div>
    <div class="pill-row" id="cats"></div>
    <div class="pill-row">
      <span class="pill active" onclick="findTab('script',this)">剧本</span>
      <span class="pill" onclick="findTab('shop',this)">门店</span>
      <span class="pill" onclick="findTab('dm',this)">DM</span>
    </div>
    <div id="find-list" class="wrap loading">加载中…</div>`;
  const cats=['全部','情感','推理','阵营','恐怖','欢乐'];
  document.getElementById('cats').innerHTML=cats.map((c,i)=>
    `<span class="pill ${i===0?'active':''}" onclick="filterCat('${c}',this)">${c}</span>`).join('');
  findTab('script');
}
let findMode='script', findCat='全部';
function filterCat(c,el){findCat=c;el.parentElement.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));el.classList.add('active');loadFind();}
function findTab(m,el){findMode=m;if(el){el.parentElement.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));el.classList.add('active');}loadFind();}
async function loadFind(){
  const box=document.getElementById('find-list'); box.innerHTML='<div class="loading">加载中…</div>';
  if(findMode==='script'){
    const q=findCat==='全部'?'':'?category='+encodeURIComponent(findCat);
    const sc=await API.get('/api/player/scripts'+q);
    box.innerHTML=sc.map(scriptCard).join('')||'<div class="empty">暂无</div>';
  }else if(findMode==='shop'){
    const sh=await API.get('/api/player/shops');
    box.innerHTML=sh.map(s=>`<div class="card" onclick="shopDetail(${s.id})">
      <div class="row"><img class="cover" style="width:70px;height:70px;border-radius:10px;object-fit:cover" src="${s.cover}" onerror="this.style.opacity=.3">
      <div><h3 style="font-size:16px">${esc(s.name)} <span class="rate" style="font-size:13px">★${s.rating}</span></h3>
      <div class="meta">${esc(s.city)} · ${s.room_count}间房</div>
      <p class="muted" style="font-size:12px">${esc(s.intro)}</p></div></div></div>`).join('');
  }else{
    const dms=await API.get('/api/player/dms');
    box.innerHTML=dms.map(d=>`<div class="card">
      <div class="row" style="align-items:center"><div style="width:48px;height:48px;border-radius:50%;background:var(--card2);display:flex;align-items:center;justify-content:center;font-size:22px">🎙️</div>
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
  document.getElementById('role-list').innerHTML=rs.map(r=>`
    <div class="card" onclick="openChat('${esc(r.name)}','${esc(r.script)}')">
      <div class="row" style="align-items:center">
      <div style="width:54px;height:54px;border-radius:14px;background:linear-gradient(135deg,var(--purple),var(--rose));display:flex;align-items:center;justify-content:center;font-size:26px">🎭</div>
      <div style="flex:1"><h3 style="font-size:16px">${esc(r.name)}</h3>
      <div class="meta">${esc(r.script)}</div>
      <p class="muted" style="font-size:12px">${esc(r.tagline)}</p></div>
      <div class="gold" style="font-size:20px">›</div></div></div>`).join('');
}
let chatHistory=[], chatRole='';
function openChat(name,script){
  chatRole=name; chatHistory=[];
  document.querySelector('.tabbar').style.display='none';
  app.innerHTML=`<div class="topbar" style="position:sticky"><h1 style="font-size:16px">🎭 ${esc(name)} <span class="muted" style="font-size:12px;font-weight:400">${esc(script)}</span></h1>
    <span class="badge" onclick="closeChat()" style="cursor:pointer">返回</span></div>
    <div class="chat-list" id="chat" style="padding-bottom:80px">
      <div class="msg ai">（${esc(name)}正静静看着你……说点什么吧）</div></div>
    <div class="chat-input"><input id="chat-in" placeholder="对 ${esc(name)} 说…" onkeydown="if(event.key==='Enter')sendChat()">
      <button class="btn" onclick="sendChat()">发送</button></div>`;
}
function closeChat(){document.querySelector('.tabbar').style.display='flex';go('roles');}
async function sendChat(){
  const inp=document.getElementById('chat-in'); const msg=inp.value.trim(); if(!msg)return;
  const box=document.getElementById('chat');
  box.innerHTML+=`<div class="msg me">${esc(msg)}</div>`;
  inp.value=''; box.scrollTop=box.scrollHeight;
  chatHistory.push({role:'user',content:msg});
  const tip=document.createElement('div'); tip.className='msg ai'; tip.textContent='…'; box.appendChild(tip);
  box.scrollTop=box.scrollHeight;
  const r=await API.post('/api/player/roles/chat',{role_name:chatRole,message:msg,history:chatHistory});
  tip.textContent=r.reply||'（信号中断）';
  chatHistory.push({role:'assistant',content:r.reply||''});
  box.scrollTop=box.scrollHeight;
}

// ---------- 我的 ----------
function renderMine(){
  app.innerHTML=`<div class="wrap"><div class="sec-title">👤 我的</div>
    <div class="card" style="text-align:center;padding:24px">
    <div style="width:64px;height:64px;border-radius:50%;background:var(--card2);margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:30px">🕵️</div>
    <h3>情感玩家Nana</h3><div class="muted" style="font-size:13px">成都 · 情感/沉浸/爱BE</div></div>
    <div class="card"><b>我的局</b><p class="muted" style="font-size:13px;margin-top:6px">· 六月未晚（已满员，明天18:00）<br>· 雾港旧梦（招募中 4/6）</p></div>
    <div class="card"><b>我的测本记录</b><p class="muted" style="font-size:13px;margin-top:6px">感性沉浸型玩家 · 推荐了《雾港旧梦》《六月未晚》</p></div>
    <button class="btn block ghost" onclick="location.href='/'">切换身份</button></div>`;
}

// ---------- 详情（简化弹窗） ----------
async function scriptDetail(id){
  const s=await API.get('/api/player/scripts/'+id);
  alert(`《${s.title}》\n${s.category} · ${s.player_min}-${s.player_max}人 · ${Math.round(s.duration/60)}h\n评分 ★${s.rating}（${(s.reviews||[]).length}条评价）\n\n${s.intro}\n\n${(s.reviews||[]).map(r=>'💬 '+r.content).join('\n')||''}`);
}
async function sessionDetail(id){
  const s=await API.get('/api/player/sessions/'+id);
  const ok=s.status==='recruiting';
  if(confirm(`《${s.script_title}》\n${s.shop_name} · ${s.start_time}\nDM ${s.dm_name} · ¥${s.price}\n进度 ${s.joined_players}/${s.need_players}\n${s.note}\n\n${ok?'点确定上车拼局':'该局已满员'}`)){
    if(ok){const r=await API.post('/api/player/sessions/'+id+'/join',{user_id:5});
      if(r.error)alert(r.error);else{alert('上车成功！当前 '+r.joined_players+'/'+r.need_players);go('plaza');}}
  }
}
async function shopDetail(id){
  const s=await API.get('/api/player/shops/'+id);
  alert(`${s.name}\n${s.address}\n评分 ★${s.rating}\n\n${s.intro}\n\nDM：${(s.dms||[]).map(d=>d.nickname).join('、')}`);
}

// 初始化
initAiBadge(); go('home');
