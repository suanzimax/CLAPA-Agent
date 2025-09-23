# -*- coding: utf-8 -*-
"""
llm_client.py
=============
LLM客户端模块 - 处理与DeepSeek API的交互
"""

import requests
from typing import List, Dict, Optional
from config import API_KEY, LLM_MODEL
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMClient:
    """LLM客户端类"""

    def __init__(self, api_key: str = API_KEY, model: str = LLM_MODEL):
        """
        初始化LLM客户端

        Args:
            api_key (str): DeepSeek API密钥
            model (str): 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

        # 系统提示词
        self.system_prompt = """你是加速器控制系统实验室的专业AI助手。你的任务是:
1. 基于提供的知识库内容回答用户问题
2. 提供准确、专业的技术指导
3. 当遇到设备故障、调试问题时，提供详细的解决方案
4. 如果知识库中没有相关信息，请明确告知用户，并建议用户上传相关文档

请用专业、友好的语调回答问题，特别注意处理CLAPA控制系统架构、EPICS、PVAccess等专业术语。"""

    def chat_with_deepseek(self, user_message: str, context: str,
                          chat_history: List[Dict] = None,
                          temperature: float = 0.7,
                          max_tokens: int = 2000) -> str:
        """
        与DeepSeek API对话

        Args:
            user_message (str): 用户输入的问题
            context (str): 知识库检索的上下文
            chat_history (List[Dict], optional): 对话历史
            temperature (float): 生成温度，控制回答的创造性
            max_tokens (int): 最大生成令牌数

        Returns:
            str: API返回的回答或错误信息
        """
        # 构建用户提示
        user_prompt = f"""
根据以下知识库内容回答用户问题：

知识库内容：
{context}

用户问题：{user_message}

请基于知识库内容提供准确、详细的回答。如果知识库中没有相关信息，请明确说明，并建议用户上传相关文档。
"""

        # 构建消息列表
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        # 添加历史对话（最近3轮）
        if chat_history:
            for msg in chat_history[-3:]:
                messages.append({"role": "user", "content": msg["user"]})
                messages.append({"role": "assistant", "content": msg["bot"]})

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_prompt})

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            logger.info("DeepSeek API调用成功")
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logger.error(f"API调用失败: {e}")
            return f"API调用失败: {e}"
        except Exception as e:
            logger.error(f"处理响应时出错: {e}")
            return f"处理响应时出错: {e}"

    def simple_chat(self, message: str, temperature: float = 0.7) -> str:
        """
        简单对话，不使用知识库上下文

        Args:
            message (str): 用户输入的问题
            temperature (float): 生成温度

        Returns:
            str: API返回的回答或错误信息
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message}
        ]

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 1500
            }

            response = requests.post(self.base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()

            result = response.json()
            logger.info("DeepSeek API简单对话调用成功")
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            logger.error(f"API调用失败: {e}")
            return f"API调用失败: {e}"
        except Exception as e:
            logger.error(f"处理响应时出错: {e}")
            return f"处理响应时出错: {e}"

    def set_system_prompt(self, prompt: str):
        """
        设置系统提示词

        Args:
            prompt (str): 新的系统提示词
        """
        self.system_prompt = prompt
        logger.info("系统提示词已更新")

    def get_system_prompt(self) -> str:
        """
        获取当前系统提示词

        Returns:
            str: 当前系统提示词
        """
        return self.system_prompt

    def validate_api(self) -> bool:
        """
        验证API密钥是否有效

        Returns:
            bool: True如果API密钥有效，False否则
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Test"},
                    {"role": "user", "content": "Ping"}
                ],
                "temperature": 0.7,
                "max_tokens": 10
            }

            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            logger.info("API密钥验证成功")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"API密钥验证失败: {e}")
            return False
        except Exception as e:
            logger.error(f"API密钥验证过程中出错: {e}")
            return False


# 创建全局LLM客户端实例
llm_client = LLMClient()