"""
order_writes.py — 訂單寫入工具（6 個）

涵蓋取消訂單、退款、更新訂單、建立/更新/取消出貨紀錄。
所有工具需 ENABLE_WRITE_TOOLS=true 才會載入。
"""

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from mcp_easystore.tools.base_tool import api_post, api_put, to_json


# ── Pydantic Models ───────────────────────────────────────

class CancelOrderInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    reason: Optional[str] = Field(None, description="取消原因，例如：customer / inventory / fraud / other")


class RefundOrderInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    amount: float = Field(..., description="退款金額", gt=0)
    type: Optional[str] = Field(None, description="退款方式，例如：original / credit / manual")
    note: Optional[str] = Field(None, description="退款備注")
    reference_number: Optional[str] = Field(None, description="外部參考號碼")
    transaction_id: Optional[str] = Field(None, description="關聯交易 ID")


class UpdateOrderInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    remark: Optional[str] = Field(None, description="訂單備注（商家內部用）")
    note: Optional[str] = Field(None, description="訂單附言")


class CreateFulfillmentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    tracking_company: Optional[str] = Field(None, description="物流商名稱，例如：黑貓宅急便")
    tracking_number: Optional[str] = Field(None, description="追蹤號碼")
    tracking_url: Optional[str] = Field(None, description="物流追蹤網址")
    status: Optional[str] = Field(None, description="狀態：open / in_transit / delivered / cancelled")
    message: Optional[str] = Field(None, description="出貨備注")
    is_mail: Optional[bool] = Field(None, description="是否寄送通知信")


class UpdateFulfillmentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    fulfillment_id: str = Field(..., description="出貨紀錄 ID", min_length=1)
    tracking_number: Optional[str] = Field(None, description="更新後的追蹤號碼")
    tracking_url: Optional[str] = Field(None, description="更新後的物流追蹤網址")
    status: Optional[str] = Field(None, description="狀態：open / in_transit / delivered")
    message: Optional[str] = Field(None, description="備注")


class CancelFulfillmentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    order_id: str = Field(..., description="訂單 ID", min_length=1)
    fulfillment_id: str = Field(..., description="出貨紀錄 ID，⚠️ 取消後無法復原", min_length=1)


# ── 工具註冊 ──────────────────────────────────────────────

def register_order_writes(mcp: FastMCP):

    @mcp.tool()
    async def easystore_cancel_order(params: CancelOrderInput) -> str:
        """取消訂單。⚠️ 不可逆操作。建議先用 easystore_get_order 確認訂單狀態再執行。"""
        body = {}
        if params.reason:
            body["reason"] = params.reason
        result = await api_post(f"orders/{params.order_id}/cancel", body)
        return to_json(result)

    @mcp.tool()
    async def easystore_refund_order(params: RefundOrderInput) -> str:
        """退款。需指定退款金額。可搭配 easystore_get_order（fields=transactions）先查詢付款金額。"""
        body: dict = {"amount": params.amount}
        if params.type:
            body["type"] = params.type
        if params.note:
            body["note"] = params.note
        if params.reference_number:
            body["reference_number"] = params.reference_number
        if params.transaction_id:
            body["transaction_id"] = params.transaction_id
        result = await api_post(f"orders/{params.order_id}/refund", body)
        return to_json(result)

    @mcp.tool()
    async def easystore_update_order(params: UpdateOrderInput) -> str:
        """更新訂單備注或附言。"""
        order: dict = {}
        if params.remark is not None:
            order["remark"] = params.remark
        if params.note is not None:
            order["note"] = params.note
        result = await api_put(f"orders/{params.order_id}", {"order": order})
        return to_json(result)

    @mcp.tool()
    async def easystore_create_fulfillment(params: CreateFulfillmentInput) -> str:
        """建立出貨紀錄，標記訂單已出貨並填入追蹤資訊。"""
        body: dict = {}
        if params.tracking_company:
            body["tracking_company"] = params.tracking_company
        if params.tracking_number:
            body["tracking_number"] = params.tracking_number
        if params.tracking_url:
            body["tracking_url"] = params.tracking_url
        if params.status:
            body["status"] = params.status
        if params.message:
            body["message"] = params.message
        if params.is_mail is not None:
            body["is_mail"] = params.is_mail
        result = await api_post(f"orders/{params.order_id}/fulfillments", body)
        return to_json(result)

    @mcp.tool()
    async def easystore_update_fulfillment(params: UpdateFulfillmentInput) -> str:
        """更新出貨紀錄的追蹤號碼、狀態或備注。"""
        body: dict = {}
        if params.tracking_number:
            body["tracking_number"] = params.tracking_number
        if params.tracking_url:
            body["tracking_url"] = params.tracking_url
        if params.status:
            body["status"] = params.status
        if params.message:
            body["message"] = params.message
        result = await api_put(
            f"orders/{params.order_id}/fulfillments/{params.fulfillment_id}", body
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_cancel_fulfillment(params: CancelFulfillmentInput) -> str:
        """取消出貨紀錄。⚠️ 不可逆操作，請確認後再執行。"""
        result = await api_post(
            f"orders/{params.order_id}/fulfillments/{params.fulfillment_id}/cancel", {}
        )
        return to_json(result)
