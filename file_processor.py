# -*- coding: utf-8 -*-
"""
file_processor.py
=================
文件处理模块
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import pytesseract
import streamlit as st

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredFileLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
    UnstructuredImageLoader,
)
from langchain.schema import Document


class FileProcessor:
    """文件处理类"""
    
    def __init__(self):
        pass
    
    def extract_text_from_image(self, image_path: str) -> str:
        """从图片中提取文字（OCR）"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='eng+chi_sim')
            return text
        except Exception as e:
            st.warning(f"图片OCR失败: {e}")
            return ""
    
    def load_file_to_docs(self, file_path: str, file_type: str = None) -> List[Document]:
        """根据文件类型加载文档"""
        try:
            suffix = file_path.lower().rsplit(".", 1)[-1] if not file_type else file_type
            
            if suffix == "pdf":
                loader = PyPDFLoader(file_path)
                docs = loader.load()
            elif suffix in ("doc", "docx"):
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
            elif suffix in ("ppt", "pptx"):
                loader = UnstructuredPowerPointLoader(file_path)
                docs = loader.load()
            elif suffix in ("jpg", "jpeg", "png", "bmp", "tiff"):
                # 图片处理：使用OCR提取文字
                text = self.extract_text_from_image(file_path)
                if text.strip():
                    docs = [Document(page_content=text, metadata={"source": file_path, "type": "image"})]
                else:
                    docs = [Document(page_content="[图片文件 - 无可提取文字]", metadata={"source": file_path, "type": "image"})]
            else:
                # 其他文件类型
                loader = UnstructuredFileLoader(file_path)
                docs = loader.load()
                
            return docs
        except Exception as e:
            st.warning(f"⚠️ 解析文件 {Path(file_path).name} 失败: {e}")
            return [Document(page_content=f"[文件解析失败: {Path(file_path).name}]", 
                           metadata={"source": file_path, "error": str(e)})]
    
    def process_uploaded_files(self, uploaded_files, temp_dir: str, 
                             batch_category: str = "", batch_description: str = "") -> tuple:
        """处理上传的文件列表"""
        file_paths = []
        file_info = []
        
        for uploaded_file in uploaded_files:
            # 保存文件
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            file_paths.append(file_path)
            file_info.append({
                'name': uploaded_file.name,
                'type': uploaded_file.name.split('.')[-1].lower(),
                'size': uploaded_file.size,
                'category': batch_category,
                'description': batch_description
            })
        
        return file_paths, file_info
    
    def validate_file_type(self, filename: str, supported_extensions: Dict[str, str]) -> bool:
        """验证文件类型是否支持"""
        file_ext = filename.lower().split('.')[-1]
        return file_ext in supported_extensions
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件基本信息"""
        file_path_obj = Path(file_path)
        
        return {
            'name': file_path_obj.name,
            'size': file_path_obj.stat().st_size if file_path_obj.exists() else 0,
            'extension': file_path_obj.suffix.lower().lstrip('.'),
            'stem': file_path_obj.stem
        }


# 创建全局文件处理器实例
file_processor = FileProcessor()

