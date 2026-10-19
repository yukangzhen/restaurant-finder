# Handoff PRD for complete records in single document answers

**Status:** Approved with “proceed.” Local implementation and offline verification PASS; publication and deployment remain outside this scope. Final cleanup/provenance is recorded in ignored evidence.

**Prepared:** 2026-10-19, Asia/Kuala_Lumpur.

**Outcome:** Ordinary document answers preserve a complete supported menu record or cancellation policy even when the model selects a shortened, authentic quote. Ambiguous, fabricated or unverifiable selections cannot become answers.

**Audience and purpose:** The project owner and implementing engineer. This repair addresses the demonstrated live omission before another portfolio demonstration or deployment trial.

**Definition of done:** Reproduce the live failure locally, complete its record deterministically from already retrieved verified evidence, verify original-source citations and unchanged moderation boundaries, and pass offline regression. Produce a reviewable local diff and evidence of its limits. Publication, image building and another live trial require a separate reviewed scope.

## 1 Verified starting point

| Item | Inspected state |
| --- | --- |
| Branch | `feat/document-multipart-rollout` |
| HEAD | `0dc57694b0a5efc863ba18c4b6beafed5813a88d` |
| Prior tooling release | `e4d147ef660e9348c6c08e8013dab92e4e80d46e` |
| Existing draft PR | [PR 1](https://github.com/yukangzhen/restaurant-finder/pull/1) |
| Last verified deployment | Prior vector image, matching READY Runtime and DEFAULT version 21; hybrid-mode key absent |
| Previous validation | Release and closeout CI artifacts confirmed 290 API, 50 UI and 55 infrastructure tests and all five reports |
| Prior live outcome | L1 FAIL; L2–L7 UNUSED; matrix closed; one authorized rollback completed |
| Owner work | Untracked `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`; preserve unchanged |

The [previous recovery closeout](HANDOFF_PRD_HYBRID_RETRIEVAL_RECOVERY.md#recovery-closeout--failed--recovered) records the live evidence. This preparation does not recheck AWS or infer that the old seven-slot ledger can be reopened.

The completed L1 answer quoted `Mushroom pasta - RM32 per serving`. Harbor menu v2/page 1 contains `Mushroom pasta - RM32 per serving. Contains wheat and milk.` The native PDF displayed the full record. Correlated traces showed one correctly scoped hybrid retrieval path with 349 context characters, selection/validation and unchanged approved output moderation.

### Existing code to reuse

- `src/application/document_rag/workflow.py`: `render_answer` verifies a quote is an exact substring; `render_document_answer` verifies original-source provenance. Ordinary single-question selection currently reaches these functions without complete-task validation.
- `src/application/document_rag/comparison.py`: `_records` locates a requested menu title, its price sentence, adjacent recognized qualifiers and a boundary-confidence flag. `validate_menu_selection` requires a complete record and checks conflicting prices.
- `src/application/document_rag/multipart.py`: `validate_passages` checks pinned scope and evidence bounds; `policy_record` locates a complete retrieved Reservations and cancellation section; `validate_task_selection` enforces complete menu/policy selections.
- `src/application/document_rag/workflow.py`: resolved continuations already call `validate_task_selection`. Preserve that strict behavior, including rejection of incomplete continuation quotes.
- `src/evaluation/rag.py`: the expected renderer is independent of the production renderer. Preserve that independence.

## 2 Chosen behavior

The model selects relevant evidence. Server code may extend an authentic selection to one unambiguous complete record in that same retrieved chunk. The server cannot repair invented text, obtain missing text from an unretrieved passage, or substitute another item/source.

| Input and verified source | Required outcome |
| --- | --- |
| L1 quote without its final period or allergens; full Harbor record retrieved | Answer with the complete RM32/serving record, including wheat and milk; preserve its original chunk/PDF citation |
| Sakura price selection omits dinner-only qualifier | Include the complete RM36/serving record, wheat/milk and dinner-only wording |
| Only the late-fee sentence of a verified Harbor policy selected | Include the complete controlled policy body: free at least 24 hours before booking; later RM20 per booking |
| Only the free-cancellation sentence selected | Include the same complete policy body, including its late fee |
| Full valid record selected | Leave it unchanged; completion is idempotent |
| Invented RM999 quote, wrong chunk/venue/generation/hash, or instruction passage | Return the existing safe invalid-answer outcome; no citations or reusable approved context |
| Two incompatible records, an unknown boundary, a split policy section or a record over 600 characters | Refuse to guess or truncate; return an appropriate existing non-answer outcome with no citations |
| Selector returns insufficient evidence, including the valet-parking question | Preserve abstention; do not turn it into an answer because some unrelated policy exists |

This is a bounded repair for the controlled document formats already supported. It does not add general PDF table understanding or arbitrary restaurant-document schemas.

### Why completion precedes strict validation

Rejecting the observed shortened quote alone would avoid an incomplete answer but would leave L1 unanswered. A prompt-only change would leave completeness dependent on the model. Deterministic completion can produce the correct full record without a second model call; existing strict validators then independently check it.

## 3 Scope and authorization

After sign-off, implement the local repair, add tests, run the specified credential-free offline verification, and update the listed engineering documentation. Stop with a reviewable local diff and actual results.

Do not publish commits or PR edits, build/push images, use Docker, change the live UI, call AWS/TypeSafe/models, synchronize prompts, change IAM/guardrails, ingest documents, change the corpus, run a benchmark or begin the demo. The stopped recovery's unused attempts are not available for this repair.

### Allowed paths after sign-off

All paths below are relative to the repository root.

| Path | Permitted purpose |
| --- | --- |
| `restaurant-finder-api/src/application/document_rag/single_record.py` | New pure task-admission and completion boundary |
| `restaurant-finder-api/src/application/document_rag/workflow.py` | Invoke the boundary in ordinary single-question answering before rendering/context creation |
| `restaurant-finder-api/src/application/document_rag/comparison.py` | Expose the existing menu-record parser through a documented shared function; preserve current comparison behavior |
| `restaurant-finder-api/tests/test_document_single_records.py` | New deterministic regression and workflow tests |
| `restaurant-finder-api/tests/test_rag_evaluation.py` | Add completeness/oracle mutation checks if needed; retain existing assertions |
| `restaurant-finder-api/src/evaluation/datasets/document_rag.json` | Strengthen only affected expected gold quotes, as specified below |
| `restaurant-finder-api/src/evaluation/datasets/document_retrieval.json` | Strengthen affected expected-answer fields only if an inspected dependency requires it |
| `restaurant-finder-api/src/evaluation/datasets/document_followups.json` | Strengthen ordinary seed expectations only if an inspected dependency requires it |
| `README.md` | Explain the local fix and its deployment status |
| `docs/DOCUMENT_RAG.md` | Document completion, rejection boundaries and provenance |
| `docs/CI_AND_RAG_EVALUATION.md` | Record observed tests/reports and intentional gold changes |
| `docs/HANDOFF_PRD_SINGLE_DOCUMENT_RECORD_COMPLETENESS.md` | Maintain execution decisions, evidence and completion criteria |

The two conditional dataset paths are not an allowance to change simulations or turn admission/rejection expectations into passing answers. Establish and document the exact affected case IDs and JSON fields before editing either. If the repair needs other production paths, a new dependency, schema/prompt changes or broader semantics, stop and present the concrete additional change.

Preserve the existing browser acceptance helper/fixture/tests, UI application, IaC, CI workflow, dependencies/locks, prompt definitions and immutable prompt manifest, original documents and previous failure records. Preserve the comparison/multipart datasets byte for byte.

## 4 Design requirements

### 4.1 Admit bounded tasks from trusted scope

1. Use the original admitted question and server-resolved restaurant scope. Do not allow a model rewrite or selected quote to choose another venue or requested dish.
2. Mask catalog venue aliases before interpreting menu/policy words, following the existing `resolve_query` approach; a restaurant name containing Price or Policy must not imply an operation.
3. Recognize the current L1/L2 forms and existing dataset price/cancellation forms. Include `what is the <item> price`, `how much is <item>`, their existing venue/possessive variants and explicit cancellation-fee/free-notice questions. Bound an item to the existing 80-character contract and admitted catalog scope.
4. Preserve the existing legacy single path for the one-venue menu-and-policy question. Admit both its item-price and cancellation tasks; require both supported parts before answering it. Do not redirect it into the LLM multipart planner.
5. Handle the existing legacy scoped cancellation follow-up when follow-ups are disabled; it must retain its existing rewrite/call contract. The enabled deterministic continuation path keeps its present validator and behavior.
6. Keep genuine general questions and valet-parking abstention working. A price/policy request that needs clarification cannot bypass the completeness boundary through a generic fallback. Unknown/multiple dishes or unclear scope require clarification rather than a guessed task.
7. Do not add model-based task classification or broad natural-language grammar. Cover admitted forms with explicit positive and negative tests. Unsupported forms must have a documented safe outcome.

Use existing task/selection contracts where they fit. Do not use `MultipartRequest` for a single task: it deliberately requires mixed tasks. A local tuple of existing task objects can represent one or two tasks without changing public graph/SSE schemas.

### 4.2 Verify the original selection before completing it

For an answered draft, revalidate its schema and each selected chunk's complete provenance against the pinned manifest and retrieved evidence. Reuse existing checks for generation, restaurant, document type, version, hashes, text and locations, and original-source validation.

Canonicalize whitespace with `canonical_text`. Require the original quote to be a nonempty exact contiguous substring of the selected verified chunk. Keep the existing rejection of instruction-like content. An invented or edited quote must fail before the code constructs any corrected quote.

Completion must preserve `chunk_id` and use only that chunk's already retrieved text. Manifest metadata can verify identity or detect conflicts; manifest-only text cannot supply missing answer evidence. No additional source read, retrieval, embedding, rewrite or selector call is allowed.

### 4.3 Complete menu records conservatively

Expose the existing controlled menu-record parser through a shared function instead of copying its regex into a second parser. Add focused coverage for the new public interface. Comparison behavior must remain unchanged.

Resolve the requested dish from the admitted task, then locate complete candidate records in the selected retrieved chunk. The quote must anchor that record's title and price, including the observed L1 form with a missing final period. A bare number, a generic fragment, a different dish, or a quote spanning two records cannot serve as an anchor.

Require one unambiguous record with a known boundary. Preserve adjacent recognized qualifiers such as Contains, Available, Served, Vegan and Vegetarian. Do not consume a following dish, footer or unrelated paragraph. The parser's boundary-confidence flag must be checked; obtaining a price does not prove record completeness.

Inspect all relevant retrieved candidates for conflicts, including differing qualifiers at the same price. Do not resolve contradictory records by picking the first or cheapest. If compatible duplicate sources exist, keep the selected chunk only when its complete record is unambiguous. Do not switch to an unselected chunk to obtain a preferred record.

The completed canonical quote must be at most 600 characters and remain a contiguous substring of that chunk. Never truncate it to satisfy the limit. Pass the completed selection through the existing strict menu/task validation and citation rendering.

### 4.4 Complete cancellation policies conservatively

Reuse `policy_record` and its controlled Reservations and cancellation section rules. Require the complete body from the selected retrieved chunk in the same venue/generation. Its supported late-fee or free-notice sentence may anchor completion; a generic word such as booking is insufficient.

Retain the free-cancellation window, late fee, per-booking unit, timing conditions, negation and any other condition in the complete supported body. Do not stitch sections across chunks or use another source to fill a missing condition. Preserve unsupported-layout, missing-evidence and conflict distinctions using existing safe outcomes.

The existing `policy_record` helper may deterministically identify a different equivalent chunk when duplicate sources exist. Verify the returned record belongs to the model-selected chunk; never silently replace its source identity. Reject an ambiguous mapping. Finish with `validate_task_selection` on the completed draft.

### 4.5 Render and approve once

Apply completion only to ordinary single-question answering. Preserve strict resolved-continuation, comparison and multipart validation; their existing incomplete-selection rejection tests must still pass.

For legacy mixed questions, preserve model selection order and stable source labels while verifying exact admitted task coverage. Redundant fragments of the same selected record may be coalesced deterministically; do not add an unsupported task or manufacture a partial success outcome. Keep the existing three-citation ceiling.

Render the completed draft once through `render_document_answer`. Continue through the existing final output guardrail and memory/context approval boundaries. Only unchanged approved text may publish source references or reusable context. Rejection, masking or blocking must not retain raw selections, citations, scope or new approved context.

Keep low-level `render_answer`/`render_document_answer` contracts usable for citation/provenance tests. Integrate the new behavior at the workflow boundary, where the admitted question and retrieved scope are available, instead of making a generic renderer infer user intent.

## 5 Exact execution steps after sign-off

### Step 1 Freeze and inventory

Record approval, HEAD/status and hashes of tracked inputs and the owner's warning document. Create an ignored evidence directory under `restaurant-finder-api/.generated/single-record-<UTC timestamp>/`. Confirm no implementation already serves this purpose and no unrelated change is being absorbed.

Inventory every existing test/evaluator that executes ordinary single-question answering. Record affected case IDs, current scripts, current gold quotes and source locations. Preserve historical reports as historical observations.

### Step 2 Reproduce before repairing

Create tests in the new test file using actual v2 PDF and policy fixtures, real generation preparation and scripted selectors. Reproduce L1 with exactly `Mushroom pasta - RM32 per serving` as the simulated selection. Assert that the desired answer contains the full record and that the current implementation fails that assertion.

Also demonstrate the fee-only policy omission. Use existing fake stores/embeddings/vectors and forbid real client/model creation. Save the targeted failing results. Do not invoke the live UI or model to reproduce a failure already established by evidence.

### Step 3 Implement the pure completion boundary

Add bounded task admission and completion in `single_record.py`, expose the existing menu parser as needed, and integrate before rendering and context-candidate creation in the ordinary single workflow. Use the requirements in section 4. Keep injected dependency interfaces intact and prevent circular imports at module import time.

Use existing safe outcomes. Keep errors and optional telemetry free of question text, quote payloads, source URLs or identities. No new service, configuration flag, retry or model prompt is needed.

### Step 4 Add independent regression coverage

At minimum, cover each row below with named tests. Use vector and hybrid modes for the principal workflow cases. Declare intended test cases in advance; record actual discovered test counts after running them.

| Group | Required cases |
| --- | --- |
| Observed omission | Exact L1 selection without period; price sentence with period; already complete record; idempotence |
| Qualifiers | Harbor wheat/milk; Sakura dinner-only; vegan/vegetarian/served/negative timing text retained when supported by the controlled grammar |
| Policies | Harbor fee-only; Harbor free-notice-only; full Harbor body; Sakura 12-hour/RM15 body |
| Relevance | Wrong dish in correct chunk; pure amount/generic fragment; quote spanning two dishes; restaurant name containing intent words |
| Boundaries | Unknown attached prose; over-600-character record; split/long policy; contradictory full records or qualifiers |
| Provenance | Wrong selected ID, venue, generation, version, hash, page/lines; record present only in unretrieved text |
| Existing workflows | Legacy mixed menu/policy coverage; legacy scoped cancellation; strict enabled continuation/comparison/multipart rejection unchanged |
| Non-answers | Parking insufficient evidence; missing/ambiguous dish/scope; model insufficient evidence not upgraded to an answer |
| Publication boundary | Exactly matched citations; masked/blocked/rejected answer cannot publish references/context or save an unapproved answer |
| Bounded work | No extra selector/rewrite/embedding/retrieval calls; no client/network creation; repeated completion makes no changes |

Gold strings must come from independently inspected sample originals. Do not generate expected answers by calling the production completion helper, parser or renderer. Mutate a completed observed answer to remove wheat/milk, dinner-only, free-notice or late-fee wording and prove the independent assertions detect it.

### Step 5 Strengthen the affected gold answers

The original document RAG dataset currently accepts shortened quotes and checks exact final text. Requiring its report hash to remain unchanged would conflict with this repair.

Keep all 17 case IDs, questions, simulated model selections, rewrite scripts, expected statuses, calls, versions and provenance. Strengthen only `expected.quotes[*].quote` for these affected answered cases:

`harbor_price_v2`, `harbor_price_v1`, `sakura_price`, `spice_price`, `harbor_fee`, `sakura_fee`, `spice_fee`, `harbor_followup`, `explicit_scope_override`, `harbor_fee_alias`, `harbor_menu_and_policy`.

Use complete records from each case's specified corpus version; preserve the RM28/RM32 difference. Keep the shortened simulation quotes so existing cases exercise completion. Leave the six clarification/insufficient/invalid cases unchanged. The mixed case retains two gold quotes and both original sources.

Inspect document-retrieval and follow-up evaluator dependencies. Change only demonstrably affected expected-answer fields in their allowlisted datasets; preserve inputs, simulations, operation/status expectations, variants, turns and call budgets. If a failing test indicates an unexpected semantic change, diagnose the behavior before touching its gold data. Do not weaken evaluator logic or remove negative cases.

Record before/after expected strings and source locations in the evidence receipt. New report hashes are expected for intentionally strengthened outputs; unchanged reports should remain identical. No historical test/report result should be relabeled as verification of the repair.

### Step 6 Run authorized offline verification

Use existing installed dependencies. Launch a credential-free child process with AWS/provider credentials removed, metadata/export/evaluation disabled, prompt sync disabled and no production prompt manifest. Prevent AWS clients and external HTTP/socket destinations, including failures caught by application code. Permit only Windows asyncio's internal loopback socket-pair mechanism where required.

From `restaurant-finder-api`, use the existing interpreter for:

```text
python -m unittest discover -s tests -p test_document_single_records.py -v
python -m unittest discover -s tests -v
python -m src.evaluation.rag --offline --output <owned-evidence>/document-rag.json
python -m src.evaluation.document_comparison --offline --output <owned-evidence>/document-comparison.json
python -m src.evaluation.document_multipart --offline --output <owned-evidence>/document-multipart.json
python -m src.evaluation.document_followups --offline --output <owned-evidence>/document-followups.json
python -m src.evaluation.document_retrieval --offline --output <owned-evidence>/document-retrieval.json
```

Replace `<owned-evidence>` with the resolved operation directory; never pass that placeholder literally. Configure the environment/guards before importing application modules. Use the existing Windows setup/verification conventions documented in the earlier hybrid PRD; do not install or synchronize dependencies.

Run the unchanged UI suite from `restaurant-finder-ui` and existing infrastructure tests from `restaurant-finder-infra` with offline/dummy context. Expected historical floors are 290 API, 50 UI and 55 infrastructure tests; the API total must include the new tests. Record actual totals, not a predicted sum.

Inspect every report's completeness, checks and missing/unmeasured results. Preserve 17/20/40/24/24 case coverage, 28 conversation variants/63 turns and 57 retrieval variants; do not assume historical check counts/hashes when strengthened gold behavior changes a report. Investigate any count change.

### Step 7 Review and document

Inspect the full diff and whitespace. Verify all non-allowlisted input hashes, especially prompts/manifests, source documents, dependencies, UI/acceptance tooling, IaC/CI and owner work. Review each expected-answer edit against source content and the frozen simulation inputs.

Update the three engineering docs and this execution record with the decision, admitted forms, exact completion/rejection behavior, new tests, affected gold cases, actual report results and known limits. State that the fix is local and Runtime 21 was not changed by this scope.

Remove only owned temporary helper/profile files after containment/process/reparse checks; preserve evidence logs and user files. Do not commit/push or spend live attempts. Return the reviewable diff, evidence paths and any unmet criterion.

## 6 Acceptance criteria

| ID | Observable result |
| --- | --- |
| S01 | L1 is reproduced before the fix and passes afterward in vector and hybrid workflow tests |
| S02 | Full menu/policy qualifiers are completed solely from selected, already retrieved verified records |
| S03 | Forgery, ambiguity, conflicts, unknown boundaries and over-limit records fail safely; abstention is preserved |
| S04 | Original citation identity/order and unchanged final-approval/context/save boundaries pass tests |
| S05 | Strict continuation/comparison/multipart behavior and operation call budgets remain intact |
| S06 | Independent completeness assertions and all offline suites/reports pass; actual counts and intentional gold diffs are recorded |
| S07 | Only allowlisted paths change; prompts/corpus/dependencies/UI/IaC/CI/owner work remain preserved |
| S08 | No live/external call, deployment, publication, Docker action, benchmark or demo; temporary owned files are cleaned |

An invalid-answer response for the exact authentic L1 quote does not satisfy S01. Passing fixture or offline checks does not establish that a new deployment passes the seven-question live matrix. A later rollout needs a newly built/audited API image and a separately approved fresh attempt budget; do not reuse the previous image or stopped slots for changed code.

## 7 Decisions and approval boundary

The proposed choice is deterministic completion followed by strict existing validation, with no additional model call or prompt change. The owner can instead choose strict rejection of all shortened quotes, but that choice changes the required L1 outcome and needs an explicit revision before implementation.

There is no product or paid-service choice blocking preparation. Source ambiguity, unsupported forms and layout limits are handled conservatively rather than by expanding this scope. The owner's AGENTS.md requires review of this PRD before a new implementation; a further “proceed” after reviewing it authorizes the local repair and offline verification described here. Publication and live rollout remain separate.

**Preparation record:** Inspected the current Git state, recovery evidence narrative, single/comparison/multipart/follow-up code, existing tests, independent evaluator and shortened gold selections. Added this PRD only. No application code change, test execution, browser action, publication or AWS/provider request was made while preparing it.

## 8 Local execution record

The owner approved this PRD with “proceed.” Implementation started from `0dc57694b0a5efc863ba18c4b6beafed5813a88d` and remains an uncommitted local diff. The evidence root is `restaurant-finder-api/.generated/single-record-20261019041108/`.

### Implemented boundary

`single_record.py` admits bounded price and cancellation tasks from the original question and pinned catalog scope. It verifies the original selection and provenance before completing it. Menu completion requires the selected title/price prefix, one known record boundary, compatible retrieved records and a quote no longer than 600 characters. Policy completion requires a complete cancellation sentence in the selected retrieved controlled section. Conflicts/forgery produce invalid answers; unsupported/missing controlled policies produce insufficient evidence with distinct internal reason codes; unclear price tasks request clarification. Abstention stays unchanged.

The shared `comparison.menu_records` wrapper strips only an exactly matching verified Markdown section heading before applying the existing title/qualifier parser. The strict validator uses the same wrapper. This is needed for the existing synthetic `R01` fixture's verified heading as well as ordinary menu headings; comparison gold behavior remains unchanged. The compiler also admits the existing terse `Harbor mushroom pasta price?` form. These refinements preserve the old parent-graph and retrieval cases without changing their expectations.

Workflow integration occurs inside `rag.validate` for ordinary single answers. Clarification/unavailable-policy exceptions are handled inside that span because its error boundary deliberately sanitizes exceptions before propagation. Existing strict continuation/comparison/multipart selection paths are preserved. Pure provenance validators may internally invoke rendering; the workflow publishes and moderates one completed final answer. There is no added provider call, retry, source read or graph/SSE schema.

### Reproduction and regression evidence

Before changing production code, two named tests failed in both vector and hybrid modes: the exact L1 quote omitted wheat/milk, and the fee-only policy quote omitted free notice. `before-fix.log` records four failing subtests with the expected and observed answers. Both tests subsequently passed.

Final discovery passed **322 API tests**, including **31 new record tests** and **one new independent evaluator mutation test**. The unchanged UI suite passed **50 tests** and infrastructure suite **55 tests**. Parent-graph tests cover unchanged approval, masking, blocking, fabricated originals, citation/context publication, safe memory contents and cleared private candidates. Other cases cover source/venue/generation/hash/location mutations, wrong dishes, conflicting same-price qualifiers, unknown boundaries, long/split policies, missing retrieved passages, idempotence, source ordering and bounded calls.

Four recorded examples in `examples.json` demonstrate the corrected menu and policy answers in vector and hybrid modes, using actual local originals and simulated providers. Each records one embedding, retrieval and selector call. The original citation/version/hash/page or lines is preserved. These examples do not invoke the live application.

### Gold and evaluation evidence

`gold-changes.json` records the 12 changed `expected.quotes[*].quote` fields in the 11 section 5 cases before the dataset edit. All questions, scripts, short simulated selections, statuses, calls, versions and source locations remain unchanged. The comparison, multipart, follow-up and retrieval datasets are byte-identical to the baseline. No conditional dataset edit was necessary.

| Report | Cases passed | Measured checks |
| --- | --- | --- |
| Document RAG | 17 | 374 |
| Comparison | 20 | 260 |
| Multipart | 40 | 609 |
| Follow-ups | 24 | 1,147 |
| Retrieval | 24 | 1,070 |

Conversation coverage remains 28 variants/63 turns and retrieval coverage 57 variants. Every required case/check passed; the reports retain their existing unmeasured live-quality/latency/cost dimensions. Safe report contents match the prior all-pass reports after parsing, and their bytes match after LF normalization. They report outcomes rather than answer text. The stronger gold dataset, independent qualifier-removal mutation test and recorded complete answers establish the changed acceptance rule; the aggregate pass counts alone do not.

### Verification boundaries and preservation

Python child processes ran from an owned short staging directory with credentials removed, nonexistent credential/config/production-manifest paths, sync/export/metadata disabled and network/client guards installed before application import. The existing S3 Vectors Stubber test was allowed to construct one explicitly fake-key SDK client; no AWS request was made. Node infrastructure tests used a preload guard against HTTP/TCP/fetch. Boundary receipts recorded no unexpected clients, external sockets or HTTP attempts. An initial infrastructure preload path-quoting error was corrected in the temporary launcher before its tests executed; dependencies were unchanged.

The preservation audit checked 173 non-allowlisted baseline files, including original documents, prompt definitions/manifest, dependencies, UI and browser tooling, IaC/CI, earlier plans and the owner's warning document. Only the approved active paths changed. Temporary launchers, guard/staging files and owned generated files are removed at closeout after containment/reparse checks; full logs, hashes, reports and final cleanup receipts remain in the ignored evidence directory.

| Criterion | Local result |
| --- | --- |
| S01 | PASS — red reproduction, then complete L1 in both retrieval modes |
| S02 | PASS — completed menu/policy text and unchanged selected source identity |
| S03 | PASS — safe ambiguity/conflict/forgery/layout/limit rejection and preserved abstention |
| S04 | PASS — citation order and parent approval/context/save tests |
| S05 | PASS — existing strict workflow regression and provider-call budgets |
| S06 | PASS — 322/50/55 tests, five full evaluations and independent gold mutations |
| S07 | PASS — allowed diff and protected-input hashes; final source hashes in receipts |
| S08 | PASS for local/external-action boundaries; owned cleanup verified in the final receipt |

This scope performed no publication, image build/push, Docker action, browser/live request, AWS/provider access, ingestion, prompt sync, IAM/guardrail change, benchmark or demo. Runtime 21 was not changed or rechecked. The previous seven-slot live matrix remains closed. A separate publication/image/rollout plan is needed to verify the repaired API in AWS.
