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
from mcp_easystore.tools.base_tool import api_get, api_get_nested, fetch_all_pages, to_json


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

class GetRFMOrdersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    days: Optional[int] = Field(None, ge=1, le=365, description="過去幾天，例如 180（與 date_from/date_to 二選一）")
    date_from: Optional[str] = Field(None, description="開始日期 YYYY-MM-DD")
    date_to: Optional[str] = Field(None, description="結束日期 YYYY-MM-DD")
    page: int = Field(default=1, ge=1, description="頁碼，從 1 開始")
    limit: int = Field(default=100, ge=1, le=250, description="每頁筆數，建議 100–250，預設 100")


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

        ⚠️ 性能考量：
        - EasyStore 無內建聚合 API，需翻頁取得全部訂單後在 client 端加總
        - 推薦查詢範圍：30 天以內（約 5-10 次 API 呼叫）
        - 超過 90 天的查詢可能需要 20+ 次 API 呼叫
        - 例：2026-04 (30天, ~1250筆訂單) 需約 5 次 API 呼叫

        Args:
            params: financial_status（預設 paid）+ 日期範圍

        Returns:
            str: JSON，包含 order_count、total_revenue、currency（取自第一筆訂單）、avg_order_value。
        """
        fs = params.financial_status or "paid"
        query: dict = {
            "financial_status": fs,
            "limit": 250,
            "fields": ""  # 最小化響應大小：不返回擴展字段 (items, addresses, etc.)
        }
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

    @mcp.tool(
        name="easystore_get_rfm_orders",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_rfm_orders(params: GetRFMOrdersInput) -> str:
        """取得 RFM 分析專用的已付款訂單資料（最小化 token 消耗）。

        固定只回傳 RFM 計算所需的五個欄位：
        - id：訂單 ID
        - customer_id：會員 ID（訪客結帳為 null）
        - customer_email：客戶 email
        - total_price：訂單金額
        - created_at：下單時間

        相比 easystore_list_orders 預設回傳，token 消耗減少約 85%。
        固定篩選 financial_status=paid，確保只計算實際付款訂單。

        ⚠️ 建議流程：
        1. 先用 easystore_get_order_summary 確認訂單總數與 page_count
        2. 若 total_count > 2000，建議縮短時間範圍（days=90）
        3. 逐頁取回：page=1, 2, 3... 直到 page >= page_count
        4. 以 customer_id 彙總，計算 R（距今天數）、F（次數）、M（金額）

        Args:
            params: 時間範圍（days 或 date_from/date_to）+ 分頁設定

        Returns:
            str: JSON，包含 total_count、page_count、page、period、orders 陣列。
        """
        min_dt, max_dt = _resolve_dates(params.date_from, params.date_to, params.days)

        query: dict = {
            "financial_status": "paid",
            "fields": "id,customer_id,customer_email,total_price,created_at",
            "page": params.page,
            "limit": params.limit,
        }
        if min_dt:
            query["created_at_min"] = min_dt
        if max_dt:
            query["created_at_max"] = max_dt

        data = await api_get("orders", query)
        if isinstance(data, str):
            return data

        _RFM_FIELDS = {"id", "customer_id", "customer_email", "total_price", "created_at"}
        slim_orders = [
            {k: v for k, v in order.items() if k in _RFM_FIELDS}
            for order in data.get("orders", [])
        ]

        total_count = data.get("total_count", 0)
        page_count = -(-total_count // params.limit) if total_count > 0 else 1  # ceiling division

        return to_json({
            "total_count": total_count,
            "page": params.page,
            "page_count": page_count,
            "period": {"from": min_dt or "all", "to": max_dt or "now"},
            "orders": slim_orders,
        })
