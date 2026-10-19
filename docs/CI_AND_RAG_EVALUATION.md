# Automated checks and document RAG evaluation

## What runs on GitHub

The `Offline quality checks` workflow runs on pushes and pull requests:

| Job | Checks |
| --- | --- |
| API and document RAG | Locked dependencies, API unit/regression suite, complete offline RAG and comparison datasets. |
| UI | Locked dependencies and UI regression suite. |
| Infrastructure | Locked npm dependencies, TypeScript compilation, Jest and CDK synthesis with dummy context/no lookups. |
| Quality checks | Passes only when all three jobs succeed; failure, cancellation and skipped jobs do not pass. |

The workflow needs no AWS/TypeSafe credentials, model calls, prompt synchronization or deployments. It has read-only repository permission, pinned action commits, job timeouts and per-project dependency caches. It publishes the RAG case table in the job summary and keeps only the fictional evaluation report and concise test logs as artifacts for seven days. Original documents, `.env`, private session files and AWS state are not uploaded.

Logged test commands explicitly enable Bash `pipefail`, so piping output through `tee` preserves test failures. Regression tests verify this behavior for all three jobs as well as the aggregate check. Corpus source paths must be relative on Windows and Linux; the parser rejects drive-qualified, rooted and out-of-directory paths before reading source files.

This supplies a status check. Enforcing merge/deployment ordering through protected branches or deployment gates is separate repository policy, not configured here. The existing main-only deployment workflows remain separate.

The owner approved enabling previously disabled Actions for this repository. Its selected-action allowlist permits the pinned CI action commits and the references already used by existing workflows. When changing an action reference, update that allowlist deliberately; a new SHA/tag is not automatically permitted.

## Run the document evaluation locally

From `restaurant-finder-api`, use the locked environment. Dependency installation is `uv sync --locked`; an existing local AWS development environment may retain its `local-aws` extra. The evaluation itself requires no AWS login.

PowerShell:

```powershell
$env:PROMPT_SYNC_MODE='false'
$env:PROMPT_MANIFEST_PATH='.generated/offline-no-manifest.json'
$env:REQUIRE_PROMPT_MANIFEST='false'
$env:AWS_EC2_METADATA_DISABLED='true'
$env:AGENT_OBSERVABILITY_ENABLED='false'
$env:EVALUATION_ENABLED='false'
$env:LOGURU_LEVEL='ERROR'
uv run --no-sync python -m src.evaluation.rag --list-cases
uv run --no-sync python -m src.evaluation.rag --offline --output .generated/evaluation/document-rag.json
uv run --no-sync python -m src.evaluation.document_comparison --offline --output .generated/evaluation/document-comparison.json
```

The CLI writes JSON and a same-name `.md` case table. Generated local reports are ignored by Git. Exit codes:

- **0:** every dataset case is present and all required measured checks pass.
- **1:** a check fails or the observations do not cover the full dataset.
- **2:** malformed/unsupported/oversize input or an execution error.

Use the exit code from the current invocation. Invalid input does not create a new report; a report from an earlier invocation is not evidence of success for the failed command.

Run API regressions with `uv run --no-sync python -m unittest discover -s tests -q`. From `restaurant-finder-ui`, run the same command for UI tests. From `restaurant-finder-infra`, run `npm ci`, `npm run build`, `npm test -- --runInBand`, and CDK synth with dummy account `123456789012`, region `us-east-2`, `--no-lookups` and the explicit dummy image context shown in `.github/workflows/ci.yml`. Do not substitute an authenticated deployment command for this check.

## What the 17 cases check

The versioned dataset is `restaurant-finder-api/src/evaluation/datasets/document_rag.json`.

- Harbor v1/v2 menu prices (RM28/RM32), Sakura mushroom pasta (RM36) and Spice chickpea curry (RM22).
- The three restaurant cancellation fees (RM20/RM15/RM10).
- Missing parking evidence, unspecified/unknown/multiple restaurants, follow-up scope and explicit scope override.
- Forged chunk selection and changed source quotation.
- Full-name and short-alias Harbor policy queries.
- A mixed Harbor menu/policy question requiring both the RM32 menu quote and RM20 cancellation-policy quote, with two separately verified citations.

