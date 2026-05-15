"""
tool_registry.py — 工具統一註冊

集中管理所有工具的載入，讀寫分離控制。
寫入工具需設定環境變數 ENABLE_WRITE_TOOLS=true 才會載入。
"""

from mcp.server.fastmcp import FastMCP

from config.settings import ENABLE_WRITE_TOOLS
from tools.analytics_tools import register_analytics_tools
from tools.order_tools import register_order_tools
from tools.product_tools import register_product_tools
from tools.customer_tools import register_customer_tools
from tools.settings_tools import register_settings_tools
from tools.storefront_tools import register_storefront_tools


def register_all_tools(mcp: FastMCP) -> int:
    """
    註冊所有工具到 MCP server。
    回傳已載入的工具數量。
    """
    # ── 讀取工具（預設全部載入）──────────────────────────
    register_analytics_tools(mcp)
    register_order_tools(mcp)
    register_product_tools(mcp)
    register_customer_tools(mcp)
    register_settings_tools(mcp)
    register_storefront_tools(mcp)

    read_count = (
        10  # analytics
        + 8   # orders
        + 10  # products
        + 10  # customers
        + 13  # settings
        + 7   # storefront
    )

    # ── 寫入工具（需明確啟用）────────────────────────────
    write_count = 0
    if ENABLE_WRITE_TOOLS:
        from tools.writes.order_writes import register_order_writes
        from tools.writes.product_writes import register_product_writes
        from tools.writes.customer_writes import register_customer_writes
        from tools.writes.storefront_writes import register_storefront_writes
        from tools.writes.settings_writes import register_settings_writes

        register_order_writes(mcp)
        register_product_writes(mcp)
        register_customer_writes(mcp)
        register_storefront_writes(mcp)
        register_settings_writes(mcp)
        write_count = 41  # 6 orders + 9 customers + 8 products + 9 storefront + 9 settings

    return read_count + write_count
