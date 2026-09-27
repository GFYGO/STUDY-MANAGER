# -*- coding: utf-8 -*-
"""待办（作业）业务逻辑：校验、排序、状态流转。"""

from datetime import date, datetime, timedelta

from app.dao.db import init_db
from app.dao.todo_dao import TodoDAO
from app.commons.constants import STATUS_DONE, STATUS_PENDING, SUBJECT_PRESETS, WORK_TYPE_PRESETS

# 上交时间下拉预设 → 相对天数
DUE_OFFSETS = {"今天": 0, "明天": 1, "后天": 2, "本周日": None}


def resolve_due_date(text: str) -> str:
    """把上交时间下拉值换算为具体日期 YYYY-MM-DD；已是日期则原样返回。"""
    text = (text or "").strip()
    if not text:
        return ""
    if text in DUE_OFFSETS:
        offset = DUE_OFFSETS[text]
        if offset is not None:
            return (date.today() + timedelta(days=offset)).isoformat()
        # 本周日
        days_until_sunday = (6 - date.today().weekday()) % 7
        return (date.today() + timedelta(days=days_until_sunday)).isoformat()
    return text


class TodoService:
    def __init__(self):
        init_db()
        self.dao = TodoDAO()

    def create(self, subject, work_type, due_time="", content=""):
        """新增作业待办，返回 id。"""
        subject = (subject or "").strip()
        work_type = (work_type or "").strip()
        if not subject or not work_type:
            raise ValueError("科目与作业类型不能为空")
        return self.dao.insert(subject, work_type, resolve_due_date(due_time), content.strip() or None)

    def update(self, todo_id, subject, work_type, due_time="", content=""):
        subject = (subject or "").strip()
        work_type = (work_type or "").strip()
        if not subject or not work_type:
            raise ValueError("科目与作业类型不能为空")
        self.dao.update(todo_id, subject, work_type, resolve_due_date(due_time), content.strip() or None)

    def finish(self, todo_id):
        self.dao.set_status(todo_id, STATUS_DONE, datetime.now().isoformat(timespec="seconds"))

    def reopen(self, todo_id):
        self.dao.set_status(todo_id, STATUS_PENDING, None)

    def delete(self, todo_id):
        self.dao.delete(todo_id)

    def list(self, status=None, keyword=""):
        """按状态筛选 + 关键字搜索（作业内容/科目/类型），默认按上交时间升序、新建在前的待办在前。"""
        rows = self.dao.fetch_all()
        keyword = (keyword or "").strip().lower()
        result = []
        for r in rows:
            if status is not None and r["status"] != status:
                continue
            if keyword:
                haystack = " ".join(
                    filter(None, [r["subject"], r["work_type"], r["content"]])
                ).lower()
                if keyword not in haystack:
                    continue
            result.append(r)
        # 待办在前，已完成在后；待办按上交时间升序，已完成按完成时间倒序
        pending = sorted(
            [r for r in result if r["status"] == STATUS_PENDING],
            key=lambda r: (r["due_time"] or "9999", r["created_at"], r["id"]),
        )
        done = sorted(
            [r for r in result if r["status"] == STATUS_DONE],
            key=lambda r: (r["completed_at"] or "", r["id"]),
            reverse=True,
        )
        return pending + done

    def subject_options(self) -> list:
        """预设 + 历史自定义科目（去重，保持预设在前）。"""
        customs = [s for s in self.dao.distinct_subjects() if s not in SUBJECT_PRESETS]
        return list(SUBJECT_PRESETS) + customs

    def work_type_options(self) -> list:
        presets = WORK_TYPE_PRESETS
        customs = [w for w in self.dao.distinct_work_types() if w not in presets]
        return list(presets) + customs