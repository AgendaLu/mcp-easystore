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
    from mcp_easystore.config import settings

    # 與 easystore_diagnose 工具同一份邏輯，避免「腳本測的是另一份設定」
    desc = settings.describe_config()

    print(f"  商店 URL   : {desc['shop_url']}")
    print(f"  Base URL   : {desc['base_url']}")
    print(f"  權杖指紋   : {desc['access_token']}")
    print(f"  寫入工具   : {'已啟用' if desc['enable_write_tools'] else '未啟用（預設）'}")
    print(f"  工作目錄   : {desc['cwd']}")
    print(f"  套件根目錄 : {desc['package_root']}")
    print(f"  讀到的 env 檔：{', '.join(desc['env_files']['loaded']) or '（無）'}")
    if desc["dropped_as_unset"]:
        print(f"  視為未設定 : {', '.join(desc['dropped_as_unset'])}（空值或未展開的 ${{VAR}}）")

    print("\n  每個變數的實際來源：")
    for key, source in desc["sources"].items():
        print(f"    - {key}: {source}")

    if desc["config_error"]:
        print(f"\n⚠️  配置問題：{desc['config_error']}")
    else:
        print("\n✅ 所有配置正常！")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_env_vars()
