# 安裝設定指南

從零到可用三步：**拿到 API 權杖** → **裝 uv** → **註冊 MCP server**。

使用者端不需要 clone repo、不需要裝 Python、不需要建虛擬環境。

> **先確認你用的介面**：本專案是 stdio 本機伺服器，Claude 在你自己的電腦上把它當子行程啟動。
> **terminal 的 `claude` 指令、Claude Code、Claude Desktop 一般聊天、Claude Cowork 都能用**，但設定分兩份：
> 前兩者共用 `~/.claude.json`（`claude mcp add` 寫入），後兩者共用 `claude_desktop_config.json`（手動編輯）。
> Cowork 沒有自己的 MCP 設定介面，它用的是 Claude Desktop 已註冊的本機 server——所以要在 Cowork 用，設定就得寫進 Desktop 的設定檔。
> **claude.ai 網頁版與手機版不支援**：那邊的連接器由 Anthropic 雲端主動連出去，只吃公網可達的遠端 MCP，不會啟動你機器上的行程。

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
| MCP server 端 | `ENABLE_WRITE_TOOLS` | 預設 `false`，只註冊 60 個讀取工具 |

只想查資料就給讀取範疇、`ENABLE_WRITE_TOOLS` 維持 `false`。要用取消訂單、退款、批次改價這些操作，兩邊都得打開（41 個寫入工具，總計 101 個）。

> 權杖只在儲存當下顯示一次，遺失就重新產生。外洩時也是回這個頁面重新產生，舊的立刻失效。

---

---

## 手動寫設定前，先把這些湊齊

`claude mcp add` 會幫你產生 JSON；**手動編輯 `claude_desktop_config.json` 的話**（Cowork 與 Desktop 一般聊天走這條），下面五項要先確定，不然就是裝完才發現不動、再回頭一項一項猜。

| 要填的 | 正確來源 | 常見填錯 |
|---|---|---|
| `command` | `which uvx` 的**絕對路徑**（Homebrew 多半是 `/opt/homebrew/bin/uvx`） | 直接寫 `"uvx"`。Desktop 從 GUI 啟動不繼承 shell 的 `PATH`，會 spawn 失敗 |
| `args` | `["--from", "git+https://github.com/AgendaLu/mcp-easystore", "mcp-easystore"]` | 開發安裝時是另一組：`command` 用 `.venv/bin/python` 的絕對路徑、`args` 用 `["-m", "mcp_easystore.server"]` |
| `EASYSTORE_SHOP_URL` | `https://<easystore_domain>`，見下 | 填 `easystore.co`（那是 EasyStore 官網不是你的店）、填後台網址列、填已停用的舊商店 |
| `EASYSTORE_ACCESS_TOKEN` | 後台 → 安裝擴充 → 更多 → 客製擴充，儲存後只顯示一次 | 權杖重新產生過，舊的已失效 |
| `ENABLE_WRITE_TOOLS` | `"true"` 或 `"false"`，**字串** | 寫成 JSON 布林 `false` |

### 商店網址到底填什麼

權威值是 `GET /store.json` 回應裡的 **`easystore_domain`** 欄位：

```json
{ "store": { "name": "你的店名", "easystore_domain": "yourshop.easy.co", "domains": [] } }
```

所以 `EASYSTORE_SHOP_URL` 填 `https://yourshop.easy.co`。`domains` 是自訂網域，有值時通常也打得通，但基準是 `easystore_domain`。

還沒有可用設定、拿不到 `store.json` 時，用 curl 先驗——五秒，省一小時：

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "EasyStore-Access-Token: 你的權杖" https://你的商店.easy.co/api/3.0/store.json
```

`200` 才寫進設定檔。`404` 是商店網址錯（不是權杖問題），`401` 是網址對但權杖錯。

裝好之後改用 `easystore_diagnose`：它會回報生效的網址、實際的 `easystore_domain`，兩者不一致時直接給出警告。

### JSON 本身的兩個坑

不能有註解與尾逗號；`easystore` 這一項要**併進**既有的 `mcpServers`，不是整份覆蓋（那個檔案裡通常還有其他設定）。改完 Cmd+Q 完全結束 Claude Desktop 再開，關視窗不算，Cowork 也要一起重開。

---

## 步驟 2：安裝 uv（只做一次）

```bash
brew install uv
```

或 `curl -LsSf https://astral.sh/uv/install.sh | sh`。

uv 是單一執行檔，**連 Python runtime 都會自己下載**——機器上沒有 Python、或版本太舊，都不影響。
使用者不需要建虛擬環境，也不需要跑任何 `pip` 指令。

## 步驟 3：註冊 MCP server

兩份設定，涵蓋四個介面：

