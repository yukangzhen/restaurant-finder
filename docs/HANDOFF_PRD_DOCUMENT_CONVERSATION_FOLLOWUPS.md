# Handoff PRD for document conversation follow ups

**Status:** Phase A implementation and offline acceptance complete. AC01-AC14 passed locally; final protected-file and cleanup verification is recorded in the private closeout receipt. Publication and rollout remain separate decisions.

**Prepared:** 2026-10-14, Asia/Kuala_Lumpur.

**Audience:** The project owner and the engineer implementing the next AI engineering portfolio feature.

**Repository:** `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.

**Inspected branch and HEAD:** `feat/document-multipart-rollout`, `574cc6304b1be4060cb8d281657c84303e6eb357`.

## 1 Outcome and reason

Make the document workflow understand a bounded set of follow up questions across single, comparison and multipart answers. The user should be able to say “And what about its cancellation fee?” after discussing one restaurant, or “Which is cheaper?” after comparing one dish at two restaurants. When a reference could mean either restaurant, the assistant must ask which one and accept a restaurant name as the next reply.

Deliver reviewed local source changes, an independent conversation regression dataset, reproducible offline reports, and updated engineering documentation. The feature demonstrates explicit conversation state, reference resolution, workflow dispatch, evidence validation and moderation before context is committed. It supports the owner's technical portfolio demonstration; the project remains a controlled demo using fictional documents.

Phase A ends with a concrete local diff and inspected offline evidence. Publication, a Runtime rollout, billable validation and the demo walkthrough are separate decisions.

## 2 Verified starting point

### Existing functionality

- Jev classifies ordinary requests, with Bedrock as the provider failure fallback.
- The single document workflow already resolves some follow ups using `rag_approved_scope` and can perform a model query rewrite.
- Price comparison and multipart workflows have bounded admission, pinned retrieval, exact quotation validation, deterministic arithmetic and inspectable original citations.
- `output_guardrail_node` deliberately clears `rag_approved_scope` for every approved comparison or multipart response. Multipart outcomes also reject a single restaurant scope. This is an intentional existing contract, not an accidental deployment failure.
- `run_orchestrator_turn` resets transient fields and restores conversation state through the LangGraph checkpointer. The worker subgraphs do not checkpoint their private manifests, plans or evidence.
- Input moderation precedes graph execution. Output moderation precedes public delivery and parent memory persistence. Modified or blocked document answers release no citations.

Relevant inspected sources: `src/application/document_rag/{workflow,retrieval,comparison_workflow,multipart_workflow}.py`, `src/application/orchestrator/{streaming,identity}.py`, `src/application/orchestrator/workflow/{state,nodes,graph}.py`, `src/infrastructure/{streaming,jev_router}.py`, and the existing document tests. Paths beginning with `src` here are under `restaurant-finder-api`.

### Accepted deployment record

The final receipt at `restaurant-finder-api/.generated/guardrail-rollout-20261014005846/final-verification.json`, inspected while preparing this PRD, records Runtime/DEFAULT 16, multipart enabled, pinned guardrail `ih5xpt3qi946:1`, six accepted live requests, zero remaining sends and no rollback. Its timestamp is `2026-10-14T03:00:38.274522+00:00`. This is the last accepted receipt, not a new AWS status check.

The six-case record includes a deliberate clarification for the follow up after a Harbor-only multipart answer. That accepted historical result remains valid for the existing implementation. Enabling this feature will introduce a new contract and new acceptance cases.

The deployed image contains release `3771a4ca4fa661da384e2e8f1ba92e7eb7008ab9`; HEAD `574cc6304b1be4060cb8d281657c84303e6eb357` adds documentation only. Existing draft [PR 1](https://github.com/yukangzhen/restaurant-finder/pull/1) remains open against `feat/jev-router`.

### Documentation correction

The README opening and the multipart rollout paragraph in `docs/CI_AND_RAG_EVALUATION.md` still describe the failed first trial and retained Runtime 15 as the current state. Phase A must keep that trial as history and add the successful pinned guardrail retry, Runtime 16 and the six-case acceptance result with a link to section 14 of `HANDOFF_PRD_PINNED_GUARDRAIL_AND_MULTIPART_RETRY.md`. Do not overwrite historical PRDs or imply that the new follow up feature is deployed.

## 3 Scope and constraints

### In scope for Phase A after sign off

1. Correct the two stale current-status summaries.
2. Add strict private conversation contracts and a pure deterministic resolver.
3. Retain context from unchanged, approved, validated document answers.
4. Resolve the explicitly supported forms in section 5; resume one approved clarification on the immediately following user turn.
5. Run the existing retrieval and validation paths for every resolved answer, with fresh evidence.
6. Add a default-off feature flag, paired API documentation and narrowly scoped CDK serialization.
7. Add focused tests and a separate 24-conversation offline evaluator; extend the existing CI API job to run it.
8. Record local evidence and a reviewable diff.

### Preserve

Preserve dependency versions and lock files, real `.env` files, the nine immutable prompts and their manifests, original documents, the active corpus, guardrail behavior and binding, AWS identities/IAM, existing search tools, and the accepted deployment. Leave the running UI and its retained staging directory intact.

Preserve the owner-created untracked `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`. Its preparation-time SHA-256 is `c3f491550280ba5568cea656d1e90378a76547ee5520e462a323469949aebf9f`. Recheck and report drift; never reset or stage it under this feature.

### Outside this feature

Do not add general free-form conversation planning, a resolver model, answer caching, reranking, hybrid search, uploaded-document administration, restaurant recommendations based on fictional records, policy-only comparison across two restaurants, references such as “the cheaper one,” or automatic replay of failed requests. A new dish, new criterion, “those other restaurants,” or a non-catalog venue requires an explicit supported question.

Do not edit the original 17/20/40 evaluation datasets to make existing expectations pass. Do not merge the PR, push upstream, run Docker, deploy CDK, create prompt versions, mutate the corpus, perform AWS reads or inference, run a benchmark, or begin the demo under Phase A.

## 4 Observable definition of done

| ID | Required local result | Evidence |
| --- | --- | --- |
| AC01 | Default flag off preserves all existing dispatch, scope, moderation, memory and citation behavior. | Existing suites and unchanged 17/20/40 datasets and complete reports. |
| AC02 | Approved Harbor-only multipart context resolves the supported singular policy follow up to Harbor. | Executed parent graph conversation, exact policy quote and original citation. |
| AC03 | Approved two-restaurant price context resolves “Which is cheaper?” and “What is the price difference?” to the same pair and item. | Executed comparison path; correct qualifiers, arithmetic and fresh citations. |
| AC04 | Singular reference after two restaurants asks which one with no retrieval/model work; an immediate exact alias reply resumes only that approved request. | Three-turn graph case and measured operation counters. |
| AC05 | Resolution uses only validated server context. Unknown venues, additional instructions, multiple reply aliases and malformed context cannot inherit a restaurant or silently discard a criterion. | Negative cases and resolver/unit tests. |
| AC06 | Context and clarification candidates become usable only after unchanged output approval and payload validation. Masks, blocks and failed outcomes do not install candidates. | Approval tests, producer message identity checks and checkpoint observations. |
| AC07 | New chats and actor/thread mismatches cannot reuse the new context; old checkpoints without the new fields remain usable. | Independent conversations and migration tests. |
| AC08 | Every resolved answer uses the current pinned corpus generation; previous prices or quotations never serve as evidence. | v1-to-v2 fixture transition and mid-request pointer-change tests. |
| AC09 | Original user messages are preserved in graph history and parent memory; one final moderation and at most one parent memory save occur for each turn. | Executed graph/SSE tests and call captures. |
| AC10 | Citation controls remain associated with their own answer after later follow ups. | UI regression using existing PDF/Markdown originals and source identities. |
| AC11 | All 24 new conversations run with injected dependencies and independent gold; omitted or forged observations cannot pass. | Fresh JSON/Markdown report and evaluator mutation tests. |
| AC12 | API/CDK flag defaults and opt-in serialization are tested; toggling the flag changes only that Runtime environment leaf. | Dummy-account no-lookup synth and infrastructure tests. |
| AC13 | CI adds only the new offline command, safe summary and two report artifacts. | Inspected workflow diff; local report schema and shell review. |
| AC14 | Current-status docs are corrected, protected files match, actual counts are recorded, and the closeout distinguishes local completion from deployment. | Diff, hashes, local execution record and criterion table. |

No live result, CI run or performance gain is required or claimed for local completion. A later approved rollout must establish live acceptance independently.

## 5 Supported conversations and admission rules

### 5.1 Normalization

Normalize Unicode and whitespace with `canonical_text`. Allow case differences, straight/curly apostrophes, an optional leading “And,” and one trailing question mark or full stop. Accept at most 1,000 characters and reject control characters. Match the entire remaining question, not a substring.

Resolve names against validated catalog IDs and exact aliases, longest aliases first. Resolve possessive suffixes explicitly; do not treat arbitrary text near “at,” “for” or “about” as a catalog identity. The current IDs are `demo-harbor-pasta`, `demo-sakura-table` and `demo-spice-garden`.

Do not inspect prior answer prose, tool results, stored dining preferences or quoted documents to infer context. The resolver receives only the current moderated question, validated private context, validated pending clarification, request identity and the static catalog. It performs no network, embedding, model, memory or source read.

### 5.2 Exact first-version forms

| Form after normalization | Required approved context | Resolution |
| --- | --- | --- |
| `What about its cancellation fee?` / `What is its cancellation fee?` | Exactly one restaurant. | A fresh policy-only question for that restaurant. |
| `What about its cancellation policy?` / `What is its cancellation policy?` | Exactly one restaurant. | A fresh complete cancellation-policy question. |
| `What about <exact alias>'s cancellation fee?` / `What about <exact alias>'s cancellation policy?` | No inherited venue is needed. | The explicit known venue overrides the prior venue. Unknown alias clarifies. |
| `Which is cheaper?` / `What is the price difference?` | Exactly two restaurants and one admitted item from a comparison/multipart plan. | Existing price comparison for that pair and item. |
| `What about its price?` / `What is its price?` | Exactly one restaurant and one admitted item. | A fresh complete item-price record for that venue. |
| `What about its price and cancellation policy?` | Exactly one restaurant and one admitted item. | Existing two-task multipart form. |
| `What about both restaurants' prices and cancellation policies?` | Exactly two restaurants and one admitted item. | Existing four-task multipart form. |
| `<one exact restaurant alias>` | One usable approved clarification from the immediately previous turn, containing that ID as a candidate. | Resume the saved operation with that venue. |

