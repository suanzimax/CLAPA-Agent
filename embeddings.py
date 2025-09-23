# -*- coding: utf-8 -*-
"""
embeddings.py
=============
嵌入模型管理模块
"""

import os
import shutil
import torch
from typing import List, Union
import socket
import threading

try:
    from langchain.embeddings.base import Embeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # 如果没有安装langchain，创建一个基础的Embeddings类
    class Embeddings:
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            raise NotImplementedError
        
        def embed_query(self, text: str) -> List[float]:
            raise NotImplementedError
    LANGCHAIN_AVAILABLE = False


class EmbeddingManager:
    """嵌入模型管理类 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EmbeddingManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self.embeddings = None
        self._huggingface_available = None  # 缓存Hugging Face连接状态
        self._setup_environment()
        self._initialized = True
    
    def _setup_environment(self):
        """设置环境变量"""
        # 设置缓存目录 - 只使用新的HF_HOME，移除废弃的TRANSFORMERS_CACHE
        os.environ['HF_HOME'] = './cache'
        # 移除可能存在的废弃环境变量
        if 'TRANSFORMERS_CACHE' in os.environ:
            del os.environ['TRANSFORMERS_CACHE']
        # 设置网络超时
        socket.setdefaulttimeout(10)
    
    def _check_internet_connection(self):
        """检查网络连接和Hugging Face可达性"""
        if self._huggingface_available is not None:
            return self._huggingface_available
        
        try:
            # 直接检查Hugging Face的可达性
            import requests
            response = requests.get("https://huggingface.co", timeout=5)
            self._huggingface_available = response.status_code == 200
            return self._huggingface_available
        except Exception:
            # 如果requests不可用，回退到socket检查
            try:
                socket.create_connection(("huggingface.co", 443), timeout=5)
                self._huggingface_available = True
                return True
            except OSError:
                self._huggingface_available = False
                return False
    
    def _clear_cache(self):
        """清除可能损坏的缓存"""
        cache_dir = os.path.expanduser("~/.cache/torch/sentence_transformers")
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print("已清理sentence-transformers缓存")
            except Exception as e:
                print(f"清理缓存失败: {e}")
    
    def create_embeddings_safe(self):
        """安全创建embedding模型，解决网络连接问题"""
        print(f"📊 嵌入管理器调用 - ID: {id(self)}, 已有嵌入: {self.embeddings is not None}")
        
        if self.embeddings is not None:
            print("✅ 使用已存在的嵌入模型")
            return self.embeddings
        
        # 检查网络连接
        has_internet = self._check_internet_connection()
        print(f"🌐 网络状态检查: {has_internet}")
        
        if not has_internet:
            print("⚠️ 网络连接不可用，直接使用离线模式（TF-IDF嵌入）")
            embedding_wrapper = TFIDFEmbeddingWrapper()
            self.embeddings = embedding_wrapper
            return embedding_wrapper
        
        # 清除可能损坏的缓存
        self._clear_cache()
        
        try:
            # 方法1：使用SentenceTransformer（在线模式）
            from sentence_transformers import SentenceTransformer
            import ssl
            
            # 解决SSL证书问题
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:
                pass
            
            # 尝试使用不同的模型
            model_names = [
                "sentence-transformers/paraphrase-MiniLM-L6-v2",
                "sentence-transformers/all-MiniLM-L6-v2", 
                "sentence-transformers/distilbert-base-nli-mean-tokens"
            ]
            
            for model_name in model_names:
                try:
                    print(f"🔄 尝试加载模型: {model_name}")
                    model = SentenceTransformer(
                        model_name,
                        device="cpu",
                        cache_folder="./cache"
                    )
                    
                    # 创建wrapper类
                    embedding_wrapper = EmbeddingWrapper(model)
                    print(f"✅ 使用 {model_name} 创建成功")
                    self.embeddings = embedding_wrapper
                    return embedding_wrapper
                    
                except Exception as e:
                    print(f"❌ 模型 {model_name} 失败: {e}")
                    # 如果是网络连接问题，标记为不可用并直接跳出
                    if "couldn't connect" in str(e).lower() or "huggingface.co" in str(e).lower():
                        print("🚫 检测到网络连接问题，跳过剩余在线模型")
                        self._huggingface_available = False
                        break
                    continue
            
            # 如果所有模型都失败，使用简单的TF-IDF方法
            print("⚠️ 所有Transformer模型都失败，使用TF-IDF嵌入")
            embedding_wrapper = TFIDFEmbeddingWrapper()
            self.embeddings = embedding_wrapper
            return embedding_wrapper
            
        except Exception as e:
            print(f"❌ 嵌入模型创建失败: {e}")
            # 最后的备用方案：使用简单的TF-IDF
            print("🔄 使用备用TF-IDF嵌入方案")
            embedding_wrapper = TFIDFEmbeddingWrapper()
            self.embeddings = embedding_wrapper
            return embedding_wrapper
    
    def get_embeddings(self):
        """获取嵌入模型实例"""
        if self.embeddings is None:
            return self.create_embeddings_safe()
        return self.embeddings


class EmbeddingWrapper(Embeddings):
    """SentenceTransformer的包装类，提供与LangChain兼容的接口"""
    
    def __init__(self, model):
        self.model = model
    
    def __call__(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """使对象可调用，兼容FAISS的调用方式"""
        if isinstance(texts, str):
            return self.embed_query(texts)
        else:
            return self.embed_documents(texts)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        return self.model.encode([text])[0].tolist()


class TFIDFEmbeddingWrapper(Embeddings):
    """TF-IDF嵌入包装类，作为网络连接失败时的备用方案"""
    
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        # 使用更稳定的TF-IDF配置，避免min_df/max_df冲突
        self.vectorizer = TfidfVectorizer(
            max_features=384,  # 使用常见的嵌入维度
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,  # 最小文档频率
            max_df=1.0,  # 避免与min_df冲突，使用1.0表示不过滤
            lowercase=True,
            token_pattern=r'(?u)\b\w\w+\b'  # 确保至少2个字符的token
        )
        self.fitted = False
        self.dimension = 384
        self.training_texts = []  # 存储训练文本以保持一致性
        
    def _ensure_fitted(self, texts: List[str]):
        """确保vectorizer已训练"""
        if not self.fitted:
            print("🔧 初始化TF-IDF向量化器...")
            # 合并所有文本进行训练，确保一致性
            all_texts = self.training_texts + texts
            
            # 如果文本太少，添加一些默认文本以确保TF-IDF工作正常
            if len(all_texts) < 2:
                all_texts.extend([
                    "default document for tfidf initialization",
                    "another default document to ensure proper tfidf training",
                    "additional text content for vectorizer training"
                ])
            
            try:
                self.vectorizer.fit(all_texts)
                self.fitted = True
                vocab_size = len(self.vectorizer.get_feature_names_out())
                print(f"✅ TF-IDF训练完成，词汇表大小: {vocab_size}")
            except Exception as e:
                print(f"❌ TF-IDF训练失败: {e}")
                # 使用最简单的配置重试
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.vectorizer = TfidfVectorizer(
                    max_features=384,
                    lowercase=True,
                    token_pattern=r'(?u)\b\w+\b'
                )
                self.vectorizer.fit(all_texts)
                self.fitted = True
                print("✅ 使用简化配置重新训练TF-IDF完成")
    
    def __call__(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """使对象可调用，兼容FAISS的调用方式"""
        try:
            if isinstance(texts, str):
                return self.embed_query(texts)
            else:
                return self.embed_documents(texts)
        except Exception as e:
            print(f"❌ TF-IDF嵌入调用失败: {e}")
            # 返回零向量作为备用
            if isinstance(texts, str):
                return [0.0] * self.dimension
            else:
                return [[0.0] * self.dimension for _ in texts]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档"""
        try:
            if not texts:
                return []
            
            # 存储训练文本
            self.training_texts.extend(texts)
            self._ensure_fitted(texts)
            
            # 转换文档为向量
            vectors = self.vectorizer.transform(texts).toarray()
            
            # 确保维度一致
            if vectors.shape[1] < self.dimension:
                # 如果特征数不足，用零填充
                import numpy as np
                padded_vectors = np.zeros((vectors.shape[0], self.dimension))
                padded_vectors[:, :vectors.shape[1]] = vectors
                vectors = padded_vectors
            elif vectors.shape[1] > self.dimension:
                # 如果特征数过多，截断
                vectors = vectors[:, :self.dimension]
                
            return vectors.tolist()
            
        except Exception as e:
            print(f"❌ TF-IDF文档嵌入失败: {e}")
            # 返回零向量
            return [[0.0] * self.dimension for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        try:
            if not text.strip():
                return [0.0] * self.dimension
                
            self._ensure_fitted([text])
            
            vector = self.vectorizer.transform([text]).toarray()[0]
            
            # 确保维度一致
            if len(vector) < self.dimension:
                import numpy as np
                padded_vector = np.zeros(self.dimension)
                padded_vector[:len(vector)] = vector
                vector = padded_vector
            elif len(vector) > self.dimension:
                vector = vector[:self.dimension]
                
            return vector.tolist()
            
        except Exception as e:
            print(f"❌ TF-IDF查询嵌入失败: {e}")
            # 返回零向量
            return [0.0] * self.dimension


# 创建全局嵌入管理器实例
embedding_manager = EmbeddingManager()