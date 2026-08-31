#!/usr/bin/env python3
"""
摘要型工具在 API 失敗時必須「回報錯誤」，不得回傳看起來正確的 0。

背景：api_get 失敗時回傳的是錯誤「字串」而不是 dict。analytics_tools 裡
`data.get("total_count", 0) if isinstance(data, dict) else 0` 會把每一次失敗
記成 0，於是商店網址填錯、權杖過期、429 限流全都變成一份「本月 0 筆訂單」
的報表，而使用者會相信它。這組測試把那條路釘死。
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("EASYSTORE_SHOP_URL", "https://test.example.com")
os.environ.setdefault("EASYSTORE_ACCESS_TOKEN", "test_token")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp_easystore.tools import analytics_tools  # noqa: E402

API_ERROR = "[orders] Error 404: 商店不存在或已停用（或路徑／ID 錯誤）。請求 URL：https://test.example.com/api/3.0/orders.json"


@pytest.fixture
def tools():
    mcp = FastMCP("test")
    analytics_tools.register_analytics_tools(mcp)
    return {t.name: t.fn for t in mcp._tool_manager.list_tools()}


@pytest.fixture
def failing_api(monkeypatch):
    """讓所有 api_get 呼叫回傳錯誤字串（模擬 404 / 401 / 429）。"""
    calls = []

    async def fake_api_get(path, params=None):
        calls.append((path, params))
        return API_ERROR

    monkeypatch.setattr(analytics_tools, "api_get", fake_api_get)
    return calls


def _call(fn, params_cls=None, **kwargs):
    if params_cls is None:
        return asyncio.run(fn())
    return asyncio.run(fn(params_cls(**kwargs)))


@pytest.mark.parametrize("tool_name,params_cls,kwargs", [
    ("easystore_get_order_summary", analytics_tools.DateRangeInput, {"days": 30}),
    ("easystore_get_financial_status_summary", analytics_tools.DateRangeInput, {"days": 365}),
    ("easystore_get_fulfillment_status_summary", analytics_tools.DateRangeInput, {"days": 30}),
    ("easystore_get_product_inventory_summary", None, {}),
    ("easystore_get_collection_product_count", analytics_tools.CollectionStatsInput, {"collection_id": 1}),
    ("easystore_get_store_info", None, {}),
])
def test_api_failure_surfaces_as_error(tools, failing_api, tool_name, params_cls, kwargs):
    out = _call(tools[tool_name], params_cls, **kwargs)

    assert "Error 404" in out, f"{tool_name} 吞掉了 API 錯誤，回傳：{out}"
    # 不得出現「一切正常、只是沒資料」那種假答案
    assert '"total_orders": 0' not in out
    assert '"total_count": 0' not in out
    assert '"product_count": 0' not in out
    assert '"total_products": 0' not in out


def test_order_summary_stops_at_first_failure(tools, failing_api):
    """失敗即中止，不要把剩下的狀態一路打完再回報。"""
    _call(tools["easystore_get_order_summary"], analytics_tools.DateRangeInput, days=30)
    assert len(failing_api) == 1, f"應在第一次失敗就中止，實際呼叫 {len(failing_api)} 次"
