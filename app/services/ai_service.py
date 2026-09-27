# -*- coding: utf-8 -*-
"""AI 服务：读取默认 API Key，调用 OpenAI 兼容接口，执行 function-calling 技能循环。"""

import json
import urllib.error
import urllib.request

from app.commons.constants import PROVIDER_INFO
from app.services.ai_tools import EXECUTORS, TOOL_SCHEMAS
from app.services.key_service import KeyService

MAX_TOOL_TURNS = 5        # 单轮对话最多工具调用轮数
REQUEST_TIMEOUT = 90      # 秒

SYSTEM_PROMPT = (
    "你是「学习管理」桌面应用内置的 AI 学习助手，面向高中生。\n"
    "你可以通过调用工具完成四类任务：\n"
    "1. 建文档：把学习笔记、错题整理、知识点总结等内容保存为文档（build_document）；\n"
    "2. 整理文档：先查看文档库（list_documents），再合并、设置分类或重命名（organize_documents）；\n"
    "3. 建待办：把作业记录为待办事项（build_todo），含科目、作业类型、上交时间；\n"
    "4. 查看待办：可查看作业待办列表（list_todos），按状态过滤。\n"
    "用户询问有哪些作业、还剩什么没做完、待办进度时，请调用 list_todos 查看。\n"
    "用户要求创建/整理/记录/查询时，请优先调用对应工具；工具执行结果对用户可见。"
    "回答保持简洁、友好的中文。"
)


class NoKeyError(Exception):
    """未配置默认 API Key。"""


