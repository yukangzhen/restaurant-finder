# Handoff PRD: Publish and Roll Out Document Conversation Follow-ups

**Status:** Phase B publication, release CI, audited image, two-leaf rollout and seven live acceptance requests PASS on 2026-10-14. Retain READY Runtime/DEFAULT 17; no rollback was needed. Documentation closeout publication/CI and owned cleanup are recorded independently after this commit. Stop before the demo walkthrough.

**Deliverable:** Publish the reviewed follow-up extension to the owner's existing draft PR, deploy one audited ARM64 image with the extension enabled, and establish functional acceptance through seven controlled UI requests and inspectable original sources. Retain the release only if the required checks pass; otherwise use the single conditional rollback defined here. Stop before the demo walkthrough.

## 1. Outcome, audience and reason

This is an engineering portfolio project for a future LinkedIn demonstration. The owner wants to show an improvement to the original Restaurant Finder: document answers can support a bounded conversational continuation without another router or rewrite model call, while still retrieving current evidence, applying moderation and exposing verified citations.

The local extension already implements that behavior. Phase B closes the remaining integration gap: the real AgentCore checkpointer, deployed container, guardrail, retrieval services and existing UI must work together across consecutive turns. Simulated local tests cannot establish that live integration by themselves.

The executor must produce a release and acceptance record that another engineer can inspect. Do not present this limited matrix as a production readiness assessment, a benchmark, general conversational understanding, authenticated tenant isolation, or measured cost/latency improvement.

## 2. Inspected starting evidence

### 2.1 Current local state

Repository root: `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.

| Item | Verified during PRD preparation |
| --- | --- |
| Branch | `feat/document-multipart-rollout` |
| HEAD | `574cc6304b1be4060cb8d281657c84303e6eb357` |
| Origin | `https://github.com/yukangzhen/restaurant-finder.git` |
| Upstream reference | `https://github.com/JoudAwad97/agentic-ai-langgraph-and-aws-agentcore.git`; never publish there. |
| Feature changes | 22 tracked modifications and seven new feature paths, uncommitted and unpublished. This new PRD adds one proposed publication path, making 30. |
| Protected owner work | Untracked `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`, SHA-256 `c3f491550280ba5568cea656d1e90378a76547ee5520e462a323469949aebf9f`; preserve and exclude. |
| Feature flag | API and CDK default `DOCUMENT_FOLLOWUPS_ENABLED` to false. |
| Local acceptance | Phase A AC01-AC14 complete in the inspected final receipt. |

Phase A plan: `docs/HANDOFF_PRD_DOCUMENT_CONVERSATION_FOLLOWUPS.md`, particularly its final execution section. Private evidence root: `restaurant-finder-api/.generated/document-followups-20261014/`.

| Local check | Inspected final result |
| --- | --- |
| API unit regression | 258 tests, exit 0 |
| UI unit regression | 32 tests, exit 0 |
| Infrastructure | TypeScript build exit 0; 53 Jest tests passed |
| Original single document evaluation | 17/17 cases, 374 checks |
| Existing comparison evaluation | 20/20 cases, 260 checks |
| Existing multipart evaluation | 40/40 cases, 609 checks |
| New follow-up evaluation | 24/24 conversations, all 28 named variants, 63 simulated graph turns, 1,147 checks |
| Offline synthesis | Default/off and true templates differ only in the new flag; five invalid context forms rejected before assembly. |
| Preservation | 22 protected identities matched; original three evaluation datasets are byte-identical. |
| Phase A closeout | 29 feature paths reviewed; 24 implementation/test/config/CI source hashes recorded separately; 11 owned temporary paths removed. No helper scripts remain. |

Inspect `baseline.json`, `local-verification.json` and `final-verification.json`; do not rely only on these copied counts. Phase A performed no publication, cloud requests, billable requests or live acceptance.

### 2.2 Last accepted deployment: historical baseline, not a fresh read

The inspected previous receipt is `restaurant-finder-api/.generated/guardrail-rollout-20261014005846/final-verification.json`, timestamp `2026-10-14T03:00:38.274522+00:00`. Its source PRD is `docs/HANDOFF_PRD_PINNED_GUARDRAIL_AND_MULTIPART_RETRY.md`, final execution section.

