# mcp-easystore — 專案結構

> **更新日期**：2026-05-08
> **內容**：上半部為當前實際結構，下半部為各工具的端點對照表（規劃／實作參考）。

---

## 當前專案結構

```
mcp-easystore/
├── README.md
├── LICENSE
├── SKILL.md                         # Claude skill 定義（easystore-analyst）
├── CLAUDE.md                        # Claude Code session 進入點說明
├── mcp_server.py                    # MCP 伺服器入口（stdio JSON-RPC 2.0）
├── requirements.txt
├── .env / .env.example / .gitignore
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # 環境變數載入、API 設定
│
├── tools/                           # MCP 工具實作（讀取工具皆已上線）
│   ├── __init__.py
│   ├── base_tool.py                 # 共用 HTTP client
│   ├── tool_registry.py             # 統一註冊（讀寫分離控制）
│   ├── analytics_tools.py           # 數據分析（9 個）
│   ├── order_tools.py               # 訂單（8 個）
│   ├── product_tools.py             # 商品（10 個）
│   ├── customer_tools.py            # 客戶（10 個）
│   ├── settings_tools.py            # 商店設定（13 個）
│   └── storefront_tools.py          # Storefront 建設（7 個）
│   # 寫入工具（tools/writes/）規劃中，預設不載入；ENABLE_WRITE_TOOLS=true 才啟用
│
├── scripts/                         # 一次性腳本：連線測試、優化驗證
│   ├── start_mcp.sh
│   ├── check_env.py
│   ├── auth/test_connection.py
│   ├── test_fields_optimization.py
│   ├── test_revenue_optimization.py
│   └── verify_fields_support.py
│
├── tests/
│   └── test_orders.py
│
└── docs/
    ├── setup/                       # 環境變數、Cowork 設定
    ├── api-reference/               # EasyStore / Shopline API 端點清單
    ├── architecture/                # 本檔
    ├── optimization/                # 規劃中的優化分析、checklist、實施指南
    └── archive/                     # 已完成的測試結果與實施報告
```

### 工具總數（讀取）

| 模組 | 數量 |
|------|-----|
| analytics | 9 |
| orders | 8 |
| products | 10 |
| customers | 10 |
| settings | 13 |
| storefront | 7 |
| **合計** | **57** |

寫入工具規劃約 55 個（`tools/writes/`），目前未實作；`tool_registry.py` 已預留載入點，需 `ENABLE_WRITE_TOOLS=true`。

---

## 各檔案的工具清單規劃

### `tools/analytics_tools.py` ── 數據分析讀取（~12 個）

> 將跨資源的摘要型查詢整合成分析工具，是 MCP 場景的高頻使用場景。

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_get_store_info` | `GET /store.json` | 取得商店基本資訊（名稱、幣別、時區） |
| `easystore_get_order_summary` | `GET /orders.json` + params | 訂單量統計（依狀態、時間區間） |
| `easystore_get_revenue_summary` | `GET /orders.json` + params | 營收統計（依時間聚合） |
| `easystore_get_product_inventory_summary` | `GET /products.json` | 商品庫存概況 |
| `easystore_get_customer_growth` | `GET /customers.json` + params | 新會員成長統計 |
| `easystore_get_fulfillment_status_summary` | `GET /orders.json?fields=fulfillments` | 出貨狀態分佈 |
| `easystore_get_financial_status_summary` | `GET /orders.json?financial_status=` | 付款狀態分佈 |
| `easystore_get_top_products` | `GET /orders.json` → 聚合 | 熱銷商品排行（client-side 聚合） |
| `easystore_get_gateway_usage` | `GET /gateways.json` | 金流方式使用概況 |
| `easystore_get_collection_product_count` | `GET /collects.json?collection_id=` | 各分類商品數量 |
| `easystore_get_customer_order_stats` | `GET /customers/:id.json` + orders | 單一會員消費統計 |
| `easystore_get_webhook_health` | `GET /webhooks.json` | Webhook 設定健康檢查 |

---

### `tools/order_tools.py` ── 訂單讀取（~10 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_list_orders` | `GET /orders.json` | 訂單列表（分頁、多條件篩選） |
| `easystore_get_order` | `GET /orders/:order_id.json` | 單筆訂單完整資料 |
| `easystore_list_fulfillments` | `GET /orders/:id/fulfillments.json` | 訂單出貨紀錄 |
| `easystore_get_fulfillment` | `GET /orders/:id/fulfillments/:id.json` | 單筆出貨詳情 |
| `easystore_list_transactions` | `GET /orders/:id/transactions.json` | 訂單付款交易紀錄 |
| `easystore_get_transaction` | `GET /orders/:id/transactions/:id.json` | 單筆交易詳情 |
| `easystore_list_checkouts` | `GET /checkouts.json` | 結帳（購物車）列表 |
| `easystore_get_checkout` | `GET /checkouts/:cart_token.json` | 單筆結帳詳情 |
| `easystore_filter_orders_by_status` | `GET /orders.json?financial_status=&fulfillment_status=` | 依付款 / 出貨狀態篩選（常用分析工具） |
| `easystore_filter_orders_by_date` | `GET /orders.json?created_at_min=&created_at_max=` | 依時間區間篩選訂單 |

