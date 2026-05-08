# EasyStore Storefront API 3.0 — Endpoint Inventory

> **Base URL** `https://{shop}/api/3.0/`  
> **Auth Header** `EasyStore-Access-Token: {token}`  
> **Version** Storefront API 3.0  
> **Source** Postman Collection（匯出日期：2026-05-06）

## ⚠️ Known Issues（文件異常紀錄）

> [!WARNING]
> 以下問題已從 Postman collection 原始資料中發現，整理時保留原路徑，待工程確認後修正。

| # | 問題 | 受影響路徑 |
|---|------|-----------|
| 1 | 路徑缺少 `/api` 前綴（其他 endpoint 均有） | `GET /3.0/customers/:customer_id.json` |
| 2 | 同上，且 path variable 拼錯（`coode`） | `GET /3.0/customers/:customer_id_or_coode/points.json` |
| 3 | Vouchers 兩支 endpoint 標記為 Coming soon，尚未正式開放 | `/customers/:id/vouchers.json` |

## Resource Summary

> 共 **24 個資源群組**，**134 支 endpoints**。

| # | Resource | Required Scope | Endpoints |
|---|----------|---------------|:---------:|
| 1 | [Auth](#auth) | — | 2 |
| 2 | [Store](#store) | — | 1 |
| 3 | [Checkouts](#checkouts) | — | 4 |
| 4 | [Products](#products) | `read_products / write_products` | 13 |
| 5 | [Images](#images) | `read_products / write_products` | 4 |
| 6 | [Collections](#collections) | `read_products / write_products` | 5 |
| 7 | [Collects](#collects) | `read_products / write_products` | 5 |
| 8 | [Orders](#orders) | `read_orders / write_orders` | 8 |
| 9 | [Fulfillments](#fulfillments) | `read_fulfillments / write_fulfillments` | 5 |
| 10 | [Transactions](#transactions) | `read_orders / write_orders` | 3 |
| 11 | [Curls](#curls) | — | 6 |
| 12 | [Customers](#customers) | `read_customers / write_customers` | 12 |
| 13 | [Customer Addresses](#customer-addresses) | `read_customers / write_customers` | 6 |
| 14 | [Customer Custom Attributes](#customer-custom-attributes) | `read_customer_attributes / write_customer_attributes` | 5 |
| 15 | [Locations](#locations) | `read_shipping / write_locations` | 4 |
| 16 | [Gateways](#gateways) | — | 2 |
| 17 | [Groups](#groups) | `read_customers / write_customers` | 9 |
| 18 | [Metafields](#metafields) | — | 6 |
| 19 | [Snippets](#snippets) | `read_snippets / write_snippets` | 6 |
| 20 | [Script Tags](#script-tags) | `read_script_tags / write_script_tags` | 6 |
| 21 | [Pages](#pages) | `read_content / write_content` | 5 |
| 22 | [Navigations](#navigations) | `read_content / write_content` | 6 |
| 23 | [Redirects](#redirects) | — | 5 |
| 24 | [Webhooks](#webhooks) | — | 6 |

---

## Auth

> 取得及更新 OAuth Access Token

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `POST` | `/api/3.0/oauth/access_token.json` | Request access token | — | code, client_id, client_secret |
| `POST` | `/oauth/token` | Renew access token | — | refresh_token |

---

## Store

> 讀取商店基本設定（名稱、幣別、時區、網域）

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/store.json` | Retrieve the store configuration | — | — |

---

## Checkouts

> 管理購物車結帳流程

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/checkouts.json` | Retrieve a list of checkouts | page, limit, sort, ids, collection_ids, skus, since_id, visibility, published_at_min/max, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/checkouts/:cart_token.json` | Retrieve a single checkout | — | — |
| `POST` | `/api/3.0/checkouts.json` | Create a checkout | — | checkout: { presentment_currency, line_items[ {variant_id, quantity, price} ] } |
| `PUT` | `/api/3.0/checkouts/:cart_token.json` | Update a checkout | — | checkout: { presentment_currency, line_items, … } |

---

## Products

> 商品 CRUD 及規格、選項管理

> [!NOTE]
> **Required Scope** `read_products / write_products`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/products.json` | Retrieve a list of products | page, limit, sort, ids, collection_ids, skus, since_id, visibility, published_at_min/max, created_at_min/max, updated_at_min/max, is_bundle | — |
| `GET` | `/api/3.0/products/:product_id.json` | Retrieve a single product | — | — |
| `POST` | `/api/3.0/products.json` | Create a new product | — | product: { title, description, body_html, taxable, shipping_required, variant_types, variants, images, collections, published_at } |
| `PUT` | `/api/3.0/products/:product_id.json` | Update an existing product | — | product: { title, description, body_html, inventory_management, images, collections, published_at } |
| `DELETE` | `/api/3.0/products/:product_id.json` | Delete a product | — | — |

### Variant

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/products/:product_id/variants.json` | Retrieve variants of a product | — | — |
| `GET` | `/api/3.0/products/:product_id/variants/:variant_id.json` | Retrieve a single variant | — | — |
| `PUT` | `/api/3.0/products/:product_id/variants.json` | Update existing variants (bulk) | — | variants[]: { id, name, sku, price, compare_at_price, inventory_quantity, … } |

### Opti

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `POST` | `/api/3.0/products/:product_id/options.json` | Create new variant options | — | { option_type, option_values[] } |
| `PUT` | `/api/3.0/products/:product_id/options.json` | Update existing variant options | — | { variant_options[ {name, options[]} ] } |
| `DELETE` | `/api/3.0/products/:product_id/options.json` | Delete option type or value | — | { option_type [, option_value] } |

### Option Type

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `PUT` | `/api/3.0/products/:product_id/option_type.json` | Rename an option type | — | { old_option_type, new_option_type } |

### Option Value

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `PUT` | `/api/3.0/products/:product_id/option_value.json` | Rename an option value | — | { option_type, old_option_value, new_option_value } |

---

## Images

> 商品圖片管理

> [!NOTE]
> **Required Scope** `read_products / write_products`

### Image

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/products/:product_id/images.json` | Retrieve a list of images for a product | — | — |
| `GET` | `/api/3.0/products/:product_id/images/:image_id.json` | Retrieve a single image | — | — |
| `POST` | `/api/3.0/products/:product_id/images.json` | Add images to a product | — | { images: ["url1", "url2"] } |
| `DELETE` | `/api/3.0/products/:product_id/images.json` | Delete images of a product | — | { image_ids: "id1,id2" } |

---

## Collections

> 商品分類管理

> [!NOTE]
> **Required Scope** `read_products / write_products`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/collections.json` | Retrieve a list of collections | page, limit, sort, ids, since_id, visibility, published_at_min/max, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/collections/:collection_id.json` | Retrieve a single collection | — | — |
| `POST` | `/api/3.0/collections.json` | Create a new collection | — | collection: { name, metafields_global_title_tag } |
| `PUT` | `/api/3.0/collections/:collection_id.json` | Update an existing collection | — | collection: { name, handle, description, metafields_global_title_tag, metafields_global_description_tag } |
| `DELETE` | `/api/3.0/collections/:collection_id.json` | Delete a collection | — | — |

---

## Collects

> 商品與分類的關聯（product ↔ collection mapping）

> [!NOTE]
> **Required Scope** `read_products / write_products`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/collects.json` | Retrieve a list of collects | page, limit, sort, ids, since_id, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/collects/count.json` | Retrieve collects count | — | — |
| `GET` | `/api/3.0/collects/:collect_id.json` | Retrieve a single collect | — | — |
| `POST` | `/api/3.0/collects.json` | Create a new collect | — | collect: { product_id, collection_id } |
| `DELETE` | `/api/3.0/collects/:collect_id.json` | Delete a collect | — | — |

---

## Orders

> 訂單 CRUD、取消、退款管理

> [!NOTE]
> **Required Scope** `read_orders / write_orders`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/orders.json` | Retrieve a list of orders | page, limit, sort, ids, since_id, financial_status, fulfillment_status, status, source_type, attribution_location_id, processed_at_min/max, created_at_min/max, updated_at_min/max, last_transaction_at_min/max, customer_id, fields | — |
| `GET` | `/api/3.0/orders/:order_id.json` | Retrieve a single order | fields: items, addresses, note_attributes, transactions, fulfillments, refunds, taxes, customer, shipping_fees, metafields, discounts, points, fulfillment_orders, cancellation, referral | — |
| `POST` | `/api/3.0/orders.json` | Create a new order | — | order: { currency_code, line_items[], cod_type, shipping_address, billing_address, remark, note } |
| `PUT` | `/api/3.0/orders/:order_id.json` | Update an existing order | — | order: { currency_code, line_items[], shipping_address, billing_address } |
| `DELETE` | `/api/3.0/orders/:order_id.json` | Delete an order | — | — |

### Cancel

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `POST` | `/api/3.0/orders/:order_id/cancel.json` | Cancel an order | — | { reason } |

### Refund

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `POST` | `/api/3.0/orders/:order_id/refund.json` | Refund an order | — | { amount, type, note, restock_items[], reference_number, transaction_id } |

### Cancel Refund

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `PUT` | `/api/3.0/orders/:order_id/cancel_refund/:refund_id/cancel.json` | Cancel a refund | — | { is_revert_restock } |

---

## Fulfillments

> 訂單物流出貨管理

> [!NOTE]
> **Required Scope** `read_fulfillments / write_fulfillments`

### Fulfillment

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/orders/:order_id/fulfillments.json` | Retrieve a list of fulfillments | status, tracking_number, is_cancelled, ids, sort, service, tracking_company | — |
| `GET` | `/api/3.0/orders/:order_id/fulfillments/:fulfillment_id.json` | Retrieve a single fulfillment | — | — |
| `POST` | `/api/3.0/orders/:order_id/fulfillments.json` | Create a new fulfillment | — | { tracking_company, tracking_number, tracking_url, status, service, message, is_mail, consignment_note_url, line_items[{id, quantity}] } |
| `PUT` | `/api/3.0/orders/:order_id/fulfillments/:fulfillment_id.json` | Update an existing fulfillment | — | { courier, tracking_number, tracking_url, status, service, message, consignment_note_url } |
| `POST` | `/api/3.0/orders/:order_id/fulfillments/:fulfillment_id/cancel.json` | Cancel a fulfillment | — | — |

---

## Transactions

> 訂單付款交易紀錄

> [!NOTE]
> **Required Scope** `read_orders / write_orders`

### Transacti

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/orders/:order_id/transactions.json` | Retrieve a list of transactions | — | — |
| `GET` | `/api/3.0/orders/:order_id/transactions/:transaction_id.json` | Retrieve a single transaction | — | — |
| `POST` | `/api/3.0/orders/:order_id/transactions.json` | Create a transaction | — | transaction: { currency, amount, status, gateway: { type, title, method } } |

---

## Curls

> Logistic App 的 callback URL 設定（shipping / pickup / external）

> [!TIP]
> 「Curls」並非 HTTP curl 工具，而是 EasyStore 內部對 Logistic App callback endpoint 設定的命名。

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/curls.json` | Retrieve a list of curls | limit, page, since_id, created_at_min/max, updated_at_min/max, sort | — |
| `GET` | `/api/3.0/curls/:curl_id.json` | Retrieve a single curl | — | — |
| `GET` | `/api/3.0/curls/count.json` | Count total of curls | — | — |
| `POST` | `/api/3.0/curls.json` | Create curl | — | curl: { url, topic }<br>topic 可為：shipping/list/cod, shipping/list/non_cod, pickup/locations/list, pickup/methods/list, pos/pickup/methods/list, external/customer/get, pickup/verify |
| `PUT` | `/api/3.0/curls/:curl_id.json` | Update curl | — | curl: { url, topic } |
| `DELETE` | `/api/3.0/curls/:curl_id.json` | Delete curl | — | — |

---

## Customers

> 會員 CRUD、搜尋，以及積分、儲值金、優惠券子資源

> [!NOTE]
> **Required Scope** `read_customers / write_customers`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/customers.json` | Retrieve a list of customers | page, limit, ids, since_id, created_at_min/max, updated_at_min/max, sort, query, fields | — |
| `GET` | `/api/3.0/customers/search.json` | Search customers | page, limit, ids, since_id, created_at_min/max, updated_at_min/max, sort, code, phone, email, fields | — |
| `GET` | `/api/3.0/customers/:customer_id.json` | Retrieve a single customer | fields: points, membership | — |
| `POST` | `/api/3.0/customers.json` | Create a customer | — | customer: { code, first_name, last_name, email, phone, birthdate, gender, country_code, avatar_url, addresses[], groups[] } |
| `PUT` | `/api/3.0/customers/:customer_id.json` | Update an existing customer | — | customer: { first_name, last_name, email, phone, birthdate, gender, country_code, avatar_url, addresses[], groups[], code } |
| `DELETE` | `/api/3.0/customers/:customer_id.json` | Delete a customer | — | — |

### Point

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/customers/:customer_id/points.json` | Retrieve customer points | — | — |
| `PUT` | `/api/3.0/customers/:customer_id/point/adjust.json` | Adjust customer point | — | { value, description } |

### Credit

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `PUT` | `/api/3.0/customers/:customer_id/credits/set.json` | Set customer credit (absolute) | — | { total_credit, description } |
| `PUT` | `/api/3.0/customers/:customer_id/credits/adjust.json` | Adjust customer credit (relative) | — | { adjustment_amount, description } |

### Voucher

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/customers/:customer_id/vouchers.json` | List customer vouchers ⚠️ Coming soon | page, limit | — |
| `GET` | `/api/3.0/customers/:customer_id/vouchers/:code/use.json` | Mark voucher as used ⚠️ Coming soon | — | — |

---

## Customer Addresses

> 會員地址管理

> [!NOTE]
> **Required Scope** `read_customers / write_customers`

### Addresse

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/customers/:customer_id/addresses.json` | Retrieve a list of customer addresses | page, limit | — |
| `GET` | `/api/3.0/customers/:customer_id/addresses/:address_id.json` | Retrieve a single address | — | — |
| `POST` | `/api/3.0/customers/:customer_id/addresses.json` | Create a new address for a customer | — | { first_name, last_name, company, phone, address1, address2, city, zip, province_code, country_code } |
| `PUT` | `/api/3.0/customers/:customer_id/addresses/:address_id.json` | Update an existing customer address | — | { first_name, last_name, company, address1, country_code, province_code } |
| `DELETE` | `/api/3.0/customers/:customer_id/addresses/:address_id.json` | Delete an address | — | — |
| `PUT` | `/api/3.0/customers/:customer_id/addresses/:address_id/default.json` | Set primary address for a customer | — | — |

---

## Customer Custom Attributes

> 自訂會員屬性欄位設定

> [!NOTE]
> **Required Scope** `read_customer_attributes / write_customer_attributes`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/customer_attributes.json` | Retrieve a list of custom attributes | page, limit | — |
| `GET` | `/api/3.0/customer_attributes/:id.json` | Retrieve a single custom attribute | — | — |
| `POST` | `/api/3.0/customer_attributes.json` | Create a custom attribute | — | { title, input_type, is_required, options[ {value} ] } |
| `PUT` | `/api/3.0/customer_attributes/:id.json` | Update an existing custom attribute | — | { title, input_type, is_required, options[ {id, value} ] } |
| `DELETE` | `/api/3.0/customer_attributes/:id.json` | Delete a custom attribute | — | — |

---

## Locations

> 實體門市 / 自取點管理

> [!NOTE]
> **Required Scope** `read_shipping / write_locations`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/locations.json` | Retrieve a list of locations | page, limit, ids, since_id, created_at_min/max, updated_at_min/max, sort | — |
| `GET` | `/api/3.0/locations/:location_id_or_code.json` | Retrieve a single location | — | — |
| `POST` | `/api/3.0/locations.json` | Create a location | — | { name, address1, address2, city, country_code, province_code, phone, email, latitude, longitude, enabled_pickup, cod_type, cod_min_amount, pickup_charge, business_hour, disabled_date[] } |
| `PUT` | `/api/3.0/locations/:location_id_or_code.json` | Update an existing location | — | { code, name, address1, address2, city, country_code, province_code, phone, email, … } |

---

## Gateways

> 讀取金流設定（唯讀）

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/gateways.json` | Retrieve store gateways | extras: sub_gateways | — |
| `GET` | `/api/3.0/es_gateways.json` | Retrieve all available gateways in EasyStore | — | — |

---

## Groups

> 會員分群管理

> [!NOTE]
> **Required Scope** `read_customers / write_customers`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/groups.json` | Retrieve a list of groups | — | — |
| `GET` | `/api/3.0/groups/:group_id.json` | Retrieve a single group | — | — |
| `POST` | `/api/3.0/groups.json` | Create a group | — | group: { name } |
| `PUT` | `/api/3.0/groups/:group_id.json` | Update an existing group | — | group: { name } |
| `DELETE` | `/api/3.0/groups/:group_id.json` | Delete a group | — | — |

### Customer

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/groups/:group_id/customers.json` | List customers in a group | — | — |
| `POST` | `/api/3.0/groups/:group_id/customers.json` | Add customers to a group | — | { customer_ids[] } |
| `PUT` | `/api/3.0/groups/:group_id/customers.json` | Update customers in a group (replace) | — | { customer_ids[] } |
| `DELETE` | `/api/3.0/groups/:group_id/customers.json` | Remove customers from a group | — | { customer_ids[] } |

---

## Metafields

> 自訂 metadata（可掛載於 Store、Order、Product 等資源）

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/metafields.json` | Retrieve a list of metafields | limit, page, since_id, namespace, key, value_type, ids, sort, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/metafields/count.json` | Retrieve count of metafields | — | — |
| `GET` | `/api/3.0/metafields/:metafield_id.json` | Retrieve a single metafield | — | — |
| `POST` | `/api/3.0/metafields.json` | Create a metafield | — | metafield: { namespace, key, value, value_type, description, is_private } |
| `PUT` | `/api/3.0/metafields/:metafield_id.json` | Update a metafield | — | metafield: { value, value_type, description } |
| `DELETE` | `/api/3.0/metafields/:metafield_id.json` | Delete a metafield | — | — |

---

## Snippets

> 注入 storefront 的 HTML／Liquid 程式碼片段

> [!NOTE]
> **Required Scope** `read_snippets / write_snippets`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/snippets.json` | Retrieve a list of snippets | limit, page, since_id, field, snippet_ids, sort, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/snippets/count.json` | Retrieve count of snippets | — | — |
| `GET` | `/api/3.0/snippets/:snippet_id.json` | Retrieve a single snippet | — | — |
| `POST` | `/api/3.0/snippets.json` | Create a snippet | — | snippet: { field, value } |
| `PUT` | `/api/3.0/snippets/:snippet_id.json` | Update a snippet | — | snippet: { value } |
| `DELETE` | `/api/3.0/snippets/:snippet_id.json` | Delete a snippet | — | — |

---

## Script Tags

> 注入 storefront 的外部 JavaScript 連結

> [!NOTE]
> **Required Scope** `read_script_tags / write_script_tags`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/script_tags.json` | Retrieve a list of script tags | limit, page, since_id, src, script_tag_ids, sort, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/script_tags/count.json` | Retrieve count of script tags | — | — |
| `GET` | `/api/3.0/script_tags/:script_tag_id.json` | Retrieve a single script tag | — | — |
| `POST` | `/api/3.0/script_tags.json` | Create a script tag | — | script_tag: { src, event } |
| `PUT` | `/api/3.0/script_tags/:script_tag_id.json` | Update a script tag | — | script_tag: { src } |
| `DELETE` | `/api/3.0/script_tags/:script_tag_id.json` | Delete a script tag | — | — |

---

## Pages

> 靜態頁面管理

> [!NOTE]
> **Required Scope** `read_content / write_content`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/pages.json` | Retrieve a list of pages | page, limit, ids, since_id, created_at_min/max, updated_at_min/max, published_at_min/max, sort, handle, title, visibility | — |
| `GET` | `/api/3.0/pages/:page_id.json` | Retrieve a single page | — | — |
| `POST` | `/api/3.0/pages.json` | Create a page | — | { name, title, handle, description, body_html } |
| `PUT` | `/api/3.0/pages/:page_id.json` | Update an existing page | — | { name, title, handle, description, body_html } |
| `DELETE` | `/api/3.0/pages/:page_id.json` | Delete a page | — | — |

---

## Navigations

> Storefront 導覽選單管理

> [!NOTE]
> **Required Scope** `read_content / write_content`

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/navigations.json` | Retrieve a list of navigations | limit, page, ids, since_id, created_at_min/max, updated_at_min/max, published_at_min/max, sort | — |
| `GET` | `/api/3.0/navigations/count.json` | Retrieve count of navigations | — | — |
| `GET` | `/api/3.0/navigations/:navigation_id.json` | Retrieve a single navigation | — | — |
| `POST` | `/api/3.0/navigations.json` | Create a navigation | — | navigation: { name, parent_id, link, link_type, is_published } |
| `PUT` | `/api/3.0/navigations/:navigation_id.json` | Update a navigation | — | { name, handle, is_published } |
| `DELETE` | `/api/3.0/navigations/:navigation_id.json` | Delete a navigation | — | — |

---

## Redirects

> URL 轉址規則管理

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/redirects.json` | Retrieve a list of redirects | page, limit, ids, since_id, created_at_min/max, updated_at_min/max, sort, path, target | — |
| `GET` | `/api/3.0/redirects/:redirect_id.json` | Retrieve a single redirect | — | — |
| `POST` | `/api/3.0/redirects.json` | Create a redirect | — | { path, target } |
| `PUT` | `/api/3.0/redirects/:redirect_id.json` | Update an existing redirect | — | { path, target } |
| `DELETE` | `/api/3.0/redirects/:redirect_id.json` | Delete a redirect | — | — |

---

## Webhooks

> 事件 Webhook 訂閱管理

| Method | Path | Description | Query Params | Request Body |
|--------|------|-------------|-------------|--------------|
| `GET` | `/api/3.0/webhooks.json` | Retrieve a list of webhooks | limit, page, since_id, topic, webhook_ids, sort, created_at_min/max, updated_at_min/max | — |
| `GET` | `/api/3.0/webhooks/count.json` | Retrieve count of webhooks | — | — |
| `GET` | `/api/3.0/webhooks/:webhook_id.json` | Retrieve a single webhook | — | — |
| `POST` | `/api/3.0/webhooks.json` | Create a webhook | — | webhook: { topic, url }<br>topic: app/uninstall, store/update, product/create, product/update, product/delete, customer/create, customer/update, customer/delete, order/create, order/update, order/delete, refund/create, fulfillment/create, fulfillment/update |
| `PUT` | `/api/3.0/webhooks/:webhook_id.json` | Update a webhook | — | webhook: { url } |
| `DELETE` | `/api/3.0/webhooks/:webhook_id.json` | Delete a webhook | — | — |

---

## Common Query Parameters

> 以下 query params 在多數列表型 endpoint 均適用。

### Pagination

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | integer | `1` | 頁碼 |
| `limit` | integer | `50` | 每頁筆數（最大值因資源而異，通常為 50 或 250） |
| `since_id` | integer | — | 只回傳 ID 大於此值的資料（cursor-style pagination） |
| `sort` | string | 資源預設 | 排序欄位與方向，格式 `{field}.{asc\|desc}`，例如 `created_at.desc` |

### Date Filters

| Param | Format | Description |
|-------|--------|-------------|
| `created_at_min` / `created_at_max` | `2014-04-25 16:15:47` | 建立時間範圍 |
| `updated_at_min` / `updated_at_max` | 同上 | 更新時間範圍 |
| `published_at_min` / `published_at_max` | 同上 | 發佈時間範圍（商品、分類、頁面） |
| `processed_at_min` / `processed_at_max` | 同上 | 訂單處理時間範圍 |

### ID Filters

| Param | Description |
|-------|-------------|
| `ids` | 以逗號分隔的 ID 清單，例如 `123,456,789` |

---

## HTTP Response Codes

> [!NOTE]
> EasyStore API 以 HTTP status code 表示操作結果，所有成功回應均為 `200 OK`（含 POST / PUT / DELETE）。

| Code | Meaning |
|------|---------|
| `200 OK` | 操作成功（包含建立、更新、刪除） |
| `401 Unauthorized` | Access Token 缺失或錯誤 |
| `403 Forbidden` | App 缺少必要 scope 或權限被拒 |
| `404 Not Found` | 資源不存在（RecordNotFound） |
| `408 Request Timeout` | 請求超時 |
| `422 Unprocessable Entity` | 請求參數驗證失敗 |
| `429 Too Many Requests` | 超過 API 呼叫頻率限制 |

> [!TIP]
> 可透過回應 header 監控使用量：  
> `X-RateLimit-Remaining` — 目前剩餘可用次數  
> `X-RateLimit-Limit` — 該 shop 的總上限次數
