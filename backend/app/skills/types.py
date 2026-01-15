"""
Skill System 核心类型定义

定义Skill系统中使用的所有数据类型，包括：
- SkillMetadata: L1元数据
- SkillMatch: 匹配结果
- SkillChain: 多Skill执行链
- ContextIsolationMode: Context隔离策略
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SkillStatus(Enum):
    """Skill执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContextIsolationMode(Enum):
    """Context隔离策略
    
    - ISOLATED: 每个Skill独立Context，互不影响
    - SHARED: 共享Context（默认），所有Skill可访问
    - INHERIT: 继承前序Skill的Context，可修改
    """
    ISOLATED = "isolated"
    SHARED = "shared"
    INHERIT = "inherit"


class SkillChainMode(Enum):
    """Skill链执行模式
    
    - SEQUENTIAL: 串行执行，前序输出作为后序输入
    - PARALLEL: 并行执行，结果聚合
    - CONDITIONAL: 根据前序结果决定后续
    - ITERATIVE: 循环执行直到满足条件
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    ITERATIVE = "iterative"


@dataclass
class SkillMetadata:
    """Skill L1 元数据
    
    始终存在于System Prompt中，用于意图识别。
    控制在约100 tokens以内。
    """
    # 基础信息
    name: str                              # 唯一标识（小写+下划线）
    display_name: str                      # 显示名称（中文）
    description: str                       # 详细描述，用于匹配
    version: str                           # 版本号（semver）
    
    # 可选信息
    author: str = "system"                 # 作者
    tags: List[str] = field(default_factory=list)  # 标签，辅助搜索
    
    # 工具配置（Action Space Pruning）
    allowed_tools: List[str] = field(default_factory=list)  # 允许使用的工具列表
    
    # 执行配置
    max_iterations: int = 30               # 最大迭代次数
    timeout: int = 300                     # 超时时间（秒）
    enabled: bool = True                   # 是否启用
    
    # 匹配配置（新增）
    match_threshold: float = 0.7           # 匹配阈值
    priority: int = 0                      # 优先级（数字越大越优先）
    
    # 协同配置（新增）
    conflicts_with: List[str] = field(default_factory=list)  # 冲突Skill列表
    requires: List[str] = field(default_factory=list)        # 依赖Skill列表
    
    # 路径信息
    skill_path: str = ""                   # Skill文件路径
    
    def to_system_prompt(self) -> str:
        """生成System Prompt片段（约100 tokens）"""
        return f"- **{self.display_name}**: {self.description}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "allowed_tools": self.allowed_tools,
            "max_iterations": self.max_iterations,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "match_threshold": self.match_threshold,
            "priority": self.priority,
            "conflicts_with": self.conflicts_with,
            "requires": self.requires,
        }


@dataclass
class SkillMatch:
    """Skill匹配结果"""
    skill_id: str                          # 匹配到的Skill ID
    score: float                           # 匹配分数 (0-1)
    reason: str                            # 匹配原因
    metadata: Optional[SkillMetadata] = None  # Skill元数据
    
    def is_confident(self) -> bool:
        """判断是否高置信度匹配"""
        if self.metadata:
            return self.score >= self.metadata.match_threshold
        return self.score >= 0.7


@dataclass
class SkillChainStep:
    """Skill链中的单个步骤"""
    skill_id: str                          # Skill ID
    order: int                             # 执行顺序
    status: SkillStatus = SkillStatus.PENDING
    
    # 输入输出
    input_artifacts: List[str] = field(default_factory=list)   # 输入产出物ID
    output_artifacts: List[str] = field(default_factory=list)  # 输出产出物ID
    
    # 条件执行（用于CONDITIONAL模式）
    condition: Optional[str] = None        # 执行条件表达式
    
    # 执行结果
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class SkillChain:
    """多Skill执行链
    
    定义多个Skill的编排执行计划。
    """
    id: str                                # 链ID
    mode: SkillChainMode                   # 执行模式
    steps: List[SkillChainStep]            # 执行步骤
    
    # Context配置
    context_isolation: ContextIsolationMode = ContextIsolationMode.SHARED
    
    # 状态
    status: SkillStatus = SkillStatus.PENDING
    current_step: int = 0
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_skill_ids(
        cls, 
        chain_id: str,
        skill_ids: List[str], 
        mode: SkillChainMode = SkillChainMode.SEQUENTIAL
    ) -> "SkillChain":
        """从Skill ID列表创建执行链"""
        steps = [
            SkillChainStep(skill_id=sid, order=i)
            for i, sid in enumerate(skill_ids)
        ]
        return cls(id=chain_id, mode=mode, steps=steps)
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "SkillChain":
        """从JSON数据创建执行链"""
        import uuid
        skill_ids = data.get("skills", [])
        mode_str = data.get("mode", "sequential")
        mode = SkillChainMode(mode_str)
        return cls.from_skill_ids(
            chain_id=str(uuid.uuid4()),
            skill_ids=skill_ids,
            mode=mode
        )
    
    def get_current_step(self) -> Optional[SkillChainStep]:
        """获取当前执行步骤"""
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def advance(self) -> bool:
        """推进到下一步，返回是否还有更多步骤"""
        if self.current_step < len(self.steps):
            self.current_step += 1
        return self.current_step < len(self.steps)
    
    def is_complete(self) -> bool:
        """检查是否所有步骤都完成"""
        return all(
            step.status == SkillStatus.COMPLETED 
            for step in self.steps
        )


@dataclass
class Artifact:
    """Skill产出物
    
    用于Skill之间传递数据。
    """
    id: str                                # 产出物ID
    skill_id: str                          # 生成该产出物的Skill
    name: str                              # 产出物名称
    type: str                              # 类型 (markdown, pptx, code, etc.)
    
    # 内容（二选一）
    content: Optional[str] = None          # 文本内容
    file_path: Optional[str] = None        # 文件路径
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_content(self) -> str:
        """获取产出物内容"""
        if self.content:
            return self.content
        if self.file_path:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""


@dataclass
class SkillContext:
    """Skill执行上下文
    
    包含Skill执行所需的所有信息。
    """
    session_id: str
    workspace_id: str
    user_id: str
    
    # 当前Skill信息
    skill_id: str
    skill_metadata: SkillMetadata
    
    # L2指令内容
    l2_instructions: str = ""
    
    # 输入产出物
    input_artifacts: List[Artifact] = field(default_factory=list)
    
    # 可用工具（经过Action Space Pruning）
    available_tools: List[str] = field(default_factory=list)
    
    # 执行状态
    iteration: int = 0
    max_iterations: int = 30
    
    def to_context_message(self) -> str:
        """生成注入Context的消息"""
        parts = [
            f"## 当前技能: {self.skill_metadata.display_name}\n",
            self.l2_instructions,
        ]
        
        if self.input_artifacts:
            parts.append("\n## 输入数据\n")
            for artifact in self.input_artifacts:
                parts.append(f"### {artifact.name}\n{artifact.get_content()[:2000]}...\n")
        
        return "\n".join(parts)
