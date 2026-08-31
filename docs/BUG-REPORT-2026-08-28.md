# 使用者錯誤回報：一個填錯的商店網址，花了一小時才定位

**回報日期**：2026-08-28
**回報情境**：透過 Claude Desktop 的 MCP bridge，在 Cowork 中使用 `easystore_*` 工具
**商店**：花石間（`glamglow.easy.co`）
**mcp SDK**：1.27.0

---

## TL;DR

根因是**設定值填錯**——桌面版設定檔指向一個已不存在的商店。這本身是五秒鐘的問題。

但它花了一小時，因為 repo 有四個設計缺陷把它偽裝成別的東西：錯誤被靜靜吞成 `0`、無法得知哪份設定生效、404 訊息把人導向錯誤方向、`.env` 的 fallback 實際上從不生效。

**設定問題我已自行解決，不需要處理。本報告要求修的是那四個缺陷。**

---

## 症狀

1. 所有唯讀工具回 404：

   ```
   easystore_get_store_info      → [store] Error 404: 資源不存在，請確認 ID 或路徑是否正確。
   easystore_list_orders         → [orders] Error 404: ...
   easystore_list_products       → [products] Error 404: ...
   easystore_list_collections    → [collections] Error 404: ...
   easystore_list_customers      → [customers] Error 404: ...
   ```

2. **但 summary 類工具回報「一切正常，只是沒有資料」**：

   ```json
   // easystore_get_order_summary({"days": 30})
   { "total_orders": 0, "by_status": { "open": 0, "cancelled": 0, "archived": 0 } }

   // easystore_get_financial_status_summary({"days": 365})
   { "financial_status_distribution": { "paid": 0, "pending": 0, "unpaid": 0,
                                        "refunded": 0, "voided": 0, "cod": 0 } }
   ```

   實際上這是 5 次與 6 次連續 404 的結果。該商店有 **187 筆訂單**。

---

## 根因（已確認，不需修）

`~/Library/Application Support/Claude/claude_desktop_config.json` 中的
`EASYSTORE_SHOP_URL` 是 `https://dressup12.easy.co`——該商店在 EasyStore 已不存在。

以 stdlib 直接打 API 驗證：

| 商店 | `/store.json` | `/orders.json` |
|---|---|---|
| `dressup12.easy.co` | 404 | 404 |
| `glamglow.easy.co` | **200**（花石間） | **200**（187 筆） |

改成 `glamglow.easy.co` 後所有工具恢復正常，程式碼一行未改。

---

## 要修的問題

### P0-1　API 錯誤被吞成 `0`

**檔案**：`mcp_easystore/tools/analytics_tools.py`

| 行號 | 所屬工具 |
|---|---|
| 106 | `easystore_get_order_summary` |
| 191 | `easystore_get_fulfillment_status_summary` |
| 225 | `easystore_get_financial_status_summary` |
| 280, 281 | `easystore_get_product_inventory_summary` |

```python
data = await api_get("orders", q)
results[status] = data.get("total_count", 0) if isinstance(data, dict) else 0
#                                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# api_get 失敗時回傳「錯誤字串」→ 非 dict → 直接記成 0
```

**為什麼是 P0**：這不是回傳錯誤，是**回傳一個看起來正確的假答案**。今天是設定錯，一眼看得出來；下次是 token 過期、429 限流、或某個 scope 被關掉，使用者會拿到一份「本月營收 0」的報表，然後相信它。

同檔案的 `fetch_all_pages`（`base_tool.py:157`）做法是對的，可作為範本：

```python
if isinstance(data, str):   # 錯誤訊息
    return data
```

**要求**：任何一次 `api_get` 失敗就中止並把錯誤往上回傳，不要用預設值填補。`SKILL.md` 第五節寫「資料不完整就說出來」，這五行正在做相反的事。

---

### P0-2　無法得知「現在生效的是哪份設定」

同一組環境變數散落在四個地方，優先級沒有任何地方說明，也沒有工具能查：

| 來源 | 實際內容 | 狀態 |
|---|---|---|
| `claude_desktop_config.json` | `dressup12.easy.co` | ← 實際生效（找了一小時才確定） |
| `.env` | `dressup12.easy.co` | 從未被讀取（見 P1-4） |
| `.claude/settings.local.json` | `glamglow.easy.co` | `args` 指向不存在的 `mcp_server.py` |
| `.mcp.json` | `${VAR:-}` 佔位 | 展開為空後被 `_drop_blank_env` 丟棄 |

`scripts/auth/test_connection.py` 做的正是對的事（印出 shop URL、base URL、實打一次 `/store.json`），但它讀的是 `.env`，而 MCP server 跑的是桌面版設定——**測的是另一份設定**。

**要求**：新增唯讀工具 `easystore_diagnose`，無參數，回傳：

- 生效的 `EASYSTORE_SHOP_URL`
- 完整 base URL（`get_base_url()`）
- token **指紋**（長度 + sha1 前 8 碼）——**絕對不可回傳 token 本身**
- `ENABLE_WRITE_TOOLS` 狀態與已載入的寫入工具數量
- `Path.cwd()`，以及 `.env` / `.env.local` 是否真的被讀到
- 對 `/store.json` 實打一次，回傳 HTTP 狀態碼與商店名稱

