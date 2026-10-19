# Handoff PRD for hybrid retrieval publication and rollout

**Status:** Proposed Phase B. Preparing this PRD does not authorize publication, AWS actions or paid requests. Execute after the owner's explicit sign-off under AGENTS.md.

**Prepared:** 2026-10-15, Asia/Kuala_Lumpur.

**Audience:** The project owner and engineer publishing the AI engineering portfolio extension.

**Deliverable:** Publish the reviewed hybrid retrieval release to the existing draft PR, deploy one audited ARM64 image with hybrid retrieval enabled, and verify seven controlled UI requests, inspectable originals and correlated traces. Retain a recoverable baseline. Stop before the demo walkthrough.

## 1 Outcome and scope

Phase A implemented local BM25 keyword ranking alongside vector search, combined through Reciprocal Rank Fusion (RRF). Phase B verifies the exact implementation with real Runtime, Bedrock, S3 Vectors, stored documents, moderation, checkpoints and the existing Chainlit UI.

Success means this bounded matrix and its evidence checks pass. It does not establish better semantic ranking than vector search, measured cost savings, faster responses or production readiness. Benchmarking remains skipped.

After approval, execute:

1. Bounded readiness/provenance checks and a fresh rollback baseline.
2. Publication of exactly 21 paths to origin and the existing draft PR, with exact-release CI inspection.
3. One committed-source ARM64 image, offline container audit and ECR publication.
4. One reviewed forward update changing only the Runtime image and retrieval-mode value.
5. Seven attempted Runtime requests, at most 18 citation opens/reopens and four actual original downloads.
6. At most one conditional rollback.
7. Documentation closeout, CI and cleanup of owned temporary material.

No new application implementation, prompt synchronization, ingestion, guardrail/IAM change, deployment of other stacks, benchmark, demo, PR merge, upstream push or cloud resource/image deletion is included.

## 2 Inspected local baseline

Repository: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.

| Item | Inspected value |
| --- | --- |
| Branch and HEAD | `feat/document-multipart-rollout`, `b61b1342041fdbe96fb6d5488104995acc371e1f` |
| Origin | `https://github.com/yukangzhen/restaurant-finder.git` |
| Phase A | COMPLETE; AC01–AC15 PASS |
| Feature paths | 20 uncommitted paths; all 20 hashes matched Phase A's receipt while preparing this PRD |
| Publication | Those 20 paths plus this PRD, exactly 21 |
| Mode | API/direct construction/CDK default to `vector`; hybrid requires explicit selection |
| Owner work | Untracked `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`, SHA-256 `c3f491550280ba5568cea656d1e90378a76547ee5520e462a323469949aebf9f`; preserve and exclude |

Phase A plan: [implementation and local execution record](HANDOFF_PRD_HYBRID_DOCUMENT_RETRIEVAL.md).

Evidence root: `restaurant-finder-api/.generated/hybrid-retrieval-20261015-1792062032624/`. Inspect `final-verification.json`, `acceptance-verification.json`, `baseline.json`, `export-files.json`, reports and command receipts. Temporary scripts, network guard and source copies were removed; do not try to execute them.

| Local check | Inspected result |
| --- | --- |
| API / UI / infrastructure tests | 290 / 32 / 55, all passing |
| Infrastructure compilation | Exit 0 |
| Single-document evaluation | 17 cases, 374 checks |
| Comparison evaluation | 20 cases, 260 checks |
| Multipart evaluation | 40 cases, 609 checks |
| Conversation evaluation | 24 cases, 28 named variants / 63 simulated turns, 1,147 checks |
| Retrieval evaluation | 24 cases, 57 required variants, 1,070 checks |
| Preservation | 155 protected files unchanged, including the four original datasets |
| Offline syntheses | Three stack templates equal after removing only the new mode value |

These are completed local checks, not current GitHub CI or live acceptance. Preparation rechecked local hashes and original sample bytes; it did not rerun tests or contact AWS, GitHub or Docker.

## 3 Historical deployment and preservation targets

