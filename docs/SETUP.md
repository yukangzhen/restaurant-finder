# Setup and verification

These instructions use **PowerShell 7**, Python **3.11.9+ within 3.11**, uv **0.12.15** (the CI version) and Node.js **22**. They target the public release on `main`. Bash users must translate the shell syntax.

## 1. Get the code

```powershell
git clone https://github.com/yukangzhen/restaurant-finder.git
Set-Location restaurant-finder
$Repo = (Get-Location).Path
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
```

In each new terminal, navigate to your clone root and set `$Repo = (Get-Location).Path` again. Install Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.11 and Node.js 22 first. No separate global AgentCore CLI installation is needed: the API lockfile includes the SDK/starter toolkit.

## 2. Offline checks

Use a fresh clone without `.env` or a generated prompt manifest. If your checkout is already configured, use a second fresh clone rather than overwrite its environment. Dependency installation needs internet; tests/evaluations use simulated cloud/model dependencies and need no AWS account.

From the root terminal:

```powershell
'AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','AWS_SESSION_TOKEN','AWS_PROFILE','AWS_DEFAULT_PROFILE' |
    ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
$env:AWS_SHARED_CREDENTIALS_FILE = Join-Path $Repo '.offline-no-credentials'
$env:AWS_CONFIG_FILE = Join-Path $Repo '.offline-no-config'
$env:AWS_EC2_METADATA_DISABLED = 'true'
$env:AWS_REGION = 'us-east-2'
$env:PROMPT_SYNC_MODE = 'false'
$env:REQUIRE_PROMPT_MANIFEST = 'false'
$env:PROMPT_MANIFEST_PATH = Join-Path $Repo '.offline-no-prompt-manifest.json'
$env:AGENT_OBSERVABILITY_ENABLED = 'false'
$env:EVALUATION_ENABLED = 'false'
$env:LOGURU_LEVEL = 'ERROR'

Set-Location (Join-Path $Repo 'restaurant-finder-api')
uv sync --locked --python 3.11
uv run --no-sync python -m unittest discover -s tests -q
uv run --no-sync python -m src.evaluation.rag --offline --output .generated/evaluation/document-rag.json
uv run --no-sync python -m src.evaluation.document_comparison --offline --output .generated/evaluation/document-comparison.json
uv run --no-sync python -m src.evaluation.document_multipart --offline --output .generated/evaluation/document-multipart.json
uv run --no-sync python -m src.evaluation.document_followups --offline --output .generated/evaluation/document-followups.json
uv run --no-sync python -m src.evaluation.document_retrieval --offline --output .generated/evaluation/document-retrieval.json
uv run --no-sync python -m src.deployment.ingest_documents --dry-run --corpus sample_documents/corpus.json

Set-Location (Join-Path $Repo 'restaurant-finder-ui')
uv sync --locked --python 3.11
uv run --no-sync python -m unittest discover -s tests -q

Set-Location (Join-Path $Repo 'restaurant-finder-infra')
npm ci
npm run build
npm test -- --runInBand
$env:CDK_DEFAULT_ACCOUNT = '123456789012'
$env:CDK_DEFAULT_REGION = 'us-east-2'
npx --no-install cdk synth --all --no-lookups -c imageUri=123456789012.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:offline-ci --output cdk.out/offline
Set-Location $Repo
```

API reports appear under ignored `.generated/evaluation/`. Use the current invocation's exit code; an old report does not establish a new pass. The five evaluations do not measure live Jev/Haiku accuracy, cloud availability, semantic recall, latency or cost. See [evaluation interpretation](CI_AND_RAG_EVALUATION.md).

## 3. First AWS deployment

**This section creates/changes AWS resources and can incur charges.** It assumes your own development account without an existing Restaurant Finder installation. For updates, inspect and preserve existing contexts, corpus and guardrail pair first.

Start a **new terminal** at the clone root so offline AWS overrides do not leak into deployment:

```powershell
$Repo = (Get-Location).Path
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$env:AWS_PROFILE = 'default' # Change to your configured development profile.
$env:AWS_REGION = 'us-east-2'
aws sts get-caller-identity --profile $env:AWS_PROFILE --region us-east-2
```

