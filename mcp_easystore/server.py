#!/usr/bin/env python3
"""
mcp_easystore.server — EasyStore MCP Server 入口

stdio JSON-RPC 2.0，供 Claude Code / Claude Desktop 使用。
讀取工具預設全部啟用；寫入工具需設定 ENABLE_WRITE_TOOLS=true。

環境變數：
  EASYSTORE_SHOP_URL       商店網址，例如 https://yourshop.easystore.co
  EASYSTORE_ACCESS_TOKEN   EasyStore App Access Token
  ENABLE_WRITE_TOOLS       設為 true 才啟用寫入工具（預設 false）

啟動方式：
  uvx --from git+https://github.com/AgendaLu/mcp-easystore mcp-easystore
  python -m mcp_easystore.server
"""

import sys

from mcp.server.fastmcp import FastMCP

from mcp_easystore.tools.tool_registry import register_all_tools, ENABLE_WRITE_TOOLS

mcp = FastMCP("easystore_mcp")

tool_count = register_all_tools(mcp)

write_status = "✅ 寫入工具已啟用" if ENABLE_WRITE_TOOLS else "🔒 寫入工具未啟用（設定 ENABLE_WRITE_TOOLS=true 啟用）"

# 啟動時輸出到 stderr（不影響 stdio 通訊）
print(f"[easystore_mcp] 已載入 {tool_count} 個工具 | {write_status}", file=sys.stderr)


def main():
    """console script entry point（pyproject.toml 的 mcp-easystore 指令）。"""
    mcp.run()


if __name__ == "__main__":
    main()
