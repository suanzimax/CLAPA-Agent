# -*- coding: utf-8 -*-
"""
ui_components.py
================
UI组件模块 - 处理Streamlit界面组件
"""

import os
import tempfile
import shutil
from typing import List, Dict, Any
from datetime import datetime
import streamlit as st

from config import SUPPORTED_EXTENSIONS
from database import db_manager
from knowledge_base import kb_manager
from file_processor import file_processor


class UIComponents:
    """UI组件管理类"""
    
    def __init__(self):
        pass
    
    def render_sidebar(self):
        """渲染侧边栏 - 知识库管理"""
        with st.sidebar:
            st.header("📚 知识库管理")
            
            # 上传文件区域
            self._render_file_upload_section()
            
            # 文件管理区域
            self._render_file_management_section()
            
            # 知识库操作
            self._render_knowledge_base_operations()
    
    def _render_file_upload_section(self):
        """渲染文件上传区域"""
        with st.expander("📁 上传文件", expanded=True):
            uploaded_files = st.file_uploader(
                "选择文件",
                type=list(SUPPORTED_EXTENSIONS.keys()),
                accept_multiple_files=True,
                help="支持PDF、Word、PPT、图片等多种格式"
            )
            
            if uploaded_files:
                st.write(f"已选择 {len(uploaded_files)} 个文件")
                
                # 批量设置分类和描述
                col1, col2 = st.columns(2)
                with col1:
                    batch_category = st.selectbox(
                        "文件分类",
                        ["设备文档", "控制系统", "实验数据", "技术手册", "故障记录", "其他"],
                        key="batch_category"
                    )
                with col2:
                    batch_description = st.text_input("批量描述", key="batch_desc")
                
                if st.button("🚀 上传并构建知识库"):
                    self._handle_file_upload(uploaded_files, batch_category, batch_description)
    
    def _handle_file_upload(self, uploaded_files, batch_category: str, batch_description: str):
        """处理文件上传"""
        # 保存文件
        temp_dir = tempfile.mkdtemp()
        
        try:
            progress_bar = st.progress(0, text="正在上传文件...")
            
            # 处理上传的文件
            file_paths, file_info = file_processor.process_uploaded_files(
                uploaded_files, temp_dir, batch_category, batch_description
            )
            
            # 保存文件信息到数据库
            for i, (file_path, info) in enumerate(zip(file_paths, file_info)):
                db_manager.save_file_to_db(
                    info['name'],
                    file_path,
                    info['type'],
                    info['size'],
                    info['category'],
                    info['description']
                )
                
                progress_bar.progress((i + 1) / len(uploaded_files), 
                                    text=f"已上传 {i + 1}/{len(uploaded_files)} 个文件")
            
            # 构建知识库
            store = kb_manager.build_knowledge_base(file_paths, file_info)
            if store:
                st.session_state["vector_store"] = store
                st.success("知识库更新成功！")
                st.rerun()
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _render_file_management_section(self):
        """渲染文件管理区域"""
        with st.expander("📋 文件管理"):
            files = db_manager.get_files_from_db(limit=10)
            if files:
                st.write(f"知识库中共有 {len(db_manager.get_files_from_db())} 个文件")
                
                for file_data in files:
                    file_id, filename, _, file_type, file_size, upload_time, category, description, _ = file_data
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="file-info">
                            <strong>{filename}</strong> ({file_type.upper()})<br>
                            <small>分类: {category} | 大小: {file_size} bytes</small><br>
                            <small>上传时间: {upload_time}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🗑️", key=f"delete_{file_id}", help="删除文件"):
                            if db_manager.delete_file_from_db(file_id):
                                st.success(f"已删除文件: {filename}")
                                st.rerun()
                            else:
                                st.error("删除文件失败")
            else:
                st.info("暂无上传文件")
    
    def _render_knowledge_base_operations(self):
        """渲染知识库操作区域"""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 加载知识库"):
                try:
                    store = kb_manager.load_existing_knowledge_base()
                    st.session_state["vector_store"] = store
                    st.success("知识库加载成功！")
                except FileNotFoundError:
                    st.warning("未找到现有知识库")
                except Exception as e:
                    st.error(f"加载知识库失败: {e}")
        
        with col2:
            if st.button("🗑️ 清空知识库"):
                if kb_manager.clear_knowledge_base():
                    st.session_state["vector_store"] = None
                    st.success("知识库已清空")
                    st.rerun()
                else:
                    st.error("清空知识库失败")
    
    def render_chat_interface(self):
        """渲染对话界面"""
        st.header("💬 智能对话系统")
        
        # 显示对话历史
        self._render_chat_history()
        
        # 注意：输入区域和操作按钮在main.py中单独渲染，避免重复
    
    def _render_chat_history(self):
        """渲染对话历史"""
        if st.session_state.get("chat_history"):
            st.subheader("对话历史")
            for chat in st.session_state["chat_history"]:
                with st.container():
                    st.markdown(f"""
                    <div class="chat-message">
                        <strong>🧑‍🔬 用户:</strong> {chat['user']}<br><br>
                        <strong>🤖 助手:</strong> {chat['bot']}
                    </div>
                    """, unsafe_allow_html=True)
    
    def _render_input_area(self):
        """渲染输入区域"""
        # 创建两列布局
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_input = st.text_area(
                "请输入您的问题",
                placeholder="例如：\n• 我想了解CLAPA控制系统架构\n• 调试光谱仪时遇到了XX问题，如何解决？\n• 设备启动流程是什么？",
                height=100,
                key="user_input"
            )
        
        with col2:
            st.write("📎 上传相关文件")
            query_files = st.file_uploader(
                "问题相关文件",
                type=list(SUPPORTED_EXTENSIONS.keys()),
                accept_multiple_files=True,
                key="query_files"
            )
        
        return user_input, query_files
    
    def _render_chat_controls(self):
        """渲染对话控制按钮"""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            send_clicked = st.button("🚀 发送消息", type="primary")
        
        with col2:
            clear_clicked = st.button("🗑️ 清空对话历史")
        
        return send_clicked, clear_clicked
    
    def display_file_info(self, files_data: List[tuple]):
        """显示文件信息表格"""
        if not files_data:
            st.info("暂无文件")
            return
        
        # 创建表格数据
        table_data = []
        for file_data in files_data:
            file_id, filename, _, file_type, file_size, upload_time, category, description, _ = file_data
            table_data.append({
                "ID": file_id,
                "文件名": filename,
                "类型": file_type.upper(),
                "大小(KB)": round(file_size / 1024, 2),
                "分类": category,
                "上传时间": upload_time
            })
        
        st.dataframe(table_data, use_container_width=True)
    
    def show_stats(self):
        """显示统计信息"""
        files = db_manager.get_files_from_db()
        conversations = db_manager.get_conversations(limit=100)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📁 文件总数", len(files))
        
        with col2:
            st.metric("💬 对话记录", len(conversations))
        
        with col3:
            # 计算总文件大小
            total_size = sum([file[4] for file in files]) if files else 0
            st.metric("💾 存储空间(MB)", round(total_size / (1024 * 1024), 2))


# 创建全局UI组件管理器实例
ui_components = UIComponents()