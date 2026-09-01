"""
diagnostics_tools.py — 自我診斷工具（1 個）

回答「現在生效的是哪一份設定」。同一組環境變數可能來自 claude_desktop_config.json、
`claude mcp add` 寫進 ~/.claude.json、.mcp.json、或 repo 裡的 .env——出問題時
使用者沒有任何方式知道 server 實際讀到的是哪一個。這個工具就是那個答案。

輸出一律不含權杖明文，只給指紋（長度 + sha1 前 8 碼）。
"""

import httpx
from mcp.server.fastmcp import FastMCP

from mcp_easystore.config import settings
from mcp_easystore.tools.base_tool import handle_api_error, to_json


def _store_summary(payload: dict, configured_url: str) -> dict:
    """從 /store.json 的回應整理出「這是哪家店」，並比對設定值。

    EasyStore 的權威網域欄位是 `easystore_domain`（例如 glamglow.easy.co）——
    要手動寫 MCP 設定時，EASYSTORE_SHOP_URL 就該填 https://<這個值>。
    自訂網域列在 `domains`，可以打得通但不是這裡的基準。
    """
    store = payload.get("store", payload) if isinstance(payload, dict) else {}
    canonical = store.get("easystore_domain")
    result = {
        "store_name": store.get("name"),
        "easystore_domain": canonical,
        "custom_domains": [d.get("host") or d.get("domain") for d in store.get("domains") or []],
        "plan": store.get("plan_name"),
    }
    configured_host = configured_url.split("://")[-1].strip("/")
    if canonical and configured_host and configured_host != canonical:
        result["warning"] = (
            f"設定的 {configured_host} 打得通，但這家店的 EasyStore 網域是 {canonical}。"
            f"建議把 EASYSTORE_SHOP_URL 改成 https://{canonical}。"
        )
    return result


async def _probe_store() -> dict:
    """實打一次 /store.json，回傳 HTTP 狀態碼與商店名稱。"""
    if settings.validate_config():
        return {"skipped": "設定不完整，未發出請求"}

    url = f"{settings.get_base_url()}/store.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=settings.get_headers())
        result = {"url": url, "http_status": resp.status_code}
        if resp.status_code == 200:
            try:
                payload = resp.json()
            except Exception:
                payload = {}
            result.update(_store_summary(payload, settings.EASYSTORE_SHOP_URL))
            result["ok"] = True
        else:
            result["ok"] = False
            result["hint"] = handle_api_error(
                httpx.HTTPStatusError("", request=resp.request, response=resp), "store", url
            )
        return result
    except Exception as e:
        return {"url": url, "ok": False, "error": handle_api_error(e, "store", url)}


def register_diagnostics_tools(mcp: FastMCP):

    @mcp.tool(
        name="easystore_diagnose",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_diagnose() -> str:
        """診斷 MCP server 目前生效的設定，並實打一次 API 驗證連線。

        查不到資料、工具全部回 404 或 401 時的第一站。回傳：
        - 生效的 EASYSTORE_SHOP_URL 與完整 base URL
        - 每個環境變數的來源（client 注入 / 哪一個 .env 檔）
        - 權杖指紋（長度 + sha1 前 8 碼，不含明文）
        - ENABLE_WRITE_TOOLS 狀態與已載入的工具數量
        - 工作目錄、實際讀到的 .env 檔案
        - GET /store.json 的 HTTP 狀態碼與商店名稱

        Returns:
            str: JSON 格式的診斷報告（不含任何憑證明文）。
        """
        config = settings.describe_config()
        all_tools = mcp._tool_manager.list_tools()
        write_tools = [t for t in all_tools if not (t.annotations and t.annotations.readOnlyHint)]

        return to_json({
            "config": config,
            "tools": {
                "total": len(all_tools),
                "write_tools_loaded": len(write_tools),
                "enable_write_tools": settings.ENABLE_WRITE_TOOLS,
            },
            "store_probe": await _probe_store(),
        })
