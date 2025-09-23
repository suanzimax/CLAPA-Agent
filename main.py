# -*- coding: utf-8 -*-
"""
main.py
=======
加速器控制系统实验室知识库管理与RAG对话系统 - 主程序

专为加速器控制系统实验室设计的知识库管理系统：
- 支持多种文件格式（PDF、Word、PPT、图片等）
- 知识库管理功能
- 基于RAG的智能对话系统
- 多模态内容理解
"""

import os
import tempfile
import shutil
from datetime import datetime
import streamlit as st

# 导入自定义模块
from config import PAGE_CONFIG, CUSTOM_CSS, SUPPORTED_EXTENSIONS
from database import db_manager
from session_manager import session_manager
from knowledge_base import kb_manager
from llm_client import llm_client
from ui_components import ui_components
from file_processor import file_processor


class AcceleratorKnowledgeSystem:
    """加速器控制系统知识库主应用"""
    
    def __init__(self):
        self.setup_page()
        session_manager.init_session_state()
        # 检查并修复向量数据库兼容性问题
        self.check_vector_store_compatibility()
    
    def check_vector_store_compatibility(self):
        """检查向量数据库兼容性"""
        try:
            from config import VECTOR_DIR
            if os.path.exists(VECTOR_DIR) and not hasattr(st.session_state, 'compatibility_checked'):
                # 标记已检查，避免重复检查
                st.session_state.compatibility_checked = True
                
                # 检查当前嵌入模型类型
                from embeddings import embedding_manager
                embeddings = embedding_manager.get_embeddings()
                if hasattr(embeddings, 'vectorizer'):  # TF-IDF嵌入
                    print("🔄 检测到切换到TF-IDF嵌入，清理旧的向量数据库...")
                    try:
                        shutil.rmtree(VECTOR_DIR)
                        st.session_state.show_compatibility_warning = True
                        print("✅ 已清理旧的向量数据库")
                        return
                    except Exception as e:
                        print(f"清理向量数据库时出错: {e}")
                
                # 尝试加载现有知识库，如果失败说明不兼容
                try:
                    kb_manager.load_existing_knowledge_base()
                    print("✅ 向量数据库兼容性检查通过")
                except Exception as e:
                    print(f"⚠️ 检测到向量数据库不兼容: {e}")
                    # 如果不兼容，清理数据并在session中标记
                    if any(keyword in str(e).lower() for keyword in ["dimension", "embedding", "shape", "vector", "size", "需要重建"]):
                        try:
                            if os.path.exists(VECTOR_DIR):
                                shutil.rmtree(VECTOR_DIR)
                            st.session_state.show_compatibility_warning = True
                            print("🔄 已清理不兼容的向量数据库")
                        except:
                            pass
        except Exception as e:
            print(f"向量数据库兼容性检查失败: {e}")

    def setup_page(self):
        """设置页面配置"""
        st.set_page_config(**PAGE_CONFIG)
        
        # 应用自定义CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        
        # 主标题
        st.markdown(
            '<div class="main-header">'
            '<h1>🔬 加速器控制系统实验室知识库管理系统</h1>'
            '<p>专业的多模态知识库管理与智能对话平台</p>'
            '</div>', 
            unsafe_allow_html=True
        )
    
    def run(self):
        """运行主应用"""
        # 渲染侧边栏
        ui_components.render_sidebar()
        
        # 渲染主界面
        self.render_main_interface()
    
    def render_main_interface(self):
        """渲染主界面"""
        # 显示兼容性警告（如果需要）
        if st.session_state.get('show_compatibility_warning', False):
            st.warning("⚠️ 检测到嵌入模型已更换，原有的知识库数据已清理。请重新上传文件构建知识库。")
            if st.button("我知道了", key="ack_compatibility"):
                st.session_state.show_compatibility_warning = False
                st.rerun()
        
        # 渲染对话界面
        ui_components.render_chat_interface()
        
        # 处理用户输入
        user_input, query_files = ui_components._render_input_area()
        send_clicked, clear_clicked = ui_components._render_chat_controls()
        
        # 处理发送消息
        if send_clicked:
            self.handle_send_message(user_input, query_files)
        
        # 处理清空对话历史
        if clear_clicked:
            session_manager.clear_chat_history()
            st.rerun()
    
    def handle_send_message(self, user_input: str, query_files=None):
        """处理发送消息"""
        if not user_input.strip():
            st.warning("请输入问题！")
            return
        
        vector_store = session_manager.get_vector_store()
        if vector_store is None:
            st.warning("请先上传文件并构建知识库！")
            return
        
        with st.spinner("正在思考中..."):
            try:
                # 处理查询文件
                enhanced_query = self.process_query_files(user_input, query_files)
                
                # 搜索知识库
                relevant_docs = kb_manager.search_knowledge_base(enhanced_query, vector_store)
                context = kb_manager.build_context_from_docs(relevant_docs)
                
                # 获取对话历史
                chat_history = session_manager.get_chat_history()
                
                # 获取AI回答
                bot_response = llm_client.chat_with_deepseek(
                    enhanced_query, 
                    context, 
                    chat_history
                )
                
                # 保存对话
                context_files = [doc.metadata.get('filename', '') for doc in relevant_docs]
                session_manager.add_chat_message(user_input, bot_response, context_files)
                
                # 保存到数据库
                db_manager.save_conversation(user_input, bot_response, context_files)
                
                st.rerun()
                
            except Exception as e:
                st.error(f"处理消息时出错: {e}")
    
    def process_query_files(self, user_input: str, query_files) -> str:
        """处理查询相关的上传文件"""
        if not query_files:
            return user_input
        
        temp_dir = tempfile.mkdtemp()
        query_context = ""
        
        try:
            for query_file in query_files:
                file_path = os.path.join(temp_dir, query_file.name)
                with open(file_path, "wb") as f:
                    f.write(query_file.getbuffer())
                
                # 提取文件内容
                docs = file_processor.load_file_to_docs(file_path)
                for doc in docs:
                    query_context += f"\n[上传文件: {query_file.name}]\n{doc.page_content[:500]}\n"
            
            # 将上传文件内容添加到查询中
            enhanced_query = f"{user_input}\n\n相关文件内容：{query_context}"
            return enhanced_query
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def main():
    """主函数"""
    try:
        # 创建并运行应用
        app = AcceleratorKnowledgeSystem()
        app.run()
        
    except Exception as e:
        st.error(f"应用启动失败: {e}")
        st.info("请检查配置文件和依赖包是否正确安装")


if __name__ == "__main__":
    main()