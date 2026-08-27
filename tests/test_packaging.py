#!/usr/bin/env python3
"""
打包完整性檢查。

搬命名空間時最容易漏掉「縮排在函式內的 import」——它不會在載入模組時執行，
測試跑綠也照樣藏著，直到使用者呼叫到那個工具才 ImportError。這裡用 AST 靜態
掃描所有 import 目標，不必逐一呼叫工具就能抓出來。
"""
import ast
import importlib
import importlib.util
import os
import pkgutil
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("EASYSTORE_SHOP_URL", "https://test.example.com")
os.environ.setdefault("EASYSTORE_ACCESS_TOKEN", "test_token")

import mcp_easystore  # noqa: E402

PACKAGE_FILES = sorted(Path(mcp_easystore.__file__).parent.rglob("*.py"))


def _module_names(path):
    """取出檔案裡所有 import 的頂層模組路徑（含函式內的）。"""
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                yield node.module


def test_package_files_found():
    assert PACKAGE_FILES, "找不到 mcp_easystore 底下的原始碼"


@pytest.mark.parametrize("path", PACKAGE_FILES, ids=lambda p: p.name)
def test_every_import_target_exists(path):
    """每個 import 目標都要解析得到——包含縮排在函式內的。"""
    broken = []
    for name in _module_names(path):
        try:
            if importlib.util.find_spec(name) is None:
                broken.append(name)
        except (ImportError, ModuleNotFoundError, ValueError):
            broken.append(name)
    assert broken == [], f"{path.name} 有解析不到的 import: {broken}"


def test_all_modules_import_cleanly():
    pkg_dir = str(Path(mcp_easystore.__file__).parent)
    failures = []
    for mod in pkgutil.walk_packages([pkg_dir], prefix="mcp_easystore."):
        try:
            importlib.import_module(mod.name)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{mod.name}: {exc}")
    assert failures == [], f"模組載入失敗: {failures}"


def test_console_entry_point_resolves():
    """pyproject.toml 宣告的 mcp-easystore 指令要真的指得到可呼叫的物件。"""
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    target = config["project"]["scripts"]["mcp-easystore"]
    module_path, _, attr = target.partition(":")
    module = importlib.import_module(module_path)
    assert callable(getattr(module, attr)), f"{target} 不是可呼叫的物件"


def test_runtime_dependencies_are_installed():
    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    name_map = {"python-dotenv": "dotenv"}
    missing = []
    for spec in config["project"]["dependencies"]:
        dist = spec.split(">")[0].split("<")[0].split("=")[0].strip()
        module = name_map.get(dist, dist.replace("-", "_"))
        if importlib.util.find_spec(module) is None:
            missing.append(dist)
    assert missing == [], f"pyproject 宣告但未安裝: {missing}"
