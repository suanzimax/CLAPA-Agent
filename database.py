# -*- coding: utf-8 -*-
"""
database.py
===========
数据库管理模块
"""

import sqlite3
import json
from typing import List, Tuple, Optional
from config import DB_FILE


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建文件记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                description TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # 创建对话记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                relevant_files TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_file_to_db(self, filename: str, filepath: str, file_type: str, 
                       file_size: int, category: str = "", description: str = "") -> int:
        """保存文件信息到数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO files (filename, filepath, file_type, file_size, category, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, filepath, file_type, file_size, category, description))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id
    
    def get_files_from_db(self, limit: Optional[int] = None) -> List[Tuple]:
        """从数据库获取文件列表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('SELECT * FROM files WHERE status = "active" ORDER BY upload_time DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM files WHERE status = "active" ORDER BY upload_time DESC')
        
        files = cursor.fetchall()
        conn.close()
        return files
    
    def delete_file_from_db(self, file_id: int) -> bool:
        """从数据库删除文件记录"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET status = "deleted" WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def save_conversation(self, user_message: str, bot_response: str, 
                         relevant_files: List[str] = None) -> int:
        """保存对话记录到数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        relevant_files_json = json.dumps(relevant_files) if relevant_files else "[]"
        
        cursor.execute('''
            INSERT INTO conversations (user_message, bot_response, relevant_files)
            VALUES (?, ?, ?)
        ''', (user_message, bot_response, relevant_files_json))
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conversation_id
    
    def get_conversations(self, limit: int = 50) -> List[Tuple]:
        """获取对话历史"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_message, bot_response, timestamp, relevant_files 
            FROM conversations 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        conversations = cursor.fetchall()
        conn.close()
        return conversations
    
    def clear_conversations(self) -> bool:
        """清空对话历史"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM conversations')
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False


# 创建全局数据库管理器实例
db_manager = DatabaseManager()