# -*- coding: utf-8 -*-
"""AI 技能工具：function-calling 的 schema 声明与本地执行器。

三个技能：建文档、整理文档、建待办（作业）。
"""

import json

from app.services.document_service import DocumentService
from app.services.todo_service import TodoService
from app.commons.constants import STATUS_DONE, STATUS_PENDING

# OpenAI 兼容的工具 schema；DeepSeek / 通义 / Kimi 均支持该格式
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "查看文档库中的全部文档（含标题、分类、正文内容），整理文档前可先调用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "查看作业待办列表（含科目、作业类型、上交时间、是否已完成）。可按状态过滤。",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "done"],
                        "description": "只查看某种状态：pending=未完成，done=已完成。省略则返回全部。",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_document",
            "description": "新建一篇学习文档（Markdown 格式），保存到文档库。适合保存笔记、错题整理、知识点总结等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "文档标题"},
                    "content": {"type": "string", "description": "文档正文（Markdown）"},
                    "category": {"type": "string", "description": "分类，如语文/数学/英语，可选"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "organize_documents",
            "description": "整理文档库：把多篇文档合并为一篇新文档、为文档设置分类、或重命名文档。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["merge", "set_category", "rename"],
                        "description": "merge=合并多篇为新文档；set_category=设置分类；rename=重命名",
                    },
                    "document_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "目标文档在文档库中的 id",
                    },
                    "new_title": {"type": "string", "description": "新标题（rename 或 merge 时使用）"},
                    "new_category": {"type": "string", "description": "新分类（set_category 时使用）"},
                    "merged_content": {
                        "type": "string",
                        "description": "合并后的正文（merge 时可选，未提供则自动拼接原文档内容）",
                    },
                },
                "required": ["action", "document_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "build_todo",
            "description": "把作业记录为待办事项，需要科目、作业类型、上交时间（如“明天”“后天”或具体日期 2026-09-21）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "科目，如数学、语文"},
                    "work_type": {"type": "string", "description": "作业类型，如练习、试卷、背诵"},
                    "due_time": {"type": "string", "description": "上交时间，可为 今天/明天/后天/本周日 或日期 2026-09-21，可选"},
                    "content": {"type": "string", "description": "作业内容说明，可选"},
                },
                "required": ["subject", "work_type"],
            },
        },
    },
]

MAX_CONTENT_CHARS = 6000  # 喂给模型的单篇文档正文上限，超出截断并提示


def _truncate(text: str) -> str:
    text = text or ""
    if len(text) <= MAX_CONTENT_CHARS:
        return text
    return text[:MAX_CONTENT_CHARS] + "\n\n……（内容过长已截断）……"


def exec_list_documents(args: dict | None = None) -> str:
    docs = DocumentService().list()
    if not docs:
        return "文档库为空。"
    lines = [
        {
            "id": d["id"],
            "title": d["title"],
            "category": d["category"],
            "updated_at": d["updated_at"],
            "content": _truncate(d["content"]),
        }
        for d in docs
    ]
    return json.dumps(lines, ensure_ascii=False)


STATUS_ALIASES = {"pending": STATUS_PENDING, "todo": STATUS_PENDING, "unfinished": STATUS_PENDING,
                  "done": STATUS_DONE, "finished": STATUS_DONE, "completed": STATUS_DONE}


def exec_list_todos(args: dict | None = None) -> str:
    """查看作业待办，可按状态过滤。"""
    args = args or {}
    status = str(args.get("status") or "").strip().lower()
    if status:
        status_value = STATUS_ALIASES.get(status)
        if status_value is None:
            return f"状态参数无效：{args.get('status')}（可用：pending/done）。"
    else:
        status_value = None
    rows = TodoService().list(status=status_value)
    if not rows:
        return "待办列表为空。"
    lines = [
        {
            "id": r["id"],
            "subject": r["subject"],
            "work_type": r["work_type"],
            "due_time": r["due_time"],
            "content": r["content"],
            "status": "done" if r["status"] == STATUS_DONE else "pending",
            "completed_at": r["completed_at"],
        }
        for r in rows
    ]
    return json.dumps(lines, ensure_ascii=False)


def exec_build_document(args: dict) -> str:
    title = (args.get("title") or "").strip()
    try:
        doc = DocumentService().create(
            title,
            content=args.get("content") or "",
            category=args.get("category") or "",
        )
        return f"已新建文档「{doc['title']}」（id={doc['id']}，分类：{doc['category']}）。"
    except ValueError as exc:
        return f"建文档失败：{exc}"


def exec_organize_documents(args: dict) -> str:
    action = args.get("action")
    ids = args.get("document_ids") or []
    service = DocumentService()

    docs = {str(d["id"]): d for d in service.list()}
    missing = [i for i in ids if str(i) not in docs]
    if missing:
        return f"整理失败：找不到文档 id={missing}。"

    if action == "merge":
        new_title = (args.get("new_title") or "").strip()
        if not new_title:
            return "整理失败：merge 需要提供 new_title。"
        merged = args.get("merged_content") or ""
        if not merged:
            # 自动拼接原文档
            parts = []
            for doc_id in ids:
                d = docs[str(doc_id)]
                parts.append(f"# {d['title']}\n\n{d['content']}\n")
            merged = "\n".join(parts)
        try:
            new_doc = service.merge(ids, new_title, merged)
            names = "、".join(f"「{docs[str(i)]['title']}」" for i in ids)
            return f"已把 {names} 合并为新文档「{new_doc['title']}」（id={new_doc['id']}），原文档保留。"
        except ValueError as exc:
            return f"合并失败：{exc}"

    if action == "set_category":
        category = (args.get("new_category") or "").strip()
        if not category:
            return "整理失败：set_category 需要提供 new_category。"
        names = []
        for doc_id in ids:
            service.set_category(doc_id, category)
            names.append(docs[str(doc_id)]["title"])
        return f"已把「{'、'.join(names)}」设置为分类：{category}。"

    if action == "rename":
        new_title = (args.get("new_title") or "").strip()
        if not new_title:
            return "整理失败：rename 需要提供 new_title。"
        names = []
        for doc_id in ids:
            service.rename(doc_id, new_title)
            names.append(docs[str(doc_id)]["title"])
        return f"已重命名文档「{'、'.join(names)}」→「{new_title}」。"

    return f"整理失败：未知动作 {action}。"


def exec_build_todo(args: dict) -> str:
    subject = (args.get("subject") or "").strip()
    work_type = (args.get("work_type") or "").strip()
    due = (args.get("due_time") or "").strip()
    content = (args.get("content") or "").strip()
    service = TodoService()
    try:
        todo_id = service.create(subject, work_type, due, content)
        stored = service.dao.get(todo_id)
        return (
            f"已新增作业待办：{stored['subject']}·{stored['work_type']}"
            f"（上交时间：{stored['due_time'] or '未填'}，id={todo_id}）。"
        )
    except ValueError as exc:
        return f"建待办失败：{exc}"


EXECUTORS = {
    "list_documents": exec_list_documents,
    "list_todos": exec_list_todos,
    "build_document": exec_build_document,
    "organize_documents": exec_organize_documents,
    "build_todo": exec_build_todo,
}