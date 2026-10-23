# Architecture: reading guide and sources

[Editable SVG](architecture.svg) · [PNG preview](architecture.png)

The diagram describes the repository's supported architecture, not a live inventory of a particular AWS account. Optional paths require the switches and account configuration documented in the [setup guide](../SETUP.md). The demonstrated UI is local; the Python backend runs on AWS.

## Read the connections

- **Blue:** application requests and web-tool calls. Restaurant search and document RAG are alternatives selected by the router, not a sequential pipeline.
- **Gray:** workflow answers converge on final moderation. Simple/off-topic responses bypass the tools. The diagram groups internal functions to keep the overview readable.
- **Purple:** external Jev classification and the approved-turn memory path. Missing/unavailable Jev falls back to Bedrock; supported contextual document follow-ups can use deterministic routing shortcuts.
- **Teal:** document retrieval and the separately authorized local original-source read. Source originals, manifest/chunks and vectors are different objects/access paths.
- **Bottom strip:** supporting deployment and telemetry relationships, not extra steps performed for each question. CDK defines resources; an explicit build/push supplies the ECR image that Runtime runs.

Bedrock serves the configured chat model, router fallback, Titan V2 embeddings and enabled guardrails. The Bedrock service icon is reused for those capabilities; it is not a separate Titan or Claude logo. AgentCore's service icon represents Runtime, Gateway and Memory because the supplied toolkit does not provide distinct icons for each of those capabilities.

### Deliberate simplifications

- Search's tool loop is bounded to four tool calls per turn. Browser tools are optional. A separate, optional document-covered discovery branch intersects the active catalog with online verification; it is grouped under discovery/search here, not drawn as another model pipeline.
- Document comparisons/multipart requests use at most two concurrent workers; single-document questions need not fan out. BM25/RRF is optional, local hybrid-ranking logic alongside vector retrieval. This is custom RAG, not Amazon Bedrock Knowledge Bases.
- Runtime can read the active pointer, generation manifests/chunks and vector index. It cannot read original-source/cache objects or write/activate the corpus. The local UI uses its own AWS profile to fetch generation-specific originals and verify their SHA-256 hashes.
- Final moderation precedes response delivery and the durable conversation-turn post-hook. Session checkpoints are a separate state mechanism; the approval rule does not imply every checkpoint is written only after final moderation. Memory retrieval is on demand.
- Reviewed ingestion/activation and prompt synchronization are explicit preparation/deployment operations. Live search does not ingest arbitrary discovered menus automatically. Supporting secrets/IAM/prompt resources are omitted from the overview, not replaced by an invented authentication layer.
- OpenTelemetry records operation spans, logs and metrics. CloudWatch export/account setup is required; the diagram does not claim an enabled waterfall dashboard or expose private model reasoning.

## Component-to-code map

| Diagram component | Authoritative implementation |
| --- | --- |
| Local Chainlit request/response handling | [UI application](../../restaurant-finder-ui/app.py) |
| Original-source validation and viewing | [Source viewer](../../restaurant-finder-ui/source_documents.py) |
| Input moderation and buffered SSE delivery | [Infrastructure streaming](../../restaurant-finder-api/src/infrastructure/streaming.py) |
| LangGraph nodes, alternative routes and convergence | [Graph construction](../../restaurant-finder-api/src/application/orchestrator/workflow/graph.py), [edges](../../restaurant-finder-api/src/application/orchestrator/workflow/edges.py), [nodes](../../restaurant-finder-api/src/application/orchestrator/workflow/nodes.py) |
| Jev classification and Bedrock fallback | [Jev adapter](../../restaurant-finder-api/src/infrastructure/jev_router.py), [router node](../../restaurant-finder-api/src/application/orchestrator/workflow/nodes.py) |
| Chat-model generation | [Model adapter](../../restaurant-finder-api/src/infrastructure/model.py), [chains](../../restaurant-finder-api/src/application/orchestrator/workflow/chains.py) |
| Search tools / optional browser tools | [Tool registration](../../restaurant-finder-api/src/application/orchestrator/workflow/tools.py), [search Lambda](../../restaurant-finder-infra/mcp/lambda/handler.py) |
| Document scope, retrieval and quotation validation | [Document workflow](../../restaurant-finder-api/src/application/document_rag/workflow.py), [retriever](../../restaurant-finder-api/src/application/document_rag/retrieval.py) |
| Bounded document workers and follow-ups | [Multipart workflow](../../restaurant-finder-api/src/application/document_rag/multipart_workflow.py), [comparison workflow](../../restaurant-finder-api/src/application/document_rag/comparison_workflow.py), [conversation handling](../../restaurant-finder-api/src/application/document_rag/conversation.py) |
| Optional document-covered discovery | [Discovery branch](../../restaurant-finder-api/src/application/document_rag/discovery.py) |
| Titan query embeddings | [Embedding adapter](../../restaurant-finder-api/src/infrastructure/embeddings.py) |
| AgentCore memory | [Memory adapters](../../restaurant-finder-api/src/infrastructure/memory.py), [approved-turn post-hook](../../restaurant-finder-api/src/application/orchestrator/workflow/nodes.py) |
| OpenTelemetry / CloudWatch | [Observability](../../restaurant-finder-api/src/infrastructure/observability.py), [RAG spans](../../restaurant-finder-api/src/infrastructure/rag_observability.py) |
| Runtime configuration and restricted data access | [AgentCore stack](../../restaurant-finder-infra/lib/stacks/agentcore-stack.ts) |
| ECR and document-store infrastructure | [ECR stack](../../restaurant-finder-infra/lib/stacks/ecr-stack.ts), [RAG stack](../../restaurant-finder-infra/lib/stacks/rag-stack.ts) |

