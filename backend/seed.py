"""初始化种子数据：让三端页面一打开就有真实感的示例内容。"""
from datetime import datetime, timedelta
from .models import db, User, Shop, Script, DMProfile, GameSession, SessionMember, Review


def seed_all():
    if User.query.first():
        return  # 已初始化

    # 用户：店家、DM、玩家
    owner = User(nickname="解忧剧本社-店长", phone="13800000001", role="merchant", city="成都")
    dm1 = User(nickname="DM·阿墨", phone="13800000002", role="dm", city="成都")
    dm2 = User(nickname="DM·小唐", phone="13800000003", role="dm", city="成都")
    p1 = User(nickname="推理狂魔", phone="13800000101", role="player", city="成都",
              profile_tags="推理,硬核,老玩家")
    p2 = User(nickname="情感玩家Nana", phone="13800000102", role="player", city="成都",
              profile_tags="情感,沉浸,爱BE")
    db.session.add_all([owner, dm1, dm2, p1, p2])
    db.session.flush()

    # 门店
    shop1 = Shop(owner_id=owner.id, name="解忧剧本社(春熙路店)", city="成都",
                 address="成都市锦江区春熙路8号3F", intro="成都口碑老店，情感/推理双强，DM带本细腻。",
                 rating=4.8, room_count=5,
                 cover="https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600")
    shop2 = Shop(owner_id=owner.id, name="迷雾探案馆(太古里店)", city="成都",
                 address="成都市锦江区中纱帽街太古里", intro="硬核推理与阵营本专精，还原度极高。",
                 rating=4.6, room_count=4,
                 cover="https://images.unsplash.com/photo-1606167668584-78701c57f13d?w=600")
    db.session.add_all([shop1, shop2])
    db.session.flush()

    # DM 资料
    dmp1 = DMProfile(user_id=dm1.id, shop_id=shop1.id, good_at="情感本,还原本",
                     style="细腻,共情,声音好听", rating=4.9, fans=1280,
                     intro="从业3��，情感本催泪担当，带过300+场。")
    dmp2 = DMProfile(user_id=dm2.id, shop_id=shop2.id, good_at="推理本,阵营本",
                     style="逻辑清晰,掌控全场", rating=4.7, fans=860,
                     intro="硬核推理DM，擅长复杂机制本。")
    db.session.add_all([dmp1, dmp2])
    db.session.flush()

    # 剧本
    scripts = [
        Script(title="雾港旧梦", category="情感", tags="民国,推理,微BE", player_min=6, player_max=6,
               duration=300, difficulty=3, is_be=True, has_horror=False, rating=4.9, play_count=3200,
               intro="民国雾港，一桩旧案牵出六��被时代裹挟的人生。",
               cover="https://images.unsplash.com/photo-1476234251651-f353703a034d?w=600"),
        Script(title="六月未晚", category="情感", tags="青春,治愈,BE", player_min=5, player_max=5,
               duration=240, difficulty=2, is_be=True, has_horror=False, rating=4.8, play_count=5100,
               intro="毕业季的错过与重逢，来得及说再见吗？",
               cover="https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=600"),
        Script(title="代号：终局", category="阵营", tags="谍战,硬核,机制", player_min=8, player_max=8,
               duration=360, difficulty=5, is_be=False, has_horror=False, rating=4.7, play_count=2100,
               intro="双阵营谍战博弈，谁是潜伏最深的那枚棋子？",
               cover="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600"),
        Script(title="山鬼夜行", category="恐怖", tags="惊悚,沉浸,还原", player_min=6, player_max=7,
               duration=300, difficulty=4, is_be=False, has_horror=True, rating=4.5, play_count=1800,
               intro="深山古庙一夜，山鬼索命，胆小慎入。",
               cover="https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=600"),
        Script(title="欢乐今宵", category="欢乐", tags="轻松,搞笑,社交", player_min=6, player_max=8,
               duration=180, difficulty=1, is_be=False, has_horror=False, rating=4.4, play_count=6800,
               intro="笑到肚子疼的沉浸式喜剧，萌新友好。",
               cover="https://images.unsplash.com/photo-1543007630-9710e4a00a20?w=600"),
    ]
    db.session.add_all(scripts)
    db.session.flush()

    # 拼本局
    now = datetime.now()
    sessions = [
        GameSession(script_id=scripts[0].id, shop_id=shop1.id, dm_id=dmp1.id, host_id=p2.id,
                    start_time=now + timedelta(days=1, hours=3), price=198, need_players=6,
                    joined_players=4, status="recruiting", note="求两位女玩家，一起哭一场~"),
        GameSession(script_id=scripts[2].id, shop_id=shop2.id, dm_id=dmp2.id, host_id=p1.id,
                    start_time=now + timedelta(days=2, hours=1), price=258, need_players=8,
                    joined_players=6, status="recruiting", note="硬核局，老玩家优先"),
        GameSession(script_id=scripts[1].id, shop_id=shop1.id, dm_id=dmp1.id, host_id=p2.id,
                    start_time=now + timedelta(hours=6), price=168, need_players=5,
                    joined_players=5, status="full", note="已满员，可候补"),
    ]
    db.session.add_all(sessions)
    db.session.flush()

    db.session.add_all([
        SessionMember(session_id=sessions[0].id, user_id=p2.id),
        SessionMember(session_id=sessions[1].id, user_id=p1.id),
    ])

    # 评价
    db.session.add_all([
        Review(user_id=p2.id, target_type="script", target_id=scripts[0].id, rating=5,
               content="情感封神，DM带得太好了，全场哭成一片。"),
        Review(user_id=p1.id, target_type="dm", target_id=dmp2.id, rating=5,
               content="逻辑超清晰，复杂机制讲得明明白白。"),
        Review(user_id=p1.id, target_type="shop", target_id=shop1.id, rating=5,
               content="环境好，服务到位，会再来。"),
    ])

    db.session.commit()
    print("[seed] 初始化完成")
