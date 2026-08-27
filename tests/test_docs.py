#!/usr/bin/env python3
"""
文件與實際註冊狀態的一致性檢查。

README / CLAUDE.md 的工具數量與清單過去是手動維護的，工具增減後沒人同步，
數字與歸屬都漂掉過（例如 get_collection_product_count 實際註冊在 analytics
卻列在商品工具表）。這裡把文件當成會過期的東西來驗。
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("EASYSTORE_SHOP_URL", "https://test.example.com")
os.environ.setdefault("EASYSTORE_ACCESS_TOKEN", "test_token")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp_easystore.tools.tool_registry import register_all_tools  # noqa: E402


def _tool_names(enable_writes):
    os.environ["ENABLE_WRITE_TOOLS"] = "true" if enable_writes else "false"
    import importlib

    import mcp_easystore.config.settings
    import mcp_easystore.tools.tool_registry

    importlib.reload(mcp_easystore.config.settings)
    importlib.reload(mcp_easystore.tools.tool_registry)

    mcp = FastMCP("test")
    mcp_easystore.tools.tool_registry.register_all_tools(mcp)
    return [t.name for t in asyncio.run(mcp.list_tools())]


@pytest.fixture(scope="module")
def read_tools():
    return _tool_names(enable_writes=False)


@pytest.fixture(scope="module")
def all_tools():
    return _tool_names(enable_writes=True)


@pytest.fixture(scope="module")
def readme():
    return (REPO_ROOT / "README.md").read_text()


def test_every_tool_appears_in_readme(all_tools, readme):
    """每個註冊的工具都要在 README 找得到（含 easystore_ 前綴或省略前綴）。"""
    missing = [
        name for name in all_tools
        if name not in readme and name.replace("easystore_", "") not in readme
    ]
    assert missing == [], f"README 沒有記錄這些工具: {missing}"


def test_readme_totals_match_actual(read_tools, all_tools, readme):
    read_n, write_n = len(read_tools), len(all_tools) - len(read_tools)
    assert f"**{read_n} 個讀取工具**" in readme
    assert f"## 讀取工具（{read_n} 個，預設全部載入）" in readme
    assert f"**{write_n} 個寫入工具**" in readme
    assert f"## 寫入工具（{write_n} 個，需 `ENABLE_WRITE_TOOLS=true`）" in readme


def test_claude_md_totals_match_actual(read_tools, all_tools):
    text = (REPO_ROOT / "CLAUDE.md").read_text()
    read_n, write_n = len(read_tools), len(all_tools) - len(read_tools)
    assert f"**{read_n} 個讀取工具 + {write_n} 個寫入工具**" in text


def test_docs_do_not_reference_removed_config_files():
    """已刪除的設定檔不該再出現在文件裡（故障排除段落的說明除外）。"""
    stale = ("`.claude/launch.json`", "env-variable-guide.md", "mcp-cowork-setup.md")
    offenders = []
    for path in REPO_ROOT.glob("*.md"):
        text = path.read_text()
        offenders += [f"{path.name}: {s}" for s in stale if s in text]
    for path in (REPO_ROOT / "docs").rglob("*.md"):
        if "archive" in path.parts:  # 歷史紀錄保持原樣
            continue
        text = path.read_text()
        offenders += [f"{path.name}: {s}" for s in stale if s in text]
    assert offenders == [], f"文件仍指向已刪除的檔案: {offenders}"