Unqualified singular `its` with two candidates creates a targeted clarification. A price operation without an admitted item asks for a complete question naming the item. Plural policy-only requests such as “What about their cancellation fees?” ask for a supported explicit question; this version does not introduce a new two-policy workflow. Unsupported extra clauses invalidate the entire continuation, including “and parking” or embedded instructions. Never answer just the recognized part.

An exact bare catalog alias without a usable clarification asks what the user wants to know about that restaurant; it does not repeat an older question. Full explicit single/comparison/multipart questions continue through their existing admission rules. Greetings, thanks, search and off-topic requests continue through ordinary routing.

### 5.3 Internal questions

Produce an internal effective question only from the admitted operation, exact catalog identity and admitted item. For example:

```text
Original user question: And what about its cancellation fee?
Approved restaurant: demo-harbor-pasta
Effective question: According to Harbor Pasta Lab's policy, quote the complete
Reservations and cancellation policy, including the free-cancellation window
and late-cancellation fee.

Original user question: Which is cheaper?
Approved pair: demo-harbor-pasta, demo-sakura-table
Approved item: mushroom pasta
Effective question: Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab.
```

The effective question is private execution data. Do not replace or append a `HumanMessage` with it. The original question remains the user message saved to memory and shown in the UI.

Recompile generated comparison/multipart questions with the existing planners. Compare their exact ordered targets and item to the resolver result. Revalidate against the pinned catalog before any embedding. A mismatch becomes a fixed safe failure; do not fall back to unconstrained rewriting.

## 6 Conversation state and approval

### 6.1 Strict private contracts

Create `src/domain/document_conversation.py` using strict, frozen Pydantic contracts with `extra="forbid"`. Store JSON-compatible values in checkpoint fields, then validate on every read. Do not accept these fields from the public payload.

