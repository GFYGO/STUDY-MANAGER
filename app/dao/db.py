# -*- coding: utf-8 -*-
"""SQLite 连接与建表。"""

import sqlite3
from pathlib import Path

# 数据库文件位于项目根 data/ 目录（运行期生成）
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "study.db"


def get_connection() -> sqlite3.Connection:
    """建立连接；连接以 dict-like 行对象返回。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """建表（幂等，可重复调用）。"""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS api_key (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                base_url TEXT,
                model TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS todo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                work_type TEXT NOT NULL,
                due_time TEXT,
                content TEXT,
                status INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_todo_status ON todo(status);
            CREATE INDEX IF NOT EXISTS idx_todo_due ON todo(due_time);

            CREATE TABLE IF NOT EXISTS document (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT '通用',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )