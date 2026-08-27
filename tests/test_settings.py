#!/usr/bin/env python3
"""
config/settings.py 的環境變數解析測試。

settings.py 的載入邏輯寫在 module 層級（import 時就執行），所以每個案例都在
獨立的子行程中跑，並且把 settings.py 複製到 tmp 目錄——settings.py 用
__file__ 定位專案根目錄，複製過去就能安全地擺放假的 .env / .claude 檔案，
不會動到真正的 repo。
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# 子行程裡跑的探針：印出 settings 解析後的結果
PROBE = """
import json, sys
sys.path.insert(0, ".")
from config import settings
print(json.dumps({
    "shop_url": settings.EASYSTORE_SHOP_URL,
    "token": settings.EASYSTORE_ACCESS_TOKEN,
    "write_tools": settings.ENABLE_WRITE_TOOLS,
    "error": settings.validate_config(),
}))
"""


@pytest.fixture
def project(tmp_path):
    """建立一個只含 config/settings.py 的最小專案樹。"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "__init__.py").write_text("")
    shutil.copy(REPO_ROOT / "config" / "settings.py", config_dir / "settings.py")
    return tmp_path


def run_settings(project_dir, env=None):
    """在乾淨環境中載入 settings，回傳解析結果。"""
    child_env = {
        k: v for k, v in os.environ.items()
        if not k.startswith("EASYSTORE_") and k != "ENABLE_WRITE_TOOLS"
    }
    child_env.update(env or {})
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=project_dir,
        env=child_env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


def test_env_vars_are_used_as_is(project):
    """MCP client 注入的環境變數直接生效。"""
    out = run_settings(project, {
        "EASYSTORE_SHOP_URL": "https://shop.example.com/",
        "EASYSTORE_ACCESS_TOKEN": "tok_123",
        "ENABLE_WRITE_TOOLS": "true",
    })
    assert out["shop_url"] == "https://shop.example.com"  # 尾端斜線被去掉
    assert out["token"] == "tok_123"
    assert out["write_tools"] is True
    assert out["error"] is None


def test_missing_config_reports_error(project):
    """沒有任何來源提供憑證時，validate_config 要回報錯誤。"""
    out = run_settings(project)
    assert out["shop_url"] == ""
    assert out["token"] == ""
    assert out["error"] is not None


def test_dotenv_still_supported(project):
    """.env / .env.local 這條路徑保留給 scripts/ 底下的腳本使用。"""
    (project / ".env").write_text(
        "EASYSTORE_SHOP_URL=https://from-dotenv.example.com\n"
        "EASYSTORE_ACCESS_TOKEN=tok_dotenv\n"
    )
    (project / ".env.local").write_text("EASYSTORE_ACCESS_TOKEN=tok_local\n")
    out = run_settings(project)
    assert out["shop_url"] == "https://from-dotenv.example.com"
    assert out["token"] == "tok_local"  # .env.local 蓋過 .env


def test_claude_settings_json_is_not_a_config_source(project):
    """settings.py 不再自行解析 .claude/settings*.json。

    MCP server 的環境變數由 MCP client（.mcp.json / claude mcp add）注入，
    settings.py 只讀 os.environ 與 .env。自行解析 .claude/settings.json 會
    讀到不該生效的值，且 Claude Desktop 本來就不吃這個檔案。
    """
    claude_dir = project / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text(json.dumps({
        "env": {
            "EASYSTORE_SHOP_URL": "https://should-not-be-read.example.com",
            "EASYSTORE_ACCESS_TOKEN": "should_not_be_read",
        }
    }))

    out = run_settings(project)
    assert out["shop_url"] == ""
    assert out["token"] == ""
    assert out["error"] is not None


def test_claude_settings_local_json_is_not_a_config_source(project):
    """settings.local.json 同理，不是 settings.py 的設定來源。"""
    claude_dir = project / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.local.json").write_text(json.dumps({
        "env": {"ENABLE_WRITE_TOOLS": "true"}
    }))

    out = run_settings(project)
    assert out["write_tools"] is False  # 預設關閉，沒被 .claude 檔案打開
