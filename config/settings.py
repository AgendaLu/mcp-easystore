"""
EasyStore MCP Server — 設定模組
從環境變數讀取 API 認證資訊，不接受硬編碼。

環境變數優先級（由高到低）：
  1. Claude Cowork 注入的環境變數（已存在 os.environ）
  2. .claude/settings.local.json 中的 env 字段
  3. .env.local 檔案
  4. .env 檔案
  5. 系統環境變數
"""
import os
import json
import re
from pathlib import Path


_SHELL_VAR_RE = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-?([^}]*))?\}')


def _expand_shell_vars(value):
    """解析 ${VAR} 與 ${VAR:default} / ${VAR:-default} 語法。
    若 VAR 已在 os.environ 中則用其值，否則用 default（無 default 時回傳空字串）。
    """
    if not isinstance(value, str):
        return value

    def repl(match):
        var_name = match.group(1)
        default = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(var_name, default)

    return _SHELL_VAR_RE.sub(repl, value)


def _load_env_files():
    """按優先級加載環境變數檔案"""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[WARNING] python-dotenv 未安裝，部分環境變數可能無法加載")
        return

    root_dir = Path(__file__).parent.parent

    # 優先級：.env < .env.local
    # 注意：load_dotenv 只會加載尚未存在的變數，已存在的不會被覆蓋
    env_file = root_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)

    env_local_file = root_dir / ".env.local"
    if env_local_file.exists():
        load_dotenv(env_local_file, override=True)


def _load_claude_settings_env():
    """從 .claude/settings.local.json 或 .claude/settings.json 加載環境變數"""
    root_dir = Path(__file__).parent.parent
    claude_dir = root_dir / ".claude"

    # 優先級：settings.local.json > settings.json
    settings_files = [
        claude_dir / "settings.local.json",
        claude_dir / "settings.json",
    ]

    for settings_file in settings_files:
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    env_vars = config.get("env", {})

                    # 只設定尚未在環境中的變數（優先級更高的源已經設定過了）
                    for key, value in env_vars.items():
                        if key not in os.environ:
                            expanded = _expand_shell_vars(value)
                            if expanded:
                                os.environ[key] = str(expanded)

                    break  # 只加載最高優先級的檔案
            except Exception as e:
                print(f"[WARNING] 無法加載 {settings_file.name}: {e}")


# 執行環境變數加載
_load_env_files()
_load_claude_settings_env()

EASYSTORE_SHOP_URL: str = os.environ.get("EASYSTORE_SHOP_URL", "").rstrip("/")
EASYSTORE_ACCESS_TOKEN: str = os.environ.get("EASYSTORE_ACCESS_TOKEN", "")
ENABLE_WRITE_TOOLS: bool = os.environ.get("ENABLE_WRITE_TOOLS", "false").lower() == "true"
API_VERSION: str = "3.0"

def get_base_url() -> str:
    return f"{EASYSTORE_SHOP_URL}/api/{API_VERSION}"

def get_headers() -> dict:
    return {
        "EasyStore-Access-Token": EASYSTORE_ACCESS_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def validate_config() -> str | None:
    """回傳錯誤訊息，或 None 表示設定正常。"""
    if not EASYSTORE_SHOP_URL:
        return "請設定環境變數 EASYSTORE_SHOP_URL（例如：https://yourshop.easystore.co）"
    if not EASYSTORE_ACCESS_TOKEN:
        return "請設定環境變數 EASYSTORE_ACCESS_TOKEN"
    return None
