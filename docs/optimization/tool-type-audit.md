# MCP EasyStore 工具类型检查报告

**生成日期**: 2026-05-08  
**项目**: mcp-easystore  
**总工具数**: 57 个读取工具 + 55 个写入工具（可选）= 最多 112 个

---

## 1. 工具分类概览

### 读取工具（57 个 - 默认启用）
| 类别 | 文件 | 工具数 | 用途 |
|------|------|-------|------|
| 分析 | `analytics_tools.py` | 9 | 商店统计、订单摘要、收入、库存、客户成长 |
| 订单 | `order_tools.py` | 8 | 订单列表、出货记录、交易、结账流程 |
| 商品 | `product_tools.py` | 10 | 商品、规格、图片、分类、Collects |
| 客户 | `customer_tools.py` | 10 | 会员、地址、群组、自定属性 |
| 设置 | `settings_tools.py` | 13 | Webhooks、Curls、Metafields、地点、网关、自定属性 |
| Storefront | `storefront_tools.py` | 7 | 静态页面、导航、URL转向、代码片段、脚本标签 |

### 写入工具（55 个 - 需要 ENABLE_WRITE_TOOLS=true）
| 文件 | 工具数 | 状态 |
|------|-------|------|
| `tools/writes/order_writes.py` | ? | 条件启用 |
| `tools/writes/product_writes.py` | ? | 条件启用 |
| `tools/writes/customer_writes.py` | ? | 条件启用 |
| `tools/writes/storefront_writes.py` | ? | 条件启用 |
| `tools/writes/settings_writes.py` | ? | 条件启用 |

---

## 2. 工具定义模式

### 2.1 工具装饰器

所有工具使用 **FastMCP** 的 `@mcp.tool()` 装饰器注册：

```python
@mcp.tool(
    name="easystore_list_orders",
    annotations={
        "readOnlyHint": True,      # 标记是否为只读
        "destructiveHint": False   # 标记是否具有破坏性
    }
)
async def easystore_list_orders(params: ListOrdersInput) -> str:
    """工具文档字符串"""
    ...
```

### 2.2 参数定义 - Pydantic 模型

所有工具参数使用 **Pydantic BaseModel** 定义，统一配置：

```python
class ExampleInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,  # 自动去除字符串空格
        extra="forbid"              # 禁止额外字段
    )
    field_name: FieldType = Field(default=value, description="说明")
```

#### 常见参数类型：

| 类型 | 示例 | 验证规则 |
|------|------|---------|
| `int` | `page`, `limit`, `days` | `ge=1, le=250` 范围限制 |
| `str` | `order_id`, `product_id` | `min_length=1` |
| `Optional[str]` | `status`, `query`, `sort` | 可选，含说明文档 |
| `Optional[int]` | `since_id`, `customer_id` | 可选，用于分页游标 |
| `Optional[bool]` | `is_bundle`, `is_cancelled` | 三态过滤 |

---

## 3. 工具类型详细清单

### 3.1 Analytics Tools (9 个)

**模式**: 摘要查询、跨资源统计  
**返回**: JSON 字符串

```
✓ easystore_get_store_info()
  - 无参数
  - 返回: 商店信息

✓ easystore_get_order_summary(DateRangeInput)
  - 参数: date_from, date_to, days
  - 返回: 订单状态分布统计

✓ easystore_get_financial_status_summary(DateRangeInput)
  - 参数: 日期范围
  - 返回: 支付状态分布

✓ easystore_get_fulfillment_status_summary(DateRangeInput)
  - 参数: 日期范围
  - 返回: 出货状态分布

✓ easystore_get_product_inventory_summary()
  - 无参数
  - 返回: 库存概览（上架商品数、库存总和）

✓ easystore_get_revenue_summary(FinancialStatusInput)
  - 参数: 日期、支付状态
  - 返回: 期间营收统计

✓ easystore_get_customer_growth(CustomerGrowthInput)
  - 参数: 日期、limit
  - 返回: 新会员统计

✓ easystore_get_gateway_usage()
  - 无参数
  - 返回: 已启用支付方式列表

✓ easystore_get_webhook_health()
  - 无参数
  - 返回: Webhook 订阅健康检查
```

### 3.2 Order Tools (8 个)

**模式**: CRUD + 关联资源  
**参数**: 严格的 Pydantic 验证

