"""联网搜索服务 —— 腾讯云 WSA SearchPro（实时联网检索）。

用纯 requests + TC3-HMAC-SHA256 手写签名，避免额外引入腾讯云 SDK 依赖
（云函数构建器打包更稳）。无 Key 或调用失败时优雅降级返回空列表，
不影响任何现有流程。
"""
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone

import requests

from ..config import Config

_HOST = "wsa.tencentcloudapi.com"
_SERVICE = "wsa"
_ACTION = "SearchPro"
_VERSION = "2025-05-08"
_REGION = ""  # 该接口无需 region


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _build_headers(secret_id, secret_key, payload):
    """构造 TC3-HMAC-SHA256 鉴权头。"""
    ts = int(time.time())
    date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

    # 1) 规范请求串
    http_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = (
        f"content-type:{ct}\n"
        f"host:{_HOST}\n"
        f"x-tc-action:{_ACTION.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (
        f"{http_method}\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{hashed_payload}"
    )

    # 2) 待签名字符串
    algorithm = "TC3-HMAC-SHA256"
    credential_scope = f"{date}/{_SERVICE}/tc3_request"
    hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (
        f"{algorithm}\n{ts}\n{credential_scope}\n{hashed_canonical}"
    )

    # 3) 计算签名
    secret_date = _sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _sign(secret_date, _SERVICE)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # 4) 授权头
    authorization = (
        f"{algorithm} Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return {
        "Authorization": authorization,
        "Content-Type": ct,
        "Host": _HOST,
        "X-TC-Action": _ACTION,
        "X-TC-Version": _VERSION,
        "X-TC-Timestamp": str(ts),
    }


def search_available():
    return bool(Config.TENCENT_SEARCH_SID and Config.TENCENT_SEARCH_SKEY)


def web_search(query, cnt=5, timeout=8):
    """联网搜索，返回 [{title,url,site,date,passage,score}] 列表。

    无 Key 或失败时返回 []（上层据此决定是否降级为纯模型知识）。
    """
    if not search_available() or not query:
        return []
    payload = json.dumps({"Query": query}, ensure_ascii=False)
    try:
        headers = _build_headers(
            Config.TENCENT_SEARCH_SID, Config.TENCENT_SEARCH_SKEY, payload
        )
        resp = requests.post(
            f"https://{_HOST}", headers=headers,
            data=payload.encode("utf-8"), timeout=timeout,
        )
        data = resp.json().get("Response", {})
        if "Error" in data:
            print("[search] api error:", data["Error"])
            return []
        out = []
        for p in data.get("Pages", [])[:cnt]:
            try:
                d = json.loads(p)
            except Exception:
                continue
            out.append({
                "title": d.get("title", ""),
                "url": d.get("url", ""),
                "site": d.get("site", ""),
                "date": d.get("date", ""),
                "passage": d.get("passage", ""),
                "score": d.get("score", 0),
            })
        return out
    except Exception as e:
        print("[search] failed:", e)
        return []


def search_context(query, cnt=5):
    """把搜索结果拼成可喂给大模型的上下文文本；无结果返回空串。"""
    results = web_search(query, cnt=cnt)
    if not results:
        return ""
    lines = ["【联网检索到的实时资料，供参考】"]
    for i, r in enumerate(results, 1):
        seg = f"{i}. {r['title']}"
        if r.get("site"):
            seg += f"（来源：{r['site']}）"
        if r.get("passage"):
            seg += f"：{r['passage'][:120]}"
        lines.append(seg)
    return "\n".join(lines)
