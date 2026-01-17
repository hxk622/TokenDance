# -*- coding: utf-8 -*-
"""
知识图谱构建服务

提供:
- LLM 驱动的实体抽取
- 关系抽取
- 实体消歧 (去重)
- 增量图谱合并
"""

import json
import logging
import hashlib
from typing import List, Optional, Dict, Any, Tuple

from .models import (
    Entity, Relation, EntityType, RelationType,
    ResearchKnowledgeGraph, ResearchSource
)

logger = logging.getLogger(__name__)


# ==================== 提示词模板 ====================

ENTITY_EXTRACTION_PROMPT = """从以下文本中提取关键实体。

文本:
{text}

请以 JSON 格式返回实体列表，每个实体包含:
- name: 实体名称
- type: 实体类型 (person/org/concept/event/product/location/document/claim/data_point)
- description: 简短描述 (可选)
- aliases: 别名列表 (可选)

示例输出:
```json
[
  {{"name": "OpenAI", "type": "org", "description": "AI研究公司"}},
  {{"name": "GPT-4", "type": "product", "description": "大语言模型"}}
]
```

仅返回 JSON，不要其他解释。"""

RELATION_EXTRACTION_PROMPT = """从以下文本中提取实体之间的关系。

文本:
{text}

已识别的实体:
{entities}

请以 JSON 格式返回关系列表，每个关系包含:
- source: 源实体名称
- target: 目标实体名称
- type: 关系类型 (works_for/founded/authored/leads/is_a/part_of/related_to/compared_to/depends_on/preceded_by/followed_by/concurrent_with/cited_in/supports/contradicts/refines)
- evidence: 支持该关系的原文摘录

示例输出:
```json
[
  {{"source": "Sam Altman", "target": "OpenAI", "type": "leads", "evidence": "Sam Altman担任OpenAI的CEO"}}
]
```

仅返回 JSON，不要其他解释。"""

CLAIM_EXTRACTION_PROMPT = """从以下文本中提取可验证的声明/论断。

文本:
{text}

请以 JSON 格式返回声明列表，每个声明包含:
- claim: 声明内容
- entities: 涉及的实体列表
- evidence: 支持该声明的原文

示例输出:
```json
[
  {{"claim": "GPT-4在医学考试中达到了90%的准确率", "entities": ["GPT-4"], "evidence": "研究表明GPT-4在USMLE医学考试中获得了90%的准确率"}}
]
```

仅返回可验证的具体声明，不要观点或主观评价。仅返回 JSON。"""


