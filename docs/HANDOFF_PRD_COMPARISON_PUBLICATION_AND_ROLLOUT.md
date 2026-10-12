# Handoff PRD: Publish, deploy, and verify document price comparisons

**Status:** Owner approved execution on 2026-10-12; publication and release checks in progress.
**Prepared:** 2026-10-12, Asia/Kuala_Lumpur.
**Audience:** The owner and the execution agent responsible for the Restaurant Finder AI engineering demonstration.
**Repository:** [yukangzhen/restaurant-finder](https://github.com/yukangzhen/restaurant-finder).
**Local workspace:** `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`.
**Inspected branch/base:** `feat/jev-router`, `f6513da1467d7b269cf5c41e372870bd1aadec22`.

## 1. Outcome and reason

Put the completed document comparison implementation into the existing AWS AgentCore Runtime, publish its source to the owner's GitHub repository, and inspect a bounded set of real UI results. The deliverable is a traceable release with verified menu comparisons, original document links, safe missing-evidence behavior, and working conversational scope.

This is a portfolio demonstration using fictional restaurants. The owner wants to demonstrate AI engineering: LangGraph orchestration, parallel scoped retrieval, model-assisted quotation selection, deterministic price arithmetic, evidence validation, deployment, and regression checks. This phase establishes that the implemented workflow works with real providers before further functionality is added.

Deliverables:

1. Reviewed feature changes committed and pushed to the existing feature branch, with inspected GitHub offline CI results for the exact release SHA.
2. One uniquely tagged ARM64 API image with recorded source SHA, prompt-manifest hash, resolved build provenance, and ECR digest.
3. One reviewed CloudFormation update that changes only the existing Runtime container image.
4. A fresh rollback snapshot and proof that the previous image remains available.
5. At most six live Runtime invocation attempts, with scenario results, source inspection, and available correlated telemetry.
6. A published execution record separating passed criteria from failures, blocked work, and unmeasured internals.

Stop after release validation and its engineering record. Demo walkthrough, recording, benchmarking, LinkedIn publication, and further feature development are outside this phase.

## 2. What has already been inspected

### 2.1 Local implementation and evidence

The [comparison implementation PRD](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/docs/HANDOFF_PRD_DOCUMENT_COMPARISON.md:509) records approved local completion:

| Item | Existing inspected evidence; not rerun during preparation |
| --- | --- |
| API regression suite | 166 tests passed. |
| UI regression suite | 28 tests passed. |
| Original document RAG evaluation | 17/17 cases; 374 measured checks passed. |
| Comparison evaluation | 20/20 cases; 260 measured checks passed. |
| Workflow | Stateless LangGraph subgraph, two Send workers, maximum concurrency two, one pinned comparison manifest, ordered aggregation. |
| Evidence and calculation | Complete literal menu-record validation, original-source provenance, Decimal arithmetic, conditional quotations retained. |
| Partial results | One supported venue gives one citation and no price-difference calculation. Integrity/conflict failures reject the comparison. |
| Parent workflow | Common output moderation, approved comparison clears single-venue scope, parent memory hook runs after the final approved response. |
| CI | Comparison evaluator added to the existing offline API job; existing pinned actions and read-only workflow permissions retained. |
| Live behavior | Comparison Jev routing, Haiku selection, Titan ranking, and AWS execution remain unmeasured. |

Current changes are uncommitted. The earlier Runtime warning PRD is also untracked and belongs to separate work; preserve it and exclude it from publication here. No application, UI, infrastructure, dependency, corpus, or prompt edits are needed for this release unless a new reviewed repair scope is approved.

Code and workflow references:

- [Comparison planner, validator, and calculator](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/restaurant-finder-api/src/application/document_rag/comparison.py).
- [Parallel comparison graph and provider limits](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/restaurant-finder-api/src/application/document_rag/comparison_workflow.py).
- [Single/comparison dispatch and follow-up rewrite](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/restaurant-finder-api/src/application/document_rag/workflow.py).
- [Output moderation, scope, router, and memory](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/restaurant-finder-api/src/application/orchestrator/workflow/nodes.py).
- [Original source loader and hash checks](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/restaurant-finder-ui/source_documents.py).
- [Offline CI](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/.github/workflows/ci.yml).
- [Existing image deployment workflow](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/.github/workflows/deploy-image.yml).

### 2.2 Existing release machinery

Offline CI runs on branch pushes and pull requests. It has API, UI, infrastructure, and aggregate quality jobs. Both deployment workflows restrict their push triggers to relevant `main` changes; destruction is manual only. The image deployment workflow also supports manual dispatch, synchronizes prompts, publishes both SHA and `latest` tags, and directly calls the Runtime update API. Do not dispatch it for this phase. Publish only to `feat/jev-router`; do not merge into `main`.

Use the earlier rollout's minimal tracked-source staging and reviewed CloudFormation procedure, with a **new source SHA and fresh baseline**. The Dockerfile validates eight managed prompt definitions and starts the instrumented application. Its base image reference is not digest-pinned: record the resolved base/build provenance, and do not claim byte-for-byte reproducible rebuilds merely because Python dependencies are locked.

AWS documents Runtime artifact changes as updates without replacement. Actual scope must still be confirmed from this release's change set. See [Runtime resource reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-runtime.html), [create-change-set](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-change-set.html), and [get-agent-runtime-endpoint](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/get-agent-runtime-endpoint.html).

### 2.3 Historical AWS baseline: discovery hints only

The [previous rollout record](C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore/docs/HANDOFF_PRD_RUNTIME_ROLLOUT_AND_LIVE_VALIDATION.md) and saved local verification establish the following historical values. No fresh AWS identity, service readiness, Docker readiness, or remote GitHub state was checked while preparing this PRD.

| Item | Last recorded value |
| --- | --- |
| Account / region / profile | `447393541969` / `us-east-2` / `default` |
| AgentCore stack | `restaurantFinder-AgentCoreStack` |
| Runtime ID | `restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime and DEFAULT endpoint | READY, version 12, recorded 2026-10-09 |
| Image tag | `query-scope-ef146a2-20261009031110-arm64` |
| ECR digest | `sha256:e4afa3b679bc2c69ea8ca70a00e77115ed7d0a4b4f54ad7827bcd6c4ae694428` |
| ECR repository | `restaurantfinder-agent` |
| Document bucket | `restaurantfinder-ragstack-documentbucketae41e5a9-vqrmcnuycjq5` |
| Vector index | `arn:aws:s3vectors:us-east-2:447393541969:bucket/restaurantfinder-rag-447393541969-us-east-2/index/documents-titan-v2-512` |
| Active generation | `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` |
| Demo address | `http://localhost:8010/`, loopback only |

The earlier six-request allowance is exhausted. It does not carry over. The previous Docker restart authorization was used and does not authorize another restart.

## 3. Approval and authorization boundary

The owner's latest **okay go ahead** approved preparing this document following the recommendation to prepare a PRD for review. It is not deployment or live-call approval.

After this reviewable PRD was presented, the owner explicitly supplied **proceed** on 2026-10-12. This approves the complete scoped execution, including publication, the image update, conditional rollback, and a fresh maximum of six Runtime attempts. The sign-off gate is satisfied.

**Required execution sign-off:** After reviewing this PRD, the owner must explicitly approve its execution, including publication, the image-only AWS update, the rollback conditions, and the new maximum of six Runtime attempts. Update section 13 with that approval before Step 1. Under complete sign-off, matching actions below need no repeated generic confirmation; ask only for a material deviation or an unavailable permission.

### Included if the owner approves the complete PRD

- Review and commit the explicit allowlist below; push only to the owner's existing feature branch and inspect its automatically triggered offline CI.
- Use existing locked environments for offline packaging validation. CI runs the existing suites and evaluators; no new tests are designed here.
- Read current GitHub authentication/repository state and current AWS control-plane, corpus metadata, original sources, and relevant telemetry.
- Build and publish one unique ARM64 image to the existing ECR repository. Permit one corrected local rebuild for a packaging/transient failure before publication, without application-source edits.
- Create, review, and execute one matching CloudFormation UPDATE change set for the existing Runtime image.
- Use a private, short-lived Docker authentication directory inside ignored local evidence when required by the known credential-helper issue; restrict its ACL to the executing user, never print its token/auth contents, and remove it in `finally`. Do not modify global Docker configuration.
- Reuse the existing AWS-mode UI or start it on loopback if absent. Restart only a positively identified project UI process if its configuration must change.
- Perform at most six live Runtime attempts under section 5, including failed or diagnostic replacements.
- Execute at most one reviewed image-only rollback if this release causes failure or regression, as specified in section 10.
- Update this execution record, publish scoped documentation, and remove task-created scratch material within verified workspace paths.

### Excluded

- Application fixes, broader model/router changes, new prompts or prompt synchronization, dependency upgrades, corpus ingestion, re-embedding, pointer publication, or index/document deletion.
- IAM, secrets, credentials, billing, quotas, ECR lifecycle rules, guardrail configuration, tracing destinations, Gateway/Lambda/Memory resources, network configuration, or stack identity changes.
- PR creation, `main` merge/push, force push, broad rebase/reset, GitHub Actions settings changes, deployment/destruction workflow dispatch, or `cdk deploy --all`.
- Direct Runtime or endpoint updates outside the reviewed CloudFormation change set.
- Additional model probes, warm-ups, fallback fault injection, live evaluators, benchmarks, public hosting, messaging, recording, and LinkedIn publication.
- Docker Desktop restart/reset, WSL shutdown/reset, unrelated process/container termination, and broad resource cleanup. An unhealthy engine requires a new narrow recovery decision.

Publication exposes the reviewed feature source and documentation on GitHub. The image push consumes storage and the rollout/live checks may incur AWS/provider charges. Runtime rollback cannot undo publication, storage, inference charges, telemetry, or memory events. These are the consequences covered by execution approval.

## 4. Definition of done

| ID | Observable acceptance criterion |
| --- | --- |
| D1 | Exact approved feature files are committed on `feat/jev-router`; unrelated warning work is preserved; remote release SHA matches local commit. |
| D2 | All four offline CI jobs pass for that SHA. Downloaded artifacts confirm API/UI tests, 17 original RAG cases, and 20 comparison cases with no missing cases or unmeasured offline checks. |
| D3 | Fresh intended AWS identity, stable stack/Runtime/DEFAULT mapping, current image/digest, corpus pointer/manifest, and usable rollback image are captured. |
| D4 | Image contains exact committed API source plus only the validated prompt manifest; eight prompts validate; architecture is linux/arm64; ECR read-back identifies its unique tag/digest. |
| D5 | Recursive template comparison has exactly one image-URI leaf change; actual change set is one existing Runtime Modify with Replacement=False and only AgentRuntimeArtifact changed. |
| D6 | Stack UPDATE_COMPLETE; Runtime and DEFAULT READY on the new version/image; environment, role, resource identities, and active pointer remain equal to the fresh baseline. |
| D7 | V1-V6 meet their inspected functional expectations within six attempts, including both source documents, a one-source partial, ambiguity after comparison, and a scoped single-restaurant follow-up. |
| D8 | Actual PDF/Markdown source controls open originals; downloads match pinned hashes; distinct answers retain correct source associations. Source actions send no Runtime request. |
| D9 | Available request-correlated router/comparison/retrieval/moderation/memory telemetry is inspected. Required routing and comparison execution are established; missing detailed counters or span timing are explicitly unmeasured. |
| D10 | Release/source/digest/versions, CI artifacts, actual request usage, rollback decision, every criterion, and remaining gaps are recorded and scoped documentation published. |

Report PASS, FAIL, BLOCKED, or UNMEASURED per criterion. Do not declare the whole phase complete while a required criterion is unresolved. A deployment-only success or a passing offline simulation is not live functional acceptance.

The live checks are small functional checks. They do not establish broad natural-language accuracy, retrieval quality across arbitrary documents, production readiness, speed improvements, or cost savings.

## 5. Live request and cost allowance

Proposed new allowance: **six total Runtime invocation attempts**, sequentially initiated. Reserve each slot before sending. A failed submission whose delivery is uncertain, timeout, automatic UI resend, or diagnostic Runtime call consumes a slot. Never retry the same prompt for free. If a send is definitely rejected locally before any Runtime invocation, retain proof before treating the slot as unused.

Use the exact scenarios in section 8. An alternative diagnostic replaces a planned scenario; it is not an additional seventh call. Stop at six, and stop earlier on a provider error/retry, invalid source or calculation, unexpected route, timeout, or expanded workflow. Unused slots do not authorize unrelated questions.

Expected logical work on a successful run:

| Work | Planned bound and limitation |
| --- | --- |
| Jev classifications | Up to six; existing fallback may add up to six Bedrock routing calls. Record the provider actually used. |
| RAG retrievals/query embeddings | Three comparisons with two workers each, plus two single-venue questions: up to eight logical retrievals/embeddings. V2 should perform none. |
| Answer selectors | Up to eight logical selector calls; fewer when a branch has no retrieved evidence. Missing-item passages may still require selection. |
| Follow-up rewrite | One expected for V6. V2 has no approved single-venue scope and should clarify before rewriting/retrieval. |
| Comparison providers | Each branch uses one embedding attempt, one vector-query page, and at most one selector invocation. Existing comparison selector SDK config uses one total attempt, 3-second connect and 20-second read timeouts. |
| Comparison graph bounds | Two workers; top-k at most five each; context at most 9,000 characters per branch; selector output at most 1,600 tokens. Shared worker deadline is at most 45 seconds with finalization reserve inside the 60-second RAG node deadline. |
| UI Runtime transport | Existing SDK total attempts one; 300-second response deadline. Do not add retries. |

These are planned logical operations, not an account-wide spending cap. Single-venue vector queries retain their existing bounded pagination; single-venue selectors, rewrite, and Bedrock fallback use existing SDK configuration whose HTTP retries must be inspected, not assumed to be one. Guardrails, memory/checkpoints, S3 reads, vector metadata, logging, build downloads, and image storage also contribute work or charges.

Record configured retry bounds before sending V1 through safe offline inspection of the selected dependency/source configuration. Do not start the application to probe model access, resolve secrets, or create extra billable calls. If an actual provider retry/error or an unexpectedly expanded workflow appears, stop later submissions and report it. Do not change environment/source to enforce new limits during this image-only phase.

No guaranteed dollar ceiling is proposed. If the owner requires one, settle that before execution approval using current pricing and available account controls. Read-only metadata, original-source inspection, and CI do not consume Runtime slots, but are not claimed to be cost-free.

## 6. Publication, release, and deployment steps

### Execution conventions

- Run from the specified workspace. Use task-specific variables; never repurpose HOME or CODEX_HOME.
- Bind example variables to the freshly inspected operation values before running commands. Use absolute workspace-contained paths for evidence/staging. Save and restore any task-changed environment variables in `finally`.
- Check `$LASTEXITCODE` immediately after each native command, before parsing or running another command. A successful pipeline/empty object is not evidence that AWS, Git, or Docker succeeded.
- Write JSON/text as UTF-8 without BOM. Use structured `--cli-input-json file://...` arguments for change sets; do not assemble JSON bodies through shell interpolation.
- Keep raw control-plane snapshots and permitted fictional outputs in a unique ignored directory under `restaurant-finder-api/.generated/comparison-rollout-<UTC timestamp>/`. Do not overwrite earlier evidence. Verify `git check-ignore` before writing sensitive machine/account evidence.
- Never print API keys, login/OAuth material, Docker auth, signed URLs, complete environment dumps, or credential-bearing headers. Store no credentials in Git or the image. If an unexpected secret is embedded in a template/config, preserve it in memory for comparison and stop before persisting it to a normal evidence file; do not silently redact a deployable rollback template and use it.
- Keep each wait below 60 seconds and provide progress commentary. Use bounded read-only polling rather than leaving an opaque long-running wait.

### Step 1 — Establish approved source scope

1. Record explicit owner execution approval and the new six-attempt allowance in section 13.
2. Inspect `git status --short`, `git diff --stat`, full tracked diffs, and every new feature file. Read the comparison implementation PRD's execution record.
3. Require the expected branch and base SHA above, or reconcile later changes before committing. Preserve the unrelated `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`; do not stage it.
4. Inspect existing staged changes separately. If unrelated files are already staged, stop the commit step and reconcile without unstaging/overwriting the owner's work automatically.
5. Use the explicit commit allowlist in section 7. Check that source documents, locks, prompts, infrastructure, secrets, and deployment workflows have no feature changes. Review file contents for accidental secret/private evidence before publication.
6. Run `git diff --check`; inspect its exit code. This is source review, not a new live invocation.

**Output:** understood diff and exact feature publication inventory. Stop on unexplained changes; do not use `git add .`, `git add -A`, or a broad commit.

### Step 2 — Publish the feature branch and verify CI

1. Inspect GitHub CLI authentication using `gh auth status --hostname github.com` and the authenticated login with `gh api user --jq .login`. Confirm access to `yukangzhen/restaurant-finder`; do not start a new browser login unless needed and do not display tokens.
2. Fetch only `origin/feat/jev-router`, then inspect divergence from the expected base. Stop on unexpected remote work instead of force-pushing or rebasing it.
3. Stage only section 7's files after review. Inspect `git diff --cached --name-only` and `git diff --cached`. Require exactly the intended allowlist, with no ignored reports or warning PRD.
4. Commit with a descriptive feature message, such as `feat: add verified parallel document price comparisons`. Record the full resulting SHA as `release_sha`; do not invent it in advance.
5. Push explicitly:

   ```powershell
   git push origin HEAD:refs/heads/feat/jev-router
   ```

6. Verify the remote branch SHA equals `release_sha`. Inspect automatically triggered `ci.yml` runs for that exact SHA:

   ```powershell
   gh run list --repo yukangzhen/restaurant-finder --workflow ci.yml --branch feat/jev-router --commit $releaseSha --limit 5 --json databaseId,headSha,status,conclusion,url
   gh run view $runId --repo yukangzhen/restaurant-finder --json headSha,status,conclusion,jobs,url
   ```

7. Wait with bounded snapshots for at most 30 minutes. Download that run's three allowlisted artifact bundles into the ignored evidence directory and inspect their logs/reports, not only the green badge:

   ```powershell
   gh run download $runId --repo yukangzhen/restaurant-finder --name offline-rag-and-api --dir $apiArtifactRoot
   gh run download $runId --repo yukangzhen/restaurant-finder --name offline-ui --dir $uiArtifactRoot
   gh run download $runId --repo yukangzhen/restaurant-finder --name offline-infrastructure --dir $infraArtifactRoot
   ```

   Require all four jobs successful, 166 API tests, 28 UI tests, the existing infrastructure suite, 17/17 original RAG cases with 374 measured checks, and 20/20 comparison cases with 260 measured checks. Investigate any platform/count difference rather than weakening requirements or accepting skipped/missing cases.
8. A cancelled/waiting/failed run is not a pass. If no run starts or Actions permissions reject it, report the blocker; do not change Actions settings or dispatch deployment workflows. If repair changes application/CI source, obtain a reviewed repair scope and repeat source publication/CI for the new SHA before building.

**Output:** published exact source and inspected release CI receipt. No AWS rollout on failed or unverified CI.

### Step 3 — Check AWS and Docker readiness

1. Use the existing profile and region explicitly:

   ```powershell
   aws sts get-caller-identity --profile default --region us-east-2 --no-cli-pager
   docker info --format '{{json .}}'
   ```

2. Require intended account `447393541969`; inspect the principal privately. An AWS account alias is not a different authentication profile. If expired, have the owner complete `aws login --profile default`, then rerun only the identity check. Do not create credentials or change identity automatically.
3. Docker must return a valid Linux engine response with exit zero. Inspect the active context/daemon endpoint and buildx availability. An ordinary supported start of a stopped Docker Desktop is permitted under full sign-off; a restart/reset or unrelated cleanup needs a separate decision. Do not infer engine health from a Desktop process being present.
4. Confirm Git/uv/Node/Docker/AWS CLIs and existing locked environments are usable. No upgrade or fresh dependency versions are included. Buildx must support `linux/arm64`; report a missing capability rather than installing/resetting tools silently.
5. Inspect port 8010's process owner and command, plus any relevant project listeners. Do not stop or commandeer an unrelated listener. Fresh AWS identity/daemon readiness replaces the old historical evidence.

**Output:** successful preflight or concrete blocker. No paid model smoke test is part of readiness.

### Step 4 — Capture a fresh baseline and rollback

1. Create the unique ignored evidence directory. Record `release_sha`, current UTC time, and an invocation ledger with `maximum=6`, `used=0`.
2. Read the AgentCore stack and its `Original` template:

   ```powershell
   aws cloudformation describe-stacks --stack-name restaurantFinder-AgentCoreStack --profile default --region us-east-2 --no-cli-pager
   aws cloudformation get-template --stack-name restaurantFinder-AgentCoreStack --template-stage Original --profile default --region us-east-2 --no-cli-pager
   aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id restaurantFinder_Agent-Ha58oX5Psu --profile default --region us-east-2 --no-cli-pager
   aws bedrock-agentcore-control get-agent-runtime-endpoint --agent-runtime-id restaurantFinder_Agent-Ha58oX5Psu --endpoint-name DEFAULT --profile default --region us-east-2 --no-cli-pager
   ```

3. Capture full template, stack parameters/capabilities/execution role, Runtime environment/role/network settings, current image/version, endpoint mapping, resource identities, and stack outputs. Normalize TemplateBody whether it is an object or a JSON string. Print only safe summaries.
4. Require a stable stack and READY Runtime/DEFAULT pointing at the same intended version. Reconcile any material difference from the historical Runtime 12 baseline before continuing. Check for drift between the template's Runtime configuration and actual configuration; do not overwrite a direct/manual update silently.
5. Read the current image's actual ECR digest and repository tag-mutability/lifecycle metadata. Prove the rollback image can be fetched and that one push will not threaten its retention. A historical digest or successful old rollout is insufficient. Do not edit repository policies.
6. Read `rag/active.json` and its ETag through the bounded existing DocumentStore, then read its derived manifest key. Validate with `ActivePointer` and `GenerationManifest` using the selected source. Use fresh configuration as authority; do not guess arbitrary S3 keys or list/download unrelated documents.
7. Read vector index metadata, without QueryVectors or embedding calls. Require Titan V2, 512 dimensions, float32, cosine, top-k at most five for the planned comparison, and the existing enabled RAG/viewer configuration.
8. Read the four distinct planned originals: Harbor menu, Sakura menu, Harbor policy, and Spice menu. Bound each read to the existing source limit of 5 MiB, close bodies, verify SHA-256 against the manifest, and inspect their facts. Copy permitted fictional originals into ignored evidence only.
9. Require the historical active generation and expected v2 fixtures below. If it changed, stop and review new gold expectations before sending questions. Do not restore an older pointer to force this plan's answers.
10. Save a rollback template copied from this fresh baseline, not a historical `.generated/rag`, `.generated/citations`, or previous rollout rollback file. Record before-state hashes and digest availability.

**Output:** baseline snapshots, verified corpus facts, usable rollback template and digest, with zero Runtime attempts.

### Step 5 — Prepare the exact build context and manifest

1. Require `release_sha` to remain the approved, CI-passing source. Verify no uncommitted application source is substituted.
2. Export only the committed API subtree into a new staging directory under evidence. Use the previous release's CRLF-safe form:

   ```powershell
   git -c core.autocrlf=false archive --format=tar --output=$archivePath $releaseSha restaurant-finder-api
   tar -xf $archivePath -C $stagingRoot
   ```

   Resolve and check archive/extraction paths remain within this task's evidence directory before extraction. Preserve the nested API directory and build from it.
3. Compare every exported tracked API file against the selected Git blob bytes; archive success alone is insufficient. Keep an inventory/hash receipt. Add only the existing `.generated/prompt-manifest.json` to the staged API.
4. Exclude `.env`, credentials, Git metadata, local environments, reports, caches, downloaded originals, staging scripts, and all other generated files. Do not use the working API directory as Docker build context: the current `.dockerignore` does not exclude every generated evidence directory.
5. Validate eight prompts offline from staged source, using the existing API Python environment, `PROMPT_SYNC_MODE=false`, `REQUIRE_PROMPT_MANIFEST=true`, and an absolute staged `PROMPT_MANIFEST_PATH`:

   ```powershell
   & $apiPython -m src.deployment.validate_prompts
   ```

   Run with staged API as working directory. Inspect exit zero, all eight metadata entries, immutable version metadata, and local content hashes. Record the manifest SHA-256. Save/restore only task-changed environment variables in `finally`; do not overwrite `.env`.
6. If the manifest is missing/mismatched, stop for reviewed repair. Neither `sync_prompts` nor creating Bedrock prompt versions is authorized here.

**Output:** exact Git source staging, one allowed extra manifest, eight-prompt validation and hash. No application startup or provider probe.

### Step 6 — Build and publish the ARM64 release image

1. Generate a unique tag `comparison-<release SHA first 7>-<UTC yyyyMMddHHmmss>-arm64`. Check ECR proves it absent; an AccessDenied/network error is not absence. Never push `latest`, reuse a tag, or overwrite the rollback tag.
2. Build from the staged API using the existing Dockerfile and locked dependencies:

   ```powershell
   docker buildx build --platform linux/arm64 --load --label "org.opencontainers.image.revision=$releaseSha" --metadata-file $buildMetadataPath --tag $imageUri $stagedApi
   docker image inspect --format '{{.Os}}/{{.Architecture}}' $imageUri
   ```

   Check each command independently. Require `linux/arm64`; save the build log/metadata, including resolved base identity where available. Record the revision label and Dockerfile/dependency identities.
3. Audit the resulting image with its normal entrypoint overridden and `--network none`. Validate its prompt manifest offline and compare packaged application source hashes with staged Git bytes. Do not launch `src.main`, initialize AWS clients, or invoke a model. Use operation-owned stopped containers only if needed for extraction; remove only those explicitly identified containers afterward.
4. For ECR authentication, create an operation-owned temporary Docker config directory under ignored evidence, restrict and verify its current-user ACL, and use the verified existing daemon endpoint with explicit `--config`/`--host`. This avoids the previously failing global credential helper. Do not change global config or persist auth after the operation.
5. Obtain `aws ecr get-login-password` using `default`/`us-east-2` into an unprinted task-local variable; check the AWS exit code immediately; pipe it directly to `docker login --password-stdin` for the exact intended registry. Check login, push only `$imageUri`, and clear the variable/remove the private auth directory in `finally`. Do not tee tokens into logs.
6. Read ECR `describe-images` for the unique tag and record the actual digest. Inspect the published manifest/build descriptor for ARM64. A local Docker image ID is not the ECR digest.
7. Re-read the fresh baseline digest and confirm retention after this push. If tag/digest identity or rollback availability differs, stop before deployment.

**Output:** `image.json` with release SHA, manifest hash, unique tag, URI, actual digest, architecture, source audit, and build provenance. One pre-publication corrected rebuild is allowed; additional publication/build changes require review.

### Step 7 — Review an image-only CloudFormation change set

1. Re-read current stack/Runtime/endpoint/pointer immediately before preparing the update. Require equality with the captured baseline and no competing update.
2. Synthesize only the existing AgentCore stack with explicit image URI, intended account/region, `--no-lookups`, and a unique ignored output directory. Use existing locked Node/CDK tooling, from the infrastructure directory:

   ```powershell
   $env:CDK_DEFAULT_ACCOUNT = '447393541969'
   $env:CDK_DEFAULT_REGION = 'us-east-2'
   npx --no-install cdk synth restaurantFinder-AgentCoreStack --no-lookups -c "imageUri=$imageUri" --output $synthRoot
   ```

   Restore task-changed variables afterward. Review representation differences against baseline; do not deploy or publish assets from synthesis.
3. Deep-copy the fresh original template and change exactly this leaf, resolving and validating the existing Runtime logical ID:

   ```text
   /Resources/restaurantFinderAgentCoreRuntime/Properties/AgentRuntimeArtifact/ContainerConfiguration/ContainerUri
   ```

4. Recursively compare original/update JSON. Assert exactly one differing leaf at that path. Preserve environment, role, networking, resource definitions/identities, dependencies, parameters, outputs, metadata, Lambda assets, Memory and Gateway settings. Save the machine-readable review.
5. Write the update template UTF-8 without BOM. Its inline TemplateBody must be at most 51,200 bytes. A larger template needs a reviewed upload method; do not silently publish a template object.
6. Prepare a structured `change-set-input.json` with `StackName`, unique `ChangeSetName`, `ChangeSetType=UPDATE`, TemplateBody as actual JSON text, every existing parameter with `UsePreviousValue=true`, baseline capabilities, and existing RoleARN if present. Use a UUID client token for this operation. Preserve existing rollback/notification behavior; no new drift, deployment, import, or rollback settings.
7. Create and inspect the change set:

   ```powershell
   aws cloudformation create-change-set --cli-input-json file://$changeSetInputPath --profile default --region us-east-2 --no-cli-pager
   aws cloudformation describe-change-set --change-set-name $changeSetArn --profile default --region us-east-2 --no-cli-pager
   ```

8. Wait for CREATE_COMPLETE/AVAILABLE, then require exactly one resource change: existing `AWS::BedrockAgentCore::Runtime`, Action Modify, Replacement False, matching logical/physical ID, and only AgentRuntimeArtifact changed. No Add/Remove, conditional replacement, extra properties, nested update, or unrelated resources are acceptable.
9. Show the concrete before/after image and reviewed scope in commentary. Complete PRD approval authorizes execution of this matching change set; a wider change set must stop for review.

**Output:** actual change-set ARN plus exact template/resource review, ready for the approved update.

### Step 8 — Execute and verify the new Runtime

1. Reconfirm the unique tag still resolves to the captured digest. Execute only the reviewed ARN:

   ```powershell
   aws cloudformation execute-change-set --change-set-name $changeSetArn --profile default --region us-east-2 --no-cli-pager
   ```

2. Observe stack events/status with bounded polls, meaningful progress updates, and a 30-minute phase deadline. Do not start a second update/rollback while the stack is transitioning.
3. Require UPDATE_COMPLETE; read Runtime/DEFAULT again. Both must be READY, Runtime must use the exact published URI, its version must be newer than baseline, and DEFAULT must map to that version. Do not invoke a model to establish readiness. If DEFAULT remains stale, report the gap; an extra endpoint update is outside scope.
4. Compare the deployed template against the reviewed update, and Runtime environment/role/network against baseline. Compare physical resource IDs and output identities, allowing the intended Runtime-version value to advance. Re-read active-pointer content/ETag and verify no corpus change.
5. Save post-deployment snapshots and the comparison result. If release-caused readiness/configuration regression occurs, use section 10. Do not silently alter source or environment during validation.

**Output:** verified deployed version and preserved configuration, before any Runtime attempt.

### Step 9 — Prepare the UI, sessions, and ledger

1. Reuse a suitable existing UI only after verifying AWS mode, intended Runtime ARN, region/profile, document bucket, and enabled source viewer from safe process/config evidence. Loading `http://localhost:8010/` alone does not establish AWS mode.
2. If needed, start the existing locked UI with task-local environment: `AGENT_CONNECTION_MODE=aws`, fresh `AGENT_RUNTIME_ARN`, `AWS_REGION=us-east-2`, `AWS_PROFILE=default`, fresh `RAG_DOCUMENT_BUCKET`, and `DOCUMENT_SOURCE_VIEWER_ENABLED=true`. Do not edit `.env` or run a local API substitute.
3. Use the existing Python entrypoint from the UI directory:

   ```powershell
   .venv/Scripts/python.exe -m chainlit run app.py --host 127.0.0.1 --port 8010 --headless
   ```

   For a background helper use `Start-Process -WindowStyle Hidden`, with logs in ignored evidence. Restart only the positively identified project UI process if needed, preserving unrelated work.
4. Use fresh synthetic actor/session identities and new conversations created after deployment; no reused pre-update Runtime session. Assign conversations A for V1/V2, B for V3, and C for V4/V5/V6. Do not send greetings/warm-ups/connectivity probes. The UI's locally generated welcome message does not invoke the agent.
5. Before each send, reserve the ledger slot with case ID, planned prompt, private session correlation, UTC start, and `attempted` state. After completion, record final response/status/citations/error and evidence paths. Keep private IDs out of published summaries.
6. Capture metadata from the existing SSE/UI transport where available; do not invoke Runtime a second time merely to get a JSON capture. A diagnostic harness may replace a scenario, using one total SDK attempt and the same ledger.

**Output:** correct AWS-mode UI, fresh sessions, six-slot ledger. No extra send is authorized.

## 7. Exact initial commit allowlist

Stage only these repository-relative paths after reviewing them. Commands execute within the full workspace above; do not assume a relative path targets the right checkout.

```text
.github/workflows/ci.yml
docs/CI_AND_RAG_EVALUATION.md
docs/DOCUMENT_RAG.md
docs/HANDOFF_PRD_DOCUMENT_COMPARISON.md
docs/HANDOFF_PRD_COMPARISON_PUBLICATION_AND_ROLLOUT.md
restaurant-finder-api/src/application/document_rag/comparison.py
restaurant-finder-api/src/application/document_rag/comparison_workflow.py
restaurant-finder-api/src/application/document_rag/retrieval.py
restaurant-finder-api/src/application/document_rag/workflow.py
restaurant-finder-api/src/application/orchestrator/streaming.py
restaurant-finder-api/src/application/orchestrator/workflow/nodes.py
restaurant-finder-api/src/application/orchestrator/workflow/state.py
restaurant-finder-api/src/domain/document_comparison.py
restaurant-finder-api/src/domain/document_rag.py
restaurant-finder-api/src/evaluation/datasets/document_comparison.json
restaurant-finder-api/src/evaluation/document_comparison.py
restaurant-finder-api/src/infrastructure/model.py
restaurant-finder-api/src/infrastructure/rag_observability.py
restaurant-finder-api/src/infrastructure/vector_store.py
restaurant-finder-api/tests/test_document_comparison.py
restaurant-finder-api/tests/test_rag_evaluation.py
restaurant-finder-ui/tests/test_source_documents.py
```

The warning PRD, generated evidence, credentials, and source originals are excluded. No pull request is needed for this approved publication scope. If the owner later requests one, create it separately and attach its URL to the Codex task.

## 8. Six live functional scenarios

### Source-derived gold facts

Confirm these from the fresh manifest and hashed originals before V1:

- Harbor menu v2, PDF page 1: `Mushroom pasta - RM32 per serving. Contains wheat and milk.`
- Sakura menu v1, Markdown Main dishes: `Mushroom pasta - RM36 per serving. Contains wheat and milk. Available at dinner only.`
- Correct listed-price difference: MYR/RM4 per serving, Harbor lower. The dinner-only qualifier remains visible with Sakura's quote.
- Spice's menu has no mushroom pasta record. Phrase this as missing in the retrieved/active menu evidence, not proof that the real restaurant never serves it.
- Harbor policy v1, Reservations and cancellation: at least 24 hours is free; less than 24 hours incurs RM20 per booking.

These are fictional listed menu facts, not comparable meal availability at every time or a dietary-safety recommendation. Do not replace the model's incorrect answer with a hand-authored expected output and count it as passed.

### Send order and acceptance

| ID | Conversation and exact prompt | Required inspected result |
| --- | --- | --- |
| V1 | A, new: `Compare mushroom pasta prices at Harbor Pasta Lab and Sakura Table Lab. Show the sources.` | Jev or observed Bedrock fallback routes document_qa. Comparison has two supported rows in Harbor/Sakura order, RM32/RM36 per serving, RM4 lower at Harbor, coverage 2/2, and exactly two distinct original citations in one generation. Both complete quotations retain qualifiers. |
| V2 | A, immediately after approved V1: `And what is its cancellation fee?` | Clarifies which restaurant; does not choose either operand, retain a single-venue scope, quote a fee, show citations, rewrite, embed, or query vectors. Existing workflow should route document_qa and clarify. |
| V3 | B, new: `Which is cheaper for mushroom pasta: Sakura or Harbor?` | Same correct prices/difference, rows and source labels in Sakura/Harbor request order, coverage 2/2, no completion-order leak or swapped sources. This verifies aliases and the alternative accepted request form. |
| V4 | C, new: `Compare mushroom pasta prices at Harbor and Spice. Show the sources.` | Partial result: Harbor RM32 with one Harbor menu citation, Spice missing evidence, coverage 1/2, no numeric difference or invented Spice price. No Spice-policy or unrelated-dish quote is presented as mushroom-pasta evidence. |
| V5 | C, after approved V4: `According to Harbor Pasta Lab's policy, what is the cancellation fee?` | Explicit Harbor scope established; complete conditional RM20 policy evidence with its original Markdown citation, no stale comparison/menu citation. |
| V6 | C, immediately after approved V5: `And what is its mushroom pasta price?` | Retains Harbor single-venue scope, quotes RM32 from the menu v2 PDF, not policy/Sakura evidence. One bounded follow-up rewrite is expected; restaurant/type remain server-resolved. |

Send V2 and V6 within **60 seconds** of the respective approved prior response, with the same conversation IDs. Record actual UTC response/send timestamps and gap. Prepare the prompts beforehand. Do not click, download, wait for telemetry, or change domains between those turns. A missed timing threshold is a failed timing criterion even if the functional answer later passes; it does not authorize a free rerun.

Execute V1-V6 sequentially. Open sources only after the dependent follow-ups are sent and answered. Successful source inspection must use actual observed UI controls, not guessed session URLs. Stop later sends on an important failure and preserve unused slots.

The parser supports these bounded request forms, not arbitrary comparative language. Invalid formats, duplicate/unknown venues, third venues, multiple dishes, and adversarial/conflicting evidence remain covered by the inspected offline suite, not extra live requests here. Clearing scope after a partial comparison is covered offline; V5/V6 verify live explicit restoration and later single-venue retention, not an additional live pronoun check after the partial.

## 9. Source inspection and telemetry

### Step 10 — Verify originals without another agent request

1. After V2, reopen V1's Source 1/2 controls. Inspect Harbor PDF page 1 and Sakura Markdown Main dishes with surrounding text. After V3, verify reversed labels still open the correct originals. V4 must have only the supported Harbor source.
2. After V6, inspect V5's Harbor policy Markdown and V6's Harbor PDF. Reopen V1's earlier source while later answers exist to prove answer/source association is preserved.
3. Download each distinct cited original through observed UI controls into the workspace. Resolve paths inside permitted directories. Hash bytes with SHA-256 and compare to that answer's actual pinned citation/manifest, including generation, document ID, version, source hash, and page/section/line metadata. Do not regenerate or substitute a surrogate file.
4. Check complete/partial answers transport structured citations only after unchanged output approval. A masked/blocked answer cannot count as success merely because offline data proves the expected result.
5. Source loading/downloading must not send Runtime requests. Record observed invocation count against the ledger. If source controls fail, preserve the response and flag D8; do not resend the question automatically.

### Step 11 — Inspect correlated workflow evidence

1. Read only the fresh release sessions/time window in existing CloudWatch destinations. Filter using private correlation values and publish only safe summaries. Allow up to ten minutes for telemetry delivery, with waits below 60 seconds.
2. Inspect `router.classify` and the recorded provider/model/fallback reason. V1/V3/V4 must reach document_qa comparison execution; V2/V5/V6 must reach their expected document paths. Bedrock fallback is permitted, but if every request falls back, mark live Jev operation unmeasured rather than claiming Jev worked. Do not break credentials to force fallback.
3. For comparisons inspect `rag.comparison.plan`, two `rag.comparison.worker` scopes, `rag.embed`, `rag.vector_query`, applicable `rag.comparison.select`/`validate`, and `rag.comparison.aggregate` coverage/status/citation count. Worker generation IDs must agree with citations and each other.
4. Worker timestamp overlap can support a live concurrency observation if available. Source code and offline barrier tests prove the concurrency contract; without usable live span timing, report live overlap unmeasured. Do not infer it from a fast answer.
5. For V2 expect clarification with no retrieval/selector/rewrite; for V5/V6 inspect scope/retrieval/selection and V6 rewrite where available. Inspect common output moderation and one parent `memory.save` operation per approved turn where emitted. Do not query memory with another agent/tool request or infer successful durable storage from the answer alone.
6. Distinguish logical call counts from provider HTTP retries. Exact live document-type filters, single manifest-pin read count, selector internals, duplicate persistent memory events, and total spend may be absent from existing instrumentation. Mark those unmeasured unless actual inspected evidence supports them. Do not add instrumentation or dump internal checkpoints during this rollout.
7. Legacy logging warnings and uncorrelated HTTP-parser warnings were recorded in previous work. Capture whether they recur, but do not attribute them to this feature without request-correlated evidence or expand into the separate warning repair task.

**Output:** source hash receipt and safe trace/call summary. Failure or missing evidence remains visible in D7-D9; green CI is not a substitute.

## 10. Failure handling and rollback

1. Before deployment, stop on failed CI/auth/Docker, unexpected source/account/baseline, invalid manifest, wrong architecture, unsafe image contents, reused tag, threatened rollback retention, or wider change set. Complete independent read-only evidence/reporting; do not bypass the gate.
2. If deployment fails, observe CloudFormation's automatic recovery. Wait for a stable state; never launch competing updates. If it restores the fresh baseline, verify image/config/DEFAULT and record that outcome. Do not issue a redundant manual rollback.
3. A failed live release scenario consumes its slot and stops remaining sends. Record whether it is a routing, selector, retrieval, arithmetic, citation, guardrail, session, or infrastructure failure based on inspected evidence. No code tuning/rebuild/resubmission is included automatically.
4. Full PRD sign-off authorizes one manual rollback **only** for a release-caused deployment failure/regression, when the stack is stable, this release is still active, no concurrent/newer change exists, and the captured baseline digest is available. Missing telemetry alone does not prove a runtime regression. If ownership/cause/current state is uncertain, preserve evidence and obtain a narrow decision.
5. Prepare a rollback UPDATE by deep-copying the currently deployed template and restoring only ContainerUri to the fresh baseline image URI. Assert the deployed/current configuration still matches the intended release apart from the image. Compare the result to the saved baseline template and inspect the same one-Runtime/no-replacement change-set rules. Never apply an old pre-RAG template or reset environment/role.
6. Execute the reviewed rollback ARN once. Verify UPDATE_COMPLETE, Runtime READY on the baseline URI/digest, DEFAULT READY on the resulting restored version, and preserved role/environment/pointer. A rollback creates a new version; do not require the old numeric version to reappear.
7. Rollback readiness checks add no Runtime sends. A model smoke check after rollback needs an unused authorized slot replacing a planned case, or a separately approved new allowance. Never infer restored functional behavior solely from READY.
8. If stack recovery needs rollback continuation, role/IAM changes, a missing image republish, endpoint mutation, more attempts, Docker restart, or application repair, stop and describe the smallest required deviation. Do not expand this PRD silently.

## 11. Closeout and publication

### Step 12 — Preserve evidence and publish the result

1. Re-read final stack/Runtime/DEFAULT, tag/digests, environment/role, and active pointer. Record whether the release is retained, automatically recovered, or manually rolled back.
2. Close D1-D10 individually with inspected evidence. Record actual used/unused slots, prompts that were replaced or never run, timing gaps, actual routing providers, original-file hashes, and missing telemetry. Do not mark an incomplete matrix successful.
3. Update section 13 with release SHA, CI run/artifact receipt, manifest hash, tag/digest/build architecture, before/after versions, actual change-set scope, V1-V6, D1-D10, and remaining gaps. Raw private evidence stays ignored; publish only safe concise records and non-secret stable references.
4. Stage/commit/push only this PRD's execution record and, if useful, a concise checkpoint in `docs/DOCUMENT_RAG.md` or `docs/CI_AND_RAG_EVALUATION.md`. Preserve the warning PRD and all unrelated work. Do not mix an application fix into the closeout commit.
5. Inspect automatically triggered CI for the documentation commit too. It has a different SHA from the release image; record both. Confirm Git blob bytes of the packaged API/dependency files match the original release source so a later docs-only commit is not misrepresented as an image rebuild.
6. Remove only operation-owned scratch archive/context/auth directories after resolving them inside the evidence root. Preserve rollback/provenance/ledger/source receipts needed for the demo and all owner files. Verify temporary Docker auth removal even on failure. Do not remove cached user tools or earlier phase evidence.
7. Leave an owner-useful project UI running if started for the demo; privately record its PID/command/log. Report the end state and any unmet criterion. Stop before scripting or recording a walkthrough.

Suggested local evidence inventory:

```text
source-review.json
release-ci.json and downloaded allowlisted CI artifacts
baseline-stack.json / baseline-runtime.json / baseline-endpoint.json
baseline.template.json / runtime-rollback.template.json
baseline-active.json / manifest.json / original-source-verification.json
source-inventory.json / prompt-validation.json / image.json / build metadata
runtime-update.template.json / change-set-input.json / template-review.json
change-set-review.json / deployed-verification.json
runtime-ledger.json / fictional response captures / source-download-verification.json
safe-telemetry-summary.json / final-verification.json / closeout-ci.json
```

No login material, Docker auth directory, secret dump, signed download URL, unrelated conversation, or raw credential-bearing trace belongs in that retained inventory or Git.

## 12. Open questions and fixed assumptions

- Execution approval and the new six-attempt allowance were granted by the owner's explicit **proceed** after review. Preparation alone did not authorize those actions.
- Current AWS/GitHub login, Docker health, DEFAULT mapping, rollback-image retention, live corpus identity, and prompt validity are unresolved preflight facts; inspect them before asking the owner for discoverable information.
- Assumption: keep the existing Jev router, existing Haiku configuration, Titan V2/512, corpus v2, branch, stack, and loopback UI. Different configuration requires reconciliation, not an automatic replacement.
- The six-attempt allowance is accepted as a bounded functional exercise if this PRD is approved. It is not a monetary ceiling; a required dollar cap must be agreed before execution.
- No deliberate Jev failure, arbitrary document upload, invalid-input live matrix, benchmark, warning repair, or recorded demo is included.
- Use the current agent/runtime model unless the owner explicitly chooses another supported model. Do not claim execution used a particular model without runtime metadata.

## 13. Execution record — fill only with inspected outcomes

**Preparation completed:** This PRD was created after inspecting local implementation, release/CI workflows, source handling, provider bounds, and historical release evidence. No test suite, AWS check, model call, Git publication, Docker operation, deployment, UI restart, or walkthrough was performed during preparation.

| Record | Outcome |
| --- | --- |
| Owner execution approval and date | Explicit **proceed** on 2026-10-12 after PRD presentation. |
| Fresh six-attempt allowance | Approved: maximum six Runtime attempts, including failures/replacements. |
| Release commit / matching remote SHA | Not executed |
| Release CI run / artifact checks | Not executed |
| Fresh AWS/Docker baseline | Not executed |
| Prompt manifest validation/hash | Not executed |
| ARM64 image tag/digest/provenance | Not executed |
| Reviewed/actual change set | Not executed |
| Before/after Runtime and DEFAULT versions | Not executed |
| Environment/role/pointer preservation | Not executed |
| V1 / V2 / V3 / V4 / V5 / V6 | Not executed |
| Runtime attempts used / remaining | 0 / 6 approved |
| Originals/source hashes | Not executed |
| Routing/worker/moderation/memory telemetry | Not executed |
| D1-D10 acceptance matrix | Not executed |
| Retain/recovery/rollback decision | Not executed |
| Closeout documentation SHA / CI | Not executed |
| Remaining gaps/deviations | Live-release criteria pending. GitHub CLI absent from PATH; existing Git credential helper plus GitHub REST reads verified owner identity/access without installing tools or exposing credentials. Remote feature FETCH_HEAD equals the inspected base, with zero divergence. |
