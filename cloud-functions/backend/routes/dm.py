"""DM 端 API：个人主页、可接单场次、接单、切换接单状态。"""
from flask import Blueprint, request, jsonify
from ..models import (db, User, Shop, Script, DMProfile, GameSession)

dm_bp = Blueprint("dm", __name__, url_prefix="/api/dm")


@dm_bp.route("/profile/<int:user_id>")
def profile(user_id):
    dm = DMProfile.query.filter_by(user_id=user_id).first()
    if not dm:
        return jsonify({"error": "未找到DM资料"}), 404
    d = dm.to_dict()
    u = User.query.get(user_id)
    d["nickname"] = u.nickname if u else "DM"
    shop = Shop.query.get(dm.shop_id) if dm.shop_id else None
    d["shop_name"] = shop.name if shop else "自由DM"
    return jsonify(d)


@dm_bp.route("/profile/<int:user_id>/available", methods=["POST"])
def toggle_available(user_id):
    dm = DMProfile.query.filter_by(user_id=user_id).first_or_404()
    dm.available = (request.json or {}).get("available", not dm.available)
    db.session.commit()
    return jsonify({"available": dm.available})


@dm_bp.route("/orders/<int:user_id>")
def my_orders(user_id):
    """我带的场次。"""
    dm = DMProfile.query.filter_by(user_id=user_id).first()
    if not dm:
        return jsonify([])
    items = GameSession.query.filter_by(dm_id=dm.id).order_by(GameSession.start_time).all()
    out = []
    for s in items:
        d = s.to_dict()
        sc = Script.query.get(s.script_id)
        shop = Shop.query.get(s.shop_id)
        d["script_title"] = sc.title if sc else ""
        d["shop_name"] = shop.name if shop else ""
        out.append(d)
    return jsonify(out)


@dm_bp.route("/market")
def market():
    """待接单市场：没有指派DM的招募中场次。"""
    items = GameSession.query.filter_by(dm_id=None, status="recruiting").all()
    out = []
    for s in items:
        d = s.to_dict()
        sc = Script.query.get(s.script_id)
        shop = Shop.query.get(s.shop_id)
        d["script_title"] = sc.title if sc else ""
        d["script_category"] = sc.category if sc else ""
        d["shop_name"] = shop.name if shop else ""
        out.append(d)
    return jsonify(out)


@dm_bp.route("/market/<int:sid>/take", methods=["POST"])
def take_order(sid):
    s = GameSession.query.get_or_404(sid)
    data = request.json or {}
    dm = DMProfile.query.filter_by(user_id=data.get("user_id")).first()
    if not dm:
        return jsonify({"error": "请先完善DM资料"}), 400
    if s.dm_id:
        return jsonify({"error": "该场次已被接单"}), 400
    s.dm_id = dm.id
    db.session.commit()
    return jsonify(s.to_dict())
