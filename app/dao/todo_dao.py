# -*- coding: utf-8 -*-
"""todo（作业）表数据访问。"""

from app.dao.db import get_connection


def strftime_now() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


class TodoDAO:
    def insert(self, subject, work_type, due_time, content=None):
        """新增一条作业待办，返回自增 id。"""
        now = strftime_now()
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO todo (subject, work_type, due_time, content, status, created_at)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (subject, work_type, due_time, content, now),
            )
            return cur.lastrowid

    def get(self, todo_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM todo WHERE id = ?", (todo_id,)).fetchone()
            return dict(row) if row else None

    def fetch_all(self):
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM todo ORDER BY id").fetchall()
            return [dict(r) for r in rows]

    def update(self, todo_id, subject, work_type, due_time, content):
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE todo SET subject = ?, work_type = ?, due_time = ?, content = ?
                WHERE id = ?
                """,
                (subject, work_type, due_time, content, todo_id),
            )

    def set_status(self, todo_id, status, completed_at=None):
        with get_connection() as conn:
            conn.execute(
                "UPDATE todo SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, todo_id),
            )

    def delete(self, todo_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM todo WHERE id = ?", (todo_id,))

    def distinct_subjects(self) -> list:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT subject FROM todo ORDER BY subject"
            ).fetchall()
            return [r["subject"] for r in rows]

    def distinct_work_types(self) -> list:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT work_type FROM todo ORDER BY work_type"
            ).fetchall()
            return [r["work_type"] for r in rows]