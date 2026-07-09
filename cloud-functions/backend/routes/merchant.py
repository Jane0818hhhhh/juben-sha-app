"""店家端 API：排期管理、剧本库、DM 派单、订单概览、数据看板。"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from ..models import (db, User, Shop, Script, DMProfile, GameSession, SessionMember)

merchant_bp = Blueprint("merchant", __name__, url_prefix="/api/merchant")


@merchant_bp.route("/shops/<int:owner_id>")
def my_shops(owner_id):
    items = Shop.query.filter_by(owner_id=owner_id).all()
    return jsonify([s.to_dict() for s in items])


# ---------------- 排期管理 ----------------
@merchant_bp.route("/shops/<int:shop_id>/schedule")
def shop_schedule(shop_id):
    """门店所有场次（排期看板）。"""
    items = GameSession.query.filter_by(shop_id=shop_id).order_by(GameSession.start_time).all()
    out = []
    for s in items:
        d = s.to_dict()
        script = Script.query.get(s.script_id)
        dm = DMProfile.query.get(s.dm_id) if s.dm_id else None
        d["script_title"] = script.title if script else ""
        d["dm_name"] = (User.query.get(dm.user_id).nickname if dm else "未派单")
        out.append(d)
    return jsonify(out)


@merchant_bp.route("/schedule", methods=["POST"])
def create_schedule():
    """店家开一个场次（可供玩家上车）。"""
    data = request.json or {}
    try:
        start = datetime.strptime(data["start_time"], "%Y-%m-%d %H:%M")
    except Exception:
        return jsonify({"error": "时间格式错误，应为 YYYY-MM-DD HH:MM"}), 400
    s = GameSession(
        script_id=data["script_id"], shop_id=data["shop_id"],
        dm_id=data.get("dm_id"), host_id=data.get("host_id", 1),
        start_time=start, price=data.get("price", 0),
        need_players=data.get("need_players", 6), joined_players=0,
        status="recruiting", note=data.get("note", "店家开场"),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict())


@merchant_bp.route("/schedule/<int:sid>/status", methods=["POST"])
def update_status(sid):
    s = GameSession.query.get_or_404(sid)
    s.status = (request.json or {}).get("status", s.status)
    db.session.commit()
    return jsonify(s.to_dict())


@merchant_bp.route("/schedule/<int:sid>/assign_dm", methods=["POST"])
def assign_dm(sid):
    s = GameSession.query.get_or_404(sid)
    s.dm_id = (request.json or {}).get("dm_id")
    db.session.commit()
    return jsonify(s.to_dict())


# ---------------- 剧本库 ----------------
@merchant_bp.route("/scripts", methods=["POST"])
def add_script():
    data = request.json or {}
    s = Script(
        title=data["title"], category=data.get("category", ""),
        tags=",".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else data.get("tags", ""),
        player_min=data.get("player_min", 6), player_max=data.get("player_max", 6),
        duration=data.get("duration", 240), difficulty=data.get("difficulty", 3),
        is_be=data.get("is_be", False), has_horror=data.get("has_horror", False),
        intro=data.get("intro", ""), cover=data.get("cover", ""),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict())


# ---------------- DM 花名册 ----------------
@merchant_bp.route("/shops/<int:shop_id>/dms")
def shop_dms(shop_id):
    items = DMProfile.query.filter_by(shop_id=shop_id).all()
    out = []
    for x in items:
        d = x.to_dict()
        u = User.query.get(x.user_id)
        d["nickname"] = u.nickname if u else "DM"
        out.append(d)
    return jsonify(out)


# ---------------- 数据看板 ----------------
@merchant_bp.route("/shops/<int:shop_id>/dashboard")
def dashboard(shop_id):
    sessions = GameSession.query.filter_by(shop_id=shop_id).all()
    total = len(sessions)
    confirmed = len([s for s in sessions if s.status in ("full", "confirmed", "finished")])
    total_players = sum(s.joined_players for s in sessions)
    revenue = sum(s.price * s.joined_players for s in sessions if s.status in ("full", "confirmed", "finished"))
    # 热门本
    from collections import Counter
    c = Counter(s.script_id for s in sessions)
    hot = []
    for sid, cnt in c.most_common(3):
        sc = Script.query.get(sid)
        if sc:
            hot.append({"title": sc.title, "count": cnt})
    return jsonify({
        "total_sessions": total,
        "confirmed_sessions": confirmed,
        "total_players": total_players,
        "revenue": round(revenue, 0),
        "fill_rate": round(confirmed / total * 100, 0) if total else 0,
        "hot_scripts": hot,
    })
