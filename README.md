# Restaurant Finder - Agentic AI with AWS Bedrock AgentCore

An AI-powered restaurant finder built with **AWS Bedrock AgentCore**, **LangGraph**, and **Chainlit**. This project demonstrates a production-grade multi-agent system that searches for restaurants, researches detailed information, remembers user preferences, and applies content guardrails — all deployed as a containerized runtime on AWS.

## Architecture

### Key Components

| Component                | Technology                 | Purpose                                                  |
| ------------------------ | -------------------------- | -------------------------------------------------------- |
| **Multi-Agent Workflow** | LangGraph                  | Router → Search Agent (ReAct) → Tools → Memory           |
| **Runtime**              | Bedrock AgentCore          | Containerized Python app with auto-scaling               |
| **Tool Routing**         | MCP Gateway + Lambda       | Restaurant search via SearchAPI                          |
| **Memory**               | AgentCore Memory           | User preferences, semantic facts, conversation summaries |
| **Guardrails**           | Bedrock Guardrails         | Content filtering, PII protection, topic control         |
| **Observability**        | OpenTelemetry + CloudWatch | Distributed tracing, GenAI Observability dashboard       |
| **UI**                   | Chainlit                   | Chat interface with streaming responses                  |
| **Infrastructure**       | AWS CDK (TypeScript)       | Full IaC for all AWS resources                           |
| **CI/CD**                | GitHub Actions             | Automated infra deployment + container builds            |

## Project Structure

```
├── restaurant-finder-api/          # Backend agent application
│   ├── src/
│   │   ├── application/            # Orchestrator workflow
│   │   │   └── orchestrator/
│   │   │       ├── generate_response.py   # Streaming response handler
│   │   │       └── workflow/
│   │   │           ├── agents/     # Specialized agents (data, explorer, research)
│   │   │           ├── chains.py   # LLM chain construction
│   │   │           ├── edges.py    # Graph routing logic
│   │   │           ├── graph.py    # LangGraph workflow definition
│   │   │           ├── nodes.py    # Graph node implementations
│   │   │           ├── state.py    # Workflow state definition
│   │   │           └── tools.py    # Tool definitions
│   │   ├── domain/                 # Domain models and prompts
│   │   │   ├── models.py          # Pydantic models (Restaurant, SearchResult)
│   │   │   ├── prompts.py         # LLM prompt definitions
│   │   │   └── utils.py           # Shared utility functions
│   │   ├── evaluation/            # Agent evaluation framework
│   │   │   ├── client.py          # Evaluation API client
│   │   │   ├── on_demand.py       # On-demand evaluation
│   │   │   ├── online.py          # Production evaluation
│   │   │   ├── runner.py          # Evaluation orchestrator
│   │   │   └── test_cases.py      # Test case definitions
│   │   └── infrastructure/        # AWS service integrations
│   │       ├── api.py             # BedrockAgentCoreApp entrypoint
│   │       ├── browser.py         # AgentCore Browser toolkit
│   │       ├── guardrails.py      # Bedrock Guardrails management
│   │       ├── jev_router.py      # TypeSafe Jev router client and classification
│   │       ├── mcp_client.py      # MCP Gateway client
│   │       ├── memory.py          # AgentCore Memory manager
│   │       ├── model.py           # Bedrock model configuration
│   │       ├── observability.py   # OpenTelemetry setup
│   │       ├── prompt_manager.py  # Bedrock Prompt Management sync
│   │       ├── startup.py         # Application initialization
│   │       └── utils.py           # Streaming + guardrail utilities
│   ├── Dockerfile                 # Container build with OTEL instrumentation
│   ├── Makefile                   # Development and evaluation tasks
│   └── pyproject.toml             # Python dependencies
│
├── restaurant-finder-infra/        # AWS CDK infrastructure
│   ├── bin/cdk.ts                 # CDK app entry point
│   ├── lib/stacks/
│   │   ├── agentcore-stack.ts     # Gateway, Memory, Runtime, Lambda
│   │   └── ecr-stack.ts           # ECR container repository
│   ├── mcp/lambda/                # MCP Lambda function
│   │   ├── handler.py             # SearchAPI integration
│   │   └── tools_schema.json      # Tool schema definition
│   └── package.json               # CDK dependencies
│
├── restaurant-finder-ui/           # Chainlit chat frontend
│   ├── app.py                     # Chat application (local + AWS modes)
│   ├── pyproject.toml             # UI dependencies
│   └── .env.example               # UI configuration template
│
└── .github/workflows/              # CI/CD pipelines
    ├── deploy-image.yml           # Build + deploy container
    ├── deploy-infra.yml           # Deploy CDK stacks
    └── destroy-infra.yml          # Tear down infrastructure
```

## Prerequisites

