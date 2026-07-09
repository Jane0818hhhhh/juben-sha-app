"""大模型服务：封装 Azure OpenAI 调用，供测本推荐和角色陪伴使用。

无 Key 或调用失败时优雅降级为规则/模板返回，保证功能不中断（评审可用）。
"""
import json
from ..config import Config

_client = None
_llm_ready = False


def _get_client():
    global _client, _llm_ready
    if _client is not None:
        return _client
    try:
        from openai import AzureOpenAI
        if not Config.OPENAI_API_KEY or not Config.AZURE_OPENAI_ENDPOINT:
            return None
        _client = AzureOpenAI(
            api_key=Config.OPENAI_API_KEY,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_version=Config.AZURE_OPENAI_API_VERSION,
        )
        _llm_ready = True
        return _client
    except Exception as e:
        print("[llm] init failed:", e)
        return None


def llm_status():
    """返回当前 LLM 是否为真实调用模��。"""
    return {"ready": _get_client() is not None, "model": Config.LLM_MODEL}


def chat(messages, temperature=0.8, max_tokens=800, json_mode=False):
    """统一对话入口。返回字符串内容；失败返回 None（由上层降级）。"""
    client = _get_client()
    if client is None:
        return None
    try:
        kwargs = {
            "model": Config.AZURE_OPENAI_DEPLOYMENT,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    except Exception as e:
        print("[llm] chat failed:", e)
        return None


def chat_json(messages, **kwargs):
    """要求返回 JSON 的对话，自动解析。失败返回 None。"""
    raw = chat(messages, json_mode=True, **kwargs)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        # 容错：截取花括号
        try:
            s = raw[raw.index("{"): raw.rindex("}") + 1]
            return json.loads(s)
        except Exception:
            return None
