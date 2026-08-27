# mcp-easystore

EasyStore 電商平台的 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 伺服器。

讓 Claude 透過自然語言直接查詢並操作 EasyStore 商店資料。支援 **59 個讀取工具** + **41 個寫入工具**（選用），涵蓋訂單、商品、顧客、營收、庫存、金流等全域操作。

## 功能概覽

- **訂單管理**：查詢、取消、退款、建立出貨紀錄
- **顧客分群**：RFM 分析 → 自動分群 → 批次更新群組（讀寫閉環）
- **商品操作**：查詢庫存、批次更新規格價格、管理分類
- **店務設定**：金流方式、Webhook 健康檢查、商店基本資訊
- **前台內容**：頁面、導覽、轉址規則管理
- **Token 優化**：所有工具針對最小化 token 消耗設計

## 快速開始

不需要 clone、不需要裝 Python、不需要建虛擬環境。

### 1. 安裝 uv（只做一次）

```bash
brew install uv
```

或 `curl -LsSf https://astral.sh/uv/install.sh | sh`。uv 是單一執行檔，連 Python runtime 都會自己準備。

### 2. 取得 API 權杖

EasyStore 後台 → **安裝擴充** → **更多** → **客製擴充** → 命名 → 設定存取範疇 → 儲存後顯示 **API 存取權杖**。