| Contract | Required data and bounds |
| --- | --- |
| `DocumentContextDraft` | Ordered unique restaurant IDs, one or two; optional canonical item, 1-80 characters with the existing admitted item grammar; origin mode `single/comparison/multipart`; pinned generation SHA-256. |
| `DocumentConversationContext` | Draft fields plus schema version 1; hashes of actor/thread identity; producing human and approved AI message IDs, each bounded to 100 characters; canonical payload digest. |
| `DocumentFollowupDraft` | Allowed operation enum; exactly two candidate IDs for venue ambiguity; optional item when needed; digest of the approved context being referenced. No arbitrary saved question template or executable text. |
| `PendingDocumentFollowup` | Followup draft plus schema version 1, owner hashes and producing clarification human/approved AI message IDs; canonical payload digest. |
| `FollowupResolution` | Decision `not_applicable/resolved/clarify`; bounded operation, targets/item, effective question or fixed clarification text, and optional clarification draft. Validate which fields are legal for each decision. |

A context is an instruction about which records to request next. It contains no price, fee, quote, evidence, source key, signed URL, model draft, worker result or manifest. The generation is provenance of the preceding answer, not the generation to use for the next answer.

Compute each sealed payload digest with the existing canonical `digest` helper over all its other fields and check it on every read. This detects accidental field corruption; an unkeyed digest does not authenticate a checkpoint against an attacker who can rewrite it. Trust still comes from the server-only writer, checkpoint boundary and approval/producer checks.

For a general approved single-document answer, store only its resolved restaurant and `item=None`. A recognized item-price continuation may retain the item from its validated effective request. Do not extract a dish from free-form answer text. Comparison and multipart drafts derive their item and all requested targets from the validated admitted plan. A partial answer may retain requested targets because they were admitted, but no missing value becomes a fact.

### 6.2 Graph fields

Add these fields to `OrchestratorState`:

- Transient: `rag_followup_resolution`, `rag_pending_context`, `rag_pending_followup`.
- Persistent: `rag_approved_context`, `rag_approved_followup`.

Reset all three transient fields in `run_orchestrator_turn` before every invocation. Do not reset persistent fields there. Missing persistent fields mean no new context; old checkpoints need no destructive migration.

The legacy `rag_approved_scope` remains for flag-off compatibility. With the flag on, do not trust a legacy scope without a valid new context. Synchronize it to a newly approved one-restaurant context if needed for ordinary routing; set it to `None` for a two-restaurant context or revoked context. This removes stale fallback scope without altering legacy flag-off semantics.

### 6.3 Eligibility and lifecycle

1. For a normal continuation, the context owner hashes must match the current configurable actor/thread, and its producer IDs must identify the immediately previous completed graph turn's human and unchanged approved AI messages. Do not scan backward until a usable older answer is found.
2. For a clarification reply, validate the pending clarification against the immediately previous completed turn, its owner, and the digest of its retained context. Accept exactly one candidate alias on that next user turn. Preserve the original active context only for this single clarification exchange.
3. A new unchanged approved document `answered/partial` outcome with valid citations replaces active context and clears the pending clarification. A general single answer or single policy continuation replaces the previous item with `None`; a recognized price continuation retains its admitted item.
4. An unchanged approved targeted clarification installs its pending draft only after final moderation. It retains the referenced context for one reply. Other clarifications clear both persistent fields.
5. A non-document completed turn, disabled feature outcome, unavailable/invalid/insufficient-evidence outcome, output mask or output block clears eligibility for the new feature. Never install their candidate context. Keep any clearing explicit in the node update.
6. A pending clarification is consumed or discarded by the next graph turn. An intervening greeting, unrelated request or malformed reply cannot leave it available later. A complete explicit question supersedes it and follows ordinary admission.
7. Input blocking occurs before graph execution and leaves its checkpoint unchanged. It creates no new context. A guardrail exception or incomplete graph turn must not make a candidate usable; producer identity checks must reject any intervening unapproved draft in checkpoint history.
8. A fresh chat requires an explicit seed question. Actor/thread binding is an additional consistency check for this demo; caller-supplied identifiers are not authentication and this feature does not add a public identity system.

`output_guardrail_node` is the only writer of approved context/clarification. It must validate candidates against this turn's admitted request, effective mode, generation, coverage and released citations before sealing them with owner and producer IDs. For a resolved turn, compare targets/item to its validated resolution. For an ordinary comparison/multipart seed, recompile the current explicit question with the static catalog and compare targets/item; this performs no corpus read. For a general single seed, require its context venue to equal `rag_pending_scope`, with no claimed item. In all paths require the candidate generation to match the released citations, and multipart targets to match the validated coverage. Require `response_status="approved"` and exact equality between raw and approved text. A mask cannot advance context even though the modified answer is safe to display.

Do not rely on a `document_rag_response` flag or a client-supplied assistant message as proof of approval. Context must have been produced by this server gate. Any structurally corrupt or inconsistent candidate fails safely without publishing facts or sources.

## 7 Execution flow and budgets

```text
Original user input
  -> existing input moderation
  -> router node
       -> flag off: existing Jev then Bedrock fallback
       -> flag on: pure follow up resolution
            -> recognized continuation/clarification: document_qa
            -> not applicable: existing Jev then Bedrock fallback
  -> document_qa
       -> clarification: fixed text, no source/model calls
       -> resolved: validate effective question and dispatch
            -> single / comparison / multipart
            -> fresh pin, scoped retrieval, verified selection and rendering
  -> existing output moderation
  -> approve citations and seal context, or revoke eligibility
  -> existing parent memory hook
  -> complete SSE answer and its own sources
```

The deterministic shortcut applies only to the bounded forms and their clarification cases while `DOCUMENT_RAG_ENABLED` and `DOCUMENT_FOLLOWUPS_ENABLED` are true. Ordinary complete requests keep Jev and its Bedrock fallback. Leave Jev SDK configuration and managed router prompts unchanged. Record shortcut routing with provider `document_followup`; do not attribute it to Jev or invent model confidence.

Resolved continuations bypass the existing model query rewrite because the server has already supplied a complete admitted request. Preserve rewriting for legacy flag-off requests and any ordinary existing path that still requires it.

