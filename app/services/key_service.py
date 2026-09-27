# -*- coding: utf-8 -*-
"""API Key 业务逻辑：加密后入库，读取时解密。"""

from app.dao.db import init_db
from app.dao.key_dao import KeyDAO
from app.security.crypto import decrypt, encrypt


class KeyService:
    def __init__(self):
        init_db()
        self.dao = KeyDAO()

    def save_key(self, provider, api_key, base_url="", model="", is_default=False) -> int:
        """保存一条密钥（仅密文入库），返回 id。"""
        api_key = api_key.strip()
        if not provider.strip() or not api_key:
            raise ValueError("供应商名称与 API Key 不能为空")
        encrypted = encrypt(api_key)
        return self.dao.insert(
            provider.strip(), encrypted, base_url.strip() or None, model.strip() or None, is_default
        )

    def list_keys(self) -> list:
        """返回已保存密钥列表（含解密后的明文，仅供界面临时展示）。"""
        keys = self.dao.fetch_all()
        for key in keys:
            key["api_key_decrypted"] = decrypt(key["api_key_encrypted"])
        return keys

    def get_default(self) -> dict | None:
        """返回默认密钥（含明文 api_key），无默认时返回 None。"""
        row = self.dao.fetch_default()
        if row is None:
            return None
        row["api_key"] = decrypt(row["api_key_encrypted"])
        return row

    def set_default(self, key_id) -> None:
        self.dao.set_default(key_id)

    def delete(self, key_id) -> None:
        self.dao.delete(key_id)