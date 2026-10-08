from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Model configurations ---
    ORCHESTRATOR_MODEL_ID: str = Field(
        default="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        description="Model for main orchestrator (tool selection, conversation management).",
    )
    EXTRACTION_MODEL_ID: str = Field(
        default="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        description="Model for data extraction tasks (JSON parsing, structured data).",
    )
    ROUTER_MODEL_ID: str = Field(
        default="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        description="Model for router/intent classification (lightweight, fast).",
    )

    # --- Jev router configuration ---
    TYPESAFE_API_KEY: SecretStr | None = Field(
        default=None,
        description="TypeSafe API key used by the Jev intent router.",
    )
    TYPESAFE_SECRET_ARN: str = Field(
        default="",
        description="Secrets Manager ARN containing the TypeSafe API key for deployed runtimes.",
    )
    JEV_ROUTER_MODEL: str = Field(
        default="jev-1.13.0",
        description="Pinned Jev model version for intent classification.",
    )
    JEV_ROUTER_TIMEOUT_SECONDS: float = Field(
        default=2.0,
        gt=0,
        description="Maximum time allowed for a Jev routing request before Bedrock fallback.",
    )

    # --- Controlled document RAG (runtime reads only) ---
    DOCUMENT_RAG_ENABLED: bool = False
    RAG_DOCUMENT_BUCKET: str = ""
    RAG_VECTOR_INDEX_ARN: str = ""
    RAG_ACTIVE_MANIFEST_KEY: str = "rag/active.json"
    RAG_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v2:0"
    RAG_EMBEDDING_DIMENSIONS: int = 512
    RAG_TOP_K: int = Field(default=5, ge=1, le=10)
    RAG_MAX_CONTEXT_CHARACTERS: int = Field(default=9000, ge=1800, le=9000)
    RAG_REQUEST_TIMEOUT_SECONDS: float = Field(default=60, gt=0, le=60)

    # --- Browser Tools Configuration ---
    ENABLE_BROWSER_TOOLS: bool = Field(
        default=True,
        description="Enable browser-based tools (restaurant_explorer, restaurant_research).",
    )

    # --- Guardrails configurations ---
    BEDROCK_GUARDRAIL_NAME: str = Field(
        default="restaurant-finder-guardrail",
        description="The name for the Bedrock guardrail (used for create-or-get).",
    )
    BEDROCK_GUARDRAIL_ID: str = Field(
        default="",
        description="The Bedrock guardrail ID (auto-populated on startup if empty).",
    )
    BEDROCK_GUARDRAIL_VERSION: str = Field(
        default="DRAFT",
        description="The Bedrock guardrail version (e.g., 'DRAFT', '1', '2').",
    )
    GUARDRAIL_ENABLED: bool = Field(
        default=True,
        description="Enable or disable guardrails globally.",
    )

    # --- AWS configurations ---
    AWS_REGION: str = Field(
        default="us-east-2",
        description="The AWS region where services are hosted.",
    )

    # --- AgentCore Gateway configurations ---
    GATEWAY_URL: str = Field(
        default="",
        description="The AgentCore MCP Gateway URL for tool routing.",
    )
    GATEWAY_ID: str = Field(
        default="",
        description="The AgentCore Gateway ID.",
    )
    RUNTIME_ID: str = Field(
        default="",
        description="The AgentCore Runtime ID.",
    )

    # --- AgentCore Memory configurations ---
    MEMORY_ID: str = Field(
        default="",
        description="The AgentCore Memory ID. Must be set from CDK stack output.",
    )

    # --- Observability configurations ---
    AGENT_OBSERVABILITY_ENABLED: bool = Field(
        default=False,
        description="Enable OpenTelemetry-based observability for CloudWatch GenAI Observability.",
    )
    OTEL_SERVICE_NAME: str = Field(
        default="restaurant-finder-agent",
        description="Service name for OpenTelemetry tracing attribution.",
    )

    # --- Evaluation configurations ---
    EVALUATION_ENABLED: bool = Field(
        default=True,
        description="Enable AgentCore Evaluations for agent quality monitoring.",
    )
    EVALUATION_SAMPLING_RATE: int = Field(
        default=10,
        description="Percentage of sessions to evaluate in online mode (1-100).",
    )
    EVALUATION_OUTPUT_DIR: str = Field(
        default="evaluation_results",
        description="Directory for storing evaluation results.",
    )


settings = Settings()
