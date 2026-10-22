# Restaurant Finder infrastructure

AWS CDK application in `bin/cdk.ts`. The app fixes deployment to **us-east-2** and obtains the account from CDK credentials/context. Use Node.js 22 and `npm ci` with the committed lockfile. Deployment commands are in [Setup](../docs/SETUP.md#3-first-aws-deployment).

| Stack | Resources / dependency |
| --- | --- |
| `restaurantFinder-EcrStack` | Retained ECR repository for the ARM64 image. |
| `restaurantFinder-RagStack` | Private versioned S3 corpus bucket and retained S3 vector bucket/index (512 dimensions, cosine). |
| `restaurantFinder-AgentCoreStack` | Runtime, IAM-authorized MCP Gateway/Lambda, SearchAPI/Jev secrets, Memory, roles and telemetry configuration. Depends on ECR and RAG. |

Push a valid uniquely tagged image before deploying AgentCore. The image must contain the generated immutable prompt manifest. Corpus ingestion/activation and regional CloudWatch trace-destination configuration are explicit operations outside normal Runtime startup.

## CDK contexts

| Context | Default | Meaning |
| --- | --- | --- |
| `imageUri` | Repository `:latest` | Supply a unique audited ARM64 image URI for reproducibility. |
| `documentMultipartEnabled` | `false` | Bounded menu-price/cancellation tasks. |
| `documentFollowupsEnabled` | `false` | Supported contextual continuations. |
| `documentRealSourcesEnabled` | `false` | Reviewed real-source corpus support. |
| `ragRetrievalMode` | `vector` | `vector` or `hybrid` (BM25 + vector RRF). |
| `guardrailId`, `guardrailVersion` | Omitted | Supply both for an existing immutable guardrail; version must be a positive integer string. Omission uses automatic guardrail setup. |

Boolean contexts accept booleans or exact `true`/`false` strings. Omitting a previously enabled flag on a later deployment can disable it. Preserve intended contexts explicitly. Deployed `DOCUMENT_RAG_ENABLED=true` does not ingest documents or publish an active corpus.

## Checks and workflow limits

`npm run build` and `npm test -- --runInBand` are local checks. The [offline setup](../docs/SETUP.md#2-offline-checks) supplies the dummy-account `cdk synth --no-lookups` command. `cdk diff`, `bootstrap`, `deploy` and `destroy` are AWS operations, not substitutes for offline validation.

Image/infra workflows are manual; offline CI runs on pushes/PRs. The infrastructure workflow passes only `imageUri`, so it does not preserve all optional document feature settings or a separately pinned guardrail pair. Use reviewed manual CDK commands for the walkthrough configuration. Do not run multiple deployment paths concurrently.

Destroying stacks does not delete retained ECR images, corpus/vector storage or retained log groups, and does not undo every resource created outside CloudFormation (such as automatic guardrails, prompt versions or regional tracing). Review [cleanup](../docs/SETUP.md#7-cleanup-and-retained-resources).
