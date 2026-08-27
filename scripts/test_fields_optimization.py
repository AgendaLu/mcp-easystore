#!/usr/bin/env python3
"""
高级 fields 参数测试脚本

测试多种 fields 语法来找到最佳优化方案：
1. 负向语法 (-items, -customer 等)
2. 具体字段指定
3. 字段组合
4. 对比响应大小和性能影响
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

# 加入项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file, override=True)

from mcp_easystore.tools.base_tool import api_get, api_get_nested, to_json
from mcp_easystore.config.settings import validate_config, EASYSTORE_SHOP_URL, EASYSTORE_ACCESS_TOKEN

# ========== 工具函数 ==========

class ResponseAnalyzer:
    """分析 API 响应大小和结构"""

    @staticmethod
    def analyze(data_dict, label=""):
        """分析响应"""
        if isinstance(data_dict, str):
            # 错误响应
            return {
                "error": data_dict,
                "size": len(data_dict),
                "tokens": len(data_dict) / 4,
                "valid": False
            }

        if not isinstance(data_dict, dict):
            return {"error": "Invalid response type", "valid": False}

        json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
        char_count = len(json_str)
        token_count = char_count / 4

        # 提取样本项目
        first_item = None
        item_keys = []
        for key, value in data_dict.items():
            if isinstance(value, list) and len(value) > 0:
                first_item = value[0]
                item_keys = list(first_item.keys()) if isinstance(first_item, dict) else []
                break

        return {
            "size": char_count,
            "tokens": token_count,
            "item_keys": item_keys,
            "valid": True
        }

    @staticmethod
    def compare(base_result, test_result, base_label="基线", test_label="测试"):
        """对比两个响应"""
        if not base_result.get("valid") or not test_result.get("valid"):
            print(f"\n⚠️ 无法对比 - 包含错误响应")
            if not base_result.get("valid"):
                print(f"  {base_label}: {base_result.get('error', 'Unknown error')}")
            if not test_result.get("valid"):
                print(f"  {test_label}: {test_result.get('error', 'Unknown error')}")
            return None

        base_tokens = base_result.get("tokens", 0)
        test_tokens = test_result.get("tokens", 0)

        if base_tokens > 0:
            savings = (base_tokens - test_tokens) / base_tokens * 100
            reduction = base_tokens - test_tokens
            multiplier = base_tokens / test_tokens if test_tokens > 0 else float('inf')
        else:
            savings = 0
            reduction = 0
            multiplier = 1

        print(f"\n{'-'*60}")
        print(f"对比: {base_label} → {test_label}")
        print(f"{'-'*60}")
        print(f"{base_label}:")
        print(f"  Token: {base_tokens:.0f}")
        print(f"  字符: {base_result.get('size', 0):,}")
        print(f"  字段: {base_result.get('item_keys', [])[:3]}{'...' if len(base_result.get('item_keys', [])) > 3 else ''}")

        print(f"\n{test_label}:")
        print(f"  Token: {test_tokens:.0f}")
        print(f"  字符: {test_result.get('size', 0):,}")
        print(f"  字段: {test_result.get('item_keys', [])[:3]}{'...' if len(test_result.get('item_keys', [])) > 3 else ''}")

        if savings > 0:
            print(f"\n✨ 优化效果:")
            print(f"  Token 减少: {reduction:.0f} ({savings:.1f}%)")
            print(f"  加速倍数: {multiplier:.2f}x")
        else:
            print(f"\n ℹ️ 无优化效果 (相同或更大)")

        return {
            "savings": savings,
            "reduction": reduction,
            "multiplier": multiplier
        }

# ========== 测试场景 ==========

async def test_orders_fields_variants():
    """测试 orders API 的各种 fields 变体"""
    print(f"\n{'#'*70}")
    print("# 测试 1: /orders.json - 字段优化变体")
    print(f"{'#'*70}")

    results = {}
    base_result = None

    # 测试场景列表
    test_cases = [
        ("默认", None),
        ("fields=''", ""),
        ("fields='id,total_price,currency_code'", "id,total_price,currency_code"),
        ("fields='-items,-customer,-addresses'", "-items,-customer,-addresses"),
        ("fields='-items'", "-items"),
        ("fields='-customer'", "-customer"),
        ("fields='items'", "items"),
    ]

    print(f"\n[共 {len(test_cases)} 个测试场景]\n")

    for label, fields_value in test_cases:
        print(f"测试: {label}...")

        query = {"limit": 10, "page": 1}
        if fields_value is not None:
            query["fields"] = fields_value

        data = await api_get("orders", query)
        result = ResponseAnalyzer.analyze(data, label)
        results[label] = result

        if result.get("valid"):
            print(f"  ✅ Token: {result['tokens']:.0f} | 字段数: {len(result.get('item_keys', []))}")
        else:
            print(f"  ❌ 错误: {result.get('error', 'Unknown')}")

        if base_result is None and result.get("valid"):
            base_result = result

    # 对比结果
    print(f"\n\n{'='*70}")
    print("对比结果")
    print(f"{'='*70}")

    if base_result:
        for label, result in results.items():
            if label != "默认" and result.get("valid"):
                ResponseAnalyzer.compare(base_result, result, "默认", label)

    return results

async def test_checkouts_fields_variants():
    """测试 checkouts API 的各种 fields 变体"""
    print(f"\n\n{'#'*70}")
    print("# 测试 2: /checkouts.json - 字段优化变体")
    print(f"{'#'*70}")

    results = {}
    base_result = None

    test_cases = [
        ("默认", None),
        ("fields=''", ""),
        ("fields='cart_token,created_at'", "cart_token,created_at"),
        ("fields='-line_items'", "-line_items"),
        ("fields='-customer'", "-customer"),
        ("fields='line_items'", "line_items"),
        ("fields='financial_status'", "financial_status"),
    ]

    print(f"\n[共 {len(test_cases)} 个测试场景]\n")

    for label, fields_value in test_cases:
        print(f"测试: {label}...")

        query = {"limit": 10, "page": 1}
        if fields_value is not None:
            query["fields"] = fields_value

        data = await api_get("checkouts", query)
        result = ResponseAnalyzer.analyze(data, label)
        results[label] = result

        if result.get("valid"):
            print(f"  ✅ Token: {result['tokens']:.0f} | 字段数: {len(result.get('item_keys', []))}")
        else:
            print(f"  ❌ 错误: {result.get('error', 'Unknown')}")

        if base_result is None and result.get("valid"):
            base_result = result

    # 对比结果
    print(f"\n\n{'='*70}")
    print("对比结果")
    print(f"{'='*70}")

    if base_result:
        for label, result in results.items():
            if label != "默认" and result.get("valid"):
                ResponseAnalyzer.compare(base_result, result, "默认", label)

    return results

async def test_fulfillments_with_new_token():
    """用新 token 测试 fulfillments API"""
    print(f"\n\n{'#'*70}")
    print("# 测试 3: /orders/:id/fulfillments.json - 新 Token 权限测试")
    print(f"{'#'*70}")

    # 首先获取一个订单
    print(f"\n[获取订单 ID]...")
    orders_data = await api_get("orders", {"limit": 1, "page": 1})

    if isinstance(orders_data, str) or not orders_data.get("orders"):
        print(f"❌ 无法获取订单: {orders_data}")
        return None

    order_id = orders_data["orders"][0].get("id")
    print(f"✅ 订单 ID: {order_id}\n")

    results = {}
    base_result = None

    test_cases = [
        ("默认", {}),
        ("fields=''", {"fields": ""}),
        ("fields='-line_items'", {"fields": "-line_items"}),
        ("fields='status'", {"fields": "status"}),
    ]

    print(f"[共 {len(test_cases)} 个测试场景]\n")

    for label, params in test_cases:
        print(f"测试: {label}...")

        data = await api_get_nested(f"orders/{order_id}/fulfillments", params)
        result = ResponseAnalyzer.analyze(data, label)
        results[label] = result

        if result.get("valid"):
            print(f"  ✅ Token: {result['tokens']:.0f}")
        else:
            print(f"  ❌ 错误: {result.get('error', 'Unknown')}")

        if base_result is None and result.get("valid"):
            base_result = result

    # 对比结果
    print(f"\n\n{'='*70}")
    print("对比结果")
    print(f"{'='*70}")

    if base_result:
        for label, result in results.items():
            if label != "默认" and result.get("valid"):
                ResponseAnalyzer.compare(base_result, result, "默认", label)

    return results

# ========== 主函数 ==========

async def main():
    print(f"{'='*70}")
    print("高级 fields 参数优化测试")
    print(f"{'='*70}")
    print(f"\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 验证配置
    error = validate_config()
    if error:
        print(f"❌ 配置错误: {error}")
        sys.exit(1)

    print(f"✅ 配置正常")
    print(f"   Shop URL: {EASYSTORE_SHOP_URL}")
    print(f"   Token: {EASYSTORE_ACCESS_TOKEN[:10]}...{EASYSTORE_ACCESS_TOKEN[-10:]}")

    try:
        # 运行测试
        orders_results = await test_orders_fields_variants()
        checkouts_results = await test_checkouts_fields_variants()
        fulfillments_results = await test_fulfillments_with_new_token()

        # 生成总结
        print(f"\n\n{'='*70}")
        print("🎯 测试总结和建议")
        print(f"{'='*70}\n")

        # 分析 orders 结果
        print("📊 ORDERS 优化:")
        best_orders = None
        best_savings = 0
        for label, result in orders_results.items():
            if label != "默认" and result.get("valid"):
                base_tokens = orders_results["默认"]["tokens"]
                test_tokens = result["tokens"]
                savings = (base_tokens - test_tokens) / base_tokens * 100
                if savings > best_savings:
                    best_savings = savings
                    best_orders = (label, savings)

        if best_orders:
            print(f"✨ 最佳优化: {best_orders[0]}")
            print(f"   节省: {best_orders[1]:.1f}%")
        else:
            print(f"ℹ️ 无有效优化方案")

        # 分析 checkouts 结果
        print(f"\n📊 CHECKOUTS 优化:")
        best_checkouts = None
        best_savings = 0
        for label, result in checkouts_results.items():
            if label != "默认" and result.get("valid"):
                base_tokens = checkouts_results["默认"]["tokens"]
                test_tokens = result["tokens"]
                savings = (base_tokens - test_tokens) / base_tokens * 100
                if savings > best_savings:
                    best_savings = savings
                    best_checkouts = (label, savings)

        if best_checkouts:
            print(f"✨ 最佳优化: {best_checkouts[0]}")
            print(f"   节省: {best_checkouts[1]:.1f}%")
        else:
            print(f"ℹ️ 无有效优化方案")

        # 分析 fulfillments 结果
        if fulfillments_results:
            print(f"\n📊 FULFILLMENTS 优化:")
            best_fulfillments = None
            best_savings = 0
            for label, result in fulfillments_results.items():
                if label != "默认" and result.get("valid"):
                    base_tokens = fulfillments_results["默认"]["tokens"]
                    test_tokens = result["tokens"]
                    savings = (base_tokens - test_tokens) / base_tokens * 100
                    if savings > best_savings:
                        best_savings = savings
                        best_fulfillments = (label, savings)

            if best_fulfillments:
                print(f"✨ 最佳优化: {best_fulfillments[0]}")
                print(f"   节省: {best_fulfillments[1]:.1f}%")
            else:
                print(f"ℹ️ 无有效优化方案")

        print(f"\n{'='*70}")
        print("✅ 测试完成！")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
