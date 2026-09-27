# -*- coding: utf-8 -*-
"""文档业务逻辑：Markdown 文件存储 + 索引表同步。"""

import re
from datetime import datetime
from pathlib import Path

from app.dao.db import init_db
from app.dao.document_dao import DocumentDAO
from app.commons.constants import DOC_CATEGORY_DEFAULT, DOC_DIR


def _doc_root() -> Path:
    """文档存放目录：项目根 data/documents。"""
    root = Path(__file__).resolve().parents[2] / "data" / DOC_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_filename(title: str) -> str:
    """由标题生成安全文件名，去非法字符。"""
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", title.strip())
    return name or "untitled"


def _make_filename(seed: str, existed_names: list | None = None) -> str:
    """生成带时间戳的唯一文件名。"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{_safe_filename(seed)}_{timestamp}.md"
    while existed_names and filename in existed_names:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        filename = f"{_safe_filename(seed)}_{timestamp}.md"
    return filename


class DocumentService:
    def __init__(self):
        init_db()
        self.dao = DocumentDAO()

    def create(self, title, content="", category=DOC_CATEGORY_DEFAULT) -> dict:
        """新建文档（写文件 + 索引），返回文档 dict。"""
        title = (title or "").strip()
        if not title:
            raise ValueError("文档标题不能为空")
        existed = [d["filename"] for d in self.dao.fetch_all()]
        filename = _make_filename(title, existed)
        self._write_file(filename, content or f"# {title}\n")
        category = (category or DOC_CATEGORY_DEFAULT).strip() or DOC_CATEGORY_DEFAULT
        doc_id = self.dao.insert(title, filename, category)
        return self.get(doc_id)

    def get(self, doc_id):
        doc = self.dao.get(doc_id)
        if doc:
            doc["content"] = self.read_content(doc)
        return doc

    def list(self):
        """返回文档列表（含内容）。"""
        docs = self.dao.fetch_all()
        for doc in docs:
            doc["content"] = self.read_content(doc)
        return docs

    def read_content(self, doc) -> str:
        path = _doc_root() / doc["filename"]
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _write_file(self, filename, content) -> Path:
        path = _doc_root() / filename
        path.write_text(content or "", encoding="utf-8")
        return path

    def save_content(self, doc_id, content):
        """保存文档正文（仅更新文件与 updated_at）。"""
        doc = self.dao.get(doc_id)
        if not doc:
            raise ValueError("文档不存在")
        self._write_file(doc["filename"], content)
        self.dao.update_meta(doc_id)

    def rename(self, doc_id, new_title):
        """重命名：同步文件文件名与索引标题。"""
        doc = self.dao.get(doc_id)
        if not doc:
            raise ValueError("文档不存在")
        new_title = (new_title or "").strip() or doc["title"]
        if new_title == doc["title"]:
            return
        new_filename = _make_filename(new_title, [d["filename"] for d in self.dao.fetch_all()])
        old_path = _doc_root() / doc["filename"]
        new_path = _doc_root() / new_filename
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
        else:
            new_path.write_text(self.read_content(doc), encoding="utf-8")
        self.dao.update_meta(doc_id, title=new_title)
        self.dao.update_meta(doc_id, filename=new_filename)

    def set_category(self, doc_id, category):
        doc = self.dao.get(doc_id)
        if not doc:
            raise ValueError("文档不存在")
        self.dao.update_meta(doc_id, category=category.strip() or DOC_CATEGORY_DEFAULT)

    def delete(self, doc_id):
        doc = self.dao.get(doc_id)
        if not doc:
            return
        path = _doc_root() / doc["filename"]
        if path.exists():
            path.unlink()
        self.dao.delete(doc_id)

    def merge(self, source_ids, new_title, content) -> dict:
        """合并多篇文档为新的文档（原文档保留），返回新文档 dict。"""
        return self.create(new_title, content=content)