這樣任何「怎麼抓不到資料」的問題，第一步就有答案。

---

### P1-3　404 訊息誤導，且不顯示實際 URL

**檔案**：`mcp_easystore/tools/base_tool.py:33`

```python
if status == 404:
    return f"{prefix}Error 404: 資源不存在，請確認 ID 或路徑是否正確。"
```

「請確認路徑是否正確」把人推去懷疑 API 路徑寫錯。實際原因是**商店本身不存在**。訊息裡也沒有印出實際打的 URL，所以看不到自己正在打 `dressup12`。

**要求**：

1. 所有錯誤訊息帶上實際請求的 URL（`base_tool.py` 有 5 處組 URL：行 61、81、98、113、128）
2. 404 的文案改為同時點出兩種可能：「商店不存在或已停用」與「路徑／ID 錯誤」
3. 若 URL 中含 token 等敏感值需先遮蔽（目前 token 走 header，應該安全，請確認）

---

### P1-4　`.env` 的 fallback 依賴 cwd，實務上永不生效

**檔案**：`mcp_easystore/config/settings.py:51`

```python
root_dir = Path.cwd()          # ← MCP server 由 client 啟動時，cwd 不是 repo 根目錄
env_file = root_dir / ".env"
```

我在排查時改了 `.env` 並重啟，行為完全沒變——因為那個檔案從頭到尾沒被讀過。docstring 有提到這件事，但寫成描述而非警告，讀起來像「設計如此」。

**要求**（擇一，請在 PR 說明選擇理由）：

- **A**：改為以套件位置回推 repo 根目錄（`Path(__file__).resolve().parents[2]`），讓 fallback 真的可用
- **B**：明確移除 `.env` fallback，並在 `validate_config()` 失敗訊息中講清楚「本 server 只讀 client 注入的環境變數」

**不要維持現狀**——一個看起來存在、實際不會生效的 fallback，比沒有更糟。

---

### P2-5　殘留設定與過期文件

1. `.claude/settings.local.json` 的 `args` 是 `["mcp_server.py"]`，全 repo 無此檔案，正確入口是 `mcp_easystore/server.py`。此設定照著啟動必定失敗。
2. 文件與範本一律寫 `https://yourshop.easystore.co`，但實際商店網域是 `.easy.co`。位置：`server.py:9`、`settings.py:86`、`.env.example:11`、`README.md:42,64`、`docs/setup/setup-guide.md:54,85,174,255-256`、`docs/optimization/order-tools-checklist.md:71`、`docs/optimization/tool-type-audit.md:376`。

   **注意**：`.easy.co` 是有效的 API 網域（已實測 200）。這裡要修的是「範本容易誤導」，不是網域寫錯。建議範本改成 `https://<yourshop>.easy.co`，或兩種格式都列出並說明。

3. `docs/setup/setup-guide.md` 應新增一節「設定優先級」，明列四個來源與誰蓋過誰。

---

## 驗收標準

- [ ] 把 `EASYSTORE_SHOP_URL` 改成一個不存在的商店，`easystore_get_order_summary` 必須回傳**錯誤**，不得回傳 `total_orders: 0`
- [ ] 同上，`get_financial_status_summary`、`get_fulfillment_status_summary`、`get_product_inventory_summary` 皆須回傳錯誤
- [ ] `easystore_diagnose` 能正確指出當前生效的 shop URL，且輸出中不含 token 明文
- [ ] 404 錯誤訊息含實際請求 URL
- [ ] 針對「api_get 回傳錯誤字串」新增單元測試，涵蓋上述四個 summary 工具
- [ ] 設定正確時，`easystore_get_order_summary({"days": 365})` 對花石間回傳非 0 訂單數

---

## 請不要做的事

- **不要修改任何設定檔中的 token 或商店網址**——設定問題已解決，動它只會再次打壞
- **不要改 `ENABLE_WRITE_TOOLS` 的預設值**（目前 `false`），也不要在本次一併調整寫入工具的行為
- **不要重構工具註冊架構**（`tool_registry.py`）——本報告的範圍只有錯誤處理、診斷能力與文件
- **不要刪除 `scripts/auth/test_connection.py`**，它是對的，只是測錯對象；可考慮讓它改用與 `easystore_diagnose` 相同的邏輯

---

## 附錄：排查過程中被誤導的兩個環節

留作參考，說明這些缺陷實際造成的成本。

1. 因為 404 訊息說「請確認路徑」，最初推論是 `.easy.co` 與 `.easystore.co` 網域寫錯——**這個推論是錯的**，`.easy.co` 完全有效。是文件範本清一色寫 `easystore.co` 強化了這個誤判。
2. 因為 `get_order_summary` 回報 0 筆，一度以為「連得上、只是沒資料」，往錯誤方向查了一輪。直到 `list_orders` 回 404、而 summary 回 0，兩者矛盾，才發現錯誤被吞掉。