- **AWS Account** with access to the Claude Haiku 4.5 inference profile (`us.anthropic.claude-haiku-4-5-20251001-v1:0`)
- **AWS CLI** configured with credentials (`aws configure`)
- **Node.js 20+** (for CDK)
- **Python 3.11+**
- **uv** - Python package manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker** (for building container images)
- **SearchAPI.io API key** ([sign up](https://www.searchapi.io/)) - for restaurant search data
- **Bedrock AgentCore CLI** (`pip install bedrock-agentcore`)

## Quick Start (Local Development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd restaurant-finder-agentic-ai-with-agentcore
```

### 2. Deploy Infrastructure First

Even for local development, the Gateway and Memory must be deployed. The AgentCore Runtime stack also expects its container image to exist in ECR, so deploy the ECR repository, build and push the initial image, then deploy the AgentCore stack:

```bash
cd restaurant-finder-infra
npm ci
npx cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/us-east-2"   # First time only
npx cdk deploy restaurantFinder-EcrStack

cd ..
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent"
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com"
docker build --platform linux/arm64 -t "$ECR_URI:latest" ./restaurant-finder-api
docker push "$ECR_URI:latest"

cd restaurant-finder-infra
npx cdk deploy restaurantFinder-AgentCoreStack
```

Note the stack outputs — you'll need `GatewayUrl`, `GatewayId`, and `MemoryId`.

### 3. Set the SearchAPI Secret

After CDK deployment, update the secret with your SearchAPI key:

```bash
aws secretsmanager put-secret-value \
  --secret-id restaurantFinder/restaurant-search-key \
  --secret-string '{"api_key":"YOUR_SEARCHAPI_KEY"}'
```

The CDK stack also creates a Secrets Manager secret named `restaurantFinder/jev-router-key`. Copy the `TYPESAFE_API_KEY` value from your local `.env` into that secret in the AWS console. The deployed Runtime reads it using its execution role; the key is not included in the image or CloudFormation environment values.

### 4. Set Up the API

```bash
cd restaurant-finder-api
cp .env.example .env
```

Edit `.env` and fill in the CDK stack output values:

```env
AWS_REGION=us-east-2
GATEWAY_URL=https://your-gateway-url.gateway.bedrock-agentcore.us-east-2.amazonaws.com/mcp
GATEWAY_ID=your-gateway-id
MEMORY_ID=your-memory-id
TYPESAFE_API_KEY=your-typesafe-api-key
```

The TypeSafe key is used by the local Jev router. Keep it in the ignored `.env` file and never commit it. For the deployed Runtime, also copy it to the `restaurantFinder/jev-router-key` Secrets Manager secret created by CDK.

Install dependencies and start the local server:

```bash
uv sync
agentcore dev
```

The API server starts on `http://localhost:8080`.

### 5. Set Up the UI

```bash
cd restaurant-finder-ui
cp .env.example .env
uv sync
chainlit run app.py
```

The UI opens at `http://localhost:8000`.

### 6. Test It

Open `http://localhost:8000` and try:

- "Find Italian restaurants in San Francisco"
- "I need vegan-friendly Thai food under $20"
- "Tell me more about The French Laundry"

## AWS Deployment (Production)

### 1. Deploy Infrastructure

```bash
cd restaurant-finder-infra
npm ci
npx cdk bootstrap "aws://$(aws sts get-caller-identity --query Account --output text)/us-east-2"   # First time only
npx cdk deploy restaurantFinder-EcrStack
```

This first creates the ECR repository. The AgentCore stack cannot be deployed until its initial image has been pushed.

### 2. Build and Push the Container

**Option A: Automatic via GitHub Actions**

Push to `main` with changes in `restaurant-finder-api/` — the `deploy-image.yml` workflow builds and deploys automatically.

**Option B: Manual deployment**

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="$ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent"
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com"
docker build --platform linux/arm64 -t "$ECR_URI:latest" ./restaurant-finder-api
docker push "$ECR_URI:latest"
```

### 3. Deploy the AgentCore Stack

After the initial container image is available in ECR, deploy the stack that creates the Gateway, Memory, Runtime, Lambda, and supporting roles:

```bash
cd restaurant-finder-infra
npx cdk deploy restaurantFinder-AgentCoreStack
```

### 4. Set the SearchAPI Secret

```bash
aws secretsmanager put-secret-value \
  --secret-id restaurantFinder/restaurant-search-key \
  --secret-string '{"api_key":"YOUR_SEARCHAPI_KEY"}'
```

### 5. Set the TypeSafe Jev Secret

Copy the `TYPESAFE_API_KEY` value from `restaurant-finder-api/.env` into the `restaurantFinder/jev-router-key` secret in AWS Secrets Manager, in `us-east-2`.

### 6. Connect the UI to AWS

```bash
cd restaurant-finder-ui
cp .env.example .env
```

Edit `.env`:

```env
AGENT_CONNECTION_MODE=aws
AGENT_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-east-2:<ACCOUNT_ID>:runtime/<RUNTIME_ID>
AWS_REGION=us-east-2
```

```bash
uv sync
chainlit run app.py
```

## CI/CD Pipelines

GitHub Actions are disabled for this development repository so the inherited deploy workflows cannot change AWS resources when code is pushed. Enable Actions in repository settings only when you are ready to configure deployment credentials and use those workflows.

| Workflow            | Trigger                                  | Action                                           |
| ------------------- | ---------------------------------------- | ------------------------------------------------ |
| `deploy-infra.yml`  | Push to `main` (infra changes) or manual | Deploys CDK stacks (ECR + AgentCore)             |
| `deploy-image.yml`  | Push to `main` (API changes) or manual   | Builds container, pushes to ECR, updates runtime |
| `destroy-infra.yml` | Manual only (requires confirmation)      | Destroys selected CDK stacks                     |

**Required GitHub Secrets:**

- `AWS_ACCESS_KEY_ID` - IAM access key with deployment permissions
- `AWS_SECRET_ACCESS_KEY` - Corresponding secret key

## Configuration Reference

### API Environment Variables (`restaurant-finder-api/.env`)

| Variable                      | Required | Default                   | Description                             |
| ----------------------------- | -------- | ------------------------- | --------------------------------------- |
| `AWS_REGION`                  | Yes      | `us-east-2`               | AWS region for all services             |
| `TYPESAFE_API_KEY`            | For Jev  | -                         | Secret TypeSafe API key for local Jev routing |
| `TYPESAFE_SECRET_ARN`         | Runtime | Set by CDK                | Secrets Manager ARN used by deployed Jev routing |
| `JEV_ROUTER_MODEL`            | No       | `jev-1.13.0`               | Jev model used for intent classification |
| `JEV_ROUTER_TIMEOUT_SECONDS`  | No       | `2.0`                     | Jev request timeout before Bedrock fallback |
| `ORCHESTRATOR_MODEL_ID`       | No       | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock model for the orchestrator |
| `EXTRACTION_MODEL_ID`         | No       | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock model for structured data extraction |
| `ROUTER_MODEL_ID`             | No       | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock router used when Jev fails |
| `GATEWAY_URL`                 | Yes      | -                         | MCP Gateway URL (CDK output)            |
| `GATEWAY_ID`                  | Yes      | -                         | Gateway identifier (CDK output)         |
| `MEMORY_ID`                   | Yes      | -                         | Memory identifier (CDK output)          |
| `RUNTIME_ID`                  | No       | -                         | Runtime ID (needed for evaluation only) |
| `ENABLE_BROWSER_TOOLS`        | No       | `true`                    | Enable browser-based agent tools        |
| `GUARDRAIL_ENABLED`           | No       | `true`                    | Enable Bedrock content guardrails       |
| `AGENT_OBSERVABILITY_ENABLED` | No       | `true`                    | Enable OpenTelemetry tracing            |
| `OTEL_SERVICE_NAME`           | No       | `restaurant-finder-agent` | Service name for traces                 |

### UI Environment Variables (`restaurant-finder-ui/.env`)

| Variable                | Required    | Default                             | Description              |
| ----------------------- | ----------- | ----------------------------------- | ------------------------ |
| `AGENT_CONNECTION_MODE` | No          | `local`                             | `local` or `aws`         |
| `AGENTCORE_API_URL`     | No          | `http://localhost:8080/invocations` | Local API endpoint       |
| `AGENT_RUNTIME_ARN`     | If aws mode | -                                   | Runtime ARN (CDK output) |
| `AWS_REGION`            | No          | `us-east-2`                         | AWS region               |

## Evaluation

The project includes a comprehensive evaluation framework:

```bash
cd restaurant-finder-api

# Run full evaluation suite (all test cases + built-in evaluators)
make eval

# Run specific categories
make eval-categories CATEGORIES="basic_search dietary_search"

# Run safety evaluations only
make eval-safety

# Evaluate an existing session
make eval-session SESSION_ID=your-session-id

# Set up online (production) evaluation
make eval-online SAMPLING_RATE=10
```

Test categories: `basic_search`, `filtered_search`, `dietary_search`, `memory_recall`, `research`, `safety`, `multi_step`, `out_of_scope`

## Development

### Code Quality

```bash
cd restaurant-finder-api

# Format code
make format-fix

# Lint code
make lint-fix

# Check formatting (CI)
make format-check

# Check linting (CI)
make lint-check
```

## Cleanup

To tear down all AWS resources:

```bash
cd restaurant-finder-infra
npx cdk destroy --all
```

Or use the GitHub Actions `destroy-infra.yml` workflow with manual dispatch.