| Resolved operation | Maximum logical execution |
| --- | --- |
| Clarification or rejected continuation | Zero pin, embeddings, vector queries, planners, selectors, rewrites and router provider calls. Final output moderation remains. |
| One restaurant policy or item price | One pin; one scoped embedding/vector retrieval; at most one selector; zero query rewrite/planner/router provider calls. |
| Two restaurant price comparison | Existing one pin and two bounded workers/selectors; zero multipart planner/rewrite/router provider calls. |
| One restaurant price and policy | Existing one pin, one multipart planner and two workers/selectors. |
| Two restaurant prices and policies | Existing one pin, one multipart planner and four workers/selectors. |

Keep existing per-path top-k, context-size, serving-unit, conflict, citation, retry, concurrency-two and deadline limits. The resolver must not add a second corpus pin or extend a deadline. A disabled multipart gate returns its existing disabled response before pinning or planning.

For resolved single policy continuations, reuse `policy_record` and `validate_task_selection` with a typed cancellation task to require the complete controlled cancellation section, including its conditions. For resolved single price continuations, reuse `validate_menu_selection` to require the requested item record with qualifiers. Continue using the existing selector and renderer; do not introduce an extra model call. If the selector omits conditions or evidence is unavailable, return the existing safe failure. Apply these stricter checks to recognized continuations only, preserving ordinary single-question behavior.

Use current evidence to answer every continuation. Pin the active generation once per answer. A corpus change between turns should produce new prices and citations; a pointer change after this turn's pin must not mix generations.

## 8 File change map

All paths below are relative to the repository root. They are the proposed Phase A scope, not changes already made.

| Path | Required change |
| --- | --- |
| `README.md` | Correct current rollout status; describe bounded follow ups as locally implemented only after acceptance; document default-off flag and new report. |
| `docs/DOCUMENT_RAG.md` | Explain approved context, clarification resume, fresh evidence and limitations with examples. |
| `docs/CI_AND_RAG_EVALUATION.md` | Correct rollout summary; add conversation report command, independent scoring and simulated-dependency interpretation. |
| `docs/HANDOFF_PRD_DOCUMENT_CONVERSATION_FOLLOWUPS.md` | Append approval/execution/closeout evidence; retain original requirements. |
| `restaurant-finder-api/src/config.py` | Add `DOCUMENT_FOLLOWUPS_ENABLED: bool = False`. |
| `restaurant-finder-api/.env.example` | Document the default-off opt-in; leave real `.env` untouched. |
| `restaurant-finder-api/src/domain/document_conversation.py` | New strict private contracts and coherent bounds. |
| `restaurant-finder-api/src/domain/document_rag.py` | Optional private context draft on `RagOutcome`; validate status/mode/generation consistency. Do not add public citation fields. |
| `restaurant-finder-api/src/application/document_rag/conversation.py` | New pure resolution, alias matching, eligibility, clarification and context validation helpers. |
| `restaurant-finder-api/src/application/document_rag/workflow.py` | Consume resolution; choose mode from effective question; return no-call clarification; generate single context draft; apply continuation-only record validation. |
| `restaurant-finder-api/src/application/document_rag/comparison_workflow.py` | Return context draft from admitted plan on valid answered/partial result when enabled. |
| `restaurant-finder-api/src/application/document_rag/multipart_workflow.py` | Return context draft from validated request/plan on valid answered/partial result when enabled. |
| `restaurant-finder-api/src/application/orchestrator/workflow/state.py` | New transient/persistent fields; keep legacy state contract. |
| `restaurant-finder-api/src/application/orchestrator/workflow/nodes.py` | Resolve bounded forms inside router; seal/revoke context only at final moderation; preserve ordinary routing. |
| `restaurant-finder-api/src/application/orchestrator/streaming.py` | Reset new transient fields and preserve original user message; do not expose context in `TurnResult`. |
| `restaurant-finder-api/tests/test_document_conversation.py` | New contract, resolver, graph, lifecycle, corpus and security-consistency tests. |
| `restaurant-finder-api/tests/test_router.py` | Prove shortcut/no provider calls and ordinary Jev/fallback preservation. |
| `restaurant-finder-api/tests/test_document_rag_retrieval.py` | Preserve flag-off scope tests; add reset and resolved continuation checks as needed. |
| `restaurant-finder-api/tests/test_document_comparison.py` | Explicit legacy feature setting and enabled context provenance checks. |
| `restaurant-finder-api/tests/test_document_multipart.py` | Explicit legacy feature setting and enabled admitted context checks. |
| `restaurant-finder-api/tests/test_document_citations.py` | Context gate, masking/blocking/corruption and released-source consistency. |
| `restaurant-finder-api/src/evaluation/document_followups.py` | New offline conversation runner, independent scorer and safe reporting CLI. |
| `restaurant-finder-api/src/evaluation/datasets/document_followups.json` | New versioned 24-conversation independent gold and separate provider scripts. |
| `restaurant-finder-api/tests/test_document_followup_evaluation.py` | Complete coverage, invalid input and scorer mutation tests. |
| `restaurant-finder-ui/tests/test_source_documents.py` | Later answer sources and retained earlier controls through mocked transport; preserve originals. |
| `restaurant-finder-infra/bin/cdk.ts` | Parse `documentFollowupsEnabled` using the existing strict boolean context convention. |
| `restaurant-finder-infra/lib/stacks/agentcore-stack.ts` | Add optional `documentFollowupsEnabled` prop; serialize `DOCUMENT_FOLLOWUPS_ENABLED` as true/false, default false. |
| `restaurant-finder-infra/test/document-rag.test.ts` | Default, explicit opt-in, invalid context and one-leaf toggle tests. |
| `restaurant-finder-infra/README.md` | Describe the opt-in and preservation of the guardrail pair/multipart gate. |
| `.github/workflows/ci.yml` | New offline evaluator step, safe summary and exact JSON/Markdown artifact entries. |

Existing `graph.py`, `retrieval.py`, source viewer implementation, API/SSE schema, Jev module, prompts and memory implementation should remain unchanged unless inspection exposes a specific required integration change. Present evidence and the exact added scope before changing an unlisted source. Do not refactor unrelated code.

## 9 Ordered implementation steps

### Step 1 Capture the baseline

Read HEAD, branch, status and the prior closeout receipts. Recheck this PRD's assumptions against current code. Record hashes of real configuration, lock files, corpus originals/catalog, the three existing datasets, immutable prompt manifests and owner warning. Record owned live UI source/process information only if needed to avoid disrupting it; do not send a request.

