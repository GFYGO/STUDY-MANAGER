# -*- coding: utf-8 -*-
"""api_key 表数据访问。"""

from app.dao.db import get_connection


class KeyDAO:
    def insert(self, provider, api_key_encrypted, base_url, model, is_default=0):
        """新增一条密钥记录，返回自增 id。"""
        now = strftime_now()
        with get_connection() as conn:
            if is_default:
                conn.execute("UPDATE api_key SET is_default = 0")
            cur = conn.execute(
                """
                INSERT INTO api_key
                    (provider, api_key_encrypted, base_url, model, is_default, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (provider, api_key_encrypted, base_url, model, int(is_default), now),
            )
            return cur.lastrowid

    def fetch_all(self):
        """返回全部记录（密文形式）。"""
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM api_key ORDER BY id").fetchall()
            return [dict(r) for r in rows]

    def fetch_default(self):
        """返回默认密钥（密文形式），无则 None。"""
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM api_key WHERE is_default = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def set_default(self, key_id):
        """把指定 id 设为默认，其余解除默认。"""
        with get_connection() as conn:
            conn.execute("UPDATE api_key SET is_default = 0")
            conn.execute("UPDATE api_key SET is_default = 1, updated_at = ? WHERE id = ?", (strftime_now(), key_id))

    def delete(self, key_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM api_key WHERE id = ?", (key_id,))


def strftime_now() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")