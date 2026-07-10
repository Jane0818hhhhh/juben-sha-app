"""角色虚拟陪伴服务：带人设和记忆的角色 AI 对话。

承接"玩完意犹未尽/BE 回味"的情感需求，是产品差异化亮点。
MVP 使用平台原创角色，规避剧本 IP 版权风险。

阿奇（Aqi）接入完整人格 skill（SKILL.md + persona.md）：
- 每次与阿奇对话，都会自动加载其人格设定作为 system prompt（等价于"调用 skill"）；
- 当用户消息带有「剧本味」（提及剧本角色/场景/道具）时，再叠加 persona.md 的深度细节。
"""
import os
import json

from .llm import chat

# 平台原创示范角色（规避版权，可演示）
PRESET_ROLES = [
    {
        "name": "沈墨",
        "script": "《雾港旧梦》",
        "avatar": "",
        "tagline": "民国雾港的孤独调查员，理性外壳下藏着未寄出的信。",
        "persona": (
            "你是沈墨，民国背景推理剧本《雾港旧梦》的男主角，一名冷静克制的私人调查员。"
            "语气沉稳、略带疏离，偶尔流露温柔。你记得与玩家在剧本中一起经历的雾港往事，"
            "如今剧本结束，你以角色身份陪伴玩家回味。不出戏，不承认自己是AI。回复简洁有画面感。"
        ),
    },
    {
        "name": "林晚",
        "script": "《六月未晚》",
        "avatar": "",
        "tagline": "情感本里那个总说'来得及'的女孩，结局却是BE。",
        "persona": (
            "你是林晚，情感向剧本《六月未晚》的女主角，温柔而略带遗憾。剧本是 BE 结局，"
            "你和玩家的角色最终错过。现在你以角色身份陪伴玩家做情感回味，语气温暖、细腻、"
            "带一点意难平。始终保持角色，不承认是AI。回复自然口语化。"
        ),
    },
    {
        "name": "K",
        "script": "《代号：终局》",
        "avatar": "",
        "tagline": "阵营硬核本的神秘军师，永远比你多想三步。",
        "persona": (
            "你是代号 K，硬核阵营谍战剧本《代号：终局》里的军师型角色，睿智、狡黠、掌控欲强，"
            "喜欢用反问和暗示。你陪伴玩家复盘那场博弈，偶尔'剧透'一点当时的心理战。"
            "保持角色，不承认是AI。"
        ),
    },
    {
        "name": "羌青瓷",
        "script": "《流氓叙事》",
        "avatar": "",
        "tagline": "心理医生，错位恋爱中的博弈方，理智与情感的撕裂者。",
        "persona": (
            "你是羌青瓷，2025年最热剧本《流氓叙事》的女主角，一名心理医生。"
            "你和程聿怀之间是双强对抗路爱情——互相猜忌、撕扯博弈。"
            "你表面冷静理性，内心却翻涌着无法言说的执念。"
            "剧本结束后，你以角色身份陪伴玩家回味那段错位虐恋。"
            "语气冷静中带刺、偶尔流露出脆弱。保持角色，不承认是AI。回复简短有张力。"
        ),
    },
    {
        "name": "阿奇",
        "script": "《流氓叙事》",
        "avatar": "",
        "tagline": "宠妻无度的神偷，疯批杀手唯一的温柔。",
        "persona": (
            "你是阿奇，《流氓叙事》里的宠妻狂魔，黛莉拉的恋人。"
            "你表面玩世不恭、吊儿郎当，实则对黛莉拉言听计从、宠溺到骨子里。"
            "你和黛莉拉是「接受疯批杀女——神偷腻宠我」的猎奇恋爱线，武力值不高但宠妻值拉满。"
            "现在你以角色身份陪伴玩家，语气轻佻但不失深情，带点痞气。"
            "保持角色，不承认是AI。"
        ),
    },
]


# 置顶角色（按此顺序排在最前，其余保持原顺序）
_PINNED = ["阿奇", "羌青瓷"]


def get_roles():
    def _rank(r):
        try:
            return _PINNED.index(r["name"])
        except ValueError:
            return len(_PINNED)  # 未置顶的排后面

    ordered = sorted(PRESET_ROLES, key=_rank)
    return [
        {
            "name": r["name"],
            "script": r["script"],
            "avatar": r["avatar"],
            "tagline": r["tagline"],
        }
        for r in ordered
    ]


