#!/usr/bin/env python3
"""
環境變數檢查工具

用途：驗證環境變數是否正確加載
使用：python3 scripts/check_env.py
"""

import os
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

    # 4. 檢查 .claude/settings.json
    print("\n4️⃣  .claude/settings.json（專案級配置）")
    print("-" * 60)
    settings_file = root_dir / ".claude" / "settings.json"
    if settings_file.exists():
        print(f"  ✓ 檔案存在: {settings_file}")
        try:
            with open(settings_file, 'r') as f:
                config = json.load(f)
                env_vars = config.get("env", {})
                if env_vars:
                    for key in env_vars:
                        print(f"    - {key}")
                else:
                    print("    （無環境變數定義）")
        except Exception as e:
            print(f"  ✗ 讀取失敗: {e}")
    else:
        print(f"  ✗ 檔案不存在: {settings_file}")

    # 5. 檢查 .claude/settings.local.json
    print("\n5️⃣  .claude/settings.local.json（本地配置 - 敏感信息）")
    print("-" * 60)
    settings_local_file = root_dir / ".claude" / "settings.local.json"
    if settings_local_file.exists():
        print(f"  ✓ 檔案存在: {settings_local_file}")
        try:
            with open(settings_local_file, 'r') as f:
                config = json.load(f)
                env_vars = config.get("env", {})
                if env_vars:
                    for key, value in env_vars.items():
                        display_value = str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                        print(f"    - {key}: {display_value}")
                else:
                    print("    （無環境變數定義）")
        except Exception as e:
            print(f"  ✗ 讀取失敗: {e}")
    else:
        print(f"  ℹ 檔案不存在（需要手動創建，.gitignore 已排除）")

    # 6. 環境變數驗證
    print("\n6️⃣  環境變數驗證")
    print("-" * 60)

    config_errors = []

    if not os.environ.get("EASYSTORE_SHOP_URL"):
        config_errors.append("❌ EASYSTORE_SHOP_URL 未設定")
    else:
        print("✓ EASYSTORE_SHOP_URL: 已設定")

    if not os.environ.get("EASYSTORE_ACCESS_TOKEN"):
        config_errors.append("❌ EASYSTORE_ACCESS_TOKEN 未設定")
    else:
        print("✓ EASYSTORE_ACCESS_TOKEN: 已設定")

    enable_write = os.environ.get("ENABLE_WRITE_TOOLS", "false").lower() == "true"
    status = "已啟用" if enable_write else "未啟用（預設）"
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
