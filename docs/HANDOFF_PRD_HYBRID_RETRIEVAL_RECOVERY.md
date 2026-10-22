# Handoff PRD for browser automation repair and hybrid retrieval validation

**Status:** Approved execution closed as FAILED / RECOVERED. Gate A PASS; live L1 failed the required qualifier criterion; recovered Runtime/DEFAULT 21. Final closeout publication/cleanup is recorded in later receipts.

**Prepared:** 2026-10-19, Asia/Kuala_Lumpur.

**Outcome:** Repair the acceptance tooling, prove it against the real Chainlit UI with local simulated services, then reuse the already audited hybrid image for a fresh bounded live trial. Keep the prior deployment recoverable and stop before the demo.

**Audience:** The project owner and engineer completing the AI engineering portfolio extension.

## 1 Problem and decisions

The hybrid implementation and its offline CI passed. The prior deployment reached READY Runtime/DEFAULT 18, but the acceptance helper passed top-level `await page…` to a CLI that requires a JavaScript function. The fill operation failed, then the shell still invoked the send helper. That helper reserved L1 before its code also failed to parse. No acceptance question reached Runtime.

The earlier scope treated that reserved error as consumed, stopped the matrix and restored the previous image at READY Runtime/DEFAULT 19. Its remaining six slots cannot be reused. See the [original execution record](HANDOFF_PRD_HYBRID_RETRIEVAL_PUBLICATION_AND_ROLLOUT.md#11-phase-b-execution-and-recovery).

This recovery makes these decisions explicit:

1. Keep a small acceptance helper and regression fixtures in version control.
2. Validate CLI syntax, filled input, error handling, citations and real UI downloads locally before cloud mutation.
3. Use one sequential controller for fill, verification and submit. A failed prerequisite cannot fall through to Enter.
4. Reuse the audited image without a rebuild, image push or Docker-engine dependency.
5. Approve a new seven-slot live matrix with its own ledger and rollback limit.
6. Preserve the current application, prompts, guardrail, identity behavior and document corpus.

A successful local fixture trial proves browser/control compatibility. It does not prove hybrid retrieval or AWS behavior. Only the later live trial can satisfy the live criteria.

## 2 Inspected baseline and evidence

Repository: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.

| Item | Inspected local or historical value |
| --- | --- |
| Branch / HEAD | `feat/document-multipart-rollout` / `9c116edc9043a7f1a6b4ee3ac11bc4cbabb45bd2` |
| Hybrid release | `22f8d9ce1831e2e1d0cfb8086665eb88ca52a99c` |
| Existing draft PR | [PR #1](https://github.com/yukangzhen/restaurant-finder/pull/1), base `feat/jev-router` |
| Previous result | Private final receipt: B01–B05 and operational B09 PASS; B06–B08 unmet; FAILED_RECOVERED |
| Previous application tests | 290 API, 32 UI, 55 infrastructure; release and closeout push/PR CI artifacts inspected |
| Retrieval regression | 24 cases / 57 variants / 1,070 checks, simulated dependencies |
| Recovered AWS state | Last verified Runtime/DEFAULT 19; previous image restored; retrieval-mode key absent |
| Preserved bindings | Multipart/follow-ups true; guardrail `ih5xpt3qi946:1`; prior IAM/corpus |
| Owner work | Untracked `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`; preserve and exclude |
| CLI interface | Installed `run-code --help` says its argument is a function invoked with `page`; native fill/click commands also exist |
| Old helper files | Removed at prior closeout; recreate the repaired tooling from this specification, not from an assumed remaining script |

Previous evidence root: `restaurant-finder-api/.generated/hybrid-rollout-20261016033626/`. Read `final-verification.json`, `published-image.json`, `image-audit.json`, `image-audit-files.json`, CI receipts and `rollback-ready.json`. Preserve old failures and owner-only ACLs.

Fresh AWS/GitHub service health has not been established during preparation of this plan. Historical values must pass Gate B preflight.

### 2.1 Audited image to reuse

| Identity | Required value |
| --- | --- |
| Image URI | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:hybrid-retrieval-22f8d9c-20261019013820-arm64` |
| OCI index | `sha256:d755be05db461862c57ac4c90957bd648dc2932804b278f1b916fe74c7526b19` |
| linux/arm64 child | `sha256:031b5125231617d312bb53c50d3e1b772b7a9ef9c885f6a0e3e3aaef7e116892` |
| Config | `sha256:321233bfe98e7b0f61c85d7397027bdaa8d63f82347fe5f549a293e5f7fc1288` |
| Audit | 90 packaged files / 79 runtime source files; UID 1000; normal instrumented command; network-disabled inspection |
| Prompt manifest | Nine prompts; SHA-256 `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9` |
| Provenance | API tree must equal release `22f8d9c`; UI application/dependency files and IaC remain unchanged |

A missing/mismatched registry image or unexplained provenance difference stops this scope. A new build or push requires a separate decision. Do not substitute an unaudited tag.

## 3 Deliverables and authorization

After sign-off on this entire PRD, execute Gate A first. Gate B may start only after all Gate A criteria pass. The sign-off covers both gates and the concrete external/paid limits below; no repeated approval is needed for a conforming change set.

### 3.1 Exact eight-path publication allowlist

~~~text
restaurant-finder-ui/acceptance.py
restaurant-finder-ui/tests/test_acceptance.py
restaurant-finder-ui/tests/fixtures/hybrid_acceptance.py
README.md
docs/DOCUMENT_RAG.md
docs/CI_AND_RAG_EVALUATION.md
docs/HANDOFF_PRD_HYBRID_RETRIEVAL_PUBLICATION_AND_ROLLOUT.md
docs/HANDOFF_PRD_HYBRID_RETRIEVAL_RECOVERY.md
~~~

The first three are operational/test tooling. They must not be imported into the live UI or API. Keep `app.py`, `source_documents.py`, dependencies/locks, API, IaC, prompts, datasets and `.github` unchanged.

Closeout may change only the five documentation paths in that list. Use one initial normal commit/push and one documentation-only closeout commit/push to the existing branch/PR. Do not merge, force-push, create a PR, dispatch workflows or change Actions settings.

### 3.2 Excluded actions

No new application functionality, new dependency/install/upgrade, API image build/push, Docker operation/recovery, prompt sync, ingestion, guardrail/IAM change, corpus switch, authenticated identity feature, benchmark or demo. Do not stop/restart the existing UI unless Gate B proves the one permitted owned restart is necessary.

## 4 Gate A implementation

### Step A1 Freeze inputs and create owned staging

1. Record approval, current HEAD/remotes/status and hashes of all tracked files plus the owner warning. Stop on unexplained drift.
2. Create one ignored operation evidence root under `restaurant-finder-api/.generated/hybrid-recovery-<UTC timestamp>/` and one short fixture staging root under the task's `tmp` directory.
3. Use existing installed Python/Chainlit/Node/CLI/browser versions. Read CLI version/help and resolve the exact installed CLI entry point. Record their identities.
4. Copy unchanged UI application inputs into fixture staging without real `.env` or credentials. Preserve the 8010 listener and its source directory.

### Step A2 Implement the small sequential helper

Implement `restaurant-finder-ui/acceptance.py` using standard-library orchestration and the already installed CLI. No browser package or SDK dependency is added.

Required behavior:

- Expose local-fixture and explicitly selected live modes. Default to local; reject an unapproved/unverified live ledger.
- Accept explicit CLI path, owned session name, loopback base URL, evidence root and approved matrix. Reject remote/unexpected origins, arbitrary executable paths, path traversal and slot IDs outside the frozen matrix.
- Prefer native CLI commands when they satisfy privacy/output requirements. For `run-code`, generate a complete function, for example `async (page) => { ... }`, and pass it through a temporary file using `--filename`.
- Compile each generated function with installed Node without calling it. Verify that the expression evaluates to a function. This happens before live-slot reservation.
- Pass process arguments as an array; do not interpolate user text into shell commands. Serialize question/locator strings as data. Do not place credentials in arguments or files.
- Check exit codes and structured/textual CLI errors. A semantic CLI error cannot be interpreted as success merely because the process exits zero.
- Inspect a fresh snapshot before choosing a control. Avoid guessed IDs or unobserved selectors. Refresh a stale snapshot instead of blindly repeating a click.
- Fill only the observed message textbox. Read its actual value back and require equality with the exact intended question.
- Verify there is exactly one intended textbox/send control, the expected conversation and no pending send before reserving a slot.
- Save the slot reservation durably immediately before one Enter/send dispatch. No shell-separated fill-and-send sequence. A failed fill/read-back/compiler check returns without invoking submit.
- Treat interruption, timeout, uncertain delivery, an attempted Enter that errors, provider errors and blocked/masked responses as consumed. Never automatically resubmit.
- Keep source-opening/download actions separate from question submission. Reserve their counters before a click.
- Use one isolated browser profile, no persistent credential state, sanitized stdout snapshots and private screenshots/downloads. Generated action code uses selectors/names rather than session-bearing source URLs.
- Configure the CLI to avoid raw network/console/snapshot files where possible. Validate actual artifact behavior; scrub URLs in memory before writing evidence. If raw sensitive artifacts cannot be prevented, Gate A fails before live use.
- Close only owned sessions and listeners. Validate absolute paths/reparse points before cleanup.

The ledger distinguishes `UNUSED`, `PREPARED`, `DISPATCH_RESERVED`, `SUBMITTED/UNCERTAIN` and final PASS/FAIL. A compiler/fill failure proven to precede reservation leaves the slot UNUSED. Once reserved for dispatch, an interrupted or uncertain action is consumed conservatively. This definition applies only to the new matrix; the previous L1 record remains unchanged.

At most two snapshot/locator refreshes are allowed for a proven pre-dispatch stale control, with unchanged question/helper code. They cannot issue Enter. Exhaustion stops the live matrix. No implementation repair or helper replacement is allowed after publication during Gate B.

### Step A3 Add failure regression tests

Add at least these twelve named independent cases in `tests/test_acceptance.py`, using simulated subprocess results and temporary ledgers:

1. Top-level-await input is rejected before dispatch; a valid function compiles.
2. Nonzero fill exit prevents submit and leaves the slot UNUSED.
3. A textual/structured CLI error with exit zero prevents submit.
4. Empty/wrong input read-back prevents reservation and submit.
5. Missing/ambiguous textbox or send control prevents submit.
6. Successful exact fill/read-back performs one reservation and one submit.
7. Dispatch exception/timeout leaves a consumed uncertain slot and cannot resend.
8. Restarting the controller cannot repeat a reserved/completed slot.
9. Failed seed prevents dependent follow-ups; exact order and chat assignment are enforced.
10. Source opens/downloads respect their separate limits and do not call submit.
11. Quotes, newlines and shell metacharacters remain inert data; only the approved origin/path/slot is accepted.
12. Synthetic source/session tokens are redacted from every saved QA artifact, while fixture source identities remain inspectable.

Use existing unittest discovery. Unit tests simulate compiler/CLI subprocess boundaries; they must not require Node, a CLI/browser installation or AWS in the automatic UI job. Real Node compilation and browser compatibility are verified separately in Steps A2/A4. Run the existing UI suite plus the new tests in a credential-free process. Record actual test count and each named result; do not claim a predicted total as observed.

### Step A4 Prove against the real UI with simulated services

Implement `tests/fixtures/hybrid_acceptance.py` with explicit guarded entry points. Importing it must not launch listeners or browsers.

1. Launch the staged unchanged Chainlit UI in `local` mode and one local SSE stub on free loopback ports, preferring 8011/8012. If occupied, preserve those listeners and allocate free loopback ports; record them.
2. Launch hidden owned processes using `Start-Process -WindowStyle Hidden`. Record exact PIDs/cwd/interpreter and restoration/cleanup targets.
3. Use existing local sample originals. The SSE stub returns clearly labeled fixture responses/citations in the application's actual chunk/done envelope. Give fixture metadata a synthetic generation distinct from the live generation.
4. Replace only the fixture process's S3 client factory with a bounded in-memory adapter, so the real `load_original` hash checks, source-element construction and Chainlit viewers execute. Do not patch the live UI process or rewrite its application files.
5. Strip AWS/provider credentials/profile configuration from fixture processes; disable metadata/export/evaluation. Block AWS SDK clients and all external HTTP/socket destinations. Permit only the owned loopback services and Windows asyncio's internal loopback socket pair.
6. Use the installed CLI to open a fresh owned fixture browser. Observe controls, then run two mock conversations in the same seven-message order as section 6.
7. Inspect full displayed answers, native PDF/Markdown views, answer-specific source labels, four actual fixture UI downloads and retained older links after later answers. Hash each download against the local original.
8. Verify the SSE stub saw exactly seven intended requests, in order and in two distinct conversations. Fault cases must demonstrate zero extra submissions.
9. Verify the twelve failure cases, source/download counters, saved-artifact redaction and fresh-context behavior. Do not count fixture activity as AWS acceptance or trace evidence.
10. Close only owned fixture services/browser, remove temporary profiles/code exports after containment/process/reparse checks, and preserve sanitized results and download hashes.

Allow one initial fixture round and up to two local repair rounds. If Gate A remains incomplete after that, stop without cloud action. No real 8010 agent message is part of Gate A.

### Gate A definition of done

| ID | Observable result |
| --- | --- |
| A01 | Only the eight allowlisted paths changed; application/dependencies/IaC/corpus and owner work unchanged |
| A02 | Installed CLI/compiler protocol recorded; generated action functions compile before dispatch |
| A03 | All twelve failure cases pass; failed fill cannot fall through to submit |
| A04 | Full existing UI suite and new helper tests pass; exact count recorded |
| A05 | Real local Chainlit with simulated services completes seven mock sends in two conversations, with no extras |
| A06 | Native source views, retained associations and four real fixture downloads verified |
| A07 | AWS/external-service boundaries and artifact redaction pass; no real agent invocation |
| A08 | Owned fixture cleanup and provenance receipt pass |

## 5 Gate B preflight and publication

### Step B1 Recheck recoverability and provenance

1. Verify default AWS login explicitly in region `us-east-2`. Require account `447393541969` and an authorized non-root identity. Expiry requires the owner to run `aws login --profile default`; do not rewrite credentials.
2. Read current stable stack/template, Runtime and DEFAULT. Expect the last recovered version 19, baseline image and absent mode key. Unexplained drift requires reconciliation before mutation. Capture a new secured rollback baseline; do not reuse an old template as current authority.
3. Require `restaurantFinder-AgentCoreStack` / logical ID `restaurantFinderAgentCoreRuntime` / Runtime `restaurantFinder_Agent-Ha58oX5Psu`. Preserve multipart/follow-ups true and every other effective setting.
4. Verify the existing candidate tag/index/ARM64/config against section 2.1 and the prior complete audit. Require the API tree and packaged-source hashes to match release `22f8d9c`, and unchanged application/dependency/IaC inputs. New UI acceptance/test files are not runtime API inputs.
5. Verify the baseline image remains fetchable and retained under actual ECR lifecycle/inventory rules. Count actual OCI indexes/children/attestations; do not equate one tag to one stored manifest. No image publication occurs in this retry.
6. Recheck immutable guardrail `ih5xpt3qi946:1` and effective IAM with the accepted canonical projections, then capture full fresh equality baselines. No standalone moderation call or policy edit.
7. Recheck pointer/manifest/index. Require generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` and ETag `"d3705246c1cc2a4fd7f694bc91553e95"`, six originals, Titan V2 / 512 / float32 / cosine and top-k five.
8. Read the four originals in section 6.1 once each, at most 5 MiB each, close bodies and verify exact hashes/records. Read each of nine pinned immutable prompt versions once and compare with unchanged committed definitions/manifest. Do not sync/create prompts.
9. Verify the owned 8010 UI listener, seven original application/dependency files, AWS mode/DEFAULT ARN/region/bucket/source viewer and current credential mechanism without dumping environment values. Reuse it if valid. At most one necessary owned restart is included, with exact source/settings captured and no real .env edit.
10. Verify GitHub identity, branch/remote head and draft PR #1's current base. Preserve unrelated owner work and private ACLs.

Use the fingerprint targets and original identity definitions in the [previous PRD](HANDOFF_PRD_HYBRID_RETRIEVAL_PUBLICATION_AND_ROLLOUT.md#3-historical-deployment-and-preservation-targets). Recheck service values; prior receipts do not establish current health.

### Step B2 Publish the exact tooling release

1. Freeze Gate A helper/fixture/test bytes and their verification receipt. No helper code changes during the live trial.
2. Stage exactly the eight paths, inspect the full staged diff and whitespace, normally commit/push once to origin after a remote-head check.
3. Preserve existing PR sections/title/base/draft. Append actual Gate A evidence and planned retry; attach the existing PR through the app tool.
4. Inspect both automatic exact-head push/PR CI runs, all four jobs and all five report sets/test logs. API 290 and infrastructure 55 must remain unchanged. UI count must equal the actual Gate A count, including the existing 32 and newly added tests.
5. Require original 17/20/40/24 case regressions, 28 conversation variants/63 turns and 24 retrieval cases/57 variants/1,070 checks, with complete passing checks and inspected artifact hashes.
6. Stop before deployment on unexplained source drift or failing/missing CI. No workflow dispatch, dependency update or new image publication.

### Step B3 Propose, review and execute one update

1. Copy the fresh deployed template. Change only the Runtime container URI to the exact existing candidate and `EnvironmentVariables.RAG_RETRIEVAL_MODE` to `hybrid`.
2. Restore those two leaves to their baseline presence/value in a parsed comparison; require full equality elsewhere. Preserve parameters/capabilities/resources/outputs.
3. Create one UPDATE change set. Require one existing Runtime Modify, Replacement False, only the two property groups and RequiresRecreation Never.
4. Record proposal hash and source/image identity; immediately recheck baseline and candidate registry identity. Execute once only for that conforming proposal.
5. Poll every 15–30 seconds, at most 20 minutes. Require UPDATE_COMPLETE and matching READY Runtime/DEFAULT versions, audited image and hybrid value. Measure the version rather than assuming 20.
6. Verify full template, all 18 expected resource mappings/outputs, surrounding Runtime settings, guardrail/IAM and corpus before any message. Unexpected differences enter the rollback decision.
7. Use the frozen Gate A helper with one owned live browser and a fresh seven-slot ledger. No smoke greeting or warm-up.

## 6 Fresh live matrix

These seven slots are new and independent of the stopped prior matrix. Use the real 8010 UI in AWS mode against DEFAULT. Start two fresh conversation IDs, and keep consecutive dependent turns free of unrelated messages.

| Slot | Chat | Exact text | Required result |
| --- | --- | --- | --- |
| L1 | A1 | According to Harbor Pasta Lab's menu, what is the mushroom pasta price? | RM32 per serving; wheat/milk; 1–3 relevant Harbor menu selections |
| L2 | A2 | According to Harbor Pasta Lab's policy, how much notice must I give to cancel without charge, and what is charged if I cancel too late? | Free at least 24 hours before booking; later RM20 per booking; 1–3 relevant Harbor policy selections covering both |
| L3 | A3 immediately after L2 | And what about its cancellation fee? | Deterministic Harbor continuation; fresh full 24-hour/RM20 policy, one source; no router/rewrite inference |
| L4 | A4 | According to Harbor Pasta Lab's documents, is valet parking available? | Insufficient evidence, no availability claim or new citation; scoped retrieval/selection still run |
| L5 | B1, fresh chat | Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources. | RM32/RM36 per serving, wheat/milk, Sakura dinner only; Harbor cheaper by RM4; two menu sources |
| L6 | B2 immediately after L5 | Which is cheaper? | Deterministic continuation; fresh two-venue retrieval, full records and RM4 difference; two new sources; no router/rewrite/planner inference |
| L7 | B3 immediately after L6 | What about both restaurants' prices and cancellation policies? | Four tasks, at most two active workers; both full menu records, Harbor free ≥24h / late RM20, Sakura free ≥12h / late RM15 per booking; four originals |

L1/L2/L4/L5 require ordinary document routing through Jev, with the existing Bedrock fallback only if actually observed. L3/L6/L7 require `document_followup`. All seven require input moderation and unchanged final output approval. A masked/blocked result cannot pass.

Validate final answer/control associations before each dependent turn. Defer lengthy views/downloads until the conversation's dependent sequence finishes. Stop at the first failed/unverified required result; no resend, rewording, provider switch or use of remaining slots as probes.

### 6.1 Original identities

| File | Version | Bytes | SHA-256 | Full record |
| --- | --- | --- | --- | --- |
| harbor-menu-v2.pdf | v2 | 1975 | `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10` | PDF p1; RM32/serving; wheat/milk |
| harbor-policy.md | v1 | 534 | `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471` | Reservations and cancellation, lines 5–8; full ≥24h / late RM20 per booking |
| sakura-menu.md | v1 | 383 | `0ac797361e4fc9abc433685b26693e6d877ed6ad873c94110cd0e3a7be7e9637` | Main dishes, lines 5–11; RM36/serving; wheat/milk; dinner only |
| sakura-policy.md | v1 | 466 | `e61b5aa2a3c6969061866379a754fbd7a3d07aef4e82a39c5dc89ddea4c6668f` | Reservations and cancellation, lines 5–8; full ≥12h / late RM15 per booking |

After A1–A4, open all L1/L2 controls and L3's control, then reopen the first L1 control: at most eight actions. Confirm L4 has none; download Harbor menu and policy once each through actual UI controls.

After B1–B3, open L5's two, L6's two and L7's four, then reopen L5's two: ten actions. Download Sakura menu and policy once each. Verify full content, version/hash/location and retained answer association, using the already downloaded Harbor originals where relevant. Total: at most 18 opens/reopens and four actual original downloads.

Repository copies, fixture downloads and backend-only GETs cannot replace live UI downloads.

## 7 Cost and operation limits

| Operation | New limit after approval |
| --- | --- |
| Real Runtime sends | Seven reserved dispatch attempts, L1–L7; no automatic resubmission |
| Local repair | One initial fixture round plus at most two repair rounds before publication; zero real agent/model requests |
| Source preflight | Four unique S3 originals, each ≤5 MiB; six manifest identities |
| Prompts | Nine immutable read-backs, one each; one final metadata reconciliation only if needed |
| Live source actions | ≤18 attempted opens/reopens; four actual original downloads |
| Screenshots | ≤18 private live screenshots; fixture screenshots recorded separately |
| Build / image publication | Zero builds, pushes, tag overwrites, image deletions or Docker operations |
| Cloud updates | One reviewed forward execution and at most one conditional reviewed rollback |
| UI | Reuse; at most one necessary owned restart and one rollback restoration if this phase changed it |
| Logs | Acceptance window ±60 seconds; ten pages of ≤1,000 events per relevant group, shared across initial read and one delayed reconciliation; count empty/repeated-token pages |
| Polls | Readiness every 15–30 seconds, ≤20 minutes per update; CI every ≥30 seconds, ≤30 minutes per publication; blocking waits ≤60 seconds |
| Git publication | One exact eight-path release and one five-document closeout, normal pushes, same draft PR |

Seven sends is not seven AWS calls or a dollar cap. Ordinary AWS/TypeSafe, storage, logging and CI charges may apply. No credit-balance or price estimate is implied. No extra guardrail probe, greeting, benchmark, live evaluator, ablation or generation-switch trial is included.

## 8 Trace verification and rollback

### Step B4 Verify correlated execution

Read only the bounded acceptance window and safe correlations. Confirm current presence of `aws/spans`, `/aws/vendedlogs/bedrock-agentcore/restaurantFinder-telemetry` and the known Runtime DEFAULT log group before querying.

Require:

- Four ordinary document routes and three deterministic continuations, with no router/rewrite inference for L3/L6/L7.
- Twelve logical retrieval paths: four singles, two comparison workers each for L5/L6 and four L7 workers.
- Twelve associated `rag.keyword_rank` / `rag.fuse` pairs, mode `hybrid`, algorithm `bm25-rrf-v1`, correct generation and venue.
- Fresh embedding/vector/selection work; one L7 planner; at most two concurrent workers.
- Vector/keyword counts ≤5, union ≤10, consistent overlap, returned passages ≤5, context ≤9,000 characters.
- Unchanged output approval/save boundaries and safe new application attributes; inspect standard exporter fields separately.

Separate logical operations from duplicate instrumentation and observed SDK retries. Never export raw provider bodies, checkpoints, conversation identities or session/source URLs. A successful answer alone cannot establish rank spans or live keyword-only recovery.

Missing required telemetry/source evidence leaves acceptance incomplete. No extra Runtime call is permitted to improve evidence.

### Step B5 Retain or recover once

Retain the candidate only when every live result, source, trace and preservation criterion passes.

The one conditional rollback is authorized for a failed/unready update, failed moderation/answer/workflow/source contract, or bounded verification that cannot establish acceptance.

1. Stop all sends. Preserve safe failure evidence and unused slots.
2. Reconcile current state; do not overwrite another actor's concurrent configuration change.
3. Restore the fresh baseline image and exact prior mode presence/value. Remove the key if absent. Preserve previously accepted flags and pinned guardrail.
4. Review one no-replacement rollback change set and execute once. Require stable matching READY Runtime/DEFAULT, original template/resources/settings, IAM/guardrail and corpus.
5. Restore the owned UI only if this phase changed it and restoration is necessary.
6. Do not invoke the recovered application. Preserve commits, image, originals and failure evidence. Another recovery mutation needs a new decision.

A rollback is FAILED / RECOVERED, not a live acceptance pass.

## 9 Closeout and final criteria

Update only the five documentation paths with observed results, source/image/Runtime identity, CI links, actual attempted/unused slots, originals/trace evidence and retain/rollback. Normally commit/push once and inspect exact closeout CI/artifacts. Application/API/IaC/CI trees and the frozen helper/fixture/tests must equal the tooling release.

Keep the durable acceptance helper and tests tracked. Remove only owned temporary action files, fixture copies/services/profiles and incidental operational scripts, after path/process/reparse checks. Preserve private evidence, old failures, dependencies, the existing UI tree and owner warning. Clear temporary auth if any; do not broaden private ACLs.

Record the later closeout SHA/CI and final cleanup in ignored receipts and the existing PR body, because a commit cannot contain its own future SHA/run.

| ID | Completion criterion |
| --- | --- |
| R01 | Gate A A01–A08 pass and frozen harness/test provenance is recorded |
| R02 | Exact eight-path publication; automatic release CI and inspected reports pass |
| R03 | Fresh approved-account rollback baseline, immutable prompts/corpus and reusable audited image verified |
| R04 | Exact two-property, one-Runtime no-replacement update; READY/live versions agree; surrounding state preserved |
| R05 | All seven real UI results and required routing/moderation behavior pass in two fresh conversations |
| R06 | All required source controls/retained associations and four actual UI downloads pass |
| R07 | Correlated hybrid execution, twelve retrieval paths, bounds and output/save behavior established |
| R08 | Retain/recover decision, closeout publication/CI, owner preservation and owned cleanup verified |
| R09 | No unapproved inference/mutation, no image rebuild/push, and no benchmark/demo |

Every unmet criterion must remain explicit. Fixture success does not satisfy R05–R07. No semantic-quality, latency or dollar-saving claim follows from this bounded compatibility trial.

## 10 Approval and preparation record

**Approval requested:** Implement and verify the three tooling/test files with local simulated services; publish the exact eight-path release and documentation-only closeout to draft PR #1; perform bounded readiness reads; reuse the audited image for one narrow Runtime update; execute seven new attempted real requests, ≤18 source opens/reopens and four downloads; inspect bounded traces; allow one necessary owned UI restart and one conditional rollback; complete cleanup. No build/push or Docker recovery is included.

No unresolved product choice is needed. Fresh access, service state, ports and image availability are execution prerequisites. Unexplained drift or a failed gate stops dependent work.

Preparation inspected local Git status/history, the prior PRD/final receipt, UI source boundaries, installed CLI help and existing dependency configuration. It added this PRD only. No implementation, regression/fixture execution, browser session, publication, AWS request, deployment or paid Runtime request was performed for this recovery scope.

## 11 Execution record — Gate A

The owner approved both gates with “approve.” Gate A A01–A08 passed on 2026-10-19. The full credential-free UI suite passed 50 tests: 32 existing and 18 new acceptance regressions. Installed Node v22.22.0 / Playwright CLI 0.1.22 compiled complete `async (page) => { ... }` functions before dispatch. CLI entry SHA-256: `fda252270793401d2856530a5f503adf7fc326fc07bed97e413138f67c50662b`.

One initial fixture round and two local tooling repairs completed exactly seven mock sends in two distinct backend conversations, 14 source opens/reopens and four actual UI downloads. The two repairs handled PDF text loading after its heading and Chainlit's observed “Create New Chat” confirmation dialog. Neither repair submitted an extra question. All four original byte hashes matched section 6.1. One private fixture screenshot was inspected. The audit checked 156 text artifacts without finding an unredacted session/source URL; the fixture recorded zero AWS/external-service attempts.

Only owned browser/listeners, the short fixture stage and incidental generated root Chainlit files were removed after process/path/reparse checks. The existing 8010 UI remained running. Application, dependencies, API, IaC, corpus and the owner's warning document matched their baseline hashes. Frozen helper/test hashes and full sanitized receipts are retained in the ignored `restaurant-finder-api/.generated/hybrid-recovery-20261019021936/` evidence root. This fixture pass does not satisfy live R05–R07. Gate B preflight/publication and live acceptance are pending at this release checkpoint.

## Recovery closeout — FAILED / RECOVERED

The approved recovery published tooling release `e4d147ef660e9348c6c08e8013dab92e4e80d46e` to the existing draft PR. Both automatic exact-head [pull_request CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39192404885), [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39192402121) passed all four jobs. Downloaded artifacts verified 290 API, 50 UI and 55 infrastructure tests, all five unchanged report hashes, 28 conversation variants/63 turns and 57 retrieval variants/1,070 checks. Gate A A01–A08 passed; its mock results remain separate from live evidence.

Fresh preflight verified the nine pinned prompt versions, four original hashes, six-source generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a`, guardrail `ih5xpt3qi946:1`, IAM and reusable audited image. Candidate OCI index `sha256:d755be05db461862c57ac4c90957bd648dc2932804b278f1b916fe74c7526b19` / ARM64 child `sha256:031b5125231617d312bb53c50d3e1b772b7a9ef9c885f6a0e3e3aaef7e116892` / config `sha256:321233bfe98e7b0f61c85d7397027bdaa8d63f82347fe5f549a293e5f7fc1288` were reused without any Docker operation, build or image push.

One reviewed no-replacement update changed only the image URI and `RAG_RETRIEVAL_MODE=hybrid`, reaching matching READY Runtime/DEFAULT 20. The frozen controller submitted **L1 exactly once**. Its completed answer quoted “Mushroom pasta - RM32 per serving” and cited Harbor menu v2/page 1, but omitted **“Contains wheat and milk.”** The native PDF viewer visibly retained the complete source record. L1 therefore failed the agreed full-record criterion. L2–L7 stayed UNUSED; no resend, alternate question, other conversation, benchmark or demo was performed. There were zero manual live source opens/reopens or original downloads, and one private live screenshot. The requested four live UI downloads and retained-link matrix remain unverified; preflight/fixture copies do not replace them.

Bounded reads of the three known log groups used two pages per group (40/16/32 observed events); no delayed reconciliation was needed. Forty unique spans established one correlated Jev document route (`jev-1.13.0`), input moderation, fresh embedding/vector/selection, one `rag.keyword_rank` / `rag.fuse` pair with `hybrid` / `bm25-rrf-v1`, the correct Harbor/generation scope, one vector and one keyword candidate, union/overlap/returned count one, and 349 context characters. Final output was approved with no moderation change; memory save followed. The twelve-path/seven-request trace criterion remains unmet. No semantic-quality, keyword-only recovery, latency or dollar-saving result is established.

The existing single-question renderer validates a selected quote as an exact substring (`workflow.py`, `render_answer`). Unlike resolved continuations, the ordinary single-question path does not call the complete-task selection validator. This code boundary is consistent with the observed partial record surviving validation. The next application repair should enforce complete supported menu/policy records in ordinary single-question answers and add deterministic truncation regressions; it requires a new implementation/rollout scope. No prompt or application repair was made in this recovery.

One reviewed conditional rollback restored the fresh baseline image and removed the previously absent retrieval-mode key. Runtime/DEFAULT are READY **21**. Full template equality, all 18 resource mappings/outputs, surrounding Runtime fields, pinned guardrail/IAM and corpus were reverified. The existing 8010 UI was reused throughout, with no restart or credential-file edit; the recovered application was not invoked. The owned acceptance browser was closed. Durable tooling remains tracked; private evidence and the owner's warning document are preserved. Final documentation-only commit/CI and incidental-script cleanup are recorded after publication in ignored receipts and the PR body.


### Final criterion disposition

| Criterion | Result |
| --- | --- |
| R01 | PASS — Gate A and frozen helper/test provenance |
| R02 | PASS — exact eight-path release; both CI artifact sets inspected |
| R03 | PASS — fresh baseline, pinned prompts/corpus and audited existing image |
| R04 | PASS — narrow update reached READY 20 with preservation verified |
| R05 | FAIL — L1 omitted required qualifiers; L2–L7 UNUSED |
| R06 | UNMET — full live source/download/retained-link matrix not executed |
| R07 | UNMET — one correlated retrieval path verified; twelve required |
| R08 | Recovery verified; final closeout CI/cleanup recorded in later receipts/PR |
| R09 | PASS — one live attempt, one forward/rollback; no rebuild/Docker/demo |

The deployment is FAILED / RECOVERED. Gate A and safe recovery succeeded; hybrid live acceptance did not pass. No unused slots may be reused from this stopped matrix.
