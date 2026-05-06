"""
product_tools.py — 商品讀取工具（~12 個）

涵蓋商品列表、規格、圖片、分類、Collects。
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from tools.base_tool import api_get, api_get_nested, to_json, extract_resource


class ListProductsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    visibility: Optional[str] = Field(None, description="published / unpublished")
    collection_ids: Optional[str] = Field(None, description="逗號分隔的分類 ID，例如：123,456")
    skus: Optional[str] = Field(None, description="逗號分隔的 SKU 列表")
    ids: Optional[str] = Field(None, description="逗號分隔的商品 ID")
    since_id: Optional[int] = Field(None)
    is_bundle: Optional[bool] = Field(None, description="是否為組合商品")
    created_at_min: Optional[str] = Field(None)
    created_at_max: Optional[str] = Field(None)
    updated_at_min: Optional[str] = Field(None)
    updated_at_max: Optional[str] = Field(None)
    sort: Optional[str] = Field(None, description="例如 position.desc")

class GetProductInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., min_length=1)

class ListVariantsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., min_length=1)

class GetVariantInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., min_length=1)
    variant_id: str = Field(..., min_length=1)

class ListImagesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    product_id: str = Field(..., min_length=1)

class ListCollectionsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    ids: Optional[str] = Field(None)
    since_id: Optional[int] = Field(None)
    visibility: Optional[str] = Field(None, description="true / false")
    sort: Optional[str] = Field(None, description="例如 id.asc")

class GetCollectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    collection_id: str = Field(..., min_length=1)

class ListCollectsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    collection_id: Optional[int] = Field(None, description="依分類 ID 篩選")
    product_id: Optional[int] = Field(None, description="依商品 ID 篩選")
    since_id: Optional[int] = Field(None)


def register_product_tools(mcp: FastMCP):

    @mcp.tool(
        name="easystore_list_products",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_products(params: ListProductsInput) -> str:
        """列出 EasyStore 商品，支援多條件篩選。

        可依上架狀態、分類、SKU、商品 ID、時間區間等條件篩選。
        適合用於：商品目錄管理、庫存盤點、特定條件的商品查詢。

        Args:
            params: 篩選條件 + 分頁

        Returns:
            str: JSON，包含 total_count、products 陣列（含價格、庫存、規格）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("products", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_product",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_product(params: GetProductInput) -> str:
        """取得單筆商品完整資料（含所有規格、圖片）。

        Args:
            params: product_id

        Returns:
            str: JSON 格式的商品資料。
        """
        data = await api_get(f"products/{params.product_id}")
        return to_json(extract_resource(data, "product"))

    @mcp.tool(
        name="easystore_list_variants",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_variants(params: ListVariantsInput) -> str:
        """取得商品的所有規格（variants）列表。

        包含每個規格的 SKU、價格、庫存、尺寸重量。
        適合用於：庫存分析、規格價格比較、SKU 管理。

        Args:
            params: product_id

        Returns:
            str: JSON，variants 陣列。
        """
        data = await api_get_nested(f"products/{params.product_id}/variants")
        return to_json(data)

    @mcp.tool(
        name="easystore_get_variant",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_variant(params: GetVariantInput) -> str:
        """取得單筆規格詳情。

        Args:
            params: product_id + variant_id

        Returns:
            str: JSON 格式的規格資料。
        """
        data = await api_get_nested(f"products/{params.product_id}/variants/{params.variant_id}")
        return to_json(extract_resource(data, "variant"))

    @mcp.tool(
        name="easystore_list_product_images",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_product_images(params: ListImagesInput) -> str:
        """取得商品圖片列表。

        Args:
            params: product_id

        Returns:
            str: JSON，images 陣列（含 url、尺寸）。
        """
        data = await api_get_nested(f"products/{params.product_id}/images")
        return to_json(data)

    @mcp.tool(
        name="easystore_list_collections",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_collections(params: ListCollectionsInput) -> str:
        """列出商品分類（collections）。

        Args:
            params: 分頁 + 可選篩選（ids、visibility、sort）

        Returns:
            str: JSON，collections 陣列。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("collections", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_collection",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_collection(params: GetCollectionInput) -> str:
        """取得單筆分類詳情。

        Args:
            params: collection_id

        Returns:
            str: JSON 格式的分類資料。
        """
        data = await api_get(f"collections/{params.collection_id}")
        return to_json(extract_resource(data, "collection"))

    @mcp.tool(
        name="easystore_list_collects",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_collects(params: ListCollectsInput) -> str:
        """列出商品↔分類的關聯記錄（Collects）。

        Collect 是 EasyStore 中商品與分類之間多對多關聯的獨立資源，
        每筆記錄代表「某商品屬於某分類」。
        適合用於：確認商品分類狀態、查詢某分類包含哪些商品。

        Args:
            params: 可選 collection_id 或 product_id 篩選

        Returns:
            str: JSON，collects 陣列（含 product_id、collection_id）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("collects", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_collects_count",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_collects_count() -> str:
        """取得 Collect 關聯記錄總數。

        Returns:
            str: JSON，{ "count": N }。
        """
        data = await api_get("collects/count")
        return to_json(data)