The accepted [follow-up rollout record](HANDOFF_PRD_FOLLOWUP_PUBLICATION_AND_ROLLOUT.md#12-phase-b-execution-and-acceptance) records these values. Recheck them before mutation; they are historical evidence.

| Item | Last accepted value |
| --- | --- |
| Existing PR | `https://github.com/yukangzhen/restaurant-finder/pull/1`, draft, head `feat/document-multipart-rollout`, base `feat/jev-router` |
| AWS | Profile `default`, account `447393541969`, region `us-east-2`, authorized non-root identity |
| Stack | `restaurantFinder-AgentCoreStack` |
| Runtime logical ID / identity | `restaurantFinderAgentCoreRuntime` / `restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime / DEFAULT | READY, version/live version 17 |
| Existing behavior | RAG enabled, multipart true, follow-ups true, top-k 5 |
| Retrieval mode | Absent or vector expected; capture exact key presence/value |
| Guardrail | Immutable `ih5xpt3qi946:1`, READY |
| Accepted application release | `11590ea927076e96c92b251912f8747ba0732085`; current HEAD adds documentation only |
| Accepted image | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:document-followups-11590ea-20261014082247-arm64` |
| OCI index | `sha256:fe3763ab8be2b66a3c7e3b99b25d1cab14c6bdc6dc52532c4b12ab1ac1866163` |
| Runnable linux/arm64 child | `sha256:258c7d60a341c20df5cf8954618d5e5e18dcf302a088c33aa50f6925862dfd9b` |
| Image config | `sha256:722a0dd0b52a065ba8b1a4607f1e2a277172789a6f798bd9b04f100c0e47e9a0` |
| UI | `http://127.0.0.1:8010/` |

Historical UI cwd: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/tmp/pinned-3771a4c-20261014005846/restaurant-finder-ui`. Preserve this directory if it still backs the listener. An old PID is not ownership proof.

Preserve:

- Guardrail policy fingerprint `cbf24512ff86fcd0187d95424e868d0f4b5ee1199515bdd4b06363ccdfad176d`.
- Guardrail-specific Runtime inline policy hash `6ff2a7301b03e26308a4a8c10a12716c57205775e7f0472c168818a527c80eaa`.
- Two captured inline-policy documents' combined hash `bdd6fafd298761b8d4250b8b472adfbe1d52ab30bda5369d1de86d6082c6855d`.
- Historical 18 physical resource mappings and outputs; capture the actual full set.
- Bucket `restaurantfinder-ragstack-documentbucketae41e5a9-vqrmcnuycjq5`, pointer `rag/active.json`.
- Generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` and ETag `"d3705246c1cc2a4fd7f694bc91553e95"`.
- Index `arn:aws:s3vectors:us-east-2:447393541969:bucket/restaurantfinder-rag-447393541969-us-east-2/index/documents-titan-v2-512`; Titan V2 / 512 / float32 / cosine.
- All six originals, nine immutable prompts, locks, configured provider/model identities and every other Runtime setting.

Reuse the accepted canonical fingerprint projections. Exclude service response metadata without dropping effective configuration. A response-shape difference is not proof of policy drift; an unknown configuration difference cannot be discarded to obtain equality.

Prior request, rollback and Docker-recovery allowances do not carry into this phase.

## 4 Exact publication allowlist

Stage these 21 paths individually or through this exact list. Inspect staged names/count and full diff. Do not use `git add .`, `git add -A` or wildcard staging.

~~~text
.github/workflows/ci.yml
README.md
docs/CI_AND_RAG_EVALUATION.md
docs/DOCUMENT_RAG.md
docs/HANDOFF_PRD_HYBRID_DOCUMENT_RETRIEVAL.md
docs/HANDOFF_PRD_HYBRID_RETRIEVAL_PUBLICATION_AND_ROLLOUT.md
restaurant-finder-api/.env.example
restaurant-finder-api/src/application/document_rag/comparison_workflow.py
restaurant-finder-api/src/application/document_rag/ranking.py
restaurant-finder-api/src/application/document_rag/retrieval.py
restaurant-finder-api/src/application/document_rag/workflow.py
restaurant-finder-api/src/config.py
restaurant-finder-api/src/domain/document_rag.py
restaurant-finder-api/src/evaluation/datasets/document_retrieval.json
restaurant-finder-api/src/evaluation/document_retrieval.py
restaurant-finder-api/tests/test_document_hybrid_retrieval.py
restaurant-finder-api/tests/test_document_retrieval_evaluation.py
restaurant-finder-api/tests/test_document_retrieval_ranking.py
restaurant-finder-infra/bin/cdk.ts
restaurant-finder-infra/lib/stacks/agentcore-stack.ts
restaurant-finder-infra/test/document-rag.test.ts
~~~

Closeout may modify only README, `docs/DOCUMENT_RAG.md`, `docs/CI_AND_RAG_EVALUATION.md`, the Phase A hybrid PRD and this PRD. No implementation change belongs in documentation closeout.

## 5 Operation and cost limits

| Operation | Bound after sign-off |
| --- | --- |
| Runtime sends | Seven attempts, exactly L1–L7. Reserve before sending. Errors, timeouts, blocked/masked answers and uncertain delivery consume the slot. |
| Sequencing | Stop at the first failed/unverified required result. No dependent follow-up after a failed seed. Unused slots are not troubleshooting probes. |
| Paid work | Requests can invoke Jev, Bedrock guardrails/selection/planning, Titan, S3 Vectors, S3, AgentCore/checkpoints/memory and logs. Seven sends is not seven underlying calls or a dollar cap. |
| Additional inference | Zero greetings, warm-ups, standalone guardrail checks, live evaluators, vector-vs-hybrid comparisons, keyword-only probes or generation-switch experiments. |
| Original reads | Four unique preflight originals, each ≤5 MiB; four actual UI downloads, one intended download per original. Inspect all six identities through the manifest. |
| Citation actions | At most 18 attempted opens/reopens, allocated below. Download clicks have a separate four-original limit. HTTP/range/cache behavior is not an exact S3-call count. |
| Browser evidence | One owned browser session, two fresh conversations, at most 18 private screenshots. Every DOM/source inspection need not create a screenshot. |
| Prompts | One read-back per nine pinned immutable versions; one final metadata reconciliation if needed. No writes/sync. |
| Build/push | One initial build, at most one reconciled pre-publication retry on unchanged source/manifest, one successful audited unique image and one intended push. |
| Deployment | One reviewed forward change set/execution; at most one reviewed conditional rollback change set/execution. |
| Polling | Readiness every 15–30 seconds, at most 20 minutes per update; CI every ≥30 seconds, at most 30 minutes per publication. Blocking waits ≤60 seconds. |
| Logs | Acceptance window ±60 seconds; at most ten pages of ≤1,000 events per relevant group, shared across the first read and one delayed reconciliation. Count empty/repeated-token pages too. |
| UI | Reuse by default; at most one necessary owned UI restart and one rollback restoration. |
| Docker recovery | No Desktop restart, WSL reset, pruning or broad termination. Obtain a separate recovery decision; the owner previously preferred manual restoration. |
| Publication | One release commit/push and one documentation-only closeout commit/push; no force-push, merge, new PR or manual workflow dispatch. |

Readiness/source reads, image storage/build infrastructure and CI may also incur normal charges. No numerical cost estimate or credit-balance claim is made. Readiness performs no model or Runtime invocation.

## 6 Exact live matrix

Use the real Chainlit UI in AWS mode against DEFAULT. Start genuinely new conversation IDs A and B with New Chat. Keep existing anonymous identity behavior; do not manufacture actors or claim authenticated isolation.

Validate each final answer and its attached source controls before the next dependent turn. Submit consecutive messages without unrelated input. Defer lengthy source viewing/downloads until that conversation's dependent sequence finishes. A later source-inspection failure still fails acceptance and stops remaining sends.

| Slot | Chat | Exact text | Required public and workflow result |
| --- | --- | --- | --- |
| L1 | A1 | `According to Harbor Pasta Lab's menu, what is the mushroom pasta price?` | RM32 per serving and wheat/milk qualifiers. One to three relevant exact selections, all from Harbor's menu original; no unrelated dish claim. Hybrid menu retrieval. |
| L2 | A2 | `According to Harbor Pasta Lab's policy, how much notice must I give to cancel without charge, and what is charged if I cancel too late?` | Free cancellation at least 24 hours before booking; RM20 per booking when later. One to three relevant exact selections collectively cover both conditions, all from Harbor's policy original. |
| L3 | A3 immediately after L2 | `And what about its cancellation fee?` | Deterministic Harbor follow-up; fresh hybrid policy retrieval, full 24-hour/RM20 policy, one source. No new router/rewrite inference. |
| L4 | A4 | `According to Harbor Pasta Lab's documents, is valet parking available?` | Insufficient evidence, no availability claim and no new citation control. Scoped retrieval/selection still run. |
| L5 | B1, fresh chat | `Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources.` | Harbor RM32 and Sakura RM36, both per serving; wheat/milk and Sakura dinner-only qualifier; Harbor cheaper by RM4. Two menu citations, two scoped workers. |
| L6 | B2 immediately after L5 | `Which is cheaper?` | Deterministic continuation; fresh hybrid retrieval for both venues, complete prices and RM4 difference, two new menu citations. No router/rewrite/planner inference. |
| L7 | B3 immediately after L6 | `What about both restaurants' prices and cancellation policies?` | Deterministic continuation into four-task multipart work: complete menu records plus Harbor free ≥24h / late RM20 per booking and Sakura free ≥12h / late RM15 per booking. Four original citations; at most two active workers. |

L1/L2/L4/L5 use ordinary Jev document routing; the existing Bedrock router fallback is permitted only when evidenced. L3/L6/L7 use `document_followup`. All seven require input moderation and unchanged final output approval. Masked/blocked results do not pass.

### 6.1 Citation inspection and downloads

After A1–A4:

1. Open every L1/L2 citation and L3's one citation: at most seven opens.
2. Confirm L4 added no source control. Reopen the first L1 control after the later answers: one additional open.
3. Download Harbor menu and Harbor policy using actual UI source/download controls, once each.

After B1–B3:

1. Open L5's two, L6's two and L7's four controls: eight opens.
2. Reopen both L5 controls after L7 and verify retained answer/document associations: two additional opens.
3. Download Sakura menu and Sakura policy once each. Reuse the already downloaded Harbor originals for hashes.

This totals at most 18 attempted opens/reopens and four unique downloads. Wait for asynchronous content and inspect actual document/version/hash/location. Copies of sample files or backend-only URL checks cannot replace UI downloads.

### 6.2 Original identities and factual gold

The following local sample bytes were hashed during preparation; the first three also match the prior accepted rollout. Fresh deployed manifest/source reads must agree before mutation. Drift requires reconciliation, not revision of gold after observing answers.

| Original | Identity and SHA-256 | Required location/record |
| --- | --- | --- |
| Harbor menu | `harbor-menu-v2.pdf`, v2, 1,975 bytes; `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10` | PDF page 1; mushroom pasta RM32 per serving; wheat/milk |
| Harbor policy | `harbor-policy.md`, v1, 534 bytes; `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471` | Reservations and cancellation, lines 5–8; full 24-hour free window and RM20 late fee per booking |
| Sakura menu | `sakura-menu.md`, v1, 383 bytes; `0ac797361e4fc9abc433685b26693e6d877ed6ad873c94110cd0e3a7be7e9637` | Main dishes, lines 5–11; RM36 per serving; wheat/milk; dinner only |
| Sakura policy | `sakura-policy.md`, v1, 466 bytes; `e61b5aa2a3c6969061866379a754fbd7a3d07aef4e82a39c5dc89ddea4c6668f` | Reservations and cancellation, lines 5–8; full 12-hour free window and RM15 late fee per booking |

This matrix verifies deployed hybrid execution and workflow/source compatibility. It does not prove a real vector query missed a passage that BM25 rescued. Controlled keyword-only recovery remains established by offline fixtures; no live ablation or deliberate provider failure is included.

## 7 Observable definition of done

| ID | Required evidence |
| --- | --- |
| B01 | Fresh approved-account baseline and recoverable image/configuration; Phase A hashes, protected files, corpus and prompts verified. |
| B02 | Exactly 21 paths published to the existing draft PR; exact release SHA and remote head read back. |
| B03 | Exact-release push/PR CI passes four jobs; inspected artifacts confirm 290/32/55 tests, complete 17/20/40/24/24 datasets, 57 new variants and 1,070 checks. |
| B04 | One audited unique linux/arm64 image from committed Git bytes and nine-prompt manifest; UID/command, source hashes and registry digest chain recorded. |
| B05 | Only image URI and mode presence/value changed on one Runtime without replacement; READY Runtime/DEFAULT agree; surrounding resources/settings equal. |
| B06 | All seven requests pass in two conversations with correct approval, facts, insufficient-evidence behavior and workflow routes. |
| B07 | All required source controls/retained associations inspected; four actual original downloads match hashes/locations. |
| B08 | Correlated traces establish hybrid ranking/fusion and fresh scoped retrieval, bounded counts and safe new attributes; visibility limits explicit. |
| B09 | Retain/rollback, closeout publication/CI, protected checks and owned cleanup complete; demo not started. |

A partial matrix is not B06 PASS. A successful rollback restores a baseline and does not turn failed feature acceptance into a pass. Missing required source/telemetry evidence is a validation gap.

## 8 Execution instructions after approval

### Step 0 Record approval and freeze the local package

1. Record sign-off on this exact scope: publication, ordinary service charges, seven sends, source actions, conditional rollback and only a necessary owned UI restart. PRD-preparation approval is not execution approval.
2. Create an operation-owned ignored evidence root, for example `restaurant-finder-api/.generated/hybrid-rollout-<UTC timestamp>/`. Record its resolved absolute path, ledger, short staging path under the task's tmp directory and intended cleanup.
3. Re-read status, HEAD/branch/remotes, all 21 diffs, Phase A receipts and protected hashes. Verify Phase A's 20 final hashes before staging; record this PRD's hash separately. Reconcile drift/new owner work.
4. Preserve warning PRD, real environment/credential files, locks, four original datasets, originals/catalogs, retained prompt manifests, past failures/evidence and the live UI tree.
5. New helpers belong only in owned ignored directories, contain no secrets and are removed at closeout. Do not broaden old private-directory ACLs or copy raw configuration into public staging.

**Checkpoint:** approval and exact package recorded; zero Runtime attempts and zero publication/cloud mutation.

### Step 1 Check readiness and capture rollback authority

1. Check installed authentication/tools, locked interpreters, Node/CDK, Docker/buildx and AWS CLI. No installation/upgrade. Require a usable Linux Docker engine; recovery beyond normal use needs its own decision.
2. Run `aws sts get-caller-identity --profile default --region us-east-2`. Require account `447393541969` and an authorized non-root identity. Expiry requires the owner to complete `aws login --profile default`. Do not rewrite profiles/credentials or infer identity from the account alias.
3. Read stable stack/template, parameters, resources/outputs, Runtime configuration and DEFAULT endpoint. Require section 3 agreement. Privately capture exact rollback template/configuration. Distinguish absent retrieval-mode key from explicit vector.
4. Read baseline ECR manifests/digests and lifecycle/tag settings. Prove the baseline image is fetchable and recoverable after adding one tag. No policy edit, tag overwrite or older-image substitution.
5. Read immutable guardrail and Runtime inline policies. Validate accepted fingerprints with existing canonical projections; capture full current equality baselines. No standalone moderation or IAM change.
6. Read pointer/manifest and index metadata. Require accepted generation/ETag, six-original identities and embedding/index configuration. Read only the four originals above, close bodies and verify bytes/hash/full records.
7. Identify the owned 8010 listener with fresh process/source proof. Verify committed UI application bytes, interpreter, AWS mode, DEFAULT ARN, profile/region, bucket, source viewer and existing anonymous identity configuration. Do not dump environment values. Capture restoration source/configuration if needed.
8. Verify GitHub identity `yukangzhen`, origin/remote head and PR #1's draft/head/base. Browser login alone does not prove CLI/Git authorization. Readiness makes no Runtime, embedding, QueryVectors or model call.

**Stop:** wrong account, unstable/drifting state, unavailable rollback, missing access, unknown listener ownership or unsupported Docker recovery. Unresolved readiness consumes zero L slots; preserve the accepted baseline.

### Step 2 Publish the release and inspect exact CI

1. Freshly compare remote head to the intended local parent. Do not reset, force-push or overwrite another writer.
2. Stage the exact 21 paths, inspect names/count/full diff and `git diff --cached --check`. Use configured author identity; exclude unrelated/ignored files.
3. Commit, record release SHA/parent/paths, normally push once to origin and read back remote SHA. Reconcile uncertain outcomes before retrying; do not create a duplicate release.
4. Preserve PR title/base/draft and old body sections; append actual scope/local evidence and planned live acceptance. Use structured arguments or an exact body file with real newlines. Attach the existing PR through the app tool if required.
5. Inspect automatic push and PR CI for the exact head. Verify merge-ref head association where applicable. Require API, UI, infrastructure and quality jobs.
6. Download fresh artifacts. Inspect logs/all five JSON and Markdown reports, counts, completeness, 28 conversation variants/63 turns and 57 retrieval variants. Record actual hashes/run URLs; do not require platform-dependent report bytes to equal Phase A's local hashes.
7. Do not dispatch deployment/destruction workflows or change Actions settings. Missing/failing CI stops before image publication; application/CI repairs need a reviewed repair scope.

GitHub CLI was absent previously. Reuse existing authenticated tooling; the proven fallback is Git Credential Manager into process memory with structured GitHub requests. Never print/save tokens or place them in URLs/command lines.

### Step 3 Export committed inputs and validate prompts

1. Export exact API/infrastructure Git blob bytes into short owned staging. Never build from the working API directory containing private generated evidence.
2. Compare export to the chosen commit. Explicitly reconcile deterministic Git line-ending normalization between working-file and committed hashes; allow no semantic change. Committed-source CI validates the release.
3. Add only retained `restaurant-finder-api/.generated/multipart-rollout-20261013032223/nine-prompt-manifest.json` as staged API `.generated/prompt-manifest.json`. Require SHA-256 `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9`. Do not copy surrounding generated data.
4. Read back all nine immutable CHAT versions and match IDs/versions/ARNs, committed system text, user placeholder and variables. Hybrid adds no prompt. Failure is not permission to synchronize or create one.
5. Run staged read-only `src.deployment.validate_prompts` with the existing locked interpreter, absolute manifest path, sync off, metadata credentials off, export/evaluation off and no real .env. Require exit 0; never start `src.main`.
6. Record candidate URI; compile/synthesize committed IaC with installed dependencies, no lookups and the intended settings:

~~~text
imageUri=<unique candidate URI>
documentMultipartEnabled=true
documentFollowupsEnabled=true
ragRetrievalMode=hybrid
guardrailId=ih5xpt3qi946
guardrailVersion=1
~~~

Resolve placeholders before use and write assembly beneath owned staging. This checks IaC provenance; do not deploy all stacks. The captured deployed template controls the narrow Runtime update.

### Step 4 Build and audit one image

1. Choose absent unique tag `hybrid-retrieval-<release SHA first 7>-<UTC timestamp>-arm64` in existing `restaurantfinder-agent`. Access failure does not prove absence; never overwrite/use latest.
2. Build from the clean export with the unchanged Dockerfile/lock:

~~~text
docker buildx build --platform linux/arm64 --load --label org.opencontainers.image.revision=<release SHA> --metadata-file <owned metadata file> --tag <unique URI> <staged API root>
~~~

Record build/base metadata. The mutable base tag provides no byte-identical rebuild guarantee.

3. Require linux/arm64, exact revision label, UID 1000 and normal `opentelemetry-instrument python -m src.main` command. Audit with entrypoint overridden and `--network none`, without agent startup.
4. Recompute packaged paths/count and hash against staged Git bytes/manifest. Include new ranking/evaluator/dataset files admitted by the unchanged Dockerfile; do not prune importable code by folder name.
5. Verify no real .env, credentials, private reports, downloads, helpers, tests or sample originals. .env.example is allowed. Docker ignore does not exclude every .generated directory; clean export plus the sole manifest is essential.
6. At most one reconciled retry is permitted after a pre-publication failure on unchanged source/manifest. Docker recovery still needs its own decision. Two failed builds or source changes stop this allowance.

### Step 5 Publish the audited image and review the update

1. Authenticate only to the existing ECR registry; use memory/stdin for tokens. If needed, use current-user-only temporary Docker auth and the verified engine endpoint. Preserve global configuration and remove temporary credentials in finally. Never broaden private ACLs.
2. Push the audited unique image once; reconcile uncertainty by read-back. Record OCI index, runnable ARM64 child and config digests separately, including attestation distinctions.
3. Recheck rollback fetchability and unchanged live baseline.
4. Copy the captured deployed template and change only:

~~~text
Resources.restaurantFinderAgentCoreRuntime.Properties.AgentRuntimeArtifact.ContainerConfiguration.ContainerUri
Resources.restaurantFinderAgentCoreRuntime.Properties.EnvironmentVariables.RAG_RETRIEVAL_MODE
~~~

Set audited image URI and string `hybrid`. Restore these two leaves to baseline presence/value during parsed full-template comparison; require equality elsewhere.

5. Preserve multipart/follow-ups true, pinned guardrail, model/embedding configuration, IAM, other resources, parameters and outputs.
6. Create one named UPDATE change set with existing parameter values/capabilities. Require one existing Runtime Modify, no replacement/create/delete and no RequiresRecreation demand. Record proposal hash and reviewed identity.
7. Recheck baseline and image immediately before execution. Sign-off covers only this conforming proposal; unexpected changes require reconciliation/new decision.

### Step 6 Execute once and verify readiness

1. Execute once and reconcile uncertain outcomes without blind re-execution.
2. Poll within limits; require UPDATE_COMPLETE, exact image/mode and matching READY Runtime/DEFAULT live version. Measure the version; do not assume 18.
3. Compare deployed template/proposal, surrounding Runtime configuration, resources/outputs, IAM/guardrail and corpus identities. Keep rollback image fetchable.
4. Reuse verified UI. If necessary, prove ownership, capture restoration and stop only its process. Launch committed UI with the existing interpreter, loopback 8010 and explicit AWS/Runtime/source settings in an isolated process using `Start-Process -WindowStyle Hidden`. Preserve real environment files and unrelated listeners.
5. Verify HTTP/listener readiness without an agent message. Start one isolated owned browser session using the applicable browser skill; preserve unrelated sessions/tabs.

**Checkpoint:** conforming deployment and ready UI; zero L attempts. Verification failure enters the rollback decision.

### Step 7 Execute the seven-slot matrix

1. Create L1–L7 ledger and reserve each slot durably before its single UI submission. Record safe correlation, attempted/completed/uncertain state, output gate, route, source count and result.
2. Submit exact texts/order, wait for final text and attached controls, and inspect visible records/associations before dependent turns. Defer lengthy viewing as section 6 specifies.
3. Stop on first failed/unverified requirement. No resend, wording change, context injection, provider switch or reuse of unused slots.
4. Inspect controls within 18 attempts and perform four actual UI downloads. Verify bytes/hash/page/section/lines and retained associations. Reconcile viewer delays from existing state without another Runtime call.
5. Keep evidence private; sanitize session-bearing source URLs from snapshots. Never persist browser tokens, credentials, provider bodies or arbitrary checkpoints.
6. Reconcile attempted/unused L slots and browser/source allowances at completion or stop. No additional inference follows the matrix.

### Step 8 Verify correlated hybrid execution

1. Read only bounded acceptance window/known correlations. Historical groups are `aws/spans`, `/aws/vendedlogs/bedrock-agentcore/restaurantFinder-telemetry` and `/aws/bedrock-agentcore/runtimes/restaurantFinder_Agent-Ha58oX5Psu-DEFAULT`. Confirm actual presence; aws/spans has no leading slash.
2. Correlate seven turns, four ordinary document routes and three deterministic continuations. Require `document_followup` and no router/rewrite inference for L3/L6/L7. Report real fallback behavior.
3. Expect 12 logical retrieval paths: four singles L1–L4, two two-worker comparisons L5/L6 and four L7 workers. Require matching `rag.keyword_rank` and `rag.fuse` spans, `rag.retrieval_mode=hybrid`, `rag.ranking_algorithm=bm25-rrf-v1` and generation/venue association.
4. Check observed vector/keyword counts ≤5, union ≤10, consistent overlap, returned passages ≤5 and characters ≤9,000. Counts do not establish every HTTP request or exact filter payload.
5. Require fresh embedding/vector/selection work, one L7 planner and at most two active workers. L4 abstains without citations. A failed/short-circuited path is not a completed expected operation.
6. Inspect unchanged output approval/save boundaries. New rank-span app fields must remain committed enums/counts/catalog/generation identifiers. Inspect standard exporter keys separately and never save raw payloads.
7. Separate logical calls, overlapping model instrumentation and observed SDK retries. CreateEvent spans include checkpoints and do not prove durable memory totals.
8. One delayed reconciliation may use the same window within the combined page cap; no new request to improve tracing. Missing required hybrid evidence leaves B08 unmet.

Live recall improvement, authentication, exact thread cancellation, changed-generation behavior and cost/latency remain unmeasured. Offline keyword-only recovery is not inferred from successful live answers.

### Step 9 Retain or roll back once

Retain after B01–B08 and protected checks pass. Record actual source/image/Runtime identity, attempts, sources and telemetry. B09 awaits closeout.

One rollback is allowed if the update fails/remains unready, a required public/moderation/source/workflow contract fails or bounded verification cannot establish acceptance.

1. Stop sends and capture failure safely. Never overwrite another actor's concurrent configuration change.
2. Restore fresh baseline image and exact prior mode presence/value. Remove the key if absent originally. Keep earlier accepted multipart/follow-ups and pinned guardrail intact.
3. Review one rollback change set under the same no-replacement constraints, execute once and require stable matching Runtime/DEFAULT. Version numbers may increase; recovery does not mean numeric version 17.
4. Restore owned UI only if this phase changed it and restoration is needed. Read-only verify configuration/resources/pointer/image; no post-rollback inference is included.
5. Preserve commits/images/originals/events/failure evidence. Rollback does not erase publication or charges. Another mutation/failed rollback needs a recovery decision.

Record FAILED/RECOVERED, not accepted, if rollback is used. Do not spend remaining slots against the old image as hybrid acceptance.

### Step 10 Publish closeout and clean up

1. Update only the five permitted documentation paths with actual B01–B09, source/digests/versions, CI links, attempts, inspections, retain/rollback and gaps.
2. Make one documentation-only commit/push to the same draft PR; verify its exact-source CI/artifacts. Application/UI/infrastructure/.github trees must equal the release. Do not rebuild because the docs SHA differs.
3. Record future closeout SHA/CI in private receipts and PR body; a commit cannot contain its own later SHA/run.
4. Recheck owner/protected files, remote/PR, retained/recovered cloud state, rollback image and guardrail/IAM/corpus identities.
5. Remove only owned helpers, temporary auth/build exports/audit containers and dependency links after absolute containment, process and reparse checks. Preserve evidence, prior failures and any tree backing the UI.
6. Use native PowerShell literal paths end-to-end. If WMI is unavailable, an installed read-only process library can inspect ownership. Do not broaden permissions or recursively follow junctions. Remove verified owned links non-recursively and prove targets remain.
7. Close only the owned browser, leave verified retained UI available, reconcile allowances and checkpoint. Stop before the demo.

## 9 Evidence and reporting

Keep privately under the owned ignored root:

- Approval/attempt ledger, source/protected hashes and exact publication/closeout lists.
- Git/PR/CI associations, downloaded safe reports and hashes.
- Fresh rollback template/configuration, resources/outputs, policy/image/corpus identities.
- Exact committed export, nine-prompt validation, image audit and registry digests.
- Reviewed update/execution/readiness, seven-slot outcomes, four real downloads and sanitized traces.
- Retain/rollback, final equality and cleanup.

Raw rollback configuration stays access-controlled and ignored. Never publish credentials, full environment, signed/source-session URLs, owner hashes, provider bodies or raw checkpoints. Non-sensitive helpers may use separate short staging without changing ACLs on old private evidence.

## 10 Approval and execution record

**Proposed approval:** 21-path publication to existing draft PR #1; exact CI/artifacts; bounded readiness reads; one audited image with at most one reconciled pre-publication build retry; one two-leaf Runtime update; seven attempted requests; ≤18 source opens/reopens and four actual downloads; necessary owned UI restart; one conditional rollback; documentation closeout/CI and cleanup. Docker recovery remains separate.

**Preparation completed:** local source/status, Phase A receipts/hash equality, prior accepted deployment record and four sample original hashes/facts inspected. One new PRD is the output.

**Not executed during preparation:** tests, GitHub requests/publication, AWS/Docker checks, image publication, deployment, browser/UI actions, paid requests, rollback or demo.

Populate B01–B09 after execution with actual evidence. Record stops/remaining allowances and gaps; preserve the implementation record. No current service health, future version number or performance gain is implied.
