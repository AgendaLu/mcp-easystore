"""
analytics_tools.py — 數據分析讀取工具（~12 個）

跨資源的摘要型查詢，是分析場景的高頻入口。
包含商店基本資訊、訂單統計、營收、庫存、客戶成長。
"""

import json
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from tools.base_tool import api_get, api_get_nested, fetch_all_pages, to_json


# ── Pydantic Models ───────────────────────────────────────

class DateRangeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    date_from: Optional[str] = Field(None, description="開始日期，格式 YYYY-MM-DD，例如 2025-01-01")
    date_to: Optional[str] = Field(None, description="結束日期，格式 YYYY-MM-DD，例如 2025-01-31")
    days: Optional[int] = Field(None, ge=1, le=365, description="最近 N 天（與 date_from/date_to 二選一）")

class FinancialStatusInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    financial_status: Optional[str] = Field(None, description="付款狀態：paid / pending / unpaid / refunded / voided / cod")
    date_from: Optional[str] = Field(None, description="開始日期 YYYY-MM-DD")
    date_to: Optional[str] = Field(None, description="結束日期 YYYY-MM-DD")

class CustomerGrowthInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    date_from: Optional[str] = Field(None, description="開始日期 YYYY-MM-DD")
    date_to: Optional[str] = Field(None, description="結束日期 YYYY-MM-DD")
    limit: int = Field(default=50, ge=1, le=250, description="回傳筆數")

class CollectionStatsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    collection_id: Optional[int] = Field(None, description="指定分類 ID（不填則查全部）")


def _resolve_dates(date_from: Optional[str], date_to: Optional[str], days: Optional[int]) -> tuple[str, str]:
    """解析日期參數，回傳 (created_at_min, created_at_max)。"""
    if days:
        end = datetime.now()
        start = end - timedelta(days=days)
        return start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59")
    return (date_from or ""), (date_to or "")


# ── Tools ─────────────────────────────────────────────────