Human-written gold quotes are checked against real local source chunks, versions and page/line locations. Gold and simulated selector inputs occupy separate dataset fields. The offline harness calls the real document workflow, query resolver, `DocumentRetriever`, provenance validator and renderer. Its store, vector results, embeddings and model answers are explicitly simulated; it does not copy an expected result into an observation.

The scorer independently checks the complete extractive answer text, expected status/scope/generation, every citation field, evidence integrity, source inclusion and supplied call counters. A valid quote about tomato pasta still fails the mushroom-pasta question, even if its source hash and page are correct. Exact prices alone are not an accepted gold quote.

### Restaurant names and document scope

The resolver determines the restaurant from registered catalog names and aliases, then masks all matched name spans only in the text used for document-type inference. The complete canonical question still goes to retrieval and answer selection. Repeated/overlapping aliases, case differences and possessives are covered by tests; words outside the matched names retain their normal meaning.

For example, `Harbor Pasta Lab cancellation policy` now selects **policy**: `Pasta` belongs to the venue name. `Harbor Pasta Lab mushroom pasta price` selects **menu** because the separate dish/price words remain. A question explicitly requesting the menu price and cancellation policy selects **both** (no document-type restriction). A neutral documents question also has no type restriction.

Both full-name and short-alias policy cases now require policy-only evidence. The scorer rejects a full-name policy observation if its recorded filter is changed back to the previous unrestricted value. This remains a keyword heuristic, not a general semantic classifier; contextual phrases such as policy `cost` can still match both keyword groups. See the [query-scoping PRD](HANDOFF_PRD_RAG_QUERY_SCOPE.md) for the scope and execution evidence. Deploying the corrected code requires a separate Runtime rollout.

## Separate hybrid retrieval regression

`src/evaluation/datasets/document_retrieval.json` contains 24 cases with 57 required named variants. It covers exact terms, vector-only paraphrases, deterministic ties, overlap, scoped keyword statistics, complete-passage budgets, corrupted candidates, pointer changes, deadlines, configuration and keyword-only answers in comparison/multipart/conversation workflows.

```powershell
.\.venv\Scripts\python.exe -m src.evaluation.document_retrieval --offline --output .generated/evaluation/document-retrieval.json
```