```
✓ easystore_list_orders(ListOrdersInput)
  - 参数: 状态、财务状态、时间范围、分页
  - 注解: readOnlyHint=True, destructiveHint=False

✓ easystore_get_order(GetOrderInput)
  - 参数: order_id, fields(可选扩展字段)

✓ easystore_list_fulfillments(ListFulfillmentsInput)
  - 参数: order_id, status, tracking_number
  - 路径: /orders/:id/fulfillments

✓ easystore_get_fulfillment(GetFulfillmentInput)
  - 参数: order_id, fulfillment_id

✓ easystore_list_transactions(ListTransactionsInput)
  - 参数: order_id

✓ easystore_get_transaction(GetTransactionInput)
  - 参数: order_id, transaction_id

✓ easystore_list_checkouts(ListCheckoutsInput)
  - 参数: 分页、时间过滤、since_id

✓ easystore_get_checkout(GetCheckoutInput)
  - 参数: cart_token(UUID)
```

### 3.3 Product Tools (10 个)

**模式**: 商品及其关联资源的列表和详情

```
✓ easystore_list_products(ListProductsInput)
  - 参数: visibility, collection_ids, skus, ids, 时间范围
  
✓ easystore_get_product(GetProductInput)
  - 参数: product_id

✓ easystore_list_variants(ListVariantsInput)
  - 参数: product_id

✓ easystore_get_variant(GetVariantInput)
  - 参数: product_id, variant_id

✓ easystore_list_product_images(ListImagesInput)
  - 参数: product_id

✓ easystore_list_collections(ListCollectionsInput)
  - 参数: 分页、visibility、sort

✓ easystore_get_collection(GetCollectionInput)
  - 参数: collection_id

✓ easystore_list_collects(ListCollectsInput)
  - 参数: collection_id(可选), product_id(可选)

✓ easystore_get_collection_product_count(CollectionStatsInput)
  - 参数: collection_id(可选) - 查询各分类商品数

✓ easystore_count_collects()
  - 无参数 - Collect 关联总数
```

### 3.4 Customer Tools (10 个)

**模式**: 会员数据 + 关联资源（地址、群组、属性）

```
✓ easystore_list_customers(ListCustomersInput)
  - 参数: query, 时间范围, sort, fields

✓ easystore_search_customers(SearchCustomersInput)
  - 参数: email, phone, code - 精确查询

✓ easystore_get_customer(GetCustomerInput)
  - 参数: customer_id, fields(points/membership)

✓ easystore_get_customer_points(GetCustomerPointsInput)
  - 参数: customer_id

✓ easystore_get_customer_attribute(GetByIdInput)
  - 参数: attribute_id

✓ easystore_list_customer_attributes(PaginationInput)
  - 参数: 分页

✓ easystore_list_customer_addresses(ListAddressesInput)
  - 参数: customer_id, 分页

✓ easystore_get_customer_address(GetAddressInput)
  - 参数: customer_id, address_id

✓ easystore_list_groups()
  - 无参数

✓ easystore_list_group_customers(GetGroupInput)
  - 参数: group_id - 获取群组成员 ID 列表
```

### 3.5 Settings Tools (13 个)

**模式**: 商店配置和基础设施

```
✓ easystore_list_webhooks(PaginationInput)
✓ easystore_get_webhook(GetByIdInput)
✓ easystore_count_webhooks()

✓ easystore_list_curls(PaginationInput)
✓ easystore_get_curl(GetByIdInput)
✓ easystore_count_curls()

✓ easystore_list_metafields(ListMetafieldsInput)
  - 参数: namespace, key, value_type 过滤

✓ easystore_get_metafield(GetByIdInput)
✓ easystore_count_metafields()

✓ easystore_list_locations(ListLocationsInput)
✓ easystore_get_location(GetByIdInput)

✓ easystore_list_gateways()
  - 已启用支付方式

✓ easystore_list_es_gateways()
  - 平台所有支持的支付方式
```

### 3.6 Storefront Tools (7 个)

**模式**: Storefront 基础设施（EasyStore 特有）

```
✓ easystore_list_pages(ListPagesInput)
  - 参数: visibility, handle, title

✓ easystore_get_page(GetByIdInput)

✓ easystore_list_navigations(ListNavigationsInput)
  - 返回: 树状导航结构

✓ easystore_list_redirects(ListRedirectsInput)
  - 参数: path, target 过滤

✓ easystore_list_snippets(ListSnippetsInput)
  - 参数: field 位置过滤（global/body_start 等）

✓ easystore_list_script_tags(ListScriptTagsInput)
  - 参数: src URL 过滤
```

---

## 4. 底层类型系统

### 4.1 HTTP 请求类型

基于 `base_tool.py`：

