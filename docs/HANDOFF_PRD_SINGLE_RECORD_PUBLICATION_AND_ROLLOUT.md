# Handoff PRD for complete document answers publication and rollout

**Status:** Live acceptance PASS; READY Runtime/DEFAULT 22 retained with hybrid retrieval. Release/CI, audited image, all seven UI requests, fourteen citation opens/reopens, four original downloads and required traces passed. Documentation closeout CI and final owned cleanup are recorded in later ignored receipts and the existing draft PR body.

**Prepared:** 2026-10-19, Asia/Kuala_Lumpur.

**Outcome:** Publish the verified record-completeness repair, deploy a new audited ARM64 image with hybrid retrieval, and verify complete answers, clickable originals, conversation follow-ups and correlated execution through the existing UI. Keep the accepted baseline recoverable. Stop before the demo walkthrough.

**Audience and purpose:** The project owner and executing engineer preparing the AI engineering portfolio extension. The previous live trial exposed an incomplete quotation despite a correct retrieved source; this rollout verifies the local repair under the deployed workflow.

**Definition of done:** The exact release and CI artifacts pass; its packaged code and nine pinned prompts match an audited image; a narrow Runtime update preserves surrounding configuration; all seven UI requests, source inspections, four original downloads and required traces pass; closeout and owned cleanup are complete. A failed trial must be reported as failed, with the conditional recovery result separately recorded.

## 1 Problem and chosen release

The previous live L1 answer returned `Mushroom pasta - RM32 per serving` and omitted `Contains wheat and milk.` The native PDF retained the full record. The trial stopped and restored the prior image and absent retrieval-mode key at matching READY Runtime and DEFAULT version 21. L2–L7 were unused and the old attempt ledger was closed.

The approved [local repair](HANDOFF_PRD_SINGLE_DOCUMENT_RECORD_COMPLETENESS.md) now completes an authentic shortened selection from its same already retrieved, verified record before strict validation. It preserves source identity and final moderation. It adds no completion model call, retrieval or embedding. Unsupported boundaries, conflicts and fabricated selections fail safely; insufficient evidence stays an abstention. Strict continuation behavior remains unchanged.

This rollout uses that completed code. It includes no further application repair. The old `hybrid-retrieval-22f8d9c-20261019013820-arm64` image predates the fix and cannot replace the new candidate.

## 2 Verified local starting point

Repository root: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.