def register_analytics_tools(mcp: FastMCP):

    @mcp.tool(
        name="easystore_get_store_info",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_store_info() -> str:
        """取得 EasyStore 商店基本資訊。

        回傳商店名稱、網域、主要幣別、時區、國家、方案等設定。
        適合用於：確認商店環境、快速確認幣別和時區、作為其他分析的前置資訊。

        Returns:
            str: JSON 格式的商店設定資料。
        """
        data = await api_get("store")
        return to_json(data.get("store", data) if isinstance(data, dict) else data)

    @mcp.tool(
        name="easystore_get_order_summary",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_order_summary(params: DateRangeInput) -> str:
        """取得指定時間區間的訂單量統計摘要。

        依訂單狀態（open / cancelled / archived）和付款狀態分組統計，
        適合用於：快速掌握期間訂單概況、每日/每週例行檢查、異常偵測前的基線建立。

        Args:
            params: 日期範圍（date_from + date_to，或 days=7 表示最近7天）

        Returns:
            str: JSON，包含 total_count、依狀態分組的計數、查詢期間。
        """
        min_dt, max_dt = _resolve_dates(params.date_from, params.date_to, params.days)
        query = {"limit": 1}
        if min_dt:
            query["created_at_min"] = min_dt
        if max_dt:
            query["created_at_max"] = max_dt

        # 抓各狀態
        results = {}
        for status in ["open", "cancelled", "archived"]:
            q = {**query, "status": status}
            data = await api_get("orders", q)
            results[status] = data.get("total_count", 0) if isinstance(data, dict) else 0

        total = sum(results.values())
        return to_json({
            "period": {"from": min_dt or "all", "to": max_dt or "now"},
            "total_orders": total,
            "by_status": results,
        })

    @mcp.tool(
        name="easystore_get_revenue_summary",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_revenue_summary(params: FinancialStatusInput) -> str:
        """取得指定時間區間的營收統計（付款訂單加總）。

        只計算已付款（financial_status=paid）的訂單，逐筆加總 total_price。
        適合用於：週報/月報、營收趨勢分析、對帳參考。

        注意：EasyStore 無內建聚合 API，此工具會自動翻頁取得全部訂單後在 client 端加總。
        訂單量大時（>500筆）建議縮短日期範圍以加快回應。

        Args:
            params: financial_status（預設 paid）+ 日期範圍

        Returns:
            str: JSON，包含 order_count、total_revenue、currency（取自第一筆訂單）、avg_order_value。
        """
        fs = params.financial_status or "paid"
        query: dict = {"financial_status": fs, "limit": 250}
        if params.date_from:
            query["created_at_min"] = params.date_from
        if params.date_to:
            query["created_at_max"] = params.date_to

        orders = await fetch_all_pages("orders", "orders", query, max_pages=20)
        if isinstance(orders, str):
            return orders

        total = sum(float(o.get("total_price", 0)) for o in orders)
        currency = orders[0].get("currency_code", "N/A") if orders else "N/A"
        avg = total / len(orders) if orders else 0

        return to_json({
            "period": {"from": params.date_from or "all", "to": params.date_to or "now"},
            "financial_status": fs,
            "order_count": len(orders),
            "total_revenue": round(total, 2),
            "avg_order_value": round(avg, 2),
            "currency": currency,
        })

    @mcp.tool(
        name="easystore_get_fulfillment_status_summary",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_fulfillment_status_summary(params: DateRangeInput) -> str:
        """取得訂單出貨狀態分佈（已出貨 / 部分出貨 / 未出貨）。

        適合用於：出貨進度監控、找出積壓未出貨的訂單批次、物流效率分析。

        Args:
            params: 日期範圍

        Returns:
            str: JSON，包含各 fulfillment_status 的訂單數量分佈。
        """
        min_dt, max_dt = _resolve_dates(params.date_from, params.date_to, params.days)
        query: dict = {"limit": 1, "status": "open"}
        if min_dt:
            query["created_at_min"] = min_dt
        if max_dt:
            query["created_at_max"] = max_dt

        results = {}
        for fs in ["fulfilled", "partially_fulfilled", "unfulfilled"]:
            q = {**query, "fulfillment_status": fs}
            data = await api_get("orders", q)
            results[fs] = data.get("total_count", 0) if isinstance(data, dict) else 0

        return to_json({
            "period": {"from": min_dt or "all", "to": max_dt or "now"},
            "fulfillment_status_distribution": results,
            "total_open_orders": sum(results.values()),
        })

    @mcp.tool(
        name="easystore_get_financial_status_summary",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_financial_status_summary(params: DateRangeInput) -> str:
        """取得訂單付款狀態分佈（已付款 / 待付款 / 未付款 / 退款等）。

        適合用於：催款追蹤、財務對帳前的快速盤點、異常付款狀態偵測。

        Args:
            params: 日期範圍

        Returns:
            str: JSON，各付款狀態的訂單數量分佈。
        """
        min_dt, max_dt = _resolve_dates(params.date_from, params.date_to, params.days)
        query: dict = {"limit": 1}
        if min_dt:
            query["created_at_min"] = min_dt
        if max_dt:
            query["created_at_max"] = max_dt

        results = {}
        for fs in ["paid", "pending", "unpaid", "refunded", "voided", "cod"]:
            q = {**query, "financial_status": fs}
            data = await api_get("orders", q)
            results[fs] = data.get("total_count", 0) if isinstance(data, dict) else 0

        return to_json({
            "period": {"from": min_dt or "all", "to": max_dt or "now"},
            "financial_status_distribution": results,
        })

    @mcp.tool(
        name="easystore_get_customer_growth",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_customer_growth(params: CustomerGrowthInput) -> str:
        """取得新會員成長統計。

        回傳期間內新增的會員數量，可作為行銷活動效果的初步判斷指標。

        Args:
            params: 日期範圍 + limit

        Returns:
            str: JSON，包含 new_customer_count 和查詢期間。
        """
        query: dict = {"limit": 1}
        if params.date_from:
            query["created_at_min"] = params.date_from
        if params.date_to:
            query["created_at_max"] = params.date_to

        data = await api_get("customers", query)
        if isinstance(data, str):
            return data

        return to_json({
            "period": {"from": params.date_from or "all", "to": params.date_to or "now"},
            "new_customer_count": data.get("total_count", 0),
        })

    @mcp.tool(
        name="easystore_get_product_inventory_summary",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_product_inventory_summary() -> str:
        """取得商品庫存概況（上架商品總數、庫存統計）。

        適合用於：庫存健康檢查、找出無庫存商品、上架狀態確認。

        Returns:
            str: JSON，包含 published_count、unpublished_count、total_inventory_quantity（上架商品加總）。
        """
        pub_data = await api_get("products", {"visibility": "published", "limit": 1})
        unpub_data = await api_get("products", {"visibility": "unpublished", "limit": 1})

        if isinstance(pub_data, str):
            return pub_data

        pub_count = pub_data.get("total_count", 0) if isinstance(pub_data, dict) else 0
        unpub_count = unpub_data.get("total_count", 0) if isinstance(unpub_data, dict) else 0

        return to_json({
            "published_products": pub_count,
            "unpublished_products": unpub_count,
            "total_products": pub_count + unpub_count,
            "note": "inventory_quantity 加總需使用 easystore_list_products 並設定 limit=250 逐頁累計",
        })

    @mcp.tool(
        name="easystore_get_collection_product_count",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_collection_product_count(params: CollectionStatsInput) -> str:
        """取得各分類的商品數量分佈。

        透過 Collects API 統計每個分類有多少商品，適合用於：
        分類內容健康檢查、找出空分類、商品分類分佈分析。

        Args:
            params: 可選 collection_id（指定單一分類），不填則查全部分類。

        Returns:
            str: JSON，包含各分類的 name 和 product_count。
        """
        if params.collection_id:
            data = await api_get("collects", {"collection_id": params.collection_id, "limit": 1})
            if isinstance(data, str):
                return data
            return to_json({
                "collection_id": params.collection_id,
                "product_count": data.get("total_count", 0),
            })

        # 取所有分類
        collections = await fetch_all_pages("collections", "collections", {"limit": 50})
        if isinstance(collections, str):
            return collections

        results = []
        for col in collections:
            count_data = await api_get("collects", {"collection_id": col["id"], "limit": 1})
            results.append({
                "collection_id": col["id"],
                "collection_name": col.get("name"),
                "product_count": count_data.get("total_count", 0) if isinstance(count_data, dict) else 0,
            })

        results.sort(key=lambda x: x["product_count"], reverse=True)
        return to_json({"collections": results, "total_collections": len(results)})

    @mcp.tool(
        name="easystore_get_gateway_usage",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_gateway_usage() -> str:
        """取得商店已啟用的金流方式清單。

        適合用於：確認支援哪些付款方式、金流設定審計、與訂單 financial_status 交叉分析。

        Returns:
            str: JSON，包含已啟用的金流列表（type、title、是否代管付款）。
        """
        data = await api_get("gateways", {"extras": "sub_gateways"})
        if isinstance(data, str):
            return data

        gateways = data.get("gateways", [])
        summary = [
            {
                "type": g.get("gateway_type"),
                "title": g.get("custom_title") or g.get("title"),
                "is_enabled": g.get("is_enabled"),
                "is_hosted_payment": g.get("is_hosted_payment"),
            }
            for g in gateways
        ]
        return to_json({"gateways": summary, "total": len(summary)})

    @mcp.tool(
        name="easystore_get_webhook_health",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_webhook_health() -> str:
        """取得 Webhook 設定清單，用於健康檢查。

        適合用於：確認事件訂閱是否正常設定、找出重複訂閱、審計已訂閱的 topic。

        Returns:
            str: JSON，包含所有 webhook 的 topic / url，以及總數。
        """
        data = await api_get("webhooks", {"limit": 50})
        if isinstance(data, str):
            return data

        webhooks = data.get("webhooks", [])
        return to_json({
            "total": data.get("total_count", len(webhooks)),
            "webhooks": [
                {"id": w.get("id"), "topic": w.get("topic"), "url": w.get("url")}
                for w in webhooks
            ],
        })