Create one ignored `.generated/document-followups-<unique timestamp>/` evidence directory. It must contain safe metadata and reports only. Use task-specific names and preserve every previous evidence directory.

**Output:** source/configuration identity, protected hash baseline, change allowlist and AC table initially pending.

### Step 2 Correct the current status summaries

Replace the stale present-tense retained Runtime 15 summaries with a short account of the failed trial followed by the accepted pinned retry at Runtime 16. Link to the accepted handoff and its release/closeout CI. Keep existing simulated report limitations and the original default-off multipart setting. State that conversation follow ups are a proposed/local feature until implemented and accepted.

**Output:** two surgical documentation corrections, with historical receipts preserved.

### Step 3 Add contracts and the default-off configuration

Implement section 6 contracts. Validate unique catalog targets, item/mode coherence, identity hashes, generation length, producer identity bounds and version. Add the flag to API configuration and example only. Add tests for missing/extra/coerced fields, corrupt owner hashes, malformed items, duplicate targets and unsupported schema versions.

**Output:** strict models with no provider imports/initialization and default-off tests.

### Step 4 Implement the pure resolver

Implement whole-question admission, eligibility and exact alias matching in `conversation.py`. Return a typed decision; build canonical effective questions from admitted fields. Reuse comparison/multipart admission to check their output. Keep clarification text fixed and targeted. Validate a bare alias only against an immediately usable pending request.

Treat a recognizable continuation containing extra criteria/instructions as one clarification, with no partial execution. An unknown explicit venue never falls back to the old venue. A broken context disables inheritance; an independently explicit supported question can still proceed normally.

**Output:** all section 5 forms plus negative cases pass in isolated pure tests without any mocked network dependency being invoked.

### Step 5 Integrate routing and transient resets

Resolve inside `router_node` after input moderation and before ordinary classification. For `resolved/clarify`, set `intent=document_qa`, the transient resolution, and truthful shortcut telemetry. For `not_applicable`, execute the original Jev/fallback behavior, deriving any trusted single routing scope only from eligible new context when enabled.

Reset new transient fields on every parent invocation. Preserve the original human content, ID and timestamp. Keep graph topology and tool routing unchanged. Prove no Jev/fallback/rewrite call occurs for an admitted deterministic continuation, and ordinary requests still exercise both providers through existing tests.

**Output:** router decision tests, preserved ordinary routing and correct per-turn reset captures.

### Step 6 Integrate document execution

Handle clarification before constructing any retriever or model. For a resolved request, choose effective mode consistently in both dispatcher and node metadata. Validate targets against the freshly pinned catalog in the existing path. Bypass query rewriting only for resolved continuations.

For single continuations, enforce the complete policy/item validators described in section 7. For comparison/multipart, reuse existing workers and arithmetic. Return a private context draft derived from actual admitted scope, not from answer prose or the planner's unvalidated draft. Keep provider errors, integrity failure and deadline handling safe and bounded.

**Output:** observed operation budgets, correct path/mode/citations, and valid context candidates from all three paths.

### Step 7 Commit context at the output gate

Extend the final moderation node to validate, seal and publish context candidates in one node update. Bind owner/producer identities to the actual current messages/configuration. Implement every lifecycle rule in section 6.3. Clear all transient candidates after use.

Prove blocked/masked responses cannot install context or citations, and that a guardrail exception cannot make an intermediate checkpoint draft eligible. Keep one final output check and the existing parent memory behavior. Capture original human questions in memory; do not save effective questions as extra turns.

**Output:** executed approval/lifecycle tests, private checkpoint inspection, and parent memory call captures.

### Step 8 Add the 24 conversation cases and scorer

Implement the table in section 10 using executed parent graph turns and `InMemorySaver`. Use the existing controlled source fixtures, fake stores/vectors/embeddings, scripted selectors/planner and mocked router/moderation/memory boundaries. Forbid cloud clients. Do not bypass the real dispatcher, resolver, validator, renderer or output gate.

Each conversation seeds context through an executed answer, except explicitly labeled malformed-checkpoint/migration unit tests. Gold outcomes/quotes/citations and provider scripts occupy separate dataset fields. The scorer must not call the production resolver to generate its expected decisions or scopes.

**Output:** 24 independently checked conversations and scorer mutation coverage; existing datasets remain unchanged.

### Step 9 Add source retention and infrastructure checks

Extend existing mocked UI tests to render a seed answer, its follow up and an earlier retained source action. Inspect correct document/generation/hash/page/section binding for both answers. Use actual existing fixture bytes; source viewing does not send an agent request.

Add the strict CDK flag context and prop using the existing boolean convention: omission false; boolean true/false and exact string `true/false` accepted; other values rejected. Assert toggling only this flag changes only its Runtime environment value, preserving multipart, guardrail pair, image, resources, outputs and IAM. Use dummy account `123456789012`, `us-east-2` and no lookups.

**Output:** source association regressions and synthesized flag-only difference evidence.

### Step 10 Extend CI and engineering documentation

Add `python -m src.evaluation.document_followups --offline --output .generated/evaluation/document-followups.json` to the existing API job. Append its Markdown report to the summary and add only its two report paths to the allowlisted artifact. Keep pinned actions, permissions, concurrency, existing steps and deployment/destruction workflows unchanged. Keep feature enablement inside fixtures rather than setting CI's live configuration true.

Document the supported grammar, context lifecycle, default flag, fresh-evidence behavior and offline report interpretation. Update this PRD with actual implementation decisions if a reviewed adjustment is needed.

**Output:** narrow CI diff and readable setup/architecture documentation.

### Step 11 Execute offline acceptance

Run section 11 commands in fresh credential-free subprocesses with installed locked dependencies. Inspect each exit code and report. Fix failures within this scope, then rerun affected and final required checks. Do not loosen evidence/admission checks or edit existing gold to hide a failure.

Record actual unit-test counts; historical counts are not a completion target. Require all 17 single-document, 20 comparison, 40 multipart and 24 new conversations, with no missing/duplicate/unknown case and no failed required check.

**Output:** fresh command receipts and complete reports tied to the final local source hashes.

### Step 12 Review and stop at local completion

