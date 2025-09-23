# -*- coding: utf-8 -*-
"""
session_manager.py
==================
会话管理模块 - 处理Streamlit会话状态
"""

import streamlit as st
from typing import List, Dict, Any, Optional


class SessionManager:
    """会话管理类"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """初始化会话状态"""
        # 知识库相关
        if "vector_store" not in st.session_state:
            st.session_state["vector_store"] = None
        
        # 对话历史
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        
        # 文件列表
        if "knowledge_base_files" not in st.session_state:
            st.session_state["knowledge_base_files"] = []
        
        # 当前对话上下文
        if "current_context" not in st.session_state:
            st.session_state["current_context"] = ""
        
        # 系统状态
        if "system_ready" not in st.session_state:
            st.session_state["system_ready"] = False
        
        # 用户设置
        if "user_settings" not in st.session_state:
            st.session_state["user_settings"] = {
                "max_chat_history": 50,
                "search_k": 5,
                "temperature": 0.7,
                "max_tokens": 2000
            }
    
    def get_vector_store(self):
        """获取向量存储"""
        return st.session_state.get("vector_store")
    
    def set_vector_store(self, store):
        """设置向量存储"""
        st.session_state["vector_store"] = store
    
    def get_chat_history(self) -> List[Dict]:
        """获取对话历史"""
        return st.session_state.get("chat_history", [])
    
    def add_chat_message(self, user_message: str, bot_response: str, 
                        context_files: List[str] = None):
        """添加对话消息"""
        chat_record = {
            "user": user_message,
            "bot": bot_response,
            "timestamp": st.session_state.get("current_time", ""),
            "context_files": context_files or []
        }
        
        chat_history = st.session_state.get("chat_history", [])
        chat_history.append(chat_record)
        
        # 限制历史记录长度
        max_history = st.session_state.get("user_settings", {}).get("max_chat_history", 50)
        if len(chat_history) > max_history:
            chat_history = chat_history[-max_history:]
        
        st.session_state["chat_history"] = chat_history
    
    def clear_chat_history(self):
        """清空对话历史"""
        st.session_state["chat_history"] = []
    
    def get_knowledge_base_files(self) -> List[Dict]:
        """获取知识库文件列表"""
        return st.session_state.get("knowledge_base_files", [])
    
    def set_knowledge_base_files(self, files: List[Dict]):
        """设置知识库文件列表"""
        st.session_state["knowledge_base_files"] = files
    
    def add_knowledge_base_file(self, file_info: Dict):
        """添加知识库文件"""
        files = st.session_state.get("knowledge_base_files", [])
        files.append(file_info)
        st.session_state["knowledge_base_files"] = files
    
    def remove_knowledge_base_file(self, file_id: str):
        """移除知识库文件"""
        files = st.session_state.get("knowledge_base_files", [])
        files = [f for f in files if f.get("id") != file_id]
        st.session_state["knowledge_base_files"] = files
    
    def get_current_context(self) -> str:
        """获取当前对话上下文"""
        return st.session_state.get("current_context", "")
    
    def set_current_context(self, context: str):
        """设置当前对话上下文"""
        st.session_state["current_context"] = context
    
    def is_system_ready(self) -> bool:
        """检查系统是否就绪"""
        return st.session_state.get("system_ready", False)
    
    def set_system_ready(self, ready: bool):
        """设置系统就绪状态"""
        st.session_state["system_ready"] = ready
    
    def get_user_settings(self) -> Dict:
        """获取用户设置"""
        return st.session_state.get("user_settings", {})
    
    def update_user_setting(self, key: str, value: Any):
        """更新用户设置"""
        settings = st.session_state.get("user_settings", {})
        settings[key] = value
        st.session_state["user_settings"] = settings
    
    def get_user_setting(self, key: str, default: Any = None):
        """获取单个用户设置"""
        settings = st.session_state.get("user_settings", {})
        return settings.get(key, default)
    
    def reset_session(self):
        """重置会话状态"""
        keys_to_keep = ["user_settings"]  # 保留用户设置
        
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        
        self.init_session_state()
    
    def get_session_info(self) -> Dict:
        """获取会话信息摘要"""
        return {
            "vector_store_exists": st.session_state.get("vector_store") is not None,
            "chat_history_count": len(st.session_state.get("chat_history", [])),
            "files_count": len(st.session_state.get("knowledge_base_files", [])),
            "system_ready": st.session_state.get("system_ready", False),
            "current_context_length": len(st.session_state.get("current_context", ""))
        }
    
    def export_chat_history(self) -> str:
        """导出对话历史为文本格式"""
        chat_history = self.get_chat_history()
        if not chat_history:
            return "暂无对话记录"
        
        export_text = "=== 加速器控制系统实验室 - 对话历史导出 ===\n\n"
        
        for i, chat in enumerate(chat_history, 1):
            export_text += f"【对话 {i}】\n"
            export_text += f"时间: {chat.get('timestamp', '未知')}\n"
            export_text += f"用户: {chat['user']}\n"
            export_text += f"助手: {chat['bot']}\n"
            if chat.get('context_files'):
                export_text += f"参考文件: {', '.join(chat['context_files'])}\n"
            export_text += "\n" + "="*50 + "\n\n"
        
        return export_text


# 创建全局会话管理器实例
session_manager = SessionManager()