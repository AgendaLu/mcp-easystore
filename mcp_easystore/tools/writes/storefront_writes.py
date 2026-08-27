"""
storefront_writes.py — 前台內容寫入工具（9 個）

涵蓋頁面 CRUD、導覽選單更新、轉址規則 CRUD、Snippet 與 Script Tag 更新。
所有工具需 ENABLE_WRITE_TOOLS=true 才會載入。
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from mcp_easystore.tools.base_tool import api_post, api_put, api_delete, to_json


# ── Pydantic Models ───────────────────────────────────────

class CreatePageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(..., description="頁面標題", min_length=1)
    body_html: Optional[str] = Field(None, description="頁面內容（HTML）")
    published: Optional[bool] = Field(None, description="是否公開，預設 false（草稿）")


class UpdatePageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page_id: str = Field(..., description="頁面 ID", min_length=1)
    title: Optional[str] = Field(None, description="頁面標題")
    body_html: Optional[str] = Field(None, description="頁面內容（HTML）")
    published: Optional[bool] = Field(None, description="是否公開")


class DeletePageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    page_id: str = Field(..., description="頁面 ID，⚠️ 刪除後無法復原", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


class UpdateNavigationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    navigation_id: str = Field(..., description="導覽選單 ID", min_length=1)
    title: Optional[str] = Field(None, description="選單標題")


class CreateRedirectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(..., description="來源路徑，例如：/old-page", min_length=1)
    target: str = Field(..., description="目標路徑，例如：/new-page", min_length=1)


class UpdateRedirectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    redirect_id: str = Field(..., description="轉址規則 ID", min_length=1)
    path: Optional[str] = Field(None, description="來源路徑")
    target: Optional[str] = Field(None, description="目標路徑")


class DeleteRedirectInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    redirect_id: str = Field(..., description="轉址規則 ID", min_length=1)
    confirm: bool = Field(False, description="需明確設為 true 才會執行刪除")


class UpdateSnippetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    snippet_id: str = Field(..., description="Snippet ID", min_length=1)
    value: str = Field(..., description="Snippet 內容（HTML/Liquid）")


class UpdateScriptTagInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    script_tag_id: str = Field(..., description="Script Tag ID", min_length=1)
    src: str = Field(..., description="Script 來源 URL", min_length=1)


# ── 工具註冊 ──────────────────────────────────────────────

def register_storefront_writes(mcp: FastMCP):

    @mcp.tool()
    async def easystore_create_page(params: CreatePageInput) -> str:
        """建立新的前台頁面。未設定 published=true 則為草稿。"""
        page: dict = {"title": params.title}
        if params.body_html is not None:
            page["body_html"] = params.body_html
        if params.published is not None:
            page["published"] = params.published
        result = await api_post("pages", {"page": page})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_page(params: UpdatePageInput) -> str:
        """更新前台頁面的標題、內容或發布狀態。"""
        page: dict = {}
        if params.title is not None:
            page["title"] = params.title
        if params.body_html is not None:
            page["body_html"] = params.body_html
        if params.published is not None:
            page["published"] = params.published
        result = await api_put(f"pages/{params.page_id}", {"page": page})
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_page(params: DeletePageInput) -> str:
        """⚠️ 刪除前台頁面（不可逆）。需傳入 confirm=true 才會執行。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"pages/{params.page_id}")
        return to_json(result)

    @mcp.tool()
    async def easystore_update_navigation(params: UpdateNavigationInput) -> str:
        """更新導覽選單標題。先用 easystore_list_navigations 查詢可用選單。"""
        navigation: dict = {}
        if params.title is not None:
            navigation["title"] = params.title
        result = await api_put(f"navigations/{params.navigation_id}", {"navigation": navigation})
        return to_json(result)

    @mcp.tool()
    async def easystore_create_redirect(params: CreateRedirectInput) -> str:
        """建立網址轉址規則，將舊路徑導向新路徑。"""
        result = await api_post(
            "redirects", {"redirect": {"path": params.path, "target": params.target}}
        )
        return to_json(result)

    @mcp.tool()
    async def easystore_update_redirect(params: UpdateRedirectInput) -> str:
        """更新現有轉址規則的來源或目標路徑。"""
        redirect: dict = {}
        if params.path is not None:
            redirect["path"] = params.path
        if params.target is not None:
            redirect["target"] = params.target
        result = await api_put(f"redirects/{params.redirect_id}", {"redirect": redirect})
        return to_json(result)

    @mcp.tool()
    async def easystore_delete_redirect(params: DeleteRedirectInput) -> str:
        """⚠️ 刪除轉址規則（不可逆）。需傳入 confirm=true 才會執行。"""
        if not params.confirm:
            return to_json({"error": "請設定 confirm=true 以確認刪除操作。"})
        result = await api_delete(f"redirects/{params.redirect_id}")
        return to_json(result)

    @mcp.tool()
    async def easystore_update_snippet(params: UpdateSnippetInput) -> str:
        """更新前台 Snippet 內容（HTML/Liquid）。先用 easystore_list_snippets 查詢可用 Snippet。"""
        result = await api_put(f"snippets/{params.snippet_id}", {"snippet": {"value": params.value}})
        return to_json(result)

    @mcp.tool()
    async def easystore_update_script_tag(params: UpdateScriptTagInput) -> str:
        """更新 Script Tag 的來源 URL。先用 easystore_list_script_tags 查詢現有 Script Tags。"""
        result = await api_put(f"script_tags/{params.script_tag_id}", {"script_tag": {"src": params.src}})
        return to_json(result)