---

### `tools/product_tools.py` ── 商品讀取（~12 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_list_products` | `GET /products.json` | 商品列表（含庫存、狀態篩選） |
| `easystore_get_product` | `GET /products/:id.json` | 單筆商品完整資料 |
| `easystore_list_variants` | `GET /products/:id/variants.json` | 商品規格列表 |
| `easystore_get_variant` | `GET /products/:id/variants/:id.json` | 單筆規格詳情 |
| `easystore_list_product_images` | `GET /products/:id/images.json` | 商品圖片列表 |
| `easystore_list_collections` | `GET /collections.json` | 分類列表 |
| `easystore_get_collection` | `GET /collections/:id.json` | 單筆分類詳情 |
| `easystore_list_collects` | `GET /collects.json` | Product↔Collection 關聯列表 |
| `easystore_get_collects_count` | `GET /collects/count.json` | 關聯總數 |
| `easystore_filter_products_by_collection` | `GET /products.json?collection_ids=` | 依分類篩選商品 |
| `easystore_filter_products_by_sku` | `GET /products.json?skus=` | 依 SKU 查詢商品 |
| `easystore_filter_products_by_visibility` | `GET /products.json?visibility=` | 依上架狀態篩選 |

---

### `tools/customer_tools.py` ── 客戶讀取（~10 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_list_customers` | `GET /customers.json` | 會員列表 |
| `easystore_get_customer` | `GET /customers/:id.json` | 單筆會員資料（含 points / membership） |
| `easystore_search_customers` | `GET /customers/search.json` | 依 email / phone / code 搜尋 |
| `easystore_get_customer_points` | `GET /customers/:id/points.json` | 會員點數餘額與設定 |
| `easystore_list_customer_addresses` | `GET /customers/:id/addresses.json` | 會員地址列表 |
| `easystore_get_customer_address` | `GET /customers/:id/addresses/:id.json` | 單筆地址詳情 |
| `easystore_list_groups` | `GET /groups.json` | 會員群組列表 |
| `easystore_get_group` | `GET /groups/:id.json` | 單筆群組詳情 |
| `easystore_list_group_customers` | `GET /groups/:id/customers.json` | 群組成員列表 |
| `easystore_list_customer_attributes` | `GET /customer_attributes.json` | 自訂屬性 schema 列表 |

---

### `tools/settings_tools.py` ── 商店設定讀取（~14 個）

> 涵蓋 Webhooks、Curls、Metafields、Snippets、Script Tags、Locations、Customer Custom Attributes。

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_list_webhooks` | `GET /webhooks.json` | Webhook 訂閱列表 |
| `easystore_get_webhook` | `GET /webhooks/:id.json` | 單筆 Webhook |
| `easystore_count_webhooks` | `GET /webhooks/count.json` | Webhook 總數 |
| `easystore_list_curls` | `GET /curls.json` | Logistic callback URL 列表 |
| `easystore_get_curl` | `GET /curls/:id.json` | 單筆 curl 設定 |
| `easystore_count_curls` | `GET /curls/count.json` | Curl 總數 |
| `easystore_list_metafields` | `GET /metafields.json` | Metafield 列表（可依 namespace 篩選） |
| `easystore_get_metafield` | `GET /metafields/:id.json` | 單筆 metafield |
| `easystore_count_metafields` | `GET /metafields/count.json` | Metafield 總數 |
| `easystore_list_locations` | `GET /locations.json` | 門市 / 自取點列表 |
| `easystore_get_location` | `GET /locations/:id.json` | 單筆門市詳情 |
| `easystore_list_gateways` | `GET /gateways.json` | 商店已啟用金流列表 |
| `easystore_list_es_gateways` | `GET /es_gateways.json` | EasyStore 全平台支援金流列表 |
| `easystore_get_customer_attribute` | `GET /customer_attributes/:id.json` | 單筆自訂屬性 |

---

### `tools/storefront_tools.py` ── Storefront 建設讀取（~8 個）

> EasyStore 獨有的 Storefront 基礎建設層，Shopline 無對應。

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_list_pages` | `GET /pages.json` | 靜態頁面列表 |
| `easystore_get_page` | `GET /pages/:id.json` | 單筆頁面詳情 |
| `easystore_list_navigations` | `GET /navigations.json` | 導覽選單列表 |
| `easystore_get_navigation` | `GET /navigations/:id.json` | 單筆選單項目 |
| `easystore_count_navigations` | `GET /navigations/count.json` | 選單項目總數 |
| `easystore_list_redirects` | `GET /redirects.json` | URL 轉址規則列表 |
| `easystore_list_snippets` | `GET /snippets.json` | HTML/Liquid 片段列表 |
| `easystore_list_script_tags` | `GET /script_tags.json` | 外部 JS 注入列表 |

---

### `tools/writes/order_writes.py` ── 訂單寫入（~8 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_create_order` | `POST /orders.json` | 建立訂單 |
| `easystore_update_order` | `PUT /orders/:id.json` | 更新訂單 |
| `easystore_delete_order` | `DELETE /orders/:id.json` | 刪除訂單 |
| `easystore_cancel_order` | `POST /orders/:id/cancel.json` | 取消訂單 |
| `easystore_refund_order` | `POST /orders/:id/refund.json` | 退款 |
| `easystore_cancel_refund` | `PUT /orders/:id/cancel_refund/:refund_id/cancel.json` | 取消退款 |
| `easystore_create_fulfillment` | `POST /orders/:id/fulfillments.json` | 建立出貨紀錄 |
| `easystore_update_fulfillment` | `PUT /orders/:id/fulfillments/:id.json` | 更新出貨狀態 |

---

### `tools/writes/product_writes.py` ── 商品寫入（~14 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_create_product` | `POST /products.json` | 建立商品 |
| `easystore_update_product` | `PUT /products/:id.json` | 更新商品 |
| `easystore_delete_product` | `DELETE /products/:id.json` | 刪除商品 |
| `easystore_update_variants` | `PUT /products/:id/variants.json` | 批次更新規格 |
| `easystore_create_options` | `POST /products/:id/options.json` | 新增 option type |
| `easystore_update_options` | `PUT /products/:id/options.json` | 更新 options |
| `easystore_delete_options` | `DELETE /products/:id/options.json` | 刪除 option type 或 value |
| `easystore_rename_option_type` | `PUT /products/:id/option_type.json` | 重命名 option type |
| `easystore_rename_option_value` | `PUT /products/:id/option_value.json` | 重命名 option value |
| `easystore_add_product_images` | `POST /products/:id/images.json` | 新增商品圖片 |
| `easystore_delete_product_images` | `DELETE /products/:id/images.json` | 刪除商品圖片 |
| `easystore_create_collection` | `POST /collections.json` | 建立分類 |
| `easystore_update_collection` | `PUT /collections/:id.json` | 更新分類 |
| `easystore_delete_collection` | `DELETE /collections/:id.json` | 刪除分類 |

---

### `tools/writes/customer_writes.py` ── 客戶寫入（~12 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_create_customer` | `POST /customers.json` | 建立會員 |
| `easystore_update_customer` | `PUT /customers/:id.json` | 更新會員資料 |
| `easystore_delete_customer` | `DELETE /customers/:id.json` | 刪除會員 |
| `easystore_adjust_customer_point` | `PUT /customers/:id/point/adjust.json` | 調整會員點數 |
| `easystore_set_customer_credit` | `PUT /customers/:id/credits/set.json` | 設定儲值金（絕對值） |
| `easystore_adjust_customer_credit` | `PUT /customers/:id/credits/adjust.json` | 調整儲值金（相對值） |
| `easystore_create_customer_address` | `POST /customers/:id/addresses.json` | 新增地址 |
| `easystore_update_customer_address` | `PUT /customers/:id/addresses/:id.json` | 更新地址 |
| `easystore_delete_customer_address` | `DELETE /customers/:id/addresses/:id.json` | 刪除地址 |
| `easystore_set_primary_address` | `PUT /customers/:id/addresses/:id/default.json` | 設為主要地址 |
| `easystore_create_group` | `POST /groups.json` | 建立會員群組 |
| `easystore_manage_group_customers` | `POST/PUT/DELETE /groups/:id/customers.json` | 管理群組成員 |

---

### `tools/writes/storefront_writes.py` ── Storefront 寫入（~12 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_create_page` | `POST /pages.json` | 建立靜態頁面 |
| `easystore_update_page` | `PUT /pages/:id.json` | 更新頁面 |
| `easystore_delete_page` | `DELETE /pages/:id.json` | 刪除頁面 |
| `easystore_create_navigation` | `POST /navigations.json` | 建立導覽選單項目 |
| `easystore_update_navigation` | `PUT /navigations/:id.json` | 更新選單項目 |
| `easystore_delete_navigation` | `DELETE /navigations/:id.json` | 刪除選單項目 |
| `easystore_create_redirect` | `POST /redirects.json` | 建立 URL 轉址 |
| `easystore_update_redirect` | `PUT /redirects/:id.json` | 更新轉址規則 |
| `easystore_delete_redirect` | `DELETE /redirects/:id.json` | 刪除轉址規則 |
| `easystore_create_snippet` | `POST /snippets.json` | 建立 HTML/Liquid 片段 |
| `easystore_update_snippet` | `PUT /snippets/:id.json` | 更新片段 |
| `easystore_create_script_tag` | `POST /script_tags.json` | 新增外部 JS |

---

### `tools/writes/settings_writes.py` ── 設定寫入（~9 個）

| 工具名稱 | 對應 Endpoint | 說明 |
|----------|--------------|------|
| `easystore_create_webhook` | `POST /webhooks.json` | 建立 Webhook 訂閱 |
| `easystore_update_webhook` | `PUT /webhooks/:id.json` | 更新 Webhook URL |
| `easystore_delete_webhook` | `DELETE /webhooks/:id.json` | 刪除 Webhook |
| `easystore_create_curl` | `POST /curls.json` | 建立 Logistic callback |
| `easystore_update_curl` | `PUT /curls/:id.json` | 更新 callback URL |
| `easystore_delete_curl` | `DELETE /curls/:id.json` | 刪除 callback |
| `easystore_create_metafield` | `POST /metafields.json` | 建立 metafield |
| `easystore_update_metafield` | `PUT /metafields/:id.json` | 更新 metafield |
| `easystore_delete_metafield` | `DELETE /metafields/:id.json` | 刪除 metafield |

---

## 設計差異說明（vs mcp-shopline）

### 新增的檔案

| 新增 | 原因 |
|------|------|
| `storefront_tools.py` | EasyStore 獨有的 Storefront 建設層（Pages / Nav / Redirects / Snippets / Script Tags），Shopline 無此域，需獨立檔案 |
| `checkout_tools.py` | 合併入 `order_tools.py` 的備選，若 Checkout 使用頻繁可獨立出來 |
| `writes/storefront_writes.py` | 對應讀取層，管理 Storefront 資源的寫入 |

### 移除的檔案（Shopline 有但 EasyStore 無 API）

