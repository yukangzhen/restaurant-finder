# Handoff PRD: Deploy the RAG query-scoping fix and verify the live demo

**Status:** Execution closed on 2026-10-09 with the R6 timing deviation recorded. Runtime 12 is retained; all six functional expectations passed. Documentation was published to the feature branch and its offline CI artifacts were inspected; see the publication receipt below.
**Prepared:** 2026-10-09, Asia/Kuala_Lumpur.
**Audience:** The owner and the agent executing the rollout for the LinkedIn AI engineering demonstration.
**Selected application source:** `feat/jev-router`, commit `ef146a295fe8edd0c5a9fa50ff5c9eccf70de35e`.

## 1. Outcome and reason

Put the already implemented restaurant-name masking fix into the existing AWS AgentCore Runtime, then demonstrate that the real application returns document-grounded answers and opens the original cited files. The code and offline evaluation are complete. The missing deliverable is a verified deployed version with a small set of live functional results.

The application is a controlled portfolio demonstration with fictional restaurant documents. Success enables the owner to record an accurate technical walkthrough of deployment, document retrieval, conversational scope, quotation validation and source inspection.

Deliverables:

1. One uniquely tagged ARM64 API image built from the selected source commit and the validated existing prompt manifest.
2. One reviewed update to the existing AgentCore stack, changing only its Runtime container image.
3. A fresh rollback snapshot that preserves the current RAG and clickable-citation configuration.
4. Six explicitly planned live Runtime attempts, including UI sends and any diagnostic replacements, with inspected results and correlated telemetry.
5. Browser evidence that the PDF and Markdown citations open the original documents and that downloads match their pinned source hashes.
6. A final execution record distinguishing passed, failed, blocked and unmeasured criteria, with no unsupported production-readiness or performance claim.

## 2. Evidence inspected while preparing this PRD

### 2.1 Verified local/code state

