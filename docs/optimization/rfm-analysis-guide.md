# RFM 顧客分眾分析指南

## 什麼是 RFM？

RFM 是行銷常用的顧客分群模型，透過三個維度評估每位顧客的價值：

| 維度 | 說明 | 計算方式 |
|------|------|---------|
| **R（Recency）最近購買** | 最後一次購買距今幾天 | 天數越少 → 分數越高 |
| **F（Frequency）購買頻率** | 分析期間內的購買次數 | 次數越多 → 分數越高 |
| **M（Monetary）消費金額** | 分析期間內的累計消費 | 金額越高 → 分數越高 |

### 典型分群標籤

| 分群 | R | F | M | 行銷策略 |
|------|---|---|---|---------|
| 冠軍顧客 | 高 | 高 | 高 | VIP 專屬優惠、新品優先體驗 |
| 忠誠顧客 | 中高 | 高 | 中高 | 會員升等、感謝方案 |
| 潛力顧客 | 高 | 低 | 中 | 引導第二次購買、推薦相關商品 |
| 新顧客 | 高 | 1 | 任意 | 歡迎序列、新手禮包 |
| 需喚回顧客 | 低 | 中 | 中 | 「好久不見」優惠碼 |
| 流失顧客 | 很低 | 低 | 低 | 最後挽留、或停止投放 |

---

## 查詢流程（四步驟低 Token 策略）

> **核心原則**：先評估規模，再分頁取回，避免一次拉回大量資料。

### Step 1：確認店家設定（1 次 API）

```
工具：easystore_get_store_info
用途：確認時區與貨幣，確保日期計算與金額顯示正確
Token 消耗：~200
```

### Step 2：評估訂單規模（1 次 API）

```
工具：easystore_get_order_summary
參數：days=180（或自訂 date_from / date_to）
用途：確認總訂單數，決定需要幾頁
Token 消耗：~150

⚠️ 若 total_orders > 2000，建議縮短時間範圍（例如改用 days=90）
   以免 API 呼叫次數過多（每頁 50 筆 = 40+ 次呼叫）
```

### Step 3：分頁取回訂單（N 次 API）

```
工具：easystore_get_rfm_orders
參數：
  days=180                  ← 分析時間範圍
  limit=100                 ← 每頁筆數（預設 100，最大 250）
  page=1, 2, 3...           ← 逐頁取回，直到 page >= page_count

Token 消耗：每頁約 500–800 tokens（相比完整欄位節省 ~86%）
```

**重要**：`easystore_get_rfm_orders` 已固定只回傳 RFM 所需的 5 個欄位（`id`、`customer_id`、`customer_email`、`total_price`、`created_at`），並透過 API `fields` 參數減少網路傳輸量，**不需要**也**不應改用** `easystore_list_orders`。

### Step 4：Claude 端彙總計算（0 次 API）

以 `customer_id` 為 key，從所有分頁結果彙總：

```python
# 彙總邏輯（概念）
customer_stats = {}
for order in all_orders:
    cid = order["customer_id"]
    if cid not in customer_stats:
        customer_stats[cid] = {
            "last_order_date": order["created_at"],
            "order_count": 0,
            "total_spent": 0.0
        }
    else:
        if order["created_at"] > customer_stats[cid]["last_order_date"]:
            customer_stats[cid]["last_order_date"] = order["created_at"]
    customer_stats[cid]["order_count"] += 1
    customer_stats[cid]["total_spent"] += float(order["total_price"])
```

計算 R/F/M 分數（各維度 1–5 分，用五分位數分組）：

- **R 分數**：距今天數，最近 → 5 分，最遠 → 1 分
- **F 分數**：購買次數，最多 → 5 分，最少 → 1 分
- **M 分數**：消費金額，最高 → 5 分，最低 → 1 分

---

## Token 消耗估算

| 訂單規模 | 頁數（limit=100）| 預估 token | 完整欄位對比 | 節省比例 |
|---------|------|-----------|------------|---------|
| 500 筆（5 頁） | 5 次 | ~5,000 | ~60,000 | **92%** |
| 1,000 筆（10 頁） | 10 次 | ~10,000 | ~120,000 | **92%** |
| 2,000 筆（20 頁） | 20 次 | ~20,000 | ~240,000 | **92%** |

> 節省來源：`easystore_get_rfm_orders` 透過 API `fields` 參數只取 5 個欄位，並在 Claude 端進一步過濾，相比完整欄位回傳節省 ~86% token；limit=100 再將 API 呼叫次數減半。

---

## 完整 Prompt 範例

```
請幫我做 RFM 顧客分析，分析過去 180 天的付費訂單。

步驟：
1. 先呼叫 easystore_get_store_info 確認幣別
2. 呼叫 easystore_get_order_summary(days=180) 確認總訂單數
3. 分頁呼叫 easystore_get_rfm_orders(days=180, limit=100)
   直到 page >= page_count
4. 彙總每位顧客的：最後購買日期、購買次數、累計消費金額
5. 依 R/F/M 各打 1–5 分，分成以下群組並統計人數：
   - 冠軍顧客（R≥4, F≥4, M≥4）
   - 忠誠顧客（F≥3, M≥3）
   - 潛力顧客（R≥4, F≤2）
   - 需喚回顧客（R≤2, F≥2）
   - 流失顧客（R=1, F=1）
6. 輸出分群人數表格，並給出行銷建議
```

---

## 常見問題

**Q：為什麼不用 `easystore_get_revenue_summary`？**
A：該工具只能取得整體營收，無法區分個別顧客的消費金額。RFM 需要「每位顧客」的資料。

**Q：訂單沒有 `customer_id` 怎麼辦？**
A：訪客結帳（Guest Checkout）的訂單不會有 `customer_id`，可以用 `customer_email` 作為替代識別鍵，或直接跳過這些訂單。

**Q：如果要查詢特定分群顧客的詳細資料？**
A：先完成 RFM 分群取得 `customer_id` 列表，再用 `easystore_list_customers(ids="id1,id2,...")` 批次查詢，避免逐一呼叫 `easystore_get_customer`。
