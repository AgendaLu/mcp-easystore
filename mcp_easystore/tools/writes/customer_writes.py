"""
customer_writes.py — 顧客與分群寫入工具（9 個）

涵蓋顧客更新、點數/購物金調整、顧客群組 CRUD 及成員管理。
搭配 easystore_get_rfm_orders 可實現 RFM 分析 → 自動分群閉環。
所有工具需 ENABLE_WRITE_TOOLS=true 才會載入。
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from mcp_easystore.tools.base_tool import api_post, api_put, api_delete, to_json


# ── Pydantic Models ───────────────────────────────────────

class UpdateCustomerInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., description="顧客 ID", min_length=1)
    first_name: Optional[str] = Field(None, description="名")
    last_name: Optional[str] = Field(None, description="姓")
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="電話")
    gender: Optional[str] = Field(None, description="male / female / other")
    birthdate: Optional[str] = Field(None, description="生日，格式：YYYY-MM-DD")
    country_code: Optional[str] = Field(None, description="國家代碼，例如：TW")


class AdjustPointsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., description="顧客 ID", min_length=1)
    point: int = Field(..., description="調整點數（正數=增加，負數=扣除）")
    reason: Optional[str] = Field(None, description="調整原因，例如：客服補發、活動獎勵")


class SetCreditsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., description="顧客 ID", min_length=1)
    credits: float = Field(..., description="設定購物金絕對值（直接覆蓋）", ge=0)


class AdjustCreditsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(..., description="顧客 ID", min_length=1)
    credits: float = Field(..., description="調整購物金（正數=增加，負數=扣除）")
    reason: Optional[str] = Field(None, description="調整原因")


class CreateGroupInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(..., description="群組名稱，例如：VIP 會員、流失客待喚回", min_length=1)


class UpdateGroupInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    group_id: str = Field(..., description="群組 ID", min_length=1)
    name: str = Field(..., description="新群組名稱", min_length=1)


class GroupCustomersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    group_id: str = Field(..., description="群組 ID", min_length=1)
    customer_ids: List[str] = Field(..., description="顧客 ID 清單", min_length=1)


class RemoveGroupCustomersInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    group_id: str = Field(..., description="群組 ID", min_length=1)
    customer_ids: List[str] = Field(..., description="要移除的顧客 ID 清單", min_length=1)


# ── 工具註冊 ──────────────────────────────────────────────

def register_customer_writes(mcp: FastMCP):

    @mcp.tool()
    async def easystore_update_customer(params: UpdateCustomerInput) -> str:
        """更新顧客基本資料（姓名、Email、電話、性別、生日、國家）。"""
        customer: dict = {}
        for field in ["first_name", "last_name", "email", "phone", "gender", "birthdate", "country_code"]:
            val = getattr(params, field)
            if val is not None:
                customer[field] = val
        result = await api_put(f"customers/{params.customer_id}", {"customer": customer})
        return to_json(result)

    @mcp.tool()
    async def easystore_adjust_customer_points(params: AdjustPointsInput) -> str:
        """調整顧客點數（正數增加，負數扣除）。適用客服補發、活動獎勵等情境。"""
        body: dict = {"point": params.point}
        if params.reason:
            body["reason"] = params.reason
        result = await api_put(f"customers/{params.customer_id}/point/adjust", body)
        return to_json(result)

    @mcp.tool()
    async def easystore_set_customer_credits(params: SetCreditsInput) -> str:
        """直接設定顧客購物金絕對值（覆蓋現有金額）。⚠️ 會覆蓋原有金額，若要累加請用 easystore_adjust_customer_credits。"""
        result = await api_put(
            f"customers/{params.customer_id}/credits/set", {"credits": params.credits}
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_adjust_customer_credits(params: AdjustCreditsInput) -> str:
        """相對調整顧客購物金（正數增加，負數扣除）。適用活動補發、客服處理等情境。"""
        body: dict = {"credits": params.credits}
        if params.reason:
            body["reason"] = params.reason
        result = await api_put(f"customers/{params.customer_id}/credits/adjust", body)
        return to_json(result)

    @mcp.tool()
    async def easystore_create_group(params: CreateGroupInput) -> str:
        """建立新的顧客群組。建立後可用 easystore_add_customers_to_group 加入成員。"""
        result = await api_post("groups", {"group": {"name": params.name}})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_group(params: UpdateGroupInput) -> str:
        """更新顧客群組名稱。"""
        result = await api_put(f"groups/{params.group_id}", {"group": {"name": params.name}})
        return to_json(result)

    @mcp.tool()
    async def easystore_add_customers_to_group(params: GroupCustomersInput) -> str:
        """批次將顧客加入群組。搭配 RFM 分析結果可自動化分群。"""
        result = await api_post(
            f"groups/{params.group_id}/customers", {"customer_ids": params.customer_ids}
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_update_group_customers(params: GroupCustomersInput) -> str:
        """⚠️ 替換群組內所有成員（原有成員會被清空）。適用定期重新執行 RFM 分群。"""
        result = await api_put(
            f"groups/{params.group_id}/customers", {"customer_ids": params.customer_ids}
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_remove_customers_from_group(params: RemoveGroupCustomersInput) -> str:
        """從群組中移除指定顧客。"""
        from mcp_easystore.tools.base_tool import get_base_url, get_headers, handle_api_error
        import httpx
        url = f"{get_base_url()}/groups/{params.group_id}/customers.json"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(
                    "DELETE", url,
                    headers=get_headers(),
                    json={"customer_ids": params.customer_ids}
                )
                resp.raise_for_status()
                try:
                    return to_json(resp.json())
                except Exception:
                    return to_json({"status": "removed"})
        except Exception as e:
            return handle_api_error(e, f"groups/{params.group_id}/customers")
