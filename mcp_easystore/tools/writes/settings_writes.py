"""
settings_writes.py — 系統設定寫入工具（9 個）

涵蓋 Webhook CRUD、Curl（物流 callback）CRUD、Metafield CRUD。
⚠️ 這些操作影響系統整合，修改前請確認影響範圍。
所有工具需 ENABLE_WRITE_TOOLS=true 才會載入。
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from mcp_easystore.tools.base_tool import api_post, api_put, api_delete, to_json


# ── Pydantic Models ───────────────────────────────────────

class CreateWebhookInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    topic: str = Field(
        ...,
        description=(
            "Webhook 事件類型：app/uninstall, store/update, "
            "product/create, product/update, product/delete, "
            "customer/create, customer/update, customer/delete, "
            "order/create, order/update, order/delete, "
            "refund/create, fulfillment/create, fulfillment/update"
        ),
    )
    url: str = Field(..., description="接收 Webhook 的目標 URL", min_length=1)


class UpdateWebhookInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    webhook_id: str = Field(..., description="Webhook ID", min_length=1)
    url: str = Field(..., description="新的目標 URL", min_length=1)


class DeleteWebhookInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    webhook_id: str = Field(..., description="Webhook ID，⚠️ 刪除後系統將停止推送該事件", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


class CreateCurlInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    url: str = Field(..., description="物流 App 的 callback URL", min_length=1)
    curl_type: Optional[str] = Field(None, description="類型：shipping / pickup / external")


class UpdateCurlInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    curl_id: str = Field(..., description="Curl ID", min_length=1)
    url: str = Field(..., description="新的 callback URL", min_length=1)


class DeleteCurlInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    curl_id: str = Field(..., description="Curl ID", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


class CreateMetafieldInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    namespace: str = Field(..., description="命名空間，例如：custom", min_length=1)
    key: str = Field(..., description="欄位鍵名，例如：warranty_period", min_length=1)
    value: str = Field(..., description="欄位值", min_length=1)
    value_type: Optional[str] = Field(None, description="值類型：string / integer / json_string")
    owner_resource: Optional[str] = Field(None, description="所屬資源類型，例如：product / order / customer")
    owner_id: Optional[str] = Field(None, description="所屬資源 ID")


class UpdateMetafieldInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    metafield_id: str = Field(..., description="Metafield ID", min_length=1)
    value: str = Field(..., description="新的欄位值", min_length=1)
    value_type: Optional[str] = Field(None, description="值類型：string / integer / json_string")


class DeleteMetafieldInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    metafield_id: str = Field(..., description="Metafield ID", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


# ── 工具註冊 ──────────────────────────────────────────────

def register_settings_writes(mcp: FastMCP):

    @mcp.tool()
    async def easystore_create_webhook(params: CreateWebhookInput) -> str:
        """建立新的 Webhook 訂閱。系統會在指定事件發生時推送通知到目標 URL。"""
        result = await api_post("webhooks", {"webhook": {"topic": params.topic, "url": params.url}})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_webhook(params: UpdateWebhookInput) -> str:
        """更新 Webhook 的目標 URL。先用 easystore_list_webhooks 查詢現有設定。"""
        result = await api_put(f"webhooks/{params.webhook_id}", {"webhook": {"url": params.url}})
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_webhook(params: DeleteWebhookInput) -> str:
        """⚠️ 刪除 Webhook（不可逆，系統將停止推送該事件）。需傳入 confirm=true 才會執行。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"webhooks/{params.webhook_id}")
        return to_json(result)

    @mcp.tool()
    async def easystore_create_curl(params: CreateCurlInput) -> str:
        """建立物流 App 的 callback URL（Curl）設定。"""
        curl: dict = {"url": params.url}
        if params.curl_type:
            curl["type"] = params.curl_type
        result = await api_post("curls", {"curl": curl})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_curl(params: UpdateCurlInput) -> str:
        """更新物流 callback URL。先用 easystore_list_curls 查詢現有設定。"""
        result = await api_put(f"curls/{params.curl_id}", {"curl": {"url": params.url}})
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_curl(params: DeleteCurlInput) -> str:
        """⚠️ 刪除物流 callback URL（不可逆）。需傳入 confirm=true 才會執行。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"curls/{params.curl_id}")
        return to_json(result)

    @mcp.tool()
    async def easystore_create_metafield(params: CreateMetafieldInput) -> str:
        """建立自訂欄位（Metafield）。可附加到商品、訂單或顧客等資源。"""
        metafield: dict = {
            "namespace": params.namespace,
            "key": params.key,
            "value": params.value,
        }
        if params.value_type:
            metafield["value_type"] = params.value_type
        if params.owner_resource:
            metafield["owner_resource"] = params.owner_resource
        if params.owner_id:
            metafield["owner_id"] = params.owner_id
        result = await api_post("metafields", {"metafield": metafield})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_metafield(params: UpdateMetafieldInput) -> str:
        """更新自訂欄位的值。先用 easystore_list_metafields 查詢現有欄位。"""
        metafield: dict = {"value": params.value}
        if params.value_type:
            metafield["value_type"] = params.value_type
        result = await api_put(f"metafields/{params.metafield_id}", {"metafield": metafield})
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_metafield(params: DeleteMetafieldInput) -> str:
        """⚠️ 刪除自訂欄位（不可逆）。需傳入 confirm=true 才會執行。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"metafields/{params.metafield_id}")
        return to_json(result)
