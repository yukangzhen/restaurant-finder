# Handoff PRD: Custom Document RAG for Restaurant Menus and Policies

**Status:** Approved by the owner on 2026-10-08; implementation and bounded rollout in progress.

**Prepared:** October 8, 2026.

**Repository:** C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore

**Inspected baseline:** Branch feat/jev-router, commit 7ba4643c3b1b200074372e2c01f325104b099dac. The worktree was clean before this PRD was added.

## 1. Outcome, audience, and reason

Add a custom document retrieval-augmented generation pipeline to the existing Restaurant Finder. It must ingest a small collection of restaurant menus and policies, retrieve relevant passages, and answer document questions with inspectable source references.

The owner wants a LinkedIn portfolio demonstration of AI engineering. The deliverable should expose meaningful engineering decisions: parsing, chunking, embedding compatibility, metadata filters, publication of document versions, model output contracts, citation validation, graph orchestration, failure handling, and behavioral verification.

This is a personal demonstration using explicitly fictional restaurants and synthetic documents. It is not a public service or a claim that restaurant facts are verified against real businesses. Credit the upstream project and identify the custom RAG work as the owner's contribution.

### Exact deliverables

1. Python ingestion CLI with a local dry-run mode and an explicitly invoked AWS publication mode.
2. Three fictional restaurants, each with a menu and a policy document; at least one menu is a text-based PDF.
3. Versioned document/chunk storage in ordinary S3 and an S3 Vectors index containing Titan embeddings.
4. A dedicated LangGraph document-question path, selected by Jev with the existing Bedrock fallback.
5. Cited answers rendered through the existing moderated SSE response.
6. Focused offline regression tests and a bounded live verification record.
7. CDK definitions, configuration examples, setup instructions, architecture diagrams, and a sanitized implementation checkpoint.

### Observable completion

An owner can ingest the sample corpus, ask a price or policy question through the normal UI, inspect the supporting passage and its document location, repeat ingestion without creating duplicates, update a menu, and receive an answer from the new published version. Existing restaurant search, memory, and guardrail checks still pass.

Do not declare the deployed feature complete if an acceptance criterion remains unverified. Local completion and AWS completion are separate statuses in the final report.

## 2. Inspected baseline and integration constraints

| Existing component | Inspected behavior | Required integration |
| --- | --- | --- |
| workflow/state.py | Three intents: restaurant_search, simple, off_topic | Add document_qa and typed RAG state |
| infrastructure/jev_router.py | Jev Choice classification; reusable client; timeout/error fallback | Add document criteria without changing Jev model selection |
| workflow/nodes.py | Bedrock fallback parses labels by substring | Validate the complete fallback routing label against the shared enum |
| workflow/graph.py | Search ReAct loop, simple response, output guardrail, memory hook | Add a bounded document branch that rejoins the output guardrail |
| application/orchestrator/streaming.py | Invokes the graph once; resets turn fields; returns approved text | Reset temporary RAG fields on every turn |
| infrastructure/streaming.py | Input moderation, one approved complete SSE chunk, done/error/blocked events | Preserve the public payload and event shape |
| infrastructure/memory.py | AgentCore checkpointing and semantic memory retrieval | Preserve memory; never treat remembered restaurant facts as current document evidence |
| restaurant-finder-ui/app.py | Renders response text and blocked/error messages | Display citations inside approved Markdown text |
| deployment/sync_prompts.py and infrastructure/prompt_metadata.py | Explicit lists of six prompt objects | Register new RAG prompts in both lists |
| restaurant-finder-infra | ECR and AgentCore stacks; installed CDK exposes CfnVectorBucket and CfnIndex | Add a separate RAG stack and scoped runtime read permissions |

The runtime currently has unused broad S3 vector write/delete permissions and a wildcard S3 document-prefix policy. Review their usages, then replace those two statements with the precise RAG read permissions described below. This is an explicit scope item, not a general IAM redesign.

The installed CDK S3 Vectors declarations inspected during planning do not expose an indexMode property. Do not invent a property or upgrade dependencies solely to add a newer index mode. Use the supported index configuration and verify filtered retrieval with the actual small corpus.

Previously recorded deployment and telemetry facts in README are historical evidence. Re-read AWS state before cloud work. In particular, the last repair record had no fresh telemetry for its latest live checks; do not assume that new RAG spans are delivered.

## 3. Scope and design decisions

### Included in version 1

- English Markdown and digitally generated PDFs with an extractable text layer.
- Six controlled source documents and one owner-run update to demonstrate version handling.
- Section/page-aware chunking and complete menu-item records.
- Titan Text Embeddings V2: amazon.titan-embed-text-v2:0, 512 dimensions, normalized float embeddings.
- S3 Vectors semantic retrieval with exact generation, restaurant, and optional document-type filters.
- Dedicated document_qa workflow and a bounded Haiku structured-output call.
- Source filename, restaurant, PDF page or Markdown section, document version, and supporting excerpt.
- Explicit clarification, insufficient-evidence, disabled, and unavailable outcomes.
- Immutable corpus generations, idempotent ingestion, publication conflict detection, and a reversible active pointer.
- Existing moderation before display and memory.
- Offline correctness checks and bounded AWS/UI smoke checks.

### Deferred

Public document uploads, authentication, multi-tenant access controls, arbitrary web/PDF crawling, OCR, complex table reconstruction, image embeddings, multilingual retrieval, hybrid lexical search, reranking models, cross-restaurant aggregation, numerical menu analysis, automatic document refresh, retention cleanup, and latency/cost benchmarking.

Do not add another database or another foundation model for these deferred capabilities.

### Answer style decision for owner review

