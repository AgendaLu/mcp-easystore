"""
EasyStore MCP Server — 設定模組
從環境變數讀取 API 認證資訊，不接受硬編碼。

環境變數優先級（由高到低）：
  1. MCP client 注入的環境變數（.mcp.json / claude mcp add，已存在 os.environ）
  2. .env.local 檔案
  3. .env 檔案

.env 兩個檔案是給 scripts/ 底下的獨立腳本用的；MCP server 由 client 啟動時，
環境變數已經注入 os.environ，不會走到檔案這條路。
"""
import os
from pathlib import Path


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


# 執行環境變數加載
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
        return "請設定環境變數 EASYSTORE_SHOP_URL（例如：https://yourshop.easystore.co）"
    if not EASYSTORE_ACCESS_TOKEN:
        return "請設定環境變數 EASYSTORE_ACCESS_TOKEN"
    return None