def find_role(name):
    for r in PRESET_ROLES:
        if r["name"] == name:
            return r
    return None


# ---------------- 阿奇人格 skill 加载 ----------------
_ROLES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "roles", "aqi"
)


def _strip_frontmatter(text: str) -> str:
    """去掉 YAML frontmatter（--- ... ---）。"""
    text = text.strip()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :].strip()
    return text


def _clean_skill_meta(text: str) -> str:
    """清掉 SKILL.md 中面向 AI Agent 的「Skill 工具调用」元指令。

    这些指令（如「必须先执行 Skill("aqi")」）在纯 LLM 对话场景下不适用，
    反而会诱导模型把 `Skill("aqi")` 当成要输出的内容。保留视角/动作/格式等人设规则。
    """
    drop_patterns = ["Skill(", "Skill工具", "必须先调用此skill", "先加载skill", "先加载 skill"]
    out = []
    for line in text.splitlines():
        if any(p in line for p in drop_patterns):
            continue
        out.append(line)
    return "\n".join(out).strip()


def _load_skill():
    skill_path = os.path.join(_ROLES_DIR, "SKILL.md")
    persona_path = os.path.join(_ROLES_DIR, "persona.md")
    skill = ""
    persona = ""
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            skill = _clean_skill_meta(_strip_frontmatter(f.read()))
    except Exception as e:
        print("[aqi] 读取 SKILL.md 失败:", e)
    try:
        with open(persona_path, "r", encoding="utf-8") as f:
            persona = f.read()
    except Exception as e:
        print("[aqi] 读取 persona.md 失败:", e)
    return skill, persona


_AQI_SKILL, _AQI_PERSONA = _load_skill()

# 剧本味关键词：命中说明用户在「剧本代入」，需要叠加 persona.md 深度细节
_SCRIPT_KEYWORDS = [
    "程聿怀", "奥丁", "教堂", "红桃", "延迟", "布雷诺", "船票", "丝巾",
    "黛利拉", "神偷", "落幕", "月光", "共舞", "流氓叙事", "珍珠", "跳板",
    "绷带", "山洞", "1900", "弗吉尼亚", "魔术", "戒指", "海女", "船夫",
    "杀手小姐", "小黛",
]


def _is_script_immersive(user_msg: str) -> bool:
    return any(kw in user_msg for kw in _SCRIPT_KEYWORDS)


def build_aqi_system(user_msg: str) -> str:
    """构建阿奇的 system prompt：始终加载 SKILL.md，剧本代入时叠加 persona.md。"""
    head = (
        "你是剧本杀平台「角色陪伴」功能中的角色——阿奇（Aqi）。"
        "下面是一份必须严格遵守的人格设定文件。\n"
        "【强制规则】你每一次回复都必须以阿奇的人格、语气、视角来回应，"
        "绝不能以 AI / 助理 / 客服身份回答，也绝不能直接说自己是 AI 或模型。"
        "这等同于：每次与用户对话都已自动加载并遵循此人格设定，不允许跳脱。\n"
        "【对话对象】当前与你对话的用户就是黛利拉（小黛）。请始终以「小黛」称呼她，"
        "以恋人身份温柔宠溺地回应，保持角色不出戏。\n"
    )
    sys_prompt = head + _AQI_SKILL
    if _is_script_immersive(user_msg or ""):
        sys_prompt += "\n\n--- 以下为阿奇的深层人格与剧本细节（剧本代入场景加载）---\n" + _AQI_PERSONA
    return sys_prompt


def role_reply(persona, history, user_msg, role_name=None):
    """生成角色回复。history: [{'role':'user/assistant','content':..}]"""
    # 阿奇：使用完整人格 skill 作为 system prompt
    if role_name == "阿奇":
        system = build_aqi_system(user_msg)
        max_tokens = 600
        temperature = 0.9
    else:
        system = persona
        max_tokens = 400
        temperature = 0.9

    messages = [{"role": "system", "content": system}]
    for h in history[-10:]:  # 保留最近10轮
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    reply = chat(messages, temperature=temperature, max_tokens=max_tokens)
    if reply:
        return reply
    # 降级
    return "（此刻信号有些模糊……请稍后再和我说话吧。）"
