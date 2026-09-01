#!/usr/bin/env python3
"""
fix_desktop_config.py — 把 Claude 桌面版設定裡的 EasyStore 商店換成能通的那組。

來源：本 repo 的 .claude/settings.local.json（glamglow，已實測 200）
目標：~/Library/Application Support/Claude/claude_desktop_config.json

會先備份原檔。全程不在畫面上輸出 token 內容。

用法（在 repo 根目錄）：
    python3 scripts/auth/fix_desktop_config.py          # 預覽，不寫入
    python3 scripts/auth/fix_desktop_config.py --apply  # 實際寫入
"""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".claude/settings.local.json"
DST = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"


def fp(t):
    return f"len={len(t)} sha={hashlib.sha1(t.encode()).hexdigest()[:8]}" if t else "(空)"


def main():
    apply = "--apply" in sys.argv

    if not SRC.exists():
        print(f"找不到來源設定：{SRC}", file=sys.stderr)
        return 1
    if not DST.exists():
        print(f"找不到桌面版設定：{DST}", file=sys.stderr)
        return 1

    good = json.loads(SRC.read_text(encoding="utf-8"))["mcpServers"]["easystore"]["env"]
    good_url, good_token = good["EASYSTORE_SHOP_URL"], good["EASYSTORE_ACCESS_TOKEN"]

    cfg = json.loads(DST.read_text(encoding="utf-8"))
    servers = cfg.get("mcpServers", {})

    targets = [n for n, s in servers.items()
               if "EASYSTORE_SHOP_URL" in (s.get("env") or {})]
    if not targets:
        print("桌面版設定裡找不到帶 EASYSTORE_SHOP_URL 的 server。", file=sys.stderr)
        return 1

    for name in targets:
        srv = servers[name]
        env = srv["env"]
        print(f"\n[{name}]")
        print(f"  command : {srv.get('command', '(無)')}")
        print(f"  args    : {srv.get('args', [])}")
        print(f"  舊網址  : {env.get('EASYSTORE_SHOP_URL')}")
        print(f"  舊 token: {fp(env.get('EASYSTORE_ACCESS_TOKEN', ''))}")
        print(f"  新網址  : {good_url}")
        print(f"  新 token: {fp(good_token)}")
        print(f"  寫入工具: ENABLE_WRITE_TOOLS={env.get('ENABLE_WRITE_TOOLS', '(未設定)')}")
        env["EASYSTORE_SHOP_URL"] = good_url
        env["EASYSTORE_ACCESS_TOKEN"] = good_token

    if not apply:
        print("\n── 這是預覽，沒有寫入任何東西 ──")
        print("確認無誤後再跑一次，加上 --apply")
        return 0

    backup = DST.with_suffix(f".json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(DST, backup)
    DST.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 已寫入 {DST.name}")
    print(f"   備份：{backup.name}")
    print("   請重啟 Claude 桌面版讓新設定生效。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
