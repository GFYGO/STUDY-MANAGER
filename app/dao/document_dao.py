# -*- coding: utf-8 -*-
"""document（学习文档）表数据访问。"""

from app.dao.db import get_connection


def strftime_now() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


class DocumentDAO:
    def insert(self, title, filename, category):
        now = strftime_now()
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO document (title, filename, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, filename, category, now, now),
            )
            return cur.lastrowid

    def get(self, doc_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM document WHERE id = ?", (doc_id,)
            ).fetchone()
            return dict(row) if row else None

    def fetch_all(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM document ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def update_meta(self, doc_id, title=None, category=None, filename=None):
        fields = []
        values = []
        if title is not None:
            fields.append("title = ?")
            values.append(title)
        if category is not None:
            fields.append("category = ?")
            values.append(category)
        if filename is not None:
            fields.append("filename = ?")
            values.append(filename)
        if not fields:
            return
        fields.append("updated_at = ?")
        values.append(strftime_now())
        values.append(doc_id)
        with get_connection() as conn:
            conn.execute(f"UPDATE document SET {', '.join(fields)} WHERE id = ?", values)

    def delete(self, doc_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM document WHERE id = ?", (doc_id,))