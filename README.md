# mcp-easystore

EasyStore 電商平台的 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 伺服器。

讓 Claude 透過自然語言直接查詢 EasyStore 商店資料，無需手動導出報表。支援訂單、商品、顧客、營收、庫存、金流等 57+ 讀取工具。

## 功能概覽

- **訂單分析**：依狀態、付款、時間篩選，計算營收、出貨進度
- **顧客洞察**：顧客清單、積分查詢、**RFM 分群分析**
- **商品管理**：商品列表、庫存概況、分類統計
- **店務設定**：金流方式、Webhook 健康檢查、商店基本資訊
- **Token 優化**：所有工具針對最小化 token 消耗設計

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 並填入您的 EasyStore 設定：

```bash
cp .env.example .env
```

```env
EASYSTORE_SHOP_URL=https://your-shop.myeasystore.com
EASYSTORE_ACCESS_TOKEN=your_access_token
```

完整說明見 [docs/setup/env-variable-guide.md](docs/setup/env-variable-guide.md)。

### 3. 設定 Claude Desktop

在 Claude Desktop 的 MCP 設定中加入：

```json
{
  "mcpServers": {
    "easystore": {
      "command": "python",
      "args": ["/path/to/mcp-easystore/mcp_server.py"],
      "env": {
        "EASYSTORE_SHOP_URL": "https://your-shop.myeasystore.com",
        "EASYSTORE_ACCESS_TOKEN": "your_access_token"
      }
    }
  }
}
```

完整設定路徑說明見 [docs/setup/](docs/setup/)。

## 工具一覽

### 分析工具（analytics_tools）— 10 個

| 工具 | 說明 |
|------|------|
| `easystore_get_store_info` | 商店基本資訊（幣別、時區、方案） |
| `easystore_get_order_summary` | 期間訂單量統計（依狀態分組） |
| `easystore_get_revenue_summary` | 營收加總（付款訂單） |
| `easystore_get_fulfillment_status_summary` | 出貨狀態分佈 |
| `easystore_get_financial_status_summary` | 付款狀態分佈 |
| `easystore_get_customer_growth` | 新會員成長統計 |
| `easystore_get_product_inventory_summary` | 商品庫存概況 |
| `easystore_get_collection_product_count` | 各分類商品數量 |
| `easystore_get_gateway_usage` | 已啟用金流方式 |
| `easystore_get_rfm_orders` | RFM 分析專用訂單資料（85% token 節省） |

### 訂單工具（order_tools）— 8 個

`list_orders` / `get_order` / `list_fulfillments` / `get_fulfillment` / `list_transactions` / `get_transaction` / `list_checkouts` / `get_checkout`

### 商品工具（product_tools）— 10 個

`list_products` / `get_product` / `list_variants` / `get_variant` / `list_product_images` / `list_collections` / `get_collection` / `list_collects` / `get_collects_count` / `get_collection_product_count`

### 顧客工具（customer_tools）— 10 個

`list_customers` / `search_customers` / `get_customer` / `get_customer_points` / `list_customer_addresses` / `get_customer_address` / `list_customer_attributes` / `get_customer_attribute` / `list_groups` / `get_group` / `list_group_customers`

### 設定工具（settings_tools）— 13 個

金流、Webhook、Metafield 相關讀取工具。

### 店面工具（storefront_tools）— 7 個

頁面、導覽列、Script Tag、Snippet、Redirect 等讀取工具。

## RFM 顧客分群

使用 `easystore_get_rfm_orders` 搭配分步驟查詢，對顧客進行 Recency / Frequency / Monetary 分群：

```
1. easystore_get_order_summary(days=180)   → 確認訂單規模
2. easystore_get_rfm_orders(days=180, page=N)  → 分頁取回最小欄位
3. Claude 端彙總 → 分群輸出
```

詳見 [docs/optimization/rfm-analysis-guide.md](docs/optimization/rfm-analysis-guide.md)。

## 寫入工具（選用）

預設不載入，需設定 `ENABLE_WRITE_TOOLS=true` 才啟用，避免誤操作。

```env
ENABLE_WRITE_TOOLS=true
```

## 開發

```bash
# 環境檢查
python scripts/check_env.py

# API 連線測試
python scripts/auth/test_connection.py

# 執行測試
python -m pytest tests/
```

專案結構詳見 [docs/architecture/project-structure.md](docs/architecture/project-structure.md)。

## 文件

| 目錄 | 內容 |
|------|------|
| `docs/setup/` | 環境變數設定、Claude Desktop 設定 |
| `docs/api-reference/` | EasyStore API 端點清單 |
| `docs/architecture/` | 專案結構說明 |
| `docs/optimization/` | Token 優化指南、RFM 分析指南 |
| `docs/archive/` | 已完成優化的驗證報告 |
