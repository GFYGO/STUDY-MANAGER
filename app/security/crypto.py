# -*- coding: utf-8 -*-
"""API Key 加密封装（Fernet 对称加密，密钥单独存文件）。"""

from pathlib import Path

from cryptography.fernet import Fernet

# 加密密钥文件位于项目根 data/ 目录（运行期生成）
KEY_FILE = Path(__file__).resolve().parents[2] / "data" / "secret.key"

_fernet = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def _load_or_create_key() -> bytes:
    """加载本地密钥；不存在则生成并持久化。"""
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    return key


def encrypt(plain_text: str) -> str:
    """加密为 Base64 字符串。"""
    return _get_fernet().encrypt(plain_text.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    """解密，失败时抛出异常。"""
    return _get_fernet().decrypt(token.encode("ascii")).decode("utf-8")