| 設定檔 | 涵蓋 |
|---|---|
| `~/.claude.json`（`claude mcp add` 寫入） | terminal 的 `claude` 指令、Claude Code |
| `claude_desktop_config.json`（手動編輯） | Claude Desktop 一般聊天、Claude Cowork |

四個介面都要用就兩份都寫，同一組權杖各寫一次。

### terminal CLI 與 Claude Code

```bash
claude mcp add easystore --scope local \
  -e EASYSTORE_SHOP_URL=https://yourshop.easy.co \
  -e EASYSTORE_ACCESS_TOKEN=你的權杖 \
  -e ENABLE_WRITE_TOOLS=false \
  -- uvx --from git+https://github.com/AgendaLu/mcp-easystore mcp-easystore
```

確認連線：

```bash
claude mcp list
```

看到 `easystore ✔ Connected` 就成功了。第一次啟動 uvx 要下載 Python 與依賴，約 30 秒；之後走快取，啟動很快。

> ⚠️ 這會把權杖明文寫進 `~/.claude.json`。該檔案常被連同 dotfiles 備份或分享，注意別外流。

`--scope local` 只在目前這個專案目錄生效；想在任何目錄下都能用，改成 `--scope user`。

### Claude Cowork 與 Claude Desktop 一般聊天

這兩個介面共用 Claude Desktop 的設定檔。Cowork 沒有自己的 MCP 設定介面——它呼叫的就是 Desktop 已註冊的這個本機 server，所以只要這裡設好，Cowork 的工具清單裡就會出現 `easystore_*`：

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

```json
{
  "mcpServers": {
    "easystore": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/AgendaLu/mcp-easystore", "mcp-easystore"],
      "env": {
        "EASYSTORE_SHOP_URL": "https://yourshop.easy.co",
        "EASYSTORE_ACCESS_TOKEN": "你的權杖",
        "ENABLE_WRITE_TOOLS": "false"
      }
    }
  }
}
```

Desktop 從 GUI 啟動時 `PATH` 可能找不到 `uvx`，這時把 `command` 換成絕對路徑（`which uvx` 查）。改完要重啟 Desktop。

### 更新

uvx 每次啟動會抓 repo 最新版，重啟 client 即可。要強制重抓：

```bash
uv cache clean mcp-easystore
```

## 開發者安裝（要改程式碼才需要）

```bash
git clone https://github.com/AgendaLu/mcp-easystore.git && cd mcp-easystore
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

repo 根目錄的 [`.mcp.json`](../../.mcp.json) 走本地 venv（不強制裝 uv），憑證從 shell 環境變數展開：

```json
{
  "mcpServers": {
    "easystore": {
      "type": "stdio",
      "command": "${EASYSTORE_PYTHON:-.venv/bin/python}",
      "args": ["-m", "mcp_easystore.server"],
      "env": {
        "EASYSTORE_SHOP_URL": "${EASYSTORE_SHOP_URL:-}",
        "EASYSTORE_ACCESS_TOKEN": "${EASYSTORE_ACCESS_TOKEN:-}",
        "ENABLE_WRITE_TOOLS": "${ENABLE_WRITE_TOOLS:-false}"
      }
    }
  }
}
```

從專案目錄啟動 Claude Code，第一次會問要不要信任這個專案的 MCP server。憑證放 `.env.local` 即可（見下節），不必 export。

虛擬環境不在 `.venv/` 的話，用 `EASYSTORE_PYTHON` 指到實際的 python 執行檔。

---

## 權杖要放哪裡

三個位置都不會進版控，差別在「誰讀得到」：

| 位置 | 適合 | 風險 |
|------|------|------|
| `.env.local`（專案內） | 只有這個專案要用、想跟 repo 放一起 | 明文檔案，但範圍最小；記得 `chmod 600` |
| shell 環境變數（`~/.zshrc`、direnv） | 同時要跑 scripts 與 MCP server | 每個從該 shell 啟動的程式都讀得到；`~/.zshrc` 常被連同 dotfiles 上傳 |
| `~/.claude.json`（`claude mcp add` 寫入） | 只給 Claude 用、不想動 shell | 明文，且該檔常被備份或分享 |

**`.env.local` 是預設建議**：範圍最小，且 `.gitignore` 已排除。

```bash
cp .env.example .env.local
# 填入 EASYSTORE_SHOP_URL 與 EASYSTORE_ACCESS_TOKEN
chmod 600 .env.local
```

以上是**開發者**的選擇。透過 uvx 安裝的使用者只有 `~/.claude.json`（或 Desktop 設定檔）這一個位置。

開發用的 `.mcp.json` 其 `${EASYSTORE_ACCESS_TOKEN:-}` 在 shell 沒設定時會注入空值，settings.py
把空值視為沒設定，接著由 `.env.local` 補上——所以只填 `.env.local` 也能正常啟動，不必動 shell。

> 用 direnv 的話 `.envrc` 也要進 `.gitignore`。要更嚴格可以把權杖放進 macOS Keychain，在
> `.zshrc` 用 `export EASYSTORE_ACCESS_TOKEN=$(security find-generic-password -s easystore -w)`
> 取出，磁碟上就不留明文。

### 已經外洩怎麼辦

權杖出現在終端輸出、log、截圖或被 commit 過，就當作已外洩：回後台客製擴充頁面重新產生，
舊的立刻失效。權杖沒有有效期限，不主動換就會一直有效。

若已經 commit 進版控，改檔案不夠——歷史紀錄還在，一定要重新產生權杖。

## 環境變數一覽

| 變數 | 用途 | 必填 | 預設 |
|------|------|------|------|
| `EASYSTORE_SHOP_URL` | 商店網址，例如 `https://yourshop.easy.co` | ✓ | — |
| `EASYSTORE_ACCESS_TOKEN` | 客製擴充的 API 存取權杖 | ✓ | — |
| `ENABLE_WRITE_TOOLS` | 設 `true` 才註冊 41 個寫入工具 | ✗ | `false` |
| `EASYSTORE_PYTHON` | 覆寫 `.mcp.json` 用的 python 路徑 | ✗ | `.venv/bin/python` |

