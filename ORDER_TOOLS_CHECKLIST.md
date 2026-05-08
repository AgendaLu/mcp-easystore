# Order/Transaction/Fulfillment 工具 - 快速优化清单

---

## 📋 工具清单（8 个）

### ✅ 列表查询工具（容易优化）

```
🔴 P1  easystore_list_orders
       ├─ 现状: 支持 fields 参数，但文档不清楚
       ├─ 问题: 用户不知道如何使用 fields 减少数据
       ├─ 优化: 更新文档 + 提供示例
       └─ 预期节省: 60-70%

🔴 P1  easystore_list_checkouts
       ├─ 现状: 不支持 fields 参数(?)
       ├─ 问题: 可能返回 500+ 条记录，包含完整 line_items
       ├─ 优化: 验证 API 支持，添加 fields 参数
       └─ 预期节省: 50-60%

🔴 P1  easystore_list_fulfillments
       ├─ 现状: 不支持 fields 参数(?)
       ├─ 问题: 无法控制响应字段
       ├─ 优化: 验证 API，添加 fields 参数
       └─ 预期节省: 30-40%

🟨 P2  easystore_list_transactions
       ├─ 现状: 固定返回该订单的全部交易
       ├─ 问题: 无法优化（通常只有 1-3 条）
       ├─ 优化: 文档说明 + 使用指南
       └─ 预期节省: 0% (固定成本)
```

### ✅ 详情查询工具（难度高）

```
🟨 P2  easystore_get_order
       ├─ 现状: 支持 fields 参数
       ├─ 问题: 默认返回行为不清楚
       ├─ 优化: 改进文档，说明默认字段
       └─ 预期节省: 20-30%

🟢 P3  easystore_get_fulfillment
       ├─ 优化潜力: 无 (单笔，数据小)
       └─ 建议: 无需改动

🟢 P3  easystore_get_transaction
       ├─ 优化潜力: 无 (单笔，数据小)
       └─ 建议: 无需改动

🟢 P3  easystore_get_checkout
       ├─ 优化潜力: 低
       └─ 建议: 可跳过
```

---

## 🔍 需要检查的 5 个关键问题

### ❓ Q1: API 是否支持 fields 参数？

**检查对象**:
- [ ] `/api/3.0/checkouts.json?fields=...` 是否有效？
- [ ] `/api/3.0/orders/:id/fulfillments.json?fields=...` 是否有效？

**检查方法**:
```bash
# 测试 checkouts 是否支持 fields
curl -H "EasyStore-Access-Token: YOUR_TOKEN" \
  "https://yourshop.easystore.co/api/3.0/checkouts.json?limit=1&fields="

# 查看返回的字段数量
```

**文档参考**: `/EasyStore_API_Endpoint_Inventory.md`

---

### ❓ Q2: 列表查询的默认字段是什么？

**检查对象**: 
- `easystore_list_orders` - 不指定 fields 时返回什么？
- `easystore_list_checkouts` - 包括 line_items 吗？

**检查方法**:
```python
# 实际调用，查看响应
import json
data = easystore_list_orders(page=1, limit=1, fields=None)
resp = json.loads(data)
print("返回的顶级字段:", resp.keys())
if resp.get('orders'):
    print("订单字段:", resp['orders'][0].keys())
    # 查找大字段（items, customer, addresses 等）
```

**影响**: 决定了文档中应该如何建议

---

### ❓ Q3: 实际数据大小是多少？

**检查对象**:
- `list_orders` 包含 items 时的大小
- `list_checkouts` 的 line_items 大小
- `list_fulfillments` 的完整响应大小

**检查方法**:
```python
# 采样数据大小
import json

# 获取一个实际的订单响应
data = easystore_list_orders(page=1, limit=1, fields="items,addresses")
resp = json.loads(data)

# 计算大小
json_str = json.dumps(resp, ensure_ascii=False)
print(f"响应大小: {len(json_str)} 字符")
print(f"Token 估算: {len(json_str) / 4:.0f}")

# 只获取基础字段
data2 = easystore_list_orders(page=1, limit=1, fields="")
resp2 = json.loads(data2)
json_str2 = json.dumps(resp2, ensure_ascii=False)
print(f"优化后: {len(json_str2)} 字符")
print(f"节省: {(1 - len(json_str2)/len(json_str)) * 100:.1f}%")
```

**影响**: 决定优化是否值得

---

### ❓ Q4: 典型查询的数据量是多少？

**检查对象**:
- 30 天的 checkouts 通常有多少条？
- 30 天的 orders 通常有多少条？

