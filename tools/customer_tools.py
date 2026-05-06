"""
customer_tools.py — 客戶讀取工具（~10 個）
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from tools.base_tool import api_get, api_get_nested, to_json, extract_resource


class ListCustomersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    ids: Optional[str] = Field(None, description="逗號分隔的會員 ID")
    since_id: Optional[int] = Field(None)
    sort: Optional[str] = Field(None, description="例如 id.desc")
    query: Optional[str] = Field(None, description="依姓名或 email 關鍵字篩選")
    created_at_min: Optional[str] = Field(None)
    created_at_max: Optional[str] = Field(None)
    updated_at_min: Optional[str] = Field(None)
    updated_at_max: Optional[str] = Field(None)
    fields: Optional[str] = Field(None, description="額外欄位：total_point")

class SearchCustomersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    email: Optional[str] = Field(None, description="精確 email 查詢")
    phone: Optional[str] = Field(None, description="手機號碼（含國碼，例如：60191234567）")
    code: Optional[str] = Field(None, description="會員代碼")
    fields: Optional[str] = Field(None)

class GetCustomerInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., min_length=1)
    fields: Optional[str] = Field(None, description="額外欄位：points, membership")

class GetCustomerPointsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., min_length=1)

class ListAddressesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)

class GetAddressInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., min_length=1)
    address_id: str = Field(..., min_length=1)

class GetGroupInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    group_id: str = Field(..., min_length=1)

class ListCustomerAttributesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)


def register_customer_tools(mcp: FastMCP):

    @mcp.tool(
        name="easystore_list_customers",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_customers(params: ListCustomersInput) -> str:
        """列出會員清單，支援多條件篩選。

        可依關鍵字、時間區間、ID 等篩選。
        適合用於：會員資料盤點、分析期間新增會員、匯出目標族群。

        Args:
            params: 篩選條件 + 分頁

        Returns:
            str: JSON，total_count + customers 陣列。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("customers", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_search_customers",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_search_customers(params: SearchCustomersInput) -> str:
        """依 email、手機或會員代碼精確查詢會員。

        與 easystore_list_customers 的差別：此工具用於精確查找特定會員，
        支援 email / phone / code 三種精確查詢條件。

        Args:
            params: email 或 phone 或 code（至少填一個）

        Returns:
            str: JSON，符合條件的 customers 陣列。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("customers/search", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_customer",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_customer(params: GetCustomerInput) -> str:
        """取得單筆會員詳細資料。

        透過 fields 可選擇性載入積分（points）或會員等級（membership）。

        Args:
            params: customer_id + 可選 fields

        Returns:
            str: JSON 格式的會員資料。
        """
        query = {}
        if params.fields:
            query["fields"] = params.fields
        data = await api_get(f"customers/{params.customer_id}", query or None)
        return to_json(extract_resource(data, "customer"))

    @mcp.tool(
        name="easystore_get_customer_points",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_customer_points(params: GetCustomerPointsInput) -> str:
        """取得會員的點數餘額與點數設定（兌換率、有效期等）。

        適合用於：點數餘額查詢、點數規則確認、兌換資格判斷。

        Args:
            params: customer_id

        Returns:
            str: JSON，包含 total_point 和 point_settings（earning/redemption 規則）。
        """
        # 注意：此 endpoint 在 Postman collection 中路徑為 /3.0/customers/:id/points.json
        # 疑似缺少 /api 前綴，實作時使用標準路徑，若出現 404 需確認
        data = await api_get_nested(f"customers/{params.customer_id}/points")
        return to_json(data)

    @mcp.tool(
        name="easystore_list_customer_addresses",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_customer_addresses(params: ListAddressesInput) -> str:
        """取得會員的地址列表。

        Args:
            params: customer_id + 分頁

        Returns:
            str: JSON，addresses 陣列（含主要地址標記 is_primary）。
        """
        query = {"page": params.page, "limit": params.limit}
        data = await api_get_nested(f"customers/{params.customer_id}/addresses", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_customer_address",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_customer_address(params: GetAddressInput) -> str:
        """取得會員的單筆地址詳情。

        Args:
            params: customer_id + address_id

        Returns:
            str: JSON 格式的地址資料。
        """
        data = await api_get_nested(f"customers/{params.customer_id}/addresses/{params.address_id}")
        return to_json(extract_resource(data, "address"))

    @mcp.tool(
        name="easystore_list_groups",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_groups() -> str:
        """列出所有會員群組。

        適合用於：了解現有群組結構、分析各群組規模。

        Returns:
            str: JSON，groups 陣列（含 id、name）。
        """
        data = await api_get("groups")
        return to_json(data)

    @mcp.tool(
        name="easystore_get_group",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_group(params: GetGroupInput) -> str:
        """取得單筆會員群組詳情。

        Args:
            params: group_id

        Returns:
            str: JSON 格式的群組資料。
        """
        data = await api_get(f"groups/{params.group_id}")
        return to_json(extract_resource(data, "group"))

    @mcp.tool(
        name="easystore_list_group_customers",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_group_customers(params: GetGroupInput) -> str:
        """取得群組成員列表（customer_ids）。

        適合用於：分析特定群組的成員組成、批次操作前的成員確認。

        Args:
            params: group_id

        Returns:
            str: JSON，{ "group": { "title": ..., "customer_ids": [...] } }
        """
        data = await api_get_nested(f"groups/{params.group_id}/customers")
        return to_json(data)

    @mcp.tool(
        name="easystore_list_customer_attributes",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_customer_attributes(params: ListCustomerAttributesInput) -> str:
        """列出商店的自訂會員屬性欄位定義。

        適合用於：了解有哪些自訂欄位、確認欄位類型和選項。

        Args:
            params: 分頁

        Returns:
            str: JSON，customer_attributes 陣列（含 title、input_type、options）。
        """
        query = {"page": params.page, "limit": params.limit}
        data = await api_get("customer_attributes", query)
        return to_json(data)