| Item | Inspected value |
| --- | --- |
| Branch | `feat/document-multipart-rollout` |
| HEAD | `0dc57694b0a5efc863ba18c4b6beafed5813a88d` |
| Origin | `https://github.com/yukangzhen/restaurant-finder.git` |
| Existing draft PR | [PR 1](https://github.com/yukangzhen/restaurant-finder/pull/1), expected base `feat/jev-router` |
| Repair state | Ten uncommitted repair paths; all ten working-file hashes match the final local receipt |
| Local acceptance | S01–S08 PASS; 322 API, 50 UI and 55 infrastructure tests passed |
| New regressions | Thirty-one record tests and one independent evaluator mutation test |
| Gold changes | Twelve expected quote fields in eleven cases; simulation inputs unchanged; other four datasets unchanged |
| Prior cloud state | Last verified READY Runtime/DEFAULT 21, recovered image, retrieval-mode key absent |
| Owner work | Untracked `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`; preserve and exclude |

Local evidence: `restaurant-finder-api/.generated/single-record-20261019041108/`. Inspect `final-verification.json`, `verification.json`, `gold-changes.json`, `examples.json`, `report-comparison.json`, logs and cleanup receipts. The final receipt records 173 protected files unchanged and zero external calls. Operational helpers and their short stage were removed; do not assume those scripts still exist.

| Offline report | Cases | Checks | Additional coverage |
| --- | ---: | ---: | --- |
| Document RAG | 17 | 374 | Strengthened independent complete-record gold |
| Comparison | 20 | 260 | Existing behavior preserved |
| Multipart | 40 | 609 | Existing behavior preserved |
| Follow-ups | 24 | 1,147 | Twenty-eight variants, sixty-three simulated turns |
| Retrieval | 24 | 1,070 | Fifty-seven variants |

These are inspected local results. Fresh GitHub CI and AWS health must be established during execution. Compare report structure/content and normalized line endings; Windows CRLF and Linux LF need not have equal raw hashes.

The [previous recovery record](HANDOFF_PRD_HYBRID_RETRIEVAL_RECOVERY.md) and `restaurant-finder-api/.generated/hybrid-recovery-20261019021936/final-verification.json` record FAILED_RECOVERED, one failed L1, six unused slots and completed recovery/cleanup. Preserve that history.

## 3 Scope and authorization

After sign-off, execute these gates in order. Approval covers the specified publication, ordinary service charges, one image, one conforming forward update, the fresh bounded live trial, one conditional rollback and documentation closeout. A conforming reviewed change set needs no repeated approval. Unexpected changes, additional paid attempts or Docker recovery need a new decision.

### 3.1 Exact release allowlist

Publish these ten repair paths plus this PRD, exactly eleven paths. Stage explicit paths and inspect the staged diff; do not use blanket or wildcard staging.

~~~text
README.md
docs/CI_AND_RAG_EVALUATION.md
docs/DOCUMENT_RAG.md
docs/HANDOFF_PRD_SINGLE_DOCUMENT_RECORD_COMPLETENESS.md
docs/HANDOFF_PRD_SINGLE_RECORD_PUBLICATION_AND_ROLLOUT.md
restaurant-finder-api/src/application/document_rag/comparison.py
restaurant-finder-api/src/application/document_rag/single_record.py
restaurant-finder-api/src/application/document_rag/workflow.py
restaurant-finder-api/src/evaluation/datasets/document_rag.json
restaurant-finder-api/tests/test_document_single_records.py
restaurant-finder-api/tests/test_rag_evaluation.py
~~~

Before publication, this PRD may record completed preflight results. Do not alter the ten verified repair inputs during rollout. Record Git normalization explicitly before comparing committed bytes to working-file hashes.

Closeout may update only these five documents: `README.md`, `docs/CI_AND_RAG_EVALUATION.md`, `docs/DOCUMENT_RAG.md`, `docs/HANDOFF_PRD_SINGLE_DOCUMENT_RECORD_COMPLETENESS.md` and this PRD. All application, dataset, test, UI, dependency, infrastructure and workflow bytes must equal the release during closeout.

### 3.2 Preserved boundaries

Preserve prompts and immutable versions, guardrail/IAM configuration, corpus/pointer/originals/index, dependencies/locks, UI application and acceptance tooling, infrastructure code, workflows, anonymous identity behavior, real environment files, prior failures and owner work.

Exclude prompt synchronization, ingestion, new functionality/tests, provider/model substitution, IAM/guardrail changes, other stack deployment, image deletion/pruning, tag overwrite, new PR/merge/force-push/upstream publication, workflow dispatch/Actions changes, benchmarks and the demo walkthrough. Code or tooling defects discovered here require a separate repair scope.

## 4 Deployment and preservation identities

Cloud values below are historical expectations and require fresh verification before mutation.

| Item | Expected baseline |
| --- | --- |
| AWS profile / account / region | `default` / `447393541969` / `us-east-2` |
| Identity | Authorized non-root identity; last verified IAM user `kangzhen` |
| Stack | `restaurantFinder-AgentCoreStack` |
| Runtime logical ID | `restaurantFinderAgentCoreRuntime` |
| Runtime ID | `restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime / DEFAULT | Last verified READY 21 / live version 21; measure current state |
| Accepted flags | Multipart true, follow-ups true, RAG enabled, top-k 5 |
| Retrieval mode | Key absent at last recovery; capture exact current presence/value |
| Guardrail | Immutable `ih5xpt3qi946:1` |
| Existing UI | `http://127.0.0.1:8010/`, AWS mode, DEFAULT Runtime |
| ECR repository | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent` |
| Resources | Previously eighteen physical resource mappings; capture full current mappings and outputs |

### 4.1 Recoverable image

| Identity | Last recovered baseline |
| --- | --- |
| URI | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:document-followups-11590ea-20261014082247-arm64` |
| OCI index | `sha256:fe3763ab8be2b66a3c7e3b99b25d1cab14c6bdc6dc52532c4b12ab1ac1866163` |
| Runnable linux/arm64 child | `sha256:258c7d60a341c20df5cf8954618d5e5e18dcf302a088c33aa50f6925862dfd9b` |
| Config | `sha256:722a0dd0b52a065ba8b1a4607f1e2a277172789a6f798bd9b04f100c0e47e9a0` |

Capture fresh rollback authority from the currently deployed stable template and Runtime configuration. Reconcile differences from this record before publication/deployment; do not silently select an older baseline.

Read actual ECR lifecycle policy and manifest inventory. Previous inventory contained eighteen manifests and the rollback index was ranked fourth under an any-image keep-ten policy. Tags are not the lifecycle count: indexes, runnable children and attestations differ. Prove adding the new image preserves a fetchable rollback graph, then verify after push. Do not change retention or add protection tags in this scope.

### 4.2 Pinned prompts and policy fingerprints

Use `restaurant-finder-api/.generated/multipart-rollout-20261013032223/nine-prompt-manifest.json`, SHA-256 `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9`. This rollout adds no prompt.

| Existing canonical projection | Expected SHA-256 |
| --- | --- |
| Guardrail effective policy | `cbf24512ff86fcd0187d95424e868d0f4b5ee1199515bdd4b06363ccdfad176d` |
| Guardrail Runtime inline policy | `6ff2a7301b03e26308a4a8c10a12716c57205775e7f0472c168818a527c80eaa` |
| Two inline-policy documents combined | `bdd6fafd298761b8d4250b8b472adfbe1d52ab30bda5369d1de86d6082c6855d` |

Reuse previously verified projection definitions and sorted compact UTF-8 JSON. Also privately compare full effective IAM trust, inline/attached policies and permissions boundary. Exclude volatile response metadata without discarding effective configuration. An unexplained difference stops dependent work.

### 4.3 Corpus

| Item | Required identity |
| --- | --- |
| Bucket | `restaurantfinder-ragstack-documentbucketae41e5a9-vqrmcnuycjq5` |
| Active pointer | `rag/active.json` |
| Generation | `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` |
| Pointer ETag | `"d3705246c1cc2a4fd7f694bc91553e95"` |
| Manifest | `rag/generations/<generation>/manifest.json`; six originals |
| Index ARN | `arn:aws:s3vectors:us-east-2:447393541969:bucket/restaurantfinder-rag-447393541969-us-east-2/index/documents-titan-v2-512` |
| Embedding/index settings | Titan V2, 512 dimensions, float32, cosine |

## 5 Operation and cost limits

| Operation | New allowance after sign-off |
| --- | --- |
| Publication | One eleven-path release commit/push and one documentation closeout commit/push to the same draft PR |
| CI | Inspect automatic push and PR checks/artifacts for each exact head; no manual reruns/dispatch |
| Build | One initial linux/arm64 build and at most one reconciled retry before image publication, on unchanged source/manifest |
| Image publication | One successfully audited unique tag and one intended push; reconcile uncertain delivery before further action |
| Forward / rollback | One reviewed forward UPDATE execution; at most one conditional reviewed rollback execution |
| Real agent requests | Seven reserved dispatch attempts, L1–L7, in two fresh conversations; no automatic resubmission |
| Failed requests | Errors, blocked/masked answers, timeouts and uncertainty consume the reserved slot; stop at first failed/unverified requirement |
| Other inference | Zero greetings, warm-ups, standalone guardrail probes, live evaluators, ablations or post-rollback requests |
| Originals | Four unique preflight originals, each at most 5 MiB; inspect six manifest identities; four actual UI download attempts |
| Citation actions | At most eighteen manual opens/reopens, allocated below; automatic first-source display is separate |
| Screenshots | At most eighteen private live screenshots |
| Prompts | One read-back per nine immutable versions; one final metadata reconciliation only if needed |
| UI | Reuse; at most one necessary owned restart and one rollback restoration if this phase changed it |
| Readiness polling | Every 15–30 seconds, at most twenty minutes per update; blocking waits at most sixty seconds |
| CI polling | Every thirty seconds or longer, at most thirty minutes per publication |
| Trace reads | Acceptance window plus/minus sixty seconds; ten pages of up to 1,000 events per relevant group, across initial reads and one delayed reconciliation |
| Docker recovery | No Desktop restart, WSL reset, pruning or unrelated termination; obtain a separate scoped decision |

Seven sends is a user-attempt limit, not seven underlying AWS calls or a dollar cap. Requests can invoke Jev, Bedrock/guardrails, Titan, S3 Vectors, storage, AgentCore/checkpoints/memory and logs. Builds, registry/storage, reads and CI can also incur ordinary charges. No credit-balance or cost-saving claim is implied.

## 6 Gate A Freeze readiness and publish the repair

### Step 1 Record approval and preserve local inputs

1. Record approval of this exact scope, including cost bounds and conditional rollback. Preparation approval alone does not authorize execution.
2. Create an owned ignored evidence root such as `restaurant-finder-api/.generated/single-record-rollout-<UTC timestamp>/` and a short export directory under the task's `tmp`. Record resolved paths and cleanup ownership.
3. Re-read status, branch, HEAD, remotes and all eleven paths. Require ten repair hashes from `single-record-20261019041108/final-verification.json`; record this PRD separately. Reconcile new changes before staging.
4. Hash protected inputs and owner work, including UI/helper/fixture/tests, prompts/manifest, dependencies, other datasets, infrastructure/workflows and originals. Preserve previous private evidence and real environment/credential files.
5. Restrict the new private evidence directory to the current user and SYSTEM for rollback configuration, downloads and screenshots. Do not broaden existing private ACLs. Keep tokens in memory.

**Pass condition:** Exact package/protected baseline recorded; zero new live attempts or cloud mutations.

### Step 2 Establish access and capture fresh rollback authority

1. Inspect existing tools/interpreters, Node/CLI, Docker/buildx and AWS CLI. Do not install/upgrade tools. Bounded Docker reads must establish a usable Linux engine before the build gate. If unavailable, stop for the owner's recovery decision.
2. Run `aws sts get-caller-identity --profile default --region us-east-2`. Require the expected account and authorized non-root identity. If expired, ask the owner to finish `aws login --profile default`; do not rewrite profiles or infer identity from an alias.
3. Read stable stack template, parameters/capabilities, resources/outputs, Runtime and DEFAULT. Privately capture exact rollback authority and mode-key presence/value. Require stable matching READY versions and section 4 agreement, or reconcile drift before continuing.
4. Read ECR index/child/config, tag settings, actual inventory/lifecycle policy and rollback fetchability. Prove retention remains safe for one new image graph.
5. Read guardrail version and effective IAM configuration; verify fingerprints and full preservation baselines. No ApplyGuardrail/model call belongs in readiness.
6. Read pointer, manifest and index metadata. Require section 4.3. Fetch only the four section 8.2 originals, close bodies and verify bytes/hash/full records. Record all six manifest identities.
7. Read each of nine immutable Bedrock CHAT versions once. Match IDs/versions/ARNs, system text, user placeholder and variables to the retained manifest/local definitions. Read local text as UTF-8, including named strings and inline `Prompt(prompt=...)` definitions. Do not synchronize on failure.
8. Identify the 8010 listener through fresh PID/start-time/command/cwd/source proof. Verify UI bytes/interpreter, AWS mode, DEFAULT ARN, profile/region, bucket/viewer and existing identity behavior without dumping the environment. Capture restoration inputs; preserve any backing source tree.
9. Verify GitHub identity `yukangzhen`, origin head and PR 1 draft/head/base. Require remote-parent agreement; browser login alone is insufficient. Inspect workflow triggers: this branch should run offline CI, while deployment workflows target `main` or manual dispatch. Preserve triggers.

**Pass condition:** Access, immutable dependencies, stable state and recoverable rollback graph verified. Readiness makes no Runtime, model, embedding or QueryVectors request. Wrong account, unexplained drift, missing authority or unknown ownership stops publication/deployment.

### Step 3 Publish exactly eleven paths and inspect CI

1. Reconcile remote head immediately before staging. Inspect full local/staged diffs and `git diff --cached --check`; require section 3.1 only, with no owner/ignored material. Use configured Git author identity.
2. Make one release commit and normal origin push. Record SHA/parent/paths and read back remote SHA. Reconcile uncertainty instead of duplicating commits/pushes or force-pushing.
3. Update the existing PR body with actual repair/local evidence and planned rollout, preserving title/base/draft and historical sections. Use a structured argument or exact body file with real newlines. Attach the PR through the app artifact tool.
4. Inspect automatic push/PR CI for the exact release, including merge-ref association. Require API, UI, infrastructure and aggregate quality jobs. Do not accept another head's green run.
5. Download/inspect artifacts and logs: expect 322 API, 50 UI, 55 infrastructure tests and all five complete reports with section 2 coverage. Inspect actual outcome/check/variant counts and missing/unmeasured fields; investigate differences. Parse JSON and normalize line endings instead of requiring raw Windows hashes.
6. Record run URLs, artifact identities/hashes and source associations. Missing/failing CI stops before image publication. No code repair, weakened gold, manual rerun or Actions change is included.

GitHub CLI was previously absent. Reuse existing authenticated tooling; the established fallback is Git Credential Manager into process memory followed by structured API requests. Never print/store tokens or place them in URLs/arguments. AWS CLI exported credentials may likewise enter SDK memory without credential files/global edits.

**Pass condition:** Exact release and automatic CI evidence pass. This SHA remains image source authority after documentation closeout.

## 7 Gate B Package and deploy the candidate

### Step 4 Export committed inputs and validate packaging

1. Export exact API Git blobs from the release into clean short staging. Export committed infrastructure separately for synthesis. Do not build from the working API tree containing ignored private evidence.
2. Compare exported paths/hashes to the release tree. Reconcile LF normalization against unchanged approved working inputs; allow no semantic difference. Do not copy real `.env`, caches or reports.
3. Add only the retained manifest as API-stage `.generated/prompt-manifest.json`, preserving section 4.2's hash. No surrounding `.generated` directory belongs in the context.
4. Run staged `python -m src.deployment.validate_prompts` using the existing locked interpreter, absolute staged manifest, `REQUIRE_PROMPT_MANIFEST=true`, `PROMPT_SYNC_MODE=false`, metadata credentials disabled and evaluation/export disabled. Require nine valid prompts and exit zero. This is local validation; never start `src.main` for an audit.
5. Choose an absent unique tag `single-record-<release SHA first 7>-<UTC timestamp>-arm64`. Distinguish NotFound from denied/unavailable reads. Never use `latest` or overwrite tags.
6. Compile/synthesize committed infrastructure with installed dependencies, no lookups and owned output, using these explicit contexts:

~~~text
imageUri=<unique candidate URI>
documentMultipartEnabled=true
documentFollowupsEnabled=true
ragRetrievalMode=hybrid
guardrailId=ih5xpt3qi946
guardrailVersion=1
~~~

Resolve placeholders before use. Synthesis verifies provenance; the fresh deployed template controls the narrow update. Do not deploy all stacks.

### Step 5 Build and audit one new ARM64 image

1. Build the clean API export with unchanged Dockerfile/lock. Record base/build metadata; its mutable base tag does not guarantee identical future rebuilds.

~~~text
docker buildx build --platform linux/arm64 --load --label org.opencontainers.image.revision=<release SHA> --metadata-file <owned metadata file> --tag <unique URI> <staged API root>
~~~

2. After timeout/engine loss, reconcile image completion before the one allowed retry. Retry only before image publication on unchanged source/manifest. A second failed build or changed inputs stops the allowance. Docker recovery itself needs a separate decision.
3. Require linux/arm64 and exact revision label. Dockerfile configures `USER bedrock_agentcore`; verify passwd mapping/effective audit UID 1000. The config User string need not literally be `1000`.
4. Require normal command `["opentelemetry-instrument", "python", "-m", "src.main"]`. Audit with entrypoint overridden, `--network none`, no credentials and no agent startup.
5. Derive expected packaged paths from committed inputs and unchanged Dockerfile/ignore rules. Compare every included source/config/dataset byte and the sole manifest, specifically new `single_record.py` and changed `comparison.py`/`workflow.py`. Recompute counts; the old ninety-file image count is not the new target.
6. Verify no real `.env`, secrets, private reports, downloads, helpers, tests or sample originals. `.env.example` is allowed. Docker ignore does not exclude every `.generated` path; clean export is essential.
7. Record audit results and image identity. Local Docker image ID can identify an OCI index; do not confuse it with registry config digest.

**Pass condition:** One successfully audited new image contains intended committed runtime bytes/pinned manifest, with no agent invocation.

### Step 6 Publish the image and review the proposal

1. Authenticate only to existing ECR using stdin/memory. Restrict any temporary Docker auth to current user, preserve global configuration and clear it in `finally`.
2. Push the audited unique image once; reconcile uncertainty through registry reads before further action. Record index, runnable ARM64 child and config separately, distinguishing attestations. Require the registry chain to match audited content.
3. Recheck post-push inventory/lifecycle exposure and baseline graph fetchability. Stop cloud mutation if recovery is uncertain; do not alter retention/delete images.
4. Copy the fresh deployed template and change only these leaves:

~~~text
Resources.restaurantFinderAgentCoreRuntime.Properties.AgentRuntimeArtifact.ContainerConfiguration.ContainerUri
Resources.restaurantFinderAgentCoreRuntime.Properties.EnvironmentVariables.RAG_RETRIEVAL_MODE
~~~

Set the new audited URI and string `hybrid`. Restore both leaves to baseline presence/value in a comparison copy and require full parsed equality. Preserve parameters/outputs/resources, flags, guardrail, model/embedding settings, policies and every other Runtime property.

5. Create one named UPDATE change set with existing parameter values/capabilities. Inspect the full proposal: exactly one existing Runtime Modify, replacement false, no create/delete/other effective changes; property details confined to artifact/environment with no recreation demand.
6. Record template hash, change-set identity and review. Recheck live baseline and image graphs immediately before execution. Unexplained concurrent drift/broader proposals need a new decision; approval covers conforming proposals only.

### Step 7 Execute once and verify readiness

1. Execute once. Reconcile uncertain responses by reading state, without blind re-execution.
2. Poll within section 5 limits. Require UPDATE_COMPLETE, exact candidate/hybrid mode and matching READY Runtime/DEFAULT live version. Record observed versions; do not predict version 22.
3. Compare deployed template to proposal, mappings/outputs, surrounding Runtime fields and fresh IAM/guardrail/corpus baselines. Recheck rollback availability.
4. Reuse the verified UI. If one restart is necessary, prove ownership, preserve restoration and stop only that process. Start committed UI with the existing interpreter, loopback 8010 and explicit required AWS/source settings, using `Start-Process -WindowStyle Hidden`. Preserve environment files/unrelated listeners.
5. Verify listener/HTTP readiness without an agent message. If a mutation was attempted and readiness/preservation cannot be established, enter section 10's recovery decision.

**Pass condition:** Conforming deployment and UI ready; zero live L-slot attempts.

## 8 Gate C Execute the fresh live matrix

### 8.1 Freeze the sequential acceptance helper

Reuse tracked `restaurant-finder-ui/acceptance.py`, `tests/test_acceptance.py` and `tests/fixtures/hybrid_acceptance.py`. Fifty-test UI CI includes eighteen helper regressions. No new helper implementation/fixture round is included.

Inspected helper SHA-256: `ad459079e6bdff541cdccad85904c2006870ce5f0c2d35bf2c8f60f007d109e0`. Freeze helper/test/fixture hashes against the release and installed CLI identity. Previously verified CLI: `C:/Users/kinoc/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js`, version 0.1.22, SHA-256 `fda252270793401d2856530a5f503adf7fc326fc07bed97e413138f67c50662b`. Recheck current identity without downloading a replacement.

1. Read applicable browser skill/current CLI interface. Use one owned isolated session with helper-required `hybrid-*` naming; preserve unrelated sessions/tabs.
2. Create a new private live ledger with current `MATRIX_HASH`, helper hash, approval reference, `preflight_verified=true`, `live_allowed=true`, seven UNUSED slots and counters zero. Never reopen old ledgers/carry old allowances. Close this ledger on completion or stop.
3. Use the durable helper: it compiles complete `async (page) => { ... }` functions before dispatch. Top-level `await page...` is not this CLI interface.
4. Inspect fresh snapshots/observed controls. Known textbox name `Type your message here...`, send `chat-submit` and New Chat `new-chat-button` require confirmation. `Controller.new_chat` handles the observed Create New Chat confirmation dialog.
5. Before Enter, require one enabled textbox/send, exact filled-text read-back and no pending request. Reserve the slot durably/exclusively before its one send. Failed preparation must not fall through to a separate Enter command.
6. Mark PASS only after final answer, moderation-visible outcome and source controls satisfy the slot. Failure/uncertainty consumes the attempt; no resend/rewording. Failed seeds forbid dependent turns. Stop at first failed/unresolved required result.

### 8.2 Original source gold

Fresh manifest/preflight bytes and actual UI downloads must match these identities. Do not revise expected facts after observing answers.

| Original | Version / bytes | SHA-256 | Complete record/location |
| --- | --- | --- | --- |
| `harbor-menu-v2.pdf` | v2 / 1,975 | `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10` | PDF page 1; mushroom pasta RM32 per serving; contains wheat and milk |
| `harbor-policy.md` | v1 / 534 | `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471` | Reservations and cancellation, lines 5–8; free at least 24 hours before booking; later RM20 per booking |
| `sakura-menu.md` | v1 / 383 | `0ac797361e4fc9abc433685b26693e6d877ed6ad873c94110cd0e3a7be7e9637` | Main dishes, lines 5–11; mushroom pasta RM36 per serving; wheat/milk; dinner only |
| `sakura-policy.md` | v1 / 466 | `e61b5aa2a3c6969061866379a754fbd7a3d07aef4e82a39c5dc89ddea4c6668f` | Reservations and cancellation, lines 5–8; free at least 12 hours before booking; later RM15 per booking |

Exact Harbor menu record: `Mushroom pasta - RM32 per serving. Contains wheat and milk.` Exact Sakura menu record: `Mushroom pasta - RM36 per serving. Contains wheat and milk. Available at dinner only.` Require complete controlled records, qualifiers and both cancellation conditions; price/fee numbers alone are insufficient.

### 8.3 Seven exact requests

Create fresh backend conversations A/B using New Chat. Preserve anonymous identity behavior; new conversations do not prove authenticated isolation.

| Slot | Conversation | Exact text | Required answer/workflow |
| --- | --- | --- | --- |
| L1 | A1 | `According to Harbor Pasta Lab's menu, what is the mushroom pasta price?` | Complete RM32/serving record with wheat/milk; one to three relevant Harbor menu selections/source controls; no unrelated item claim |
| L2 | A2 | `According to Harbor Pasta Lab's policy, how much notice must I give to cancel without charge, and what is charged if I cancel too late?` | Full policy: free at least 24 hours before booking, later RM20 per booking; one to three relevant selections covering the complete controlled record |
| L3 | A3 immediately after L2 | `And what about its cancellation fee?` | Deterministic Harbor continuation, fresh full 24-hour/RM20 policy, one source; no router/rewrite inference |
| L4 | A4 | `According to Harbor Pasta Lab's documents, is valet parking available?` | Insufficient evidence, no invented availability/new citation; scoped retrieval/selection still occur |
| L5 | B1 fresh chat | `Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources.` | Full RM32/RM36 records, serving units, allergens/Sakura dinner-only qualifier; Harbor cheaper by RM4; two scoped menu sources |
| L6 | B2 immediately after L5 | `Which is cheaper?` | Deterministic continuation, fresh both-venue retrieval, full records/RM4 difference; two new sources; no router/rewrite/planner inference |
| L7 | B3 immediately after L6 | `What about both restaurants' prices and cancellation policies?` | Deterministic continuation into four-task multipart work; full menus/both full policies, four originals, one planner and at most two active workers |

L1/L2/L4/L5 require ordinary Jev document routing; existing Bedrock fallback is permitted only if evidenced. L3/L6/L7 require `document_followup`. All seven require input moderation and unchanged approved final output. Blocked/masked/incomplete answers do not pass.

Complete each dependent sequence without unrelated messages. Check final text/control association before the next turn; defer lengthy source viewing/downloads until that conversation ends. Do not inject context, switch providers, loosen completeness or use remaining slots as probes.

### 8.4 Inspect clickable originals and downloads

After A1–A4 pass:

1. Open every L1/L2 source plus L3's one, at most seven actions. Confirm L4 adds none.
2. Reopen the first L1 control after later answers, one further action; verify retained answer/document/version/location association.
3. Download Harbor menu and policy once each through actual UI original-download controls.

After B1–B3 pass:

1. Open L5's two, L6's two and L7's four sources, eight actions.
2. Reopen both L5 controls after L7, two further actions; verify retained associations.
3. Download Sakura menu and policy once each through actual UI controls. Reuse Harbor download bytes for repeated Harbor references.

Total at most eighteen attempted opens/reopens and four download attempts; reserve counters separately. Stop on unverified required sources/downloads. Preflight copies, fixtures or backend-only GETs cannot replace live UI downloads.

Check original bytes/hash, filename/version/generation and page or section/lines. Native PDF must display its real page/full record; Markdown must show the complete numbered section. Wait for content, not a panel heading: use existing `read_source(name, required_fragments)` after opening. Previously observed PDF loading required this wait. Reconcile viewer delay from current state without another agent request.

Use fresh accessible names, such as `Source 1 (answer 1)` and its `original` link. DOM icon text/accessibility names can differ. Automatic first-source display does not establish all inspections, retained links or downloaded bytes.

## 9 Gate D Verify correlated execution

1. Record safe trace/span correlations and acceptance start/end without persisting session/conversation identities. Confirm presence of historical groups `aws/spans`, `/aws/vendedlogs/bedrock-agentcore/restaurantFinder-telemetry` and `/aws/bedrock-agentcore/runtimes/restaurantFinder_Agent-Ha58oX5Psu-DEFAULT`. `aws/spans` has no leading slash.
2. Read bounded window/known correlations within shared page cap; count empty/repeated-token pages. One delayed reconciliation may use remaining allowance; no request is permitted to improve telemetry.
3. Require four ordinary document routes and three deterministic follow-ups, identifying actual Jev/fallback behavior. L3/L6/L7 avoid router/rewrite inference; L6 also avoids planner inference.
4. Require twelve logical retrieval paths: four singles L1–L4, two each for L5/L6 and four L7 paths. Each needs correlated `rag.keyword_rank`/`rag.fuse`, `hybrid`, `bm25-rrf-v1`, correct generation and restaurant.
5. Verify fresh embedding/vector/selection work and bounds per path: vector/keyword counts at most five each, union at most ten, consistent overlap, returned passages at most five, context at most 9,000 characters. Require one L7 planner/at most two active workers.
6. Verify ordinary validation precedes rendering/moderation. Image provenance plus complete outputs establish deployment of the repair; do not invent a completion-specific span/attribute. Distinguish existing ordinary query rewrites, if observed, from completion; no extra selector/retrieval/embedding may be introduced by the repair.
7. Require seven unchanged final output approvals, preserved approved-context/save boundaries and L4 abstention without sources. Separate logical work from duplicated instrumentation, SDK retries and checkpoint CreateEvent spans; those are not durable-memory totals.
8. Parse raw events in memory; retain only safe app attributes/correlations. Inspect standard exporter fields separately. Never publish tokens, raw provider bodies/checkpoints/environments, signed source URLs or session IDs. Screenshots/downloads remain private.

Missing required telemetry/source evidence leaves acceptance incomplete and enters recovery. This compatibility matrix does not establish semantic recall gains, live keyword-only rescue, latency/dollar savings, authenticated isolation or general production readiness. Benchmarking remains skipped.

## 10 Retain or recover once

Retain only after required release/image/readiness, seven requests, sources/downloads, traces and preservation pass. Closeout remains a separate completion criterion.

Conditional rollback is permitted for a failed/unready attempted update, failed answer/moderation/workflow/source contract, or bounded verification unable to establish acceptance.

1. Stop sends, close the ledger and mark attempted/failed/uncertain/unused slots exactly. Preserve safe failure evidence; never reopen the matrix.
2. Reconcile current state/concurrent changes. Do not overwrite another actor. If CloudFormation already restored baseline, verify it instead of executing redundant recovery.
3. Where needed, restore fresh baseline image and exact prior mode-key presence/value. Remove the key if originally absent. Preserve accepted multipart/follow-ups, pinned guardrail and surrounding configuration.
4. Review at most one rollback UPDATE under the same one-Runtime/no-replacement constraints and execute once. Require matching READY Runtime/DEFAULT, baseline template/resources/outputs/settings/IAM/guardrail/corpus and fetchable image. Versions can increase.
5. Restore owned UI only if this phase changed it and restoration is necessary. No request against recovered application is included.
6. Preserve commits/images/originals/failure evidence. Rollback cannot undo publication/charges. Failed/blocked recovery requires a separate decision; no second recovery mutation is included.

Restoration is FAILED_RECOVERED, not accepted hybrid functionality. If no mutation occurred, report the actual stopped gate and zero deployment/live attempts.

## 11 Documentation closeout and cleanup

1. Update only five permitted docs with actual source/image/Runtime identities, CI links, criteria, attempted/unused slots, source/download/trace counts, preservation and retain/recovery. Preserve failed history and distinguish simulations from live evidence.
2. Make one documentation-only normal commit/push to the existing PR. Inspect exact-head push/PR CI/artifacts. Verify non-document trees equal the release; do not rebuild because closeout SHA differs.
3. Record later closeout SHA/CI in ignored receipts and PR body; a commit cannot contain its own future SHA/run. Preserve title/base/draft and unrelated sections.
4. Verify protected/owner files, remote/PR, cloud configuration, guardrail/IAM/corpus and rollback graph. Check new text for secrets/session/source URLs before publication; keep raw configuration private.
5. Close only owned browser/audit containers. Remove only owned scripts, exports, profiles/auth and incidental staging after absolute containment, reparse and fresh process-identity checks. Use native PowerShell literal paths. Never kill by an old PID; PID reuse occurred previously.
6. Preserve evidence, durable helpers/tests, dependencies, prior failures, owner work and trees backing UI. Handle owned junctions separately/non-recursively, preserving their targets. Leave verified UI available where appropriate.
7. Reconcile allowances/cleanup/unmet criteria in the final receipt. Stop before demo; do not start another functionality task automatically.

## 12 Observable acceptance criteria

| ID | Required evidence |
| --- | --- |
| P01 | Approval, ten repair hashes/protected inputs preserved, fresh account baseline/recoverable graph |
| P02 | Exactly eleven paths published to existing draft PR; remote/head/parent verified |
| P03 | Exact-release CI/artifacts pass; observed 322/50/55 tests and complete five reports/variants |
| P04 | New audited ARM64 image includes repair, nine pinned prompts, no private payload, registry digest chain |
| P05 | Two-leaf one-Runtime update; matching READY/live versions; surrounding state preserved |
| P06 | Seven UI requests pass full records, abstention, routes/follow-ups/moderation |
| P07 | Source/retained-link inspections and four actual UI downloads verify originals/locations |
| P08 | Correlated twelve-path hybrid work, bounds, fresh calls/planner/concurrency/save boundaries |
| P09 | Retain/recovery, closeout/CI, protected checks and owned cleanup verified |
| P10 | Limits respected; no unapproved implementation/config/Docker recovery/inference/benchmark/demo |

Use PASS, FAIL, UNMET or NOT_STARTED. Partial execution cannot pass P06–P08. Recovery does not turn failed live criteria into passes. CI failure after deployment leaves P09 incomplete; an application rollback does not repair CI.

## 13 Approval and execution checkpoint

**Approval requested for execution:** Publish exact eleven-path release and documentation closeout to draft PR 1; inspect automatic CI/artifacts; bounded readiness reads; build/audit/push one new unique ARM64 image with one reconciled pre-publication build retry; execute one conforming image-plus-hybrid Runtime update; seven fresh one-shot UI attempts, at most eighteen source opens/reopens and four original downloads; bounded trace inspection; one necessary owned UI restart and at most one conditional reviewed rollback; cleanup. Stop before demo. Docker recovery and broader repairs remain separate decisions.

No product choice blocks this plan. Expired access, engine health, retention, fresh service state and unchanged inputs are execution prerequisites. Historical version 21 cannot replace fresh rollback capture.

**Preparation completed:** Inspected Git, verified ten repair hashes, read local test/report/prior recovery receipts, checked Docker/manifest validation source, workflow triggers, acceptance helper and preservation identities. Added this PRD only. No tests were rerun and no GitHub/AWS/Docker/browser operation, publication, build, deployment or paid request was performed during preparation.

## 14 Execution record

The owner approved this scope with “proceed” on 2026-10-19. Evidence is retained under `restaurant-finder-api/.generated/single-record-rollout-20261019071344/`.

Steps 1–2 passed. All ten repair hashes and 173 protected files match their baselines. AWS identity is the expected non-root user/account; GitHub identity, draft PR/head/base and parent match. Docker Linux engine 29.8.0 is available. The owned UI at 8010 matches committed application/source-viewer bytes after line-ending normalization, uses the expected AWS/DEFAULT configuration, and needs no restart.

Fresh Runtime/DEFAULT are READY 21 with the prior image and absent retrieval-mode key. The complete deployed template equals the previous recovered proposal; all eighteen mappings and outputs were captured. Guardrail and IAM fingerprints/trust match. All nine immutable CHAT prompt versions match the pinned manifest/local text. Corpus pointer/generation/index and six source identities are unchanged; four original hashes and complete PDF/Markdown records were verified. Current registry inventory contains sixteen manifests; rollback index rank four remains below the keep-ten threshold after at most three new manifests. Post-push verification remains required.

No live attempt, publication, image build/push, Runtime mutation or UI restart has occurred at this release checkpoint. The initial UI/index comparisons were reconciled as line-ending normalization and an SDK response wrapper, respectively; effective code/index configuration matched. No application change was made during readiness.

### Publication and image checkpoint

Release `0ec71ad401a70ade4cf8511ea01a8d058a5f125a` published exactly eleven paths to draft PR 1. Both automatic [PR CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39215532168) and [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39215527127) passed all four jobs. Downloaded artifacts confirmed 322 API, 50 UI and 55 infrastructure tests and all five reports equal to the verified local parsed reports, including all variants.

The clean committed export validated nine prompts. Two CDK CLI runs wrote templates but timed out during exit. Running the compiled committed CDK app directly with network blocked exited zero, reported no missing lookup context, and produced a template exactly equal to the first CLI assembly after matching its metadata context. No live template was generated from these assemblies for deployment; the captured deployed template remains the narrow-update authority.

One ARM64 build passed on its first attempt. A network-disabled audit, with the agent entrypoint overridden, verified all 91 packaged files and 80 runtime source files against committed bytes/manifest, UID 1000, configured user `bedrock_agentcore` and the instrumented application command. Candidate tag: `single-record-0ec71ad-20261019071344-arm64`; local OCI index `sha256:231cff888cf55d92296ac4d9d8ab96b9956b00767743cd96242dca0e091c6eb9`. Registry digest-chain verification remains pending.

Initial registry login failed in the Windows native credential helper before a push. The approved owner-only temporary auth-file method avoided that helper and started one image push. Several layers uploaded, but the command timed out after 600 seconds. Read-only reconciliation at 2026-10-19 08:01 UTC confirmed the candidate tag was absent, Docker responded, the exact baseline template/Runtime/DEFAULT 21 remained unchanged, and temporary auth was removed. No change set/execution, UI restart, browser trial or Runtime request occurred.

## 15 Image publication recovery

The owner approved this amendment by selecting “Proceed with one additional image push.” Section 5 originally allowed one intended image push. Keep the audited source/image, existing release and remaining rollout bounds unchanged.

1. Recheck the local image's exact audited index/revision and the registry tag. If the original publication has appeared, require its expected digest chain and continue without another push. An unexpected existing digest stops this scope.
2. If the tag remains absent, allow **one additional `docker push` of the same audited unique image**, with a maximum thirty-minute process limit. Reuse already uploaded layers where Docker supports it. Use owner-only temporary registry auth and remove it in `finally`. No rebuild, source/tag change, overwrite, policy edit or Docker restart is included.
3. Reconcile any uncertain delivery through read-only registry inspection; no further push is allowed by this amendment. A failed recovery stops publication and leaves the existing deployment intact.
4. Only a verified matching registry index/ARM64/config chain and retained rollback graph permit the originally approved remaining deployment, seven-request matrix, source/download checks, traces and conditional rollback to continue.

Ordinary ECR transfer/storage charges can apply. At approval, the seven Runtime attempts were unused. Approval is recorded in the ignored `image-recovery-approval.json`; the actual recovery and later gates follow below.

## 16 Live acceptance and retention

### Image recovery and forward update

The additional push succeeded within its thirty-minute process limit, reusing uploaded layers. An initial recovery preflight timed out before reserving or starting a push; a bounded explicit Linux-engine endpoint check then established the audited local image and absent candidate tag. Exactly one additional actual push was reserved and executed. No rebuild, tag overwrite, credential-helper/global configuration change, Docker restart or pruning occurred. Owner-only temporary registry auth was removed in `finally`.

| Verified candidate | Identity |
| --- | --- |
| Source release | `0ec71ad401a70ade4cf8511ea01a8d058a5f125a` |
| Tag | `single-record-0ec71ad-20261019071344-arm64` |
| OCI index | `sha256:231cff888cf55d92296ac4d9d8ab96b9956b00767743cd96242dca0e091c6eb9` |
| Linux/ARM64 child | `sha256:75815c730d13067f6e9d02caf8487448c5857abcc6d2eafc292c3f3f4a254402` |
| Config | `sha256:a819cf82545130a2ba7f3c5a990c4cb5408ec0257beb3a4ac62dc8ed6b179873` |
| Packaged files | 91 total, including 80 runtime source files and the sole pinned nine-prompt manifest |

Registry manifests/config/rootfs provenance matched the local audit. Post-push inventory contained nineteen manifests; rollback index rank seven remained inside keep-ten and its graph was fetchable. One reviewed/executed `single-record-forward-20261019071344` change set changed exactly the container URI and added `RAG_RETRIEVAL_MODE=hybrid`. The single Runtime Modify required no replacement/recreation. Stack UPDATE_COMPLETE and matching READY Runtime/DEFAULT **22** passed. All eighteen mappings/outputs, remaining Runtime settings, guardrail/IAM and corpus pointer were preserved. The UI was reused without restart.

### Seven-request matrix

| Slot | Actual result |
| --- | --- |
| L1 | PASS — full Harbor RM32/serving menu record, including wheat/milk; one source |
| L2 | PASS — full Harbor free-at-least-24-hours / late RM20-per-booking policy; one source |
| L3 | PASS — deterministic Harbor fee continuation, full policy and one new source |
| L4 | PASS — insufficient-evidence valet-parking answer, no new source |
| L5 | PASS — full Harbor/Sakura RM32/RM36 records, serving units/allergens/dinner-only qualifier, explicit Harbor RM4 lower, two sources |
| L6 | PASS — deterministic cheaper-price continuation, fresh full records/RM4 result and two new sources |
| L7 | PASS — deterministic continuation into four tasks, both full menus/policies and four sources; Sakura free-at-least-12-hours / later RM15-per-booking policy preserved |

Exactly seven sends used two fresh conversations; none were resent or unused. The operational answer checker accepted the observed wording “Harbor ... listed price is RM4 lower per serving” as the required explicit cheaper comparison. The frozen application/helper/fixture/tests were unchanged. Fourteen manual source opens/reopens verified every required citation and retained older-answer associations. Four actual UI downloads matched all section 8.2 filenames/versions/bytes/hashes. Native PDF page 1 and complete numbered Markdown sections passed content checks; four private screenshots were visually inspected. The owned acceptance browser and ledger were closed. No demo walkthrough was started.

### Correlated execution

Seven correlated request traces establish four ordinary Jev document routes (`jev-1.13.0`, no fallback) and three resolved `document_followup` paths. L3/L6/L7 invoked no router or rewrite model. L6 includes a deterministic `rag.comparison.plan` pin/compile span with no model descendants; that span is not planner inference.

Twelve keyword/embed/vector/fusion paths used `hybrid` / `bm25-rrf-v1`, the unchanged generation and correct venue scopes: one per L1–L4, two each L5/L6 and four L7. Each path had one embedding attempt and respected candidate/union/overlap, five-passage and 9,000-character bounds. Ordinary validation preceded moderation; comparison validation and multipart verified-worker/aggregation boundaries passed before final approval.

There were twelve logical selectors and one L7 model planner. Twenty-six nested model instrumentation spans were paired by ancestry into thirteen logical calls. L7 recorded four supported tasks with one retrieval/selector attempt each and maximum two simultaneously active worker spans. All seven input checks, unchanged approved final outputs and post-approval `memory.save` paths passed. Eighty-four checkpoint CreateEvent spans are reported separately and do not establish durable-memory totals. No SDK retry attempts were recorded in the inspected spans.

Initial reads plus one delayed reconciliation used four pages per known group, within the shared ten-page allowance. Across both passes, 712/240/236 events were read from `aws/spans`, the telemetry group and Runtime group respectively; the repeated reads were deduplicated to 356 scoped spans, including startup spans outside the seven request traces. Safe app attributes/correlations were retained, while raw exporter/provider values and session/source/credential data were excluded. No completion-specific span was invented.

### Retention, preservation and closeout boundary

The final read-only cloud check reconfirmed matching READY 22, the exact forward template, eighteen mappings/outputs, surrounding Runtime configuration, IAM/guardrail, active pointer and fetchable rollback graph. All required live criteria passed, so the candidate was retained; the conditional rollback allowance was unused. The old failed matrices remain closed and their recovery records unchanged.

P01–P08 passed. At this documentation-preparation checkpoint, P09 still requires documentation-only publication/CI, final protected checks and owned cleanup. The subsequent ignored final receipt and PR body record those actual results; this source file cannot contain its own later commit SHA or CI run IDs. P10 is reconciled there against actual operation counts. The closeout changes only the five section 3.1 documents and preserves all non-document release trees. The deployed image remains tied to the repair release, so documentation publication does not trigger a rebuild.

No new application repair, dependency/prompt/corpus/IAM/guardrail change, standalone probe, extra Runtime request, Docker recovery, benchmark or demo is included. The result establishes the controlled compatibility matrix, with semantic recall gains, live keyword-only rescue, latency/dollar savings, authenticated isolation and general production readiness unmeasured.