Inspect the complete diff and protected hashes, including the owner warning. Mark each AC pass/fail/unmet using inspected evidence. Record affected files, actual test/report counts, remaining gaps, source identity and explicit publication/rollout status. Remove only owned temporary helpers after resolving absolute paths and verifying workspace containment; retain reports and live UI sources.

Present the local result for review. Do not publish or execute Phase B using the previous rollout's exhausted send budget.

## 10 Required offline conversation matrix

Seeds below use the existing explicit admitted forms and real controlled fixture records. Every row is one conversation case; checks within it do not inflate the case count. Rows with alternatives require separately labeled deterministic variants within that case, and the case passes only if every variant runs and passes. Provider failures and guardrail decisions are explicit scripts, not live observations.

| Case | Executed conversation or condition | Required outcome |
| --- | --- | --- |
| F01 | `For Harbor, what is the mushroom pasta price and cancellation policy?` then `And what about its cancellation fee?` | Harbor full 24-hour/RM20 policy; one correct policy source; no rewrite. |
| F02 | F01 seed then `What about its cancellation policy?` | Same unambiguous venue and complete policy, newly retrieved. |
| F03 | `Compare mushroom pasta prices at Harbor and Sakura.` then `Which is cheaper?` | Harbor RM32/Sakura RM36 with qualifiers; RM4 difference; two new original citations. |
| F04 | F03 seed then `What is the price difference?` | Existing comparison path; same pair/item and arithmetic. |
| F05 | Four-task Harbor/Sakura price-and-policy seed then `Which is cheaper?` | Comparison only; two workers; no multipart planner on follow up. |
| F06 | One-venue Harbor multipart seed then `What about its price?` | Complete mushroom pasta price record; one menu source. |
| F07 | One-venue Harbor multipart seed then `What about its price and cancellation policy?` | Existing two-task multipart execution; two sources. |
| F08 | F03 seed then `What about both restaurants' prices and cancellation policies?` | Existing four-task multipart execution; four sources and complete qualifiers/conditions. |
| F09 | F03 seed then `What about its cancellation policy?` | Targeted Harbor-or-Sakura clarification; zero source/model calls; pending request approved. |
| F10 | F09 conversation then `Harbor` | Resume Harbor cancellation policy only; original reply retained as human message. |
| F11 | F09 conversation then `Sakura Table Lab` | Resume Sakura 12-hour/RM15 policy only; no Harbor source. |
| F12 | Harbor seed then `What about Sakura's cancellation fee?` | Explicit Sakura override, full correct policy and new context. |
| F13 | F09 then `Spice` or `Harbor and Sakura` as deterministic variants | No resume; safe clarification; no retrieval and pending request consumed. |
| F14 | F09 then `Thanks`, then `Harbor` | Ordinary simple route for thanks; bare alias cannot resume expired policy request. |
| F15 | F09 then `Sakura cancellation policy?` | Explicit complete question supersedes pending operation and proceeds normally. |
| F16 | Harbor seed then `What about Olive House's cancellation fee?` | Unknown explicit venue cannot inherit Harbor; whole-request clarification. |
| F17 | Harbor seed then `What about its cancellation policy and parking?` or appended instructions | No partial recognition; zero source/model calls; no new pending operation from the recognized substring. |
| F18 | Fresh conversation asks `Which is cheaper?` or `What about its cancellation fee?` | Ask for explicit restaurants/item; no inherited context or retrieval. |
| F19 | Same stable actor, different conversation after F03 seed | No pair/item inheritance in the new thread. |
| F20 | One-venue Harbor multipart seed on v1; active fixture switches to v2; `What about its price?` | New RM32/v2 source instead of old RM28/v1; one fresh pin; item comes from the admitted seed plan. |
| F21 | Harbor seed; new Sakura answer is blocked or masked; follow up uses `its` | New candidate/citations never installed; previous context is not silently reused after the failed completed turn. |
| F22 | Partial Harbor/Spice multipart seed then `Which is cheaper?` | Fresh comparison remains partial/missing for Spice; no invented price/difference; context contains targets, not a successful missing fact. |
| F23 | Feature off, same Harbor multipart seed and pronoun follow up | Exact existing scope-clearing clarification behavior; new resolver/context unused. |
| F24 | Valid comparison seed, multipart gate off, then F08 continuation | Safe multipart-disabled response, no pin/planner/worker calls and no new context. |

Additional focused tests must cover: actor mismatch on a loaded thread; missing/malformed/old-version checkpoint fields; client assistant messages pretending approval; wrong producer IDs; unknown pinned restaurant; mutation of context item/scope; failed or conflicting policy/price selections; a pointer change after pin; interim guardrail exceptions; transient resets; output coverage/citation corruption; deadline preservation; per-turn parent memory behavior; four-source limits; and telemetry hygiene.

The independent scorer checks full text and relevant complete quotes, expected effective mode/targets/item, each original citation field, context lifecycle, clarification consumption and measured call counts. Add mutation tests that change one scope, item, source generation, qualifier, arithmetic result, approval outcome, observation order or call count. Each must fail the appropriate check. Missing, extra or duplicate conversations cannot produce a complete passing report.

## 11 Local verification commands after Phase A approval

These are future execution instructions. Preparing this PRD did not run implementation tests. Use fresh PowerShell processes and existing locked interpreters; missing dependencies require a separately scoped environment repair, not an automatic upgrade.

Set the existing offline safeguards in each verification process:

```powershell
$env:AWS_EC2_METADATA_DISABLED = 'true'
$env:AWS_REGION = 'us-east-2'
$env:PROMPT_SYNC_MODE = 'false'
$env:REQUIRE_PROMPT_MANIFEST = 'false'
$env:AGENT_OBSERVABILITY_ENABLED = 'false'
$env:EVALUATION_ENABLED = 'false'
$env:DOCUMENT_FOLLOWUPS_ENABLED = 'false'
$env:LOGURU_LEVEL = 'ERROR'
$followupOfflineRoot = 'C:\Users\kinoc\Documents\Codex\2026-09-28\i-x20\work\agentic-ai-langgraph-and-aws-agentcore\restaurant-finder-api\.generated\evaluation'
$followupManifestSentinel = Join-Path $followupOfflineRoot ('no-manifest-' + [guid]::NewGuid().ToString() + '.json')
if (Test-Path -LiteralPath $followupManifestSentinel) { throw 'Offline manifest sentinel must not exist' }
$env:PROMPT_MANIFEST_PATH = $followupManifestSentinel
```