class AIService:
    def __init__(self):
        self.service = KeyService()
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ---------- 对外 ----------

    def send(self, user_text: str) -> tuple:
        """发送一条用户消息，返回 (回复文本, 工具执行记录列表)。"""
        self.messages.append({"role": "user", "content": user_text})
        try:
            reply, executed = self._run_tool_loop()
        except NoKeyError:
            reply = (
                "尚未配置默认 API Key。请到「设置」页填写供应商与 API Key，"
                "并勾选「设为默认」后重试。"
            )
            executed = []
        return reply, executed

    def send_stream(self, user_text: str, on_chunk) -> tuple:
        """流式发送：请求 stream=true，内容增量时回调 on_chunk(累计文本)。

        返回 (完整回复文本, 工具执行记录列表)。无默认 Key 时返回友好提示文本。
        """
        self.messages.append({"role": "user", "content": user_text})
        try:
            reply, executed = self._run_tool_loop_stream(on_chunk)
        except NoKeyError:
            reply = (
                "尚未配置默认 API Key。请到「设置」页填写供应商与 API Key，"
                "并勾选「设为默认」后重试。"
            )
            executed = []
        return reply, executed

    def reset(self):
        """清空上下文，开始新对话。"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # ---------- 内部 ----------

    def _default_key(self) -> dict:
        key = self.service.get_default()
        if key is None:
            raise NoKeyError()
        return key

    def _resolve_endpoint_model(self, key) -> tuple:
        info = PROVIDER_INFO.get(key["provider"], {})
        base = (key.get("base_url") or "").strip() or info.get("base_url")
        model = (key.get("model") or "").strip() or info.get("model")
        if not base:
            raise ValueError(
                f"供应商「{key['provider']}」缺少 Base URL，请在「设置」页补充。"
            )
        if not model:
            raise ValueError(
                f"供应商「{key['provider']}」缺少默认模型，请在「设置」页补充。"
            )
        return base.rstrip("/") + "/chat/completions", model

    def _run_tool_loop(self) -> tuple:
        key = self._default_key()
        endpoint, model = self._resolve_endpoint_model(key)
        executed = []

        for _ in range(MAX_TOOL_TURNS):
            message = self._chat_completion(endpoint, model, key["api_key"])
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                # 普通回复，结束
                self.messages.append(message)
                return message.get("content") or "", executed

            # 记录模型发起的工具调用，继续循环
            self.messages.append(message)
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                    if not isinstance(args, dict):
                        args = {}
                except json.JSONDecodeError:
                    args = {"_error": raw_args}
                executor = EXECUTORS.get(name)
                if executor is None:
                    result = f"未知技能：{name}"
                else:
                    try:
                        # 所有执行器统一为 executor(args) 签名（无参工具忽略参数）
                        result = executor(args)
                    except Exception as exc:  # 工具内部异常不打断对话
                        result = f"技能执行出错：{exc}"
                executed.append(result)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": result,
                    }
                )

        reply = "对话轮数已达上限，请简化请求后重试。"
        return reply, executed

    def _run_tool_loop_stream(self, on_chunk) -> tuple:
        """流式版工具循环：每轮走 SSE 流式请求，文本增量实时回调 on_chunk。"""
        key = self._default_key()
        endpoint, model = self._resolve_endpoint_model(key)
        executed = []

        for _ in range(MAX_TOOL_TURNS):
            message = self._chat_completion_stream(endpoint, model, key["api_key"], on_chunk)
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                # 普通回复，结束
                self.messages.append(message)
                return message.get("content") or "", executed

            # 记录模型发起的工具调用，继续循环
            self.messages.append(message)
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                    if not isinstance(args, dict):
                        args = {}
                except json.JSONDecodeError:
                    args = {"_error": raw_args}
                executor = EXECUTORS.get(name)
                if executor is None:
                    result = f"未知技能：{name}"
                else:
                    try:
                        # 所有执行器统一为 executor(args) 签名（无参工具忽略参数）
                        result = executor(args)
                    except Exception as exc:  # 工具内部异常不打断对话
                        result = f"技能执行出错：{exc}"
                executed.append(result)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": result,
                    }
                )

        reply = "对话轮数已达上限，请简化请求后重试。"
        return reply, executed

    def _chat_completion(self, endpoint, model, api_key) -> dict:
        """发起一次非流式请求，返回响应中的 message。失败抛友好异常。"""
        payload = {
            "model": model,
            "messages": self.messages,
            "tools": TOOL_SCHEMAS,
            "tool_choice": "auto",
            "temperature": 0.7,
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = self._extract_error(exc)
            raise RuntimeError(self._friendly_http_error(exc.code, detail)) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("无法连接 AI 服务器，请检查网络连接。") from exc
        except TimeoutError:
            raise RuntimeError("AI 请求超时，请稍后重试。")
        except json.JSONDecodeError as exc:
            raise RuntimeError("AI 服务返回了无法解析的内容，请稍后重试。") from exc

        try:
            return body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"AI 服务响应格式异常：{body}") from exc

    def _chat_completion_stream(self, endpoint, model, api_key, on_chunk) -> dict:
        """发起流式请求（stream=true），增量解析 SSE，回调 on_chunk(累计文本)。

        工具调用参数（tool_calls）同样可能分块到达，按 index 累积后返回完整 message。
        """
        payload = {
            "model": model,
            "messages": self.messages,
            "tools": TOOL_SCHEMAS,
            "tool_choice": "auto",
            "temperature": 0.7,
            "stream": True,
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        content_parts = []   # content 增量累积
        tool_acc = {}        # index -> 累积的 tool_call 结构
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                for raw in resp:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        content_parts.append(text)
                        if on_chunk:
                            on_chunk("".join(content_parts))
                    for tc in delta.get("tool_calls") or []:
                        idx = tc.get("index", 0)
                        acc = tool_acc.setdefault(
                            idx,
                            {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                        )
                        if tc.get("id"):
                            acc["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            acc["function"]["name"] = fn["name"]
                        if fn.get("arguments"):
                            acc["function"]["arguments"] += fn["arguments"]
        except urllib.error.HTTPError as exc:
            detail = self._extract_error(exc)
            raise RuntimeError(self._friendly_http_error(exc.code, detail)) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("无法连接 AI 服务器，请检查网络连接。") from exc
        except TimeoutError:
            raise RuntimeError("AI 请求超时，请稍后重试。")
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"流式响应读取中断：{exc}") from exc

        message = {"role": "assistant", "content": "".join(content_parts)}
        if tool_acc:
            message["tool_calls"] = [v for _, v in sorted(tool_acc.items())]
        return message

    @staticmethod
    def _extract_error(exc: "urllib.error.HTTPError") -> str:
        try:
            data = exc.read().decode("utf-8", errors="replace")
            obj = json.loads(data)
            return obj.get("error", {}).get("message") or data
        except Exception:
            return str(exc)

    @staticmethod
    def _friendly_http_error(code: int, detail: str) -> str:
        if code == 401:
            return "AI 服务鉴权失败（401），请检查「设置」里的 API Key 是否正确。"
        if code in (402, 429):
            return "AI 请求过于频繁或额度不足（429/402），请稍后重试。"
        if code >= 500:
            return f"AI 服务器繁忙（{code}），请稍后重试。"
        return f"AI 请求失败（{code}）：{detail[:200]}"