---

## 設定優先級（出問題先看這節）

同一組變數可能同時存在於好幾個檔案，而且它們**不是同一個系統在讀**。分不清楚誰生效，
就會出現「我改了 `.env` 重啟卻沒反應」這種找一小時的問題。

**誰讀哪一個：**

| 來源 | 誰讀它 | 對 MCP server 生效嗎 |
|------|--------|----------------------|
| `claude_desktop_config.json` 的 `env` | Claude Desktop、Claude Cowork | ✅ 由 client 注入行程環境 |
| `~/.claude.json`（`claude mcp add` 寫入）的 `env` | terminal CLI、Claude Code | ✅ 同上 |
| `.mcp.json` 的 `env`（專案內，開發用） | Claude Code | ✅ 同上；`${VAR:-}` 展開為空時視為沒設定 |
| `.env.local` / `.env` | `settings.py` 自己讀 | ⚠️ 只在上面沒提供時補位 |
| `.claude/settings.json` / `.claude/settings.local.json` | 沒有人 | ❌ 不是 MCP 設定來源，寫在這裡不會生效 |

**同一個行程內的優先級（由高到低）：**

1. 有值的環境變數（client 注入或 shell export）
2. `.env.local`
3. `.env`

空字串與未展開的 `${VAR}` 佔位字串一律視為「沒設定」，讓 `.env.local` 有機會補上。這是必要的：
`.mcp.json` 裡沒帶預設值的 `${VAR}`，在 shell 未設定該變數時，MCP client 會把字面字串
`"${VAR}"` 原樣注入子行程（實測結果），留著它會讓 `validate_config()` 誤判設定正常，直到打
API 才拿到 401。

`.env` / `.env.local` 會在兩個目錄找：**執行時的工作目錄**，以及**套件所在的專案根目錄**
（`mcp_easystore/` 的上一層）。後者是給開發安裝用的——MCP server 由 client 啟動時工作目錄
通常不是 repo 根目錄，只看工作目錄的話 repo 裡的 `.env` 永遠讀不到。透過 uvx 安裝時程式在
site-packages，那裡沒有 `.env`，這條路自然不生效。

**不要用猜的。** 在對話中呼叫 `easystore_diagnose`，它會直接說出目前生效的商店網址、每個變數
來自哪裡、實際讀到哪些 `.env`，並實打一次 `/store.json`：

```
easystore_diagnose
```

開發環境另有 `scripts/check_env.py`（同一份邏輯），但它看到的是**你這個 shell** 的設定，
不一定等於 Claude 啟動 server 時注入的那一份——以 `easystore_diagnose` 為準。

---

## 驗證

### 使用者

**第一步，確認 client 連得上：**

| 介面 | 怎麼確認 |
|---|---|
| terminal CLI / Claude Code | `claude mcp list` → `easystore ✔ Connected`（顯示 `Failed to connect` 看下方故障排除） |
| Claude Desktop | 重啟後點聊天框的 `+` → **Connectors**，清單裡要有 `easystore`。沒有的話是設定檔位置或 JSON 格式問題 |
| Claude Cowork | 工具清單裡找得到 `easystore_*`。找不到多半是設定只寫進了 `~/.claude.json`，Cowork 讀的是 Desktop 那份 |

**第二步，確認設定是對的**——連得上不等於設定對。任何介面都跑這一句：