Version 1 uses **extractive answers**: Haiku selects and organizes short, exact supporting quotations, and application code renders them with citations. It does not display unrestricted model-written factual paraphrases.

Example:

> According to the uploaded demo menu:
>
> “Mushroom pasta — RM28 — vegetarian.”
>
> [1] Harbor Pasta Lab — menu.pdf, page 2, document version 1.

This keeps the first grounding contract inspectable. A citation validator can establish that a quotation exists in the retrieved passage. It cannot establish that the underlying source is true, or that the model selected every relevant passage. Test relevance separately and document that limit.

The feature still performs RAG: retrieval supplies evidence to Haiku, which selects the answer material in a validated schema. Natural-language paraphrasing can be considered in a later approved increment.

## 4. Architecture

### Ingestion, run by the owner

~~~text
Local corpus manifest + source files
  -> validate files and restaurant catalog
  -> extract page/section text
  -> create complete, traceable chunks
  -> determine deterministic corpus generation
  -> reuse compatible cached embeddings or invoke Titan
  -> stage originals, chunks, embeddings, and vectors
  -> verify staged records and retrieval readiness
  -> publish the active manifest pointer conditionally
~~~

### Question answering, run by the application

~~~text
Existing input guardrail
  -> Jev router (Bedrock fallback)
     -> existing search/simple paths
     -> document_qa:
          resolve restaurant and document scope
          -> read and pin active corpus generation
          -> embed current document question
          -> filtered vector query
          -> verify returned chunk records
          -> Haiku selects exact answer quotations
          -> validate citations and quotations
          -> render response
  -> existing output guardrail
  -> existing approved-turn memory hook
  -> existing complete SSE response
~~~

Never rerun the entire graph to recover a RAG failure. Do not perform ingestion from startup, request handling, or a model tool call.

## 5. Corpus and data contracts

### Controlled demo corpus

Create these fictional IDs and display names:

| restaurant_id | Display name | Documents |
| --- | --- | --- |
| demo-harbor-pasta | Harbor Pasta Lab (fictional demo) | Menu and policy |
| demo-sakura-table | Sakura Table Lab (fictional demo) | Menu and policy |
| demo-spice-garden | Spice Garden Lab (fictional demo) | Menu and policy |

Give two restaurants a dish with the same or similar name but different prices, so restaurant filtering has a meaningful test. Put Harbor's mushroom pasta at RM28 in version 1 and RM32 in the update fixture. Include explicit cancellation terms in a policy. Deliberately omit valet parking.

Use a checked-in corpus.json that maps document IDs, restaurant IDs, display names/aliases, document types, versions, and relative source paths. Source paths must resolve inside the corpus directory. Fixtures and updated variants must not be silently ingested as additional active documents.

Each file and the catalog must label the restaurants as fictional demo data. Do not list these records as real SearchAPI results.

### Required Pydantic contracts

| Contract | Required contents |
| --- | --- |
| DocumentSpec | Stable document_id, restaurant_id, filename, menu/policy type, declared version, source path |
| ExtractedUnit | document_id, canonical extracted text, PDF page or Markdown section/line location |
| ChunkRecord | chunk_id, document_id, source_hash, text_hash, restaurant_id, document_type, version, location, canonical text |
| GenerationManifest | schema version, generation_id, source/config fingerprint, embedding model/dimensions/normalization, chunker/extractor versions, complete catalog, document/chunk counts and immutable references |
| ActivePointer | schema version, generation_id, immutable generation manifest key |
| DocumentQuery | Current standalone query, valid restaurant_id or clarification status, optional menu/policy restriction |
| RetrievedEvidence | Pinned generation_id, chunk_id, canonical text, verified document location/version, vector distance |
| RagAnswerDraft | answered or insufficient_evidence; at most three selections containing chunk_id and exact quote |
| RagOutcome | answered, clarify, insufficient_evidence, disabled, unavailable, or invalid_answer; safe rendered text and sanitized internal status |

Models must reject extra/unexpected fields where they could affect scope or rendering. Distances are ranking values, not confidence percentages.

Do not accept S3 keys, vector filters, generation IDs, or source URLs from model output as authoritative. Resolve them through validated server-side manifests.

### Storage layout

~~~text
Ordinary S3 document bucket
  rag/active.json
  rag/generations/<generation_id>/manifest.json
  rag/generations/<generation_id>/sources/<document_id>.<extension>
  rag/generations/<generation_id>/chunks/<chunk_id>.json
  rag/embedding-cache/<embedding_fingerprint>.json

S3 Vectors index
  key: <generation_id>:<chunk_id>
  data: normalized 512-dimensional float32-compatible vector
  metadata:
    generation_id
    chunk_id
    document_id
    restaurant_id
    document_type
~~~

Keep vector metadata short. Retrieve text from verified chunk objects rather than putting source passages in filterable metadata. The generation manifest maps chunk IDs to locations and hashes.

S3 Vectors has separate total and filterable metadata limits; the proposed small identifiers stay below both. Current service constraints are documented in [S3 Vectors limitations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-limitations.html).

## 6. Ingestion, versioning, and publication behavior

