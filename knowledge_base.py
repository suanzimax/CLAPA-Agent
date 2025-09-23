# -*- coding: utf-8 -*-
"""
knowledge_base.py
=================
知识库管理模块
"""

import os
import shutil
from typing import List, Dict, Any
from datetime import datetime
import streamlit as st

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from config import CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_DIR
from embeddings import embedding_manager
from file_processor import file_processor


class KnowledgeBaseManager:
    """知识库管理类"""
    
    def __init__(self):
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
    
    def build_knowledge_base(self, file_paths: List[str], file_info: List[Dict]) -> FAISS:
        """构建知识库"""
        st.info("🔄 正在构建知识库，请稍候...")
        
        docs: List[Document] = []
        progress_bar = st.progress(0, text="正在解析文档...")
        total_files = len(file_paths)
        
        # 1. 解析文档
        for idx, (fp, info) in enumerate(zip(file_paths, file_info)):
            try:
                file_docs = file_processor.load_file_to_docs(fp, info.get('type'))
                # 添加文件信息到元数据
                for doc in file_docs:
                    doc.metadata.update({
                        'filename': info['name'],
                        'category': info.get('category', ''),
                        'description': info.get('description', ''),
                        'file_type': info.get('type', ''),
                        'upload_time': datetime.now().isoformat()
                    })
                docs.extend(file_docs)
                progress_bar.progress((idx + 1) / total_files, 
                                    text=f"已解析文件 {idx + 1}/{total_files}")
            except Exception as e:
                st.warning(f"文件 {info['name']} 解析失败: {e}")
                continue
        
        if not docs:
            st.warning("❌ 未读取到任何可用文本，知识库未更新。")
            return None
        
        # 2. 分割文档
        progress_bar.progress(0.3, text="正在分割文档...")
        chunks = self.text_splitter.split_documents(docs)
        progress_bar.progress(0.6, text=f"已分割为 {len(chunks)} 个文本块...")
        
        # 3. 创建嵌入模型
        try:
            embeddings = embedding_manager.get_embeddings()
            progress_bar.progress(0.65, text="嵌入模型加载成功...")
        except Exception as e:
            st.error(f"创建嵌入模型失败: {e}")
            progress_bar.progress(1.0, text="❌ 知识库构建失败")
            return None
        
        # 4. 创建或更新向量数据库
        if os.path.exists(VECTOR_DIR):
            progress_bar.progress(0.7, text="正在更新现有知识库...")
            try:
                store = FAISS.load_local(
                    VECTOR_DIR,
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
                store.add_documents(chunks)
            except Exception as e:
                st.warning(f"加载现有知识库失败，重新创建: {e}")
                progress_bar.progress(0.8, text="正在创建新知识库...")
                store = FAISS.from_documents(chunks, embedding=embeddings)
        else:
            progress_bar.progress(0.7, text="正在创建新知识库...")
            store = FAISS.from_documents(chunks, embedding=embeddings)
        
        # 5. 保存知识库
        progress_bar.progress(0.9, text="正在保存知识库...")
        try:
            os.makedirs(VECTOR_DIR, exist_ok=True)
            store.save_local(VECTOR_DIR)
            progress_bar.progress(1.0, text="✅ 知识库构建完成！")
            st.success(f"✅ 知识库已更新，处理了 {len(chunks)} 个文本块")
            self.vector_store = store
            return store
        except Exception as e:
            st.error(f"保存知识库失败: {e}")
            progress_bar.progress(1.0, text="❌ 知识库保存失败")
            return None
    
    def load_existing_knowledge_base(self) -> FAISS:
        """加载现有知识库"""
        if not os.path.exists(VECTOR_DIR):
            raise FileNotFoundError("未找到现有知识库")
        
        embeddings = embedding_manager.get_embeddings()
        
        # 检查是否为TF-IDF嵌入，如果是则强制重建
        if hasattr(embeddings, 'vectorizer'):  # TF-IDF嵌入
            print("🔄 检测到TF-IDF嵌入，为确保兼容性将重建知识库")
            # 清除旧的向量数据库
            try:
                shutil.rmtree(VECTOR_DIR)
                print("✅ 已清理旧的向量数据库")
            except Exception as e:
                print(f"清理向量数据库时出错: {e}")
            raise FileNotFoundError("需要重建知识库以匹配新的嵌入模型")
        
        try:
            store = FAISS.load_local(
                VECTOR_DIR,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            self.vector_store = store
            print("✅ 成功加载现有知识库")
            return store
        except Exception as e:
            print(f"❌ 加载知识库失败: {e}")
            # 如果加载失败，可能是嵌入模型不兼容，清理旧数据
            if any(keyword in str(e).lower() for keyword in ["dimension", "embedding", "shape", "vector", "size"]):
                print("🔄 检测到嵌入模型不兼容，清理旧的向量数据库...")
                try:
                    shutil.rmtree(VECTOR_DIR)
                    print("✅ 已清理不兼容的向量数据库")
                except:
                    pass
            raise e
    
    def search_knowledge_base(self, query: str, store: FAISS = None, k: int = 5) -> List[Document]:
        """在知识库中搜索相关内容"""
        if store is None:
            store = self.vector_store
        
        if store is None:
            return []
        
        try:
            print(f"🔍 开始搜索知识库，查询: {query[:50]}...")
            docs = store.similarity_search(query, k=k)
            print(f"✅ 搜索完成，找到 {len(docs)} 个相关文档")
            return docs
        except Exception as e:
            error_msg = f"搜索知识库时出错: {e}"
            print(f"❌ {error_msg}")
            st.error(error_msg)
            
            # 如果是嵌入维度不兼容的问题，强制重建知识库
            if any(keyword in str(e).lower() for keyword in ["dimension", "embedding", "shape", "vector", "size"]):
                st.warning("⚠️ 检测到嵌入模型不兼容问题，正在自动修复...")
                try:
                    # 清除不兼容的向量数据库
                    if os.path.exists(VECTOR_DIR):
                        shutil.rmtree(VECTOR_DIR)
                        print("🔄 已清除不兼容的向量数据库")
                    
                    # 重置向量存储
                    self.vector_store = None
                    st.info("💡 知识库已重置，请重新上传文件以重建知识库。")
                    st.rerun()
                except Exception as reset_error:
                    print(f"❌ 重置知识库失败: {reset_error}")
                    st.error(f"重置知识库失败: {reset_error}")
            
            return []
    
    def build_context_from_docs(self, docs: List[Document]) -> str:
        """从文档构建上下文"""
        if not docs:
            return "暂无相关资料。"
        
        context_parts = []
        for i, doc in enumerate(docs):
            filename = doc.metadata.get('filename', '未知文件')
            file_type = doc.metadata.get('file_type', '')
            content = doc.page_content[:800]  # 限制长度
            
            context_parts.append(f"[资料{i+1}] 来源: {filename} ({file_type})\n内容: {content}")
        
        return "\n\n".join(context_parts)
    
    def get_vector_store(self) -> FAISS:
        """获取当前向量存储实例"""
        return self.vector_store
    
    def set_vector_store(self, store: FAISS):
        """设置向量存储实例"""
        self.vector_store = store
    
    def clear_knowledge_base(self) -> bool:
        """清空知识库"""
        try:
            if os.path.exists(VECTOR_DIR):
                shutil.rmtree(VECTOR_DIR)
            self.vector_store = None
            return True
        except Exception:
            return False


# 创建全局知识库管理器实例
kb_manager = KnowledgeBaseManager()