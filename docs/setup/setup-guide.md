# 安裝設定指南

從零到可用，兩步：**拿到 API 權杖** → **註冊 MCP server**。

---

## 步驟 1：取得 EasyStore API 權杖

依 [EasyStore 官方說明](https://support.easystore.co/zh-tw/article/easystore-api-1amargb/)：

1. 進入 EasyStore 後台 → **安裝擴充** → **更多** → **客製擴充**
2. 為客製擴充命名（例如 `Claude MCP`）
3. **設定存取範疇**（scope）—— 這步決定後面能不能寫入，見下方說明
4. 儲存後畫面才會顯示 **API 存取權杖**，複製起來

### 存取範疇要勾多少？

本專案有兩層開關，兩層都得開，寫入工具才會動：

| 層級 | 位置 | 說明 |
|------|------|------|
| EasyStore 端 | 客製擴充的存取範疇 | 沒給寫入範疇 → API 回 403 |
| MCP server 端 | `ENABLE_WRITE_TOOLS` | 預設 `false`，只註冊 59 個讀取工具 |

只想查資料就給讀取範疇、`ENABLE_WRITE_TOOLS` 維持 `false`。要用取消訂單、退款、批次改價這些操作，兩邊都得打開（41 個寫入工具，總計 100 個）。

> 權杖只在儲存當下顯示一次，遺失就重新產生。外洩時也是回這個頁面重新產生，舊的立刻失效。

---

## 步驟 2：註冊 MCP server

先建好虛擬環境與依賴：

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

接著挑一種註冊方式。

### 方式 A：`.mcp.json`（專案內建，推薦）

repo 根目錄已經有 [`.mcp.json`](../../.mcp.json)，憑證從 shell 環境變數展開，不寫死在檔案裡：

```json
{
  "mcpServers": {
    "easystore": {
      "type": "stdio",
      "command": "${EASYSTORE_PYTHON:-.venv/bin/python}",
      "args": ["mcp_server.py"],
      "env": {
        "EASYSTORE_SHOP_URL": "${EASYSTORE_SHOP_URL}",
        "EASYSTORE_ACCESS_TOKEN": "${EASYSTORE_ACCESS_TOKEN}",
        "ENABLE_WRITE_TOOLS": "${ENABLE_WRITE_TOOLS:-false}"
      }
    }
  }
}
```

在 shell（`~/.zshrc` 或 direnv）設好三個變數，再從專案目錄啟動 Claude Code：

```bash
export EASYSTORE_SHOP_URL=https://yourshop.easystore.co
export EASYSTORE_ACCESS_TOKEN=你的權杖
export ENABLE_WRITE_TOOLS=false
```

第一次啟動時 Claude Code 會問要不要信任這個專案的 MCP server，允許即可。

虛擬環境不在 `.venv/` 的話，用 `EASYSTORE_PYTHON` 指到實際的 python 執行檔（可用絕對路徑）。

### 方式 B：`claude mcp add`（憑證只留在本機）

不想把憑證放進 shell 設定檔就用這個，一行指令寫進 `~/.claude.json`：

```bash
claude mcp add easystore --scope local -e EASYSTORE_SHOP_URL=https://yourshop.easystore.co -e EASYSTORE_ACCESS_TOKEN=你的權杖 -e ENABLE_WRITE_TOOLS=false -- /絕對路徑/mcp-easystore/.venv/bin/python /絕對路徑/mcp-easystore/mcp_server.py
```

確認連線：

```bash
claude mcp list
```

看到 `easystore ✔ Connected` 就成功了。

> ⚠️ 這條路徑會把權杖明文寫進 `~/.claude.json`。該檔案常被連同 dotfiles 備份或分享，注意別外流。

### Claude Desktop

Claude Desktop 有自己的設定檔，**不會**讀專案的 `.mcp.json`：

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

格式與方式 B 寫入的內容相同，`command` 必須用 `.venv/bin/python` 的**絕對路徑**，否則找不到已安裝的套件。

---

## 環境變數一覽

| 變數 | 用途 | 必填 | 預設 |
|------|------|------|------|
| `EASYSTORE_SHOP_URL` | 商店網址，例如 `https://yourshop.easystore.co` | ✓ | — |
| `EASYSTORE_ACCESS_TOKEN` | 客製擴充的 API 存取權杖 | ✓ | — |
| `ENABLE_WRITE_TOOLS` | 設 `true` 才註冊 41 個寫入工具 | ✗ | `false` |
| `EASYSTORE_PYTHON` | 覆寫 `.mcp.json` 用的 python 路徑 | ✗ | `.venv/bin/python` |

MCP server 由 client 啟動時，這些變數已經注入行程環境，`config/settings.py` 只讀 `os.environ`。

**`.env` / `.env.local` 是給 `scripts/`、`tests/` 底下的獨立腳本用的**——直接跑 `python scripts/auth/test_connection.py` 時沒有 MCP client 幫你注入，才需要檔案：

```bash
cp .env.example .env.local   # .env.local 已被 .gitignore 排除
```

優先級：已存在的環境變數 > `.env.local` > `.env`。

---

## 驗證

```bash
python3 scripts/check_env.py          # 環境變數有沒有讀到
python3 scripts/auth/test_connection.py   # API 打得通嗎
python3 -m pytest tests/              # 單元測試
```

MCP server 啟動成功時，stderr 會出現：

```
[easystore_mcp] 已載入 59 個工具 | 🔒 寫入工具未啟用（設定 ENABLE_WRITE_TOOLS=true 啟用）
```

---

## 故障排除

### `claude mcp list` 顯示 Failed to connect

多半是 `command` 指到沒裝依賴的 python。確認：

```bash
.venv/bin/python -c "import mcp, httpx, dotenv; print('ok')"
```

### 環境變數讀不到（`EASYSTORE_SHOP_URL 為空`）

`config/settings.py` 只認 `os.environ` 與 `.env` 檔案，**不會**去讀 `.claude/settings.json` 或 `.claude/settings.local.json`——那兩個檔案沒有 `mcpServers` 或 MCP 環境變數這種欄位，寫在裡面不會生效。改用上面的方式 A 或 B。

用 `.env.local` 時注意等號兩邊不要有空格：

```bash
EASYSTORE_SHOP_URL=https://yourshop.easystore.co    # ✓
EASYSTORE_SHOP_URL = https://yourshop.easystore.co  # ✗
```

### 401 Access Token 無效

1. 權杖打錯或已重新產生 → 回後台客製擴充頁面確認
2. 客製擴充被刪除 → 重建
3. `EASYSTORE_SHOP_URL` 網址寫錯

### 403 但讀取工具正常

客製擴充的**存取範疇**沒給寫入權限。回步驟 1 調整範疇後儲存。

### 寫入工具沒出現

`ENABLE_WRITE_TOOLS` 沒設成 `true`，或設了之後沒重啟 MCP server。啟動訊息會顯示目前狀態。

---

## 安全性

- 權杖只放在 shell 環境變數、`~/.claude.json` 或 `.env.local`，三者都不進版控
- `.env.example` 是範本，永遠不填真值
- 權杖曾經出現在終端輸出、log 或截圖 → 回後台重新產生
