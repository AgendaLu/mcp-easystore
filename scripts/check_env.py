#!/usr/bin/env python3
"""
環境變數檢查工具

用途：驗證環境變數是否正確加載
使用：python3 scripts/check_env.py
"""

import os
import sys
import json
from pathlib import Path


def check_env_vars():
    """檢查所有相關的環境變數"""
    print("=" * 60)
    print("📋 環境變數檢查")
    print("=" * 60)

    # 檢查環境變數來源
    root_dir = Path(__file__).parent.parent

    # 1. 檢查系統環境變數
    print("\n1️⃣  系統環境變數")
    print("-" * 60)
    env_vars = ["EASYSTORE_SHOP_URL", "EASYSTORE_ACCESS_TOKEN", "ENABLE_WRITE_TOOLS"]
    for var in env_vars:
        value = os.environ.get(var, "")
        status = "✓" if value else "✗"
        display_value = value[:50] + "..." if len(value) > 50 else value
        print(f"  {status} {var}: {display_value}")

    # 2. 檢查 .env 檔案
    print("\n2️⃣  .env 檔案")
    print("-" * 60)
    env_file = root_dir / ".env"
    if env_file.exists():
        print(f"  ✓ 檔案存在: {env_file}")
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        key = line.split('=')[0].strip()
                        print(f"    - {key}")
        except Exception as e:
            print(f"  ✗ 讀取失敗: {e}")
    else:
        print(f"  ✗ 檔案不存在: {env_file}")

    # 3. 檢查 .env.local 檔案
    print("\n3️⃣  .env.local 檔案")
    print("-" * 60)
    env_local_file = root_dir / ".env.local"
    if env_local_file.exists():
        print(f"  ✓ 檔案存在: {env_local_file}")
        try:
            with open(env_local_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        key = line.split('=')[0].strip()
                        value = line.split('=', 1)[1].strip() if '=' in line else ""
                        display_value = value[:30] + "..." if len(value) > 30 else value
                        print(f"    - {key}: {display_value}")
        except Exception as e:
            print(f"  ✗ 讀取失敗: {e}")
    else:
        print(f"  ℹ 檔案不存在（這是正常的，使用 .env.example 作為範本）")

    # 4. 檢查 .mcp.json
    print("\n4️⃣  .mcp.json（MCP client 註冊設定）")
    print("-" * 60)
    mcp_file = root_dir / ".mcp.json"
    if mcp_file.exists():
        print(f"  ✓ 檔案存在: {mcp_file}")
        try:
            with open(mcp_file, 'r') as f:
                config = json.load(f)
                for name, server in config.get("mcpServers", {}).items():
                    print(f"    - {name}: {server.get('command')} {' '.join(server.get('args', []))}")
                    for key in server.get("env", {}):
                        print(f"        env: {key}")
        except Exception as e:
            print(f"  ✗ 讀取失敗: {e}")
    else:
        print(f"  ✗ 檔案不存在: {mcp_file}")
        print("     （改用 claude mcp add 註冊的話屬正常，見 docs/setup/setup-guide.md）")

    # 5. 環境變數驗證（用 config.settings 的解析結果，與 MCP server 看到的一致）
    print("\n5️⃣  環境變數驗證（MCP server 實際會讀到的值）")
    print("-" * 60)

    sys.path.insert(0, str(root_dir))
    from config import settings

    config_errors = []

    if settings.EASYSTORE_SHOP_URL:
        print(f"✓ EASYSTORE_SHOP_URL: {settings.EASYSTORE_SHOP_URL}")
    else:
        config_errors.append("❌ EASYSTORE_SHOP_URL 未設定")

    if settings.EASYSTORE_ACCESS_TOKEN:
        token = settings.EASYSTORE_ACCESS_TOKEN
        print(f"✓ EASYSTORE_ACCESS_TOKEN: 已設定（{token[:4]}…{token[-4:]}）")
    else:
        config_errors.append("❌ EASYSTORE_ACCESS_TOKEN 未設定")

    status = "已啟用" if settings.ENABLE_WRITE_TOOLS else "未啟用（預設）"
    print(f"✓ ENABLE_WRITE_TOOLS: {status}")

    if config_errors:
        print("\n⚠️  配置問題：")
        for error in config_errors:
            print(f"  {error}")
    else:
        print("\n✅ 所有配置正常！")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_env_vars()
