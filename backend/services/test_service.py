"""智能测本服务：问卷 → 玩家画像 → 推荐本/角色。

亮点：测完直接关联"能约的本"，不是纯娱乐测试。
"""
import json
from .llm import chat_json

# 测本问卷（前端渲染用）
QUESTIONNAIRE = [
    {"id": "q1", "title": "组局时你更像哪种人？", "options": [
        {"key": "A", "text": "话事人，带节奏推进"},
        {"key": "B", "text": "细节控，盯线索找漏洞"},
        {"key": "C", "text": "气氛组，负责好玩"},
        {"key": "D", "text": "隐身位，安静沉浸"}]},
    {"id": "q2", "title": "你最想要的游戏体验？", "options": [
        {"key": "A", "text": "烧脑推理，享受解谜"},
        {"key": "B", "text": "情感沉浸，哭一场也值"},
        {"key": "C", "text": "阵营厮杀，尔虞我诈"},
        {"key": "D", "text": "轻松欢乐，社交为主"}]},
    {"id": "q3", "title": "对恐怖惊吓元素？", "options": [
        {"key": "A", "text": "热爱，越吓越爽"},
        {"key": "B", "text": "能接受一点"},
        {"key": "C", "text": "拒绝，怕鬼"}]},
    {"id": "q4", "title": "能接受 BE（悲剧结局）吗？", "options": [
        {"key": "A", "text": "最爱BE，意难平上头"},
        {"key": "B", "text": "看剧情，好就行"},
        {"key": "C", "text": "只要HE，拒绝虐"}]},
    {"id": "q5", "title": "你的剧本杀段位？", "options": [
        {"key": "A", "text": "萌新，玩过几个"},
        {"key": "B", "text": "进阶，几十个本"},
        {"key": "C", "text": "老玩家，百本以上"}]},
]


def build_persona_and_recommend(answers, scripts):
    """输入答案 + 可选剧本库，输出画像标签 + 推荐。

    scripts: [Script.to_dict(), ...]  用于让 AI 从真实库里挑本。
    """
    script_brief = [
        {"id": s["id"], "title": s["title"], "category": s["category"],
         "tags": s["tags"], "is_be": s["is_be"], "has_horror": s["has_horror"],
         "difficulty": s["difficulty"], "intro": s["intro"][:60]}
        for s in scripts[:30]
    ]
    sys = (
        "你是资深剧本杀主持人和玩家画像分析师。根据用户问卷答案，"
        "生成玩家画像标签，并从给定剧本库中推荐最适合的本和角色定位。"
        "必须返回严格 JSON。"
    )
    user = (
        f"问卷答案：{json.dumps(answers, ensure_ascii=False)}\n"
        f"剧本库：{json.dumps(script_brief, ensure_ascii=False)}\n\n"
        "返回 JSON，结构：\n"
        "{\n"
        '  "persona_title": "一句话玩家人设，如：沉浸型情感玩家",\n'
        '  "tags": ["标签1","标签2","标签3","标签4"],\n'
        '  "analysis": "80字以内的性格与偏好分析",\n'
        '  "recommend_scripts": [{"id":剧本id,"title":"名","reason":"推荐理由30字"}],\n'
        '  "suggest_role": "适合的角色定位，如：擅长隐藏身份的阵营核心"\n'
        "}\n"
        "recommend_scripts 从剧本库里挑 2-3 个最匹配的（用真实 id）。"
    )
    result = chat_json([
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ], temperature=0.7, max_tokens=700)

    if result and "persona_title" in result:
        return result

    # 降级：规则推荐
    return _fallback(answers, scripts)


def _fallback(answers, scripts):
    q2 = answers.get("q2", "A")
    cat_map = {"A": "推理", "B": "情感", "C": "阵营", "D": "欢乐"}
    prefer = cat_map.get(q2, "推理")
    picks = [s for s in scripts if s["category"] == prefer][:3] or scripts[:3]
    return {
        "persona_title": f"{prefer}偏好型玩家",
        "tags": [prefer, "待AI补充"],
        "analysis": f"根据你的选择，你更偏爱{prefer}类剧本。（当前为规则推荐，接入AI后更精准）",
        "recommend_scripts": [
            {"id": s["id"], "title": s["title"], "reason": f"{s['category']}类高分本"}
            for s in picks
        ],
        "suggest_role": "根据现场角色分配灵活发挥",
    }