要用寫入工具的話，存取範疇記得勾寫入權限（[官方說明](https://support.easystore.co/zh-tw/article/easystore-api-1amargb/)）。

### 3. 註冊 MCP server

看你用哪個 client，二選一：

**Claude Code** — 用指令，不必手改 JSON（會寫進 `~/.claude.json`）：

```bash
claude mcp add easystore --scope local \
  -e EASYSTORE_SHOP_URL=https://yourshop.easystore.co \
  -e EASYSTORE_ACCESS_TOKEN=你的權杖 \
  -e ENABLE_WRITE_TOOLS=false \
  -- uvx --from git+https://github.com/AgendaLu/mcp-easystore mcp-easystore
```

**Claude Desktop** — 沒有對應的 CLI 指令，手動編輯設定檔：

```
~/Library/Application Support/Claude/claude_desktop_config.json    # macOS
%APPDATA%\Claude\claude_desktop_config.json                        # Windows
```

把 `easystore` 這一項**併進**既有的 `mcpServers`（檔案裡通常還有 `preferences` 之類的其他設定，別整份覆蓋掉）：

```json
{
  "mcpServers": {
    "easystore": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/AgendaLu/mcp-easystore", "mcp-easystore"],
      "env": {
        "EASYSTORE_SHOP_URL": "https://yourshop.easystore.co",
        "EASYSTORE_ACCESS_TOKEN": "你的權杖",
        "ENABLE_WRITE_TOOLS": "false"
      }
    }
  }
}
```

Desktop 從 Dock／Finder 啟動時不會載入 shell 的 `PATH`，`"command": "uvx"` 多半會連不上——改成絕對路徑（`which uvx` 查，Homebrew 通常是 `/opt/homebrew/bin/uvx`）。改完要 Cmd+Q 完全結束再開，關視窗不算。

第一次啟動時 uvx 會自動下載 Python 與依賴（約 30 秒），之後走快取。更新就是重啟——uvx 會抓 repo 最新版。

### 4. 確認裝好了

Claude Code 跑 `claude mcp list`，看到 `easystore ✔ Connected` 就成功。Claude Desktop 則是重啟後點聊天框的 `+` → **Connectors**，清單裡要有 `easystore`。

再問一句「我的商店叫什麼名字？」，Claude 會呼叫 `easystore_get_store_info` 回答你。

Claude Desktop 設定位置、開發者安裝方式、故障排除見 [docs/setup/setup-guide.md](docs/setup/setup-guide.md)。

## 支援哪些 Claude 介面

| 介面 | 支援 | 說明 |
|------|------|------|
| Claude Code（CLI / IDE 擴充） | ✅ | `claude mcp add`，見上 |
| Claude Desktop 一般聊天 | ✅ | 寫進 `claude_desktop_config.json` |
| Claude Cowork | ❌ | 只接受從 claude.ai 帳號同步的遠端連接器，不會啟動本機 stdio 行程 |
| claude.ai 網頁版 / 手機版 | ❌ | 同上 |

本專案是 stdio 本機伺服器——Claude 在**你自己的電腦上**把它當子行程啟動，權杖從頭到尾沒離開過你的機器。代價是 Cowork 與網頁版用不到：那兩邊的連接器是由 Anthropic 的雲端主動連出去的，伺服器必須公網可達（HTTPS + OAuth）。詳見 [Anthropic 的自訂連接器說明](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)。

---

## 讀取工具（59 個，預設全部載入）

### 分析工具（analytics_tools）— 11 個

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
| `easystore_get_webhook_health` | Webhook 健康狀態 |
| `easystore_get_rfm_orders` | RFM 分析專用訂單資料（~86% token 節省） |

### 訂單工具（order_tools）— 8 個

`list_orders` / `get_order` / `list_fulfillments` / `get_fulfillment` / `list_transactions` / `get_transaction` / `list_checkouts` / `get_checkout`

### 商品工具（product_tools）— 9 個

`list_products` / `get_product` / `list_variants` / `get_variant` / `list_product_images` / `list_collections` / `get_collection` / `list_collects` / `get_collects_count`

### 顧客工具（customer_tools）— 10 個

`list_customers` / `search_customers` / `get_customer` / `get_customer_points` / `list_customer_addresses` / `get_customer_address` / `list_customer_attributes` / `list_groups` / `get_group` / `list_group_customers`

### 設定工具（settings_tools）— 14 個

`list_webhooks` / `get_webhook` / `count_webhooks` / `list_curls` / `get_curl` / `count_curls` / `list_metafields` / `get_metafield` / `count_metafields` / `list_locations` / `get_location` / `list_gateways` / `list_es_gateways` / `get_customer_attribute`

### 前台工具（storefront_tools）— 7 個

`list_pages` / `get_page` / `list_navigations` / `count_navigations` / `list_redirects` / `list_snippets` / `list_script_tags`

---

## 寫入工具（41 個，需 `ENABLE_WRITE_TOOLS=true`）

預設不載入，避免分析任務中意外觸發修改。設定後重啟伺服器即可啟用。

```env
ENABLE_WRITE_TOOLS=true
```

### 訂單操作（order_writes）— 6 個

| 工具 | 說明 |
|------|------|
| `easystore_cancel_order` | ⚠️ 取消訂單 |
| `easystore_refund_order` | 退款（指定金額） |
| `easystore_update_order` | 更新訂單備注 |
| `easystore_create_fulfillment` | 建立出貨紀錄（填入追蹤號） |
| `easystore_update_fulfillment` | 更新物流追蹤號 |
| `easystore_cancel_fulfillment` | ⚠️ 取消出貨紀錄 |

### 顧客與分群（customer_writes）— 9 個

| 工具 | 說明 |
|------|------|
| `easystore_update_customer` | 更新顧客資料 |
| `easystore_adjust_customer_points` | 調整點數（正/負） |
| `easystore_set_customer_credits` | ⚠️ 設定購物金絕對值 |
| `easystore_adjust_customer_credits` | 相對調整購物金 |
| `easystore_create_group` | 建立顧客群組 |
| `easystore_update_group` | 更新群組名稱 |
| `easystore_add_customers_to_group` | 批次加入群組 |
| `easystore_update_group_customers` | ⚠️ 替換群組全部成員 |
| `easystore_remove_customers_from_group` | 從群組移除顧客 |

### 商品與分類（product_writes）— 8 個

| 工具 | 說明 |
|------|------|
| `easystore_create_product` | 建立商品 |
| `easystore_update_product` | 更新商品（含上下架） |
| `easystore_update_variants` | 批次更新規格（價格/庫存） |
| `easystore_create_collection` | 建立分類 |
| `easystore_update_collection` | 更新分類 |
| `easystore_delete_collection` | ⚠️ 刪除分類（需 confirm=true） |
| `easystore_create_collect` | 將商品加入分類 |
| `easystore_delete_collect` | ⚠️ 移除商品-分類關聯（需 confirm=true） |

### 前台內容（storefront_writes）— 9 個

`create_page` / `update_page` / `delete_page` / `update_navigation` / `create_redirect` / `update_redirect` / `delete_redirect` / `update_snippet` / `update_script_tag`

### 系統設定（settings_writes）— 9 個

`create_webhook` / `update_webhook` / `delete_webhook` / `create_curl` / `update_curl` / `delete_curl` / `create_metafield` / `update_metafield` / `delete_metafield`

> ⚠️ **不可逆操作安全機制**：所有刪除類工具需傳入 `confirm=true` 才會執行；取消訂單等不可逆操作在 docstring 明確標示警告。

---

## RFM 顧客分群（讀寫閉環）

使用 `easystore_get_rfm_orders` 分析後，搭配寫入工具自動執行分群：

```
1. easystore_get_order_summary(days=180)                  → 確認訂單規模
2. easystore_get_rfm_orders(days=180, limit=250, page=N)  → 取得 RFM 資料
3. Claude 分析 → 判斷分群條件
4. easystore_update_group_customers(group_id, customer_ids)  → 更新群組成員
```

**Token 效能**：`easystore_get_rfm_orders` 只取 5 個必要欄位，相比 `easystore_list_orders` 節省 ~86% token。

詳見 [docs/optimization/rfm-analysis-guide.md](docs/optimization/rfm-analysis-guide.md)。

---

## 開發

要改程式碼才需要 clone：

```bash
git clone https://github.com/AgendaLu/mcp-easystore.git && cd mcp-easystore
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

```bash
# 執行測試
.venv/bin/python -m pytest tests/

# 環境檢查（顯示 MCP server 實際會讀到的值）
.venv/bin/python scripts/check_env.py

# API 連線測試
.venv/bin/python scripts/auth/test_connection.py
```

憑證放 `.env.local`（`cp .env.example .env.local`，已被 `.gitignore` 排除）。repo 根目錄的 [`.mcp.json`](.mcp.json) 走本地 venv，不強制裝 uv。

專案結構詳見 [docs/architecture/project-structure.md](docs/architecture/project-structure.md)。

## 文件

| 目錄 | 內容 |
|------|------|
| `docs/setup/` | 安裝設定指南（權杖取得、MCP 註冊、故障排除） |
| `docs/api-reference/` | EasyStore API 端點清單 |
| `docs/architecture/` | 專案結構說明（含工具端點對照表） |
| `docs/optimization/` | Token 優化指南、RFM 分析指南 |
| `docs/archive/` | 已完成優化的驗證報告 |