```python
# GET 请求
async def api_get(path: str, params: Optional[dict] = None) -> dict | list | str

# 嵌套路径（/orders/:id/fulfillments）
async def api_get_nested(path: str, params: Optional[dict] = None) -> dict | str

# 自动翻页
async def fetch_all_pages(
    path: str, 
    resource_key: str,
    params: Optional[dict] = None,
    max_pages: int = 10
) -> list | str
```

### 4.2 错误处理类型

```python
def handle_api_error(e: Exception, context: str = "") -> str:
    # 返回友好的错误信息字符串
    # 处理: 401, 403, 404, 422, 429, TimeoutException, ConnectError
```

### 4.3 返回类型

**统一约定**: 所有工具返回 `str`（JSON 格式）

```python
def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
```

---

## 5. 注解类型约定

### 所有读取工具的注解

```python
annotations={
    "readOnlyHint": True,
    "destructiveHint": False
}
```

### 预期的写入工具注解

```python
annotations={
    "readOnlyHint": False,
    "destructiveHint": True  # 对于删除操作
}
```

---

## 6. 参数验证规则总结

| 规则 | 应用场景 | Pydantic 配置 |
|------|---------|-------------|
| 去除空格 | 所有 str 字段 | `str_strip_whitespace=True` |
| 禁止额外字段 | 所有模型 | `extra="forbid"` |
| 最小长度 | ID 字段 | `min_length=1` |
| 范围限制 | page, limit, days | `ge=1, le=250` |
| None 排除 | API 参数清理 | `.model_dump(exclude_none=True)` |

---

## 7. 工具命名规范

**模式**: `easystore_{action}_{resource}`

| 模式 | 示例 |
|------|------|
| `list_*` | `list_orders`, `list_customers` |
| `get_*` | `get_order`, `get_product` |
| `count_*` | `count_webhooks`, `count_collects` |
| `search_*` | `search_customers` (精确查询) |

**前缀**: 所有工具都以 `easystore_` 开头

---

## 8. 工具启用/禁用逻辑

### 环境变量控制

```python
# .env 或环境变量
EASYSTORE_SHOP_URL = "https://yourshop.easy.co"
EASYSTORE_ACCESS_TOKEN = "..."
ENABLE_WRITE_TOOLS = "true"  # 仅启用写入工具
```

### 条件注册逻辑

```python
# 读取工具: 始终加载 (57 个)
register_analytics_tools(mcp)
register_order_tools(mcp)
# ...

# 写入工具: 条件加载
if ENABLE_WRITE_TOOLS:
    register_order_writes(mcp)
    register_product_writes(mcp)
    # ...
```

---

## 9. 数据流类型

### 请求流

```
用户请求 (参数)
    ↓
Pydantic 验证 (ListOrdersInput)
    ↓
参数转换 (model_dump, 清理 None)
    ↓
api_get() 调用 (httpx)
    ↓
JSON 响应解析
    ↓
to_json() 格式化
    ↓
str 返回
```

### 错误流

```
HTTP 错误 / 异常
    ↓
handle_api_error()
    ↓
友好错误信息 (str)
    ↓
返回错误字符串
```

---

## 10. 关键设计决策

| 决策 | 原因 |
|------|------|
| 统一返回 `str` | MCP 协议要求，易于序列化 |
| Pydantic 模型 | 强类型验证，IDE 智能提示 |
| `.model_dump()` 清理 | 避免发送 None 参数到 API |
| `annotations` 标记 | 向 Claude 声明工具性质 |
| 环境变量控制写入 | 防止意外修改生产数据 |
| 异步 `async/await` | 支持并发请求 |

---

## 11. 潜在改进建议

### 类型安全
- [ ] 考虑使用 `TypedDict` 代替裸 dict 作为返回类型
- [ ] 为错误情况定义专门的 `ErrorResponse` 类

### 工具分组
- [ ] 根据功能域（Finance, Inventory, Customers）分组工具
- [ ] 为每组工具添加 `category` 或 `namespace` 元数据

### 参数重用
- [ ] `PaginationInput` 已被多次重用，可考虑更多公共基类
- [ ] 日期范围参数 `DateRangeInput` 也可进一步规范化

### 文档
- [ ] 在工具文档中添加返回示例
- [ ] 为常见的组合查询添加使用指南

---

## 总结

**工具架构特点**:
- ✅ 一致的参数验证（Pydantic）
- ✅ 统一的工具命名规范
- ✅ 清晰的读写权限分离
- ✅ 强大的错误处理
- ✅ 异步 I/O 支持
- ✅ 自动翻页机制

**类型系统完整性**: 9/10（缺少返回值类型的显式定义）