| Item | Last accepted value; recheck before action |
| --- | --- |
| Draft PR | `https://github.com/yukangzhen/restaurant-finder/pull/1`, head `feat/document-multipart-rollout`, base `feat/jev-router` |
| AWS identity | Profile `default`, account `447393541969`, region `us-east-2` |
| Stack | `restaurantFinder-AgentCoreStack` |
| Runtime | `restaurantFinder_Agent-Ha58oX5Psu`; logical resource `restaurantFinderAgentCoreRuntime` |
| Runtime/DEFAULT | READY, version/live version 16 |
| Existing multipart flag | `DOCUMENT_MULTIPART_ENABLED="true"` |
| Guardrail binding | Immutable `ih5xpt3qi946:1`, READY |
| Existing image | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:pinned-guardrail-3771a4c-20261014012132-arm64` |
| Registry OCI index digest | `sha256:2572b4e938d4926da62f906441f7098d8640c329d2db90e567b2f4db4708ba6c` |
| Runnable linux/arm64 child digest | `sha256:fd6038162d816d08f0baebce564bcdffd5f4a3e34fe3af9ba40bd4f5881d9544` |
| Packaged prior release | `3771a4ca4fa661da384e2e8f1ba92e7eb7008ab9`; current HEAD adds documentation only to that accepted application release. |
| Previous live acceptance | Six requests passed. That allowance is exhausted; zero remaining requests. No rollback occurred. |

The historical Runtime did not enable the new follow-up extension. Capture the fresh key's exact presence and value; an absent key and an explicit false value must be distinguished for rollback. If live state materially differs from this accepted baseline, stop and explain the drift before proposing another mutation.

The previous deployment and Docker recovery approvals do not carry into this release. The new seven-request allowance and single conditional rollback require sign-off on this PRD.

## 3. Scope and constraints

### In scope after explicit Phase B approval

1. Verify the local evidence and 30 publication paths; commit and normally push the reviewed release to origin; update existing draft PR #1 and inspect its automatically triggered CI.
2. Perform bounded read-only AWS readiness, provenance and rollback checks using the existing account/profile/region.
3. Export exact committed source, add the existing verified nine-prompt manifest, build/audit one unique ARM64 image and push it to the existing ECR repository.
4. Modify only the existing Runtime's image URI and `DOCUMENT_FOLLOWUPS_ENABLED="true"` through a reviewed CloudFormation change set.
5. Reuse the owned UI when its source/configuration is verified. If required, restart only that verified owned UI on loopback port 8010 using isolated process configuration.
6. Attempt the seven exact live requests in section 7, inspect their citations, download three unique originals through the actual UI, and inspect bounded sanitized telemetry.
7. Make one retain/conditional-rollback decision, publish documentation-only closeout, preserve evidence and clean up owned temporary artifacts.

### Constraints

- No new application behavior or dependency changes are planned. A failed application contract needs a separate repair PRD/sign-off, not an unreviewed patch during rollout.
- Preserve multipart true, the numbered guardrail pair, all other Runtime configuration, IAM policies, all 18 historical physical resource mappings/outputs, prompts, source documents, active pointer and vector index.
- Do not merge, target main, push upstream, force-push, manually dispatch deployment/destruction workflows, change Actions settings, create another PR, expand permissions or delete cloud resources/images.
- Do not synchronize/create/update prompts, edit real `.env` files, ingest documents, change a corpus pointer, change embedding configuration, or expose credentials/provider payloads.
- No benchmark, separate guardrail probe, warm-up, greeting, live evaluator, extra reproduction request or demo walkthrough.
- No Docker Desktop restart/reset, WSL reset, broad process termination or resource cleanup. The owner previously preferred manual Docker restoration; a new recovery decision is required if needed.
- Caller identity hashes and unkeyed context digests are consistency checks, not authentication. This rollout does not change the project's identity/security boundary.

## 4. Definition of done

| ID | Observable requirement |
| --- | --- |
| B01 | Exactly the reviewed 30 paths published to the existing draft PR; owner/unrelated files preserved; release SHA recorded and read back. |
| B02 | Exact release CI passes all four jobs; downloaded reports/logs confirm 258 API, 32 UI, 53 infrastructure tests and complete 17/20/40/24 evaluation coverage with the expected checks. No stale run/artifact is substituted. |
| B03 | Fresh approved-account baseline, retained/fetchable rollback image, immutable guardrail, nine managed prompts, corpus and owned UI state recorded safely. |
| B04 | One unique published image audited against the exact release, locked dependencies and sole generated nine-prompt manifest; linux/arm64, UID 1000, normal instrumented command, source/registry digest provenance recorded. |
| B05 | One reviewed existing-Runtime modification, no replacement, exactly two intended leaf differences; stable stack and matching READY Runtime/DEFAULT; surrounding resources/configuration/corpus preserved. |
| B06 | All seven exact requests pass through the real UI/Runtime in the required conversation order, with approved unchanged outputs, proper context/clarification behavior and expected complete facts/citations. |
| B07 | All answer citation controls inspected; earlier answer associations retained; three actual original downloads match pinned hashes/locations. Clarifications expose no new sources. |
| B08 | Correlated telemetry supports the observed routes, new deterministic resolution and fresh evidence paths, with no new resolver/rewrite call on admitted continuations. Unsupported/unmeasured internals remain labeled. |
| B09 | Retain or conditional rollback recorded honestly, allowance reconciled, closeout publication/CI inspected, protected identities preserved, owned cleanup complete and demo not started. |

A partial matrix is not B06 PASS. A successful rollback is a recovered baseline, not successful feature acceptance. Missing traces or source-inspection evidence are validation gaps, not implied passes.

## 5. Exact publication allowlist

Stage these paths individually or from this explicit array. No `git add .`, `git add -A`, wildcard staging or unrelated worktree cleanup.

```text
.github/workflows/ci.yml
README.md
docs/CI_AND_RAG_EVALUATION.md
docs/DOCUMENT_RAG.md
docs/HANDOFF_PRD_DOCUMENT_CONVERSATION_FOLLOWUPS.md
docs/HANDOFF_PRD_FOLLOWUP_PUBLICATION_AND_ROLLOUT.md
restaurant-finder-api/.env.example
restaurant-finder-api/src/application/document_rag/comparison_workflow.py
restaurant-finder-api/src/application/document_rag/conversation.py
restaurant-finder-api/src/application/document_rag/multipart_workflow.py
restaurant-finder-api/src/application/document_rag/workflow.py
restaurant-finder-api/src/application/orchestrator/streaming.py
restaurant-finder-api/src/application/orchestrator/workflow/nodes.py
restaurant-finder-api/src/application/orchestrator/workflow/state.py
restaurant-finder-api/src/config.py
restaurant-finder-api/src/domain/document_conversation.py
restaurant-finder-api/src/domain/document_rag.py
restaurant-finder-api/src/evaluation/datasets/document_followups.json
restaurant-finder-api/src/evaluation/document_followups.py
restaurant-finder-api/tests/test_document_comparison.py
restaurant-finder-api/tests/test_document_conversation.py
restaurant-finder-api/tests/test_document_followup_evaluation.py
restaurant-finder-api/tests/test_document_multipart.py
restaurant-finder-api/tests/test_document_rag_retrieval.py
restaurant-finder-api/tests/test_router.py
restaurant-finder-infra/README.md
restaurant-finder-infra/bin/cdk.ts
restaurant-finder-infra/lib/stacks/agentcore-stack.ts
restaurant-finder-infra/test/document-rag.test.ts
restaurant-finder-ui/tests/test_source_documents.py
```

The owner warning PRD remains excluded. Private `.generated` receipts, prompt manifests, live UI exports, credentials, downloads and real environment files remain outside Git.

Up to two normal commits/pushes are proposed: the reviewed release and one documentation-only closeout. Closeout may update only these five already approved paths: `README.md`, `docs/DOCUMENT_RAG.md`, `docs/CI_AND_RAG_EVALUATION.md`, the Phase A PRD and this PRD. Application/UI/infrastructure/CI trees must stay identical to the release after closeout. Any other source repair or publication requires a revised reviewed scope.

## 6. Operation allowances

| Operation | Proposed bound and stop condition |
| --- | --- |
| Runtime acceptance | Seven attempted sends total, exactly section 7. Reserve before send; a timeout, error, ambiguous send outcome or moderation rejection consumes its slot. No automatic resend. |
| Live acceptance sequencing | Stop at the first failed/unverified required public result. Do not send a follow-up dependent on a failed seed or approved clarification. Unused slots cannot become troubleshooting probes. |
| Billable services | These sends can invoke Jev, Bedrock moderation/inference, Titan, S3 Vectors, AgentCore/checkpoints/memory and logs. Seven requests is not seven underlying service calls or a dollar cap. No numerical cost estimate is claimed. |
| Source reads | Up to three unique original documents read during preflight, each at most 5 MiB, plus three actual UI downloads. Up to 12 specified citation opens/reopens; viewer HTTP/range requests are not claimed to equal one S3 call each. |
| Prompt reads | One read-back of each of the nine pinned immutable prompt definitions; a final metadata reconciliation if deployment evidence requires it. No writes/sync. |
| Build | One initial build; at most one corrected pre-publication retry on unchanged source/manifest after reconciling the outcome. One successful unique image and one intended push. No retry after uncertain publication without read-back. |
| Deployment | One reviewed forward change set and execution; at most one separately reviewed conditional rollback change set/execution to the fresh baseline. |
| Polling | One readiness poll every 15-30 seconds, at most 20 minutes per deployment/rollback. CI polling at 30 seconds or longer, at most 30 minutes per publication. Each blocking wait at most 60 seconds; communicate during work. |
| Logs | Query only the acceptance time window and known conversation/trace IDs; at most ten pages of 1,000 events per log group/window and one bounded delayed reconciliation for missing telemetry. No account-wide log scrape. |
| Browser | One isolated owned browser session, three fresh conversations; at most 12 bounded evidence screenshots. Screenshot failure alone does not authorize another agent send. |
| UI | At most one required owned UI restart for rollout and one restoration under conditional rollback. No unrelated listener/process changes. |

Reuse bounded existing readers; do not use embeddings/QueryVectors/Runtime invocation for readiness. Readiness metadata can still incur normal service charges. Approval of this plan covers these defined operations only; prior spent budgets remain spent.

## 7. Exact live conversation and citation matrix

Use the actual UI at `http://127.0.0.1:8010/`, pointing at the verified deployed DEFAULT endpoint. Start three genuinely new conversation IDs A, B and C, with distinct anonymous actors as produced by the existing UI. Preserve A's identity for A1-A2 and B's for B1-B4. Do not restart the UI or insert another message within those sequences. No separate preliminary model request.

