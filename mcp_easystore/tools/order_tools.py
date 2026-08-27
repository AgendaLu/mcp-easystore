"""
order_tools.py — 訂單讀取工具（~10 個）

涵蓋訂單列表、單筆讀取、出貨紀錄、交易紀錄、結帳流程。
所有工具均為唯讀，不修改任何資料。
"""

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from mcp_easystore.tools.base_tool import api_get, api_get_nested, fetch_all_pages, to_json, extract_resource


# ── Pydantic Models ───────────────────────────────────────

class ListOrdersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    status: Optional[str] = Field(None, description="open / cancelled / archived / deleted")
    financial_status: Optional[str] = Field(None, description="paid / pending / unpaid / refunded / voided / cod")
    fulfillment_status: Optional[str] = Field(None, description="fulfilled / partially_fulfilled / unfulfilled")
    created_at_min: Optional[str] = Field(None, description="格式：YYYY-MM-DD HH:MM:SS")
    created_at_max: Optional[str] = Field(None, description="格式：YYYY-MM-DD HH:MM:SS")
    updated_at_min: Optional[str] = Field(None)
    updated_at_max: Optional[str] = Field(None)
    processed_at_min: Optional[str] = Field(None)
    processed_at_max: Optional[str] = Field(None)
    customer_id: Optional[int] = Field(None, description="依會員 ID 篩選")
    sort: Optional[str] = Field(None, description="排序，例如 processed_at.desc")
    source_type: Optional[str] = Field(None, description="pos / web 等")
    fields: Optional[str] = Field(None, description="額外欄位：items,addresses,transactions,fulfillments,refunds,taxes,customer,shipping_fees,metafields,discounts,points")

class GetOrderInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    fields: Optional[str] = Field(None, description="額外欄位：items,addresses,transactions,fulfillments,refunds,taxes,customer,shipping_fees,metafields,discounts,points,fulfillment_orders,cancellation,referral")

class ListFulfillmentsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID")
    status: Optional[str] = Field(None, description="open / cancelled / delivered / in_transit")
    tracking_number: Optional[str] = Field(None)
    is_cancelled: Optional[bool] = Field(None)
    sort: Optional[str] = Field(None)

class GetFulfillmentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID")
    fulfillment_id: str = Field(..., description="出貨紀錄 ID")

class ListTransactionsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID")

class GetTransactionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID")
    transaction_id: str = Field(..., description="交易 ID")

class ListCheckoutsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=50)
    since_id: Optional[int] = Field(None)
    created_at_min: Optional[str] = Field(None)
    created_at_max: Optional[str] = Field(None)

class GetCheckoutInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    cart_token: str = Field(..., description="Cart token UUID")


# ── Tools ─────────────────────────────────────────────────