1. Parse every source locally before any write. Reject missing files, duplicate IDs, unknown restaurants/types, unsafe paths, empty text, encrypted PDFs without supported access, and scanned/image-only PDFs.
2. Preserve one-based PDF page numbers. For Markdown preserve section heading and line location. Never invent page numbers for Markdown.
3. Split within a page/section using paragraphs and complete menu rows. Initial maximum chunk text: 1,800 characters. Optional overlap is one complete preceding paragraph/record, at most 200 characters, within the same section. Reject oversized indivisible records instead of silently dropping their price or splitting them ambiguously.
4. Preserve canonical text for quote validation. Apply documented Unicode/whitespace normalization consistently; retain a mapping to the original page/section. Do not remove currency symbols, decimals, negation, or policy conditions.
5. Hash source bytes and canonical chunks. Derive chunk IDs deterministically from document ID, source hash, location, and canonical text.
6. Derive generation_id from the sorted document/source fingerprints plus extraction/chunking configuration, embedding model, dimensions, and normalization. Timestamps must not alter this identity.
7. Dry-run prints document/chunk counts and intended embedding/cache/vector operations without initializing AWS clients.
8. AWS mode reads the existing active pointer and its ETag. If the identical complete generation is already active, validate its manifest compatibility and return an unchanged result without embedding or vector writes.
9. For a new generation, reuse embeddings only when canonical text and the entire embedding configuration match. Store cache entries immutably, validate dimensions/finite numbers, and never treat a malformed cache entry as a valid embedding.
10. Stage all documents/chunks for the complete new corpus generation. Reuse cached embeddings for unchanged passages, but insert the whole generation's vector records under generation-specific keys.
11. Write all vectors and an immutable generation manifest. Verify every expected key and hash, and run bounded filtered readiness probes using stored vectors. A partial staging failure must leave the active pointer unchanged.
12. Publish rag/active.json last: use If-None-Match for first publication or If-Match with the observed ETag for an update. An ETag conflict is a publication conflict, not permission to overwrite another publisher's changes. Re-read and report; never blindly replace the pointer.
13. Report the new generation, document/chunk counts, reused/new embeddings, and previous pointer version/reference. Retain the previous generation for rollback.

This is generation-level publication, not a transaction spanning S3 and S3 Vectors. Reading the active pointer pins one generation for the turn; it does not guarantee instantaneous visibility of every vector operation. Failed readiness checks prevent publication, and retrieval inconsistencies fail safely.

AWS documents conditional S3 writes and their conflict outcomes in [Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html).

### Initial limits

- Six active documents; maximum 5 MiB per file, 10 PDF pages per document, and 100,000 extracted characters per document.
- At most 48 chunks in one published demo generation. If the dry-run exceeds this, adjust the controlled corpus or explain a proposed limit change before cloud work.
- Sequential or at most two concurrent embedding calls; vector batches at most 100 records.
- At most ten readiness polls within 60 seconds total per publication. Polls must release control between waits.
- At most two published generations during initial verification: initial corpus and one price update.
- No source deletion, vector deletion, automatic garbage collection, or lifecycle expiry of retained generations.

These are demo bounds, not claims about system capacity.

## 7. Retrieval and answer behavior

### Routing and scope

Add document_qa to the shared intent contract, Jev choices, Bedrock routing prompt, routing node, and graph edges.

Route questions about uploaded menus/policies, or the named fictional catalog restaurants' documented details, to document_qa. Route ordinary real-world restaurant discovery to the existing search path. Existing memory questions remain memory/search requests. A document question must not silently search the web or answer from AgentCore memory when document retrieval fails.

Use a shared intent enum and accept the Bedrock fallback only when its complete normalized label matches one allowed intent. Invalid fallback output must produce a controlled routing failure rather than a guessed document/search action.

Resolve explicit restaurant names/IDs using the checked-in catalog/validated manifest. Support a single-restaurant follow-up such as “And what is its cancellation policy?” using the last approved document scope in that conversation. If the restaurant is absent, ambiguous, or unknown, ask one clarification and perform no embeddings/vector query.

The first version handles one restaurant per document question. Requests for cross-restaurant comparisons or exhaustive lists get a focused clarification or a statement of the supported scope.

### Query preparation

If a follow-up needs rewriting, use one structured Haiku query-preparation call at most. Include the current question and only the recent context needed to resolve its reference; do not send the entire tool history.

Validate any selected restaurant/type against the catalog and explicit conversation scope. The model cannot expand scope to a different restaurant. An explicit restaurant in the latest message overrides prior scope.

For a self-contained question with a resolved restaurant, use the current question directly. Do not add a model call solely to rewrite it.

### Retrieval

1. Read rag/active.json for each document turn; pin its generation and fetch the immutable manifest.
2. Validate schema, configured embedding model, 512 dimensions, normalization, and expected index configuration. Misconfiguration is unavailable, not an empty search.
3. Embed the query using exactly the ingestion configuration.
4. Query S3 Vectors with generation_id and restaurant_id filters, plus document_type if resolved. Initial topK is 5, bounded from 1 through 10.
5. Request distances and metadata. Use the complete paginated result contract supported by the installed SDK, deduplicate IDs, then enforce the configured limit.
6. Validate each result against the pinned manifest. Fetch only listed chunk keys under the expected generation prefix; verify content hash, restaurant, document type, and location.
7. Build a bounded evidence context: at most five passages and 9,000 passage characters. Preserve whole passages; do not truncate through a menu price or policy condition.
8. A malformed result, failed object read, generation mismatch, or hash mismatch must not be passed to Haiku as valid evidence. Return unavailable when consistency cannot be established.

No hard-coded distance threshold may be described as calibrated confidence. Retrieval returns candidates; Haiku's selection and the corpus correctness fixtures determine whether an answer is supported in the tested cases.

See [S3 Vectors queries](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-query.html) and [Metadata filtering](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-metadata-filtering.html).

### Answer selection and rendering

Use the existing Haiku generation model with a RAG-specific prompt and structured output. Retrieved passages are untrusted source data, not instructions. This generation chain must have no browser, memory, ingestion, or arbitrary external tools bound.

RagAnswerDraft contains only status and selected exact quotes with chunk IDs. Validate:

- Answered requires at least one selection; insufficient_evidence requires none.
- Every selected chunk is part of this turn's verified evidence and pinned generation.
- Quotes match canonical source text using the documented normalization.
- At most three quotes, each at most 600 characters, complete enough to retain price units and policy conditions.
- Quotes containing attempted instructions to the assistant are not treated as answers to unrelated factual questions.
- Source names, locations, and versions come from the manifest, not the model.

Render through a deterministic Markdown renderer. Escape source-derived Markdown/HTML so document content cannot inject misleading links or UI controls. Version 1 shows text citations and supporting excerpts, without public S3 URLs, presigned downloads, or raw document attachments.

There is at most one answer-selection call and no automatic repair loop. Invalid structured output/citations result in a safe invalid_answer outcome; do not ask the model repeatedly until it happens to pass.

### Guardrails, memory, and state

- Route every document result, including clarification and unavailable text, through the existing output guardrail.
- Display and save only the final approved/masked text. No separate citation/source event may bypass moderation.
- Preserve one graph invocation per user turn and the complete SSE chunk contract.
- Reset rag_query, rag_evidence, rag_draft, rag_outcome, and proposed scope on each new turn. Retain only the last approved restaurant/document scope for follow-ups.
- Set the last scope only after output approval; a blocked request must not advance it.
- Keep document facts out of the source-selection process when retrieved from conversational memory. The active manifest and retrieved chunks are authoritative for this feature.
- Document QA uses a fixed retrieval operation and no autonomous tool loop. Record its retrieval count separately; preserve the existing four-tool budget for the search branch.

## 8. AWS resources, permissions, and configuration

### New CDK stack

Add restaurantFinder-RagStack with:

1. An ordinary versioned S3 bucket for source documents, chunks, cache, and manifests.
2. One S3 vector bucket.
3. One vector index: float32, dimension 512, cosine distance.
4. Outputs for document bucket name, vector bucket ARN, vector index ARN, and active pointer key.

Use S3-managed encryption, private access, TLS enforcement for the ordinary bucket, and RETAIN deletion/update-replacement policies. Do not add custom KMS keys, public access, or automatic object deletion.

Keep existing stack IDs/logical resource identities. Register RagStack in bin/cdk.ts and export it from lib/stacks/index.ts. Pass resource references to AgentCoreStack and make its dependency explicit. On future normal CDK deployments, the declared dependency should provision RAG before the AgentCore configuration uses it.

The installed CDK already provides the required low-level S3 Vectors resources. Source the index ARN from attrIndexArn; do not construct an ARN from an assumed physical name.

CloudFormation treats dimension, distance metric, and metadata configuration changes as index replacements. Freeze these values for v1. Any later embedding/index migration needs its own plan. See [AWS::S3Vectors::Index](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-s3vectors-index.html).

### Runtime identity

The runtime receives only:

- s3:GetObject on active pointer, generation manifests, and generation chunk prefixes.
- s3vectors:QueryVectors, s3vectors:GetVectors, and s3vectors:GetIndex on the exact new index.
- bedrock:InvokeModel on the Titan V2 foundation model ARN in us-east-2, in addition to the existing Haiku permissions.

GetVectors is required alongside QueryVectors when filtering or returning vector metadata. Include it deliberately. See [S3 Vectors access management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-access-management.html).

The runtime must have no RAG document/cache/pointer writes and no vector PutVectors/DeleteVectors. Replace the two inspected unused broad S3/vector statements with scoped reads after confirming there are no other consumers. Preserve unrelated IAM statements.

### Owner ingestion identity

The CLI uses the owner's existing AWS profile. Document the exact required reads/writes to the new prefixes/index and Titan invocation. Deployment uses the existing CDK execution identity.

If the owner identity lacks permission, produce the specific missing-action/resource evidence and a narrow proposed grant. Do not automatically attach broad policies, create access keys, or change the account identity.

### Configuration

Add these fields to settings and .env.example:

| Field | Proposed default / behavior |
| --- | --- |
| DOCUMENT_RAG_ENABLED | false locally; true in the deployed Runtime after approved RAG integration |
| RAG_DOCUMENT_BUCKET | Empty until configured |
| RAG_VECTOR_INDEX_ARN | Empty until configured |
| RAG_ACTIVE_MANIFEST_KEY | rag/active.json |
| RAG_EMBEDDING_MODEL_ID | amazon.titan-embed-text-v2:0 |
| RAG_EMBEDDING_DIMENSIONS | 512, matching manifest/index |
| RAG_TOP_K | 5, range 1 through 10 |
| RAG_MAX_CONTEXT_CHARACTERS | 9000 |
| RAG_REQUEST_TIMEOUT_SECONDS | 60 for the document branch |

Use normalized float embeddings consistently. Validate vectors as finite numbers of exactly 512 elements. Titan request parameters and inputTextTokenCount are documented in [Titan embedding request/response](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-embed-text.html).

Disabled mode initializes no RAG AWS clients. A disabled document question gets a readable disabled response through moderation. Enabled but misconfigured/unpublished mode gets unavailable; existing search/memory paths remain usable.

Use lazy boto3 clients with bounded connect/read timeouts and explicitly limited retries. Run blocking SDK calls off the async event loop. Propagate cancellation; do not convert it into an unsupported answer. A timed-out worker may finish its read later, but no RAG request path may perform writes.

## 9. Proposed file ownership

Paths below are relative to the repository root. Keep new package initializers lightweight.