| Slot | Conversation | Exact submitted text | Required public result and execution |
| --- | --- | --- | --- |
| L1 | A1 | `For Harbor, what is the mushroom pasta price and cancellation policy?` | Existing two-task multipart seed: complete Harbor price record RM32 per serving, wheat/milk; complete free cancellation at least 24 hours before the reservation and RM20 per booking late fee. Two original citations. Final unchanged approval establishes the one-venue context and admitted item. Ordinary Jev routing, with the existing Bedrock fallback only if actually needed. |
| L2 | A2, immediately after L1 | `And what about its cancellation fee?` | Deterministic `document_followup` resolution for Harbor. Fresh single policy retrieval/selection and full 24-hour/RM20 policy, one Harbor policy citation. No router/rewrite inference; do not answer from the L1 text or cached quote. |
| L3 | B1, fresh conversation | `Compare mushroom pasta prices at Harbor and Sakura.` | Existing two-worker comparison seed. Harbor RM32 and Sakura RM36 per serving; wheat/milk and Sakura dinner-only qualifier; Harbor cheaper by RM4. Two menu citations; approved pair/item context. Ordinary routing. |
| L4 | B2, immediately after L3 | `Which is cheaper?` | Deterministic comparison continuation for the same admitted pair/item, newly retrieved complete prices and RM4 arithmetic, two correct menu citations. No new router/rewrite/planner inference. |
| L5 | B3, immediately after L4 | `What about its cancellation policy?` | Targeted Harbor-or-Sakura clarification, zero new citations and no source pin/embedding/vector query/selector/planner/rewrite. Final unchanged approval retains only the approved pending operation and candidates needed for one immediate reply. Do not select a venue arbitrarily. |
| L6 | B4, immediately after L5 | `Harbor` | Deterministic `resumed` resolution; fresh Harbor policy evidence and full 24-hour/RM20 policy, one correct policy citation. Preserve the actual HumanMessage `Harbor`; no router/rewrite inference, Sakura source or replay of the comparison question. |
| L7 | C1, fresh conversation after B is inspected | `Which is cheaper?` | `no_context` clarification asking for explicit restaurant names/menu item. Zero citations, router/rewrite/planner/selector/embedding/vector calls; no pair/item or pending operation inherited from B. Existing input/output moderation still applies. |

All seven requests must receive the existing input moderation and final output gate. Clarification has no answer-generation model call but is still a Runtime request and may use billable moderation/checkpoint services.

Required browser inspection order:

1. After L1, open its two source controls and inspect the full item/policy records.
2. After L2, open its policy control; then reopen both L1 controls in A and prove they still target L1's documents/answer associations.
3. After L3, open its two menu controls. After L4, open its two newly associated menu controls.
4. L5 must add no source control. After L6, open its policy control, then reopen both L3 controls in B to verify retained answer association.
5. Download the three unique originals through actual UI source controls: Harbor menu PDF, Harbor policy Markdown and Sakura menu Markdown. Each has one intended download, with byte/hash verification and inspected document location. Do not substitute the repository's sample files or a backend-only URL check.
6. Open C and send L7 only after the B sequence and retained associations have been recorded. C must not inherit B's context or citation controls into its new answer.

The 12 opens/reopens above and three unique downloads are the source allowance. UI label identities may be different across answers; verify the real document/version/generation/hash/location behind each control. Do not require one global `Source 1` label to refer to the same answer forever.

### Expected original identity and facts

Require fresh manifest agreement before using these historical expectations. A changed generation/source hash or price/policy record is drift, not permission to rewrite the expected answer after the fact.

| Original | Expected identity | Required inspected location/facts |
| --- | --- | --- |
| Harbor menu | `harbor-menu-v2.pdf`, version `v2`, 1,975 bytes; SHA-256 `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10` | PDF page 1; mushroom pasta RM32 per serving, wheat/milk. |
| Harbor policy | `harbor-policy.md`, version `v1`, 534 bytes; SHA-256 `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471` | `Reservations and cancellation`, lines 5-8; full 24-hour free window and RM20 per-booking late fee. |
| Sakura menu | `sakura-menu.md`, version `v1`, 383 bytes; SHA-256 `0ac797361e4fc9abc433685b26693e6d877ed6ad873c94110cd0e3a7be7e9637` | `Main dishes`, lines 5-11; RM36 per serving, wheat/milk, dinner only. |

No generation-switch experiment is authorized. The new live matrix can establish fresh retrieval spans under an unchanged active generation; the changed-generation behavior remains established by the offline fixture only.

## 8. Ordered execution instructions after sign-off

### Step 0 — Record approval and freeze the local review package

