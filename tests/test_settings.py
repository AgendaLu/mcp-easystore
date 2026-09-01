#!/usr/bin/env python3
"""
mcp_easystore/config/settings.py 的環境變數解析測試。

settings.py 的載入邏輯寫在 module 層級（import 時就執行），所以每個案例都在
獨立的子行程中跑，並且把套件複製到 tmp 目錄、以 tmp 為工作目錄——settings.py
以工作目錄定位 .env，這樣就能安全地擺放假的 .env / .claude 檔案，不會動到
真正的 repo。
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
import json, os, sys
sys.path.insert(0, os.environ.get("PROBE_SYS_PATH", "."))
from mcp_easystore.config import settings
print(json.dumps({
    "shop_url": settings.EASYSTORE_SHOP_URL,
    "token": settings.EASYSTORE_ACCESS_TOKEN,
    "write_tools": settings.ENABLE_WRITE_TOOLS,
    "error": settings.validate_config(),
    "loaded_env_files": settings.LOADED_ENV_FILES,
    "sources": settings.ENV_VAR_SOURCES,
    "describe": settings.describe_config(),
}))
"""


@pytest.fixture
def project(tmp_path):
    """建立一個只含 mcp_easystore/config/settings.py 的最小專案樹。"""
    config_dir = tmp_path / "mcp_easystore" / "config"
    config_dir.mkdir(parents=True)
    (config_dir.parent / "__init__.py").write_text("")
    (config_dir / "__init__.py").write_text("")
    shutil.copy(
        REPO_ROOT / "mcp_easystore" / "config" / "settings.py",
        config_dir / "settings.py",
    )
    return tmp_path


def run_settings(project_dir, env=None, sys_path=None):
    """在乾淨環境中載入 settings，回傳解析結果。

    sys_path：套件所在目錄（預設等於工作目錄）。要驗「cwd 與套件位置不同」時才會用到。
    """
    child_env = {
        k: v for k, v in os.environ.items()
        if not k.startswith("EASYSTORE_") and k != "ENABLE_WRITE_TOOLS"
    }
    child_env["PROBE_SYS_PATH"] = str(sys_path) if sys_path else "."
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


def test_unexpanded_placeholder_is_treated_as_unset(project):
    """MCP client 對未設定的 ${VAR} 會原樣注入字串，不能當成有效值。

    .mcp.json 寫 "${EASYSTORE_ACCESS_TOKEN}" 而 shell 沒設定該變數時，
    子行程收到的是字面字串 "${EASYSTORE_ACCESS_TOKEN}"。若直接採用，
    validate_config 會誤判設定正常，實際打 API 才拿到 401。
    """
    out = run_settings(project, {
        "EASYSTORE_SHOP_URL": "${EASYSTORE_SHOP_URL}",
        "EASYSTORE_ACCESS_TOKEN": "${EASYSTORE_ACCESS_TOKEN}",
    })
    assert out["shop_url"] == ""
    assert out["token"] == ""
    assert out["error"] is not None


def test_dotenv_fills_in_when_client_injects_blank(project):
    """client 注入空值時，.env 仍要能補上（空值等同沒設定）。"""
    (project / ".env").write_text(
        "EASYSTORE_SHOP_URL=https://from-dotenv.example.com\n"
        "EASYSTORE_ACCESS_TOKEN=tok_dotenv\n"
    )
    out = run_settings(project, {
        "EASYSTORE_SHOP_URL": "",
        "EASYSTORE_ACCESS_TOKEN": "${EASYSTORE_ACCESS_TOKEN}",
    })
    assert out["shop_url"] == "https://from-dotenv.example.com"
    assert out["token"] == "tok_dotenv"
    assert out["error"] is None


def test_real_env_still_wins_over_dotenv(project):
    """真的有值的環境變數不受影響，仍然優先於 .env。"""
    (project / ".env").write_text("EASYSTORE_ACCESS_TOKEN=tok_dotenv\n")
    out = run_settings(project, {
        "EASYSTORE_SHOP_URL": "https://shop.example.com",
        "EASYSTORE_ACCESS_TOKEN": "tok_from_client",
    })
    assert out["token"] == "tok_from_client"


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


def test_dotenv_is_found_from_package_root_when_cwd_differs(project):
    """工作目錄不是專案根目錄時，.env 仍要被讀到。

    MCP client 啟動 server 時工作目錄通常是 `/`，只看 cwd 的話 repo 裡的 .env
    從頭到尾不會被讀——但它看起來像個有效的設定來源，改了沒反應會讓人往錯的
    方向查。改成從套件位置回推專案根目錄後這條路才真的通。
    """
    (project / ".env").write_text(
        "EASYSTORE_SHOP_URL=https://from-package-root.example.com\n"
        "EASYSTORE_ACCESS_TOKEN=tok_pkg\n"
    )
    elsewhere = project / "elsewhere"
    elsewhere.mkdir()

    out = run_settings(elsewhere, sys_path=project)
    assert out["shop_url"] == "https://from-package-root.example.com"
    assert out["token"] == "tok_pkg"
    assert str(project / ".env") in out["loaded_env_files"]


def test_describe_config_reports_effective_source_without_token(project):
    """describe_config 要指出設定來自哪裡，且不得含權杖明文。"""
    (project / ".env").write_text("EASYSTORE_SHOP_URL=https://from-dotenv.example.com\n")
    out = run_settings(project, {"EASYSTORE_ACCESS_TOKEN": "super_secret_token"})

    desc = out["describe"]
    assert desc["shop_url"] == "https://from-dotenv.example.com"
    assert desc["base_url"] == "https://from-dotenv.example.com/api/3.0"
    assert "super_secret_token" not in json.dumps(desc, ensure_ascii=False)
    assert desc["access_token"].startswith("len=18 sha1=")
    assert desc["sources"]["EASYSTORE_SHOP_URL"].endswith(".env")
    assert "環境變數" in desc["sources"]["EASYSTORE_ACCESS_TOKEN"]
    assert desc["config_error"] is None


def test_env_var_always_wins_over_dotenv_local(project):
    """.env.local 不得蓋掉 client 注入的環境變數。

    先前 .env.local 是 override=True，開發安裝下一份殘留的 .env.local 會悄悄
    蓋過 Claude Desktop 的設定，正是這次事故那一類「不知道哪份設定生效」的坑。
    """
    (project / ".env.local").write_text("EASYSTORE_SHOP_URL=https://stale-local.example.com\n")
    out = run_settings(project, {
        "EASYSTORE_SHOP_URL": "https://from-client.example.com",
        "EASYSTORE_ACCESS_TOKEN": "tok",
    })
    assert out["shop_url"] == "https://from-client.example.com"
