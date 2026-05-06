"""
EasyStore MCP Server — 設定模組
從環境變數讀取 API 認證資訊，不接受硬編碼。
"""
import os
from pathlib import Path

# 從專案根目錄的 .env 檔案載入環境變數
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # python-dotenv 未安裝，直接使用系統環境變數
    pass

EASYSTORE_SHOP_URL: str = os.environ.get("EASYSTORE_SHOP_URL", "").rstrip("/")
EASYSTORE_ACCESS_TOKEN: str = os.environ.get("EASYSTORE_ACCESS_TOKEN", "")
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
