"""数据模型：玩家 / 店家 / DM 三端 + 剧本、拼本局、预约、评价、测本、角色陪伴。

用 SQLAlchemy ORM 抽象，开发用 SQLite，上线只需改 DATABASE_URL 切到 MySQL，模型不用动。
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ---------------------------------------------------------------- 用户体系
class User(db.Model):
    """统一用户表，用 role 区分玩家/店家/DM（一个手机号可多角色，MVP先单角色）。"""
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), unique=True)
    avatar = db.Column(db.String(255), default="")
    role = db.Column(db.String(20), default="player")  # player / merchant / dm
    city = db.Column(db.String(30), default="")
    # 玩家画像（测本结果标签，JSON字符串）
    profile_tags = db.Column(db.Text, default="")
    bio = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "nickname": self.nickname, "phone": self.phone,
            "avatar": self.avatar, "role": self.role, "city": self.city,
            "profile_tags": self.profile_tags, "bio": self.bio,
        }


# ---------------------------------------------------------------- 门店
class Shop(db.Model):
    __tablename__ = "shops"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(30), default="")
    address = db.Column(db.String(255), default="")
    cover = db.Column(db.String(255), default="")
    intro = db.Column(db.Text, default="")
    rating = db.Column(db.Float, default=5.0)
    room_count = db.Column(db.Integer, default=3)   # 房间数
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "owner_id": self.owner_id, "name": self.name,
            "city": self.city, "address": self.address, "cover": self.cover,
            "intro": self.intro, "rating": round(self.rating, 1),
            "room_count": self.room_count,
        }


# ---------------------------------------------------------------- 剧本
class Script(db.Model):
    __tablename__ = "scripts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    cover = db.Column(db.String(255), default="")
    category = db.Column(db.String(30), default="")     # 情感/推理/恐怖/欢乐/机制/阵营
    tags = db.Column(db.String(255), default="")        # 逗号分隔标签
    player_min = db.Column(db.Integer, default=6)
    player_max = db.Column(db.Integer, default=6)
    duration = db.Column(db.Integer, default=240)       # 时长(分钟)
    difficulty = db.Column(db.Integer, default=3)       # 1-5
    is_be = db.Column(db.Boolean, default=False)        # 是否BE(悲剧结局)
    has_horror = db.Column(db.Boolean, default=False)   # 是否含恐怖元素
    intro = db.Column(db.Text, default="")
    roles = db.Column(db.Text, default="[]")         # JSON: [{name, gender, brief}] 角色列表
    rating = db.Column(db.Float, default=5.0)
    play_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json as _json
        try:
            _roles = _json.loads(self.roles) if self.roles else []
        except Exception:
            _roles = []
        return {
            "id": self.id, "title": self.title, "cover": self.cover,
            "category": self.category, "tags": self.tags.split(",") if self.tags else [],
            "player_min": self.player_min, "player_max": self.player_max,
            "duration": self.duration, "difficulty": self.difficulty,
            "is_be": self.is_be, "has_horror": self.has_horror,
            "intro": self.intro, "roles": _roles,
            "rating": round(self.rating, 1),
            "play_count": self.play_count,
        }


# ---------------------------------------------------------------- DM 资料
class DMProfile(db.Model):
    __tablename__ = "dm_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True)  # 归属门店(可空=自由DM)
    good_at = db.Column(db.String(255), default="")   # 擅长本类型
    style = db.Column(db.String(255), default="")     # 风格标签
    rating = db.Column(db.Float, default=5.0)
    fans = db.Column(db.Integer, default=0)
    intro = db.Column(db.Text, default="")
    available = db.Column(db.Boolean, default=True)   # 是否接单

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "shop_id": self.shop_id,
            "good_at": self.good_at, "style": self.style,
            "rating": round(self.rating, 1), "fans": self.fans,
            "intro": self.intro, "available": self.available,
        }


# ---------------------------------------------------------------- 拼本局
class GameSession(db.Model):
    """一个"局"：某店某本某时段的拼车。"""
    __tablename__ = "game_sessions"
    id = db.Column(db.Integer, primary_key=True)
    script_id = db.Column(db.Integer, db.ForeignKey("scripts.id"))
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"))
    dm_id = db.Column(db.Integer, db.ForeignKey("dm_profiles.id"), nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # 发起人
    start_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, default=0)
    need_players = db.Column(db.Integer, default=6)   # 需要人数
    joined_players = db.Column(db.Integer, default=1) # 已加入
    status = db.Column(db.String(20), default="recruiting")  # recruiting/full/confirmed/finished/cancelled
    note = db.Column(db.String(255), default="")
    city = db.Column(db.String(30), default="")
    seat_type = db.Column(db.String(30), default="普通位")  # 补贴位/CP位/恋陪/其他陪伴位
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "script_id": self.script_id, "shop_id": self.shop_id,
            "dm_id": self.dm_id, "host_id": self.host_id,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else "",
            "price": self.price, "need_players": self.need_players,
            "joined_players": self.joined_players, "status": self.status,
            "note": self.note, "city": self.city, "seat_type": self.seat_type,
        }


class SessionMember(db.Model):
    """局的成员（上车玩家）。"""
    __tablename__ = "session_members"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("game_sessions.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------- 评价
class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    target_type = db.Column(db.String(20))   # script/shop/dm
    target_id = db.Column(db.Integer)
    rating = db.Column(db.Integer, default=5)
    content = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "target_type": self.target_type,
            "target_id": self.target_id, "rating": self.rating,
            "content": self.content,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }


# ---------------------------------------------------------------- 测本结果
class TestResult(db.Model):
    __tablename__ = "test_results"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    answers = db.Column(db.Text)       # 问卷答案 JSON
    persona = db.Column(db.Text)       # AI生成的画像 JSON
    recommend = db.Column(db.Text)     # 推荐结果 JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------- 角色陪伴
class RoleChat(db.Model):
    """玩家与剧本角色 AI 的对话会话。"""
    __tablename__ = "role_chats"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    script_id = db.Column(db.Integer, db.ForeignKey("scripts.id"), nullable=True)
    role_name = db.Column(db.String(50))
    role_persona = db.Column(db.Text)   # 角色人设
    history = db.Column(db.Text, default="[]")  # 对话历史 JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
