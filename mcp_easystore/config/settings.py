"""
EasyStore MCP Server — 設定模組
從環境變數讀取 API 認證資訊，不接受硬編碼。

環境變數優先級（由高到低）：
  1. MCP client 注入的環境變數（.mcp.json / claude mcp add / Claude Desktop 設定檔）
  2. .env.local 檔案
  3. .env 檔案

.env / .env.local 的搜尋位置有兩個，依序為：**執行時的工作目錄**，以及
**套件所在的專案根目錄**（`mcp_easystore/` 的上一層）。後者是給開發安裝
（`pip install -e .`）用的——MCP client 啟動 server 時工作目錄不會是 repo 根目錄，
只看 cwd 的話 repo 裡的 .env 永遠不會被讀到，卻又看起來像是有效的設定來源。
透過 uvx 安裝時程式在 site-packages，那裡不會有 .env，這條路自然不生效。

實際讀到哪些檔案、每個變數最後來自哪裡，可用 `describe_config()` 查（
`easystore_diagnose` 工具與 `scripts/check_env.py` 都走這個函式）。
"""
import hashlib
import os
import re
from pathlib import Path

# 本模組會使用的變數
_MANAGED_VARS = ("EASYSTORE_SHOP_URL", "EASYSTORE_ACCESS_TOKEN", "ENABLE_WRITE_TOOLS")

# 未展開的 ${VAR} 佔位字串
_PLACEHOLDER_RE = re.compile(r"^\$\{[^}]*\}$")

# mcp_easystore/config/settings.py → parents[2] = 專案根目錄（或 site-packages）
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]

# 診斷用：實際被讀進來的檔案、被當成「沒設定」而丟棄的變數、每個變數的來源
LOADED_ENV_FILES: list[str] = []
DROPPED_ENV_VARS: list[str] = []
ENV_VAR_SOURCES: dict[str, str] = {}


def _env_search_dirs() -> list[Path]:
    """.env / .env.local 的搜尋目錄，依優先級排序（前面的贏）。"""
    dirs: list[Path] = []
    for d in (Path.cwd(), _PACKAGE_ROOT):
        if d not in dirs:
            dirs.append(d)
    return dirs


def _drop_blank_env():
    """把空值與未展開的 ${VAR} 佔位字串當成「沒設定」。

    .mcp.json 寫 "${EASYSTORE_ACCESS_TOKEN}" 而 shell 沒設定該變數時，
    MCP client 會把字面字串 "${EASYSTORE_ACCESS_TOKEN}" 注入子行程。留著
    它有兩個壞處：validate_config 誤判設定正常（實際打 API 才 401），以及
    卡住後面 .env 的補值（load_dotenv 只看 key 在不在，不看值是否為空）。
    """
    for key in _MANAGED_VARS:
        value = os.environ.get(key)
        if value is None:
            continue
        stripped = value.strip()
        if not stripped or _PLACEHOLDER_RE.match(stripped):
            del os.environ[key]
            DROPPED_ENV_VARS.append(key)


def _load_env_files():
    """按優先級加載環境變數檔案，並記錄每個變數實際來自哪裡。"""
    for key in _MANAGED_VARS:
        if key in os.environ:
            ENV_VAR_SOURCES[key] = "環境變數（MCP client 注入或 shell）"

    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[WARNING] python-dotenv 未安裝，部分環境變數可能無法加載")
        return

    # 一律 override=False：有值的環境變數永遠優先，檔案只負責補空缺。
    # 同一輪內先讀 .env.local 再讀 .env，所以 .env.local 蓋過 .env。
    for directory in _env_search_dirs():
        for filename in (".env.local", ".env"):
            env_file = directory / filename
            if not env_file.exists():
                continue
            before = {k for k in _MANAGED_VARS if k in os.environ}
            load_dotenv(env_file, override=False)
            LOADED_ENV_FILES.append(str(env_file))
            for key in _MANAGED_VARS:
                if key in os.environ and key not in before:
                    ENV_VAR_SOURCES[key] = str(env_file)


# 執行環境變數加載
_drop_blank_env()
_load_env_files()

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
        return "請設定環境變數 EASYSTORE_SHOP_URL（例如：https://yourshop.easy.co）"
    if not EASYSTORE_ACCESS_TOKEN:
        return "請設定環境變數 EASYSTORE_ACCESS_TOKEN"
    return None


def token_fingerprint() -> str:
    """權杖指紋：長度 + sha1 前 8 碼。永遠不回傳權杖本身。"""
    if not EASYSTORE_ACCESS_TOKEN:
        return "(未設定)"
    digest = hashlib.sha1(EASYSTORE_ACCESS_TOKEN.encode()).hexdigest()[:8]
    return f"len={len(EASYSTORE_ACCESS_TOKEN)} sha1={digest}"


def describe_config() -> dict:
    """目前實際生效的設定快照（不含權杖明文）。

    給 easystore_diagnose 工具與 scripts/check_env.py 共用——排查「怎麼抓不到資料」
    時，第一件事就是確認生效的是哪一份設定。
    """
    return {
        "shop_url": EASYSTORE_SHOP_URL or "(未設定)",
        "base_url": get_base_url() if EASYSTORE_SHOP_URL else "(未設定)",
        "access_token": token_fingerprint(),
        "enable_write_tools": ENABLE_WRITE_TOOLS,
        "config_error": validate_config(),
        "sources": {key: ENV_VAR_SOURCES.get(key, "(未設定)") for key in _MANAGED_VARS},
        "dropped_as_unset": DROPPED_ENV_VARS or [],
        "env_files": {
            "searched_dirs": [str(d) for d in _env_search_dirs()],
            "loaded": list(LOADED_ENV_FILES),
        },
        "cwd": str(Path.cwd()),
        "package_root": str(_PACKAGE_ROOT),
    }
