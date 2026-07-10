"""登录与用户体系 API。

MVP 登录：手机号 + 验证码（演示环境固定码 1234，不接短信网关）。
登录成功查/建 User，返回用户信息与简易 token（= user id 的签名串，够 MVP 用）。
未登录用户仍可匿名浏览（前端回退到默认演示用户），不破坏既有流程。
"""
import hashlib
import json
import re
from flask import Blueprint, request, jsonify

from ..models import db, User, GameSession, SessionMember, Script, TestResult, Shop

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# 演示环境固定验证码；生产应接短信网关下发随机码
_DEMO_CODE = "1234"
_PHONE_RE = re.compile(r"^1\d{10}$")


def _token(uid):
    """简易 token：uid + 盐的哈希，够 MVP 校验用（非强安全）。"""
    sig = hashlib.sha256(f"juben-{uid}-salt".encode()).hexdigest()[:16]
    return f"{uid}.{sig}"


def verify_token(token):
    """校验 token，返回 uid 或 None。"""
    try:
        uid, sig = token.split(".", 1)
        if _token(uid) == token:
            return int(uid)
    except Exception:
        pass
    return None


@auth_bp.route("/send-code", methods=["POST"])
def send_code():
    phone = (request.json or {}).get("phone", "").strip()
    if not _PHONE_RE.match(phone):
        return jsonify({"error": "手机号格式不正确"}), 400
    # 演示环境直接返回固定码；生产此处调短信网关
    return jsonify({"success": True, "demo_code": _DEMO_CODE,
                    "message": f"验证码已发送（演示码：{_DEMO_CODE}）"})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()
    if not _PHONE_RE.match(phone):
        return jsonify({"error": "手机号格式不正确"}), 400
    if code != _DEMO_CODE:
        return jsonify({"error": "验证码错误"}), 400

    user = User.query.filter_by(phone=phone).first()
    if not user:
        # 首次登录自动注册
        user = User(nickname=f"玩家{phone[-4:]}", phone=phone, role="player")
        db.session.add(user)
        db.session.commit()
    return jsonify({
        "success": True,
        "token": _token(user.id),
        "user": user.to_dict(),
    })


@auth_bp.route("/me")
def me():
    """按 token/user_id 返回资料 + 我的拼局 + 测本记录（真实查库）。"""
    uid = _resolve_uid()
    if not uid:
        return jsonify({"error": "未登录"}), 401
    user = User.query.get(uid)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    # 我参与的局（作为发起人或成员）
    member_sids = [m.session_id for m in SessionMember.query.filter_by(user_id=uid).all()]
    host_sids = [s.id for s in GameSession.query.filter_by(host_id=uid).all()]
    sids = list(set(member_sids + host_sids))
    my_sessions = []
    for s in GameSession.query.filter(GameSession.id.in_(sids)).all() if sids else []:
        sc = Script.query.get(s.script_id)
        shop = Shop.query.get(s.shop_id)
        my_sessions.append({
            "id": s.id,
            "script_title": sc.title if sc else "",
            "shop_name": shop.name if shop else "",
            "start_time": s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "",
            "status": s.status,
            "is_host": s.id in host_sids,
        })

    # 我的测本记录
    my_tests = []
    for t in TestResult.query.filter_by(user_id=uid).order_by(TestResult.id.desc()).limit(10).all():
        try:
            rec = json.loads(t.recommend) if t.recommend else []
        except Exception:
            rec = []
        my_tests.append({
            "id": t.id,
            "recommend": rec,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
        })

    return jsonify({
        "user": user.to_dict(),
        "my_sessions": my_sessions,
        "my_tests": my_tests,
    })


def _resolve_uid():
    """从 Authorization 头或查询参数解析 uid。"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if token:
        uid = verify_token(token)
        if uid:
            return uid
    # 兼容查询参数
    q = request.args.get("token") or (request.json or {}).get("token") if request.is_json else request.args.get("token")
    if q:
        return verify_token(q)
    return None
