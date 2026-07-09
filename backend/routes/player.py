"""玩家端 API：测本、拼本广场、找店找本、DM列表、评价、角色陪伴。"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from ..models import (db, User, Shop, Script, DMProfile, GameSession,
                      SessionMember, Review, TestResult, RoleChat)
from ..services import test_service, role_service

player_bp = Blueprint("player", __name__, url_prefix="/api/player")


# ---------------- 剧本库 ----------------
@player_bp.route("/scripts")
def list_scripts():
    q = Script.query
    cat = request.args.get("category")
    kw = request.args.get("kw")
    if cat and cat != "全部":
        q = q.filter_by(category=cat)
    if kw:
        q = q.filter(Script.title.like(f"%{kw}%"))
    items = q.order_by(Script.rating.desc()).all()
    return jsonify([s.to_dict() for s in items])


@player_bp.route("/scripts/<int:sid>")
def script_detail(sid):
    s = Script.query.get_or_404(sid)
    reviews = Review.query.filter_by(target_type="script", target_id=sid).all()
    d = s.to_dict()
    d["reviews"] = [r.to_dict() for r in reviews]
    return jsonify(d)


# ---------------- 门店 ----------------
@player_bp.route("/shops")
def list_shops():
    items = Shop.query.order_by(Shop.rating.desc()).all()
    return jsonify([s.to_dict() for s in items])


@player_bp.route("/shops/<int:sid>")
def shop_detail(sid):
    s = Shop.query.get_or_404(sid)
    dms = DMProfile.query.filter_by(shop_id=sid).all()
    reviews = Review.query.filter_by(target_type="shop", target_id=sid).all()
    d = s.to_dict()
    d["dms"] = [_dm_full(x) for x in dms]
    d["reviews"] = [r.to_dict() for r in reviews]
    return jsonify(d)


# ---------------- DM ----------------
def _dm_full(dm):
    d = dm.to_dict()
    u = User.query.get(dm.user_id)
    d["nickname"] = u.nickname if u else "DM"
    d["avatar"] = u.avatar if u else ""
    shop = Shop.query.get(dm.shop_id) if dm.shop_id else None
    d["shop_name"] = shop.name if shop else "自由DM"
    return d


@player_bp.route("/dms")
def list_dms():
    items = DMProfile.query.order_by(DMProfile.rating.desc()).all()
    return jsonify([_dm_full(x) for x in items])


# ---------------- 拼本局广场 ----------------
def _session_full(s):
    d = s.to_dict()
    script = Script.query.get(s.script_id)
    shop = Shop.query.get(s.shop_id)
    dm = DMProfile.query.get(s.dm_id) if s.dm_id else None
    d["script_title"] = script.title if script else ""
    d["script_cover"] = script.cover if script else ""
    d["script_category"] = script.category if script else ""
    d["shop_name"] = shop.name if shop else ""
    d["dm_name"] = (User.query.get(dm.user_id).nickname if dm else "待定")
    # 已加入成员画像
    members = SessionMember.query.filter_by(session_id=s.id).all()
    d["members"] = []
    for m in members:
        u = User.query.get(m.user_id)
        if u:
            d["members"].append({"nickname": u.nickname, "tags": u.profile_tags})
    return d


@player_bp.route("/sessions")
def list_sessions():
    status = request.args.get("status")
    q = GameSession.query
    if status:
        q = q.filter_by(status=status)
    items = q.order_by(GameSession.start_time).all()
    return jsonify([_session_full(s) for s in items])


@player_bp.route("/sessions/<int:sid>")
def session_detail(sid):
    s = GameSession.query.get_or_404(sid)
    return jsonify(_session_full(s))


@player_bp.route("/sessions", methods=["POST"])
def create_session():
    data = request.json or {}
    try:
        start = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M")
    except Exception:
        return jsonify({"error": "开局时间格式错误"}), 400
    s = GameSession(
        script_id=data.get("script_id"), shop_id=data.get("shop_id"),
        dm_id=data.get("dm_id"), host_id=data.get("host_id", 4),
        start_time=start, price=data.get("price", 0),
        need_players=data.get("need_players", 6), joined_players=1,
        status="recruiting", note=data.get("note", ""),
    )
    db.session.add(s)
    db.session.flush()
    db.session.add(SessionMember(session_id=s.id, user_id=s.host_id))
    db.session.commit()
    return jsonify(_session_full(s))


@player_bp.route("/sessions/<int:sid>/join", methods=["POST"])
def join_session(sid):
    s = GameSession.query.get_or_404(sid)
    data = request.json or {}
    uid = data.get("user_id", 5)
    if s.status != "recruiting":
        return jsonify({"error": "该局已不可加入"}), 400
    if SessionMember.query.filter_by(session_id=sid, user_id=uid).first():
        return jsonify({"error": "你已在局中"}), 400
    db.session.add(SessionMember(session_id=sid, user_id=uid))
    s.joined_players += 1
    if s.joined_players >= s.need_players:
        s.status = "full"
    db.session.commit()
    return jsonify(_session_full(s))


# ---------------- 智能测本 ----------------
@player_bp.route("/test/questionnaire")
def questionnaire():
    return jsonify(test_service.QUESTIONNAIRE)


@player_bp.route("/test/submit", methods=["POST"])
def test_submit():
    data = request.json or {}
    answers = data.get("answers", {})
    scripts = [s.to_dict() for s in Script.query.all()]
    result = test_service.build_persona_and_recommend(answers, scripts)
    # 附上推荐本的封面
    for rec in result.get("recommend_scripts", []):
        sc = Script.query.get(rec.get("id"))
        if sc:
            rec["cover"] = sc.cover
            rec["rating"] = round(sc.rating, 1)
    tr = TestResult(user_id=data.get("user_id"),
                    answers=json.dumps(answers, ensure_ascii=False),
                    persona=json.dumps(result, ensure_ascii=False),
                    recommend=json.dumps(result.get("recommend_scripts", []), ensure_ascii=False))
    db.session.add(tr)
    db.session.commit()
    return jsonify(result)


# ---- 千岛模式：搜索某剧本 → 测适合角色 ----
@player_bp.route("/scripts/<int:sid>/role-quiz")
def role_quiz(sid):
    """返回该剧本的角色列表 + 测角色问卷。"""
    s = Script.query.get_or_404(sid)
    import json as _json
    try:
        roles = _json.loads(s.roles) if s.roles else []
    except Exception:
        roles = []
    return jsonify({
        "script_title": s.title,
        "script_id": s.id,
        "roles": roles,
        "questions": test_service.get_role_questionnaire(),
    })


@player_bp.route("/scripts/<int:sid>/test-role", methods=["POST"])
def test_role(sid):
    """提交角色匹配问卷，AI 返回最适合的角色。"""
    s = Script.query.get_or_404(sid)
    data = request.json or {}
    answers = data.get("answers", {})
    import json as _json
    try:
        roles = _json.loads(s.roles) if s.roles else []
    except Exception:
        roles = []
    result = test_service.recommend_role(answers, s.title, roles)
    tr = TestResult(user_id=data.get("user_id"),
                    answers=_json.dumps(answers, ensure_ascii=False),
                    persona=_json.dumps(result, ensure_ascii=False),
                    recommend=_json.dumps({"script_title": s.title, **result}, ensure_ascii=False))
    db.session.add(tr)
    db.session.commit()
    return jsonify({"script_title": s.title, **result})


# ---------------- 评价 ----------------
@player_bp.route("/reviews", methods=["POST"])
def add_review():
    data = request.json or {}
    r = Review(user_id=data.get("user_id", 4), target_type=data["target_type"],
               target_id=data["target_id"], rating=data.get("rating", 5),
               content=data.get("content", ""))
    db.session.add(r)
    # 更新目标平均分
    db.session.flush()
    _recalc_rating(data["target_type"], data["target_id"])
    db.session.commit()
    return jsonify(r.to_dict())


def _recalc_rating(ttype, tid):
    rows = Review.query.filter_by(target_type=ttype, target_id=tid).all()
    if not rows:
        return
    avg = sum(x.rating for x in rows) / len(rows)
    model = {"script": Script, "shop": Shop, "dm": DMProfile}.get(ttype)
    if model:
        obj = model.query.get(tid)
        if obj:
            obj.rating = avg


# ---------------- 角色陪伴 ----------------
@player_bp.route("/roles")
def roles():
    return jsonify(role_service.get_roles())


@player_bp.route("/roles/chat", methods=["POST"])
def role_chat():
    data = request.json or {}
    name = data.get("role_name")
    msg = data.get("message", "")
    history = data.get("history", [])
    role = role_service.find_role(name)
    if not role:
        return jsonify({"error": "角色不存在"}), 404
    reply = role_service.role_reply(role["persona"], history, msg)
    return jsonify({"reply": reply, "role_name": name})