1. Record the owner's explicit approval of this concrete Phase B scope, including the seven attempted sends, source reads/downloads, image publication, two-leaf update, owned UI restart if required and one conditional rollback. Do not reinterpret approval of PRD preparation as execution approval.
2. Create a unique operation-owned ignored evidence directory, for example `restaurant-finder-api/.generated/followup-rollout-<UTC yyyyMMddHHmmss>/`. Keep a progress/attempt ledger there. Use a short owned staging path under the task's `tmp/` for exports if required by Windows path limits; record its resolved ownership and intended cleanup.
3. Re-read `git status`, branch/HEAD/remotes, all 30 path diffs, and the three Phase A receipts. Verify the 24 recorded source hashes and all 22 protected identities. Record this PRD's hash and the complete publication file list. A changed receipt/source or unknown extra change requires reconciliation before staging.
4. Preserve the warning PRD, both real environment files, all locks, original datasets/documents/catalog, prior manifests, evidence and the live UI staging tree. Do not delete previous failures or owner work.
5. The temporary Phase A helpers were removed. Do not try to run them as if present. Any new orchestration/audit helper must live in the owned ignored directory, contain no secrets, perform only this approved scope and be removed at closeout. Do not modify application source to make an audit pass.

**Checkpoint:** approval, preserved baseline, reviewable exact file list and unchanged Phase A implementation. Zero Runtime attempts and zero cloud mutation.

### Step 1 — Publish exact release source and inspect CI

1. Use the existing Git authentication. Confirm the authorized GitHub identity is `yukangzhen`, origin is the owner's repository and PR #1 remains open/draft with the expected head/base. Freshly compare the remote branch before pushing. Stop on another writer's change; never force-push or reset it.
2. `gh` was absent in the previous execution. Prefer available existing tooling; the proven fallback is Git Credential Manager credential retrieval into process memory followed by structured GitHub API requests. Never print/save a token, put it in a URL/command line, or treat browser login as proof of CLI authorization.
3. Stage exactly the 30 listed paths. Inspect staged names/count and full staged diff; run `git diff --cached --check`. Exclude the warning PRD and ignored artifacts. Use the existing configured author identity without inventing or changing it.
4. Commit the reviewed feature release, record `release_sha`, parent, changed paths and tracked source identities, then push normally to `origin` on `feat/document-multipart-rollout` once. Read back the remote SHA. If push outcome is uncertain, reconcile first rather than create another commit or blindly push.
5. Preserve the existing PR title/base/draft state and prior body sections. Append a concise follow-up release section with actual release SHA, local evidence, default-off behavior and the planned but unexecuted live gate. Use structured arguments or an exact body file with real newlines. Reattach PR #1 to the chat if required by the app.
6. Inspect the automatically triggered push and PR runs for this exact release. Require successful API/UI/infrastructure/quality jobs. A PR run may test a merge ref: verify the pull-request head association and actual checked-out source, rather than accepting an unrelated successful SHA.
7. Download fresh offline artifacts into owned evidence and inspect actual logs/reports. Require the section 2.1 test and evaluation counts, complete case/variant coverage, and no stale/missing follow-up report. Archive safe run URLs/IDs and report hashes. Do not dispatch a workflow or change its settings to bypass failure.

**Stop:** failing/missing CI, source mismatch, unrelated staged path or PR/remote drift. No build/push/deployment proceeds. A required source fix needs its own reviewed repair scope.

### Step 2 — Check tools, AWS readiness and fresh rollback authority

