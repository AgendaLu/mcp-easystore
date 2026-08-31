#!/usr/bin/env python3
"""
compare_stores.py — 並排比對多組 EasyStore 設定，找出哪一組真的通。

從 .env 與 .claude/settings.local.json 各讀一組 (shop_url, token)，
對每組打兩個端點，印出 HTTP 狀態碼。全程不輸出 token 內容，只印 sha 前 8 碼。

用法（在 repo 根目錄）：
    python3 scripts/auth/compare_stores.py
"""
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_VERSION = "3.0"
ENDPOINTS = ["store", "orders"]
ROOT = Path(__file__).resolve().parents[2]


def fp(token: str) -> str:
    """token 指紋，絕不輸出原文。"""
    if not token:
        return "(空)"
    return f"len={len(token)} sha={hashlib.sha1(token.encode()).hexdigest()[:8]}"


def from_env_file(path: Path):
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    def grab(key):
        m = re.search(rf"^{key}=(.*)$", text, re.M)
        return m.group(1).strip() if m else ""
    url, token = grab("EASYSTORE_SHOP_URL"), grab("EASYSTORE_ACCESS_TOKEN")
    return (url, token) if url or token else None


def from_settings_json(path: Path):
    if not path.exists():
        return None
    try:
        env = json.loads(path.read_text(encoding="utf-8"))["mcpServers"]["easystore"]["env"]
    except (KeyError, json.JSONDecodeError):
        return None
    return env.get("EASYSTORE_SHOP_URL", ""), env.get("EASYSTORE_ACCESS_TOKEN", "")


def probe(url: str, token: str, resource: str) -> str:
    target = f"{url.rstrip('/')}/api/{API_VERSION}/{resource}.json?limit=1"
    req = urllib.request.Request(target, headers={
        "EasyStore-Access-Token": token,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(400).decode("utf-8", "replace")
            return f"{resp.status} OK  {body[:90]}…"
    except urllib.error.HTTPError as e:
        return f"{e.code} {e.reason}"
    except Exception as e:
        return f"連線失敗 — {type(e).__name__}: {e}"


def main():
    sources = [
        (".env", from_env_file(ROOT / ".env")),
        (".claude/settings.local.json", from_settings_json(ROOT / ".claude/settings.local.json")),
    ]

    found = False
    for label, cfg in sources:
        print(f"\n{'='*62}\n來源：{label}")
        if not cfg:
            print("  （讀不到設定，略過）")
            continue
        url, token = cfg
        found = True
        print(f"  商店網址：{url or '(未設定)'}")
        print(f"  Token   ：{fp(token)}")
        if not url or not token:
            print("  ⚠️ 設定不完整，略過連線測試")
            continue
        for resource in ENDPOINTS:
            print(f"    /{resource}.json  →  {probe(url, token, resource)}")

    if not found:
        print("找不到任何設定來源。", file=sys.stderr)
        return 1
    print(f"\n{'='*62}\n判讀：401 = token 無效｜403 = scope 不足｜404 = 商店或路徑不存在｜200 = 通")
    return 0


if __name__ == "__main__":
    sys.exit(main())