Use the isolated credential-free process safeguards in the [hybrid retrieval PRD](HANDOFF_PRD_HYBRID_DOCUMENT_RETRIEVAL.md#10-local-verification-commands). Cloud clients and unexpected HTTP are forbidden. Windows asyncio may use an internal loopback socket pair; that allowance does not enable HTTP requests.

The runner executes the real BM25/RRF functions, retriever, chunk verification and relevant parent graphs. Semantic vectors, model responses, stores, moderation and durable memory are simulated. Gold ranks/source records and provider scripts are separate. The existing conversation gold checks complete answers, original citation fields, approval/context lifecycle and operation counts. The new retrieval scorer checks declared ranks, independent fusion arithmetic, truthful distances, provenance, scope and actual reads/calls. Missing/reordered cases or variants, forged ranks/distances/counts/sources and stripped qualifiers must fail.

JSON/Markdown reports expose safe case/check summaries and counts, label `offline_regression` / `simulated_dependencies`, and exclude raw queries, passages, quotations, provider bodies, source URLs and conversation identities. CLI exits are 0 for a complete pass, 1 for failed/missing checks and 2 for invalid input/execution failure. Existing 17/20/40/24 datasets remain unchanged and continue running in their original vector fixtures.

CI adds the fifth evaluator to the existing API job, its summary and its two allowlisted reports. No additional model or search service is required. Local acceptance on 2026-10-15 passed 290 API, 32 UI and 55 infrastructure tests, all original evaluations and all 24 retrieval cases/57 variants with 1,070 measured checks. The original evaluation datasets remained byte-identical. These are functional regression checks; semantic retrieval quality, latency and dollar cost remain unmeasured. The extension was published as `22f8d9c` on 2026-10-19. Both [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39186138435) and [pull-request CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39186143443) passed four jobs; fresh artifacts from both runs confirmed 290/32/55 tests, all five complete reports, 28 conversation variants/63 turns and 57 retrieval variants/1,070 checks. The controlled live rollout was rolled back after a browser-automation syntax error before any acceptance question was submitted. Live hybrid behavior remains unverified; see the [recovery record](HANDOFF_PRD_HYBRID_RETRIEVAL_PUBLICATION_AND_ROLLOUT.md#11-phase-b-execution-and-recovery).

## How to interpret the report

### Separate document comparison regression

The comparison evaluator keeps the original 17 single-restaurant cases unchanged. Its separate 20-case dataset covers both fixture generations, all supported question forms, aliases/order, missing evidence, malformed/unknown/duplicate operands, extra criteria, wrong-item/forged/changed quotations, a provider failure and a pointer change after pinning.

It runs the actual dispatcher, deterministic planner, compiled LangGraph workers, retriever, validator, arithmetic and renderer with simulated stores, embeddings, vector hits and selectors. Cloud-client construction is forbidden. Expected records and provider scripts occupy separate fields; observations come from executed code, not from copying expected results. An independent scorer checks exact answer text, row records, numeric conclusions, original citations, fixed generation/menu scopes, selected evidence and actual call counts.

The CLI writes ignored JSON and Markdown reports with safe case/check summaries and the same 0/1/2 success/failure/input-error distinction described above. CI requires the full comparison dataset and uploads only these reports with the existing artifact allowlist. Raw responses, source bodies, provider exceptions and session/credential values are omitted. Skipped, duplicate or unknown observations cannot yield a passing complete report.

Reports explicitly identify `offline_regression` and `simulated_dependencies`. Live Jev routing, selector accuracy, semantic vector ranking, latency and cost remain unmeasured. These are functional regression checks, not a benchmark.

Additional API tests cover ties, decimal prices, unsupported currencies/formats, different serving units, retrieved conflicts, quote qualifiers, deadline/page/attempt limits, parallel execution, cancellation, output moderation, follow-up scope and parent memory. UI tests verify two distinct PDF/Markdown originals and one-source partial responses through the existing citation transport. Synthetic arithmetic edge inputs are labeled as contract tests and do not alter the corpus originals.

### Separate multi-part document regression

`src/evaluation/datasets/document_multipart.json` adds 40 cases (M01-M40) while retaining the original 17 single-document and 20 comparison cases. It covers the five bounded compound forms, aliases/order, missing dishes, policy failures, complete/truncated records, planner omissions/duplicates/scope changes, schema extras, conflicting evidence, wrong provenance, shared deadlines, pointer changes, disabled gates and legacy comparison dispatch.

The real compiler, structured-plan validator, LangGraph subgraph, retriever, evidence validators and renderer run with fake stores/embeddings/vector hits/planner/selector. Fake providers receive separate scripted inputs, not expected answers. Gold specifies task order, status/reason, literal complete records, original locations, numeric facts and exact operation counts. The scorer independently constructs the entire expected answer and citations. Missing/extra/duplicate observations and fabricated coverage, arithmetic, text, or sources cannot pass.

Run from `restaurant-finder-api` in the credential-free offline process environment described in the handoff:

```powershell
.\.venv\Scripts\python.exe -m src.evaluation.document_multipart --offline --output .generated/evaluation/document-multipart.json
```

The JSON/Markdown reports include safe case/check summaries and measured logical operation counts, with CLI exits 0 for success, 1 for failed checks and 2 for invalid input. They omit raw questions, quotations, provider error bodies and credentials. All cloud-client construction is forbidden. Live Jev/planner/selector accuracy, semantic vector ranking, latency and cost remain unmeasured.

The new flag is enabled only in explicit offline fixtures. Parent integration tests check one final guardrail/memory save, coverage resets and private checkpoint boundaries. Tests exercise maximum-two overlap, actual timeout/client cleanup, complete policy conditions, four-source original bytes/page/lines, late source failures and old source controls. These are functional checks, not a performance benchmark.

CI's existing API job runs this third evaluator and includes its two report files in the existing allowlisted artifact and readable summary. Actions, permissions and quality jobs are preserved. The 2026-10-13 publication also adds three default-off flag checks to the infrastructure suite. The [release push run](https://github.com/yukangzhen/restaurant-finder/actions/runs/38342463448), for source `c3bcd83ed864290098c01464927727fe2f0dee5a`, and its [PR run](https://github.com/yukangzhen/restaurant-finder/actions/runs/38342701260) passed all four jobs. Downloaded push artifacts confirmed 196 API, 31 UI and 6 infrastructure tests; complete 17/20/40 cases and 374/260/609 measured checks, with no failed or missing cases. These evaluations remain simulated dependencies.

That offline success did not establish live acceptance. The first trial's initial request was blocked by final moderation and its approved rollback restored Runtime 15; the [trial record](HANDOFF_PRD_MULTIPART_PUBLICATION_AND_ROLLOUT.md) preserves that failure. The separately approved pinned-guardrail retry on 2026-10-14 passed all six actual UI/Runtime cases, including four-source delivery and hash-verified original downloads, and retained READY Runtime/DEFAULT 16 with `ih5xpt3qi946:1`. See the [accepted retry record](HANDOFF_PRD_PINNED_GUARDRAIL_AND_MULTIPART_RETRY.md#14-gate-b-execution-and-acceptance---2026-10-14). This verifies those controlled live scenarios; ranking accuracy, latency, throughput and dollar cost remain unmeasured.

### Separate document conversation regression

`src/evaluation/datasets/document_followups.json` adds 24 conversations, with 28 explicitly named variants and 63 simulated turns. The parent graph executes every seed and follow-up, including final moderation and memory, using `InMemorySaver`. The resolver, dispatch, retrieval, record validation and rendering are real; stores, embeddings, vectors, Jev/fallback, planner/selector, moderation and durable memory are injected simulations. Cloud-client construction is forbidden.

```powershell
.\.venv\Scripts\python.exe -m src.evaluation.document_followups --offline --output .generated/evaluation/document-followups.json
```

Use the credential-free safeguards described in the [approved follow-up PRD](HANDOFF_PRD_DOCUMENT_CONVERSATION_FOLLOWUPS.md#11-local-verification-commands-after-phase-a-approval). Its temporary verification runner uses an isolated working directory without real `.env` files and the existing locked interpreters. Feature enablement occurs inside explicit fixtures, leaving process/CI defaults off.

Independent gold and provider scripts occupy separate fields. The scorer checks every turn's entire answer, original citation fields, mode, scope/item, approval, clarification consumption, context and measured logical calls. Every named variant is required. Missing/duplicate/unknown cases, missing/reordered turns, changed evidence/arithmetic and fabricated operation counts cannot pass. Reports expose safe case/check summaries and label their dependencies as simulated; they omit user text, quotations, private context and provider payloads. CLI exits are 0 for a complete pass, 1 for failed checks and 2 for invalid input/execution failure.

The original 17/20/40 datasets remain unchanged. Release `11590ea927076e96c92b251912f8747ba0732085` published the extension behind default-off `DOCUMENT_FOLLOWUPS_ENABLED`. Its [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/38532357388) and [PR CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/38532361571) passed all four jobs. Downloaded artifacts confirmed 258 API, 32 UI and 53 infrastructure tests, and complete 17/20/40/24 cases with 374/260/609/1,147 checks.

The separately approved live rollout passed seven actual UI/Runtime requests and retained READY Runtime/DEFAULT 17 with the extension enabled. Correlated traces show two Jev seed classifications, five deterministic shortcuts, eight logical selections, one multipart planner, and seven input/final-output moderation paths. All final outputs were approved unchanged. Three original UI downloads were hash-verified. Six observed SDK retries occurred in AgentCore ListEvents/CreateEvent operations; no UI request was resent. See the [accepted rollout record](HANDOFF_PRD_FOLLOWUP_PUBLICATION_AND_ROLLOUT.md#12-phase-b-execution-and-acceptance). These checks establish this controlled matrix, not measured latency/cost savings, all underlying HTTP attempts or durable event totals.

### Original single-restaurant report

The original RAG report is labeled `offline_regression` and `simulated_dependencies`. It establishes reproducible workflow/contract behavior. It does **not** measure current Jev routing accuracy, Haiku answer selection, Titan vector ranking, live hallucination rate, latency or cost.

Checks have `pass`, `fail` or `unmeasured` states. The report records the expected and observed case counts, missing IDs, failed cases, measured-check count and unmeasured-check count. A partial set cannot receive complete-suite success. Source provenance establishes where a quote came from; question relevance is checked against this small curated dataset, not a universal semantic judge.

Inputs are bounded to 2 MiB, 50 cases, 15,000 answer characters, three citations and ten evidence records per observation. The dataset requires at least 14 cases; this version has 17. IDs/schemas are strict, unknown and duplicate case IDs fail, and nonfinite JSON values are rejected. Reports omit raw answer/evidence bodies, provider payloads, sessions, headers and credentials.

## Score recorded or hand-authored observations

The scorer can inspect normalized observations without generating responses:

```powershell
uv run --no-sync python -m src.evaluation.rag --observations .generated/evaluation/observations.json --output .generated/evaluation/recorded-report.json
```

Input shape:

```json
{
  "schema_version": 1,
  "observations": [
    {
      "case_id": "harbor_price_v2",
      "origin": "recorded",
      "status": "answered",
      "text": "<complete raw API answer, without the UI answer-number decoration>",
      "restaurant_id": "demo-harbor-pasta",
      "generation_id": "<actual full generation hash>",
      "citations": ["<actual structured citation objects>"],
      "calls": null,
      "evidence": null
    }
  ]
}
```

This illustration contains placeholders and is not valid executable input. Use real structured citation objects from the response and the correct dataset fixture generation. Other fields include optional `query_document_type`; full schemas are in `src/evaluation/rag.py`. Valid origins are `manual`, `recorded` or `offline_simulated`.

Imported observations always retain `imported_unverified` origin verification: a caller declaring `recorded` is not proof of a real model capture. Missing counters/evidence are reported as unmeasured. Scoring all required cases can pass answer/provenance checks without measuring retrieval internals; the report makes that distinction explicit. A live generation prepared with a different parser/config cannot silently count as the pinned local fixture's generation.

A real end-to-end model evaluation requires a separately authorized collection run and budget. This CLI deliberately contains no live-invocation option. The existing AgentCore live evaluation runner remains available through its original imports, loaded lazily only when requested.

## Evidence

The [prior verified GitHub run](https://github.com/yukangzhen/restaurant-finder/actions/runs/37750760123) checks the original CI/evaluation implementation commit `3aba7881ad9de422fbf2db77d4198b8368f33714`. Its downloaded artifacts confirmed **125 API tests**, **26 UI tests**, **3 infrastructure tests**, and **16/16 offline RAG cases** with 352 measured checks. This is historical baseline evidence; it predates the query-scoping fix and seventeenth case.

The [verified query-scoping GitHub run](https://github.com/yukangzhen/restaurant-finder/actions/runs/37760052664) checks commit `ae354b09055d9a911a0567d99cf2f821ea42686d`. Its downloaded artifacts confirm **135 API tests**, **26 UI tests**, **3 infrastructure tests**, and **17/17 offline RAG cases**, with **374 measured checks** and no failures/unmeasured checks. TypeScript compilation and CDK synthesis passed. The local API suite also passed 135 tests, and local/CI RAG JSON is identical. The [query-scoping PRD](HANDOFF_PRD_RAG_QUERY_SCOPE.md) records the detailed acceptance evidence and separate AWS rollout requirement.

The [approved execution PRD](HANDOFF_PRD_CI_AND_RAG_EVALUATION.md) records commands, controlled-failure checks, the first run's masked test failure and its repair, and all acceptance results. Inspect both the run's commit SHA and test artifacts before claiming success; a status badge alone is insufficient. These results describe offline regression with simulated dependencies, not live model accuracy.

## Local single record repair verification

The local record-completion repair passed **322 API, 50 UI and 55 infrastructure tests** on 2026-10-19. The API total includes 31 new workflow/pure-record tests and one independent evaluator mutation test. All five offline evaluations passed with 17/20/40/24/24 cases and 374/260/609/1,147/1,070 measured checks; conversation coverage remained 28 variants/63 turns and retrieval coverage 57 variants.

The original document RAG dataset strengthens 12 gold quote fields across 11 answered cases to require complete menu records and cancellation conditions. All 17 IDs/questions, simulations, rewrite scripts, statuses, call budgets and provenance remain unchanged. The short simulated selections deliberately remain short. Removing allergens, dinner-only wording, free-notice or late-fee wording from observed answers fails the independent exact-answer assertion. The comparison, multipart, follow-up and retrieval datasets remained byte-identical.

Verification used existing dependencies in credential-free child processes without real `.env` files. Network/client boundaries recorded no unexpected clients or outbound requests; the existing S3 Vectors Stubber test constructed an explicitly fake-key SDK client. The previous all-pass safe reports and new reports have equal parsed contents and equal bytes after LF normalization; Windows CRLF accounts for raw archive hash differences. The stronger source-based gold and mutation tests, rather than a changed pass count, establish the new completeness requirement.

Evidence is retained under `restaurant-finder-api/.generated/single-record-20261019041108/`, including before-fix failures, full suite logs, five report sets, four simulated completed-answer examples, exact gold diffs and preservation/boundary receipts. See the [execution record](HANDOFF_PRD_SINGLE_DOCUMENT_RECORD_COMPLETENESS.md#8-local-execution-record). These are local offline results; the separate publication/live evidence follows below. General model accuracy, latency and cost were not measured.

### Published repair and controlled live acceptance

Release `0ec71ad401a70ade4cf8511ea01a8d058a5f125a` passed both [PR CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39215532168) and [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39215527127), each with four successful jobs. Downloaded artifacts independently confirm 322 API / 50 UI / 55 infrastructure tests and exact parsed equality of all five reports with the verified local reports: 17/20/40/24/24 cases, 374/260/609/1,147/1,070 checks, 28 follow-up variants/63 turns and 57 retrieval variants. No extra tests or workflow dispatches were added during rollout.

The separately approved trial retained READY Runtime/DEFAULT 22 on 2026-10-19 after seven one-shot UI requests passed complete records, abstention, comparisons and follow-ups. Fourteen manual citation opens/reopens and four original downloads passed. Seven correlated request traces established twelve hybrid retrieval paths, four Jev classifications, three deterministic continuations, twelve selectors, one multipart model planner, maximum two active multipart workers and seven unchanged final approvals. L6's deterministic `rag.comparison.plan` span contains no model call. Twenty-six nested model spans represent thirteen logical calls; eighty-four checkpoint CreateEvent spans are not durable-memory totals. No SDK retries were recorded in these spans.

The acceptance read four pages per relevant log group across the initial pass and one delayed reconciliation, within the shared ten-page cap. Raw exporter fields/provider data were parsed in memory; retained app evidence excludes session values, source URLs and credentials. Evidence is under `restaurant-finder-api/.generated/single-record-rollout-20261019071344/`. See the [accepted rollout](HANDOFF_PRD_SINGLE_RECORD_PUBLICATION_AND_ROLLOUT.md#16-live-acceptance-and-retention). The later documentation-only SHA, its exact-head CI/artifacts and owned cleanup are recorded in ignored closeout receipts and the existing draft PR body. The deployed image continues to identify the repair release. These checks do not establish comparative retrieval quality, live keyword-only rescue, authenticated isolation, latency or dollar savings. Benchmark and demo remain skipped.

## Browser acceptance helper regression

The recovery adds 18 standard-library unit regressions in `restaurant-finder-ui/tests/test_acceptance.py`; the complete credential-free UI discovery run passed 50 tests on 2026-10-19. The existing automatic UI job discovers them without Node/browser/AWS dependencies. They cover function shape, process/semantic errors, exact read-back, ambiguous controls, dispatch reservation and uncertainty, restart/order/chat constraints, independent source/download limits, inert serialized data, redaction, compile/pending checks, explicit live approval, source-content waits and observed new-chat confirmation. Real Node v22.22.0 / Playwright CLI 0.1.22 compatibility was checked separately with the unchanged local Chainlit UI. Seven mock requests, two conversations and four byte-verified UI downloads passed. Gate B release CI and live evidence are pending; fixtures do not establish AWS behavior, retrieval quality, cost or latency.

## Recovery closeout — FAILED / RECOVERED

Tooling release `e4d147ef660e9348c6c08e8013dab92e4e80d46e` passed [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39192402121) and [PR CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39192404885), each with four successful jobs. Fresh artifacts verified 290 API / 50 UI / 55 infrastructure tests, all five report hashes unchanged from the hybrid release, 28 conversation variants/63 turns and 57 retrieval variants/1,070 checks.

The live trial failed L1's complete-record criterion because its quote omitted the source's wheat/milk qualifier. Six slots, the full source/download matrix and twelve-path trace acceptance remain unverified. One correlated hybrid path was observed; output moderation approved the answer unchanged. Runtime/DEFAULT was restored to the prior vector image at READY **21**. The fixture and CI passes do not establish live semantic quality, latency or cost. See the [full recovery record](HANDOFF_PRD_HYBRID_RETRIEVAL_RECOVERY.md#recovery-closeout--failed--recovered). Final documentation-only commit/CI and cleanup are recorded in later ignored receipts and the PR body.