1. Inspect installed locked interpreters, Node/npm/CDK, Docker engine/buildx and AWS CLI using bounded commands. No installation/upgrade is authorized. Docker must report a usable Linux engine, not merely an open Desktop window. If unavailable, stop dependent build work and request the smallest concrete recovery decision; do not restart/reset it automatically.
2. Read AWS identity explicitly with `aws sts get-caller-identity --profile default --region us-east-2`. Require account `447393541969` and an authorized non-root principal. Expired login requires the owner to restore `aws login --profile default`; no credentials/config rewrite or hidden authentication workaround.
3. Read stack status, original deployed template, resources, outputs, Runtime description and DEFAULT endpoint. Require stable state and matching Runtime identity/version/image/multipart/guardrail binding. Privately capture the exact template and entire Runtime configuration for rollback; publish only allowlisted metadata. Record follow-up key presence/value, including absence.
4. Read the baseline ECR manifests/digests and retention/mutability configuration. Prove the fresh baseline image is fetchable and not selected for expiry by one additional unique tag. Do not edit ECR policies, overwrite a tag or substitute a historical older image as rollback authority.
5. Read the immutable guardrail `ih5xpt3qi946:1`, require READY and the accepted policy fingerprint `cbf24512ff86fcd0187d95424e868d0f4b5ee1199515bdd4b06363ccdfad176d`. Preserve the original guardrail and Runtime role policy fingerprint `6ff2a7301b03e26308a4a8c10a12716c57205775e7f0472c168818a527c80eaa`. No standalone moderation probe or IAM update.
6. Read the active pointer/derived manifest and index metadata. Historical bucket: `restaurantfinder-ragstack-documentbucketae41e5a9-vqrmcnuycjq5`, pointer `rag/active.json`, generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a`, ETag `"d3705246c1cc2a4fd7f694bc91553e95"`. Require the same six-original fictional corpus and Titan V2/512/float32/cosine index, top-k no greater than five, existing RAG enabled.
7. The historical vector index ARN is `arn:aws:s3vectors:us-east-2:447393541969:bucket/restaurantfinder-rag-447393541969-us-east-2/index/documents-titan-v2-512`. Verify metadata only. Read the three originals in section 7 through bounded verified source readers, close bodies and validate hashes/full facts. No retrieval/embedding/QueryVectors call is a readiness check.
8. Identify the listener/process on 8010 and establish ownership, interpreter, cwd/source revision, Runtime/profile/region and source-viewer configuration without dumping environment values. Historical owned UI cwd is `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/tmp/pinned-3771a4c-20261014005846/restaurant-finder-ui`. PID values from old receipts are hints only. Never stop a reused PID without fresh ownership proof.
9. If a UI restart may be required, privately capture its verified prior source and non-secret launch configuration for restoration. The only UI feature change in Phase A is a test; its application tree should match the accepted release. Reuse the listener if source/configuration are correct. Stop rather than kill an unrelated/unknown listener.

**Checkpoint:** fresh baseline template/image/key semantics/guardrail/prompts/corpus/UI, exact rollback authority and zero Runtime attempts. Drift must be resolved before mutation, not explained away afterward.

### Step 3 — Export committed source and verify existing prompts

1. Export the exact `release_sha` API subtree to short owned staging with Git blob bytes, for example `git -c core.autocrlf=false archive --format=tar --output=<owned archive> <release_sha> restaurant-finder-api`, followed by extraction into the verified owned directory. Compare every staged tracked API file to the selected commit, not the mutable working directory.
2. Build only from this clean export. Keep the existing Dockerfile and lockfile unchanged. Its current `.dockerignore` excludes `.env`, virtual environments, tests and sample documents, but does not broadly exclude every `.generated` directory. Never build from the working API folder containing private receipts. Enumerate the actual build inputs and expected packaged paths; importable runtime modules must not be pruned based on their names alone.
3. Add only the retained manifest from `restaurant-finder-api/.generated/multipart-rollout-20261013032223/nine-prompt-manifest.json`, SHA-256 `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9`, as `.generated/prompt-manifest.json` beneath the staged API root, matching the accepted packaging location. Do not copy the whole generated tree or rewrite the older eight-prompt manifest.
4. Read back all nine pinned immutable CHAT prompt variants using the approved profile/region. Match committed local prompt definitions, immutable IDs/versions/ARNs, system text, user placeholder and input variables. No new resolver prompt exists. Missing/mismatched management data is a stop, not permission to run `sync_prompts`.
5. Validate the staged manifest using the existing locked API interpreter and the read-only `src.deployment.validate_prompts` entry point, in a fresh process with explicit absolute manifest path, prompt synchronization off, metadata lookup off, live evaluation/observability off and real `.env` absent. Require nine matches and exit 0. Do not import/start `src.main`.
6. Export/compile committed infrastructure with installed locked dependencies for a no-lookup source synthesis. With explicit account `447393541969`/region `us-east-2`, use `-c imageUri=<candidate image URI> -c documentMultipartEnabled=true -c documentFollowupsEnabled=true -c guardrailId=ih5xpt3qi946 -c guardrailVersion=1` and `--no-lookups`, writing the assembly only beneath the owned staging root. Assign/record the unique candidate URI before synthesis and recheck it before building. Compare the generated Runtime values against the intended proposal; the live full-template comparison below remains authoritative. Never deploy all stacks merely to enable this one flag.

**Checkpoint:** exact export, manifest hash/read-backs, offline validation and committed infrastructure provenance. No model/agent startup or prompt mutation.

### Step 4 — Build, audit and publish one image

1. Generate a unique tag `document-followups-<release SHA first 7>-<UTC yyyyMMddHHmmss>-arm64` in existing `restaurantfinder-agent`. Read ECR to establish absence; failed access is not absence. Record image intent before build. Do not use `latest` or overwrite a tag.
2. Use the existing Dockerfile: `docker buildx build --platform linux/arm64 --load --label org.opencontainers.image.revision=<release_sha> --metadata-file <owned metadata path> --tag <unique image URI> <staged API root>`. Record command exit and resolved base/build provenance. The mutable base tag means no byte-identical rebuild claim is permitted.
3. Require linux/arm64, exact revision label, unprivileged UID 1000 and normal `opentelemetry-instrument python -m src.main` command. Audit the image with entrypoint overridden and `--network none`; hash the packaged runtime files/manifest against the expected staged Git bytes. Avoid dependency-directory scans that exceed the audit bound. Do not launch the agent or infer success from an image tag alone.
4. Recompute expected packaged path count for this release; the old count of 82 is historical. Verify the two new runtime modules are present. Require no real environment files, secrets, tests, sample originals, downloads, private reports or helpers in the image. Record actual inspected paths/count/hashes without exposing credentials.
5. If a build fails before publication, reconcile engine/image/tag/metadata first. The one permitted corrected pre-publication retry may use the same unchanged source/manifest and tag only after proving no image was published. A Docker outage still requires separate recovery authorization. Two failed builds or any source/manifest change stops this plan's build allowance.
6. Authenticate to only this ECR registry using the existing supported method. Keep login tokens in process memory/stdin. If temporary Docker auth configuration is needed, put it in an owned directory with current-user ACL and the verified engine endpoint; do not change global Docker configuration. Clear credentials in `finally`, including on failure.
7. Push the single audited unique image once. Read back registry index, linux/arm64 runnable child and configuration digests; preserve attestation distinctions. Docker 29 may expose an OCI index as the local image ID, so do not call that the config digest. Reprove baseline rollback digest retention/fetchability.

**Checkpoint:** one audited/published source-bound image, actual digests and retained rollback image. No Runtime update yet.

### Step 5 — Review exactly two template differences

1. Re-read the stable live template/Runtime/pointer immediately before proposal. Require equality with the fresh Step 2 baseline; a drifted baseline invalidates the prepared rollback/proposal.
2. Copy that exact original template and change only these leaves on `Resources.restaurantFinderAgentCoreRuntime.Properties`:
   - `AgentRuntimeArtifact.ContainerConfiguration.ContainerUri` to the unique audited image URI.
   - `EnvironmentVariables.DOCUMENT_FOLLOWUPS_ENABLED` to string `"true"`, adding the key if absent.
3. Compare the full parsed templates after temporarily restoring those two leaves to their baseline presence/value. Require equality, unchanged parameters/outputs/other resources, multipart true and guardrail `ih5xpt3qi946:1`. Do not reconstruct a partial template from guesses or expose raw environment values.
4. Create one named UPDATE change set with existing stack parameter values and appropriate existing capabilities. Review actual changes/details: exactly one modified existing Runtime, `Replacement=False`, no creation/deletion and no `RequiresRecreation` demand. Any IAM/guardrail/endpoint/resource change or unexpected dynamic change is a stop before execution.
5. Record reviewed proposal SHA-256, image digest/source/manifest identity, exact changed paths and change-set ARN/summary. Just before execution recheck live baseline and image identity again. Approval of this PRD permits execution only of this conforming proposal; a broader diff needs new approval.

### Step 6 — Execute once, verify readiness and prepare UI

1. Execute the reviewed change set once and record intent/outcome. If outcome is uncertain, reconcile stack/change-set/Runtime state before any additional mutation; never execute blindly again.
2. Poll within section 6 bounds. Require stack UPDATE_COMPLETE, matching new image/follow-up flag, unchanged multipart/guardrail and matching READY Runtime/DEFAULT with the endpoint's live version targeting the new Runtime version. Do not assume the next version must be 17; measure it.
3. Compare the full deployed template to the reviewed proposal, all physical mappings/outputs and all other Runtime settings to the baseline. Recheck guardrail/index/pointer identities and rollback image. Failure enters the conditional rollback decision; no warm-up or extra model call establishes readiness.
4. Reuse the verified owned UI if its application bytes/settings match the release. If a restart is necessary, first prove ownership/capture restoration, then stop only that process and launch the exact release UI with the installed locked interpreter, loopback 8010, source viewer enabled and explicit profile/region/Runtime settings in an isolated process. Use `Start-Process -WindowStyle Hidden`; preserve real `.env` files. Require listener/HTTP readiness without sending an agent message.
5. Prepare a fresh isolated browser session using the established Playwright workflow/skill, explicit session ownership and safe browser evidence directory. Confirm UI configuration and absence of inadvertent auto-sent messages. Do not use an old conversation/checkpoint as a seed.

**Checkpoint:** conforming new deployment and owned ready UI, still zero attempted acceptance sends.

### Step 7 — Execute the seven-slot matrix and inspect originals

1. Create a ledger containing L1-L7 and their conversation dependencies before sending. Reserve a slot durably before the single UI submission; record attempted/completed/uncertain state, safe conversation correlation, response decision, route/mode and source count. Never let a failed helper leave an uncounted attempted send.
2. Submit each exact message once, wait for the final output/source controls, and inspect it against section 7. Capture evidence before proceeding to the dependent next message. Keep actual wording and full policy/menu qualifiers; a partial fee/price quote cannot pass merely because the numeric value is right.
3. A failed/blocked/masked output or source contract stops acceptance immediately. Do not compensate by choosing different wording, injecting checkpoint/context data or resending a seed. Record unused dependent slots and consider the conditional rollback.
4. Execute the specified 12 source opens/reopens and three downloads within the successful sequence. Verify associations, original bytes/hash and document/page/section/line locations. Wait for asynchronous PDF load; a tool timeout may be reconciled from bounded existing UI snapshots without another agent request.
5. Keep source-download/browser evidence private. Do not store or publish signed URLs, raw provider errors, auth headers, personal information or live context JSON. Capture only the fictional controlled answers and necessary source evidence, sanitized where applicable.

**Checkpoint:** exact attempts/results, source originals/association evidence and either seven verified public passes or an explicit failed/remaining matrix. No troubleshooting requests.

### Step 8 — Inspect telemetry and the live context lifecycle

1. Correlate the actual acceptance invocation/session/trace identities within the small execution window. Relevant historical groups are `aws/spans`, `/aws/vendedlogs/bedrock-agentcore/restaurantFinder-telemetry` and `/aws/bedrock-agentcore/runtimes/restaurantFinder_Agent-Ha58oX5Psu-DEFAULT`; `aws/spans` has no leading slash. Respect the bounded query allowance.
2. Inspect `rag.followup.resolve` enum/count/boolean attributes: `rag.followup.decision`, `reason`, `operation`, `restaurant_count`, `context_valid`, `resumed` and `mode`. The two explicit seeds should be `not_applicable`; L2/L4 resolved, L5 ambiguous clarification, L6 resumed, L7 no-context clarification. Record actual values rather than inventing expected traces.
3. Recognized continuations/clarifications should identify provider `document_followup`, not a fake Jev/model/confidence. Seeds use existing Jev routing or its observed Bedrock fallback. A fallback is permitted existing behavior when evidenced, not proof Jev handled the request.
4. Supported-answer turns L1/L2/L3/L4/L6 must show fresh retrieval/selection under the active pinned generation. L5/L7 must have no source retrieval/model generation, while still receiving moderation. Expected logical paths are one two-task multipart seed, two two-worker comparisons and two single-policy selections; do not infer exact SDK request counts from those logical paths alone.
5. Inspect unchanged final approval and citations; successful consecutive UI requests plus resolver attributes establish that approved state was usable through the actual checkpointer. L6 establishes pending-operation persistence/resumption, and L7 establishes isolation for these distinct fresh conversations. No direct checkpoint dump is necessary or authorized by this plan.
6. Verify original human turns remain the user input to parent conversation saving where safe existing evidence supports it. Do not publish `Harbor` rewritten as a user utterance or infer durable event totals from SDK CreateEvent spans, which also include checkpoints. Missing visibility must be marked unmeasured.
7. Check new span fields for payload leakage and forbidden resolver/rewrite/web/browser/repair/replan operations. Duplicate chat-model instrumentation spans do not automatically mean duplicate logical inference. Use logical workflow evidence and observed SDK retries distinctly.
8. If required traces are delayed, make one bounded reconciliation of the same window; no extra live request. Missing evidence leaves B08 pending and prevents a complete retain decision unless a separately reviewed verification path establishes it.

### Step 9 — Decide retain or execute the single conditional rollback

Retain only after B01-B08 are established and all protected/configuration checks still match. Record actual source SHA, image digests, new Runtime/DEFAULT version, flag/pair, seven attempts, source hashes and telemetry limitations. Do not mark B09 complete until closeout/cleanup is verified.

Rollback is permitted once under the signed-off scope if the forward update fails or remains unready, a required public answer/moderation/citation/context contract fails, or the required verification cannot establish a conforming accepted release within its bounds. Stop further acceptance sends first.

1. Capture current failure state and cause safely. Never override another actor's concurrent cloud change. If the live template differs beyond this plan's two leaves, stop for a recovery decision rather than overwriting drift.
2. Prepare a fresh rollback proposal restoring the Step 2 baseline image URI and exact prior presence/value of `DOCUMENT_FOLLOWUPS_ENABLED`. Remove the key if it was originally absent. Preserve multipart true and guardrail `ih5xpt3qi946:1`; do not restore historical Runtime 15 or disable earlier accepted features.
3. Review its change set as one existing Runtime modification without replacement, execute once, and require stable stack and READY matching Runtime/DEFAULT. Version numbers may increase; rollback does not mean the numeric version returns to 16.
4. Restore the verified owned UI source/configuration only if this rollout changed it and restoration is necessary. Confirm image/configuration/corpus/resource equality to the baseline through read-only checks; no post-rollback inference is included.
5. Preserve the new image, commits, immutable prompts, receipts, telemetry and stored events. Rollback cannot erase publication or service charges. No image/resource/event deletion is approved. A failed rollback or need for another mutation exceeds this allowance and needs a concrete recovery decision.

Mark the feature rollout failed/recovered, not accepted, if rollback is used. Do not continue remaining L slots against the recovered old image as if testing the extension.

### Step 10 — Publish honest closeout and clean up

1. Update only the five permitted documentation paths with observed execution status, criterion table, release source/image/Runtime identity, CI links, actual attempted/unused slots, source inspections, retain/rollback decision, cleanup and validation gaps. Keep planning/historical records recognizable and avoid retroactively rewriting failures as passes.
2. If all acceptance passed, describe the extension as deployed and accepted for this seven-request matrix. If stopped/rolled back, say so and identify the next required repair or verification. Do not claim exact dollar savings, live latency gain, broader isolation or production readiness.
3. Commit/push one documentation-only closeout to the same branch, preserving the existing draft PR. Inspect its automatically triggered exact-source CI and artifacts; verify API/UI/infrastructure/CI trees remain identical to `release_sha`. Do not rebuild/redeploy because a documentation SHA differs. Record final docs SHA and CI in private receipts/PR body since a commit cannot contain its own future SHA/run result.
4. Recheck all 22 protected identities, owner warning exclusion, remote/PR state, retained deployed/baseline image, pointer/guardrail/settings and local worktree. Final receipts must distinguish implementation release from documentation closeout and deployment acceptance from rollback.
5. Remove only owned temporary scripts, auth material, build exports/caches and temporary audit containers after checking resolved absolute containment, ownership and reparse points. Use native PowerShell literal paths; never pass enumerated paths into another shell for deletion. Preserve receipts, safe browser/source evidence, prior failures and any source tree backing the live UI.
6. Close only the owned browser session. Leave the verified UI available if retained. Reconcile actual operation allowances and append a concise checkpoint for the next engineer. Stop before the demo walkthrough or any new feature implementation.

## 9. Evidence package and reporting limits

Keep evidence private under the owned ignored operation root. The safe closeout summary should reference these categories, with actual identities/hashes and criterion results:

- Approval, source/protected baseline, exact allowlist and release/closeout SHAs.
- GitHub/PR read-back, exact CI run associations and inspected report/log hashes.
- Fresh AWS template/configuration/resource/endpoint/corpus/guardrail baseline and rollback authority.
- Staged Git source, immutable nine-prompt validation, build metadata, network-disabled image audit and registry digest chain.
- Forward change-set proposal/review/execution/readiness and full-template/resource comparison.
- Owned UI/source/interpreter readiness and isolated browser ownership.
- Seven-slot attempted/result ledger, safe answer/source association evidence, three downloaded original hashes and locations.
- Sanitized correlated routes/resolver/retrieval/moderation evidence, observed retry counts and explicitly unmeasured internals.
- Retain/rollback decision, documentation CI/source equality, protected-file checks and cleanup verification.

Never store credentials in a receipt or export raw Runtime environment, live context/owner hashes, provider response bodies or signed URLs into public documentation/CI artifacts. A privately captured rollback template must stay ignored and access-controlled if it contains sensitive configuration.

Live throughput, exact HTTP attempt totals, true per-turn dollar cost, long-session behavior, concurrent multi-user isolation, SDK thread termination after timeouts, every durable memory/checkpoint event and changed-generation live behavior are outside the acceptance claim unless separately evidenced. The offline regression already establishes many contracts with simulated dependencies; keep that evidence distinct from the live seven-case matrix.

## 10. Remaining decisions and approval

No additional application design decision is required: Phase A's bounded grammar, output-approved context, one immediate clarification reply, fresh retrieval and default-off compatibility have passed local acceptance. Fresh cloud/source state, authentication, Docker availability and exact release/image/version values are execution prerequisites, not facts to invent while drafting this plan.

The owner's AGENTS.md requires review/sign-off before external publication and costly/cloud actions. **Next approval:** proceed with Phase B as defined here: 30-path publication to existing draft PR #1; exact CI inspection; bounded cloud readiness/provenance reads; one audited ARM64 image with at most one reconciled pre-publication build retry; a two-leaf Runtime update; seven attempted live acceptance requests; three original UI downloads and specified source inspections; owned UI restart only if needed; one conditional rollback; and documentation-only closeout. Docker restart/reset, application repair and demo remain outside that approval.

## 11. Execution record

At PRD preparation: local inspection and this document only. The 24 Phase A source hashes and 22 protected hashes were rechecked with zero drift. The 30-path publication list was checked against the existing Phase A list plus this new PRD. No implementation tests were rerun. No commit/push, remote CI inspection, AWS read, Docker operation, inference, UI restart, deployment or rollback was performed for Phase B. B01-B09 are PENDING. Append actual approval, commands, receipts, decisions, failures and final criterion results here during execution; never treat a planned step as completed evidence.

### Phase B execution approval

The owner's subsequent **proceed** authorized this reviewed Phase B scope on 2026-10-14. The allowance is seven attempted UI requests, one audited unique image with at most one reconciled pre-publication build retry, one conforming forward Runtime update and one conditional rollback. Existing guardrail/multipart/prompts/corpus/IAM remain preserved. Docker recovery and application repairs require their own decision. Stop before the demo walkthrough.

Private operation receipts: `restaurant-finder-api/.generated/followup-rollout-20261014075434/`. Reserve every live slot before sending; do not inherit prior spent allowances.

## 12. Phase B execution and acceptance

**Decision:** Retain READY Runtime/DEFAULT 17. All seven exact requests passed through the owned actual UI and deployed Runtime. The allowance is exhausted: seven attempted sends, zero remaining, zero UI resends and zero rollback attempts. No demonstration or benchmark started.

### Release and deployment provenance

| Item | Observed outcome |
| --- | --- |
| Source publication | Release `11590ea927076e96c92b251912f8747ba0732085`, parent `574cc6304b1be4060cb8d281657c84303e6eb357`. Exactly the 30 reviewed paths, one normal release push to origin; owner warning excluded. Existing PR #1 remains draft against `feat/jev-router`. |
| Exact-release CI | [Push run 38532357388](https://github.com/yukangzhen/restaurant-finder/actions/runs/38532357388) and [PR run 38532361571](https://github.com/yukangzhen/restaurant-finder/actions/runs/38532361571) passed all four jobs. Downloaded reports/logs confirm 258 API, 32 UI, 53 infrastructure tests and full 17/20/40/24 evaluation coverage with 374/260/609/1,147 checks. |
| Prompts | The retained nine-prompt manifest SHA is `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9`. All nine immutable CHAT versions matched committed system text, user placeholder, variables and metadata. No synchronization or new prompt version. |
| Image | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:document-followups-11590ea-20261014082247-arm64`. One successful build, one image push, no build retry. Offline network-disabled audit verified all 87 packaged files, including 76 runtime source files, sole generated manifest, UID 1000 and normal instrumented command without agent startup. |
| Registry digest chain | OCI index `sha256:fe3763ab8be2b66a3c7e3b99b25d1cab14c6bdc6dc52532c4b12ab1ac1866163`; runnable linux/arm64 child `sha256:258c7d60a341c20df5cf8954618d5e5e18dcf302a088c33aa50f6925862dfd9b`; config `sha256:722a0dd0b52a065ba8b1a4607f1e2a277172789a6f798bd9b04f100c0e47e9a0`. Registry config and exact revision label verified. No byte-identical rebuild claim. |
| Rollback authority | Fresh READY Runtime/DEFAULT 16, accepted pinned-guardrail image, follow-up key absent. Baseline image remained fetchable after the new push and final deployment check. No older trial/comparison image substituted. |
| Forward change | Reviewed change set `followups-11590ea-20261014084304`: one existing Runtime Modify, Replacement False, both property changes RequireRecreation Never. Exactly ContainerUri and follow-up flag changed; one execution. |
| Retained state | Stack UPDATE_COMPLETE; Runtime and DEFAULT READY/live at 17. Full deployed template matches proposal, all 18 physical mappings/outputs and both captured inline IAM policies preserved. Multipart true, follow-ups true, immutable pair `ih5xpt3qi946:1`; active generation and pointer ETag unchanged. |
| UI | Verified existing owned UI on `127.0.0.1:8010`, correct profile/region/Runtime/source viewer and committed application bytes. No UI restart or Docker recovery was required. One isolated browser session used the actual New Chat controls for A, B and C. |