| 移除 | 原因 |
|------|------|
| `writes/promotion_writes.py` | EasyStore 無促銷 Public API |
| `writes/return_writes.py` | EasyStore 無退貨單 API |
| `writes/conversation_writes.py` | EasyStore 無客服對話 API |
| `writes/review_writes.py` | EasyStore 無商品評論 API |
| `writes/gift_writes.py` | EasyStore 無贈品 API |
| `writes/purchase_writes.py` | EasyStore 無採購單 API |
| `writes/media_writes.py` | EasyStore 無獨立媒體上傳 API |
| `writes/delivery_writes.py` | EasyStore 以 Fulfillments 替代，合入 `order_writes.py` |
| `extended_tools.py` | Shopline 特有（order labels / tags / action-logs），EasyStore 無對應 |

### 結構性調整

| 調整 | 說明 |
|------|------|
| `analytics_tools.py` 職責擴大 | Shopline 版只做 analytics；EasyStore 版同時包含 `store.json` 讀取和 gateway 資訊，因為這些都是分析的輸入 |
| `settings_tools.py` 範圍更廣 | 涵蓋 Webhooks + Curls + Metafields + Locations + Customer Custom Attrs，EasyStore 把這些都視為「商店設定」層 |
| 無 `category_tools.py` | Shopline 將 Category 和 Promotions 合檔；EasyStore 的 Collections / Collects 合入 `product_tools.py`（因為分類操作通常伴隨商品管理） |

---

## 工具統計

| 檔案 | 工具數 | 類型 |
|------|:------:|------|
| `analytics_tools.py` | ~12 | READ |
| `order_tools.py` | ~10 | READ |
| `product_tools.py` | ~12 | READ |
| `customer_tools.py` | ~10 | READ |
| `settings_tools.py` | ~14 | READ |
| `storefront_tools.py` | ~8 | READ |
| `checkout_tools.py` | ~4 | READ |
| `writes/order_writes.py` | ~8 | WRITE |
| `writes/product_writes.py` | ~14 | WRITE |
| `writes/customer_writes.py` | ~12 | WRITE |
| `writes/storefront_writes.py` | ~12 | WRITE |
| `writes/settings_writes.py` | ~9 | WRITE |
| **合計** | **~125** | |

> [!NOTE]
> Read tools：~70 個，Write tools：~55 個。
> 寫入工具預設不載入，需在 `.env` 設定 `ENABLE_WRITE_TOOLS=true` 並重啟伺服器才啟用，避免 Claude 在分析任務中意外觸發寫入操作。

---

## 關鍵設計決策

### 1. `base_tool.py` 需處理的 EasyStore 特殊行為

```python
# EasyStore 所有路徑都有 .json suffix
BASE_URL = f"https://{shop}/api/3.0"
url = f"{BASE_URL}/{resource}.json"

# Auth header（非 Bearer Token）
headers = {"EasyStore-Access-Token": access_token}

# 所有成功回應均為 200 OK（包含 DELETE）
# Rate limit headers
# X-RateLimit-Remaining
# X-RateLimit-Limit

# count endpoint 特性（部分資源有獨立 /count.json）
# Webhooks、Metafields、Snippets、Script Tags、Navigations、Collects、Curls
```

### 2. 已知 API 文件異常（需在 base_tool 中補償）

> [!WARNING]
> 以下兩個路徑在 Postman collection 中缺少 `/api` 前綴，實作時需確認實際行為：
> - `GET /3.0/customers/:customer_id.json`（應為 `/api/3.0/customers/:id.json`）
> - `GET /3.0/customers/:customer_id_or_coode/points.json`（path variable 拼字錯誤）

### 3. 無 `search` 端點的替代方案

> [!NOTE]
> EasyStore 無獨立搜尋端點（不像 Shopline 有 `/orders/search`、`/products/search`）。所有搜尋邏輯透過 query params 實現：
> - 訂單搜尋 → `GET /orders.json?financial_status=&customer_id=`
> - 商品搜尋 → `GET /products.json?skus=&collection_ids=`
> - 客戶搜尋 → `GET /customers/search.json?email=&phone=&code=`（此為例外，有獨立 search endpoint）
>
> MCP tool description 需明確說明可用的篩選 params，讓 Claude 能正確組合條件。
