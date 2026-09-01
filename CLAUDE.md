# mcp-easystore

EasyStore 電商平台的 MCP 伺服器。提供 **60 個讀取工具 + 41 個寫入工具**給 Claude，讓 LLM 能透過自然語言查詢訂單、商品、客戶、營收等資料，並可執行取消訂單、退款、顧客分群等寫入操作。重點目標：**token 使用效率優化**。

## 專案結構速覽

```
pyproject.toml           # 打包設定（entry point: mcp-easystore）
.mcp.json                # 開發用 MCP 註冊設定（走本地 venv）
mcp_easystore/           # 套件本體（uvx 安裝的就是這包）
  ├── server.py            入口（stdio JSON-RPC；main() 為 console script）
  ├── config/settings.py   環境變數、API 設定
  └── tools/               MCP 工具（按資源域分檔）
        ├── base_tool.py       共用 HTTP client（GET / POST / PUT / DELETE）
        ├── tool_registry.py   統一註冊（讀寫分離，數量由實際註冊狀態計算）
        ├── diagnostics_tools.py（1）  easystore_diagnose：生效設定 + 連線自檢
        ├── analytics_tools.py（11）/ order_tools.py（8）/ product_tools.py（9）
        ├── customer_tools.py（10）/ settings_tools.py（14）/ storefront_tools.py（7）
        └── writes/            寫入工具（ENABLE_WRITE_TOOLS=true 才載入）
              ├── order_writes.py      訂單操作（6 個）
              ├── customer_writes.py   顧客與分群（9 個）
              ├── product_writes.py    商品與分類（8 個）
              ├── storefront_writes.py 前台內容（9 個）
              └── settings_writes.py   系統設定（9 個）
scripts/                 # 連線測試、優化驗證腳本（需開發安裝）
tests/                   # 單元測試
docs/                    # 文件（見下方）
```

完整結構與工具端點對照：[docs/architecture/project-structure.md](docs/architecture/project-structure.md)

## 使用者怎麼裝、怎麼查（被問到時照這個回答）

**兩份設定涵蓋四個介面**，不要只講其中一份：

| 設定檔 | 涵蓋的介面 | 怎麼寫 |
|---|---|---|
| `~/.claude.json` | terminal 的 `claude` 指令、Claude Code | `claude mcp add easystore --scope local -e ... -- uvx --from git+… mcp-easystore` |
| `claude_desktop_config.json` | Claude Desktop 一般聊天、**Claude Cowork** | 手動編輯，併進既有 `mcpServers` |

Cowork 沒有自己的 MCP 設定介面，用的是 Desktop 已註冊的本機 server——「Cowork 看不到工具」的答案幾乎都是「設定只寫進了 `~/.claude.json`」。claude.ai 網頁版／手機版不支援（需要公網可達的遠端 MCP）。

**`EASYSTORE_SHOP_URL` 的正確值**是 `/store.json` 回應裡的 `easystore_domain`（例如 `https://yourshop.easy.co`）。`easystore.co` 是 EasyStore 官網，不是店家網域。

**排查一律從 `easystore_diagnose` 開始**，不要用猜的——它回報生效的商店網址、每個變數的來源、權杖指紋（無明文）、載入工具數，並實打一次 `/store.json`。症狀對照：404 → shop URL 指向不存在的商店（錯誤訊息尾端有實際請求的 URL）；401 → 權杖；讀取正常但寫入 403 → 後台存取範疇；改了設定沒反應 → 看 `config.sources` 確認改到的是不是生效的那份。

完整流程見 [README.md](README.md) 的「快速開始」與「出錯了怎麼查」，細節見 [docs/setup/setup-guide.md](docs/setup/setup-guide.md)。

## 文件分類

- `docs/setup/` — 安裝設定指南：權杖取得、MCP 註冊、故障排除（**新人從這裡開始**）
- `docs/api-reference/` — EasyStore / Shopline API 端點清單
- `docs/architecture/` — 專案結構
- `docs/optimization/` — 規劃中的優化（分析、checklist、實施指南）
- `docs/archive/` — 已完成的優化結果與驗證報告（歷史紀錄）

> 規則：規劃中→`optimization/`，完成後→搬到 `archive/`。

## 開發慣例

- **語言**：Python 3.10+（`pyproject.toml` 的 `requires-python`；開發環境為 3.12）
- **MCP framework**：官方 `mcp` SDK 內建的 `mcp.server.fastmcp.FastMCP`（不是獨立的 `fastmcp` 套件）。依賴鎖 `mcp>=1.2,<2`——2.x 已把 `FastMCP` 更名為 `MCPServer` 並移除舊 import 路徑
- **打包**：hatchling。console script `mcp-easystore` → `mcp_easystore.server:main`。使用者端走 `uvx --from git+…`，不需要 clone 或建 venv
- **環境變數**：由 MCP client 注入（`.mcp.json` / `claude mcp add`）；`mcp_easystore/config/settings.py` 只讀 `os.environ` 與 `.env` / `.env.local`（搜尋工作目錄與**套件所在的專案根目錄**；uvx 安裝時程式在 site-packages，那裡不會有 `.env`）。有值的環境變數永遠優先，檔案只補空缺；空值與未展開的 `${VAR}` 佔位字串一律視為未設定。排查設定用 `easystore_diagnose` 工具或 `settings.describe_config()`，別用猜的。設定說明見 [docs/setup/setup-guide.md](docs/setup/setup-guide.md)
- **寫入工具**：預設不載入。需 `ENABLE_WRITE_TOOLS=true` 才會註冊（避免誤操作）。
- **工具命名**：`easystore_<verb>_<resource>`，例如 `easystore_list_orders`、`easystore_get_revenue_summary`。
- **Token 優化**：新增/修改工具時，優先考慮 `fields` 參數縮減 response 大小（見 `docs/optimization/implementation-guide.md`）。
- **寫入工具安全慣例**：刪除類操作需 `confirm=true` 參數；不可逆操作在 docstring 標示 ⚠️。

## 常用指令

```bash
# 開發安裝（editable + 開發依賴）
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# 跑測試
.venv/bin/python -m pytest tests/

# 環境檢查（顯示 MCP server 實際會讀到的值）
.venv/bin/python scripts/check_env.py

# API 連線測試
.venv/bin/python scripts/auth/test_connection.py

# 直接啟動 server（平常由 MCP client 啟動，除錯才手動跑）
.venv/bin/python -m mcp_easystore.server
```

使用者端不需要以上任何一步，只要裝 uv 後用 `uvx --from git+https://github.com/AgendaLu/mcp-easystore mcp-easystore`。

## 測試守則

`tests/` 有幾組把文件與程式綁在一起的測試，改動時會擋下不一致：

- `test_packaging.py` — AST 掃描所有 import 目標，**包含縮排在函式內的**（那種 import 載入模組時不會執行，改路徑時最容易漏）
- `test_docs.py` — README / CLAUDE.md 的工具數量與清單必須與實際註冊一致
- `test_tool_registry.py` — 回報數量必須等於實際註冊數量；工具命名與唯一性

新增或刪除工具後，README 的分類表與總數要一起改，否則 `test_docs.py` 會紅。

## 注意

- `SKILL.md` 是 Claude skill 定義（`easystore-analyst`），不是一般文件。
- `mcp_easystore/server.py` 由 MCP 客戶端透過 stdio 啟動，不是直接執行的 CLI。
- 使用者端安裝走 `uvx --from git+…`，不需要 clone 或建 venv；開發時才用 `pip install -e ".[dev]"`。
