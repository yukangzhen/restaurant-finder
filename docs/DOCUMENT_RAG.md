# Document RAG engineering guide

## What this adds

The upstream agent used web/browser tools and conversational memory. This fork adds a separate, controlled document retrieval path. Jev classifies `document_qa` alongside the three existing intents; Haiku remains the routing fallback. Menus and policies live in S3, their Titan V2 embeddings in S3 Vectors. Conversation memory remains separate from the document corpus.

The sample venues are fictional: Harbor Pasta Lab, Sakura Table Lab, and Spice Garden Lab. Six English documents include a text-based PDF. They are engineering fixtures, not real restaurant recommendations.

## Ingestion

```mermaid
flowchart LR
  Catalog[Corpus catalog and source bytes] --> Parse[Bounded PDF/Markdown extraction]
  Parse --> Chunk[Whole records with stable hashes]
  Chunk --> Plan[Offline generation plan]
  Plan --> Cache[Compatible embedding cache]
  Cache --> Titan[Titan V2: 512 normalized floats]
  Titan --> Stage[Stage complete S3 generation and vectors]
  Stage --> Verify[Verify chunks, vectors and filtered query readiness]
  Verify --> Pointer[Conditional active pointer publication]
```

Run from `restaurant-finder-api` after `uv sync --extra local-aws`:

```powershell
uv run python -m src.deployment.ingest_documents --dry-run --corpus sample_documents/corpus.json
uv run python -m src.deployment.ingest_documents --publish --corpus sample_documents/corpus.json --profile default --region us-east-2 --bucket <DocumentBucketName> --index-arn <VectorIndexArn> --max-embedding-attempts 48 --report .generated/rag/initial.json
```

Dry-run constructs no AWS client. Publish is explicit and verifies identity/account/region. A repeated complete active generation creates zero embeddings and writes zero vectors. Cache compatibility covers canonical text, model, dimensions and normalization. Source/version/config changes create a new generation; unchanged text can reuse cached embeddings.

Each document is limited to 5 MiB, 10 PDF pages, and 100,000 extracted characters. A generation has at most six documents and 48 chunks. Records cannot exceed 1,800 characters; overlap retains a complete preceding record of at most 200 characters within the same page or section. Empty/image-only PDFs, unsupported inputs, unsafe paths and oversize records fail explicitly. OCR and complex table reconstruction are outside v1.

All source/chunk/manifest/cache writes are conditional and preserve existing content. The versioned active pointer is published last with the observed ETag (`IfMatch`), or `IfNoneMatch` for first publication. A conflict leaves the staged generation inactive. This provides safe publication across services, not an atomic cross-service transaction. Retained generations support in-flight requests and rollback; nothing is automatically deleted.

Use `sample_documents/corpus-v2.json` for the controlled RM28-to-RM32 Harbor price update. Verify the first price before publishing v2. This fixture changes the complete generation while reusing unchanged text embeddings.

## Single-restaurant question answering

The [document evaluation guide](CI_AND_RAG_EVALUATION.md) describes 17 source-grounded cases, deterministic answer/provenance checks and the credential-free CI workflow. Offline regression reports identify simulated dependencies; they do not claim live model or vector-ranking accuracy.

```mermaid
flowchart TD
  User[Current user question] --> Router[Jev or Haiku routing fallback]
  Router --> Scope[document_qa: pin active generation and resolve one restaurant]
  Scope --> Clarify[Ask clarification if scope is missing/ambiguous]
  Scope --> Rewrite[Optional single follow-up rewrite]
  Rewrite --> Embed[One Titan query embedding]
  Embed --> Retrieve[Query filtered by generation, restaurant and optional document type]
  Retrieve --> Validate[Verify chunk ID, metadata, text hash and source location]
  Validate --> Select[Haiku selects at most three exact quotes]
  Select --> Render[Validate selections and render trusted citations]
  Clarify --> Moderate[Existing output guardrail]
  Render --> Moderate
  Moderate --> Memory[Save approved complete answer]
  Memory --> UI[One complete SSE chunk shown in Chainlit]
```

Examples:

- “According to Harbor Pasta Lab's menu, how much is mushroom pasta?” -> supporting RM28/RM32 quote with page 1, document ID and version.
- “What does Sakura Table Lab's menu say mushroom pasta costs?” -> RM36 from Sakura, regardless of Harbor's similar dish name.
- “And what about its cancellation fee?” -> previous approved document scope, one query rewrite, policy retrieval.
- “According to Harbor's documents, does it offer valet parking?” -> insufficient evidence. Missing policy is not a negative parking claim.
- “What does the uploaded menu say mushroom pasta costs?” -> restaurant clarification, no embedding/vector query.
- “According to Harbor Pasta Lab's policy, what is the cancellation fee?” -> policy-only retrieval; `Pasta` in the restaurant name does not imply a menu request.
- “According to Harbor Pasta Lab's menu and policy, what is the mushroom pasta price and cancellation fee?” -> menu and policy retrieval with separate trusted quotations/citations.