- The feature branch is `feat/jev-router`; HEAD is the selected source commit. The worktree was clean before creating this PRD.
- `docs/HANDOFF_PRD_RAG_QUERY_SCOPE.md` records the completed name-span masking fix, scoped regression coverage and deployment boundary.
- The saved verification record at `restaurant-finder-api/.generated/evaluation/query-scope-verification.json` records all four successful GitHub CI jobs for that exact HEAD and matching remote SHA. Its artifact inspection confirms 135 API tests, 26 UI tests, 3 infrastructure tests and 17/17 offline RAG cases with 374 measured checks.
- The accepted final run is [Offline quality checks, 37760569272](https://github.com/yukangzhen/restaurant-finder/actions/runs/37760569272). These are previous inspected results, not tests rerun during PRD preparation.
- `Dockerfile` uses the locked dependencies, validates eight managed prompt definitions before completion, runs as an unprivileged user and starts `opentelemetry-instrument python -m src.main`.
- The existing local `.generated/prompt-manifest.json` contains eight prompt entries. Its hashes and immutable metadata must still be validated before packaging; counting entries alone is insufficient.
- The Docker build context normally includes ignored `.generated` content that is not covered by every `.dockerignore` rule. Use the tracked-source staging procedure below so local reports, sessions and downloaded sources cannot enter this image.

### 2.2 Historical deployed baseline; refresh before execution

The clickable-source PRD and its saved final Runtime record establish the following historical baseline:

| Item | Recorded value |
| --- | --- |
| AWS account | `447393541969` |
| Region/profile | `us-east-2` / `default` |
| AgentCore stack | `restaurantFinder-AgentCoreStack` |
| Runtime ID | `restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu` |
| Historical status/version | `READY` / `11` |
| Historical active image | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:citations-00a846a-20261008052831-arm64` |
| Historical image digest | `sha256:7704ff7ce9e906e6508d2128a16b5479b6fb27608e0d05b38bf143c444700761` |
| ECR repository | `restaurantfinder-agent` |
| Document bucket | `restaurantfinder-ragstack-documentbucketae41e5a9-vqrmcnuycjq5` |
| Vector index | `arn:aws:s3vectors:us-east-2:447393541969:bucket/restaurantfinder-rag-447393541969-us-east-2/index/documents-titan-v2-512` |
| Active generation | `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` |
| Local demonstration address | `http://localhost:8010/`, bound to loopback |

The saved original Harbor menu v2 has SHA-256 `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10`. The saved Harbor policy v1 has SHA-256 `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471`. Use a fresh pinned manifest as authority during execution.

These values are discovery hints. They are not a new live AWS inspection. Stop on a materially different baseline rather than overwriting newer work.

### 2.3 Current readiness checks on 2026-10-09

- AWS CLI, Docker CLI, uv and Node executables were found.
- A read-only `aws sts get-caller-identity --profile default --region us-east-2` attempt failed with **Your session has expired**. No current identity, stack state or Runtime state was established.
- A permitted `docker info` attempt returned HTTP **500** from `dockerDesktopLinuxEngine`; valid daemon/architecture/memory fields were not obtained. The PowerShell pipeline exit code did not represent Docker success. Docker readiness is unresolved.
- An initial sandboxed listener query returned no rows. Elevated execution inspection later established that the existing project UI was running on port 8010; the empty sandbox result was not proof that the server was absent.
- Installed AWS CLI input skeletons were inspected for Runtime reads and CloudFormation change-set creation. Skeleton generation made no AWS service calls.
- No image was built or published, deployment executed, prompt synchronized, document ingested, live model invoked, or demo process restarted while preparing this document.

## 3. Authorization and scope

The owner's earlier **okay proceed** authorized preparing this reviewable PRD. After the PRD was saved and presented, the owner supplied explicit **proceed** on 2026-10-09, approving the scoped execution and six-request allowance below. Their `AGENTS.md` sign-off gate is satisfied.

### Approved authorization

- Prepare ignored local staging/evidence files and validate the selected source and existing prompt manifest offline.
- Build and publish one unique API image to the existing ECR repository; one corrected local rebuild before publication is allowed if packaging fails, with no application-source edits.
- Create, inspect and execute one existing-stack UPDATE change set only when its actual scope is exactly the Runtime image update below.
- Verify deployment readiness, preserve the existing corpus, read original documents using existing access and inspect correlated CloudWatch telemetry.
- Start the local loopback demo on port 8010 if it is absent, or restart only the positively identified project demo process if configuration must be refreshed. Do not stop unrelated processes, ports or containers.
- Perform at most six total live Runtime invocation attempts, with no automatic client retries. All API/browser attempts, including failures and diagnostic substitutes, consume this allowance.
- If this rollout causes a deployment failure or regression, execute one reviewed Runtime-image-only rollback to the fresh captured baseline within the conditions in section 10.
- Record the result in this PRD and a concise engineering guide update if useful; commit/push only these scoped records to `feat/jev-router`, then inspect automatically triggered offline CI. No merge or deployment workflow dispatch is included.

### Excluded

- Corpus/index writes, ingestion, active-pointer publication, vector re-embedding or deletion.
- Prompt synchronization, draft changes or new managed prompt versions. A missing/mismatched manifest requires a separately reviewed repair.
- IAM, credentials, secrets, billing, quotas, tracing destinations, guardrail configuration, Gateway, Lambda, Memory, ECR lifecycle rules, stack identities or network-mode changes.
- Application/UI code changes, dependency upgrades, a router redesign, new evaluation instrumentation, benchmarking, model comparisons or public hosting.
- PR creation, `main` merge/push, Actions settings changes, deployment/destruction workflow dispatch or `cdk deploy --all`.
- Docker/WSL reset, termination of unrelated work, broad machine cleanup or destructive rollback.

If the owner approves the entire PRD, continue within these matching boundaries without another generic approval request. Ask only for a material deviation, a larger request allowance or a missing permission that requires a new grant.

## 4. Definition of done

| ID | Observable criterion |
| --- | --- |
| R1 | Fresh AWS identity matches the intended account; stable stack/Runtime/DEFAULT endpoint, current image/digest and complete rollback snapshot are captured. |
| R2 | Image provenance records the selected source SHA, prompt-manifest hash and validated eight prompt definitions. Build context contains tracked API files plus only the required prompt manifest. |
| R3 | Local image/build descriptor is `linux/arm64`; ECR read-back records its unique tag and digest. The previous active image remains available for rollback. |
| R4 | Canonical template comparison permits exactly one leaf change: Runtime `AgentRuntimeArtifact.ContainerConfiguration.ContainerUri`. The actual change set contains one Runtime Modify, Replacement=False, with AgentRuntimeArtifact as its only changed property. |
| R5 | Stack reaches UPDATE_COMPLETE; Runtime is READY on the exact new image; DEFAULT endpoint is READY on the new version. Environment/role, other stack resources and active-pointer content remain equal to the fresh baseline. |
| R6 | Planned menu, full-name policy, mixed, follow-up, unsupported and clarification scenarios each meet Step 8 expectations within six total Runtime attempts. No hidden resubmission is performed. |
| R7 | PDF and Markdown links are clicked in the browser, their original content/location is inspected and downloaded bytes match the pinned source hashes. The final answer's citations cannot open a different answer's source. |
| R8 | Fresh request-correlated telemetry identifies document_qa routing and relevant RAG stages, and records actual routing provider/fallback where available. Missing telemetry/counters are explicitly unmeasured. |
| R9 | Final evidence records SHA/tag/digest, before/after versions, exact change-set scope, request ledger, scenario results, source hashes, deployment gaps and rollback outcome. Scoped documentation is published and its offline CI inspected if authorized. |

A successful image update alone does not satisfy R6-R8. An offline simulation alone does not establish live model behavior. A previous CI run is valid historical evidence for its SHA, not a newly executed test result.

Existing `rag.vector_query` spans identify restaurant/generation/top-k but do not explicitly record the document-type filter. Do not claim independent live measurement of the exact QueryVectors filter from a policy citation alone. Use deployed-code provenance plus existing deterministic regression evidence for resolver correctness, and live outputs/telemetry for delivered behavior. Any unexposed provider-call count is also unmeasured; adding instrumentation is outside this rollout.

## 5. Cost and request boundary

This is a six-request functional check using the existing services. Image storage, inference, embeddings, guardrails, memory/checkpoint operations, S3/vector reads and telemetry may incur charges. Rollback cannot reverse incurred charges or published image storage.

- **Runtime attempts:** hard limit of six calls, started sequentially. Reserve each ledger slot before sending. A timeout or failed invocation still consumes its slot; do not rerun automatically. A diagnostic request replaces a planned scenario and leaves that scenario unmet unless it supplies equivalent inspected evidence.
- **Planned RAG logical calls:** five retrievals/query embeddings at most, up to five answer-selection invocations, and one follow-up rewrite. Clarification should perform none of those operations. Each request may use Jev once, with the existing Bedrock routing fallback if Jev is unavailable. The expected fallback path adds at most six logical Haiku routing calls for these planned cases.
- **Known limits:** Jev has zero configured retries. Query embeddings and document/vector clients use one total SDK attempt. Selector output is capped at 1,600 tokens; rewrite output at 400 tokens; RAG context at 9,000 characters; RAG node timeout at 60 seconds. UI Runtime SDK attempts are capped at one, with a 300-second total response deadline. Source preparation is bounded by the existing UI limits.
- **Provider retries:** the Haiku model factory does not explicitly set a one-attempt SDK policy or a router output-token cap. Logical model calls are not a hard cap on every HTTP attempt or on dollar spend. Inspect actual SDK retry settings before the first live request and record the configured limits; do not change Runtime environment/source to enforce a new policy under this image-only authorization. Stop further requests on a provider retry/error or unexpectedly expanded workflow.
- No additional live warm-up, greeting, embedding-access probe, direct vector query, fallback stress test, on-demand/online evaluator or benchmark is authorized. The first planned UI request is the functional smoke check.
- Read-only metadata/pointer/source checks and telemetry inspection add no intended model/embedding calls. Source clicks/downloads must not send another agent request. Avoid logging raw credentials, full HTTP headers or unrelated sessions.
- This PRD proposes a bounded request allowance, **not a guaranteed dollar ceiling**. If a fixed monetary cap is required, settle that before approving execution; current provider pricing/retries and infrastructure charges must be checked rather than guessed.

## 6. Execution steps

All commands below describe future approved execution. Preserve actual exit codes. In PowerShell, check `$LASTEXITCODE` immediately after every native process, before piping/parsing its output; an empty parsed object or later pipeline success is not readiness evidence. Write JSON/text as UTF-8 without BOM and never interpolate secrets into a logged command.

### Step 1 — Restore readiness without changing project services

1. Confirm owner sign-off covers section 3 and the six-request allowance. Record it here.
2. Ask the owner to restore the existing login interactively if still expired:

   ```powershell
   aws login --profile default
   aws sts get-caller-identity --profile default --region us-east-2 --no-cli-pager
   ```

3. Verify account `447393541969` and record the authenticated ARN privately in the baseline. An account alias is not an alternative credential profile. Stop on an unexpected account or principal rather than switching credentials automatically.
4. Recheck Docker's Linux engine. `docker info` must succeed with a valid Linux daemon response. Docker Desktop may be started if absent; do not reset Docker/WSL or terminate existing work. If HTTP 500 persists, report it and request a narrow recovery decision before a build.
5. Recheck ports 8000, 8010 and 8080, their owning processes and the existing UI dependencies. Preserve unrelated applications. Do not start the API locally or make paid startup checks as a substitute for this AWS rollout.

**Output:** approved scope and successful identity/Docker checks, or a clearly reported readiness blocker. No deployment occurs on a failed preflight.

### Step 2 — Capture the fresh deployment and rollback baseline

1. Create one ignored evidence directory, `restaurant-finder-api/.generated/rollout-query-scope-20261009/`, with a unique suffix if it already exists. Do not overwrite previous evidence.
2. Read the AgentCore/ECR/RAG stacks with `aws cloudformation describe-stacks`, using `default` and `us-east-2` explicitly. Read the AgentCore stack's `Original` template using `get-template`; normalize TemplateBody whether returned as a JSON object or a JSON string.
3. Read Runtime and DEFAULT endpoint:

   ```powershell
   aws bedrock-agentcore-control get-agent-runtime --agent-runtime-id restaurantFinder_Agent-Ha58oX5Psu --profile default --region us-east-2 --no-cli-pager
   aws bedrock-agentcore-control get-agent-runtime-endpoint --agent-runtime-id restaurantFinder_Agent-Ha58oX5Psu --endpoint-name DEFAULT --profile default --region us-east-2 --no-cli-pager
   ```

4. Require a stable stack, READY Runtime/endpoint and matching current version/image. Capture environment, role, version, image URI, endpoint mapping, stack parameters and CloudFormation execution role. Stop if an update is underway or deployed configuration materially differs from the inspected handoff.
5. Read the current image digest from ECR and retain proof that its tag/digest can be fetched. Inspect the existing lifecycle policy and recent images: one push must not threaten the rollback image's retention. Do not alter lifecycle rules under this PRD.
6. Read `rag/active.json`, its ETag and pinned manifest through existing access. Validate it with `GenerationManifest`; verify the recorded generation and Harbor menu v2/policy v1. Record existing vector-index metadata and bucket public-access blocks through metadata reads, with no vector query/embedding.
7. If the generation/facts differ from the historical values, stop and adjust the gold scenario expectations through review. Do not republish an old pointer to force the expected answers.
8. Save `baseline-stack.json`, `baseline-runtime.json`, `baseline-endpoint.json`, `baseline.template.json`, `baseline-active.json`, `manifest.json` and image/digest metadata locally. The new rollback template is an unchanged copy of this fresh baseline template.

**Critical:** Do not use `.generated/rag/runtime-rollback.template.json` for this rollout. It restores the earlier pre-RAG image/environment and disables RAG. `.generated/citations/runtime-rollback.template.json` also represents an older phase. Capture the actual current image and full environment anew.

### Step 3 — Prepare an exact, minimal image build context

1. Inspect `git status`, the selected commit and the scoped changes since the historical citation image's source commit. Existing changes outside the resolver/verification work must be understood before this release; do not deploy new unreviewed edits.
2. Require the selected source to remain `ef146a295fe8edd0c5a9fa50ff5c9eccf70de35e`. Later documentation-only commits may exist, but do not silently select a different application source.
3. Use `git archive` of the selected commit's `restaurant-finder-api` subtree into a staging directory under the new evidence directory. Resolve all staging paths within the repository before extraction. Preserve the nested API layout and build from that staged API directory.
4. Copy only the existing `.generated/prompt-manifest.json` into the staged API's `.generated` directory. Do not copy `.env`, credentials, `.venv`, other generated records, source downloads, caches, Git metadata or the current working directory wholesale.
5. Validate all eight prompt definitions offline with the staged source and existing locked environment, using `python -m src.deployment.validate_prompts`. Use an absolute manifest path if needed. Ensure `PROMPT_SYNC_MODE=false` and `REQUIRE_PROMPT_MANIFEST=true`; clear unrelated offline-test overrides after validation. Save the result and manifest SHA-256.
6. Verify there is no application-source difference between the staged tracked files and the selected Git source. Review the staged file inventory; `.dockerignore` removes tests/sample documents from the image.
7. Existing inspected CI covers the selected SHA. If needed to validate the local staging path, the existing API suite and 17-case offline evaluator may run with client-construction guards and the documented absent-manifest offline settings. No new tests, dependencies or source changes are included. Restore packaging settings afterward.

**Output:** exact-source staging inventory and eight-prompt hash validation. If prompt metadata is missing or stale, stop; do not run `sync_prompts` automatically.

### Step 4 — Build and publish the one release image

1. Choose a unique tag such as `query-scope-ef146a2-<UTC-yyyyMMddHHmmss>-arm64`; check it is absent in ECR. Record the time convention explicitly. Never use `latest` or overwrite a previous release tag.
2. Build from the staged API context with the existing Dockerfile, `--platform linux/arm64`, an OCI revision label for the full source SHA and the exact proposed tag. Use the existing locked dependencies. Save build metadata/logs without credentials.
3. Inspect local image architecture/OS and the built resolver source bytes. Offline inspection must override the normal application entrypoint; do not start infrastructure initialization or invoke models inside the container. Confirm manifest validation also passed in the Docker build.
4. Acquire ECR login credentials through the existing AWS profile and pipe directly to `docker login --password-stdin`; do not print or persist the token in evidence.
5. Push only the unique release tag. Inspect the push exit code, then read it back with ECR `describe-images`. Save its actual digest and ARM64 build descriptor. Never infer ECR digest solely from a local image ID.
6. Reconfirm that the fresh baseline image remains retrievable after publication. ECR lifecycle expiry is asynchronous; retain the checked lifecycle facts in the final record.

**Output:** `image.json` containing source commit, manifest hash, unique tag, image URI, digest and build architecture. Image storage/publication is not undone by Runtime rollback.

### Step 5 — Prepare and review the exact change set

1. Synthesize the existing AgentCore stack with the explicit new image URI as CDK context into a distinct ignored `cdk.out` directory, with the intended account/region and no lookups. Do not deploy stacks or publish Lambda assets. Review consistency with the saved baseline; preserve any previously reviewed deployed representation differences.
2. Prepare the actual UPDATE template by deep-copying `baseline.template.json` and changing only:

   ```text
   Resources.restaurantFinderAgentCoreRuntime.Properties
     .AgentRuntimeArtifact.ContainerConfiguration.ContainerUri
   ```

   Resolve the Runtime logical ID from the fresh template and confirm it equals the expected ID. Preserve all environment, IAM, Lambda code, Gateway/Memory configuration, metadata, dependencies, parameters and outputs.
3. Canonicalize the baseline/update JSON and compare recursively. Assert exactly one leaf difference at that path. Save this assertion/result as `template-review.json`. Do not accept extra property changes because a broad CDK preview describes them as harmless.
4. Write a UTF-8, BOM-free `runtime-update.template.json`. Check its byte length against CloudFormation's 51,200-byte inline limit. If it exceeds the limit, stop for a reviewed template-publication method; uploading a new template object is not included automatically.
5. Create an UPDATE change set with a unique name, the explicit template, every existing parameter using `UsePreviousValue=true`, the existing execution role and the baseline required capabilities. IAM capability acknowledgement permits parsing existing IAM resources; it does not authorize changing their policies. Omit new deployment/rollback/drift settings and preserve existing behavior.
6. Inspect the actual `describe-change-set` result after completion. Require:

   - Status `CREATE_COMPLETE`, ExecutionStatus `AVAILABLE`.
   - Exactly one resource change: `Modify`, the existing Runtime logical/physical ID, `AWS::BedrockAgentCore::Runtime`.
   - `Replacement=False`, with `AgentRuntimeArtifact` as the only changed property.
   - No added/removed resources, IAM/environment changes, nested stack updates or unrelated changes.

7. Save the change-set ARN and review result. Report its concrete image transition and matching scope in commentary. Under full PRD approval, execute the matching change set without requesting another generic confirmation. If scope differs, stop before execution and report the difference.

### Step 6 — Execute and verify deployment readiness

1. Execute only the reviewed change-set ARN. Record start time and result; do not dispatch GitHub deployment workflows or separately call `update-agent-runtime`.
2. Observe CloudFormation using bounded waits/polls; keep individual blocking waits under 60 seconds and provide meaningful progress updates. Allow up to 30 minutes for this phase before reporting unresolved state. Do not start another update or rollback while the stack is transitioning.
3. On UPDATE_COMPLETE, read the current Runtime and DEFAULT endpoint. Require READY, the new URI, a version newer than the captured baseline and DEFAULT mapped to that version. The UI uses qualifier DEFAULT, so Runtime readiness alone is insufficient.
4. Read back the deployed template, environment and role. Compare against the fresh baseline/update to prove the expected image-only change. Verify Lambda/Gateway/Memory identifiers and the active-pointer content remain equal to baseline; record the post-deployment pointer ETag as supporting metadata.
5. Save `deployed-stack.json`, `deployed-runtime.json`, `deployed-endpoint.json` and comparison results. Readiness control calls do not consume the six live invocation slots.

### Step 7 — Prepare the UI and invocation ledger

1. Recheck the port-8010 listener and owning process. If an appropriate demo is already running in AWS mode with the correct ARN and document bucket, reuse it. Do not restart it merely to update an image; the AWS endpoint controls the version for new sessions.
2. If absent, start the existing UI with its locked environment, `AGENT_CONNECTION_MODE=aws`, the fresh Runtime ARN, `AWS_REGION=us-east-2`, `AWS_PROFILE=default`, `DOCUMENT_SOURCE_VIEWER_ENABLED=true` and the fresh document bucket. Use task-local environment variables; do not overwrite `.env` or credentials.
3. Start the Python-module entrypoint on loopback with output captured to an ignored log:

   ```powershell
   .venv/Scripts/python.exe -m chainlit run app.py --host 127.0.0.1 --port 8010 --headless
   ```

   If using Start-Process for the helper, use `-WindowStyle Hidden`. Preserve an unrelated process holding the Chainlit launcher. Do not run dependency upgrades or force-stop port 8000.
4. Inspect `http://localhost:8010/` in the in-app browser. Loading the page or opening a new chat is not itself permission to send an extra prompt. Verify AWS-mode configuration from the process/start command safely, without dumping all environment variables.
5. Create `runtime-ledger.json` with maximum 6, used 0. Use fresh synthetic identities and UUID conversation IDs; never reuse an old pre-update Runtime session. Reserve a slot with case ID/session/start time before each send. Record completion/error/timeout and evidence paths afterward.
6. Keep F1 and F2 in the same new conversation. Use fresh conversations for F3-F6 so their clarification/scope expectations are meaningful. Send no extra greeting or connectivity message.

### Step 8 — Run the six planned live scenarios

Execute sequentially using the real UI where practical. If a diagnostic API harness must replace a UI send, use one total Runtime SDK attempt and the same planned prompt; count it as that slot, not a free extra check. Capture available approved answer text, citation metadata, source elements, terminal completion and correlated time/session evidence. Stop on a serious failure before sending the remaining cases.

| ID | Prompt and context | Expected inspected behavior |
| --- | --- | --- |
| F1 | Fresh chat: `According to Harbor Pasta Lab's menu, what is the mushroom pasta price?` | Document answer quotes `Mushroom pasta - RM32 per serving.` from `harbor-menu`, v2, PDF page 1 in the pinned generation. No RM28 or another restaurant's price. Open the menu source. |
| F2 | Same chat immediately after approved F1: `And what is its cancellation fee?` | Retains Harbor scope and quotes the RM20 late-cancellation rule from `harbor-policy`, v1. A single follow-up rewrite is expected. The rewrite cannot change restaurant/type filters. Open the policy source. |
| F3 | New chat: `According to Harbor Pasta Lab's policy, what is the cancellation fee?` | Full-name policy question delivers policy evidence for Harbor, including the less-than-24-hours condition and RM20 per booking. No menu citation or unrelated price. This exercises the name-masking fix's live behavior. |
| F4 | New chat: `According to Harbor Pasta Lab's menu and policy, what is the mushroom pasta price and cancellation fee?` | Both correct facts, with distinct menu-v2/PDF and policy-v1/Markdown citations. Open both and verify each belongs to this answer. Either citation order is acceptable. |
| F5 | New chat: `According to Harbor Pasta Lab's menu, what is the restaurant's Wi-Fi password?` | Explains that active documents lack enough evidence, without inventing a password, quoting unrelated menu text as an answer, showing a source citation or searching the web. |
| F6 | New chat without approved scope: `According to the documents, what is the cancellation fee?` | Asks which fictional restaurant to use. No selected answer, citations, query embedding, vector query or answer-selection stage for this request. |

All six are document questions. Expected routing is `document_qa`. Record Jev vs Bedrock fallback as observed; do not deliberately break the provider to force fallback. If a request runs restaurant search, browser tooling or memory retrieval as a substitute for documentary evidence, stop further requests and record the failure; do not silently tune the router under this rollout.

The correct price and fee come from the fresh verified original sources, not from trusting the model's generated citation. Validate exact quotes and their conditions. Escape/display formatting can differ without changing the source fact.

### Step 9 — Inspect actual citation documents and fresh telemetry

1. On F1/F2/F4, click the actual observed source controls. Inspect the whole Harbor menu PDF on page 1 and the policy's `Reservations and cancellation` section around lines 5-8. Confirm RM32 and the conditional RM20 rule appear with surrounding context.
2. Download each distinct cited original through its observed Chainlit session-file control. Resolve downloads within the permitted workspace. Compute SHA-256 and compare to that answer's pinned manifest. Preserve the original bytes; do not regenerate a PDF/Markdown surrogate.
3. Confirm both mixed-answer controls have distinct names and open the intended files. Reopen an earlier answer's source while later answers exist to check answer/source association. Clicking/downloading must not invoke the agent again.
4. Read fresh CloudWatch records only for the rollout's sessions/time window. Inspect `router.classify` provider/intent, `rag.scope`, `rag.embed`, `rag.vector_query`, `rag.retrieve`, `rag.answer_select` and `rag.validate` where each is expected. F2 should include rewrite model activity; F6 should lack retrieval/selection activity.
5. Check approved answer delivery and relevant application errors, guardrail blocking or source-load failures. If telemetry is delayed, use bounded read-only waits for up to ten minutes; individual waits remain below 60 seconds. Stop waiting and report missing delivery instead of marking it passed.
6. Record observed tokens/embedding attempts/retrievals where instrumentation provides them. Do not derive model confidence, ranking quality, exact live filters, hidden retries or dollar costs from a successful answer.

### Step 10 — Close out and publish the scoped record

1. Re-read final Runtime/endpoint/stack/active-pointer state and confirm the rollback image remains available.
2. Record R1-R9 individually as PASS/FAIL/BLOCKED/UNMEASURED, with inspected evidence for each result. Record the six-slot ledger and any unused slots; unused slots are not permission for unrelated exploration.
3. Clearly state whether the deployment is retained or rolled back and whether the UI remains running. A process started for the owner's demo may remain running; its PID/command/log path should be documented privately. Remove transient archive/build context only after verifying resolved paths are inside the new evidence directory, preserving needed evidence and all user files.
4. Update this PRD's execution section with actual source SHA, image tag/digest, versions, change-set ARN/scope, scenario/source outcomes, call allowance and remaining gaps. Add a concise deployment checkpoint to the engineering guide if useful.
5. Commit/push only reviewed documentation to `origin/feat/jev-router` under full PRD sign-off. Preserve unrelated changes. Inspect the automatically triggered offline CI for its actual SHA and artifact results; do not enable or dispatch deployment workflows.
6. Report the verified result and any remaining limitation. Demo scripting/recording is a later task; do not publish on LinkedIn or in the owner's name under this authorization.

## 7. Evidence handling

Keep private machine/account artifacts under the new ignored directory. Suggested permanent local evidence: fresh baseline/update/rollback templates, control-plane comparisons, image provenance/build descriptor, change-set review, six-request ledger, permitted screenshots/answer records, source hash verification and safe telemetry summaries.

Do not commit login material, tokens, `.env`, raw credential-bearing headers, signed URLs or unrelated chat traces. Commit only concise evidence summaries and stable non-secret identifiers needed to reproduce the engineering explanation. Remove scratch extraction directories when no longer needed; retain the selected rollback/image/request evidence for this demo phase. Do not delete previous PRD-phase evidence.

## 8. Failure handling and stop conditions

- Expired login or unhealthy Docker: stop the dependent action; complete safe planning/inspection and report the concrete blocker.
- Unrecognized account, changing stack/Runtime, different active generation or unrelated source changes: stop before publishing/updating until the baseline is reconciled.
- Invalid prompt metadata: preserve it and stop. No prompt write/sync is included.
- Unsafe image contents, wrong architecture, reused tag, changed digest or unavailable rollback image: do not execute the update.
- Extra template/change-set modifications or resource replacement: stop before execution and identify the exact differing properties.
- Live timeout/error/incorrect quote/wrong source/unexpected route: preserve the failed attempt, stop new paid requests and inspect existing logs first. No automatic retry or silent switch to a different answer source.
- Provider retry or expanded workflow: stop subsequent requests; record configured/observed limits and scope. Do not present logical counts as a hard cost cap.
- Six attempts exhausted: stop even if a criterion remains unmet. State the validation gap and ask for a separately scoped allowance if needed.
- Inconclusive telemetry: mark the relevant observation unmeasured. Do not call it absent solely because one query returned no rows; do not call it present from old traces.

## 9. Risks and practical limits

New Runtime sessions are necessary to establish the deployed version. The UI's latest answer cannot prove what an old long-lived session would run. Model choice/semantic retrieval can still fail despite passing offline tests, and the keyword intent resolver remains a heuristic. This run verifies these six controlled scenarios and does not establish universal retrieval accuracy or production suitability.

Runtime updates can temporarily disrupt the demo and produce a new version. Image publication and incurred charges are difficult to reverse. ECR's existing last-ten-images lifecycle rule can affect retained images; verify rollback retention before/after publication rather than assuming it is permanent.

The source viewer exposes complete fictional documents to a local Chainlit session. Keep the demo on loopback and preserve existing private-bucket/access settings. Public hosting or real private customer files would require separate work.

## 10. Rollback procedure

Full PRD sign-off authorizes one matching image-only rollback if this deployment fails or introduces a regression. It does not authorize broad service resets or corpus rollback.

1. Stop new live requests. If CloudFormation is still updating/rolling back, inspect its events and let the transition settle; do not race it with another update. An UPDATE_ROLLBACK_FAILED state requires a separate reviewed recovery decision, not automatic resource skipping.
2. Confirm the freshly recorded baseline image tag still resolves to its captured digest. If missing, stop rather than guessing an older image.
3. Obtain the current stack template and prepare a rollback template that changes only Runtime ContainerUri back to the fresh baseline image. Keep all current environment/IAM/resources untouched. Compare it with the fresh baseline as an additional consistency check.
4. Create and inspect a new UPDATE change set with the same existing role/parameter/capability rules. Require one Runtime Modify, Replacement=False, AgentRuntimeArtifact only. If different, stop before execution.
5. Execute the reviewed rollback. Verify stack UPDATE_COMPLETE, READY Runtime/DEFAULT mapping and the exact baseline image/digest. The rollback creates a new version; do not expect the numeric Runtime version to return to 11.
6. Verify active corpus pointer and source configuration remain unchanged. No ingestion/vector/prompt changes occurred, so none require rollback.
7. A post-rollback user prompt would consume a remaining slot from the same six-attempt allowance. If no slot remains, use control-plane readiness evidence and explicitly report that rollback response behavior was not live-validated.
8. Keep the new release image/evidence; do not delete it automatically. Report the rollback reason and unreversed costs/storage honestly.

## 11. Open items before execution

| Item | Resolution |
| --- | --- |
| Owner sign-off | Resolved: explicit **proceed** approved section 3 and six Runtime attempts. |
| AWS session | Resolved: fresh STS identity matched the intended account and IAM user `kangzhen`. |
| Docker engine | Resolved: one separately approved supported Desktop restart restored the Linux engine. No reset/deletion was performed. |
| Fresh AWS baseline | Resolved: READY Runtime/DEFAULT version 11, current complete template and corpus pointer captured before deployment. |
| Local UI | Resolved: positively identified existing port-8010 AWS-mode project UI was reused. Port 8000 was preserved. |
| Monetary ceiling | Six attempts were used; no extra Runtime calls. Dollar spend is unmeasured, and this allowance was not a monetary guarantee. |

## 12. References and execution record

- [Completed query-scoping PRD](HANDOFF_PRD_RAG_QUERY_SCOPE.md): resolver implementation, exact-source offline/CI evidence and rollout boundary.
- [Clickable-source PRD](HANDOFF_PRD_CLICKABLE_RAG_SOURCES.md): recorded Runtime 11 image, browser/file-hash checks and historical rollback context.
- [Document RAG engineering guide](DOCUMENT_RAG.md): controlled corpus, scoped retrieval, source viewer and existing infrastructure design.
- [AWS CloudFormation create-change-set reference](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-change-set.html): review before execution, UPDATE mode, existing parameter values, capabilities and inline template size limit. Inspected 2026-10-09.
- [AWS get-agent-runtime-endpoint reference](https://docs.aws.amazon.com/cli/latest/reference/bedrock-agentcore-control/get-agent-runtime-endpoint.html): endpoint read/status/version inspection. Inspected 2026-10-09.

### Execution approval and readiness

The owner approved the full scoped execution with explicit **proceed** on 2026-10-09. Fresh AWS STS inspection matched account `447393541969` and `arn:aws:iam::447393541969:user/kangzhen`, using `default` in `us-east-2`.

### Docker recovery approval

The normal start command reported already running while Desktop status remained stopped. The owner separately approved **Proceed with one Docker Desktop restart** on 2026-10-09. `docker desktop restart --timeout 50` completed successfully. Subsequent Desktop status was running, and `docker info` returned a valid Linux Docker Server 29.8.0 response. The engine had two CPUs and approximately 2 GiB RAM. No reset, WSL shutdown, image/file deletion or unrelated application termination was performed.

### Image provenance and publication

| Item | Inspected result |
| --- | --- |
| Application source | `ef146a295fe8edd0c5a9fa50ff5c9eccf70de35e` |
| Unique release tag | `query-scope-ef146a2-20261009031110-arm64` |
| ECR repository | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent` |
| Published image digest | `sha256:e4afa3b679bc2c69ea8ca70a00e77115ed7d0a4b4f54ad7827bcd6c4ae694428` |
| ARM64 descriptor digest | `sha256:7570602e7a514953e138b3ada10e5b87d98dbe1384c8559275a7c65e058c8cfc` |
| Prompt-manifest SHA-256 | `0d1b1e71dd2195a9aa3fcfcd7ac690b0ade28f4cfb1b6be12eae8788f03f6e6a` |
| Retrieval module SHA-256 | `23377a5bc7ccf192dad05ec77958b7dc1a18a290c870e824692950ab256b5ab6` |
| Source inventory | 95 tracked API files verified byte-for-byte against selected Git blobs; only extra file was `.generated/prompt-manifest.json` |
| Prompt checks | Eight immutable managed prompt entries validated offline in staging and during Docker build; no prompt synchronization |
| Container audit | `aarch64`, UID 1000, matching source/manifest hashes, no `.env`, generated directory contained only the manifest |

Windows Git archive initially applied CRLF conversion. Staging was regenerated with `git -c core.autocrlf=false archive` and verified against Git blob bytes before building. This changed only ignored staging, not application source. Docker build and push exit codes were zero. The container audit used `--network none` and did not start the application or invoke a model.

The Windows Docker credential helper failed. Publication used a narrowly scoped private temporary Docker configuration with only the ECR registry auth entry, the current-user ACL, direct password-stdin and the existing Linux engine. The directory was removed in `finally`, verified by `docker-login-cleanup.json`; the global Docker configuration was unchanged. No login material is included in this document or Git.

### Reviewed deployment and final control-plane state

Fresh baseline was Runtime **11**, READY, with DEFAULT READY on version 11 and image `citations-00a846a-20261008052831-arm64`, digest `sha256:7704ff7ce9e906e6508d2128a16b5479b6fb27608e0d05b38bf143c444700761`. Its complete original template was captured as the new rollback snapshot.

The AgentCore-only CDK synthesis used the explicit image and no lookups. The executed template was copied from the fresh deployed original, with exactly one changed leaf:

```text
/Resources/restaurantFinderAgentCoreRuntime/Properties/AgentRuntimeArtifact/ContainerConfiguration/ContainerUri
```

The 33,188-byte inline template preserved the other resources, environment, role, parameters, outputs and metadata. Actual change set:

```text
arn:aws:cloudformation:us-east-2:447393541969:changeSet/query-scope-query-scope-ef146a2-20261009031110-arm64/e94429a4-5592-4679-881a-c3803a15fe9d
```

Its inspected status was CREATE_COMPLETE/AVAILABLE and it contained exactly one existing Runtime Modify, Replacement=False, with `AgentRuntimeArtifact` as the only changed property. Execution began at **2026-10-09 03:22:49 UTC**. Stack reached UPDATE_COMPLETE; Runtime and DEFAULT reached **READY on version 12** with the exact published image.

Final reads/comparisons at **2026-10-09 05:40 UTC** confirmed READY/12, UPDATE_COMPLETE, unchanged environment/role and stack output identifiers, and deployed template equal to the reviewed update. Active-pointer content and ETag remained unchanged; the active generation is still `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a` with six sources and fourteen chunks. No corpus publication or vector write occurred.

Both release and rollback digests remained available. The previous active image ranked fourth by ECR push time, within the existing last-ten-images policy at inspection. This is current retention evidence, not a permanent guarantee. No rollback was required or performed.

### Six-attempt live ledger and inspected behavior

All six requests used the real port-8010 UI sequentially. F1/F2 used the same new Runtime conversation, and F3-F6 used distinct new conversations. Each slot was reserved before submission; there were exactly six UI sends, six corresponding invocation traces, and no diagnostic replacement, hidden resubmission, warm-up or benchmark. The allowance is exhausted.

| Case | Router start, UTC | Inspected functional result | Outcome |
| --- | --- | --- | --- |
| F1 | 03:28:51 | `Mushroom pasta - RM32 per serving`, Harbor menu v2, PDF page 1, pinned generation. The missing terminal period remained a valid contiguous source quote. | PASS |
| F2 | 05:23:54 | Same Runtime conversation as F1; one rewrite; `Cancellations less than 24 hours before the booking incur a RM20 fee per booking.`, Harbor policy v1, lines 5-8. | PASS behavior; timing deviation |
| F3 | 05:27:06 | Full-name policy question returned the same conditional RM20 rule, with only a policy citation. No menu/price answer. | PASS |
| F4 | 05:28:16 | Both exact facts; separate Harbor menu-v2 PDF and policy-v1 Markdown citations. Both controls opened their intended originals. | PASS |
| F5 | 05:33:38 | `The active documents do not contain enough evidence to answer that question.` No invented Wi-Fi password, quotation or citation. | PASS |
| F6 | 05:34:15 | Asked which fictional restaurant to use, listing Harbor, Sakura and Spice Garden. No citation, embedding, vector query or selector. | PASS |

**Timing deviation:** Step 8 requested F2 immediately after F1. The native browser download operation stalled for approximately 111 minutes before returning; F2's router started 6,903 seconds after F1's router. No Runtime calls occurred during the delay. The same Runtime conversation ID and successful approved Harbor follow-up were verified, but an immediate follow-up was not demonstrated in this run. R6 therefore retains a timing-only failure. No seventh request was sent to conceal or repair that gap.

### Original-source inspection

The F1 menu and F2 policy were opened through their actual citation controls. After F2, the earlier F1 menu control was reopened and still selected only that menu. F4's two named controls were independently clicked and inspected: PDF page 1 contained RM32; the complete eleven-line Markdown policy contained the less-than-24-hours RM20 rule at lines 5-8.

| Original | Version | Download size | SHA-256, matched to fresh pinned manifest |
| --- | --- | --- | --- |
| `harbor-menu` PDF | v2 | 1,975 bytes | `501c1300d00c571e8f94920a6ab25bd0a4ae54976e79ed047bce8e9dc8f6bb10` |
| `harbor-policy` Markdown | v1 | 534 bytes | `d3d4b1ca9ca945c0f0db133c50bf02ae8c75c8736b32232a902634a8faa79471` |

The independently downloaded F4 copies matched the same manifest hashes. Remaining transfers used the observed Chainlit session-file URLs with bounded HTTP downloads after the native download delay. These were original-file reads, not agent invocations; no public/presigned S3 link or surrogate document was created.

Chainlit's automatic panel initially combined visible source elements on F2/F4, consistent with the already documented UI behavior. Closing it and explicitly clicking each named source selected the correct individual file. The inspected named citation controls passed source association; this run does not claim that the automatic panel always shows only one element.

### Request-correlated telemetry and limits

Fresh paginated `aws/spans` reads covered F1 at 03:28-03:33 UTC and F2-F6 at 05:23-05:35 UTC. Six unique `router.classify` traces were matched by start time, Runtime session, parent spans and invocation completion; F1/F2 shared the Runtime session. The safe correlated summaries retain trace IDs privately.

Every router reported `document_qa`, provider **Jev**, model `jev-1.13.0`. No Bedrock routing fallback, restaurant-search or browser-tool path was observed. F1-F5 each had one scope, retrieval, query embedding, vector query, selector and validation stage. F2 also had one Haiku rewrite under `rag.scope`. F6 had scope/clarification without retrieval or model selection; its manifest/index metadata reads were not vector queries. Normal guardrails, checkpointing and approved-answer memory storage remained present.

| Measured observation | Total |
| --- | --- |
| Runtime invocations / Jev classifications | 6 / 6 |
| Query embedding attempts / vector queries | 5 / 5 |
| Haiku answer selections / follow-up rewrites | 5 / 1 |
| Query embedding input tokens | 84 |
| Haiku input / output tokens for selection and rewrite | 6,865 / 642 |
| Retry attempts reported by inspected instrumented AWS client spans | 0 |

LangChain and botocore both emit model spans. Counts above use the nested HTTP/model-usage records and parent relationships, so wrapper spans are not counted as extra logical calls. No ERROR status or HTTP status >=400 occurred in the inspected request traces. Token totals exclude Jev and do not establish a dollar cost.

The offline container audit found Haiku's configured retry mode `legacy` without an explicitly configured maximum, and the factory's default output cap unset. Selector/rewrite calls set their existing 1,600/400 output-token bounds. Reported AWS SDK retry counters were zero for the observed calls; internal Jev/provider/network retries beyond the instrumented fields remain unmeasured. The exact live document-type vector filter is not exposed by existing spans. Deployed source provenance and prior deterministic regressions cover filter construction; delivered citations and traces cover these live outcomes.

Application error/warning reads found **fourteen LoggingHandler deprecation warnings** and **six uncorrelated `Invalid HTTP request received` warnings**. Their cause was not established. They did not appear as failures in the six correlated request traces. No tracing configuration or application fix was applied under this image-only scope; these observations remain separate follow-up items.

### R1-R9 acceptance record

| Criterion | Status | Evidence / gap |
| --- | --- | --- |
| R1 | PASS | Fresh intended identity; stable READY/11 baseline; complete current rollback template and image digest captured. |
| R2 | PASS | 95 source blobs, only required manifest extra, eight prompt validations, matching container file hashes. |
| R3 | PASS | ARM64 build/container descriptor; published digest read from ECR; previous active digest still available. |
| R4 | PASS | One canonical template leaf; one actual Runtime Modify, no replacement, artifact property only. |
| R5 | PASS | Final UPDATE_COMPLETE and READY/12 DEFAULT; exact image; environment/role/outputs/pointer preserved. |
| R6 | FAIL — timing only | All six functional expectations passed within six attempts; immediate F2 timing was missed due to the browser download delay. |
| R7 | PASS | Explicit individual and earlier-answer source clicks; PDF/Markdown original bytes matched fresh manifest hashes, including F4 copies. |
| R8 | PASS with unmeasured fields | Six fresh correlated traces, Jev routing, expected stages/counters. Exact type filters, hidden retries and dollar spend remain unmeasured; application warnings recorded separately. |
| R9 | PASS | Deployment/ledger/source/telemetry record published to the feature branch; four successful CI jobs and actual artifact counts inspected for documentation commit `539453fa29f08cabdcc36d7ac5982ab5a0ee029f`. Final receipt-only documentation commit is checked separately against its own resulting SHA. |

### Documentation publication and offline CI receipt

The rollout record and engineering guide were committed/pushed only to `origin/feat/jev-router` as `539453fa29f08cabdcc36d7ac5982ab5a0ee029f`. [Offline quality checks, 37889994286](https://github.com/yukangzhen/restaurant-finder/actions/runs/37889994286) completed successfully for that exact SHA. API and document RAG, UI, Infrastructure, and Quality checks all passed.

Downloaded artifact contents, rather than badges alone, confirmed **135 API tests**, **26 UI tests**, **3 infrastructure tests**, and **17/17 offline RAG cases with 374 measured checks and zero unmeasured checks**. API/UI logs reported `OK`; infrastructure reported all tests passed; the complete RAG JSON reported every case passed in `offline_regression` mode. These are new inspected CI results, separate from the historical source-SHA CI and the six live Runtime scenarios. They do not measure live ranking quality or model performance.

The remote SHA matched, and the worktree was clean before recording this receipt. This receipt changes only documentation; its resulting final commit/automatically triggered CI is inspected separately and retained as `final-publication-ci-verification.json` in the ignored evidence directory, with the final CI link reported to the owner. The deployed image remains built from application source `ef146a295fe8edd0c5a9fa50ff5c9eccf70de35e`.

### Preserved evidence and process state

Private evidence lives under `restaurant-finder-api/.generated/rollout-query-scope-20261009/`. Retain baseline/update/fresh rollback templates, image/source/prompt/build/push records, actual change-set and final control-plane records, six-slot ledger, source-download verification, answer/source screenshots, safe telemetry summary, final-verification JSON and publication/CI receipts. The transient source archive and build staging were removed after checking their resolved paths stayed within this directory and contained no reparse points. Earlier phase evidence and user files were preserved.

The existing loopback port-8010 project UI was reused and remains running with source viewing enabled and the correct AWS Runtime configuration. It was not restarted. The separate port-8000 application remains running. Runtime 12 is retained and the approved rollback was unused. No application/UI source, dependencies, credentials, IAM, prompts, corpus, tracing destinations or workflow settings were changed. Documentation publication targets only `feat/jev-router`; no main push/merge, PR, deployment/destruction workflow dispatch or LinkedIn publication is included.
