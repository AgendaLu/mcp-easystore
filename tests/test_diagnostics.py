#!/usr/bin/env python3
"""
easystore_diagnose 與錯誤訊息的內容檢查。

兩件事必須成立：
1. 診斷輸出要指出「現在生效的是哪一份設定」，但絕不能出現權杖明文。
2. 錯誤訊息要帶上實際請求的 URL——否則 404 看起來像路徑寫錯，
   實際上是 EASYSTORE_SHOP_URL 指向一個不存在的商店。
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("EASYSTORE_SHOP_URL", "https://test.example.com")
os.environ.setdefault("EASYSTORE_ACCESS_TOKEN", "test_token")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp_easystore.config import settings  # noqa: E402
from mcp_easystore.tools import diagnostics_tools  # noqa: E402
from mcp_easystore.tools.base_tool import handle_api_error  # noqa: E402

SECRET = "s3cret_token_value"


@pytest.fixture
def diagnose(monkeypatch):
    monkeypatch.setattr(settings, "EASYSTORE_SHOP_URL", "https://glamglow.easy.co")
    monkeypatch.setattr(settings, "EASYSTORE_ACCESS_TOKEN", SECRET)

    async def fake_probe():
        return {"url": "https://glamglow.easy.co/api/3.0/store.json", "http_status": 200,
                "ok": True, "store_name": "花石間"}

    monkeypatch.setattr(diagnostics_tools, "_probe_store", fake_probe)

    mcp = FastMCP("test")
    diagnostics_tools.register_diagnostics_tools(mcp)
    fn = mcp._tool_manager.get_tool("easystore_diagnose").fn
    return json.loads(asyncio.run(fn()))


def test_diagnose_reports_effective_shop_url(diagnose):
    assert diagnose["config"]["shop_url"] == "https://glamglow.easy.co"
    assert diagnose["config"]["base_url"] == "https://glamglow.easy.co/api/3.0"
    assert diagnose["store_probe"]["http_status"] == 200
    assert diagnose["store_probe"]["store_name"] == "花石間"


def test_diagnose_never_leaks_the_token(diagnose):
    dumped = json.dumps(diagnose, ensure_ascii=False)
    assert SECRET not in dumped
    assert diagnose["config"]["access_token"].startswith(f"len={len(SECRET)} sha1=")


def test_diagnose_reports_cwd_and_env_files(diagnose):
    env_files = diagnose["config"]["env_files"]
    assert diagnose["config"]["cwd"]
    assert "searched_dirs" in env_files and "loaded" in env_files


STORE_PAYLOAD = {"store": {"name": "花石間", "easystore_domain": "glamglow.easy.co",
                           "plan_name": "Success", "domains": []}}


def test_store_summary_reports_canonical_domain():
    """手動寫設定時要填的就是 easystore_domain（舊版抓 `domain` 永遠是 null）。"""
    out = diagnostics_tools._store_summary(STORE_PAYLOAD, "https://glamglow.easy.co")
    assert out["store_name"] == "花石間"
    assert out["easystore_domain"] == "glamglow.easy.co"
    assert "warning" not in out


def test_store_summary_warns_when_configured_host_differs():
    """打得通但網域對不上（自訂網域、或別家店）時要講出來。"""
    out = diagnostics_tools._store_summary(STORE_PAYLOAD, "https://shop.example.com")
    assert "glamglow.easy.co" in out["warning"]


def _status_error(status: int, url: str) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", url)
    response = httpx.Response(status, request=request, text="{}")
    return httpx.HTTPStatusError("boom", request=request, response=response)


@pytest.mark.parametrize("status", [401, 403, 404, 422, 429, 500])
def test_error_messages_include_the_requested_url(status):
    url = "https://dressup12.easy.co/api/3.0/orders.json"
    msg = handle_api_error(_status_error(status, url), "orders", url)
    assert url in msg, f"HTTP {status} 的錯誤訊息沒有帶上請求 URL：{msg}"


def test_404_names_both_possible_causes():
    url = "https://dressup12.easy.co/api/3.0/orders.json"
    msg = handle_api_error(_status_error(404, url), "orders", url)
    assert "商店不存在" in msg          # 這次事故的實際原因
    assert "路徑" in msg or "ID" in msg  # 另一種可能，不要只講一半
    assert "EASYSTORE_SHOP_URL" in msg


def test_transport_errors_also_include_the_url():
    url = "https://nope.easy.co/api/3.0/store.json"
    msg = handle_api_error(httpx.ConnectError("nope"), "store", url)
    assert url in msg