## Comparing document menu prices

The document node also accepts a bounded two-restaurant comparison. Name one exact menu item and two different fictional catalog restaurants:

- `Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources.`
- `What is the price difference for mushroom pasta between Harbor and Sakura?`
- `Which is cheaper for mushroom pasta: Harbor or Sakura?`

Registered short aliases, case differences, ordinary whitespace, optional leading `the` and final punctuation are supported. Other phrasing asks for clarification. Non-price comparisons, three restaurants, multiple dishes/criteria and unknown operands are outside this version. The Jev/Haiku router is unchanged; live classification of these examples has not been measured by the offline checks.

The workflow pins the active generation once, then dispatches two isolated LangGraph workers. Each uses a server-selected restaurant/menu filter, one embedding/query and at most one structured quote-selection call. The private graph has no checkpointer; only its final answer/citations enter the parent workflow. Both branches settle before deterministic aggregation, so completion order cannot reorder the restaurants or source labels.

Exact menu records must identify the requested item, match verified chunks and retain adjacent qualifiers. The application parses fixed RM/MYR listed prices with an explicit `per serving`, `per bowl` or `per piece` unit using `Decimal`. It calculates a difference only for two supported records with matching currency and units. Ranges, discounts, unsupported currencies/units and ambiguous boundaries produce no calculation. This compares listed document prices and makes no claim about current availability, restaurant quality or equal portion sizes.

With the local v2 fixtures, Harbor's mushroom pasta is RM32 per serving and Sakura's is RM36 per serving, yielding RM4. The response includes full quotes and two original-document links: Harbor's PDF and Sakura's Markdown. It does not infer which generation is currently deployed.

| Evidence situation | User-visible result |
| --- | --- |
| Two supported, comparable prices | Two cited rows and an application-calculated difference or tie. |
| Two supported records with incompatible units/formats | Both sources; explanation that arithmetic is unavailable. |
| One supported, one missing | One-source partial result; no difference/winner. Missing retrieval evidence does not prove the dish is unavailable. |
| One supported, one provider failure | One-source partial result explicitly identifying retrieval unavailability. |
| Neither supported | Insufficient evidence, or unavailable when a provider failed. |
| Forged/changed/out-of-scope/conflicting evidence | Whole comparison rejected; no citation attachments or calculation. |

The complete answer goes through the existing output guardrail. Blocked or changed/anonymized answers lose original citation attachments. Approved comparisons clear the single-restaurant follow-up scope: `What about its cancellation policy?` asks which restaurant. A later explicit single-restaurant request establishes its normal scope again. The approved final turn is saved once.

Per comparison: two workers, two embedding/vector-query operations, one vector page per worker, at most ten chunk reads, at most 18,000 passage characters, two selector calls and two quotes/citations. Each selector allows 1,600 output tokens. SDK retries and repair loops are disabled for this path. Workers have a maximum 45-second deadline and reserve two seconds within the existing maximum 60-second document timeout for aggregation. Cancellation prevents starting subsequent operations; an already-running synchronous SDK call can still finish within its configured timeout. These limits exclude parent routing, guardrails and memory operations and are not a latency/cost benchmark.

Implementation and acceptance details are in the [comparison handoff PRD](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/docs/HANDOFF_PRD_DOCUMENT_COMPARISON.md). Offline evaluation uses simulated providers; AWS deployment and live model/ranking checks remain separate.

## Retrieval scope and historical single-restaurant validation

The following rollout record covers the earlier single-restaurant feature. The new comparison workflow has only offline validation in this phase.

Document-type inference ignores matched catalog-name/alias spans while retaining the full canonical question for embedding and answer selection. Menu-only intent selects `menu`, policy-only intent selects `policy`, and mixed/neutral intent has no type restriction. Existing restaurant clarification, approved follow-up scope and explicit restaurant override remain covered by regression tests. The [query-scoping PRD](HANDOFF_PRD_RAG_QUERY_SCOPE.md) records the code improvement and offline verification. Its selected source `ef146a295fe8edd0c5a9fa50ff5c9eccf70de35e` was deployed on 2026-10-09 as READY Runtime/DEFAULT version 12 through an image-only update; see the [live rollout record](HANDOFF_PRD_RUNTIME_ROLLOUT_AND_LIVE_VALIDATION.md).

