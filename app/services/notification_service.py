# -*- coding: utf-8 -*-
"""多渠道消息通知：邮件(SMTP) / 本地系统通知(托盘气泡)。

配置保存在 data/notify_config.json，邮箱授权码以加密形式落盘。
"""

import json
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

from app.security.crypto import decrypt, encrypt

CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "notify_config.json"

DEFAULT_CONFIG = {
    "email": {
        "enable": False,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "use_ssl": True,
        "sender": "",
        "auth_code_encrypted": "",
        "to": "",
    },
    "local": {"enable": True},
}


def _default_cfg() -> dict:
    return json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝


class NotificationService:
    def __init__(self):
        self._cfg = self.load_config()

    # ---------- 配置 ----------

    def load_config(self) -> dict:
        if not CONFIG_PATH.exists():
            cfg = _default_cfg()
            self.save_config(cfg)
            return cfg
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = _default_cfg()
            for section in merged:
                merged[section].update(cfg.get(section) or {})
            return merged
        except Exception:
            return _default_cfg()

    def save_config(self, cfg: dict) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def set_email_auth_code(self, cfg: dict, auth_code: str) -> str:
        """加密授权码写入配置；返回密文。"""
        encrypted = encrypt(auth_code) if auth_code else ""
        cfg["email"]["auth_code_encrypted"] = encrypted
        return encrypted

    def get_email_auth_code(self, cfg: dict) -> str:
        token = cfg["email"].get("auth_code_encrypted") or ""
        if not token:
            return ""
        try:
            return decrypt(token)
        except Exception:
            return ""

    # ---------- 发送 ----------

    def send(self, subject: str, content: str, tray=None) -> list:
        """按已启用渠道发送，返回逐渠道结果说明列表。

        tray：QSystemTrayIcon（用于本地系统通知气泡），可为 None。
        """
        self._cfg = self.load_config()
        results = []
        email = self._cfg["email"]
        if email.get("enable"):
            results.append("邮件：" + self._send_email(email, subject, content))
        if self._cfg["local"].get("enable"):
            results.append("本地通知：" + self._send_local(tray, subject, content))
        if not results:
            results.append("未启用任何通知渠道，请先在「设置」中开启并配置。")
        return results

    def _send_local(self, tray, subject: str, content: str) -> str:
        if tray is None:
            return "未启用系统托盘，通知气泡未显示。"
        try:
            tray.showMessage("学习管理", f"{subject}\n{content}", msecs=5000)
            return "系统通知气泡已显示。"
        except Exception as exc:
            return f"显示失败：{exc}"

    def _send_email(self, email_cfg: dict, subject: str, content: str) -> str:
        smtp_host = (email_cfg.get("smtp_host") or "").strip()
        sender = (email_cfg.get("sender") or "").strip()
        to = (email_cfg.get("to") or "").strip()
        auth_code = self.get_email_auth_code(email_cfg)
        if not smtp_host or not sender or not to or not auth_code:
            return "邮箱未完整配置（需 SMTP 服务器/发件邮箱/授权码/收件人）。"

        try:
            smtp_port = int(email_cfg.get("smtp_port") or 465)
        except ValueError:
            return "SMTP 端口不是有效数字。"
        use_ssl = bool(email_cfg.get("use_ssl", True))

        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header("学习管理", "utf-8")), sender))
        msg["To"] = to

        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                server.starttls()
            with server:
                server.login(sender, auth_code)
                server.sendmail(sender, [to], msg.as_string())
            return f"已发送至 {to}"
        except smtplib.SMTPAuthenticationError as exc:
            return f"邮箱授权码错误，请检查（{exc.smtp_code}）。"
        except Exception as exc:
            return f"发送失败：{exc}"