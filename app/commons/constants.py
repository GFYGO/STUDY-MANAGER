# -*- coding: utf-8 -*-
"""应用常量定义。"""

APP_NAME = "学习管理"
APP_VERSION = "0.2.0"

# 侧边导航项（与 QStackedWidget 页面顺序一一对应）
NAV_ITEMS = ["待办", "文档", "交流与AI", "设置", "插件", "应用"]

# 待办（作业）：科目预设
SUBJECT_PRESETS = [
    "语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理", "通用",
]

# 待办（作业）：作业类型预设
WORK_TYPE_PRESETS = [
    "练习", "试卷", "背诵", "抄写", "预习", "复习", "作文", "实验", "订正", "阅读", "其他",
]

# 待办（作业）：上交时间预设（下拉项，选择后换算为具体日期）
DUE_TIME_PRESETS = ["今天", "明天", "后天", "本周日"]

# 完成状态
TODO_STATUS = {0: "待完成", 1: "已完成"}
STATUS_PENDING = 0
STATUS_DONE = 1

# AI 供应商默认地址与默认模型（base_url/model 未填写时使用）
PROVIDER_INFO = {
    "OpenAI": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "DeepSeek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "通义千问": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "Kimi": {"base_url": "https://api.moonshot.cn/v1", "model": "kimi-k2"},
}

# 文档默认分类
DOC_CATEGORY_DEFAULT = "通用"

# 文档存放目录（项目根 data/documents，运行期生成）
DOC_DIR = "documents"