The six live scenarios returned the expected menu, policy, mixed, conversational follow-up, insufficient-evidence and clarification behavior. Jev routed every request to `document_qa`; five query embeddings/vector queries, five selections and one follow-up rewrite were observed. Clarification performed no embedding/vector query/selection. Explicit menu and policy citation clicks opened the intended originals; their downloads matched the pinned hashes. A browser download delay prevented the planned immediate follow-up timing, although the same conversation retained Harbor scope. These controlled checks do not establish universal retrieval accuracy, performance or production suitability.

Only server code creates filters and resolves manifest keys. The model selects supplied IDs and exact contiguous quotes; it cannot supply source URLs, restaurant filters or S3 paths. At most five complete passages / 9,000 characters reach each answer selector. Distances are retrieval ordering, not calibrated confidence. Invalid citations, changed quotes, malformed structured answers and instruction-like selections produce a safe failure. No automatic model/graph replay occurs.

Extractive answers intentionally sacrifice conversational paraphrasing for inspectable evidence. Exact matching validates quotation provenance, not universal factual correctness or semantic relevance. Source quality and the answer selector still matter. Retrieved text is treated as untrusted data; the document model has no executable browser, memory or ingestion tools. The normal guardrail can anonymize or block the final cited answer before UI delivery and memory storage.

## Inspecting the original source

New unchanged, approved document answers include optional structured citation references in the same complete SSE chunk. The API resolves them from the selected evidence and pinned manifest; the model still supplies only chunk IDs and exact quotes. Blocked, modified/anonymized, invalid and wholly unsupported answers carry no clickable references. A partial comparison attaches only its supported restaurant's source. Pending and approved references reset on every turn.

The local Chainlit server fetches each distinct original once from `rag/generations/<generation>/sources/<document-id>.<pdf-or-md>`, verifies its SHA-256 and 5 MiB size bound, then attaches a clickable `Source 1` through `Source 4` element. Single answers remain limited to three references and comparisons to two; only validated multi-part answers may publish four. PDFs open at their cited page. Markdown opens as complete literal text with original line numbers and the cited section/range. Original downloads contain the unmodified verified bytes. The loader uses bounded I/O, a 30-second preparation timeout and no SDK or agent retries. Failure preserves the approved answer and plain citation with a source-unavailable notice.

Configure `DOCUMENT_SOURCE_VIEWER_ENABLED=true` and `RAG_DOCUMENT_BUCKET=<DocumentBucketName>` in the UI environment. Its AWS profile needs read access to original objects in the existing private bucket; Runtime's RAG permissions still exclude originals. Source loading makes no extra model or embedding calls. No presigned/public S3 URLs or browser AWS keys are used.

The UI pins Chainlit 2.12.0 for its bundled PDF.js renderer; the earlier iframe viewer displayed a blank PDF in the in-app browser. Chainlit can initially open all new side elements together; clicking a named source selects that element alone. The UI decorates labels as `Source 1 (answer 2)` to make source names distinct across answers. Quotations and document provenance remain unchanged; the API/memory retain the original approved citation text. The UI regression suite covers the distinct labels, and explicit PDF and Markdown clicks were inspected on the final UI.

References pin the full generation and hash, so an older citation cannot silently open the latest source after a corpus update. Existing answers without metadata retain plain citations. Native elements belong to the current Chainlit session; permanent links after a restart/history restore are not provided.

Opening a source discloses the complete controlled fictional document, beyond the quotation checked by the answer guardrail. Markdown is displayed as literal data, with no document HTML/scripts/remote links executed. Keep this anonymous demonstration on loopback. Private documents or public visitors require a separate authentication/authorization design. See the [clickable-citation PRD](HANDOFF_PRD_CLICKABLE_RAG_SOURCES.md) for rollout evidence and criteria.

## Bounded multi-part document questions — local implementation

The multi-part path combines one menu item's listed price with cancellation policies for one or two explicitly named fictional catalog restaurants. It requires both `DOCUMENT_RAG_ENABLED` and `DOCUMENT_MULTIPART_ENABLED`; the second flag defaults to false. Real `.env` files and the deployed Runtime were not changed during local implementation.

Supported forms (names may use registered aliases; ordinary case, whitespace, possessive apostrophe and terminal punctuation variations are accepted):

1. `Compare mushroom pasta prices at Harbor and Sakura, and explain both restaurants' cancellation policies.`
2. `For Harbor and Sakura, compare mushroom pasta prices and their cancellation policies.`
3. `For Harbor, what is the mushroom pasta price and cancellation policy?`
4. `What is the mushroom pasta price at Harbor, and what is its cancellation policy?`
5. `Compare mushroom pasta prices at Harbor and Sakura, and explain Harbor's cancellation policy.`

