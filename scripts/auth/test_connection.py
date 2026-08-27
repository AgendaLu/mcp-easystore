#!/usr/bin/env python3
"""
scripts/auth/test_connection.py — API 連線驗證

執行方式：
  cd mcp-easystore
  python scripts/auth/test_connection.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from mcp_easystore.config.settings import validate_config, EASYSTORE_SHOP_URL, get_base_url
from mcp_easystore.tools.base_tool import api_get

async def main():
    print("=== EasyStore MCP Server — 連線驗證 ===\n")

    # 1. 設定檢查
    err = validate_config()
    if err:
        print(f"❌ 設定錯誤：{err}")
        print("\n請複製 .env.example 為 .env 並填入正確值，")
        print("或確認環境變數 EASYSTORE_SHOP_URL 和 EASYSTORE_ACCESS_TOKEN 已設定。")
        sys.exit(1)

    print(f"✅ 商店 URL：{EASYSTORE_SHOP_URL}")
    print(f"✅ Base URL：{get_base_url()}")
    print()

    # 2. 測試 store endpoint
    print("📡 測試 GET /store.json ...")
    data = await api_get("store")
    if isinstance(data, str):
        print(f"❌ 連線失敗：{data}")
        sys.exit(1)

    store = data.get("store", {})
    print(f"✅ 商店名稱：{store.get('name')}")
    print(f"✅ 主幣別：{store.get('currencies', [{}])[0].get('code', 'N/A')}")
    print(f"✅ 時區：{store.get('timezone', {}).get('zone', 'N/A')}")
    print(f"✅ 國家：{store.get('country_code')}")
    print()

    # 3. 測試訂單 endpoint（只取 1 筆確認 scope）
    print("📡 測試 GET /orders.json (limit=1) ...")
    orders = await api_get("orders", {"limit": 1})
    if isinstance(orders, str):
        print(f"⚠️  訂單 API 失敗（可能缺少 read_orders scope）：{orders}")
    else:
        print(f"✅ 訂單總數：{orders.get('total_count', 'N/A')}")

    # 4. 測試商品 endpoint
    print("📡 測試 GET /products.json (limit=1) ...")
    products = await api_get("products", {"limit": 1})
    if isinstance(products, str):
        print(f"⚠️  商品 API 失敗（可能缺少 read_products scope）：{products}")
    else:
        print(f"✅ 商品總數：{products.get('total_count', 'N/A')}")

    # 5. 測試會員 endpoint
    print("📡 測試 GET /customers.json (limit=1) ...")
    customers = await api_get("customers", {"limit": 1})
    if isinstance(customers, str):
        print(f"⚠️  會員 API 失敗（可能缺少 read_customers scope）：{customers}")
    else:
        print(f"✅ 會員總數：{customers.get('total_count', 'N/A')}")

    print("\n=== 連線驗證完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
