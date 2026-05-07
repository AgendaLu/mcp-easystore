# 在 Cowork 中執行 MCP Server

本指南說明如何在 Claude Code / Cowork 中執行 EasyStore MCP Server。

## 前置條件

✅ Python 3.12+ 已安裝
✅ 虛擬環境已建立（`.venv`）
✅ 環境變數已設定（`.claude/settings.local.json` 或 `.env.local`）

## 方法 1: 使用 Claude Code 內建啟動器

### 步驟 1: 確認配置文件

檢查以下文件是否存在且正確配置：

- ✅ `.claude/settings.json` - 專案級配置
- ✅ `.claude/settings.local.json` - 本地機器配置（包含 API 憑證）
- ✅ `.claude/launch.json` - 啟動配置

### 步驟 2: 在 Claude Code 中啟動 MCP

1. 開啟 Claude Code
2. 在命令面板（Cmd+K / Ctrl+K）中搜尋 "start server"
3. 選擇 "EasyStore MCP Server"
4. MCP 伺服器將在背景啟動

### 步驟 3: 驗證連接

MCP 伺服器啟動成功時，你會在 Claude Code 中看到：

```
[easystore_mcp] 已載入 XX 個工具 | ✅ 寫入工具已啟用
```

## 方法 2: 使用命令行

### 啟動 MCP Server

```bash
# 方法 A: 使用啟動腳本
./scripts/start_mcp.sh

# 方法 B: 直接運行
source .venv/bin/activate
python3 mcp_server.py
```

### 停止 MCP Server

按 `Ctrl+C` 停止伺服器

## 環境變數配置

### 選項 A: `.claude/settings.local.json`（推薦）

在 `.claude/settings.local.json` 中的 `mcpServers` 部分設定環境變數：

```json
{
  "mcpServers": {
    "easystore": {
      "env": {
        "EASYSTORE_SHOP_URL": "https://yourshop.easystore.co",
        "EASYSTORE_ACCESS_TOKEN": "your_token_here",
        "ENABLE_WRITE_TOOLS": "true"
      }
    }
  }
}
```

### 選項 B: `.env.local`

複製 `.env.example` 並填入實際值：

```bash
cp .env.example .env.local
```

編輯 `.env.local`：

```
EASYSTORE_SHOP_URL=https://yourshop.easystore.co
EASYSTORE_ACCESS_TOKEN=your_token_here
ENABLE_WRITE_TOOLS=false
```

## 可用工具

MCP Server 提供以下工具類別：

### 📊 分析工具 (Analytics Tools)
- 訂單統計
- 收入分析
- 客戶增長

### 👥 客戶工具 (Customer Tools)
- 查詢客戶信息
- 列出客戶清單
- 客戶地址管理

### 📦 訂單工具 (Order Tools)
- 查詢訂單詳情
- 列出訂單
- 訂單狀態查詢

### 🛍️ 產品工具 (Product Tools)
- 產品信息查詢
- 庫存管理
- 產品列表

### ⚙️ 設定工具 (Settings Tools)
- 店鋪信息
- 金流設定
- Webhook 管理

### 🏪 Storefront 工具 (Storefront Tools)
- 頁面管理
- 導航配置
- 重導規則

## 故障排除

### MCP 伺服器無法啟動

**症狀**: `mcp_server.py: command not found`

**解決方案**:
```bash
# 確保虛擬環境已啟動
source .venv/bin/activate

# 確保在專案根目錄運行
cd /path/to/mcp-easystore
```

### 環境變數未讀取

**症狀**: `EASYSTORE_SHOP_URL 為空`

**解決方案**:
1. 確認 `.claude/settings.local.json` 中的環境變數已設定
2. 重新啟動 Claude Code
3. 查看 Claude Code 的輸出日誌

### API 認證失敗

**症狀**: `401 Unauthorized` 或 `Invalid token`

**解決方案**:
1. 驗證 `EASYSTORE_ACCESS_TOKEN` 是否正確
2. 確認 token 在 EasyStore 管理介面中仍有效
3. 檢查 `EASYSTORE_SHOP_URL` 格式是否正確

### 寫入工具未啟用

**症狀**: 寫入工具不可用

**解決方案**:
在 `.claude/settings.local.json` 中設定：
```json
"ENABLE_WRITE_TOOLS": "true"
```

## 文件結構參考

```
mcp-easystore/
├── .claude/
│   ├── settings.json           # 專案級配置
│   ├── settings.local.json     # 本地配置（不提交）
│   └── launch.json             # 啟動配置
├── .venv/                       # Python 虛擬環境
├── mcp_server.py               # MCP Server 入口
├── tools/                       # 工具實現
│   ├── analytics_tools.py
│   ├── customer_tools.py
│   ├── order_tools.py
│   ├── product_tools.py
│   ├── settings_tools.py
│   ├── storefront_tools.py
│   └── tool_registry.py
└── scripts/
    └── start_mcp.sh            # 啟動腳本
```

## 更多資源

- [EasyStore API 文檔](./EasyStore_API_Endpoint_Inventory.md)
- [MCP 標準規範](https://modelcontextprotocol.io/)
- [Claude Code 文檔](https://claude.com/claude-code)