One optional `Show the sources.` sentence is accepted. These are bounded forms, not unrestricted natural-language planning. Unknown/third venues, multiple dishes, extra requirements and oversized inputs clarify without new provider operations. Two historical shapes keep their existing behavior: `According to ... menu and policy ...` uses the single-question workflow, while `Compare ... prices and cancellation policy at ...` keeps the comparison workflow's clarification. This compatibility distinction preserves the original curated regressions.

```mermaid
flowchart LR
  Admit[Pure full-request admission] --> Pin[One immutable generation]
  Pin --> Planner[One structured Haiku plan]
  Planner --> Check[Exact task-set validation]
  Check --> Workers[2-4 tasks; concurrency 2]
  Workers --> Verify[Scoped retrieval and whole-record validation]
  Verify --> Assemble[Deterministic answer and price arithmetic]
  Assemble --> Approval[Parent output guardrail once]
  Approval --> Sources[Approved original-document references]
```

The compiler defines the expected work independently of the planner. Draft tasks must match the exact restaurant/criterion/item set: omissions, extra tasks, duplicate tasks, changed dishes, or additional schema fields fail before retrieval. Server code assigns task IDs, scope filters and retrieval queries. Jev remains the intent router. The planner cannot create tools, URLs or source keys. A deterministic planner could also handle this grammar; the additional model call demonstrates a checked planning stage, without a claimed efficiency gain.

Each task has its own retrieval session and model operation. The whole workflow pins one manifest; workers never pin again. Every task has at most one embedding, one vector query page, five hits, and one selector. At most four tasks run, with two active. Retrieval context is bounded to 9,000 characters per task and 36,000 total. Planner output is limited to 1,000 tokens; selectors retain the existing 1,600-token limit. SDK total attempts are one. No replan, repair, web fallback, or free-form synthesis model is used.

The parent document-node timeout remains at most 60 seconds. Planning has at most five seconds, and workers share at most 45 seconds with assembly time reserved. Up to 250 ms of that reserve allows the graph to account for queued results after workers stop provider operations. In-flight synchronous SDK calls cannot be instantly cancelled; stop flags prevent subsequent operations, SDK timeouts bound I/O, and operation-owned clients close in their owning thread when the call exits.

Menu tasks reuse the existing complete-record and `Decimal` price validators, including allergens and dinner-only qualifiers. Cancellation tasks support only a complete Markdown `Reservations and cancellation` section represented by one chunk, with its entire body at most 600 characters. Stripping the known heading is permitted; dropping a sentence/condition is rejected. Split/long/unrecognized layouts are explicitly unsupported, and conflicting complete policies invalidate the entire factual answer. Canonical chunks do not retain arbitrary paragraph boundaries, so this feature does not reconstruct general document paragraphs.

Source order follows restaurant first appearance, with price before policy for each restaurant; completion timing does not affect labels. An answered four-part request has four citations. If Spice's mushroom-pasta price lacks evidence while Harbor's price and both policies are supported, the answer says `Answered 3 of 4 requested parts`, retains three sources, and omits the price difference. If a policy alone fails but both menu prices are supported, the partial answer can still calculate the menu-price difference. No policy fee is compared to a dish price.

Any provenance/selection conflict rejects all public facts and citations. Operational failures can retain supported parts; every required task has an explicit result. Only unchanged approved final text releases citations and safe coverage metadata. Masked/blocked answers release neither. The parent saves approved final memory once; workers do not save memory or emit public tokens. Approved multi-part turns clear the single-restaurant follow-up scope, including one-venue compounds: name the restaurant again for a later pronoun question.

The viewer still checks sequential source markers, one generation, derived immutable keys and original SHA256 hashes. Four originals are bounded to 20 MiB in total, with the existing 30-second preparation deadline. A late source error retains earlier verified viewers and shows a source notice without repeating the agent request.

Adding `RAG_MULTIPART_PLAN_PROMPT` increases the current registry to nine prompts. Both synchronization and read-only manifest validation include it. Packaging this code against an old eight-prompt manifest will fail; even a feature-disabled image needs an approved updated manifest. Historical rollout sections elsewhere in this guide refer to their original eight-prompt releases. No prompt sync, image publication or Runtime deployment was performed for this local feature.

See the [approved multi-part PRD](HANDOFF_PRD_MULTIPART_DOCUMENT_WORKFLOW.md) for acceptance evidence and the [evaluation guide](CI_AND_RAG_EVALUATION.md) for the separate 40-case offline regression.

