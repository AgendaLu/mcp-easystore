#!/usr/bin/env python3
"""
測試腳本 - 查詢今天的訂單資料
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# 加入專案根目錄
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 載入環境變數
from dotenv import load_dotenv
load_dotenv()

from tools.order_tools import register_order_tools
from tools.base_tool import api_get, to_json
from config.settings import validate_config, EASYSTORE_SHOP_URL, EASYSTORE_ACCESS_TOKEN
from mcp.server.fastmcp import FastMCP

async def main():
    # 驗證配置
    error = validate_config()
    if error:
        print(f"❌ 配置錯誤：{error}")
        sys.exit(1)

    print(f"✅ 配置正常")
    print(f"   Shop URL: {EASYSTORE_SHOP_URL}")
    print(f"   Token: {EASYSTORE_ACCESS_TOKEN[:10]}...{EASYSTORE_ACCESS_TOKEN[-10:]}")
    print()

    # 獲取今天的日期範圍
    today = datetime.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    created_at_min = today_start.strftime("%Y-%m-%d %H:%M:%S")
    created_at_max = today_end.strftime("%Y-%m-%d %H:%M:%S")

    print(f"📅 查詢日期範圍：{created_at_min} ~ {created_at_max}")
    print()

    # 構建查詢參數
    query_params = {
        "created_at_min": created_at_min,
        "created_at_max": created_at_max,
        "limit": 250,
        "fields": "items,customer,transactions"
    }

    print("🔍 正在查詢訂單資料...")
    try:
        data = await api_get("orders", query_params)
        result = to_json(data)
        print()
        print("="*60)
        print("📊 查詢結果")
        print("="*60)
        print(result)

    except Exception as e:
        print(f"❌ 查詢失敗：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