### Exact public and workflow acceptance

| Slot | Inspected result |
| --- | --- |
| L1 | PASS: Harbor two-part seed, answered 2/2; full RM32-per-serving/wheat/milk record and complete 24-hour/RM20-per-booking policy; two sources. |
| L2 | PASS: same A, resolved singular fee follow-up; full newly selected Harbor policy, one new source. Both retained L1 controls still opened their own documents after L2. |
| L3 | PASS: fresh B, existing comparison; RM32/RM36 per serving, wheat/milk and Sakura dinner-only qualifier; Harbor RM4 lower; two sources. |
| L4 | PASS: same B, `Which is cheaper?`; same admitted pair/item through a fresh comparison, correct complete prices/difference and two new sources. |
| L5 | PASS: same B, targeted `Harbor Pasta Lab or Sakura Table Lab?` clarification; zero new sources and no retrieval/planner/selector/rewrite. |
| L6 | PASS: immediate `Harbor` reply; resumed Harbor policy only, full conditions and one citation. Actual displayed human input remained `Harbor`; both older L3 controls remained correctly associated. |
| L7 | PASS: genuinely fresh C, `no_context` clarification requesting explicit restaurant(s)/item; zero sources or retrieval/model generation. Three distinct session identities were verified from correlated traces. |

All 12 specified citation opens/reopens passed with correct document/page/section/line records. Twelve bounded source screenshots were retained privately. Three unique original downloads were performed by actual UI clicks; duplicate local saves of the same browser download do not represent additional fetches:

| Original | Bytes | Verified SHA-256 |
| --- | --- | --- |
| harbor-menu-v2.pdf | 1,975 | `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10` |
| harbor-policy.md | 534 | `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471` |
| sakura-menu.md | 383 | `0ac797361e4fc9abc433685b26693e6d877ed6ad873c94110cd0e3a7be7e9637` |

### Correlated traces and limits

The bounded acceptance-window read retained 305 sanitized spans. Seven invocation/workflow traces match the attempt ledger and the A2/B4/C1 session pattern. The two explicit seeds used Jev; five continuations/clarifications recorded `document_followup`, with no router or query-rewrite call. Observed resolver reasons were not_applicable, resolved, not_applicable, resolved, ambiguous_venue, resumed and no_context.

Logical execution comprises one multipart planner, two multipart workers, four comparison workers/selections, two single-policy selections, eight embeddings and eight vector queries. Maximum observed worker overlap was two. Nineteen captured generation attributes matched the active generation. Eighteen chat-model instrumentation spans represent overlapping instrumentation of these nine planner/selection paths; they are not reported as eighteen logical generation calls.

There were seven input checks, seven approved unchanged final output gates and seven parent `memory.save` spans. Six observed SDK retry attributes belong to AgentCore ListEvents/CreateEvent operations, which completed successfully. No UI send was retried. The 84 SDK CreateEvent spans include checkpoints and do not establish 84 durable conversation events, or a separate durable-event total.