class KnowledgeGraphBuilder:
    """
    知识图谱构建器
    
    使用 LLM 从文本中抽取实体和关系，构建知识图谱
    """
    
    def __init__(
        self,
        llm_client: Any = None,
        model: str = "gpt-4o-mini",
        similarity_threshold: float = 0.8
    ):
        """
        初始化构建器
        
        Args:
            llm_client: LLM 客户端 (需要有 chat.completions.create 方法)
            model: 使用的模型
            similarity_threshold: 实体消歧的相似度阈值
        """
        self.llm_client = llm_client
        self.model = model
        self.similarity_threshold = similarity_threshold
        
        # 内存图谱
        self.graph = ResearchKnowledgeGraph()
    
    async def build_from_text(
        self,
        text: str,
        source: Optional[ResearchSource] = None,
        extract_claims: bool = True
    ) -> ResearchKnowledgeGraph:
        """
        从文本构建知识图谱
        
        Args:
            text: 输入文本
            source: 来源信息
            extract_claims: 是否提取声明
        
        Returns:
            构建的知识图谱
        """
        # 添加来源
        if source:
            self.graph.add_source(source)
        
        source_id = source.id if source else None
        
        # 1. 实体抽取
        entities = await self._extract_entities(text, source_id)
        logger.info(f"Extracted {len(entities)} entities")
        
        # 2. 实体消歧和添加
        for entity in entities:
            self._add_entity_with_disambiguation(entity)
        
        # 3. 关系抽取
        entity_names = [e.name for e in entities]
        relations = await self._extract_relations(text, entity_names, source_id)
        logger.info(f"Extracted {len(relations)} relations")
        
        # 4. 添加关系
        for relation in relations:
            self._add_relation_with_validation(relation)
        
        # 5. 声明抽取 (可选)
        if extract_claims:
            claims = await self._extract_claims(text, source_id)
            logger.info(f"Extracted {len(claims)} claims")
            
            # 将声明作为特殊实体添加
            for claim_data in claims:
                claim_entity = Entity.create(
                    name=claim_data["claim"][:100],  # 截断过长的声明
                    entity_type=EntityType.CLAIM,
                    source_id=source_id,
                    full_claim=claim_data["claim"],
                    evidence=claim_data.get("evidence", ""),
                )
                claim_id = self.graph.add_entity(claim_entity)
                
                # 连接声明和相关实体
                for entity_name in claim_data.get("entities", []):
                    related = self.graph.get_entity_by_name(entity_name)
                    if related:
                        relation = Relation.create(
                            source_id=related.id,
                            target_id=claim_id,
                            relation_type=RelationType.SUPPORTS,
                            evidence=claim_data.get("evidence", ""),
                            doc_source_id=source_id or "",
                        )
                        self.graph.add_relation(relation)
        
        return self.graph
    
    async def merge_graph(self, other: ResearchKnowledgeGraph) -> None:
        """
        合并另一个图谱
        
        实体消歧后合并，避免重复
        """
        # 合并来源
        for source_id, source in other.sources.items():
            if source_id not in self.graph.sources:
                self.graph.add_source(source)
        
        # 合并实体 (带消歧)
        id_mapping = {}  # old_id -> new_id
        for entity in other.entities.values():
            existing = self.graph.find_similar_entity(entity.name, self.similarity_threshold)
            if existing:
                # 合并到已有实体
                existing.merge_with(entity)
                id_mapping[entity.id] = existing.id
            else:
                # 添加新实体
                self.graph.add_entity(entity)
                id_mapping[entity.id] = entity.id
        
        # 合并关系 (更新 ID 引用)
        for relation in other.relations:
            new_source_id = id_mapping.get(relation.source_entity_id, relation.source_entity_id)
            new_target_id = id_mapping.get(relation.target_entity_id, relation.target_entity_id)
            
            # 检查是否已存在相同关系
            if not self._relation_exists(new_source_id, new_target_id, relation.type):
                new_relation = Relation(
                    id=relation.id,
                    source_entity_id=new_source_id,
                    target_entity_id=new_target_id,
                    type=relation.type,
                    properties=relation.properties,
                    evidence=relation.evidence,
                    source_id=relation.source_id,
                    confidence=relation.confidence,
                )
                self.graph.add_relation(new_relation)
    
    async def build_from_sources(
        self,
        sources: List[ResearchSource]
    ) -> ResearchKnowledgeGraph:
        """
        从多个来源构建图谱
        
        Args:
            sources: 来源列表 (需要有 content 字段)
        """
        for source in sources:
            if source.content:
                await self.build_from_text(source.content, source)
        
        return self.graph
    
    def get_graph(self) -> ResearchKnowledgeGraph:
        """获取当前图谱"""
        return self.graph
    
    def reset(self) -> None:
        """重置图谱"""
        self.graph = ResearchKnowledgeGraph()
    
    # ==================== 私有方法 ====================
    
    async def _extract_entities(
        self,
        text: str,
        source_id: Optional[str]
    ) -> List[Entity]:
        """使用 LLM 抽取实体"""
        if not self.llm_client:
            # 如果没有 LLM 客户端，使用简单的规则抽取
            return self._rule_based_entity_extraction(text, source_id)
        
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text[:4000])  # 截断过长文本
        
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识抽取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # 处理不同的返回格式
            if isinstance(data, list):
                entities_data = data
            elif isinstance(data, dict) and "entities" in data:
                entities_data = data["entities"]
            else:
                entities_data = []
            
            entities = []
            for item in entities_data:
                try:
                    entity_type = EntityType(item.get("type", "concept"))
                except ValueError:
                    entity_type = EntityType.CONCEPT
                
                entity = Entity.create(
                    name=item["name"],
                    entity_type=entity_type,
                    source_id=source_id,
                    description=item.get("description", ""),
                    aliases=item.get("aliases", []),
                )
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return self._rule_based_entity_extraction(text, source_id)
    
    async def _extract_relations(
        self,
        text: str,
        entity_names: List[str],
        source_id: Optional[str]
    ) -> List[Relation]:
        """使用 LLM 抽取关系"""
        if not self.llm_client or not entity_names:
            return []
        
        entities_str = ", ".join(entity_names[:30])  # 限制实体数量
        prompt = RELATION_EXTRACTION_PROMPT.format(
            text=text[:4000],
            entities=entities_str
        )
        
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识抽取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            if isinstance(data, list):
                relations_data = data
            elif isinstance(data, dict) and "relations" in data:
                relations_data = data["relations"]
            else:
                relations_data = []
            
            relations = []
            for item in relations_data:
                # 查找源和目标实体
                source_entity = self.graph.get_entity_by_name(item["source"])
                target_entity = self.graph.get_entity_by_name(item["target"])
                
                if not source_entity or not target_entity:
                    continue
                
                try:
                    relation_type = RelationType(item.get("type", "related_to"))
                except ValueError:
                    relation_type = RelationType.RELATED_TO
                
                relation = Relation.create(
                    source_id=source_entity.id,
                    target_id=target_entity.id,
                    relation_type=relation_type,
                    evidence=item.get("evidence", ""),
                    doc_source_id=source_id or "",
                )
                relations.append(relation)
            
            return relations
            
        except Exception as e:
            logger.error(f"Relation extraction failed: {e}")
            return []
    
    async def _extract_claims(
        self,
        text: str,
        source_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """使用 LLM 抽取声明"""
        if not self.llm_client:
            return []
        
        prompt = CLAIM_EXTRACTION_PROMPT.format(text=text[:4000])
        
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识抽取助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "claims" in data:
                return data["claims"]
            
            return []
            
        except Exception as e:
            logger.error(f"Claim extraction failed: {e}")
            return []
    
    def _rule_based_entity_extraction(
        self,
        text: str,
        source_id: Optional[str]
    ) -> List[Entity]:
        """
        基于规则的简单实体抽取 (回退方案)
        
        使用正则表达式匹配常见模式
        """
        import re
        
        entities = []
        
        # 匹配引号中的名称 (可能是术语、产品名等)
        quoted_pattern = r'[""](.*?)[""]'
        for match in re.finditer(quoted_pattern, text):
            name = match.group(1).strip()
            if 2 <= len(name) <= 50:
                entity = Entity.create(
                    name=name,
                    entity_type=EntityType.CONCEPT,
                    source_id=source_id,
                )
                entities.append(entity)
        
        # 匹配大写开头的词组 (可能是专有名词)
        proper_noun_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        for match in re.finditer(proper_noun_pattern, text):
            name = match.group(1).strip()
            if 2 <= len(name) <= 50:
                entity = Entity.create(
                    name=name,
                    entity_type=EntityType.CONCEPT,
                    source_id=source_id,
                )
                entities.append(entity)
        
        # 去重
        seen = set()
        unique_entities = []
        for entity in entities:
            name_lower = entity.name.lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_entities.append(entity)
        
        return unique_entities[:20]  # 限制数量
    
    def _add_entity_with_disambiguation(self, entity: Entity) -> str:
        """
        添加实体，带消歧逻辑
        
        如果存在相似实体，则合并而非创建新实体
        """
        existing = self.graph.find_similar_entity(entity.name, self.similarity_threshold)
        
        if existing:
            existing.merge_with(entity)
            return existing.id
        else:
            return self.graph.add_entity(entity)
    
    def _add_relation_with_validation(self, relation: Relation) -> Optional[str]:
        """
        添加关系，带验证
        
        检查源和目标实体是否存在，避免重复关系
        """
        # 验证实体存在
        if relation.source_entity_id not in self.graph.entities:
            return None
        if relation.target_entity_id not in self.graph.entities:
            return None
        
        # 检查重复
        if self._relation_exists(
            relation.source_entity_id,
            relation.target_entity_id,
            relation.type
        ):
            return None
        
        return self.graph.add_relation(relation)
    
    def _relation_exists(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType
    ) -> bool:
        """检查关系是否已存在"""
        for relation in self.graph.relations:
            if (relation.source_entity_id == source_id and
                relation.target_entity_id == target_id and
                relation.type == relation_type):
                return True
        return False


# ==================== 辅助函数 ====================

def create_source_from_search_result(
    result: Dict[str, Any],
    content: Optional[str] = None
) -> ResearchSource:
    """
    从搜索结果创建 ResearchSource
    
    兼容 deep_research.py 中的搜索结果格式
    """
    import hashlib
    from datetime import datetime
    
    url = result.get("url", result.get("link", ""))
    source_id = hashlib.md5(url.encode()).hexdigest()[:16]
    
    return ResearchSource(
        id=source_id,
        url=url,
        title=result.get("title", ""),
        snippet=result.get("snippet", result.get("description", "")),
        content=content,
        timestamp=datetime.now(),
        credibility_score=0.5,  # 默认中等可信度
    )
