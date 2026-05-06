"""
storefront_tools.py — Storefront 建設讀取工具（~8 個）

EasyStore 獨有的 Storefront 基礎建設層（Pages / Navigations / Redirects / Snippets / Script Tags）。
Shopline 無對應資源。
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from tools.base_tool import api_get, to_json, extract_resource


class ListPagesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=250)
    visibility: Optional[str] = Field(None, description="published / unpublished / any")
    handle: Optional[str] = Field(None, description="頁面 handle slug")
    title: Optional[str] = Field(None, description="標題篩選")

class GetByIdInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    id: str = Field(..., min_length=1)

class ListNavigationsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)

class ListRedirectsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    path: Optional[str] = Field(None, description="原始路徑篩選")
    target: Optional[str] = Field(None, description="目標路徑篩選")

class ListSnippetsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    field: Optional[str] = Field(None, description="片段位置，例如 global/body_start")

class ListScriptTagsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=250)
    src: Optional[str] = Field(None, description="依 JS URL 篩選")


def register_storefront_tools(mcp: FastMCP):

    @mcp.tool(
        name="easystore_list_pages",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_pages(params: ListPagesInput) -> str:
        """列出 EasyStore 靜態頁面。

        靜態頁面通常用於「關於我們」、「常見問題」、「退換貨政策」等。
        適合用於：Storefront 內容審計、SEO 頁面盤點。

        Returns:
            str: JSON，pages 陣列（含 handle、published_at）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("pages", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_get_page",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_get_page(params: GetByIdInput) -> str:
        """取得單筆靜態頁面詳情（含 body_html）。"""
        data = await api_get(f"pages/{params.id}")
        return to_json(extract_resource(data, "page"))

    @mcp.tool(
        name="easystore_list_navigations",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_navigations(params: ListNavigationsInput) -> str:
        """列出 Storefront 導覽選單項目。

        包含 header、footer 等選單結構，每個項目有 parent_id 形成樹狀關係。
        適合用於：網站架構審計、導覽結構分析。

        Returns:
            str: JSON，navigations 陣列（含 name、link、parent_id、handle）。
        """
        query = {"page": params.page, "limit": params.limit}
        data = await api_get("navigations", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_count_navigations",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_count_navigations() -> str:
        """取得導覽選單項目總數。"""
        data = await api_get("navigations/count")
        return to_json(data)

    @mcp.tool(
        name="easystore_list_redirects",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_redirects(params: ListRedirectsInput) -> str:
        """列出 URL 轉址規則。

        適合用於：SEO 轉址審計、舊網址遷移確認、找出失效轉址。

        Returns:
            str: JSON，redirects 陣列（含 path、target、kind）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("redirects", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_list_snippets",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_snippets(params: ListSnippetsInput) -> str:
        """列出注入 Storefront 的 HTML/Liquid 片段。

        Snippet 可注入到 global/body_start、global/body_end 等位置，
        常用於 GA、FB Pixel、第三方追蹤等程式碼。

        Returns:
            str: JSON，snippets 陣列（含 field、value）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("snippets", query)
        return to_json(data)

    @mcp.tool(
        name="easystore_list_script_tags",
        annotations={"readOnlyHint": True, "destructiveHint": False}
    )
    async def easystore_list_script_tags(params: ListScriptTagsInput) -> str:
        """列出注入 Storefront 的外部 JavaScript 連結。

        Script Tag 用於引入外部 JS 檔案（例如 chatbot、analytics SDK）。
        適合用於：前端資源審計、找出過時的第三方腳本。

        Returns:
            str: JSON，script_tags 陣列（含 src）。
        """
        query = params.model_dump(exclude_none=True)
        data = await api_get("script_tags", query)
        return to_json(data)