All seven observed application resolver attribute sets matched the committed fixed enum/count/boolean contract plus session correlation. A one-event raw schema review identified three additional standard exporter keys: `PlatformType`, `aws.local.environment` and `aws.local.service`; raw values were not saved. No private context, owner hashes, user/effective-question text, quotes, source keys or provider bodies were added by the resolver's committed setter. The raw exporter schema was inspected for one known event; no account-wide log scrape or checkpoint dump occurred.

Exact vector-filter payloads/pin-read counts, every uncaptured HTTP attempt, SDK thread termination, durable checkpoint/conversation event totals, long-session/concurrent-user coverage, live generation switching, latency/throughput and dollar cost remain unmeasured. Changed-generation behavior is established by the separate offline fixture, not this unchanged-corpus rollout.

### Tooling reconciliation and preservation

Routine helper assumptions were corrected without application changes: Git status leading whitespace, retained stack receipt shape, guardrail fingerprint projection, response metadata in lifecycle comparison, Windows dependency-path walking and the installed CDK executable name. GitHub's delayed PR-head read-back was reconciled after the single successful push. Initial Docker login failed before any image push; the prior proven owner-only scoped auth-file method succeeded, and its temporary credentials were removed. Global Docker configuration was preserved.

One response read occurred before citation controls finished attaching; the completed UI state was inspected without resending. The targeted clarification used the catalog's full aliases rather than the verifier's initial short-name expectation. Cloud/client timestamp skew required symmetric bounded correlation; no timing/performance gain was inferred. CloudWatch continuation tokens and standard exporter labels were reconciled separately from the application contract.

Automatic approval review rejected broadening sandbox ACL access to the private evidence directory. That change was not performed. The directory remained owner-only; non-sensitive helpers/build exports used a separate owned staging directory and authorized owner execution handled private receipts. No user credentials/configuration, owner warning, locks, original datasets/documents, corpus pointer, prompts or IAM permissions were changed.

### Criteria before documentation closeout

| ID | Status |
| --- | --- |
| B01 | PASS: exact 30-path release publication and draft PR read-back. |
| B02 | PASS: both release runs and downloaded artifacts inspected. |
| B03 | PASS: fresh baseline/rollback, immutable policy and IAM fingerprint, corpus, originals, prompts and UI verified. |
| B04 | PASS: audited unique ARM64 image, registry/source/manifest provenance and cleared auth. |
| B05 | PASS: exactly two leaves, one execution, READY/live 17, full-template/resource/settings/pointer preservation. |
| B06 | PASS: seven exact public requests, approved unchanged, three distinct conversations. |
| B07 | PASS: 12 source inspections, retained associations and three hash-verified original downloads. |
| B08 | PASS: correlated routes, resolver decisions, fresh retrieval/selection, moderation and bounded safe evidence. |
| B09 | PENDING until documentation-only publication/CI, final protected-file verification and owned cleanup are inspected. |

The packaged image remains tied to release `11590ea`; the later documentation commit does not trigger a rebuild or Runtime mutation. Its exact SHA and subsequently completed CI are recorded in the private closeout receipt and existing PR body because a commit cannot contain its own future SHA/run result. Stop before the demo walkthrough.