## Configuration and infrastructure

`DOCUMENT_RAG_ENABLED=false` locally avoids RAG client initialization. For enabled mode set `RAG_DOCUMENT_BUCKET` and `RAG_VECTOR_INDEX_ARN` from `restaurantFinder-RagStack`. Titan V2, 512 dimensions, cosine index distance and normalized float vectors are fixed in v1. Model/dimension changes require a new reviewed index/generation.

The new stack creates a private, versioned, TLS-only ordinary S3 bucket and an S3 vector bucket/index. All are retained on deletion/replacement and use S3-managed encryption. AgentCore depends on this stack and receives exact read permissions for the active pointer, generation manifests/chunks and vector index, plus Titan invocation. Runtime cannot publish/delete corpus data or read embedding caches/original PDFs. Existing unrelated permissions remain unchanged.

The owner's ingestion identity needs `s3:GetObject` and `s3:PutObject` on `rag/*` in the new bucket; `s3vectors:GetIndex`, `GetVectors`, `PutVectors`, `QueryVectors` on the new index; `bedrock:InvokeModel` on `arn:aws:bedrock:us-east-2::foundation-model/amazon.titan-embed-text-v2:0`; and `sts:GetCallerIdentity`. No automatic broad grants or new credentials are created.

Initial rollout: review and deploy RagStack, synchronize/validate all eight prompts, publish a unique ARM64 image, then review and execute the AgentCore-only change set. Supply a specific image URI to CDK. Preserve the existing ECR stack and Lambda/Gateway/Memory/guardrails/tracing configuration. Feature-branch pushes do not trigger the workflows restricted to `main`.

## Rollback and diagnosis

Corpus rollback is explicit and read-validates the retained manifest, chunks, vector set and query readiness before conditional pointer publication:

```powershell
uv run python -m src.deployment.ingest_documents --publish --rollback-generation <previous-generation-hash> --profile default --region us-east-2 --bucket <DocumentBucketName> --index-arn <VectorIndexArn> --report .generated/rag/rollback.json
```

Choose the Runtime rollback boundary for the current rollout. For the query-scoping Runtime-12 release, revert only the image to the captured Runtime-11 citation image, preserving the current RAG environment, role, sources and corpus pointer. Prepare the rollback from a fresh current template and inspect a change set containing only one Runtime image Modify with no replacement. The fresh snapshot is under `.generated/rollout-query-scope-20261009/runtime-rollback.template.json`; verify the baseline digest remains available before use. See the [rollout PRD](HANDOFF_PRD_RUNTIME_ROLLOUT_AND_LIVE_VALIDATION.md) for the reviewed procedure. Rollback does not reverse charges or remove prompt versions.

The earlier initial-RAG rollout saved `.generated/rag/runtime-rollback.template.json`. That historical snapshot restores its pre-RAG image/environment with RAG disabled; it is not the rollback template for Runtime 12. Keep it as phase-specific evidence and use it only for a separately reviewed pre-RAG rollback. No Runtime rollback was performed during either verification phase.

The historical pre-RAG image is `correctness-f9dcf56-20261007135110-arm64`, verified during that phase with digest `sha256:0614966b8424edbeba937ca6f4014d492ccc624d347ecc2ec4f14c35fbcc23c2`. The retained initial corpus generation is `a68dcd7921d2f96d67de441961f55c972ad5af8072eb26f5841f8d7588ef3ab3`. Runtime 12's freshly verified rollback image is `citations-00a846a-20261008052831-arm64`, digest `sha256:7704ff7ce9e906e6508d2128a16b5479b6fb27608e0d05b38bf143c444700761`. Its current active corpus remains generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a`.

Safe RAG spans cover scope, embeddings, retrieval, answer selection and validation. They record generation, restaurant IDs, counts/token usage and safe error types; raw queries, passages, embeddings and provider exception payloads are excluded. Enabled but unconfigured/unpublished retrieval returns unavailable. Failure never silently falls back to web search or dining memory.

Offline checks (use an absent manifest path until deployment prompt synchronization):

```powershell
$env:PROMPT_SYNC_MODE='false'
$env:PROMPT_MANIFEST_PATH=(Join-Path (Get-Location) '.generated/offline-no-manifest.json')
$env:REQUIRE_PROMPT_MANIFEST='false'
.venv/Scripts/python.exe -m unittest discover -s tests -q
```

Run UI tests from `restaurant-finder-ui`; run `npm run build`, `npm test -- --runInBand`, and CDK synth from `restaurant-finder-infra`. Deployment/live evidence and unmet acceptance criteria are recorded in `HANDOFF_PRD_DOCUMENT_RAG.md`.
