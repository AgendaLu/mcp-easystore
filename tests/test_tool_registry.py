#!/usr/bin/env python3
"""
tool_registry 回報的工具數量必須等於 server 上實際註冊的數量。

原本 read_count / write_count 是寫死的常數，工具增減時沒人同步，啟動訊息
與 README 的數字就跟實際狀態對不上。
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("EASYSTORE_SHOP_URL", "https://test.example.com")
os.environ.setdefault("EASYSTORE_ACCESS_TOKEN", "test_token")

from mcp.server.fastmcp import FastMCP  # noqa: E402
from tools.tool_registry import register_all_tools  # noqa: E402


def test_reported_count_matches_registered_tools():
    mcp = FastMCP("test")
    reported = register_all_tools(mcp)
    actual = len(asyncio.run(mcp.list_tools()))
    assert reported == actual


def test_all_tools_use_the_easystore_prefix():
    """工具命名慣例：easystore_<verb>_<resource>。"""
    mcp = FastMCP("test")
    register_all_tools(mcp)
    names = [t.name for t in asyncio.run(mcp.list_tools())]
    assert names, "沒有註冊到任何工具"
    bad = [n for n in names if not n.startswith("easystore_")]
    assert bad == [], f"命名不符慣例: {bad}"


def test_tool_names_are_unique():
    mcp = FastMCP("test")
    register_all_tools(mcp)
    names = [t.name for t in asyncio.run(mcp.list_tools())]
    duplicates = {n for n in names if names.count(n) > 1}
    assert duplicates == set(), f"工具名稱重複: {duplicates}"
