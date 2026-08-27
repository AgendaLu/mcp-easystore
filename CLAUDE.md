# mcp-easystore

EasyStore 電商平台的 MCP 伺服器。提供 **59 個讀取工具 + 41 個寫入工具**給 Claude，讓 LLM 能透過自然語言查詢訂單、商品、客戶、營收等資料，並可執行取消訂單、退款、顧客分群等寫入操作。重點目標：**token 使用效率優化**。

## 專案結構速覽

```
pyproject.toml       # 打包設定（entry point: mcp-easystore）
.mcp.json            # 開發用 MCP 註冊設定（走本地 venv）
mcp_easystore/       # 套件本體
  ├── server.py        入口（stdio JSON-RPC，main() 為 console script）
  ├── config/settings.py  環境變數、API 設定
  └── tools/           MCP 工具（按資源域分檔）
  ├── base_tool.py     共用 HTTP client（GET / POST / PUT / DELETE）
  ├── tool_registry.py 統一註冊（讀寫分離）
  ├── analytics_tools.py / order_tools.py / product_tools.py
  ├── customer_tools.py / settings_tools.py / storefront_tools.py
  └── writes/          寫入工具（ENABLE_WRITE_TOOLS=true 才載入）
        ├── order_writes.py     訂單操作（6 個）
        ├── customer_writes.py  顧客與分群（9 個）
        ├── product_writes.py   商品與分類（8 個）
        ├── storefront_writes.py 前台內容（9 個）
        └── settings_writes.py  系統設定（9 個）
scripts/             # 連線測試、優化驗證腳本
tests/               # 單元測試
docs/                # 文件（見下方）
```

完整結構與工具端點對照：[docs/architecture/project-structure.md](docs/architecture/project-structure.md)

## 文件分類

- `docs/setup/` — 安裝設定指南：權杖取得、MCP 註冊、故障排除（**新人從這裡開始**）
- `docs/api-reference/` — EasyStore / Shopline API 端點清單
- `docs/architecture/` — 專案結構
- `docs/optimization/` — 規劃中的優化（分析、checklist、實施指南）
- `docs/archive/` — 已完成的優化結果與驗證報告（歷史紀錄）

> 規則：規劃中→`optimization/`，完成後→搬到 `archive/`。

## 開發慣例

- **語言**：Python 3.12
- **MCP framework**：官方 `mcp` SDK 內建的 `mcp.server.fastmcp.FastMCP`（不是獨立的 `fastmcp` 套件）
- **環境變數**：由 MCP client 注入（`.mcp.json` / `claude mcp add`）；`config/settings.py` 只讀 `os.environ` 與 `.env`。`.env` 是給 `scripts/`、`tests/` 的獨立腳本用的。設定說明見 [docs/setup/setup-guide.md](docs/setup/setup-guide.md)
- **寫入工具**：預設不載入。需 `ENABLE_WRITE_TOOLS=true` 才會註冊（避免誤操作）。
- **工具命名**：`easystore_<verb>_<resource>`，例如 `easystore_list_orders`、`easystore_get_revenue_summary`。
- **Token 優化**：新增/修改工具時，優先考慮 `fields` 參數縮減 response 大小（見 `docs/optimization/implementation-guide.md`）。
- **寫入工具安全慣例**：刪除類操作需 `confirm=true` 參數；不可逆操作在 docstring 標示 ⚠️。

## 常用指令

```bash
# 啟動 MCP server
./scripts/start_mcp.sh

# 環境檢查
python scripts/check_env.py

# API 連線測試
python scripts/auth/test_connection.py

# 跑測試
python -m pytest tests/
```

## 注意

- `SKILL.md` 是 Claude skill 定義（`easystore-analyst`），不是一般文件。
- `mcp_easystore/server.py` 由 MCP 客戶端透過 stdio 啟動，不是直接執行的 CLI。
- 使用者端安裝走 `uvx --from git+…`，不需要 clone 或建 venv；開發時才用 `pip install -e ".[dev]"`。