Block cloud client construction with the existing `cloud_clients_forbidden` pattern and inject Jev/Bedrock/memory/guardrail dependencies in all new execution fixtures. Use an isolated export without real `.env` files or an equivalent demonstrated test setup that prevents their provider configuration from being consumed. Do not copy secrets into evidence. Environment flags alone are not proof that cloud calls are impossible.

From `restaurant-finder-api`, run each command separately and inspect its exit code:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -m src.evaluation.rag --offline --output .generated/evaluation/document-rag.json
.\.venv\Scripts\python.exe -m src.evaluation.document_comparison --offline --output .generated/evaluation/document-comparison.json
.\.venv\Scripts\python.exe -m src.evaluation.document_multipart --offline --output .generated/evaluation/document-multipart.json
.\.venv\Scripts\python.exe -m src.evaluation.document_followups --offline --output .generated/evaluation/document-followups.json
```

The new CLI must use exits 0 for complete pass, 1 for failed/missing required checks and 2 for invalid input/execution failure, matching existing evaluators. It must not present an old report as success after a failed command. Mark reports `offline_regression` and `simulated_dependencies`; omit raw prompts, quotations, context owners, provider error bodies and secrets from published summaries/artifacts. Count cases and logical operations separately.

From `restaurant-finder-ui`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

From `restaurant-finder-infra`, use installed locked dependencies:

```powershell
npm run build
npm test -- --runInBand
```

Inspect and execute the current CI infrastructure synth command with dummy account `123456789012`, region `us-east-2`, explicit dummy image and `--no-lookups`, once with the new context omitted and once with `-c documentFollowupsEnabled=true`. Compare the Runtime flag and normalized templates. Test invalid context forms in isolated child processes before any provider initialization. Do not use deployment commands for validation.

Finally run `git diff --check`, inspect the complete diff/worktree status and compare protected hashes. Retain actual command exit codes, final source hashes, full dataset coverage and safe reports in the owned ignored evidence directory.

## 12 Telemetry and evidence

Add a bounded `rag.followup.resolve` span with allowlisted enum/count/boolean attributes: decision, reason, operation, restaurant count, context valid, clarification resumed, and execution mode. Reuse existing retrieval/planner/selector/validation/output spans. Exceptions expose safe error classes only.

Never record the effective question, original user text, item text, quotes, context JSON, owner hashes, source keys or provider payloads in new telemetry. Approved catalog IDs are unnecessary for this span; count targets instead. Instrumentation failure must not alter an answer or context approval.

Offline receipts may contain synthetic IDs and fixture identities needed to reproduce contracts, but CI reports should contain safe case/check summaries and logical operation counts. These checks establish deterministic behavior with simulated providers. They do not establish Jev/Haiku/Titan quality, live throughput, latency, dollars saved or general conversation understanding.

## 13 Approval boundaries and later rollout

| Action | Authorization at PRD preparation |
| --- | --- |
| Read source/receipts and prepare this PRD | Authorized by the owner's `proceed`. |
| Implement Phase A and execute the explicit offline checks | Pending sign off on this PRD. |
| Edit README/current-status summaries | Included in proposed Phase A; not applied while preparing this PRD. |
| Commit/push to origin, update PR or run remote CI | Separate publication approval after the final local diff is reviewable. |
| Docker build/push, Runtime update, local UI restart | Separate rollout plan and approval. |
| AWS/provider reads or billable requests | Not included in Phase A; define exact allowance in later rollout approval. |
| Demo walkthrough, benchmark, merge, upstream publication or resource deletion | Outside this plan. |

For later Phase B, prepare a fresh handoff after Phase A passes. It must name the final source, image/manifest provenance, fresh cloud baseline, exact Runtime leaf changes, flag enablement, unchanged pinned guardrail pair, rollback conditions and bounded acceptance attempt ledger. Use the existing accepted Runtime as the baseline only after a fresh read verifies it. The previous six sends and rollback allowance do not carry forward.

The live acceptance must include an approved seed plus singular follow up, comparison seed plus price follow up, ambiguity plus alias resume, a fresh chat without context, and retained source inspection. Allocate every seed/clarification/reply as a separate potentially billable request. Define that complete sequence and allowance before asking for rollout approval; do not assume a clarification or seed is free. The new default-off flag does not authorize enabling it in the running app.

## 14 Decisions and review questions

The proposed decisions are: bounded deterministic resolution; no new resolver model or prompt version; latest eligible graph turn only; one immediate clarification reply; fresh active evidence per answer; candidate approval only after unchanged moderation; default-off compatibility; and a separate 24-conversation regression dataset. These choices keep scope observable and build on the existing workflow.

The owner can adjust the supported wording during review. A broader language surface, policy-only two-venue workflow, dish changes through pronouns, retrieval caches or an authenticated shared service would require their own contracts and acceptance criteria. No missing AWS credential or TypeSafe access answer is needed for this local phase.

**Next approval:** Sign off on Phase A, including its local implementation and explicitly listed offline verification. Stop after the reviewable local result; publication and rollout remain later decisions under the owner's AGENTS.md instructions.

## 15 Execution record

At preparation, only source/receipt inspection and this PRD are complete. AC01-AC14 are pending implementation. Append actual approval, decisions, commands, results, final source identities and unmet criteria here as work proceeds. Do not mark a criterion complete from the plan alone.

## 16 Phase A execution and local acceptance

**Approval:** The owner's subsequent `proceed` authorized Phase A implementation and the explicit offline checks on 2026-10-14. No publication, cloud read, inference, Docker operation, deployment or demo was performed.

### Implemented behavior

The new strict contracts retain ordered catalog targets and a validated item where applicable. The resolver handles the admitted singular policy/price, pair-price and multipart continuations, plus one immediate exact-alias clarification reply. Complete explicit questions retain ordinary Jev/Bedrock routing. Context candidates are sealed only after unchanged output approval and source/coverage validation; masks, blocks, unavailable/invalid outcomes and intervening turns revoke eligibility.

Every answer pins fresh evidence and reuses existing complete policy/menu record validation. Original moderated human messages are preserved in graph history and parent memory; effective questions remain private. New transient fields reset per turn, persistent fields survive the checkpointer, and worker evidence/plans remain private. The feature is default off in API and CDK; the accepted Runtime still contains the previous release.

Implementation decisions within the approved contract:

- Strict JSON validation restores tuple fields from checkpoint arrays without accepting scalar coercion. An explicit before-validator rejects boolean schema versions that Pydantic's literal handling would otherwise normalize to integer 1.
- Producer identity and owner checks accompany canonical payload digests. These are consistency checks; the unkeyed digest and caller-supplied identifiers do not add authentication.
- Ordinary explicitly named single questions retain their existing rewrite path when needed. With the extension enabled, an unadmitted implicit question cannot inherit the legacy restaurant scope and must ask for a complete question.
- Whole-question admission preserves ordinary price-related restaurant search, while appended criteria/instructions on recognized continuations are rejected as a whole.
- Optional resolver-span failures leave its decision intact. Shortcut telemetry identifies `document_followup`, never Jev or an invented confidence.
- Citation/moderation integration coverage resides in the new conversation suite, with the existing citation suite retained. `graph.py`, `retrieval.py`, API/SSE transport, prompts, Jev SDK setup, memory implementation, source-viewer implementation and dependency locks needed no changes.

### Inspected checks

| Check | Final observed result |
| --- | --- |
| API regression | 258 tests, exit 0. Includes 24 new conversation contract/execution tests, six evaluator tests and two router tests. The historical 226-test suite also passed on the initial default-off integration. |
| UI regression | 32 tests, exit 0. The added mocked transport case retains the earlier menu PDF control and the later policy control with their own hashes, viewer names and locations. |
| Infrastructure compilation and regression | TypeScript build exit 0; 53 Jest tests passed. Default/off/on, exact boolean context forms, invalid programmatic props and unchanged surrounding template properties are covered. |
| Original single document evaluation | 17/17 cases, 374 checks, complete pass. |
| Existing comparison evaluation | 20/20 cases, 260 checks, complete pass. |
| Existing multipart evaluation | 40/40 cases, 609 checks, complete pass. |
| New conversation evaluation | 24/24 cases, all 28 named variants and 63 simulated graph turns, 1,147 checks, complete pass. |
| CDK synthesis | Both dummy-account, us-east-2, no-lookup synths exited 0. Comparing the entire Runtime stack after removing the new environment value established that the flag is the only difference. |
| Invalid context execution | Five isolated compiled CLI-app children rejected invalid values before producing a cloud assembly; their nonzero exits were expected and inspected. |
| CI local review | YAML read and Bash syntax checks passed. Pinned actions, permissions, concurrency and other jobs are preserved. One offline command, one report-summary block and exactly two artifact entries were added. No remote run was dispatched. |
| Scope and preservation | 29 changed/new feature paths are within section 8. All 22 protected identities matched, including real configuration, locks, original datasets/documents, catalog, nine-prompt manifest and owner warning. |

The original 17/20/40 datasets remain byte-identical. Gold and provider scripts in the new dataset occupy separate fields; observations come from executed parent turns. Scorer mutation tests reject changed scopes/items, source generation, policy conditions, arithmetic, approval, operation counts, turn order and incomplete variant/case coverage. A changed expected context does not change provider execution.

Additional execution checks reject incomplete policy/menu selections, a forged source, a missing pinned-catalog venue and corrupted context candidates. A guardrail exception leaves an intermediate draft ineligible. A delayed simulated selector is cancelled by the existing request timeout without replanning, source release or context advancement. This demonstrates the async fixture boundary; it does not establish termination of real SDK threads after a timeout.

Initial verification found and corrected the boolean schema-version issue and a TypeScript cast in the intentionally invalid-prop test. A 10 ms timeout fixture could expire during local thread startup before reaching its selector; the final fixture allows 200 ms for setup while delaying the selector for 600 ms, and verifies one start followed by cancellation. These repairs changed no dependency, AWS resource or billable allowance.

### Acceptance criteria

| Criterion | Result and evidence |
| --- | --- |
| AC01 | PASS: full API/UI/infra suites; unchanged datasets; complete 17/20/40 reports; explicit legacy flag settings. |
| AC02 | PASS: F01-F02; complete Harbor policy and one verified original. |
| AC03 | PASS: F03-F05; exact pair/item, price qualifiers, RM4 comparison and fresh sources. |
| AC04 | PASS: F09-F11; no-call clarification followed by an exact alias resumption. |
| AC05 | PASS: F13/F16/F17 and strict contract/resolver/candidate corruption tests. |
| AC06 | PASS: F21, candidate validation, unchanged approval, intermediate guardrail-exception and context-seal tests. |
| AC07 | PASS: F18-F19, actor mismatch and old-checkpoint migration tests. |
| AC08 | PASS: F20, mid-request pointer change and missing pinned-catalog venue checks. |
| AC09 | PASS: all 63 turn counters, original-memory comparisons, transient resets and unchanged final transport contract. |
| AC10 | PASS: mocked actual UI transport plus original-byte/page/line and distinct-viewer-name assertions. |
| AC11 | PASS: complete 24-conversation independent report and scorer/invalid-input mutation tests. |
| AC12 | PASS: 53 infra tests, flag-only whole-template comparison and five invalid-context child executions. |
| AC13 | PASS: narrow inspected CI diff, YAML/Bash checks, preserved action/permission/job configuration. |
| AC14 | PASS: corrected current-status summaries, reviewed path scope, protected hashes and local closeout record. |

### Evidence and stopping point

Private evidence is in `restaurant-finder-api/.generated/document-followups-20261014/`: baseline and protected hashes, actual command receipts/logs, four independent JSON/Markdown reports, synthesized templates/manifest evidence, infrastructure verification, CI/diff review and `local-verification.json`. `final-verification.json` records the final cleanup, source hashes and criteria after closeout. Needed evidence is retained; owned temporary helpers and build scratch are removed after containment/reparse checks. Existing evidence and live UI staging are preserved.

The local source remains uncommitted and unpublished. The new feature has no live model/ranking/latency/cost acceptance and is not enabled in the accepted Runtime. Remote CI, image publication, deployment and billable acceptance require the separately reviewed Phase B plan described in section 13. No implementation criterion remains unmet locally; stop before publication, rollout and the demo walkthrough.
