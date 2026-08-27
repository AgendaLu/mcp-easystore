#!/bin/bash

# MCP Server 啟動腳本
# 在 Cowork 中運行 EasyStore MCP Server

set -e

# 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "❌ 虛擬環境不存在，請先執行: python3 -m venv .venv"
    exit 1
fi

# 啟動虛擬環境
source .venv/bin/activate

# 檢查環境變數
if [ -z "$EASYSTORE_SHOP_URL" ]; then
    echo "⚠️  環境變數 EASYSTORE_SHOP_URL 未設定"
    echo "   請 export 環境變數，或寫在 .env.local（見 docs/setup/setup-guide.md）"
fi

if [ -z "$EASYSTORE_ACCESS_TOKEN" ]; then
    echo "⚠️  環境變數 EASYSTORE_ACCESS_TOKEN 未設定"
    echo "   請 export 環境變數，或寫在 .env.local（見 docs/setup/setup-guide.md）"
fi

# 啟動 MCP Server
echo "🚀 啟動 EasyStore MCP Server..."
echo "   店鋪: $EASYSTORE_SHOP_URL"
echo "   寫入工具: ${ENABLE_WRITE_TOOLS:=false}"
echo ""

python3 -m mcp_easystore.server
