# -*- coding: utf-8 -*-
"""
config.py
=========
加速器控制系统实验室知识库管理系统 - 配置文件
"""

import os
import torch

# -------- 全局配置 --------
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
VECTOR_DIR = "./accelerator_knowledge_base"
DB_FILE = "./knowledge_base.db"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ✅ 在这里填写你的 DeepSeek API Key
API_KEY = "sk-5b78916edc064da39b381e45da03f80d"  # <<< 替换为真实 Key
LLM_MODEL = "deepseek-chat"

# 网络配置
NETWORK_TIMEOUT = 30  # 网络请求超时时间（秒）
ENABLE_OFFLINE_MODE = True  # 启用离线模式（网络失败时使用备用方案）

# 支持的文件类型
SUPPORTED_EXTENSIONS = {
    'pdf': 'PDF文档',
    'doc': 'Word文档',
    'docx': 'Word文档',
    'ppt': 'PowerPoint',
    'pptx': 'PowerPoint',
    'txt': '文本文件',
    'jpg': '图片',
    'jpeg': '图片',
    'png': '图片',
    'bmp': '图片',
    'tiff': '图片'
}

# Streamlit页面配置
PAGE_CONFIG = {
    "page_title": "加速器控制系统实验室知识库",
    "page_icon": "🔬",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# CSS样式
CUSTOM_CSS = """
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #1e3c72;
        background-color: rgba(30, 60, 114, 0.1);
        color: inherit;
    }
    .chat-message strong {
        color: #1e3c72;
    }
    .file-info {
        background-color: rgba(30, 60, 114, 0.1);
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        color: inherit;
    }
    /* 确保对话历史区域背景透明 */
    .chat-history {
        background-color: transparent !important;
    }
    /* 移除streamlit默认的白色背景 */
    .stContainer > div {
        background-color: transparent !important;
    }
</style>
"""