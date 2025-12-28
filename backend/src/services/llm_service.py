"""
大模型服务模块
负责与大模型API通信，实现知识点和关系抽取
"""

import httpx
import json
from typing import List, Dict, Optional, Any
from loguru import logger
from retry import retry

from ..core.config import settings
from ..models.schemas import KnowledgePoint


class LLMServices:
    """大模型服务类"""
    
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_endpoint = settings.LLM_API_ENDPOINT
        self.model_name = settings.LLM_MODEL_NAME
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.retry_count = settings.LLM_RETRY_COUNT
        self.timeout = settings.LLM_TIMEOUT
        
    @retry(Exception, tries=3, delay=1, backoff=2, jitter=0.5)
    async def _call_llm_api(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        调用大模型API，带重试机制
        
        Args:
            messages: 消息列表
            
        Returns:
            API响应结果
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": 0.9
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"大模型API调用失败: HTTP {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"大模型API请求失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"大模型API调用异常: {str(e)}")
            raise
        
        return None
    
    async def extract_knowledge_points(self, text: str, context: Optional[str] = None) -> List[KnowledgePoint]:
        """
        从文本中提取知识点，支持批量处理长文本
        
        Args:
            text: 待分析文本
            context: 上下文信息（如章节标题等）
            
        Returns:
            知识点列表
        """
        try:
            logger.info(f"开始提取知识点，文本长度: {len(text)} 字符")
            
            # 定义批量处理的文本块大小
            CHUNK_SIZE = 3000
            OVERLAP_SIZE = 300
            
            # 将长文本分割成多个重叠的块
            chunks = []
            for i in range(0, len(text), CHUNK_SIZE - OVERLAP_SIZE):
                chunk = text[i:i + CHUNK_SIZE]
                chunks.append(chunk)
            
            all_knowledge_points = []
            
            # 逐块处理文本
            for i, chunk in enumerate(chunks):
                logger.info(f"处理文本块 {i+1}/{len(chunks)}")
                
                # 构建提示词
                messages = [
                    {
                        "role": "system",
                        "content": "你是一个专业的知识点提取助手，请从给定文本中提取关键知识点。每个知识点应包含标题和内容，保持简洁明了。输出格式为JSON数组，包含id、title和content字段，不要添加任何解释性文字。"
                    },
                    {
                        "role": "user",
                        "content": f"从以下文本中提取知识点，上下文：{context}\n\n文本：{chunk}"
                    }
                ]
                
                # 调用大模型API
                response = await self._call_llm_api(messages)
                
                if not response or "choices" not in response:
                    logger.error(f"大模型API响应格式错误，块 {i+1}")
                    continue
                
                # 解析响应
                llm_output = response["choices"][0]["message"]["content"]
                logger.debug(f"大模型输出 (块 {i+1}): {llm_output}")
                
                # 提取JSON部分
                json_start = llm_output.find("[")
                json_end = llm_output.rfind("]") + 1
                
                if json_start == -1 or json_end == 0:
                    logger.error(f"无法从大模型输出中提取JSON格式，块 {i+1}")
                    continue
                
                json_str = llm_output[json_start:json_end]
                knowledge_points_data = json.loads(json_str)
                
                # 转换为KnowledgePoint对象
                for kp_data in knowledge_points_data:
                    knowledge_point = KnowledgePoint(
                        id=kp_data.get("id"),
                        title=kp_data.get("title", ""),
                        content=kp_data.get("content", ""),
                        start_page=1,  # 默认为1，后续会更新
                        end_page=1,    # 默认为1，后续会更新
                        page_count=1
                    )
                    all_knowledge_points.append(knowledge_point)
            
            # 去重知识点（基于标题和内容的组合）
            unique_kps = []
            seen_kps = set()
            for kp in all_knowledge_points:
                kp_key = (kp.title.strip(), kp.content.strip())
                if kp_key not in seen_kps:
                    seen_kps.add(kp_key)
                    unique_kps.append(kp)
            
            logger.info(f"成功提取 {len(unique_kps)} 个知识点 (去重后)")
            return unique_kps
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"知识点提取失败: {str(e)}")
        
        return []
    
    async def extract_relations(self, knowledge_points: List[KnowledgePoint]) -> List[Dict[str, Any]]:
        """
        提取知识点之间的关联关系
        
        Args:
            knowledge_points: 知识点列表
            
        Returns:
            知识点关联关系列表，每个元素包含source_id、target_id、relation_type和weight字段
        """
        try:
            logger.info(f"开始提取关联关系，知识点数量: {len(knowledge_points)}")
            
            # 准备知识点文本
            kp_texts = []
            for kp in knowledge_points:
                kp_texts.append(f"ID: {kp.id}, 标题: {kp.title}, 内容: {kp.content[:200]}")
            
            kp_list_text = "\n".join(kp_texts)
            
            # 构建提示词
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的知识关系分析助手，请分析给定知识点之间的关联关系。对于每对相关知识点，请识别出具体的关系类型（如：依赖、包含、相似、对比、因果、递进等），并为关系分配0-1之间的权重。输出格式为JSON，包含一个'edges'数组，每个元素包含'source_id'、'target_id'、'relation_type'和'weight'字段。不要添加任何解释性文字，只输出纯JSON格式。"
                },
                {
                    "role": "user",
                    "content": f"分析以下知识点之间的关联关系：\n\n{kp_list_text}"
                }
            ]
            
            # 调用大模型API
            response = await self._call_llm_api(messages)
            
            if not response or "choices" not in response:
                logger.error("大模型API响应格式错误")
                return []
            
            # 解析响应
            llm_output = response["choices"][0]["message"]["content"]
            logger.debug(f"大模型输出: {llm_output}")
            
            # 处理代码块标记，提取纯JSON内容
            processed_output = llm_output.strip()
            
            # 移除可能的代码块标记
            if processed_output.startswith('```json'):
                processed_output = processed_output[7:]
            if processed_output.startswith('```'):
                processed_output = processed_output[3:]
            if processed_output.endswith('```'):
                processed_output = processed_output[:-3]
            
            # 提取JSON部分
            json_start = processed_output.find("{")
            json_end = processed_output.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("无法从大模型输出中提取JSON格式")
                return []
            
            json_str = processed_output[json_start:json_end]
            result = json.loads(json_str)
            edges = result.get("edges", [])
            
            # 确保edges是列表类型
            if not isinstance(edges, list):
                logger.error(f"关联关系提取结果不是列表类型: {type(edges)}")
                return []
            
            logger.info(f"成功提取 {len(edges)} 条关联关系")
            return edges
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.error(f"JSON字符串: {json_str if 'json_str' in locals() else '未提取到'}")
        except Exception as e:
            logger.error(f"关联关系提取失败: {str(e)}")
        
        return []
    
    async def analyze_pdf_content(self, content: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        综合分析PDF内容，提取层级结构和知识点
        
        Args:
            content: PDF内容
            context: 上下文信息
            
        Returns:
            分析结果，包含章节、节和知识点
        """
        try:
            logger.info(f"开始综合分析PDF内容，长度: {len(content)} 字符")
            
            # 构建提示词
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的文档分析助手，请分析给定PDF内容，提取其层级结构（章节、节）和知识点。输出格式为JSON，包含chapters数组，每个chapter包含title、sections数组，每个section包含title和knowledge_points数组。不要添加任何解释性文字，只输出纯JSON格式。"
                },
                {
                    "role": "user",
                    "content": f"分析以下PDF内容，提取层级结构和知识点，上下文：{context}\n\n内容：{content[:5000]}..."  # 限制文本长度
                }
            ]
            
            # 调用大模型API
            response = await self._call_llm_api(messages)
            
            if not response or "choices" not in response:
                logger.error("大模型API响应格式错误")
                return {}
            
            # 解析响应
            llm_output = response["choices"][0]["message"]["content"]
            logger.debug(f"大模型输出: {llm_output}")
            
            # 处理代码块标记，提取纯JSON内容
            processed_output = llm_output.strip()
            
            # 移除可能的代码块标记
            if processed_output.startswith('```json'):
                processed_output = processed_output[7:]
            if processed_output.startswith('```'):
                processed_output = processed_output[3:]
            if processed_output.endswith('```'):
                processed_output = processed_output[:-3]
            
            # 提取JSON部分
            json_start = processed_output.find("{")
            json_end = processed_output.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("无法从大模型输出中提取JSON格式")
                return {}
            
            json_str = processed_output[json_start:json_end]
            analysis_result = json.loads(json_str)
            
            logger.info(f"PDF内容分析完成")
            return analysis_result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.error(f"JSON字符串: {json_str if 'json_str' in locals() else '未提取到'}")
        except Exception as e:
            logger.error(f"PDF内容分析失败: {str(e)}")
        
        return {}
    
    async def enhance_knowledge_graph(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用大模型增强知识图谱
        
        Args:
            graph_data: 原始知识图谱数据
            
        Returns:
            增强后的知识图谱数据
        """
        try:
            logger.info("开始增强知识图谱")
            
            # 构建提示词
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的知识图谱增强助手，请从以下方面优化给定的知识图谱：1) 添加缺失的关联关系，识别多样化的关系类型（如：依赖、包含、相似、对比、因果、递进、实例化、泛化等）；2) 增强节点元数据，丰富节点内容；3) 优化关系权重，根据关系强度分配0-1之间的权重；4) 识别并修复不合理的关系；5) 优化图谱结构，提高图谱的连通性和逻辑性。输出格式为JSON，包含nodes和edges数组。不要添加任何解释性文字，只输出纯JSON格式。"
                },
                {
                    "role": "user",
                    "content": f"优化以下知识图谱：\n\n{json.dumps(graph_data, ensure_ascii=False)}"
                }
            ]
            
            # 调用大模型API
            response = await self._call_llm_api(messages)
            
            if not response or "choices" not in response:
                logger.error("大模型API响应格式错误")
                return graph_data
            
            # 解析响应
            llm_output = response["choices"][0]["message"]["content"]
            logger.debug(f"大模型输出: {llm_output}")
            
            # 处理代码块标记，提取纯JSON内容
            processed_output = llm_output.strip()
            
            # 移除可能的代码块标记
            if processed_output.startswith('```json'):
                processed_output = processed_output[7:]
            if processed_output.startswith('```'):
                processed_output = processed_output[3:]
            if processed_output.endswith('```'):
                processed_output = processed_output[:-3]
            
            # 提取JSON部分
            json_start = processed_output.find("{")
            json_end = processed_output.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("无法从大模型输出中提取JSON格式")
                return graph_data
            
            json_str = processed_output[json_start:json_end]
            enhanced_graph = json.loads(json_str)
            
            logger.info("知识图谱增强完成")
            return enhanced_graph
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            logger.error(f"JSON字符串: {json_str if 'json_str' in locals() else '未提取到'}")
        except Exception as e:
            logger.error(f"知识图谱增强失败: {str(e)}")
        
        return graph_data


# 创建全局服务实例
llm_service = LLMServices()