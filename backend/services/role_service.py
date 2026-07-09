"""角色虚拟陪伴服务：带人设和记忆的角色 AI 对话。

承接"玩完意犹未尽/BE 回味"的情感需求，是产品差异化亮点。
MVP 使用平台原创角色，规避剧本 IP 版权风险。
"""
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
]


def get_roles():
    return [
        {"name": r["name"], "script": r["script"], "avatar": r["avatar"],
         "tagline": r["tagline"]}
        for r in PRESET_ROLES
    ]


def find_role(name):
    for r in PRESET_ROLES:
        if r["name"] == name:
            return r
    return None


def role_reply(persona, history, user_msg):
    """生成角色回复。history: [{'role':'user/assistant','content':..}]"""
    messages = [{"role": "system", "content": persona}]
    for h in history[-10:]:  # 保留最近10轮
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})

    reply = chat(messages, temperature=0.9, max_tokens=400)
    if reply:
        return reply
    # 降级
    return "（此刻信号有些模糊……请稍后再和我说话吧。）"
