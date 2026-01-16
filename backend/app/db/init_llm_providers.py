"""Initialize default LLM providers and models"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_config import LLMProvider, LLMModel


async def init_llm_providers(db: AsyncSession):
    """Initialize default LLM providers"""
    
    # Check if providers already exist
    from sqlalchemy import select
    result = await db.execute(select(LLMProvider))
    existing = result.scalars().all()
    
    if existing:
        print(f"LLM providers already initialized: {len(existing)} providers")
        return
    
    # Anthropic Provider
    anthropic_provider = LLMProvider(
        id="anthropic",
        name="anthropic",
        display_name="Anthropic",
        description="Anthropic's Claude models - known for strong reasoning and safety",
        api_base_url="https://api.anthropic.com",
        requires_api_key=True,
        supported_models=[
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ],
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        max_context_tokens=200000,
        input_price_per_1m=3.0,
        output_price_per_1m=15.0,
        is_active=True,
        is_builtin=True
    )
    
    db.add(anthropic_provider)
    
    # Anthropic Models
    claude_35_sonnet = LLMModel(
        id="claude-3-5-sonnet-20241022",
        provider_id="anthropic",
        name="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        description="Most intelligent model, ideal for complex tasks",
        max_tokens=8192,
        max_context_tokens=200000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=3.0,
        output_price_per_1m=15.0,
        recommended_temperature=1.0,
        recommended_max_tokens=8192,
        is_active=True
    )
    
    claude_35_haiku = LLMModel(
        id="claude-3-5-haiku-20241022",
        provider_id="anthropic",
        name="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        description="Fast and efficient model for simple tasks",
        max_tokens=8192,
        max_context_tokens=200000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=0.8,
        output_price_per_1m=4.0,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    claude_3_opus = LLMModel(
        id="claude-3-opus-20240229",
        provider_id="anthropic",
        name="claude-3-opus-20240229",
        display_name="Claude 3 Opus",
        description="Most capable model for complex analysis",
        max_tokens=4096,
        max_context_tokens=200000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=15.0,
        output_price_per_1m=75.0,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    claude_3_sonnet = LLMModel(
        id="claude-3-sonnet-20240229",
        provider_id="anthropic",
        name="claude-3-sonnet-20240229",
        display_name="Claude 3 Sonnet",
        description="Balanced model for most use cases",
        max_tokens=4096,
        max_context_tokens=200000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=3.0,
        output_price_per_1m=15.0,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    claude_3_haiku = LLMModel(
        id="claude-3-haiku-20240307",
        provider_id="anthropic",
        name="claude-3-haiku-20240307",
        display_name="Claude 3 Haiku",
        description="Fastest model for simple tasks",
        max_tokens=4096,
        max_context_tokens=200000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=0.25,
        output_price_per_1m=1.25,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    db.add_all([
        claude_35_sonnet,
        claude_35_haiku,
        claude_3_opus,
        claude_3_sonnet,
        claude_3_haiku
    ])
    
    # OpenAI Provider (placeholder)
    openai_provider = LLMProvider(
        id="openai",
        name="openai",
        display_name="OpenAI",
        description="OpenAI's GPT models",
        api_base_url="https://api.openai.com/v1",
        requires_api_key=True,
        supported_models=[
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ],
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        max_context_tokens=128000,
        input_price_per_1m=10.0,
        output_price_per_1m=30.0,
        is_active=True,
        is_builtin=True
    )
    
    db.add(openai_provider)
    
    # OpenAI Models
    gpt_4_turbo = LLMModel(
        id="gpt-4-turbo",
        provider_id="openai",
        name="gpt-4-turbo",
        display_name="GPT-4 Turbo",
        description="Most capable GPT-4 model",
        max_tokens=4096,
        max_context_tokens=128000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=10.0,
        output_price_per_1m=30.0,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    gpt_4 = LLMModel(
        id="gpt-4",
        provider_id="openai",
        name="gpt-4",
        display_name="GPT-4",
        description="Original GPT-4 model",
        max_tokens=8192,
        max_context_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        input_price_per_1m=30.0,
        output_price_per_1m=60.0,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    gpt_35_turbo = LLMModel(
        id="gpt-3.5-turbo",
        provider_id="openai",
        name="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        description="Fast and cost-effective model",
        max_tokens=4096,
        max_context_tokens=16385,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=False,
        input_price_per_1m=0.5,
        output_price_per_1m=1.5,
        recommended_temperature=1.0,
        recommended_max_tokens=4096,
        is_active=True
    )
    
    db.add_all([gpt_4_turbo, gpt_4, gpt_35_turbo])
    
    await db.commit()
    
    print(f"Initialized LLM providers: Anthropic (5 models), OpenAI (3 models)")