```
呼叫 easystore_diagnose
```

要看到 `store_probe.http_status` 是 `200`、`store_name` 是你的店名，才算真的驗完。這個工具會一併回報生效的商店網址、每個變數的來源、權杖指紋（不含明文）、載入的工具數量，以及設定的網域與實際 `easystore_domain` 不一致時的警告。

啟用了寫入工具的話，`diagnose` 的 `tools.write_tools_loaded` 應為 41、`total` 為 101。

### 開發者

以下透過 uvx 安裝的使用者不需要：

```bash
.venv/bin/python scripts/check_env.py          # 環境變數有沒有讀到
.venv/bin/python scripts/auth/test_connection.py   # API 打得通嗎
.venv/bin/python -m pytest tests/              # 單元測試
```

MCP server 啟動成功時，stderr 會出現：

```
[easystore_mcp] 已載入 60 個工具 | 🔒 寫入工具未啟用（設定 ENABLE_WRITE_TOOLS=true 啟用）
```

---

## 故障排除

### `claude mcp list` 顯示 Failed to connect

用 uvx 安裝的話，多半是 client 找不到 `uvx`。用絕對路徑（`which uvx`）取代 `command` 裡的 `uvx`。

開發環境則多半是 `command` 指到沒裝依賴的 python。確認：

```bash
.venv/bin/python -c "import mcp_easystore, httpx, dotenv; print('ok')"
```

### `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`

裝到 mcp 2.x 了。2.x 把 `FastMCP` 更名為 `MCPServer` 並移除舊的 import 路徑，本專案的程式仍是
v1 API。`pyproject.toml` 已鎖 `mcp>=1.2,<2`，重裝即可：

```bash
.venv/bin/pip install -e ".[dev]"
```

### 環境變數讀不到（`EASYSTORE_SHOP_URL 為空`）

`mcp_easystore/config/settings.py` 只認 `os.environ` 與 `.env` / `.env.local`（工作目錄與套件所在的專案根目錄），**不會**去讀 `.claude/settings.json` 或 `.claude/settings.local.json`——那兩個檔案沒有 `mcpServers` 或 MCP 環境變數這種欄位，寫在裡面不會生效。

先跑 `easystore_diagnose`：它會列出每個變數的實際來源，不必用猜的。詳見上方「設定優先級」。

用 `.env.local` 時注意等號兩邊不要有空格：

```bash
EASYSTORE_SHOP_URL=https://yourshop.easy.co    # ✓
EASYSTORE_SHOP_URL = https://yourshop.easy.co  # ✗
```

### 所有工具都回 404

多半不是路徑錯，是 `EASYSTORE_SHOP_URL` 指到一個**不存在或已停用**的商店（打錯字、商店改名、
用了測試站的網址）。錯誤訊息會帶上實際請求的 URL，先看那個網域對不對：

```
[orders] Error 404: 商店不存在或已停用（請確認 EASYSTORE_SHOP_URL 指到的商店還在），或路徑／ID 錯誤。 請求 URL：https://wrongshop.easy.co/api/3.0/orders.json
```

跑 `easystore_diagnose` 確認生效的商店網址，以及 `/store.json` 的實際 HTTP 狀態碼。

### 401 Access Token 無效

1. 權杖打錯或已重新產生 → 回後台客製擴充頁面確認
2. 客製擴充被刪除 → 重建
3. `EASYSTORE_SHOP_URL` 網址寫錯

### 403 但讀取工具正常

客製擴充的**存取範疇**沒給寫入權限。回步驟 1 調整範疇後儲存。

### 寫入工具沒出現

`ENABLE_WRITE_TOOLS` 沒設成 `true`，或設了之後沒重啟 MCP server。啟動訊息會顯示目前狀態，`easystore_diagnose` 的 `tools.write_tools_loaded` 也會直接告訴你載入了幾個。

注意這與 EasyStore 後台的**存取範疇**是兩層獨立開關：`ENABLE_WRITE_TOOLS=true` 但範疇沒給寫入權限，工具會出現、呼叫時回 403。

### Cowork 裡看不到 `easystore_*`

設定多半只寫進了 `~/.claude.json`（`claude mcp add` 寫的那份）。Cowork 讀的是 `claude_desktop_config.json`——那是 Claude Desktop 的設定檔，兩份是分開的。照「Claude Cowork 與 Claude Desktop 一般聊天」那節補寫，然後 Cmd+Q 完全結束 Desktop 再開。

---

## 安全性

- 權杖只放在 `~/.claude.json`、shell 環境變數或 `.env.local`，三者都不進版控
- `.env.example` 是範本，永遠不填真值
- 權杖曾經出現在終端輸出、log 或截圖 → 回後台重新產生
