# 環境變數配置指南

本文檔說明如何在 Claude Cowork 中正確配置環境變數，確保 MCP Server 能夠訪問 EasyStore API。

## 🎯 概述

EasyStore MCP Server 需要以下環境變數：

| 變數 | 用途 | 範例 | 必需 |
|------|------|------|------|
| `EASYSTORE_SHOP_URL` | 商店 API 網址 | `https://yourshop.easystore.co` | ✓ |
| `EASYSTORE_ACCESS_TOKEN` | API 訪問令牌 | `abc123def456...` | ✓ |
| `ENABLE_WRITE_TOOLS` | 啟用寫入工具 | `true` 或 `false` | ✗ |

## 📊 環境變數優先級

環境變數按以下優先級加載（由高到低）：

```
1️⃣  Claude Cowork 注入的環境變數（最高）
    ↓
2️⃣  .claude/settings.local.json 中的 env
    ↓
3️⃣  .env.local 檔案
    ↓
4️⃣  .env 檔案
    ↓
5️⃣  系統環境變數（最低）
```

**說明**：
- 優先級更高的來源會覆蓋低優先級的設定
- 這確保本地開發和生產環境都能正確運行

## 🔧 配置方式

### 方式 1: .claude/settings.local.json（推薦用於 Cowork）

編輯 `.claude/settings.local.json`：

```json
{
  "description": "本地機器配置 - 包含敏感資訊，不提交到 Git",
  "env": {
    "EASYSTORE_SHOP_URL": "https://yourshop.easy.co",
    "EASYSTORE_ACCESS_TOKEN": "your_token_here",
    "ENABLE_WRITE_TOOLS": "false"
  },
  "mcpServers": {
    "easystore": {
      "command": "python3",
      "args": ["mcp_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**優點**：
- ✓ Claude Cowork 會自動加載這個檔案
- ✓ 被 `.gitignore` 排除，不會暴露敏感信息
- ✓ 優先級更高，確保 Cowork 中的設定被使用

### 方式 2: .env.local（用於本地開發）

複製 `.env.example` 為 `.env.local`：

```bash
cp .env.example .env.local
```

編輯 `.env.local`：

```
EASYSTORE_SHOP_URL=https://yourshop.easy.co
EASYSTORE_ACCESS_TOKEN=your_token_here
ENABLE_WRITE_TOOLS=false
```

**優點**：
- ✓ 簡單直觀
- ✓ 被 `.gitignore` 排除
- ✓ 支持注釋和多行值

### 方式 3: 系統環境變數

在 shell 中設定：

```bash
export EASYSTORE_SHOP_URL=https://yourshop.easy.co
export EASYSTORE_ACCESS_TOKEN=your_token_here
export ENABLE_WRITE_TOOLS=false
```

**優點**：
- ✓ 適合 CI/CD 流程
- ✓ 不需要檔案

## ✅ 驗證環境變數

使用提供的檢查工具驗證環境變數是否正確加載：

```bash
python3 scripts/check_env.py
```

**輸出範例**：

```
============================================================
📋 環境變數檢查
============================================================

1️⃣  系統環境變數
------------------------------------------------------------
  ✓ EASYSTORE_SHOP_URL: https://yourshop.easy.co
  ✓ EASYSTORE_ACCESS_TOKEN: your_token_here
  ✓ ENABLE_WRITE_TOOLS: false

...

✅ 所有配置正常！
```

## 🚀 在 Cowork 中使用

### 步驟 1: 配置環境變數

在 `.claude/settings.local.json` 中設定：

```json
{
  "env": {
    "EASYSTORE_SHOP_URL": "https://yourshop.easystore.co",
    "EASYSTORE_ACCESS_TOKEN": "your_token_here",
    "ENABLE_WRITE_TOOLS": "false"
  }
}
```

### 步驟 2: 啟動 MCP Server

在 Claude Code 中：

```
Cmd+K → "start server" → 選擇 "EasyStore MCP Server"
```

### 步驟 3: 驗證連接

MCP Server 啟動時會顯示：

```
[easystore_mcp] 已載入 57 個工具 | ✅ 寫入工具已啟用
```

## 🔒 安全性最佳實踐

### ❌ 不要做：

```bash
# 不要硬編碼到程式碼中
EASYSTORE_ACCESS_TOKEN = "abc123..." # ❌ 危險！

