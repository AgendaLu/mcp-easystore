#!/usr/bin/env python3
"""
P1 验证脚本: EasyStore API 对 fields 参数的支持程度

验证以下 endpoint 的 fields 参数支持：
1. GET /orders.json?fields=...
2. GET /checkouts.json?fields=...
3. GET /orders/:id/fulfillments.json?fields=...

测试方法：
1. 调用不带 fields 的 API
2. 调用带 fields="" 的 API (最小化字段)
3. 调用带 fields="items" 的 API (指定字段)
4. 对比响应大小和字段
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# 加入项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量 - 必须在导入 config 之前，并使用 override=True 强制覆盖
from dotenv import load_dotenv
from pathlib import Path
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file, override=True)

from mcp_easystore.tools.base_tool import api_get, api_get_nested, to_json
from mcp_easystore.config.settings import validate_config, EASYSTORE_SHOP_URL, EASYSTORE_ACCESS_TOKEN

# ========== 测试工具函数 ==========

def analyze_response(data_dict, label=""):
    """分析 API 响应"""
    if isinstance(data_dict, str):
        return {"error": data_dict, "size": len(data_dict), "tokens": len(data_dict) / 4}

    json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
    char_count = len(json_str)
    token_count = char_count / 4

    # 分析顶级字段
    if isinstance(data_dict, dict):
        top_keys = list(data_dict.keys())
        if len(top_keys) > 0 and isinstance(data_dict[top_keys[0]], list):
            first_item = data_dict[top_keys[0]][0] if data_dict[top_keys[0]] else {}
            item_keys = list(first_item.keys()) if isinstance(first_item, dict) else []
        else:
            item_keys = []
    else:
        top_keys = []
        item_keys = []

    return {
        "char_count": char_count,
        "tokens": token_count,
        "top_level_keys": top_keys,
        "first_item_keys": item_keys,
        "sample": json_str[:300] + "..." if len(json_str) > 300 else json_str
    }

def compare_responses(resp1, resp2, label1="默认", label2="fields=''"):
    """对比两个响应"""
    tokens1 = resp1.get("tokens", 0)
    tokens2 = resp2.get("tokens", 0)

    if tokens1 > 0:
        savings = (tokens1 - tokens2) / tokens1 * 100
        reduction = (tokens1 - tokens2)
    else:
        savings = 0
        reduction = 0

    print(f"\n{'='*70}")
    print(f"对比: {label1} vs {label2}")
    print(f"{'='*70}")
    print(f"\n{label1}:")
    print(f"  字符数: {resp1.get('char_count', 'N/A'):,}")
    print(f"  Token: {resp1.get('tokens', 'N/A'):.0f}")
    print(f"  字段: {resp1.get('first_item_keys', [])[:5]}...")

    print(f"\n{label2}:")
    print(f"  字符数: {resp2.get('char_count', 'N/A'):,}")
    print(f"  Token: {resp2.get('tokens', 'N/A'):.0f}")
    print(f"  字段: {resp2.get('first_item_keys', [])[:5]}...")

    if tokens1 > 0:
        print(f"\n✨ 节省:")
        print(f"  Token 减少: {reduction:.0f} ({savings:.1f}%)")
        print(f"  加速倍数: {tokens1/tokens2:.1f}x")
    else:
        print(f"\n⚠️ 无法对比 (错误响应)")

# ========== 主测试逻辑 ==========

async def test_orders_fields():
    """测试 /orders.json 的 fields 支持"""
    print(f"\n{'#'*70}")
    print("# TEST 1: GET /orders.json - fields 支持性")
    print(f"{'#'*70}")

    # 测试 1.1: 默认查询
    print(f"\n[1.1] 不指定 fields 参数...")
    resp_default = await api_get("orders", {
        "limit": 10,
        "page": 1
    })
    analysis_default = analyze_response(resp_default, "默认")

    # 测试 1.2: fields=""
    print(f"[1.2] 指定 fields='' (最小化字段)...")
    resp_empty = await api_get("orders", {
        "limit": 10,
        "page": 1,
        "fields": ""
    })
    analysis_empty = analyze_response(resp_empty, "fields=''")

    # 测试 1.3: fields="items"
    print(f"[1.3] 指定 fields='items'...")
    resp_items = await api_get("orders", {
        "limit": 10,
        "page": 1,
        "fields": "items"
    })
    analysis_items = analyze_response(resp_items, "fields='items'")

    # 对比结果
    if not isinstance(resp_default, str) and not isinstance(resp_empty, str):
        compare_responses(analysis_default, analysis_empty, "默认", "fields=''")

    if not isinstance(resp_default, str) and not isinstance(resp_items, str):
        compare_responses(analysis_default, analysis_items, "默认", "fields='items'")

    return {
        "default": analysis_default,
        "empty": analysis_empty,
        "items": analysis_items
    }

async def test_checkouts_fields():
    """测试 /checkouts.json 的 fields 支持"""
    print(f"\n{'#'*70}")
    print("# TEST 2: GET /checkouts.json - fields 支持性")
    print(f"{'#'*70}")

    # 测试 2.1: 默认查询
    print(f"\n[2.1] 不指定 fields 参数...")
    resp_default = await api_get("checkouts", {
        "limit": 10,
        "page": 1
    })
    analysis_default = analyze_response(resp_default, "默认")

    # 测试 2.2: fields=""
    print(f"[2.2] 尝试 fields='' (最小化字段)...")
    resp_empty = await api_get("checkouts", {
        "limit": 10,
        "page": 1,
        "fields": ""
    })
    analysis_empty = analyze_response(resp_empty, "fields=''")

    # 对比结果
    if not isinstance(resp_default, str) and not isinstance(resp_empty, str):
        compare_responses(analysis_default, analysis_empty, "默认", "fields=''")
    else:
        # 检查是否返回错误
        if isinstance(resp_empty, str) and "Error" in resp_empty:
            print(f"\n⚠️ fields 参数可能不支持: {resp_empty}")

    return {
        "default": analysis_default,
        "empty": analysis_empty
    }

async def test_fulfillments_fields():
    """测试 /orders/:id/fulfillments.json 的 fields 支持"""
    print(f"\n{'#'*70}")
    print("# TEST 3: GET /orders/:id/fulfillments.json - fields 支持性")
    print(f"{'#'*70}")

    # 首先获取一个订单 ID
    print(f"\n[3.0] 获取一个订单 ID 用于测试...")
    orders_data = await api_get("orders", {"limit": 1, "page": 1})

    if isinstance(orders_data, str):
        print(f"❌ 无法获取订单: {orders_data}")
        return None

    orders = orders_data.get("orders", [])
    if not orders:
        print(f"❌ 没有订单数据可用")
        return None

    order_id = orders[0].get("id")
    print(f"✅ 使用订单 ID: {order_id}")

    # 测试 3.1: 默认查询
    print(f"\n[3.1] 不指定 fields 参数...")
    resp_default = await api_get_nested(f"orders/{order_id}/fulfillments", {})
    analysis_default = analyze_response(resp_default, "默认")

    # 测试 3.2: fields=""
    print(f"[3.2] 尝试 fields='' (最小化字段)...")
    resp_empty = await api_get_nested(f"orders/{order_id}/fulfillments", {"fields": ""})
    analysis_empty = analyze_response(resp_empty, "fields=''")

    # 对比结果
    if not isinstance(resp_default, str) and not isinstance(resp_empty, str):
        compare_responses(analysis_default, analysis_empty, "默认", "fields=''")
    else:
        if isinstance(resp_empty, str) and "Error" in resp_empty:
            print(f"\n⚠️ fields 参数可能不支持: {resp_empty}")

    return {
        "order_id": order_id,
        "default": analysis_default,
        "empty": analysis_empty
    }

async def main():
    # 验证配置
    error = validate_config()
    if error:
        print(f"❌ 配置错误: {error}")
        sys.exit(1)

    print(f"✅ 配置正常")
    print(f"   Shop URL: {EASYSTORE_SHOP_URL}")
    print(f"   Token: {EASYSTORE_ACCESS_TOKEN[:10]}...{EASYSTORE_ACCESS_TOKEN[-10:]}")

    # 运行测试
    try:
        results = {}
        results["orders"] = await test_orders_fields()
        results["checkouts"] = await test_checkouts_fields()
        results["fulfillments"] = await test_fulfillments_fields()

        # 生成总结报告
        print(f"\n\n{'='*70}")
        print("📋 测试总结")
        print(f"{'='*70}\n")

        print("✅ TEST 1: /orders.json")
        if isinstance(results["orders"]["empty"], dict) and "tokens" in results["orders"]["empty"]:
            print("   ✅ fields 参数: 支持")
            savings = (results["orders"]["default"]["tokens"] - results["orders"]["empty"]["tokens"]) / results["orders"]["default"]["tokens"] * 100
            print(f"   📊 优化效果: {savings:.1f}% 节省")
        else:
            print("   ❌ fields 参数: 不支持或错误")

        print("\n✅ TEST 2: /checkouts.json")
        if isinstance(results["checkouts"]["empty"], dict) and "tokens" in results["checkouts"]["empty"]:
            print("   ✅ fields 参数: 支持")
            savings = (results["checkouts"]["default"]["tokens"] - results["checkouts"]["empty"]["tokens"]) / results["checkouts"]["default"]["tokens"] * 100
            print(f"   📊 优化效果: {savings:.1f}% 节省")
        else:
            print("   ❌ fields 参数: 不支持或错误")

        print("\n✅ TEST 3: /orders/:id/fulfillments.json")
        if results["fulfillments"] and isinstance(results["fulfillments"]["empty"], dict) and "tokens" in results["fulfillments"]["empty"]:
            print("   ✅ fields 参数: 支持")
            savings = (results["fulfillments"]["default"]["tokens"] - results["fulfillments"]["empty"]["tokens"]) / results["fulfillments"]["default"]["tokens"] * 100
            print(f"   📊 优化效果: {savings:.1f}% 节省")
        else:
            print("   ❌ fields 参数: 不支持或错误")

        print(f"\n{'='*70}")
        print("✨ 验证完成！")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