**检查方法**:
```python
# 查询 30 天的结账数量
from datetime import datetime, timedelta
today = datetime.now()
thirty_days_ago = today - timedelta(days=30)

data = easystore_list_checkouts(
    created_at_min=thirty_days_ago.isoformat(),
    created_at_max=today.isoformat(),
    limit=1  # 只要 total_count
)
resp = json.loads(data)
print(f"30 天内的结账数: {resp.get('total_count', 0)}")
# 如果是 1000+，则需要 20+ 页
```

**影响**: 决定是否需要添加分页性能警告

---

### ❓ Q5: 用户通常需要什么字段？

**检查对象**:
- 哪些字段最常被使用？
- 哪些字段最容易被误用？

**检查方法**:
```
根据使用场景：
- 日常订单管理: 需要 items, addresses, customer
- 营收分析: 仅需 total_price, currency_code
- 棄單分析: 仅需 cart_token, created_at, item 数量
- 出货管理: 需要 fulfillments, status
- 对账: 仅需 id, total_price, transaction 状态
```

**影响**: 决定文档中应该提供的示例

---

## 📊 检查结果汇总表

检查完上述 5 个问题后，填写此表：

```
问题                    答案          优化可能性    优先级
────────────────────────────────────────────────────────
checkouts 支持 fields?  [ ] 是 / [ ] 否   ______    [ ]P1/P2/P3
fulfillments支持fields? [ ] 是 / [ ] 否   ______    [ ]P1/P2/P3
list_orders 默认包含?   ________         ______    [ ]P1/P2/P3
list_checkouts大小      ______字符/页    ______    [ ]P1/P2/P3
30天checkouts数量       ______ 条        ______    [ ]P1/P2/P3
```

---

## 🎯 按优先级采取行动

### 🔴 优先级 P1（立即改进）

#### Action 1.1: 更新 `easystore_list_orders` 文档
- 说明默认返回的字段
- 添加 fields="" 的使用示例
- 警告 items 字段的大小风险

**代码位置**: `tools/order_tools.py` L83-102

**预计工作量**: 15 分钟

#### Action 1.2: 验证 checkouts 和 fulfillments 的 fields 支持
- 调用 API 测试
- 根据结果添加参数或文档说明

**预计工作量**: 30 分钟

---

### 🟨 优先级 P2（后续改进）

#### Action 2.1: 如果支持，为 `list_checkouts` 添加 fields 参数
```python
class ListCheckoutsInput(BaseModel):
    # 现有参数...
    fields: Optional[str] = Field(None, description="可选字段: items,customer")
```

**预计工作量**: 30 分钟

#### Action 2.2: 为 `list_fulfillments` 添加 fields 参数（如支持）
**预计工作量**: 30 分钟

---

### 🟢 优先级 P3（可选）

#### Action 3.1: 添加使用指南到 README
- 列出各工具的 Token 成本
- 最佳实践示例

**预计工作量**: 45 分钟

---

## 📈 预期改进效果

| 场景 | 当前成本 | 优化后 | 节省 |
|------|---------|-------|------|
| 日常订单列表（50 条）| ~400 | ~100 | 75% |
| 棄單分析（1000 条结账）| ~50,000 | ~10,000 | 80% |
| 出货批量查询（100 条）| ~5,000 | ~1,000 | 80% |

---

## 📚 相关文档

- [ORDER_TOOLS_OPTIMIZATION_ANALYSIS.md](ORDER_TOOLS_OPTIMIZATION_ANALYSIS.md) - 详细分析
- [REVENUE_SUMMARY_OPTIMIZATION.md](REVENUE_SUMMARY_OPTIMIZATION.md) - 方案对比
- [OPTIMIZATION_PLAN_A_IMPLEMENTATION.md](OPTIMIZATION_PLAN_A_IMPLEMENTATION.md) - 实施报告
- [MCP_TOOL_TYPE_AUDIT.md](MCP_TOOL_TYPE_AUDIT.md) - 工具类型审计

---

## ✍️ 检查记录

| 日期 | 检查项 | 状态 | 备注 |
|------|--------|------|------|
| | Q1: fields 支持 | ⬜ | |
| | Q2: 默认字段 | ⬜ | |
| | Q3: 数据大小 | ⬜ | |
| | Q4: 典型数量 | ⬜ | |
| | Q5: 使用场景 | ⬜ | |

---

**创建日期**: 2026-05-08  
**下一步**: 逐项检查上述 5 个问题