If authentication fails, complete your profile's login flow: `aws login --profile default` for AWS CLI login profiles, or `aws sso login --profile YOUR_PROFILE` for SSO. Verify the account printed above before proceeding. Never copy the author's account identifiers from historical runbooks.

Additional prerequisites:

- A working Docker engine with `linux/arm64` build support and sufficient memory/disk.
- Access to `us.anthropic.claude-haiku-4-5-20251001-v1:0` and `amazon.titan-embed-text-v2:0`. IAM permissions, provider onboarding or Marketplace subscription may be required; check availability in your account.
- A deployment identity authorized for CDK bootstrap, CloudFormation/IAM, ECR, S3/S3 Vectors, AgentCore, Lambda, Secrets Manager and Bedrock. Prompt synchronization needs Bedrock Prompt Management writes.
- A [SearchAPI](https://www.searchapi.io/) key and, to demonstrate Jev rather than fallback, a TypeSafe key.
- Region **us-east-2**, deliberately fixed by this CDK app and ingestion CLI.

### Install and deploy ECR

```powershell
Set-Location (Join-Path $Repo 'restaurant-finder-infra')
npm ci
npm run build
$AccountId = aws sts get-caller-identity --profile $env:AWS_PROFILE --query Account --output text
# First time only in this account/region:
npx --no-install cdk bootstrap "aws://${AccountId}/us-east-2"
npx --no-install cdk diff restaurantFinder-EcrStack
npx --no-install cdk deploy restaurantFinder-EcrStack
```

### Synchronize prompts, build and push

Prompt synchronization writes/reuses **nine immutable Bedrock prompt versions** and creates an ignored manifest. It needs no deployed Runtime and is separate from ordinary requests.

```powershell
Set-Location (Join-Path $Repo 'restaurant-finder-api')
uv sync --locked --extra local-aws --python 3.11
uv run --no-sync python -m src.deployment.sync_prompts --profile $env:AWS_PROFILE --region us-east-2
uv run --no-sync python -m src.deployment.validate_prompts

Set-Location $Repo
$Registry = "${AccountId}.dkr.ecr.us-east-2.amazonaws.com"
$Tag = 'demo-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss') + '-arm64'
$ImageUri = "${Registry}/restaurantfinder-agent:${Tag}"
aws ecr get-login-password --profile $env:AWS_PROFILE --region us-east-2 |
    docker login --username AWS --password-stdin $Registry
docker build --platform linux/arm64 -t $ImageUri ./restaurant-finder-api
docker push $ImageUri
```

The image installs locked dependencies and validates `.generated/prompt-manifest.json` during its build. Docker excludes other generated working material, local credentials and sample originals. Keep the same unique image URI through deployment; do not replace it with mutable `latest`.

### Deploy RAG and AgentCore

This enables hybrid retrieval, multipart and follow-ups for the **fictional corpus**. Real-source support stays off.

```powershell
Set-Location (Join-Path $Repo 'restaurant-finder-infra')
$ReleaseContext = @(
    '-c', "imageUri=$ImageUri",
    '-c', 'documentMultipartEnabled=true',
    '-c', 'documentFollowupsEnabled=true',
    '-c', 'documentRealSourcesEnabled=false',
    '-c', 'ragRetrievalMode=hybrid'
)
# Optional existing guardrail: append BOTH before diff/deploy:
# $ReleaseContext += @('-c','guardrailId=YOUR_ID','-c','guardrailVersion=YOUR_NUMBERED_VERSION')
npx --no-install cdk diff restaurantFinder-RagStack @ReleaseContext
npx --no-install cdk deploy restaurantFinder-RagStack @ReleaseContext
npx --no-install cdk diff restaurantFinder-AgentCoreStack @ReleaseContext
npx --no-install cdk deploy restaurantFinder-AgentCoreStack @ReleaseContext
```

Review each diff/approval prompt. Without an explicit guardrail pair, startup performs automatic create-or-get guardrail setup, which may create a resource and uses the automatic/DRAFT path. For repeatable moderation, supply your existing **READY numbered version** as both contexts; do not copy the author's pair. Preserve all intended contexts on later updates.

Read outputs in PowerShell:

```powershell
$AgentStack = aws cloudformation describe-stacks --stack-name restaurantFinder-AgentCoreStack --profile $env:AWS_PROFILE --region us-east-2 --output json | ConvertFrom-Json
$AgentOutputs = @{}
$AgentStack.Stacks[0].Outputs | ForEach-Object { $AgentOutputs[$_.OutputKey] = $_.OutputValue }
$RagStack = aws cloudformation describe-stacks --stack-name restaurantFinder-RagStack --profile $env:AWS_PROFILE --region us-east-2 --output json | ConvertFrom-Json
$RagOutputs = @{}
$RagStack.Stacks[0].Outputs | ForEach-Object { $RagOutputs[$_.OutputKey] = $_.OutputValue }
$AgentOutputs
$RagOutputs
```

The UI needs `RuntimeArn`; local API configuration needs `GatewayUrl`, `GatewayId`, `MemoryId`; ingestion needs `DocumentBucketName`, `VectorIndexArn`. Inspect Runtime readiness in the AgentCore console. Successful stack creation alone is not an end-to-end chat check.

### Populate secrets

In AWS Secrets Manager, region **us-east-2**, edit CDK's secrets:

| Secret | Value |
| --- | --- |
| `restaurantFinder/restaurant-search-key` | JSON object with an `api_key` field containing your SearchAPI key. |
| `restaurantFinder/jev-router-key` | **Plaintext TypeSafe key**, not JSON. The loader treats the entire SecretString as the key. |

Use the secret-value editor; avoid putting real keys in shell history, Git, Docker arguments or screenshots. Populate secrets before your first invocation. The Jev client is initialized at application startup: after changing its key, start a new Chainlit chat (which supplies a fresh Runtime session ID) rather than reuse the old conversation, then inspect the routing result/logs. A client-initialization message alone does not prove a successful Jev classification; fallback is not evidence that Jev is active. Missing Jev access uses Bedrock fallback.

### Activate the sample corpus

`DOCUMENT_RAG_ENABLED=true` does not upload documents. Dry-run first, then explicitly publish; publication performs bounded embeddings/writes and updates the active pointer last.

```powershell
Set-Location (Join-Path $Repo 'restaurant-finder-api')
uv run --no-sync python -m src.deployment.ingest_documents --dry-run --corpus sample_documents/corpus.json
uv run --no-sync python -m src.deployment.ingest_documents --publish --corpus sample_documents/corpus.json --profile $env:AWS_PROFILE --region us-east-2 --bucket $RagOutputs['DocumentBucketName'] --index-arn $RagOutputs['VectorIndexArn'] --max-embedding-attempts 48 --report .generated/rag/initial.json
```

Check exit code and report status. Real-source preparation commands require reviewed research/bytes absent from a fresh clone; they are not general web-ingestion commands. Do not enable real-source mode against an unreviewed/mismatched corpus. See [the engineering guide](DOCUMENT_RAG.md).

## 4. Connect the local UI to AWS

In a new terminal at the clone root:

```powershell
$Repo = (Get-Location).Path
Set-Location (Join-Path $Repo 'restaurant-finder-ui')
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked --extra local-aws --python 3.11
```

Edit this directory's `.env` using **your outputs**. This is a template, not a shell command:

```dotenv
AGENT_CONNECTION_MODE=aws
AGENT_RUNTIME_ARN=YOUR_RuntimeArn_OUTPUT
AWS_REGION=us-east-2
AWS_PROFILE=default
DOCUMENT_SOURCE_VIEWER_ENABLED=true
RAG_DOCUMENT_BUCKET=YOUR_DocumentBucketName_OUTPUT
MEMORY_ACTOR_ID=
```

The local identity needs Runtime invocation permission. Source viewing also needs `s3:GetObject` on `arn:aws:s3:::YOUR_BUCKET/rag/generations/*/sources/*`. Reads address immutable generation keys and verify SHA-256; the current viewer does not request S3 version IDs. Do not make the bucket public.

```powershell
uv run --no-sync chainlit run app.py --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The UI remains local while the backend runs on AWS. Leave `MEMORY_ACTOR_ID` empty for conversation-scoped anonymous memory; stable values are for single-user local demonstrations, not shared authenticated use.

Optional **billable** checks, after deciding your budget:

1. Ask a greeting and a restaurant search.
2. Ask: "Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources."
3. Inspect both originals: venue, item, quotation, page/lines and price.
4. Ask: "Which is cheaper?" with follow-ups enabled.
5. Ask an explicit unsupported parking question; missing evidence must not become a fact.

These use fictional fixtures, not Ciccio/Bottega. Search can return names outside the document corpus. The known early source-viewer mismatch remains unresolved; independently verify source associations.

## 5. Optional local API

Models, gateway, memory, browser and optional document storage still use AWS. This is not an offline application. In a new terminal at the clone root:

```powershell
$Repo = (Get-Location).Path
$env:AWS_PROFILE = 'default'
Set-Location (Join-Path $Repo 'restaurant-finder-api')
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --locked --extra local-aws --python 3.11
```

Edit API `.env`: set `AWS_REGION`, `GATEWAY_URL`, `GATEWAY_ID`, `MEMORY_ID` from your outputs and optionally `TYPESAFE_API_KEY`. For document questions set `DOCUMENT_RAG_ENABLED=true`, bucket/index and intended multipart/follow-up/hybrid options. Keep real-source mode off for sample fixtures. If pinning guardrails, set **both** `BEDROCK_GUARDRAIL_ID` and numbered `BEDROCK_GUARDRAIL_VERSION`; otherwise automatic startup may create one. Keep local observability off unless configuring exporters deliberately.

```powershell
uv run --no-sync python -m src.main
```

The locked SDK's `app.run()` defaults to **8080**, loopback outside containers. Startup initializes infrastructure and is AWS-assisted. Keep this terminal open. In another terminal, configure/start the UI as in section 4 but use:

```dotenv
AGENT_CONNECTION_MODE=local
AGENTCORE_API_URL=http://localhost:8080/invocations
```

Keep the source bucket/profile for citation viewing. Chainlit runs on port 8000. Stop servers with Ctrl+C in their own terminals.

## 6. Workflows and observability

Offline CI runs on push/PR. Image/infra deployment and destruction require manual dispatch. The optional deployment workflows expect the GitHub secret names in their YAML; local deployment uses your local profile. Offline CI requires no GitHub AWS credentials.

The infra workflow passes only `imageUri`: it can reset optional document features and omits an explicit guardrail pair. It is not a replacement for context-preserving manual CDK commands on a customized installation.

Runtime OpenTelemetry exports need regional AWS permissions/destination configuration: see [AWS ADOT setup](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLP-UsingADOT.html) and [Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html). Initialization alone does not prove delivery. Check correlated spans/logs from a known request. Dashboard/indexing availability depends on account settings. Logs are not private model reasoning and may contain prompts/results; restrict access and choose retention. Ingestion/query charges can apply.

## 7. Cleanup and retained resources

Stopping local servers leaves cloud resources running. Destruction is **destructive**, requires separate review, and is not a setup verification step. From infra, `npx --no-install cdk destroy --all` requests stack removal; verify the account first.

Retained ECR images/repository, S3 versions, S3 vector bucket/index and telemetry logs can survive deletion. Automatic guardrails, prompt versions and regional tracing are outside some stack lifecycle operations. Inspect remaining resources and charges separately; do not delete retained data or change shared regional settings blindly. Redeployment may need to handle retained named-resource conflicts.

## 8. Verification boundaries

The 2026-10-22 cleanup checks command contracts and offline behavior. It does **not** run a fresh-account AWS deployment or certify model availability, IAM permissions, current prices, Runtime state or end-to-end source viewing. Historical runbooks describe their own checkpoints, not your account.

See [the readiness plan](HANDOFF_PRD_PUBLIC_REPOSITORY_READINESS.md) for execution evidence and the remaining publication gate.