def register_order_tools(mcp: FastMCP):

    @mcp.tool(
        name="easystore_list_orders",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_orders(params: ListOrdersInput) -> str:
        """列出 EasyStore 訂單，支援多條件篩選與分頁。

        可依付款狀態、出貨狀態、訂單狀態、時間區間、會員 ID 等條件篩選。
        適合用於：日常訂單管理、特定條件的訂單查詢、資料分析的原始資料提取。

        📊 性能提示：
        - 默認響應：～36,000 tokens (10 條訂單含完整字段)
        - 優化響應 (fields='id,total_price,currency_code')：～5,000 tokens (86% 節省 🚀)
        - 不指定 fields 時返回所有可用字段（items, customer, addresses 等）

        💡 推薦用法：
        - 營收分析、報表生成：fields='id,total_price,currency_code'
        - 訂單列表展示：fields='-customer' (68% 節省) 或不指定 fields
        - 完整訂單詳情：不指定 fields 或使用 easystore_get_order

        重要限制：EasyStore 無 search endpoint，所有搜尋透過此工具的 query params 實現。
        若要取得特定訂單詳情請使用 easystore_get_order。

        Args:
            params: 篩選條件（狀態、時間、會員等）+ 分頁設定
                   fields 參數可指定返回的字段，優化 API 響應大小

        Returns:
            str: JSON，包含 total_count、page_count、orders 陣列。
        """
        query = params.model_dump(exclude_none=True, exclude={"fields"})
        if params.fields:
            query["fields"] = params.fields
        data = await api_get("orders", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_order",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_order(params: GetOrderInput) -> str:
        """取得單筆訂單完整資料。

        預設回傳訂單基本資訊。透過 fields 參數可選擇性載入：
        商品明細(items)、地址(addresses)、付款交易(transactions)、
        出貨(fulfillments)、退款(refunds)、稅金(taxes)、
        客戶資料(customer)、運費(shipping_fees)、點數(points)。

        Args:
            params: order_id + 可選 fields

        Returns:
            str: JSON 格式的訂單完整資料。
        """
        query = {}
        if params.fields:
            query["fields"] = params.fields
        data = await api_get(f"orders/{params.order_id}", query or None)
        return to_json(extract_resource(data, "order"))

    @mcp.tool(
        name="easystore_list_fulfillments",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_fulfillments(params: ListFulfillmentsInput) -> str:
        """取得訂單的出貨紀錄列表。

        一筆訂單可能有多筆出貨紀錄（部分出貨場景）。
        包含物流公司、追蹤號碼、出貨狀態等資訊。
        適合用於：出貨追蹤、物流狀態監控、物流異常分析。

        Args:
            params: order_id + 可選篩選（status / tracking_number / is_cancelled）

        Returns:
            str: JSON，fulfillments 陣列。
        """
        query = {k: v for k, v in params.model_dump(exclude={"order_id"}).items() if v is not None}
        data = await api_get_nested(f"orders/{params.order_id}/fulfillments", query or None)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_fulfillment",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_fulfillment(params: GetFulfillmentInput) -> str:
        """取得單筆出貨紀錄詳情。

        Args:
            params: order_id + fulfillment_id

        Returns:
            str: JSON 格式的出貨紀錄。
        """
        data = await api_get_nested(f"orders/{params.order_id}/fulfillments/{params.fulfillment_id}")
        return to_json(extract_resource(data, "fulfillment"))

    @mcp.tool(
        name="easystore_list_transactions",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_transactions(params: ListTransactionsInput) -> str:
        """取得訂單的付款交易紀錄。

        包含金流類型（gateway）、金額、幣別、交易狀態。
        適合用於：對帳、付款異常排查、退款流程追蹤。

        Args:
            params: order_id

        Returns:
            str: JSON，transactions 陣列。
        """
        data = await api_get_nested(f"orders/{params.order_id}/transactions")
        return to_json(data)

    @mcp.tool(
        name="easystore_get_transaction",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_transaction(params: GetTransactionInput) -> str:
        """取得單筆付款交易詳情。

        Args:
            params: order_id + transaction_id

        Returns:
            str: JSON 格式的交易記錄。
        """
        data = await api_get_nested(f"orders/{params.order_id}/transactions/{params.transaction_id}")
        return to_json(extract_resource(data, "transaction"))

    @mcp.tool(
        name="easystore_list_checkouts",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_checkouts(params: ListCheckoutsInput) -> str:
        """列出結帳流程（購物車）紀錄。

        結帳（checkout）是訂單建立前的狀態，包含未完成的購物車。
        適合用於：棄單率分析、購物車放棄原因初步探查。

        Args:
            params: 分頁設定 + 可選時間篩選

        Returns:
            str: JSON，checkouts 陣列（含 financial_status、line_items）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("checkouts", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_checkout",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_checkout(params: GetCheckoutInput) -> str:
        """取得單筆結帳詳情。

        Args:
            params: cart_token（UUID 格式）

        Returns:
            str: JSON 格式的結帳資料。
        """
        data = await api_get(f"checkouts/{params.cart_token}")
        return to_json(extract_resource(data, "checkout"))