# 不要提交敏感信息到 Git
git add .env  # ❌ 危險！
git add .claude/settings.local.json  # ❌ 已在 .gitignore 排除
```

### ✅ 應該做：

```bash
# 使用 .env.local 或 .claude/settings.local.json
EASYSTORE_ACCESS_TOKEN=abc123...  # ✓ 被 .gitignore 排除

# 使用 .env.example 作為範本
cp .env.example .env.local  # ✓ 提交 .env.example，不提交 .env.local

# 驗證敏感信息不在 Git 中
git status  # ✓ 確保 .env.local 不被追蹤
```

## ⚠️ 重要：Claude Desktop（Cowork）的 MCP 設定位置

> **教訓**：如果在 Cowork 中 MCP server 收不到環境變數，很可能是因為 Claude Desktop 有自己獨立的 MCP 設定檔，**不會**讀取專案的 `.claude/settings.json`。

Claude Desktop 的 MCP server 設定檔位於：

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

需要把環境變數直接寫在這裡的 `env` 區塊，才能確保 Cowork 啟動 MCP server 時正確注入：

```json
{
  "mcpServers": {
    "easystore": {
      "command": "/path/to/mcp-easystore/.venv/bin/python3",
      "args": ["/path/to/mcp-easystore/mcp_server.py"],
      "env": {
        "EASYSTORE_SHOP_URL": "https://yourshop.easy.co",
        "EASYSTORE_ACCESS_TOKEN": "your_token_here",
        "ENABLE_WRITE_TOOLS": "false",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

> ⚠️ 注意：`command` 必須用 `.venv/bin/python3` 的絕對路徑，否則找不到已安裝的套件。

**或**，透過 terminal 用 `claude mcp add` 指令安裝（效果相同，會自動寫入設定檔）：

```bash
claude mcp remove easystore

claude mcp add easystore \
  -e EASYSTORE_SHOP_URL=https://yourshop.easy.co \
  -e EASYSTORE_ACCESS_TOKEN=your_token_here \
  -e ENABLE_WRITE_TOOLS=false \
  -e PYTHONUNBUFFERED=1 \
  -- /path/to/mcp-easystore/.venv/bin/python3 \
  /path/to/mcp-easystore/mcp_server.py

# 確認連線
claude mcp list
```

---

## 🐛 故障排除

### 環境變數未被加載

**症狀**：`EASYSTORE_SHOP_URL 為空` 或 API 認證失敗

**解決方案**：

1. 運行檢查工具：
   ```bash
   python3 scripts/check_env.py
   ```

2. 確認 `.claude/settings.local.json` 格式正確（有效的 JSON）

3. 確認 `.env.local` 檔案中的值沒有多餘空格：
   ```bash
   # ✓ 正確
   EASYSTORE_SHOP_URL=https://yourshop.easystore.co
   
   # ❌ 錯誤（有多餘空格）
   EASYSTORE_SHOP_URL = https://yourshop.easystore.co
   ```

4. 重啟 Claude Code 強制重新加載環境變數

### "python-dotenv 未安裝" 警告

**症狀**：看到 `[WARNING] python-dotenv 未安裝`

**解決方案**：

```bash
# 安裝依賴
pip install -r requirements.txt

# 或單獨安裝
pip install python-dotenv
```

### API 認證失敗

**症狀**：`Error 401: Access Token 無效或缺失`

**原因**：
1. `EASYSTORE_ACCESS_TOKEN` 為空
2. Token 已過期
3. Token 對應的 App 已被刪除

**解決方案**：

1. 檢查環境變數：
   ```bash
   python3 scripts/check_env.py
   ```

2. 在 EasyStore 管理介面重新生成 Token

3. 確保 Token 對應的 App 有足夠的權限（scope）

## 📚 相關文檔

- [MCP Cowork 設定指南](./MCP_COWORK_SETUP.md)
- [EasyStore API 文檔](./EasyStore_API_Endpoint_Inventory.md)
- [項目結構說明](./mcp_easystore_project_structure.md)

## 💡 最佳實踐總結

1. **本地開發**：使用 `.env.local`
2. **Cowork**：使用 `.claude/settings.local.json`
3. **CI/CD**：使用系統環境變數（環境變數注入）
4. **始終驗證**：用 `scripts/check_env.py` 確認設定
5. **保護敏感信息**：永遠不要提交 API Token 到 Git