Actual node/edge construction is authoritative; older explanatory docstrings can show a simplified graph.

## Logo and icon credits

Artwork was retrieved from the official sources below on **2026-10-23**. Logos identify dependencies/services; their use does not imply endorsement or transfer ownership. This document does not assert a new license for vendor marks or inherited project code.

| Artwork | Official source and treatment |
| --- | --- |
| Bedrock, AgentCore, Lambda, S3, S3 Vectors, CloudWatch, ECR and CDK | [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/), [July 31, 2026 icon package](https://d1.awsstatic.com/onedam/marketing-channels/website/public/shared/architecture-icon-release/Icon-package_07312026.5846e92413caa21490223536cc97f1269e44fa92.zip). Official service/resource SVGs, unchanged geometry/colors and proportional scaling. AWS supplies these for architecture diagrams. |
| LangGraph lockup | [LangChain brand assets and usage guidance](https://www.langchain.com/brand-assets), [supplied light-background SVG](https://cdn.prod.website-files.com/65b8cd72835ceeacd4449a53/6a994264a64b3afcdd880f6b_LangGraph_OSS%20Lockup_light%201.svg). Complete lockup, original colors/proportions, clear space; no community-logo substitution. |
| TypeSafe mark | [Official TypeSafe site](https://typesafe.ai/), header SVG `svg-684955628_986`. The supplied white glyph is placed on a dark background; the website's CSS color variable is resolved to its existing white fallback. This is the TypeSafe mark, not an invented Jev-specific logo. |
| Chainlit | [Official Chainlit organization](https://github.com/Chainlit), [organization avatar](https://avatars.githubusercontent.com/u/128686189?v=4&s=200). Organization identity was verified through GitHub's organization metadata. Original PNG, proportional scaling. |
| SearchAPI | [Official SearchAPI site](https://www.searchapi.io/), inline header logo SVG. Complete mark/wordmark preserved with its original proportions. |
| OpenTelemetry | [Official OpenTelemetry site](https://opentelemetry.io/), inline header SVG labeled `opentelemetry-logo-title`. Original white lockup on a dark background. |

Custom workflow cards, boundaries and arrows are generic diagram elements, not fabricated vendor logos. Logo SVGs are embedded in the editable diagram; the Chainlit PNG is embedded as a data URI. No external image requests, scripts or fonts are needed to display the SVG. The PNG is a direct 2× raster export of that same SVG.

### AWS package members used

- `Architecture-Service-Icons_07312026/Arch_Artificial-Intelligence/64/Arch_Amazon-Bedrock-AgentCore_64.svg`
- `Architecture-Service-Icons_07312026/Arch_Artificial-Intelligence/64/Arch_Amazon-Bedrock_64.svg`
- `Architecture-Service-Icons_07312026/Arch_Compute/64/Arch_AWS-Lambda_64.svg`
- `Architecture-Service-Icons_07312026/Arch_Storage/64/Arch_Amazon-Simple-Storage-Service_64.svg`
- `Resource-Icons_07312026/Res_Storage/Res_Amazon-Simple-Storage-Service_S3-Vectors_48.svg`
- `Architecture-Service-Icons_07312026/Arch_Management-Tools/64/Arch_Amazon-CloudWatch_64.svg`
- `Architecture-Service-Icons_07312026/Arch_Containers/64/Arch_Amazon-Elastic-Container-Registry_64.svg`
- `Architecture-Service-Icons_07312026/Arch_Developer-Tools/64/Arch_AWS-Cloud-Development-Kit_64.svg`
