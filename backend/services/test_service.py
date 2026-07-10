"""智能测本服务 —— 千岛模式：搜索剧本 → 进入详情 → 测适合角色。

保留原大问卷推本为备用入口，主力改为"先选本再测角色"。
"""
import json
from .llm import chat_json
from .search_service import search_context

# 测角色问卷（比测本更聚焦角色匹配）
ROLE_QUESTIONNAIRE = [
    {"id":"rq1","title":"你更享受哪种游戏方式？","options":[
        {"key":"A","text":"主导剧情推进，喜欢掌控节奏"},
        {"key":"B","text":"沉浸角色内心，享受情感体验"},
        {"key":"C","text":"隐藏身份，在暗处观察与博弈"},
        {"key":"D","text":"辅助团队，默默贡献关键线索"}]},
    {"id":"rq2","title":"在团队中你的位置？","options":[
        {"key":"A","text":"C位/核心人物"},
        {"key":"B","text":"信息枢纽/连接者"},
        {"key":"C","text":"独立行动/游离者"},
        {"key":"D","text":"气氛担当/调节者"}]},
    {"id":"rq3","title":"你最能代入哪种情感线？","options":[
        {"key":"A","text":"双向奔赴的热烈爱情"},
        {"key":"B","text":"爱而不得的虐恋"},
        {"key":"C","text":"友情/亲情的羁绊"},
        {"key":"D","text":"没有感情线，专注搞事业"}]},
    {"id":"rq4","title":"你的演技偏好？","options":[
        {"key":"A","text":"全程在戏里，一秒不出戏"},
        {"key":"B","text":"关键时刻爆发力强"},
        {"key":"C","text":"喜欢暗中带节奏，不动声色"},
        {"key":"D","text":"本色出演就好，轻松为主"}]},
]


def get_role_questionnaire():
    return ROLE_QUESTIONNAIRE


def recommend_role(answers, script_title, roles):
    """根据答案+具体剧本的角色列表，AI 推荐最匹配的角色。

    roles: [{"name":"","gender":"","brief":""}, ...]
    """
    if not roles or len(roles) < 2:
        return {"recommend": roles[0]["name"] if roles else "?", "analysis": "该剧本角色较少，请参考剧本详情选择"}

    sys = (
        "你是剧本杀资深DM和角色分配专家。根据玩家回答的角色匹配问卷，"
        "从指定剧本的角色列表中推荐最适合玩家扮演的角色。"
        "必须返回严格JSON。"
    )
    role_brief = [{"name":r["name"], "gender":r.get("gender","?"), "brief":r.get("brief","")} for r in roles]
    # 联网检索该剧本的真实口碑/角色评价，让推荐更贴合实际（无结果则为空串，不影响）
    web = search_context(f"{script_title} 剧本杀 角色 测评 适合", cnt=4)
    web_block = f"\n{web}\n" if web else ""
    user = (
        f"剧本：《{script_title}》\n"
        f"角色列表：{json.dumps(role_brief, ensure_ascii=False)}\n"
        f"玩家问卷答案：{json.dumps(answers, ensure_ascii=False)}\n"
        f"{web_block}\n"
        "返回 JSON：\n"
        "{\n"
        '  "primary": "最推荐的角色名",\n'
        '  "primary_reason": "推荐理由30字",\n'
        '  "secondary": "次推荐角色名",\n'
        '  "secondary_reason": "次推荐理由30字",\n'
        '  "analysis": "80字以内整体分析",\n'
        '  "play_tip": "30字演绎建议"\n'
        "}\n"
        "primary和secondary必须从角色列表里选真实名称。"
    )
    result = chat_json([
        {"role":"system","content":sys},
        {"role":"user","content":user},
    ], temperature=0.7, max_tokens=600)

    if result and "primary" in result:
        return result

    # 降级
    return {
        "primary": roles[0]["name"],
        "primary_reason": "综合匹配度最高",
        "secondary": roles[-1]["name"] if len(roles)>1 else roles[0]["name"],
        "secondary_reason": "可尝试不同风格",
        "analysis": "当前为规则降级推荐（AI未响应）",
        "play_tip": "按角色卡自由发挥即可",
    }


# ---- 保留旧的大问卷推本（作为辅助入口，非主入口）----
QUESTIONNAIRE = [
    {"id":"q1","title":"组局时你更像哪种人？","options":[
        {"key":"A","text":"话事人，带节奏推进"},{"key":"B","text":"细节控，盯线索找漏洞"},
        {"key":"C","text":"气氛组，负责好玩"},{"key":"D","text":"隐身位，安静沉浸"}]},
    {"id":"q2","title":"你最想要的游戏体验？","options":[
        {"key":"A","text":"烧脑推理，享受解谜"},{"key":"B","text":"情感沉浸，哭一场也值"},
        {"key":"C","text":"阵营厮杀，尔虞我诈"},{"key":"D","text":"轻松欢乐，社交为主"}]},
    {"id":"q3","title":"对恐怖惊吓元素？","options":[
        {"key":"A","text":"热爱，越吓越爽"},{"key":"B","text":"能接受一点"},{"key":"C","text":"拒绝，怕鬼"}]},
    {"id":"q4","title":"能接受BE（悲剧结局）吗？","options":[
        {"key":"A","text":"最爱BE，意难平上头"},{"key":"B","text":"看剧情，好就行"},{"key":"C","text":"只要HE，拒绝虐"}]},
    {"id":"q5","title":"你的剧本杀段位？","options":[
        {"key":"A","text":"萌新，玩过几个"},{"key":"B","text":"进阶，几十个本"},{"key":"C","text":"老玩家，百本以上"}]},
]

def build_persona_and_recommend(answers, scripts):
    """旧版大问卷推本（保留作为辅助入口）。"""
    script_brief = [{"id":s["id"],"title":s["title"],"category":s["category"],
        "tags":s["tags"],"is_be":s["is_be"],"has_horror":s["has_horror"],
        "difficulty":s["difficulty"],"intro":s["intro"][:60]} for s in scripts[:30]]
    sys = ("你是资深剧本杀主持人和玩家画像分析师。根据问卷答案生成画像标签，"
           "从给定剧本库推荐最适合的本和角色定位。必须返回严格JSON。")
    user = (
        f"问卷答案：{json.dumps(answers, ensure_ascii=False)}\n"
        f"剧本库：{json.dumps(script_brief, ensure_ascii=False)}\n\n"
        "返回 JSON：{\"persona_title\":\"人设\",\"tags\":[\"标签\"],"
        "\"analysis\":\"80字分析\","
        "\"recommend_scripts\":[{\"id\":id,\"title\":\"名\",\"reason\":\"理由\"}],"
        "\"suggest_role\":\"角色定位\"}")
    result = chat_json([{"role":"system","content":sys},{"role":"user","content":user}], temperature=0.7, max_tokens=700)
    if result and "persona_title" in result:
        return result
    return _fallback(answers, scripts)

def _fallback(answers, scripts):
    q2 = answers.get("q2","A")
    cat_map = {"A":"推理","B":"情感","C":"阵营","D":"欢乐"}
    prefer = cat_map.get(q2,"推理")
    picks = [s for s in scripts if s["category"]==prefer][:3] or scripts[:3]
    return {
        "persona_title":f"{prefer}偏好型玩家",
        "tags":[prefer,"待AI补充"],
        "analysis":f"根据你的选择，你更偏爱{prefer}类剧本。（规则降级推荐）",
        "recommend_scripts":[{"id":s["id"],"title":s["title"],"reason":f"{s['category']}类高分本"} for s in picks],
        "suggest_role":"根据现场角色分配灵活发挥",
    }
