"""
product_writes.py — 商品與分類寫入工具（8 個）

涵蓋商品 CRUD、規格批次更新、分類 CRUD、商品分類關聯管理。
所有工具需 ENABLE_WRITE_TOOLS=true 才會載入。
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from tools.base_tool import api_post, api_put, api_delete, to_json


# ── Pydantic Models ───────────────────────────────────────

class CreateProductInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(..., description="商品名稱", min_length=1)
    description: Optional[str] = Field(None, description="商品描述（純文字）")
    body_html: Optional[str] = Field(None, description="商品描述（HTML）")
    published_at: Optional[str] = Field(None, description="上架時間，格式：YYYY-MM-DD HH:MM:SS；留空則為草稿")


class UpdateProductInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., description="商品 ID", min_length=1)
    title: Optional[str] = Field(None, description="商品名稱")
    description: Optional[str] = Field(None, description="商品描述（純文字）")
    body_html: Optional[str] = Field(None, description="商品描述（HTML）")
    published_at: Optional[str] = Field(None, description="上架時間；設為空字串可下架")


class UpdateVariantsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., description="商品 ID", min_length=1)
    variants: List[dict] = Field(
        ...,
        description="規格清單，每筆需含 id。可更新欄位：price, compare_at_price, inventory_quantity, sku, barcode",
        min_length=1,
    )


class CreateCollectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(..., description="分類名稱", min_length=1)
    metafields_global_title_tag: Optional[str] = Field(None, description="SEO 標題")


class UpdateCollectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    collection_id: str = Field(..., description="分類 ID", min_length=1)
    name: Optional[str] = Field(None, description="分類名稱")
    description: Optional[str] = Field(None, description="分類描述")
    metafields_global_title_tag: Optional[str] = Field(None, description="SEO 標題")
    metafields_global_description_tag: Optional[str] = Field(None, description="SEO 描述")


class DeleteCollectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    collection_id: str = Field(..., description="分類 ID，⚠️ 刪除後無法復原", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


class CreateCollectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., description="商品 ID", min_length=1)
    collection_id: str = Field(..., description="分類 ID", min_length=1)


class DeleteCollectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    collect_id: str = Field(..., description="Collect ID（商品與分類的關聯 ID）", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


# ── 工具註冊 ──────────────────────────────────────────────

def register_product_writes(mcp: FastMCP):

    @mcp.tool()
    async def easystore_create_product(params: CreateProductInput) -> str:
        """建立新商品。未設定 published_at 則為草稿狀態。"""
        product: dict = {"title": params.title}
        if params.description:
            product["description"] = params.description
        if params.body_html:
            product["body_html"] = params.body_html
        if params.published_at is not None:
            product["published_at"] = params.published_at
        result = await api_post("products", {"product": product})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_product(params: UpdateProductInput) -> str:
        """更新商品資訊。published_at 設為空字串可下架商品。"""
        product: dict = {}
        if params.title is not None:
            product["title"] = params.title
        if params.description is not None:
            product["description"] = params.description
        if params.body_html is not None:
            product["body_html"] = params.body_html
        if params.published_at is not None:
            product["published_at"] = params.published_at
        result = await api_put(f"products/{params.product_id}", {"product": product})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_variants(params: UpdateVariantsInput) -> str:
        """批次更新商品規格（價格、庫存、SKU 等）。每筆 variant 需含 id。"""
        result = await api_put(
            f"products/{params.product_id}/variants", {"variants": params.variants}
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_create_collection(params: CreateCollectionInput) -> str:
        """建立新的商品分類。"""
        collection: dict = {"name": params.name}
        if params.metafields_global_title_tag:
            collection["metafields_global_title_tag"] = params.metafields_global_title_tag
        result = await api_post("collections", {"collection": collection})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_collection(params: UpdateCollectionInput) -> str:
        """更新商品分類名稱、描述或 SEO 設定。"""
        collection: dict = {}
        for field in ["name", "description", "metafields_global_title_tag", "metafields_global_description_tag"]:
            val = getattr(params, field)
            if val is not None:
                collection[field] = val
        result = await api_put(f"collections/{params.collection_id}", {"collection": collection})
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_collection(params: DeleteCollectionInput) -> str:
        """⚠️ 刪除分類（不可逆）。需傳入 confirm=true 才會執行。分類內商品不會被刪除。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"collections/{params.collection_id}")
        return to_json(result)

    @mcp.tool()
    async def easystore_create_collect(params: CreateCollectInput) -> str:
        """將商品加入分類（建立商品-分類關聯）。"""
        result = await api_post(
            "collects", {"collect": {"product_id": params.product_id, "collection_id": params.collection_id}}
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_collect(params: DeleteCollectInput) -> str:
        """⚠️ 從分類移除商品（刪除關聯，不刪除商品本身）。需傳入 confirm=true 才會執行。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"collects/{params.collect_id}")
        return to_json(result)
