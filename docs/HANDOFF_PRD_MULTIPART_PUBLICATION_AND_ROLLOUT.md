# Handoff PRD: Publish and validate the multi-part document workflow

**Status:** Owner approved execution with “proceed” on 2026-10-13. Local implementation, publication, the scoped AWS update, conditional rollback, UI restart and a fresh maximum of six Runtime attempts are authorized. Execution is in progress.

**Audience and purpose:** The project owner and execution agent delivering a controlled AI engineering portfolio demonstration. Establish that the locally verified workflow works through GitHub CI, the deployed AgentCore Runtime, and the actual source viewer before adding another feature.

**Repository:** [yukangzhen/restaurant-finder](https://github.com/yukangzhen/restaurant-finder).

**Workspace:** `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.

**Inspected starting point:** `feat/jev-router`, HEAD `081e0fb51d13cba9838ca5bf01762997ddef79ef`.

## 1. Outcome, deliverables, and stopping point

Publish the completed mixed menu-price/cancellation-policy feature in a narrowly scoped draft PR, deploy one traceable API image with the feature explicitly enabled, load the updated local UI, and inspect six bounded real requests with their original documents and available traces.

Deliverables:

1. A default-off CDK setting for the new flag, with offline checks and documented enablement. This is the only new implementation work in this phase.
2. A feature commit and draft PR against the existing enhancement branch, with inspected CI for the exact release source.
3. A separately generated, validated nine-prompt manifest and an audited ARM64 image tied to that source and manifest hash.
4. A fresh rollback snapshot and one reviewed CloudFormation UPDATE changing only the existing Runtime's image and `DOCUMENT_MULTIPART_ENABLED` value.
5. At most six live Runtime invocation attempts, including complete/partial/clarification/compatibility behavior, PDF/Markdown original-source inspection, and available correlated tracing.
6. An execution record with actual SHA/digest/versions, CI receipts, attempt usage, criterion results, rollback decision, and remaining measurement gaps.

Stop after technical release validation and documentation. Further functionality, unrestricted planning, benchmarks, a demo walkthrough, video, public hosting, and LinkedIn publication are outside this phase. This does not establish production readiness, broad model accuracy, cost savings, or improved latency.

## 2. Evidence already inspected

### 2.1 Local implementation

The [implementation PRD](HANDOFF_PRD_MULTIPART_DOCUMENT_WORKFLOW.md) records the approved local work completed on 2026-10-13. Its results were inspected; preparation of this rollout document did not rerun the suites.

| Existing evidence | Result |
| --- | --- |
| API regression suite | 196 tests, OK. |
| UI regression suite | 31 tests, OK. |
| Original document RAG evaluation | 17/17; 374 measured checks; no failed/missing cases. |
| Comparison evaluation | 20/20; 260 measured checks; no failed/missing cases. |
| Multi-part evaluation | 40/40; 609 measured checks; no failed/missing cases. |
| Workflow | Five bounded forms; one checked model plan; 2-4 tasks; maximum two concurrent workers; one pinned generation; deterministic assembly. |
| Evidence | Complete menu records and controlled Markdown cancellation sections; exact quotes/provenance; price arithmetic only with validated matching facts. |
| Approval and UI | Parent moderation/memory integration; up to four approved sources; partial coverage; verified original-byte loading. |
| Configuration | `DOCUMENT_MULTIPART_ENABLED=false` in settings/example; real environment files and deployed configuration were not changed. |
| Publication | 25 feature files remain uncommitted; unrelated warning PRD is separately untracked. No remote multipart CI or live multipart result exists in this inspected evidence. |

The generated reports identify simulated dependencies. Live Jev routing, Haiku plan/selection quality, Titan ranking, actual source clicks, concurrency in AWS, latency, and cost are unmeasured for this feature.

### 2.2 Findings that affect this release

- The current local `.generated/prompt-manifest.json` contains eight prompts, SHA-256 `0d1b1e71dd2195a9aa3fcfcd7ac690b0ade28f4cfb1b6be12eae8788f03f6e6a`. New API code requires nine, including `RAG_MULTIPART_PLAN_PROMPT`, even with the feature disabled. Generate a new manifest in this release's staging area; preserve the old file and old release artifacts.
- `sync_prompts.py` visits all nine definitions. `PromptManager` reuses matching immutable versions before considering draft updates/version creation. Verify the eight old definitions first; this phase permits writes only for the new planner prompt. Do not disguise synchronization as a read-only packaging check.
- Runtime prompt text is local and metadata is packaged; adding this definition does not itself require Runtime prompt-management permissions. Do not expand Runtime IAM to solve a deployment-identity denial.
- CDK currently enables document RAG but does not define the multipart flag. Add a default-off context/stack property before publication so future synthesis represents the feature setting.
- Local `main` and its unrefreshed tracking reference still point at the original initial commit. A PR to that base would include older enhancement work. Use a new branch based on the verified `feat/jev-router` baseline and target that branch for review; do not merge to `main`.
- Offline CI runs on pushes and pull requests. The existing deployment workflows run on relevant `main` pushes or manual dispatch; the destruction workflow is manual. This phase uses neither deployment workflow nor a main merge.
- The normal Docker context contains generated evidence that `.dockerignore` does not comprehensively exclude. Build from a committed-source export plus the one manifest, never the working API folder.

### 2.3 Historical release: discovery hints, not current readiness

Local release receipts and the [comparison rollout record](HANDOFF_PRD_COMPARISON_PUBLICATION_AND_ROLLOUT.md) report the following state at `2026-10-12T11:45:59Z`. No fresh AWS, Docker, GitHub-authentication, remote-branch, or running-UI check was made while preparing this document.

| Item | Last recorded value |
| --- | --- |
| Account / region / profile | `447393541969` / `us-east-2` / `default` |
| AgentCore stack | `restaurantFinder-AgentCoreStack` |
| Runtime ID | `restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime / DEFAULT | READY / READY, version 13 / liveVersion 13 |
| Current image tag then | `comparison-be5c35d-20261012093655-arm64` |
| ECR repository / digest then | `restaurantfinder-agent` / `sha256:671e5c9c1ecc477aca287b4cefa83e06e9ef07e1eea678547d44181490f0da5a` |
| Document bucket | `restaurantfinder-ragstack-documentbucketae41e5a9-vqrmcnuycjq5` |
| Vector index | `arn:aws:s3vectors:us-east-2:447393541969:bucket/restaurantfinder-rag-447393541969-us-east-2/index/documents-titan-v2-512` |
| Active generation | `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` |
| Local UI address | `http://127.0.0.1:8010/`, loopback only |

The prior six-request allowance is exhausted. Prior Docker restart approvals were used. Neither carries into this phase. Capture a fresh baseline, including any difference from these hints, before writing to AWS.

## 3. Execution approval and consequences

**Preparation and execution approval are satisfied.** The owner's explicit “proceed” on 2026-10-13 approves this PRD's publication, prompt synchronization, image/flag update, conditional rollback, local UI restart, and fresh six-attempt allowance. Matching steps need no repeated generic confirmation. Ask only for a material deviation or a genuinely unavailable permission.

| Included after complete sign-off | Boundary |
| --- | --- |
| Local CDK flag change, specified tests/docs | Four infrastructure paths listed in section 6; no dependency or application redesign. |
| GitHub publication | New feature branch and draft PR to `feat/jev-router`; normal pushes and offline CI inspection; no merge. |
| Read-only readiness/baseline/telemetry | Existing account/resources, intended corpus and six controlled originals; no model probes. |
| Prompt synchronization | One execution from committed staged source; create/reuse the new planner's immutable version, reuse existing matching eight; no old draft/version deletion. |
| Build/publication | One unique ARM64 image; one corrected pre-publication rebuild for packaging/transient failure if no source change is needed. |
| AWS update | One reviewed existing-Runtime UPDATE for image plus multipart flag; no other resource/property changes. |
| UI | Start/restart only the positively identified project UI on loopback, using the locked environment and explicit task-local AWS configuration. |
| Functional validation | At most six Runtime attempts, sequential submissions, exact scenarios in section 9. |
| Recovery | At most one reviewed rollback restoring the fresh baseline image and exact prior flag presence/value, plus the prior UI source/configuration. |
| Closeout | Scoped documentation commit/push and its CI; retain safe receipts and remove only operation-owned scratch/auth material. |

Excluded: IAM/secret/credential/billing/quota changes; model replacements; new stacks/endpoints; guardrail/tracing changes; corpus ingestion, embeddings for ingestion, pointer changes or deletion; dependency upgrades; application fixes; changes to Actions settings/deployment workflows; workflow dispatch; force push/reset/rebase; Docker restart/reset or WSL shutdown; unrelated process cleanup; mass communications or public demonstrations.

Publishing source/PR documentation exposes the reviewed material on GitHub. Prompt/image creation and live usage may incur charges. Runtime rollback cannot undo publication, stored images, managed prompt versions, inference charges, telemetry, or memory events. Retain the new prompt/image on rollback; deletion is not part of recovery.

The allowance limits requests and logical workflow work, not dollars or all underlying AWS HTTP calls. If the owner requires a monetary ceiling, agree on it before execution rather than inventing one.

## 4. Definition of done

| ID | Required observable result |
| --- | --- |
| R01 | CDK omission/false keeps the multipart flag off; explicit true enables it; invalid context fails before deployment; no unrelated template change. |
| R02 | Exact allowlisted feature/IaC/PRD files are committed on the new branch. Draft PR targets the verified enhancement baseline and contains only this phase. Unrelated warning work is preserved. |
| R03 | All four push CI jobs pass for the exact release SHA. Inspected artifacts retain 196 API tests, 31 UI tests, all original infrastructure checks plus new flag checks, and 17/20/40 evaluation cases with no failed/missing cases. |
| R04 | Fresh intended identity, stable stack/Runtime/DEFAULT mapping, corpus/index/original hashes, UI source/configuration, and fetchable rollback image are captured. |
| R05 | Nine prompt entries validate against committed source and immutable read-backs. Old eight definitions/versions selected for packaging remain verified; no unauthorized old prompt mutation occurs. |
| R06 | Published image is linux/arm64, source matches release Git bytes, only the approved manifest is added, and actual ECR digest/build provenance are recorded. |
| R07 | Actual change set modifies exactly one existing Runtime without replacement, only image and multipart environment key; stack and DEFAULT become READY on the new configuration, with all other settings/resources/pointer unchanged. |
| R08 | L1-L6 meet their functional expectations within six total attempts; compound answers have complete task coverage or explicit partial coverage, correct facts and source numbering. |
| R09 | Actual Source 1-4 controls open intended PDF/Markdown originals; inspected/downloaded bytes and locations match pinned metadata; earlier answers in the same active UI session keep correct source association; source actions add no Runtime request. |
| R10 | Correlated live evidence establishes document routing, multipart execution and required safety boundaries. Measurable planner/worker/moderation/memory counts are inspected; unavailable internals are explicitly unmeasured. |
| R11 | Record all criteria, actual attempts, retain/rollback decision, release/doc SHAs, CI runs/artifacts, manifest hash, image digest and versions. Publish safe closeout docs and stop before demonstration. |

Use PASS, FAIL, BLOCKED or UNMEASURED, with evidence. Do not call the whole release validated when a mandatory scenario, source control, routing check, or deployment criterion is unresolved. A successful deployment alone is insufficient. Missing optional detailed telemetry is a validation gap, not automatically proof of a runtime regression.

## 5. Live allowance and operation bounds

Proposed new allowance: **six total Runtime invocation attempts**. Reserve a ledger slot before every send. A delivered/uncertain timeout, error, automatic UI resend, or direct diagnostic consumes a slot. A definitely local rejection before delivery is free only with supporting evidence. Never retry a prompt for free.

L1-L6 are the allowed scenarios. A diagnostic may replace a remaining scenario after explaining why; it does not add a seventh request and leaves the displaced criterion unresolved. Stop earlier on wrong routing, invalid evidence/arithmetic, provider error, timeout, extra worker/replan, or unexpected tool use. Do not spend remaining slots exploring a failure.

| Planned work for the six scenarios | Bound / expected behavior |
| --- | --- |
| Jev routing | Up to six classifications; existing Bedrock fallback may add up to six routing-model calls. Record actual provider; no forced fallback injection. |
| New structured planners | Three total: L1, L2, L4; one each, maximum 1,000 output tokens and five-second planner budget. L3/L5/L6 have no multipart planner. |
| Document retrievals/embeddings/vector queries | At most 12 logical worker retrievals: 4 + 2 + 4 + 2. One embedding and at most one vector query page per worker. L3/L5 perform none. |
| Selectors | At most 12 single-attempt selectors, maximum 1,600 output tokens each. An absent dish may be identified during selection rather than empty retrieval; record actual calls and any verified skips. Never promote an upper bound into an observed count. |
| Context | At most five hits and 9,000 evidence characters per worker, 36,000 per four-task request; prompt/schema overhead is additional. |
| Worker scheduling | Maximum two active multipart workers; one shared pinned generation; shared worker budget at most 45 seconds and document-node timeout at most 60. Up to 250 ms graph accounting uses assembly reserve. |
| Rewrites/web/repair | No multi-part replan, model repair, browser/web tool, nested comparison, or follow-up rewrite is expected. L3 has no approved single-restaurant scope to rewrite. |
| Moderation/memory | Existing input moderation, one final parent output moderation, and at most one approved-turn memory operation per attempted completed request. Provider-side memory processing/HTTP work is not inferred from one span. |
| Source inspection | Bounded original S3 reads through UI; no agent/embedding calls. Four sources have 5 MiB each / 20 MiB aggregate and existing 30-second preparation bound. |

Use distinct synthetic actors for the four conversations; L1/L2/L3 share one actor/conversation and run consecutively before any UI restart. Do not use a real person's name/data. Control-plane readiness, prompt management and original reads are not Runtime attempts but can still incur service charges. No warm-up, greeting, extra smoke probe, live evaluator, or post-rollback model check is included outside this ledger.

## 6. Exact source/publication scope

Proposed new branch: `feat/document-multipart-rollout`, starting at the inspected enhancement HEAD. Draft PR base: `feat/jev-router`. Verify remote state before branch creation; if the base moved or the proposed branch contains unrelated work, stop and reconcile rather than force-resetting it.

### Publication allowlist

```text
.github/workflows/ci.yml
README.md
docs/CI_AND_RAG_EVALUATION.md
docs/DOCUMENT_RAG.md
docs/HANDOFF_PRD_MULTIPART_DOCUMENT_WORKFLOW.md
docs/HANDOFF_PRD_MULTIPART_PUBLICATION_AND_ROLLOUT.md
restaurant-finder-api/.env.example
restaurant-finder-api/src/application/document_rag/comparison.py
restaurant-finder-api/src/application/document_rag/multipart.py
restaurant-finder-api/src/application/document_rag/multipart_workflow.py
restaurant-finder-api/src/application/document_rag/workflow.py
restaurant-finder-api/src/application/orchestrator/streaming.py
restaurant-finder-api/src/application/orchestrator/workflow/nodes.py
restaurant-finder-api/src/application/orchestrator/workflow/state.py
restaurant-finder-api/src/config.py
restaurant-finder-api/src/deployment/sync_prompts.py
restaurant-finder-api/src/domain/document_multipart.py
restaurant-finder-api/src/domain/document_rag.py
restaurant-finder-api/src/domain/prompts.py
restaurant-finder-api/src/evaluation/datasets/document_multipart.json
restaurant-finder-api/src/evaluation/document_multipart.py
restaurant-finder-api/src/infrastructure/prompt_metadata.py
restaurant-finder-api/tests/test_document_multipart.py
restaurant-finder-api/tests/test_prompt_metadata.py
restaurant-finder-ui/source_documents.py
restaurant-finder-ui/tests/test_source_documents.py
restaurant-finder-infra/bin/cdk.ts
restaurant-finder-infra/lib/stacks/agentcore-stack.ts
restaurant-finder-infra/test/document-rag.test.ts
restaurant-finder-infra/README.md
```

Exactly 30 paths are intended after the four infrastructure edits. Do not stage with `git add .`, `-A` or wildcard patterns. Inspect staged names and every diff. Preserve and exclude `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`; baseline SHA-256 is `C3F491550280BA5568CEA656D1E90378A76547EE5520E462A323469949AEBF9F`. Exclude `.env`, secrets, manifests, ignored evidence, downloads and unrelated owner edits.

Existing multipart application behavior is not redesigned here. A genuine application/CI packaging failure requiring another source change needs a concrete reviewed repair scope and fresh source/CI identity before image construction.

## 7. Ordered execution instructions

Each step states its completion evidence. Keep independent reads batched, mutations/approvals/checkpoints sequential, inspect every exit code, and provide concise progress at least once per minute. Do not install tools or silently broaden scope. All shell variables below are task-specific placeholders populated from inspected results, not invented values.

### Step 0 — Confirm scope and preserve the starting state

1. Record the owner's execution approval and the fresh six-attempt allowance in section 12 before acting.
2. Inspect applicable `AGENTS.md`, this PRD, the implementation record, worktree status, branch, HEAD and remotes. Confirm intended `origin` is the owner's repository; never push `upstream`.
3. Hash/preserve the warning PRD, original evaluation datasets, current eight-prompt manifest and any unrelated changes. Record the 25 existing feature files and this new plan separately from the four planned infrastructure edits.
4. Create a unique ignored evidence root under `restaurant-finder-api/.generated/multipart-rollout-<UTC timestamp>`; prove `git check-ignore` covers it. Resolve it inside the workspace before any extraction, deletion or move. Initialize ledger `maximum=6, used=0`.
5. Read remote branch refs and GitHub authentication/repository access without printing credentials. Verify remote `feat/jev-router` equals the intended baseline; identify any existing equivalent PR to avoid duplicates. Authentication failure is not proof of missing branch/resource.

**Checkpoint:** approval, ownership, exact starting SHA, private evidence directory and unused ledger recorded. No Runtime attempts.

### Step 1 — Represent feature enablement in CDK

1. Add optional boolean `documentMultipartEnabled` to `AgentCoreStackProps` in `lib/stacks/agentcore-stack.ts`. Omission must serialize the environment value `"false"`; true must serialize `"true"`.
2. Read context `documentMultipartEnabled` in `bin/cdk.ts` before constructing stacks. Accept boolean true/false and CLI strings `"true"`/`"false"`; omission is false. Reject ambiguous values such as `"1"`/`"yes"` before synthesis can be used for deployment. Pass the parsed boolean into the existing stack.
3. Add exactly `DOCUMENT_MULTIPART_ENABLED` to the Runtime environment mapping. Preserve all resource IDs, image selection, roles, model IDs, RAG/guardrail/browser/telemetry values, dependencies and permissions.
4. Extend the existing infrastructure tests: omission/explicit false stays off and explicit true is on; keep all three old checks. Compare same-image synthesized templates for false vs true and require only the new environment leaf differs. No new dependency is needed.
5. Update the infrastructure README with default-off semantics, explicit `-c documentMultipartEnabled=true`, rollback behavior and the reviewed change-set procedure. A later generic CDK deployment without that context will request false; make this visible in documentation rather than implying the runtime remembers prior CLI context.
6. Run the approved local checks from existing locked environments. API/UI use the isolated offline environment in the implementation PRD section 12. Infrastructure uses dummy account/region, metadata lookup disabled, existing installed tooling, and no AWS lookups:

   ```powershell
   npm run build
   npm test -- --runInBand
   npx --no-install cdk synth restaurantFinder-AgentCoreStack --no-lookups -c imageUri=123456789012.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:offline-ci -c documentMultipartEnabled=false --output $taskFalseSynth
   npx --no-install cdk synth restaurantFinder-AgentCoreStack --no-lookups -c imageUri=123456789012.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:offline-ci -c documentMultipartEnabled=true --output $taskTrueSynth
   ```

   Run an omitted-context synthesis and an invalid-context synthesis separately; require default false and a clear nonzero invalid result. Check each successful output and the recursive diff. Do not call `cdk deploy`.
7. Run final API/UI suites and all three offline evaluators using the exact implementation PRD commands. Require retained 196/31 test results and 17/20/40 cases; record actual new infrastructure count. No skipped or missing case may receive success.

**Checkpoint:** default-off IaC setting and tests/docs complete, only intended infrastructure paths edited, local checks pass.

### Step 2 — Publish the reviewed source and draft PR

1. Reconfirm remote base equality and absence/ownership of the target branch. Create `feat/document-multipart-rollout` without discarding uncommitted feature files. Do not reset, stash or rewrite unrelated owner work.
2. Review all 30 allowlisted paths for correctness, credentials and irrelevant changes; run `git diff --check`. Stage exact paths, inspect `git diff --cached --name-only` and the full staged diff; confirm warning/evidence/env exclusions.
3. Commit with a clear feature message. Record resulting `releaseSha`; it is the code/image source identity. Push that named branch normally to `origin`; read back its exact remote SHA.
4. Inspect the automatically triggered **push** CI run for `releaseSha`. Require API, UI, infrastructure and aggregate quality successful. Download the allowlisted artifacts into ignored evidence; inspect test counts and all three report schemas/cases/checks, not just a green badge. Do not dispatch a workflow or change Actions settings if it fails to start.
5. Create/reuse a draft PR with head `feat/document-multipart-rollout` and base `feat/jev-router`. Include what changed, local/remote offline evidence, default-off configuration, controlled language/layout limits and planned rollout; do not claim deployment or live success yet. Use structured PR fields or an exact body file with real newlines.
6. Verify returned PR head/base/SHA and changed-file scope. Attach every created PR to the current Codex task with `attach_artifact`. Inspect automatically triggered PR CI too; distinguish its synthetic merge checkout from the branch source. The passing push run for exact `releaseSha` is the image gate.
7. If source needs repair, stop with a concrete proposal; any approved repair changes release SHA and requires fresh CI. Do not build an image from a prior green commit while silently using later working files.

**Checkpoint:** published source, draft PR URL attached, exact-SHA passing CI and artifact receipt. No merge/main push/deployment workflow.

### Step 3 — Check readiness and capture fresh rollback evidence

1. Check existing tool versions, locked environments, AWS identity and bounded Docker engine/buildx readiness. Use intended profile/region explicitly:

   ```powershell
   aws sts get-caller-identity --profile default --region us-east-2 --no-cli-pager
   docker info --format '{{json .}}'
   docker buildx ls
   ```

2. Require account `447393541969`; inspect principal privately. If expired, ask the owner to restore the existing CLI login, then rerun identity only. Do not create credentials or change IAM. An account alias is not a CLI profile.
3. Require a working Linux daemon and linux/arm64 build capability. A normal supported start of a stopped Desktop is covered by full sign-off; a restart/reset/WSL stop or broad cleanup needs a separate specific recovery decision. Bound stalled commands and stop their operation-owned process; an existing Desktop process does not prove engine health.
4. Read stack/Original template, Runtime and DEFAULT without sending an application request:

   ```powershell
   aws cloudformation describe-stacks --stack-name restaurantFinder-AgentCoreStack --profile default --region us-east-2 --no-cli-pager
   aws cloudformation get-template --stack-name restaurantFinder-AgentCoreStack --template-stage Original --profile default --region us-east-2 --no-cli-pager
   aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id restaurantFinder_Agent-Ha58oX5Psu --profile default --region us-east-2 --no-cli-pager
   aws bedrock-agentcore-control get-agent-runtime-endpoint --agent-runtime-id restaurantFinder_Agent-Ha58oX5Psu --endpoint-name DEFAULT --profile default --region us-east-2 --no-cli-pager
   ```

5. Save privately the full original template, parameters/capabilities/execution role, physical IDs/outputs, Runtime environment/role/network/protocol/image/version and endpoint mapping. Require stable stack and READY matching Runtime/DEFAULT; check template vs actual configuration for drift. Reconcile a different legitimate baseline before writing rather than overwriting it.
6. Read ECR current image/digest and repository lifecycle/mutability. Prove the baseline digest is fetchable and survives one new push under retention rules. Do not use an older historical rollback image by habit or edit repository policy.
7. Read active-pointer content/ETag, its derived manifest and vector-index metadata through bounded existing readers. Require verified Titan V2/512/float32/cosine, top-k at most five, enabled document RAG, and the intended fictional corpus. No QueryVectors/embedding call is part of readiness.
8. Read all six intended originals with 5 MiB per-object bounds, close bodies, verify every SHA-256 against the fresh manifest, inspect the facts in section 8 and policy single-chunk layout. If generation/hash/layout changed, stop for revised expectations; never republish an old pointer to force a pass.
9. Identify port 8010's owner/command/source and current UI configuration without printing sensitive environment values. Capture a rollback UI export from its verified prior source revision plus non-secret required configuration and interpreter identity. If the source/configuration cannot be established, resolve that before stopping the process. Do not stop an unrelated listener.
10. Save exact rollback template/configuration, including whether the multipart environment key is absent or explicitly false. Historical Runtime 13 is a hint; fresh evidence is the rollback authority.

**Checkpoint:** fresh identity/readiness, rollback image/template/UI, verified six originals and corpus, zero Runtime attempts.

### Step 4 — Export exact source and synchronize the ninth prompt

1. Reconfirm source SHA and CI. Export the committed API subtree with CRLF-safe Git bytes into a unique staging root beneath this release's evidence directory:

   ```powershell
   git -c core.autocrlf=false archive --format=tar --output=$taskArchivePath $releaseSha restaurant-finder-api
   tar -xf $taskArchivePath -C $taskStagingRoot
   ```

2. Validate resolved extraction paths and compare every staged tracked API file to its selected Git blob. No `.env`, credentials, virtual environment, reports, old generated directories, originals/downloads or authoring helpers may enter the build context.
3. Privately snapshot the old eight-prompt manifest and read back each pinned immutable version using the existing deployment profile. Verify each definition against committed local text and establish that synchronization can reuse a matching version. A missing/mismatched old definition is a repair gate, not permission to update it.
4. From staged API source, run the existing synchronization command once, using an **absolute** path for the new staged manifest and existing locked API interpreter:

   ```powershell
   & $taskApiPython -m src.deployment.sync_prompts --profile default --region us-east-2 --manifest $taskStagedManifest
   ```

   Full PRD sign-off authorizes new planner prompt creation/versioning here. Record new ID/version/ARN and safe management outcomes; do not print credentials. A failed/uncertain sync stops for read-only reconciliation; do not blindly rerun a write command.
5. Compare read-backs and management outcomes: old eight definitions must remain unchanged; the only intended new prompt resource/version is `RAG_MULTIPART_PLAN_PROMPT`. If a newer equivalent old version was selected by synchronization, retain the already verified prior eight manifest entries for packaging and include only the verified new planner entry; validate every retained hash/ARN/version. Do not mutate old drafts/versions or delete prompts.
6. In a fresh process set `PROMPT_SYNC_MODE=false`, `REQUIRE_PROMPT_MANIFEST=true`, explicit staged `PROMPT_MANIFEST_PATH`, metadata lookup disabled and observability/evaluation disabled. Run read-only `-m src.deployment.validate_prompts` from staged API; require nine exact names, immutable versions and matching local hashes. Record full manifest hash and account/region.
7. Preserve old worktree/default/sealed manifests. Subsequent new-code packaging/developer commands must select the new manifest explicitly; do not imply the stale default eight-prompt file was updated. Application startup/request processing must perform no prompt synchronization.

AWS describes prompt versions as snapshots for deployment; this release additionally verifies their content against the selected source. [Bedrock versioned prompt guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-management-deploy.html).

**Checkpoint:** exact committed staging, nine verified pinned entries, safe sync receipt, one added manifest, no model inference.

### Step 5 — Build, audit and publish one ARM64 image

1. Generate unique tag `multipart-<release SHA first 7>-<UTC yyyyMMddHHmmss>-arm64` in the existing repository. Confirm tag absent with successful ECR read; access/network failure is not absence. Never publish `latest` or reuse/overwrite a tag.
2. Build from staged API using existing Dockerfile/lockfile and revision label:

   ```powershell
   docker buildx build --platform linux/arm64 --load --label "org.opencontainers.image.revision=$releaseSha" --metadata-file $taskBuildMetadata --tag $taskImageUri $taskStagedApi
   docker image inspect --format '{{.Os}}/{{.Architecture}}' $taskImageUri
   ```

3. Record resolved base digest/build provenance, architecture and actual revision label. The base tag is not digest-pinned; dependency locks alone do not establish byte-identical rebuilds.
4. With entrypoint overridden and `--network none`, audit packaged source against committed Git bytes and validate nine prompts. Confirm intended unprivileged user, normal instrumented command and absence of sensitive/generated extras. Do not run `src.main` or initialize a live agent for this audit. Remove only explicitly owned temporary containers afterward.
5. Use normal supported ECR authentication. If the known credential-helper issue requires a temporary Docker config, create it beneath ignored evidence, restrict/verify its current-user ACL and use the inspected daemon endpoint; never edit global Docker configuration. Obtain login password without printing it, check AWS exit immediately, send through stdin, and clear/remove auth material in `finally` even on failure.
6. Push only the unique tag once. Read back actual ECR digest and manifest descriptors, requiring a runnable linux/arm64 image; an attestation may be present. A local image ID is not the registry digest. Confirm the baseline rollback digest remains fetchable/retained.

**Checkpoint:** image/source/manifest/revision/architecture/build receipt and unique tag/digest, rollback retention proven.

### Step 6 — Review the image-and-flag CloudFormation update

1. Refresh stack/Runtime/DEFAULT/pointer and compare to the captured baseline immediately before preparation and again before execution. No competing/newer configuration may be overwritten.
2. Synthesize only the existing stack from committed infrastructure source with explicit account/region, the new image and approved context true; use existing compiled tooling and `--no-lookups`:

   ```powershell
   npx --no-install cdk synth restaurantFinder-AgentCoreStack --no-lookups -c "imageUri=$taskImageUri" -c documentMultipartEnabled=true --output $taskReleaseSynth
   ```

   Use task-local `CDK_DEFAULT_ACCOUNT=447393541969` and `CDK_DEFAULT_REGION=us-east-2`, restore afterward. Require the image/flag semantics to match the proposed template. Do not deploy all stacks, publish Lambda assets, or change resource context.
3. Deep-copy the fresh Original template, resolving the actual existing Runtime logical ID by type/physical mapping. Historical ID `restaurantFinderAgentCoreRuntime` is a discovery hint. Change only:

   ```text
   /Resources/<runtime-logical-id>/Properties/AgentRuntimeArtifact/ContainerConfiguration/ContainerUri
   /Resources/<runtime-logical-id>/Properties/EnvironmentVariables/DOCUMENT_MULTIPART_ENABLED
   ```

   Set flag string `"true"`. It may be an added key if previously absent. Preserve all other environment keys, role/network/protocol, resource definitions, outputs, dependencies, metadata and parameters. Assert recursive diff contains exactly those two leaves; save machine-readable before/after paths. An already enabled or otherwise unexpected baseline needs reconciliation.
4. Compare relevant synthesized Runtime properties to the proposed patch and explain representation differences. Assert the new CDK source supports this configuration. Use the minimal patched baseline as deployment input so unrelated assets/formatting are not updated.
5. Write UTF-8 without BOM. Inline TemplateBody must be at most 51,200 bytes; a larger body needs an approved upload method. Prepare structured `change-set-input.json` with UPDATE, unique name/client token, actual JSON TemplateBody text, all prior parameters `UsePreviousValue=true`, existing capabilities/RoleARN and existing update behavior. Review before sending. [CloudFormation change-set API](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-change-set.html).
6. Create/read the change set; wait for CREATE_COMPLETE/AVAILABLE with bounded polls:

   ```powershell
   aws cloudformation create-change-set --cli-input-json file://$taskChangeSetInput --profile default --region us-east-2 --no-cli-pager
   aws cloudformation describe-change-set --change-set-name $taskChangeSetArn --profile default --region us-east-2 --no-cli-pager
   ```

7. Require exactly one existing `AWS::BedrockAgentCore::Runtime` Modify, Replacement=False. Details may concern only AgentRuntimeArtifact and EnvironmentVariables, with no recreation or other resources/properties. Do not accept Add/Remove, conditional replacement or broader changes. Show concrete before/after image and flag in commentary. Full execution approval covers this matching change set; a wider result requires a decision before execution.

CloudFormation documents these two Runtime properties as updates without replacement; the actual inspected change set remains the gate. [Runtime resource properties](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-runtime.html).

**Checkpoint:** exact two-leaf diff, one-Runtime/no-replacement change-set review, fresh-baseline equality.

### Step 7 — Execute and verify configuration before sending a question

1. Execute the reviewed ARN once; inspect stack events/status through a bounded wait with progress updates. Never launch a competing update:

   ```powershell
   aws cloudformation execute-change-set --change-set-name $taskChangeSetArn --profile default --region us-east-2 --no-cli-pager
   ```
2. Require UPDATE_COMPLETE, Runtime READY using the exact image URI/digest and `DOCUMENT_MULTIPART_ENABLED="true"`, and DEFAULT READY with liveVersion equal to the new Runtime version. Record actual version; do not predict “14” from history.
3. Compare deployed template/runtime against baseline: only image, flag and derived version may advance; all other environment/role/network/protocol/resource IDs/outputs and active-pointer content/ETag remain equal.
4. Readiness is control-plane evidence, not functional proof. If DEFAULT has not advanced, wait within the bounded readiness window then report a blocker; do not silently update/create another endpoint. Runtime updates create versions and DEFAULT normally follows the newest one. [AgentCore versioning](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agent-runtime-versioning.html), [endpoint read-back](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/get-agent-runtime-endpoint.html).

**Checkpoint:** verified new configuration and preserved resources; ledger still zero.

### Step 8 — Load the updated UI with explicit AWS configuration

1. Recheck the positively identified project listener. Restart only that project UI if necessary to load the new source validator; preserve rollback configuration. Do not kill a process solely by port or use an old running module as evidence of the new code.
2. Use the UI's existing locked interpreter and committed release source, with task-local `AGENT_CONNECTION_MODE=aws`, fresh Runtime ARN, `AWS_REGION=us-east-2`, `AWS_PROFILE=default`, fresh document bucket and `DOCUMENT_SOURCE_VIEWER_ENABLED=true`. Keep `.env` files unchanged. Use explicit `MEMORY_ACTOR_ID` only for the intended synthetic actor; change actor through an identified UI restart between fresh conversations if no supported per-session control exists.
3. Bind to `127.0.0.1:8010` and start headlessly using installed Chainlit. The installed CLI source inspected during preparation supports `--host`, `--port` and `--headless`; use the existing locked UI interpreter from the committed UI directory:

   ```powershell
   & $taskUiPython -m chainlit run app.py --host 127.0.0.1 --port 8010 --headless
   ```

   Recheck installed options if the environment changed. Use `Start-Process -WindowStyle Hidden` for any background helper. Do not enable file watching or automatic reload. A listener owned by unrelated work is a stop/review condition.
4. Inspect the browser page/connection mode through supported controls. Do not submit a greeting or warm-up. Avoid refresh/resend while a request is active. Opening the UI/settings alone consumes no Runtime slot unless delivery evidence shows a send.

**Checkpoint:** updated UI process/source/configuration, loopback browser ready, no model probe.

### Step 9 — Execute L1-L6 and inspect sources/traces

Use section 9's order, actor/conversation relationships, exact text and expected evidence. Reserve/send/record each slot separately; finish answer/source/trace inspection before the next question. Follow applicable browser tool/skill instructions when execution begins. Do not call a direct Runtime client to reproduce a UI answer outside the ledger.

**Checkpoint:** actual attempt ledger, safe case outcomes, original downloads/hash receipts, correlated available telemetry; unresolved cases remain explicit.

### Step 10 — Retain or roll back, then publish closeout

1. Apply section 10's decision rules. Keep the feature only when mandatory live criteria pass; do not call partial validation complete. Missing optional telemetry is recorded separately.
2. Update section 12 with actual source/PR/CI/prompt/image/configuration/attempt evidence and R01-R11 outcomes. Add only concise verified checkpoints to the implementation PRD and document/evaluation guides; do not overwrite their historical evidence.
3. Commit/push only scoped closeout documentation to the same review branch; update the existing PR body using structured fields/body file with accurate results. No merge or application fix is included. Attach the existing PR if necessary and preserve its identity.
4. Inspect automatically triggered closeout CI. Record release source SHA and documentation SHA separately; prove packaged API/dependency Git blobs still equal the release source. A documentation commit does not imply an image rebuild, and a commit cannot contain its own SHA.
5. Remove only authored scratch archive/context/synth/auth directories after resolving absolute paths inside this phase's evidence root. Preserve rollback records, provenance, ledger, downloads, receipts and unrelated owner files. Verify auth cleanup on success/failure.

**Checkpoint:** safe published engineering record and explicit stopping point, no demo/benchmark/next feature.

## 8. Expected original-document facts

The saved v2 generation and current local controlled fixtures establish these expectations. Fresh bounded S3 reads must confirm them before L1; local files alone are not live evidence.

| Venue / record | Required literal conditions | Original reference |
| --- | --- | --- |
| Harbor menu | Mushroom pasta RM32 per serving; contains wheat and milk. | `harbor-menu` v2, PDF page 1. |
| Sakura menu | Mushroom pasta RM36 per serving; contains wheat and milk; dinner only. | `sakura-menu` v1, Markdown Main dishes section. |
| Harbor cancellation | No fee at least 24 hours before booking; less than 24 hours incurs RM20 per booking. | `harbor-policy` v1, full Reservations and cancellation section body. |
| Sakura cancellation | No fee at least 12 hours before booking; later cancellation RM15 per booking. | `sakura-policy` v1, full section body. |
| Spice menu | No mushroom-pasta record. Do not substitute a different dish. | `spice-menu` v1. |
| Spice cancellation | No fee at least 6 hours before booking; later cancellation RM10 per booking. | `spice-policy` v1, full section body. |

Fresh hashes/line ranges belong in private receipts. Compare downloaded originals to fresh manifest values, not a screenshot or recreated document. No policy fee is compared with a dish price, and no policy recommendation/ranking is inferred.

## 9. Exact live scenarios and inspection

| Order / conversation | Exact request | Required outcome |
| --- | --- | --- |
| L1 / fresh A | `Compare mushroom pasta prices at Harbor and Sakura, and explain both restaurants' cancellation policies. Show the sources.` | Multipart answered 4/4: RM32/RM36, Harbor RM4 lower per serving, both full cancellation records. Four sources in task order: Harbor menu, Harbor policy, Sakura menu, Sakura policy. |
| L2 / same A immediately after L1 | `For Harbor, what is the mushroom pasta price and cancellation policy?` | Multipart answered 2/2 with complete menu/policy records, two sources, no two-venue arithmetic; even this one-venue compound clears single-restaurant scope. L1's four controls remain tied to answer 1, not answer 2. |
| L3 / same A immediately after L2 | `And what about its cancellation fee?` | Clarify restaurant because the approved multipart answer cleared single-restaurant scope. No retrieval/selection/rewrite or cited answer; ordinary legacy clarification may read a catalog. |
| L4 / fresh B | `Compare mushroom pasta prices at Harbor and Spice, and explain both restaurants' cancellation policies.` | Multipart partial 3/4: Harbor price and both full policies supported, Spice dish explicitly missing, no price difference. Three sources: Harbor menu, Harbor policy, Spice policy. |
| L5 / fresh C | `Compare mushroom pasta prices at Harbor and Sakura, and explain both restaurants' cancellation policies and parking rules.` | Multipart clarify, fixed accepted example; no planner, pin, embedding, vector query, selector or clickable source. No silently answered subset. |
| L6 / fresh D | `Compare mushroom pasta prices at Harbor and Sakura.` | Existing comparison answered 2/2 with RM4 difference and full qualifiers, two menu sources, no multipart planner. |

Keep A's same conversation/actor for L1-L3 and inspect its retained sources before leaving that session. L4-L6 use separately assigned synthetic identities. L5 is intentionally malformed and must stay outside the old `prices and cancellation policy at ...` compatibility exception. L3 is a legacy follow-up, not a new multipart grammar input.

For each request:

1. Reserve the slot, capture safe actor/conversation hash and send/start/end times, submit once, record whether delivery completed/failed/uncertain.
2. Inspect the complete response and source count/labels. Worker/model intermediate text must not appear as a partial public answer. Match conditions, currencies/units, correct arithmetic and missing-part wording against verified originals.
3. For L1, click every source using actual observed controls. Inspect PDF page 1 and all three Markdown records with original line/section context. Download all four originals, hash bytes and compare generation/document/version/hash/location to fresh immutable references. No surrogate document or public S3 link is acceptable.
4. After L2/L3, revisit L1's four controls and L2's two controls in the same session, checking distinct answer labels and document association before changing actor/restarting the UI. Inspect L4/L6 sources within their own sessions too. Cross-restart permanent links are not supported and are not an acceptance requirement. Source actions must not resubmit the question; inspect Runtime invocation evidence before/after, and charge an accidental resend to the ledger.
5. Check available session/request-correlated traces: router provider/fallback, `rag.multipart.plan`, worker and worker.complete IDs/status/reasons/attempts, aggregate required/supported counts, final moderation and parent memory. If every router request falls back, Jev operation is unmeasured; do not claim Jev ran.
6. L1/L2/L4 must show multipart execution, not merely a plausible answer from search. L6 must retain the comparison path; L5 must have zero new-family provider work. Confirm no web/browser/memory worker tool, nested comparison, repair or extra selection occurred.
7. Count planner/embedding/vector/selector operations and inspect span overlap where evidence permits. Maximum two worker spans may overlap; SDK-thread termination after timeout and exact pointer read counts remain offline-only unless actual live telemetry exposes them.
8. Confirm one final output-moderation and approved-turn parent memory span where available. A memory span is not proof of exactly one durable persisted event. No raw internal checkpoint, quote payload, provider error body or unrelated conversation is needed for this review.

Missing detailed timing, SSE citation metadata, exact filters/pin-read counts, durable memory-event counts, uncaptured HTTP retries or dollar totals must be marked unmeasured. Do not add instrumentation or broaden live usage to fill those gaps during this rollout.

## 10. Stop conditions and rollback

1. Before deployment, stop on failed/missing CI, authentication/Docker failure, moved source/base, wrong account, unexpected baseline drift, invalid old/new prompts, unsafe image contents, wrong architecture, reused tag, threatened rollback retention, changed corpus gold, or broader change set. Report the concrete gate; complete independent safe documentation without bypassing it.
2. If stack update fails, observe CloudFormation recovery until stable; do not launch a competing rollback. If automatic recovery already restores the fresh baseline, verify it and avoid redundant manual rollback.
3. Stop live sends on failed/malformed/incorrect factual output, missing/wrong fourth source, repeated selection/planning, wrong route, web tool, timeout or UI regression. Record the consumed slot and evidence. Do not improvise source patches or use extra diagnostics without a remaining replacement slot.
4. Complete sign-off authorizes one manual rollback only when a release-caused regression/failure is established, stack is stable, this release remains active, no concurrent/newer update exists and the captured baseline digest is still available. If cause/ownership is uncertain, ask for a narrow decision. Missing optional span detail alone is not a regression.
5. Copy the current deployed template and restore exactly the baseline image URI and prior multipart key presence/value. If the key was absent, remove only that key; if false, restore its exact value. Preserve every other property. Assert this matches the captured baseline configuration and inspect the same existing-Runtime/no-replacement change-set constraints before execution.
6. Execute the reviewed rollback once. Verify stable stack, Runtime/DEFAULT READY on the restored image/configuration, unchanged role/resources/pointer and fresh image digest. A rollback creates a new version; do not require numeric version 13 to return.
7. Restore the positively identified project UI using the captured prior committed source and task-local configuration/locked interpreter. Do not reset the Git branch or overwrite owner files. Retain feature source/PR/evidence for repair review.
8. Keep newly created prompt versions and image; no deletion/re-embedding/pointer change is part of rollback. Their retained existence and prior charges/events must be recorded.
9. Rollback readiness adds no Runtime sends. Any functional post-rollback request uses a remaining slot replacing an unrun scenario or needs a fresh explicit allowance. Further rollback continuation, image republish, IAM/endpoint repair, Docker restart or application fixes require a reviewed deviation.

## 11. Evidence, sources, and open decisions

Retain privately under the unique ignored evidence root:

```text
ownership.json / source-inventory.json / approval-and-attempt-ledger.json
ci-release.json / downloaded CI reports and test logs / pr-receipt.json
baseline-stack.json / baseline.template.json / baseline-runtime.json / baseline-endpoint.json
baseline-ecr.json / baseline-index.json / baseline-active.json / manifest.json
original-source-verification.json / prior-prompt-manifest.json / prompt-readbacks-summary.json
prompt-validation.json / manifest hash / sync safe receipt
build metadata / image.json / packaged-source-audit.json
template-review.json / change-set-input.json / change-set-review.json / deployed-verification.json
ui-process-source-summary.json / prior-ui-config-summary.json
L1-L6 safe outcomes / source-download-verification.json / available trace summaries
rollback-review/result if used / closeout-ci.json / final-verification.json
```

Never retain login material, Docker auth tokens, secret values, signed credential-bearing URLs, raw provider bodies or unrelated conversation traces in that inventory or Git. Raw AWS snapshots can contain identifying/configuration details; keep them ignored and publish only concise reviewed summaries. Use native PowerShell literal-path cleanup after verifying workspace containment.

Primary documentation consulted during preparation:

- [CloudFormation Runtime properties](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-runtime.html) for image/environment update behavior.
- [CloudFormation create-change-set](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-change-set.html) for a reviewable UPDATE and input limits.
- [Bedrock prompt versions](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-management-deploy.html) for snapshot-based deployment.
- [AgentCore versioning](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agent-runtime-versioning.html) and [endpoint read-back](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/get-agent-runtime-endpoint.html) for actual DEFAULT mapping.
- [GitHub pull-request API](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request) for structured head/base/draft publication. Use existing supported authentication; no connector installation is required by this plan.

Chosen assumptions for sign-off: six attempts, one image-and-flag update, new review branch/draft PR to the existing enhancement branch, default-off CDK, current configured models/corpus, no main merge, loopback UI only. No missing credential answer is required to review the plan; readiness is discovered during execution. A different dollar cap, base branch, deployment scope or validation set changes the plan and must be resolved before dependent actions.

## 12. Execution record — owner approved, work in progress

### Preparation completed on 2026-10-13

- Inspected local changes, implementation acceptance evidence, old release records/receipts, Docker packaging, prompt synchronization/validation, CDK resource definitions, UI invocation/source loading, CI/deployment triggers, fixtures and local Git refs.
- Verified preparation HEAD/branch and old eight-prompt manifest hash. Remote refs/readiness/authentication and live providers were not checked.
- Consulted the primary documentation above. This PRD is the only requested new file produced in preparation; application/IaC source, prompts, generated artifacts and owner environment files remain untouched.
- Checked the document's structure, 30 existing publication paths, 11 ordered steps, six scenario definitions, balanced code fences and whitespace; preserved HEAD and the warning-file hash.
- No application/infrastructure tests, Git mutation/publication, PR creation, AWS account operation, prompt sync, Docker operation, UI restart/submission, live inference or demo action was performed for preparation.

### Fill during execution; do not prepopulate success

| Record | Actual evidence / result |
| --- | --- |
| Owner sign-off and included allowance | Explicit “proceed” on 2026-10-13; complete scoped execution and six total Runtime attempts approved. |
| Starting/remote base SHA and warning-file hash | Local and freshly read remote `feat/jev-router`: `081e0fb51d13cba9838ca5bf01762997ddef79ef`. Proposed feature branch absent; no equivalent PR. Warning SHA-256 remains `C3F491550280BA5568CEA656D1E90378A76547EE5520E462A323469949AEBF9F`. |
| Infra changes / local suites / flag synthesis diff | Four allowlisted infrastructure paths updated. Build exit 0; 6/6 infrastructure, 196 API and 31 UI tests pass. Fresh offline evaluations: 17/17 (374 checks), 20/20 (260), 40/40 (609), no failed/missing cases. Omitted and false templates equal; true changes only `/Resources/restaurantFinderAgentCoreRuntime/Properties/EnvironmentVariables/DOCUMENT_MULTIPART_ENABLED` from `false` to `true`. Invalid `yes` fails with exit 1 and the intended error. |
| Release SHA / branch / draft PR URL and attachment | Pending. |
| Push CI / PR CI / inspected artifact results | Pending. |
| Fresh AWS identity / baseline versions / rollback image and UI | Pending. |
| Nine prompt IDs/versions / manifest hash / old-definition preservation | Pending. |
| Unique image URI/digest / architecture / packaged provenance | Pending. |
| Exact two-leaf diff / actual change-set ARN/details | Pending. |
| New Runtime/DEFAULT versions / configuration and pointer equality | Pending. |
| L1-L6 results and actual used/remaining attempts | Pending. |
| Source controls/download hashes / correlated traces / gaps | Pending. |
| Retain or rollback with cause and resulting configuration | Pending. |
| R01-R11 individual PASS/FAIL/BLOCKED/UNMEASURED | Pending. |
| Closeout docs SHA/CI and release source equality | Pending. |
| Cleanup / preserved evidence / exact stopping point | Pending. |

Do not mark this release complete merely because the image deployed or offline tests passed. Report every unresolved live criterion and distinguish any approved recovery/repair from the original plan.
