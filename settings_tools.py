"""
settings_tools.py — 商店設定讀取工具（~14 個）

涵蓋 Webhooks、Curls、Metafields、Locations、Gateways、Customer Custom Attributes。
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from tools.base_tool import api_get, to_json, extract_resource


class PaginationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)

class GetByIdInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    id: str = Field(..., min_length=1)

class ListMetafieldsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    namespace: Optional[str] = Field(None, description="命名空間篩選，例如 sales_channel")
    key: Optional[str] = Field(None, description="Key 篩選")
    value_type: Optional[str] = Field(None, description="String / Integer / Json")
    since_id: Optional[int] = Field(None)

class ListLocationsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    ids: Optional[str] = Field(None)
    since_id: Optional[int] = Field(None)
    sort: Optional[str] = Field(None, description="例如 is_primary.desc")


def register_settings_tools(mcp: FastMCP):

    # ── Webhooks ──────────────────────────────────────────

    @mcp.tool(
        name="easystore_list_webhooks",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_webhooks(params: PaginationInput) -> str:
        """列出所有 Webhook 訂閱設定。

        適合用於：確認事件訂閱狀態、找出重複訂閱、審計已訂閱的 topic。
        常見 topic：product/create, product/update, order/create, customer/create 等。

        Returns:
            str: JSON，webhooks 陣列（含 id、topic、url）。
        """
        data = await api_get("webhooks", {"page": params.page, "limit": params.limit})
        return to_json(data)

    @mcp.tool(
        name="easystore_get_webhook",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_webhook(params: GetByIdInput) -> str:
        """取得單筆 Webhook 設定詳情。"""
        data = await api_get(f"webhooks/{params.id}")
        return to_json(extract_resource(data, "webhook"))

    @mcp.tool(
        name="easystore_count_webhooks",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_count_webhooks() -> str:
        """取得 Webhook 訂閱總數。"""
        data = await api_get("webhooks/count")
        return to_json(data)

    # ── Curls (Logistic Callbacks) ────────────────────────

    @mcp.tool(
        name="easystore_list_curls",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_curls(params: PaginationInput) -> str:
        """列出 Logistic App 的 callback URL 設定（Curls）。

        Curls 是 EasyStore 對物流 App callback endpoint 的命名，非 HTTP curl 工具。
        用於 shipping/list/cod、pickup/verify、external/customer/get 等 topic 的 callback。

        Returns:
            str: JSON，curls 陣列（含 topic、url）。
        """
        data = await api_get("curls", {"page": params.page, "limit": params.limit})
        return to_json(data)

    @mcp.tool(
        name="easystore_get_curl",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_curl(params: GetByIdInput) -> str:
        """取得單筆 Logistic callback URL 設定。"""
        data = await api_get(f"curls/{params.id}")
        return to_json(extract_resource(data, "curl"))

    @mcp.tool(
        name="easystore_count_curls",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_count_curls() -> str:
        """取得 Curl callback 設定總數。"""
        data = await api_get("curls/count")
        return to_json(data)

    # ── Metafields ────────────────────────────────────────

    @mcp.tool(
        name="easystore_list_metafields",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_metafields(params: ListMetafieldsInput) -> str:
        """列出商店層級的 Metafields。

        Metafields 是附加在 Store / Order / Product 上的自訂 key-value 資料。
        可依 namespace 和 key 篩選，例如 namespace=sales_channel 可取得渠道訂單號。

        Args:
            params: 分頁 + 可選 namespace / key / value_type 篩選

        Returns:
            str: JSON，metafields 陣列（含 namespace、key、value、value_type）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("metafields", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_metafield",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_metafield(params: GetByIdInput) -> str:
        """取得單筆 Metafield 詳情。"""
        data = await api_get(f"metafields/{params.id}")
        return to_json(extract_resource(data, "metafield"))

    @mcp.tool(
        name="easystore_count_metafields",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_count_metafields() -> str:
        """取得 Metafield 總數。"""
        data = await api_get("metafields/count")
        return to_json(data)

    # ── Locations ─────────────────────────────────────────

    @mcp.tool(
        name="easystore_list_locations",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_locations(params: ListLocationsInput) -> str:
        """列出門市 / 自取點清單。

        適合用於：確認自取點設定、物流規劃、POS 門市管理。

        Returns:
            str: JSON，locations 陣列（含地址、營業時間、pickup 設定）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("locations", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_location",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_location(params: GetByIdInput) -> str:
        """取得單筆門市 / 自取點詳情（可用 ID 或 code 查詢）。"""
        data = await api_get(f"locations/{params.id}")
        return to_json(extract_resource(data, "location"))

    # ── Gateways ──────────────────────────────────────────

    @mcp.tool(
        name="easystore_list_gateways",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_gateways() -> str:
        """取得商店已啟用的金流方式清單。

        Returns:
            str: JSON，gateways 陣列（含 gateway_type、title、is_hosted_payment）。
        """
        data = await api_get("gateways", {"extras": "sub_gateways"})
        return to_json(data)

    @mcp.tool(
        name="easystore_list_es_gateways",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_es_gateways() -> str:
        """取得 EasyStore 平台支援的全部金流方式（不限商店設定）。

        適合用於：了解可接入的金流選項、比較各金流支援的付款類型。

        Returns:
            str: JSON，全部可用金流的 code / title / payment_type。
        """
        data = await api_get("es_gateways")
        return to_json(data)

    # ── Customer Custom Attributes ─────────────────────────

    @mcp.tool(
        name="easystore_get_customer_attribute",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_customer_attribute(params: GetByIdInput) -> str:
        """取得單筆自訂會員屬性欄位定義（含選項）。"""
        data = await api_get(f"customer_attributes/{params.id}")
        return to_json(data)
