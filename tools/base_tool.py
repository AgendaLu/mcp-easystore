"""
base_tool.py — 共用 HTTP client

所有 tool 檔案的基礎，統一處理：
- 認證 header
- .json suffix 路徑組裝
- 錯誤處理與友善訊息
- Rate limit 偵測
- 分頁輔助
"""

import json
import httpx
from typing import Any, Optional
from config.settings import get_base_url, get_headers, validate_config


# ── 錯誤處理 ──────────────────────────────────────────────

def handle_api_error(e: Exception, context: str = "") -> str:
    prefix = f"[{context}] " if context else ""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        try:
            body = e.response.json()
            msg = body.get("error", {}).get("message", e.response.text[:200])
        except Exception:
            msg = e.response.text[:200]
        if status == 401:
            return f"{prefix}Error 401: Access Token 無效或缺失，請確認 EASYSTORE_ACCESS_TOKEN。"
        if status == 403:
            return f"{prefix}Error 403: 權限不足，請確認 App 的 scope 包含所需資源。"
        if status == 404:
            return f"{prefix}Error 404: 資源不存在，請確認 ID 或路徑是否正確。"
        if status == 422:
            return f"{prefix}Error 422: 請求參數錯誤 — {msg}"
        if status == 429:
            return f"{prefix}Error 429: API 呼叫頻率超限，請稍後再試。"
        return f"{prefix}Error {status}: {msg}"
    if isinstance(e, httpx.TimeoutException):
        return f"{prefix}Error: 請求超時（30s），請稍後重試。"
    if isinstance(e, httpx.ConnectError):
        return f"{prefix}Error: 無法連線 — 請確認 EASYSTORE_SHOP_URL 是否正確。"
    return f"{prefix}Error: {type(e).__name__} — {str(e)}"


# ── 核心 GET 請求 ─────────────────────────────────────────

async def api_get(path: str, params: Optional[dict] = None) -> dict | list | str:
    """
    執行 GET 請求。path 不含 /api/3.0 前綴，也不需加 .json。
    例：api_get("orders", {"page": 1, "limit": 50})
    """
    config_error = validate_config()
    if config_error:
        return config_error

    # 清理 params：移除 None 和空字串
    clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}

    url = f"{get_base_url()}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=get_headers(), params=clean_params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return handle_api_error(e, path)


async def api_get_nested(path: str, params: Optional[dict] = None) -> dict | str:
    """
    用於 /orders/:id/fulfillments 這類巢狀路徑。
    path 直接傳完整子路徑，例：orders/123/fulfillments
    """
    config_error = validate_config()
    if config_error:
        return config_error

    clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
    url = f"{get_base_url()}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=get_headers(), params=clean_params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return handle_api_error(e, path)


# ── 核心寫入請求 ──────────────────────────────────────────

async def api_post(path: str, data: Optional[dict] = None) -> dict | str:
    """執行 POST 請求。path 不含 /api/3.0 前綴，也不需加 .json。"""
    config_error = validate_config()
    if config_error:
        return config_error
    url = f"{get_base_url()}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=get_headers(), json=data or {})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return handle_api_error(e, path)


async def api_put(path: str, data: Optional[dict] = None) -> dict | str:
    """執行 PUT 請求。path 不含 /api/3.0 前綴，也不需加 .json。"""
    config_error = validate_config()
    if config_error:
        return config_error
    url = f"{get_base_url()}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(url, headers=get_headers(), json=data or {})
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return handle_api_error(e, path)


async def api_delete(path: str) -> dict | str:
    """執行 DELETE 請求。path 不含 /api/3.0 前綴，也不需加 .json。"""
    config_error = validate_config()
    if config_error:
        return config_error
    url = f"{get_base_url()}/{path}.json"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(url, headers=get_headers())
            resp.raise_for_status()
            # DELETE 通常回傳空 body 或 {}
            try:
                return resp.json()
            except Exception:
                return {"status": "deleted"}
    except Exception as e:
        return handle_api_error(e, path)


# ── 分頁輔助 ──────────────────────────────────────────────

async def fetch_all_pages(path: str, resource_key: str, params: Optional[dict] = None, max_pages: int = 10) -> list | str:
    """
    自動翻頁，回傳合併後的 list。
    resource_key：回應 JSON 中的陣列鍵，例如 "orders"。
    max_pages：安全上限，避免無限翻頁。
    """
    base_params = dict(params or {})
    base_params.setdefault("limit", 50)
    all_items = []

    for page in range(1, max_pages + 1):
        base_params["page"] = page
        data = await api_get(path, base_params)
        if isinstance(data, str):  # 錯誤訊息
            return data
        items = data.get(resource_key, [])
        all_items.extend(items)
        total = data.get("total_count", 0)
        if len(all_items) >= total or not items:
            break

    return all_items


# ── 格式化輸出 ────────────────────────────────────────────

def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def extract_resource(data: dict | str, key: str) -> dict | list | str:
    """從 API 回應中取出主要資源，例如 data['order']。"""
    if isinstance(data, str):
        return data
    return data.get(key, data)