| Path | Responsibility |
| --- | --- |
| restaurant-finder-api/src/domain/document_rag.py | Contracts, enums, citation/quote validation, safe rendering |
| restaurant-finder-api/src/application/document_rag/ingestion.py | Ingestion orchestration and generation publication rules |
| restaurant-finder-api/src/application/document_rag/retrieval.py | Read-only retrieval and manifest/evidence validation |
| restaurant-finder-api/src/application/document_rag/workflow.py | Query preparation and answer-selection orchestration |
| restaurant-finder-api/src/infrastructure/document_parser.py | Markdown/PDF extraction and deterministic chunking |
| restaurant-finder-api/src/infrastructure/document_store.py | S3 object reads/writes and conditional active-pointer publication |
| restaurant-finder-api/src/infrastructure/embeddings.py | Titan invocation, validation, token usage, compatible cache contracts |
| restaurant-finder-api/src/infrastructure/vector_store.py | S3 Vectors put/get/query operations and pagination |
| restaurant-finder-api/src/deployment/ingest_documents.py | CLI, explicit dry-run/publish modes, identity/region checks and reports |
| restaurant-finder-api/src/domain/prompts.py | RAG_QUERY_PROMPT and RAG_ANSWER_PROMPT; updated routing prompt |
| restaurant-finder-api/src/application/orchestrator/workflow/* | document_qa routing, graph node, typed state, approved-scope persistence |
| restaurant-finder-api/src/infrastructure/jev_router.py | Fourth intent and catalog-aware classification |
| restaurant-finder-api/src/deployment/sync_prompts.py | Include both new prompts in explicit synchronization |
| restaurant-finder-api/src/infrastructure/prompt_metadata.py | Include both new prompts in offline manifest validation |
| restaurant-finder-api/sample_documents/ | Synthetic sources, corpus.json, update fixture, expected answers |
| restaurant-finder-api/tests/test_document_rag_*.py | Focused parsing, ingestion, retrieval, citation, routing and graph regressions |
| restaurant-finder-infra/lib/stacks/rag-stack.ts | New RAG resources and outputs |
| restaurant-finder-infra/lib/stacks/agentcore-stack.ts | Resource props, scoped read IAM and Runtime environment |
| restaurant-finder-infra/tests/document-rag.test.ts | Synthesis assertions for new resources and runtime permissions |
| README.md and API/infra README files | Setup, architecture, operation, evidence and limitations |

Names may be adjusted for existing repository conventions; preserve these responsibility boundaries. Do not combine ingestion writes with request-time retrieval.

Add pypdf and lock it through uv for PDF parsing. Use standard-library Markdown handling for the limited corpus. Do not introduce a framework dependency solely to split six small documents.

Generated manifests, local embedding caches, deployed resource outputs, SDK responses, validation reports and live screenshots remain ignored. Commit only synthetic demo inputs and sanitized results. Bundle the small restaurant-ID/name/alias catalog for classification, with no document passages embedded in router prompts. Keep source files out of the runtime image where feasible; the deployed application reads its active corpus from S3.

## 10. Acceptance criteria

| ID | Required observable evidence |
| --- | --- |
| I1 | Dry-run performs zero AWS calls and reports the six documents and stable chunk IDs |
| I2 | Menu name/price records remain intact; PDF references use correct one-based pages |
| I3 | Empty/scanned/unsupported input fails explicitly without publication |
| I4 | Repeating active-generation ingestion creates no new vectors or embedding calls |
| I5 | Staging/embedding/vector failures leave the active pointer unchanged |
| I6 | Conflicting pointer publication fails safely without an unconditional overwrite |
| I7 | Updated Harbor menu is published as a new complete generation; unchanged passages reuse compatible embeddings |
| R1 | Queries always include active generation and resolved restaurant filters |
| R2 | Similar dish names in other restaurants cannot become the answer |
| R3 | Chunk/hash/generation mismatches never reach the answer model |
| R4 | Embedding/index/manifest dimensional mismatch yields unavailable |
| A1 | Known price/policy answers contain the expected supporting quotation and correct citation location/version |
| A2 | Unknown valet information yields insufficient_evidence, not a negative parking claim |
| A3 | Fabricated chunk IDs, altered quotes and malformed structured output yield invalid_answer |
| A4 | Retrieved instructions cannot cause tool use, ingestion writes, or an answer to an unrelated command in fixtures |
| G1 | Jev and Bedrock fallback both recognize document_qa; legacy routing cases still pass |
| G2 | Ambiguous scope asks a clarification without embedding/retrieval |
| G3 | Follow-up uses only the last approved scope; explicit new restaurant overrides it |
| G4 | No blocked or unapproved RAG text/citation is shown or saved; no graph replay |
| G5 | Temporary RAG evidence resets between turns and does not contaminate ordinary search |
| U1 | Normal Chainlit UI displays final cited text and readable disabled/unavailable/blocked outcomes |
| O1 | Local spans include retrieval/generation/validation outcomes without raw queries, passages or embeddings |
| O2 | Deployed smoke evidence is correlated with fresh RAG traces, or this criterion is explicitly reported unmet |
| D1 | New CDK resources are retained/private; runtime has scoped reads and Titan invocation, not ingestion writes |
| D2 | Prompt manifest includes both new prompts and validates before ARM64 packaging |
| D3 | Reviewed changes introduce only the new RAG stack and intended Runtime image/configuration/read-IAM changes |
| D4 | Existing API/UI regression suites and infrastructure checks pass with the new feature |
| H1 | Documentation and final handoff identify source commit, deployed image, active generation, checks and gaps |

No fixed retrieval accuracy, cost reduction, latency improvement, or universal hallucination-prevention claim is an acceptance criterion.

## 11. Execution steps

Execute these steps after the relevant approval. If the entire PRD is approved, continue within its stated boundaries without repeatedly requesting the same authorization.

### Step 1 — Reconfirm the baseline and authorization

Read applicable AGENTS.md instructions, this PRD, README checkpoints, Git status, recent commits, current dependencies, existing tests, and workflow triggers. Preserve unrelated changes.

Confirm that approval covers local implementation only or the whole local/cloud plan. This “go ahead” request produced a PRD; it is not itself approval to implement or provision resources.

Exit: baseline and approval scope are recorded.

### Step 2 — Define contracts and local corpus

Implement the domain schemas and deterministic renderer/validators first. Create the six synthetic source documents, catalog and expected-answer fixtures. Include price collision, missing fact, and update cases.

If creating or inspecting PDF artifacts, follow the available PDF skill. Confirm extraction text and page references against the actual PDF. Do not call AWS or add real restaurant data.

Exit: schemas and ground-truth corpus are reviewable.

### Step 3 — Implement extraction and chunking

Add pypdf through uv and update the lockfile. Implement the bounded extraction/chunking rules. Create offline tests for supported formats, intact price rows, Unicode/currency, locations, repeated headers, unsafe paths, duplicates and unsupported files.

Exit: deterministic chunks and a no-AWS dry-run.

### Step 4 — Implement storage and embedding adapters

Define injectable/lazy clients. Implement Titan V2 body and vector validation, S3 immutable writes/reads, conditional pointer writes and S3 Vectors operations. Use stubbed responses for error, cache compatibility, partial write and pagination tests.

Verify required operations/parameters in the installed boto3/botocore service models. If unavailable, make a narrow compatible dependency update and re-lock; do not guess API arguments.

Exit: adapters can be exercised offline without credentials.

### Step 5 — Implement generation ingestion and the CLI

Implement the full-generation staging/publication sequence. Expose:

~~~powershell
# Proposed commands after implementation, from restaurant-finder-api:
uv run python -m src.deployment.ingest_documents --corpus sample_documents/corpus.json --dry-run
uv run python -m src.deployment.ingest_documents --corpus sample_documents/corpus.json --publish --profile default --region us-east-2
~~~

Publish mode requires explicit bucket/index arguments or validated configuration. Show its planned counts and enforce the bounds before writes. An explicit --publish flag is required; never make publication the default.

Provide a separately explicit rollback-pointer operation that accepts a verified retained generation and uses the same conditional publication checks. It must not delete data.

Exit: unchanged, changed, failed and conflicting ingestion cases pass offline.

### Step 6 — Implement read-only retrieval

Read/pin active generation, resolve catalog scope, embed, filter, retrieve, verify hashes and assemble bounded context. Test wrong restaurant, old generation, missing object, invalid vector, unavailable service and cancellation paths.

Exit: only verified evidence can reach answer selection.

### Step 7 — Implement query and answer chains

Add two RAG prompt objects. Use a structured query contract only when rewriting is required, and the extractive answer contract for generation. Check the installed Haiku/LangChain structured-output integration and provide one clear error path if parsing fails.

Add both prompt objects to synchronization and offline manifest validation. Update routing instructions for document_qa.

Exit: mocked model outputs render correct answers, refuse unsupported facts and reject fabricated citations.

### Step 8 — Integrate Jev, graph, state, moderation and memory

Add the fourth intent consistently. Update routing-label validation and routing regressions. Add one dedicated document workflow node or a small set of explicit nodes; no autonomous write tools.

Reset temporary fields in run_orchestrator_turn. Preserve approved scope using the output guardrail's approved transition. Every route rejoins the existing output guardrail before memory and SSE.

Exit: graph tests satisfy G1–G5 and preserve the single-execution contract.

### Step 9 — Add local observability and UI verification

Use the existing observability manager for rag.scope, rag.retrieve, rag.answer_select and rag.validate spans. Record status, duration, passage count, query-token count where supplied by Titan, and cache/ingestion counts. Keep raw prompts/documents/embeddings out of telemetry.

Verify approved citations appear as ordinary response Markdown, with no raw-source event/attachment bypass. Use direct and nested SSE fixtures consistent with existing UI tests.

Exit: local trace fixtures and UI fixtures cover success and failure.

### Step 10 — Implement and inspect CDK

Add RagStack and exact runtime reads. Inspect existing broad S3 statements before replacing them. Add synthesis tests for resource properties, retention, scoped actions, dependencies and environment values.

Preserve deployment triggers. Existing infrastructure deployment can use CDK dependencies; initial manual rollout deploys the new RAG stack explicitly before the existing AgentCore stack. Do not modify the destroy workflow to remove retained data.

Exit: local TypeScript build and synth succeed, and templates have only intended additions/modifications.

### Step 11 — Complete local verification and review

Run focused RAG checks, then the complete existing API/UI suites with cloud clients mocked and live prompt synchronization disabled. Existing recorded totals were 47 API and 8 UI tests; report actual new totals rather than treating those numbers as a required fixed count.

Use the existing unittest convention:

~~~powershell
# From each corresponding API/UI directory:
uv run python -m unittest discover -s tests -v

# From restaurant-finder-infra:
npm run build
npx --no-install cdk synth
~~~

Run infrastructure tests using the repository's installed Jest configuration. Review Python imports in fresh subprocesses; no eager client creation or import cycle is allowed.

Review diff, dependency changes, generated files, candidate secrets and git diff --check. Ensure a stale ignored prompt manifest cannot accidentally affect offline tests.

Exit: local criteria pass, implementation is reviewable, and the cloud rollout facts are prepared. Do not advance a failed local implementation.

### Step 12 — Cloud preflight and bounded access check

Only under cloud approval, verify caller account and explicit us-east-2 region. Expected account from the prior checkpoint is 447393541969; expected caller was IAM user kangzhen. A different caller in the same intended account may be valid if the owner changed identity; report it and assess the authorization rather than assuming.

~~~powershell
aws sts get-caller-identity --profile default
aws bedrock get-foundation-model --model-identifier amazon.titan-embed-text-v2:0 --profile default --region us-east-2
~~~

Model metadata is not proof of invocation access. Make one tiny synthetic embedding invocation within the live-call budget after approval and verify 512 finite dimensions.

Read the actual stack templates, Runtime image/configuration, regional trace destination and installed SDK capabilities. Confirm required deployment/ingestion permissions. Do not change regional tracing, memory settings, account identity or unrelated IAM.

Exit: intended account/region and actual Titan invocation are established, or a precise blocker is reported.

### Step 13 — Synchronize prompts and package the image

Commit the locally validated source so the image tag identifies an actual source commit. Synchronize prompts only under cloud approval:

~~~powershell
# From restaurant-finder-api:
uv run python -m src.deployment.sync_prompts --profile default --region us-east-2
uv run python -m src.deployment.validate_prompts
~~~

Expect new versions only for changed prompt text and creation of the two RAG prompts. Preserve old versions.

Build linux/arm64 with a unique tag document-rag-<source-short-sha>-<UTC timestamp>-arm64. Verify its digest, packaged manifest and configuration. Push only this tag; do not overwrite latest in the manual rollout.

Exit: validated immutable image and prompt manifest are recorded.

### Step 14 — Prepare, inspect and deploy cloud changes

Prepare a change set for restaurantFinder-RagStack. Inspect actual resource types, retention and IAM/policy content before execution. Allowed additions are the ordinary document bucket/required bucket policy, vector bucket and index.

Deploy the RAG stack, record outputs, then prepare an exclusive change set for restaurantFinder-AgentCoreStack using the new image. Account for cross-stack references without redeploying ECR.

Allowed AgentCore changes are Runtime image/environment and the scoped RAG/Titan policy described here. Existing Lambda code, Gateway, Memory, guardrail policy, tracing settings and resource identities must remain unchanged.

Inspect enhanced property values when dynamic dependency predictions appear. Stop for any unplanned removal, replacement, public access, broad new policy, or unrelated change.

Execute approved matching changes; confirm stack UPDATE_COMPLETE/CREATE_COMPLETE as appropriate and Runtime READY with the expected image/environment.

Exit: only intended cloud changes are deployed and rollback facts are recorded.

### Step 15 — Publish and verify the sample corpus

Read the actual RAG outputs and configure the ingestion CLI. Run dry-run again, then publish the six-document initial generation. Verify the active pointer, index config, counts, source hashes and readiness.

Repeat identical publication once and demonstrate zero new embeddings/vectors. Prepare an explicit corpus variant using the checked-in price-update fixture, then dry-run it locally. Retain the initial generation.

Do not activate the update until the initial known-price question has been verified, so before/after evidence has an actual baseline.

Exit: the initial generation is active, identical publication is verified unchanged, and the update is prepared without activating it.

### Step 16 — Run bounded end-to-end checks

Use at most 12 Runtime invocations for this new verification round, including failures and SDK attempts; this is a new allowance after PRD approval, not an extension of the earlier repair run. Plan them before invoking:

1. Greeting regression.
2. Existing real-world search regression.
3. Existing dining-memory recall regression with an isolated synthetic actor. If a seed turn is necessary, it consumes the spare invocation below.
4. Harbor price question on generation 1.
5. Harbor cancellation policy.
6. Similar dish at Sakura, confirming different restaurant scope.
7. Follow-up referring to the last approved restaurant.
8. Valet parking absent from documents.
9. Ambiguous document question requiring clarification.
10. Harbor price question after generation 2 activation.
11. One document question through the normal Chainlit UI.
12. One spare invocation for a synthetic memory seed, an expired-session attempt, or a single necessary diagnostic. Record how it was used.

Complete the initial-generation checks before the update. Then publish the prepared second generation under the same bounded ingestion rules, verify compatible embedding reuse and the new active pointer, and execute the updated-price check. If an earlier failed attempt consumes the spare, stop at the cap and record any unexecuted case.

Verify Jev-unavailable fallback in a local harness with dependency injection. Do not disable Jev globally or rotate its key merely to demonstrate fallback. Use local fixtures for retrieval failure, malformed citations, prompt injection and guardrail errors.

Cap total live Titan attempts at 128, including preflight, ingestion, query embeddings and retries. Cap initial publication to two generations, 96 distinct vector records and four PutVectors attempts including retries. Readiness probes use stored vectors and are bounded by section 6. If retries/extraction increase planned usage beyond a cap, report before expanding it.

Inspect fresh CloudWatch RAG spans using correlated synthetic request times; record missing delivery honestly. No regional tracing change is authorized.

Exit: acceptance criteria have actual evidence, with any gaps stated.

### Step 17 — Record results and hand off

Update README and this PRD's execution record with actual source commit, prompt versions, image tag/digest, new resource outputs, active generation, local/live results, fresh telemetry and limitations.

Explain what is new compared with the upstream project. Include diagrams for ingestion and question answering and the extractive-answer tradeoff.

Review staged paths and secrets. Commit/push only under the owner's authorized publication scope, on feat/jev-router unless the owner explicitly chooses another branch. Never merge main, dispatch workflows or create a PR merely because implementation finished.

Clean only verified generated temporary paths; preserve user-created files, synthetic source fixtures and retained cloud data. Use checked absolute targets and native PowerShell operations for Windows cleanup.

Final report links the implementation/checkpoint and states local versus deployed completion, actual test results, active corpus version, remaining gaps, and rollback procedure.

## 12. Failure handling and rollback

| Condition | Required response |
| --- | --- |
| Unsupported/empty source | Reject it; no partial active publication |
| Embedding/config mismatch | Fail before vector write or answer generation |
| Partial staging/readiness failure | Retain old pointer; report staged generation as inactive |
| Concurrent pointer conflict | Stop publication and re-read; no blind overwrite |
| No relevant answer evidence | Return insufficient_evidence |
| Wrong restaurant/hash/source generation | Return unavailable/invalid evidence; no model answer from it |
| Structured output or quote validation failure | Safe invalid_answer result; no automatic graph/model replay |
| Enabled guardrail unavailable | Existing fail-closed SSE path |
| Unplanned cloud change | Stop execution and reconcile scope with the owner |
| Missing fresh traces | Preserve application evidence; report O2 unmet and diagnose read-only |

Runtime rollback: redeploy the recorded previous image with RAG disabled/old environment through a reviewed AgentCore change set. Retain the new RAG stack. Rolling back the image does not remove new prompts, documents, vectors or charges already incurred.

Corpus rollback: validate the retained previous generation, then conditionally publish its pointer using the current ETag. No original/vector deletion is required. In-flight requests retain their pinned generation.

Do not change embedding dimensions/model in place. A future index migration requires a separately reviewed index/generation and a new plan.

## 13. Authorization and open questions

**Current authorization:** The owner approved the entire PRD with “proceed” on 2026-10-08. This covers the stated local work and bounded AWS/Git publication. Material deviations still require approval.

**Approval of the entire PRD:** Authorizes the stated local work and bounded cloud rollout/verification, including the precise new RAG resources, scoped IAM changes and publication operations. Approval limited to local work leaves the cloud steps pending. Existing credentials/settings remain confidential.

Before external work, the implementing agent must show the concrete planned resources, limits and rollback facts. If the entire plan is already approved and the actual change set matches, continue without another generic permission request. Seek approval only for a material deviation or an explicitly narrower initial authorization.

Owner decisions proposed for sign-off:

1. Custom Python/Titan/S3 Vectors approach.
2. Three fictional restaurants and six controlled English documents.
3. Extractive cited answers in v1.
4. Local implementation only versus the bounded AWS phase too.

Safely discoverable technical questions:

- Does the current identity have Titan invocation and new-stack/ingestion permissions?
- Does the installed SDK expose required vector/filter/conditional-write fields?
- Does the actual PDF extraction preserve each fixture's menu records and locations?
- Can filtered retrieval return the expected passages with the installed index/API behavior?
- Are fresh RAG traces delivered in the existing regional configuration?

Resolve these through scoped inspection and checks. They do not require an interview unless they force a change in resources, cost boundaries, source formats, or the agreed deliverable.

## 14. Primary references consulted during planning

- [Titan Text Embeddings models](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html): embedding model and supported vector dimensions.
- [Titan embedding request/response](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-embed-text.html): normalization, dimensions and actual input token count.
- [S3 Vectors queries](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-query.html): query embeddings, filters, metadata, distances and query pagination.
- [S3 Vectors metadata filtering](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-metadata-filtering.html): filter construction and metadata roles.
- [S3 Vectors access management](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-access-management.html): index-scoped actions and GetVectors requirement.
- [S3 Vectors regional availability](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-regions-quotas.html): us-east-2 availability, not proof of account permission.
- [S3 Vectors limitations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-limitations.html): service payload/metadata limits.
- [S3 conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html): safe pointer publication and conflict behavior.
- [CloudFormation S3 Vectors index](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-s3vectors-index.html): resource properties and replacement behavior.
- [pypdf text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html): text extraction and lack of image OCR.

Implementation must use the installed SDK/CDK capabilities and recheck primary documentation for uncertain behavior. Service availability and inspected source are planning evidence; no AWS operation or test has been performed by drafting this document.

## 15. Execution record

Implementation in progress (2026-10-08).

- Baseline: feat/jev-router at 7ba4643c3b1b200074372e2c01f325104b099dac; only this PRD was untracked before implementation.
- AWS identity freshly verified: account 447393541969, IAM user kangzhen, explicit us-east-2.
- Rollback baseline captured locally under ignored .generated/rag: Runtime READY version 9; image correctness-f9dcf56-20261007135110-arm64; AgentCore stack UPDATE_COMPLETE. Existing image digest from the previous checkpoint remains subject to ECR verification before rollback.
- Local source corpus: six active documents, 14 deterministic chunks, 2,488 extracted chunk characters in the first dry-run. PDF v1/v2 visually inspected at page 1; expected prices RM28/RM32.
- pypdf locked through uv at 6.19.0. Installed QueryVectors service model has no nextToken parameter; pagination support is detected, not assumed.
- Final local API regression run before packaging: 94 tests passed; UI: 10 passed; TypeScript build and three CDK tests passed. CDK synth succeeded. Diff whitespace check passed. Scanned tracked/untracked publishable text for AWS/GitHub key patterns/private keys: no matching files.
- Current deterministic initial generation: a68dcd7921d2f96d67de441961f55c972ad5af8072eb26f5841f8d7588ef3ab3. The extractor fingerprint now includes the locked pypdf version.
- Local synthesized AgentCore template compared with deployed baseline: no added/removed logical resources. Only RuntimeRole Policies and Runtime EnvironmentVariables changed (same prior image). Expected new-image artifact change will be reviewed in the rollout change set. New stack has private/versioned/TLS corpus storage and retained vector bucket/index.
- Steps 1-11 complete locally. Step 12 tiny Titan invocation passed: one attempt, 512 dimensions, 9 input tokens. No provisioning, corpus publication or new image publication yet.
