# Handoff PRD: Reliable Memory Questions, Guardrail Messages, and AWS Tracing

Prepared October 7, 2026, Asia/Kuala_Lumpur.

## 1. Intended outcome and execution status

Deliver a verified development version of Restaurant Finder that:

1. Answers dining-memory questions by retrieving the current user's stored memories.
2. Shows a readable explanation when the API blocks a request.
3. Delivers request spans to CloudWatch alongside the already working logs and metrics.
4. Preserves Jev as the primary router and Claude Haiku 4.5 as its fallback.

This is for the project owner and the next implementation agent. The owner is learning software development; explain results with concrete examples and distinguish passing checks from remaining limitations.

**Status: proposed, awaiting explicit implementation approval.** The request to create this PRD authorizes this document and read-only investigation. It does not authorize implementing this new scope, enabling Transaction Search, publishing the document, or running new paid checks. After the owner explicitly approves this PRD, proceed through its authorized steps without repeatedly requesting the same permission. Ask again only for a material expansion, unexpected replacement/deletion, new account/region, or a rollback that affects other regional tracing users.

The completion criteria in section 4 are the definition of done. Do not mark the work complete using narrower criteria.

## 2. Verified starting point

### Repository and local environment

| Item | Baseline |
| --- | --- |
| Repository | `https://github.com/yukangzhen/restaurant-finder` |
| Upstream | `https://github.com/JoudAwad97/agentic-ai-langgraph-and-aws-agentcore` |
| Local repository | `C:\Users\kinoc\Documents\Codex\2026-09-28\i-x20\work\agentic-ai-langgraph-and-aws-agentcore` |
| Branch | `feat/jev-router` |
| Baseline commit | `b2802edac52ba15d91a87eedee905b059eaf3a75` |
| Git state at inspection | Clean, except this newly created handoff document |
| Shell | PowerShell on Windows |
| API interpreter | `restaurant-finder-api\.venv\Scripts\python.exe` |
| UI interpreter | `restaurant-finder-ui\.venv\Scripts\python.exe` |
| Current UI | Last verified running at `http://localhost:8000`; recheck before restarting |

The baseline commit is already pushed. The baseline contains the AWS integration repair, immutable prompt manifest, memory fixes, ARM64 image setup, and existing tests. Reuse those pieces; do not redo the previous repair.

### AWS resources

| Item | Value |
| --- | --- |
| CLI profile | `default` |
| Region | `us-east-2` |
| Account | `447393541969` |
| Last verified caller | `arn:aws:iam::447393541969:user/kangzhen` |
| AgentCore stack | `restaurantFinder-AgentCoreStack` |
| ECR stack | `restaurantFinder-EcrStack` |
| Runtime ID | `restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu` |
| Runtime role | `arn:aws:iam::447393541969:role/restaurantFinder-AgentCor-restaurantFinderAgentCore-kO1s3now5CRm` |
| Runtime network | `PUBLIC` |
| Memory ID | `restaurantFinder_Memory-n0qbbA8z4Y` |
| ECR repository | `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent` |
| Deployed tag | `jev-router-20261007-112930-arm64` |
| Deployed digest recorded during prior deployment | `sha256:a3c50c5bb0fd77170f9011f0dcb801b21b264e2fca469a68abc69a95a573e99e` |
| Telemetry log group | `/aws/vendedlogs/bedrock-agentcore/restaurantFinder-telemetry` |
| Telemetry stream | `agentcore` |
| Runtime log group | `/aws/bedrock-agentcore/runtimes/restaurantFinder_Agent-Ha58oX5Psu-DEFAULT` |
| Trace destination | `XRay`, status `ACTIVE` |
| Default trace indexing | `DesiredSamplingPercentage: 0.0` |
| `aws/spans` log group | Not present at the latest inspection |
| Existing X-Ray logs policy, inspected earlier this session | `restaurantFinder-XRayCloudWatchLogsAccess`; permits X-Ray writes to `aws/spans`; re-read before deciding whether additional policy is needed |

The Runtime was rechecked while drafting this PRD: `READY` on the deployed tag above. Revalidate all live values before making writes; a historical snapshot is not deployment authority.

### Existing behavior proven in the preceding verification

- All 11 existing API unit tests passed.
- Real local Jev calls correctly classified a greeting, a restaurant search, and an unrelated request.
- A locally simulated Jev timeout caused a real successful Claude Haiku 4.5 fallback.
- The deployed Runtime stored and extracted vegan, Thai cuisine, and under-$25 preferences for a synthetic actor.
- A restaurant recommendation request in a different session recalled all three preferences without receiving them again in its input.
- The persistent UI AWS configuration produced a successful browser response.
- CloudWatch received memory operation logs, save/retrieve counters, and duration histograms. OTLP metrics were verified through signed PromQL queries, not classic `ListMetrics`.
- Runtime trace export logs contain `Failed to export span batch code: 400, reason: Bad Request`.

These checks are smoke checks, not a performance benchmark or proof of production readiness. The prior verification scripts were temporary and have been removed. Create new focused regression tests in the repository and temporary live-check scripts as described below.

## 3. Problems and required behavior

### A. Memory questions can take a route with no memory access

Observed request:

> Which cuisine, dietary restriction, and meal budget do you remember for my restaurant recommendations?

Observed result: `simple` intent, followed by a response saying there was no previous history, although three preference records existed for that actor.

Why this happens:

```text
simple -> simple_response_node -> response model without tools
restaurant_search -> search_agent_node -> memory_retrieval_tool is available
```

Jev currently defines `restaurant_search` mainly as asking for actual restaurant results or details. Memory-only questions can fall outside that definition. The Bedrock router prompt also has different rules from Jev, including an overly broad rule that any mention of food means search. The search prompt prioritizes restaurant search and requires a location without explicitly exempting memory-only requests.

Required behavior: dining-memory requests use the existing tool-capable route. The agent retrieves preferences/facts as appropriate, answers from returned records, and does not ask for a location or initiate web search when the user only wants remembered preferences.

### B. The UI discards guardrail-block messages

The API already returns an SSE event with this shape:

```json
{"blocked": true, "message": "I'm sorry, but I can't process that request..."}
```

The UI handles `chunk` and `error`, but ignores `blocked`. It then replaces the empty response with `No response received.` An instruction-style memory check was actually blocked by the prompt-attack guardrail, exposing this behavior.

Required behavior: show the server's readable block message, use a safe fallback if the message is absent/blank/not a string, and preserve that message after the subsequent `done` event. Keep guardrail enforcement intact.

### C. The regional trace prerequisite is missing

The Runtime uses the X-Ray OTLP trace endpoint. AWS documents Transaction Search as a prerequisite for sending spans to that endpoint. This region is currently configured for `XRay`, not `CloudWatchLogs`, and trace batches are rejected.

Required behavior: after explicit approval, enable the documented CloudWatch Logs trace destination in this account and region, then verify actual request spans. This affects regional account tracing beyond this single application. Logs and metrics already work and should continue to work.

## 4. Acceptance criteria

| ID | Observable result |
| --- | --- |
| R1 | Each dining-memory input in the required live routing subset is classified `restaurant_search` by real Jev. |
| R2 | The corresponding real Bedrock fallback subset selects the same route when Jev failure is simulated only in a local test process. |
| R3 | Ordinary greetings, thanks, and capability questions remain `simple`; unrelated coding/weather requests remain `off_topic`. |
| M1 | Actor A's preferences are saved, extraction completes, and a new session for actor A retrieves and reports vegan, Thai, and under-$25 without those values being provided in the recall question. |
| M2 | The previously failing memory-only wording succeeds; evidence shows a memory tool call and returned records, not just a plausible answer. |
| M3 | A different synthetic actor cannot retrieve actor A's records. A retrieval error is distinguishable from an empty result. |
| U1 | Both direct and nested blocked SSE fixtures show the server message and retain it after `done`; missing/blank/non-string messages show the defined fallback. |
| U2 | Normal token streaming, error display, and the empty-response fallback still work. |
| T1 | Destination reports `CloudWatchLogs` and `ACTIVE`; the existing 0% indexing setting is preserved unless the owner separately approves a change. |
| T2 | Fresh `workflow.execution`, `router.classify`, and `router.jev` spans arrive in `aws/spans` for an identified synthetic request. Router span attributes identify provider and intent. |
| T3 | No fresh trace HTTP 400/403 errors occur for the validated request window. Logs and the three memory metrics still arrive. |
| V1 | Existing tests and new focused regressions pass; the packaged prompt manifest matches the new prompt text; the new image is ARM64. |
| D1 | Runtime is `READY` on the new versioned image; AgentCore stack is stable; ECR stack and repository resources were not redeployed as a dependency. |
| H1 | Code, tests, updated documentation, and evidence summary are committed/pushed to the feature branch after approval; the final report states every remaining gap. |

If a live routing example fails, refine the approved prompt definitions and rerun the failed case plus affected controls. Do not add hard-coded keyword routing to conceal model failures. Do not claim broad accuracy or lower cost from this limited test set.

## 5. Scope, constraints, and approval boundaries

### Expected file changes

| File | Required work |
| --- | --- |
| `restaurant-finder-api/src/infrastructure/jev_router.py` | Extend intent instructions/criteria for dining memory; preserve the SDK client, model, timeout, and validation. |
| `restaurant-finder-api/src/domain/prompts.py` | Align `ROUTER_PROMPT`; explicitly handle memory recall in `SEARCH_AGENT_PROMPT`. |
| `restaurant-finder-api/src/application/orchestrator/workflow/nodes.py` | Add sanitized provider/intent evidence to the router span and completion log. |
| `restaurant-finder-ui/app.py` | Handle blocked events in `_invoke_agent`. |
| `restaurant-finder-api/tests/test_router.py` | New focused router/fallback regressions using controlled provider outputs. |
| `restaurant-finder-ui/tests/test_sse_responses.py` | New UI SSE behavior regressions with fake async streams/messages. |
| `README.md` | Update startup, verification status, and regional tracing setup/rollback notes based on actual results. |

Use the existing three intents and existing graph. `state.py`, `edges.py`, and `graph.py` should not need changes. `restaurant_search` is an internal name for the tool-capable route; document that it also handles dining memory.

Expected AWS writes after approval: deployment-time immutable prompt synchronization, one new versioned ECR image, AgentCore Runtime image deployment through its stack, the regional trace destination change, conditional creation of `aws/spans` with 30-day retention if absent, and a conditional dedicated X-Ray ingestion resource policy if the existing policies are insufficient. Synthetic live requests create isolated test memory and incur service usage.

Preserve the current 0% trace indexing. It is separate from SDK span sampling: 0% indexing does not make span ingestion free and does not prevent stored spans from being inspected through CloudWatch Logs. Do not change the application's sampling rate or promise a specific bill.

Do not merge to `main`, dispatch deployment workflows, overwrite `latest`, delete images/prompts/memory/logs, broaden runtime IAM, change guardrail strength, expose API keys, recreate the stacks, or modify unrelated regional observability services. Do not clean up the earlier stray CDK bootstrap S3 asset; it has separate history/authorization. Do not use `cdk diff` as a supposedly mutation-free check: it previously published an asset while preparing a change set.

The ignored UI `.env` now uses AWS mode, profile `default`, and a stable local actor. Preserve its keys and user settings. Client-controlled actor IDs are acceptable only for this local single-user development setup; production authentication is outside scope.

## 6. Execution runbook

All commands below use PowerShell unless labeled Python. Resolve placeholders from verified outputs. **After every native command, check `$LASTEXITCODE`; stop on nonzero.** `$ErrorActionPreference = 'Stop'` alone does not reliably stop failed native commands. Do not proceed through a failed build, test, push, or deployment.

### Step 0 — Establish approval and explain the deliverable

1. Read this PRD and applicable AGENTS.md instructions.
2. Locate the owner's explicit approval of this PRD. Approval of document creation is insufficient.
3. State the outcome, boundaries, and definition of done to the owner.
4. If approval is absent, inspect safely and prepare any needed clarification; make no implementation or cloud writes.
5. Once approved, continue autonomously within the scope in section 5. Provide concise updates at least every 60 seconds during active work.

Exit condition: implementation, AWS writes, small live checks, and feature-branch publication are explicitly authorized.

### Step 1 — Revalidate the baseline and capture rollback evidence

```powershell
$ErrorActionPreference = 'Stop'
$repoRoot = 'C:\Users\kinoc\Documents\Codex\2026-09-28\i-x20\work\agentic-ai-langgraph-and-aws-agentcore'
$env:AWS_PROFILE = 'default'
$env:AWS_REGION = 'us-east-2'
$runtimeId = 'restaurantFinder_Agent-Ha58oX5Psu'
$runtimeArn = 'arn:aws:bedrock-agentcore:us-east-2:447393541969:runtime/restaurantFinder_Agent-Ha58oX5Psu'
$stackName = 'restaurantFinder-AgentCoreStack'
$memoryId = 'restaurantFinder_Memory-n0qbbA8z4Y'
$ecrUri = '447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent'
Set-Location -LiteralPath $repoRoot
git status --short
git branch --show-current
git rev-parse HEAD
git remote -v
aws sts get-caller-identity --profile default --region us-east-2
```

Confirm the account before any write. If login is expired, the owner can restore it with `aws login --profile default`; never request pasted credentials. Do not reset a dirty checkout. This handoff document may be uncommitted and should be retained; identify other changes before editing.

Create a unique ignored evidence directory under repository `tmp/`, not a tracked credentials file:

```powershell
$runName = 'handoff-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$evidenceDir = Join-Path $repoRoot ('tmp\' + $runName)
New-Item -ItemType Directory -Path $evidenceDir | Out-Null
git check-ignore (Join-Path $evidenceDir 'runtime-before.json')
```

Read and save the current Runtime configuration, both stack statuses, deployed AgentCore template, ECR tag/digest, regional trace destination/indexing, existing log groups/retention, and resource policies. Store full snapshots only in the ignored evidence directory; do not dump potential environment secrets into the conversation.

```powershell
aws bedrock-agentcore-control get-agent-runtime --profile default --region us-east-2 --agent-runtime-id $runtimeId --output json | Set-Content -LiteralPath (Join-Path $evidenceDir 'runtime-before.json') -Encoding utf8
aws cloudformation get-template --profile default --region us-east-2 --stack-name $stackName --output json | Set-Content -LiteralPath (Join-Path $evidenceDir 'template-before.json') -Encoding utf8
aws cloudformation describe-stacks --profile default --region us-east-2 --stack-name $stackName --query 'Stacks[0].StackStatus'
aws cloudformation describe-stacks --profile default --region us-east-2 --stack-name restaurantFinder-EcrStack --query 'Stacks[0].StackStatus'
aws xray get-trace-segment-destination --profile default --region us-east-2 --output json | Set-Content -LiteralPath (Join-Path $evidenceDir 'destination-before.json') -Encoding utf8
aws xray get-indexing-rules --profile default --region us-east-2 --output json | Set-Content -LiteralPath (Join-Path $evidenceDir 'indexing-before.json') -Encoding utf8
aws logs describe-resource-policies --profile default --region us-east-2 --output json | Set-Content -LiteralPath (Join-Path $evidenceDir 'policies-before.json') -Encoding utf8
aws logs describe-log-groups --profile default --region us-east-2 --log-group-name-prefix aws/spans --output json | Set-Content -LiteralPath (Join-Path $evidenceDir 'span-groups-before.json') -Encoding utf8
```

Parse the Runtime snapshot and record its actual image URI as `$previousImageUri`. Derive its tag and call ECR `describe-images` to confirm the rollback image exists. Do not assume `latest` is the deployed image. Record the current deployed template and environment before changes.

Exit condition: correct account/region/branch; stable deployment; rollback image verified; snapshots captured; unrelated local changes identified.

### Step 2 — Read the affected flow before editing

Read the files in the change table, plus:

- API `workflow/chains.py`, `workflow/edges.py`, `workflow/graph.py`, and `workflow/state.py`.
- API `workflow/tools.py` and `infrastructure/memory.py` for memory invocation and errors.
- API `infrastructure/streaming.py` for the actual SSE contract.
- API `infrastructure/observability.py` for context-manager and span behavior.
- API `src/deployment/sync_prompts.py`, `validate_prompts.py`, and `infrastructure/prompt_metadata.py`.
- Infra `bin/cdk.ts`, `lib/stacks/agentcore-stack.ts`, and `cdk.json`.
- UI `app.py`, `.env.example`, and `pyproject.toml`; inspect actual `.env` without printing secrets.

Note that `bin/cdk.ts` declares an explicit dependency on EcrStack. An ordinary single-stack deployment can still include it. Use `--exclusively` for this change.

Exit condition: executor can explain why each proposed edit is necessary and how the two router providers share semantics.

### Step 3 — Extend Jev's dining-memory classification

In `jev_router.py`, revise the `Choice` instructions and criteria:

1. Continue classifying the latest user message; use earlier messages only to resolve references.
2. Route requests to recall the user's dietary needs, cuisine preferences, meal budget, previous recommendations, or past dining facts to `restaurant_search`, even without a location or a request for new restaurant results.
3. Treat "What do you remember about my food preferences?" and "What preferences have I told you before?" as memory requests within this restaurant assistant's scope.
4. Keep greetings, thanks, acknowledgments, goodbyes, and capability questions as `simple`, even when they mention restaurants.
5. Keep unrelated requests as `off_topic`.
6. For a bare ambiguous "What do you remember?", use prior dining context if present; without context, do not invent facts. The tool-capable path may inspect dining memory or ask a narrow clarifying question.

Preserve `_VALID_INTENTS`, `jev-1.13.0`, SDK version, client lifecycle, timeout, no-retry policy, secret loading, and output validation. Do not add a new intent or switch models.

### Step 4 — Align Bedrock fallback and search-agent behavior

In `domain/prompts.py`:

1. Add the same dining-memory examples to `__ROUTER_PROMPT`.
2. Replace the blanket "food mentioned in ANY way -> search" rule with the same precedence as Jev: genuine memory/result/detail requests use tools; greetings/capabilities remain simple.
3. Keep the output contract exactly one of the three intent names.
4. In `__SEARCH_AGENT_PROMPT`, distinguish actual restaurant searches from memory-only requests.
5. For memory-only requests, call `memory_retrieval_tool` before claiming remembered preferences. Use `preferences` for dietary/cuisine/budget recall; add `facts` when past dining facts are relevant. Request summaries only for the current session when appropriate.
6. Answer from returned records. If retrieval reports errors, explain that stored preferences could not be accessed; if successful retrieval is empty, say there are no saved relevant preferences yet. Do not fabricate history.
7. Exempt memory-only requests from the location requirement and restaurant-results output template.
8. Do not call SearchAPI or browser tools solely to recall preferences. Keep existing search-tool priority for actual restaurant result requests.

Retain `Prompt(...)` declarations and variable names. Changing text invalidates the existing manifest's hashes. Before local checks, point `PROMPT_MANIFEST_PATH` to a deliberately nonexistent path under the ignored evidence directory and set `REQUIRE_PROMPT_MANIFEST=false` for that local process. This uses local prompt text without AWS writes. Do not delete or manually edit the old manifest to bypass validation. Later regenerate a valid manifest before packaging.

### Step 5 — Add reliable router provider evidence

In `nodes.py`:

1. Bind the outer `router.classify` context manager's yielded span, e.g. `as router_span`.
2. After classification finishes, while that span is still active, set sanitized attributes: `router.intent`, `router.provider`, and `router.model`.
3. Add numeric confidence only when present/valid; add `router.fallback.reason` only for fallback, using the exception class name.
4. Handle disabled observability (`router_span is None`) safely.
5. Include intent, provider, model, and optional fallback exception class in the normal completion log. Preserve existing workflow-step events.
6. Do not log user input, actor identifiers, keys, full provider exception messages, or raw classifier content. Replace the existing unclear-fallback warning's raw response text with a sanitized message if touching that branch.

Keep fallback execution local to the existing exception handler. The live fallback test must simulate Jev failure only in a local process; never break the deployed secret or alter the shared Runtime to force failure.

### Step 6 — Handle blocked SSE messages in the UI

In `_invoke_agent` in `restaurant-finder-ui/app.py`, after direct/nested SSE decoding:

1. Check `data.get('blocked') is True` before processing ordinary chunks.
2. If `message` is a nonblank string, display it as plain message content.
3. Otherwise display this fallback: `I couldn't process that request. Please try a restaurant-related question.`
4. Call `await msg.update()` and return from invocation processing so `done` cannot overwrite the message with the empty-response fallback.
5. Preserve normal streaming, errors, and connection-mode behavior. Do not import the API package into the UI to reuse a constant.

Do not weaken the guardrail or change the API protocol. Review whether returning early closes the async response iterator cleanly; use an appropriate existing cleanup path if needed, without rewriting the whole streaming transport.

### Step 7 — Add and run focused regressions

API tests: use standard-library `unittest` and existing mocks. Follow the existing supported import order: import `src.infrastructure.api` before importing the workflow nodes. Directly importing the nodes first exposed an existing circular-import issue during prior verification; a package redesign is outside this scope.

Required API coverage:

- Valid Jev result sets the correct intent/provider/span attributes and does not invoke Bedrock.
- Timeout, unavailable client, and invalid Jev output each select fallback; controlled Bedrock outputs map to the intended route.
- Disabled observability works.
- Dining-memory intent reaches the tool-capable edge.
- Sensitive sample input/exception text does not appear in newly added completion logs or attributes.

Mocked router tests prove plumbing; they do not prove model classification accuracy. Use live checks in step 8 for that.

UI tests: import the app without launching a server. Patch the selected SSE source with an async fixture stream and use a fake message with async `stream_token`/`update` methods. No AWS or Chainlit browser is required for these fixtures.

| Fixture | Required assertion |
| --- | --- |
| Direct `blocked` event followed by `done` | Server message remains displayed; no empty-response replacement |
| Nested JSON-string SSE containing `blocked` | Same result as direct event |
| Missing, blank, or non-string blocked message | Exact safe fallback displayed |
| Two normal `chunk` events and `done` | Combined content preserved |
| `error` event | Existing error display preserved |
| Malformed JSON line | Safely ignored; following valid event handled |
| Stream with no content/block/error | Existing empty-response message preserved |

Run from each project's directory:

```powershell
# API directory; use the local-only manifest override described in step 4.
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src

# UI directory.
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m py_compile app.py
```

Run `git diff --check`. If dependency metadata changed unexpectedly, investigate; this work should not require new packages or wholesale lockfile churn. Run the infra TypeScript build only if infra code is changed. Do not reinstall a missing optional linter just to expand this task.

Exit condition: all existing and new meaningful regressions pass; code imports through the supported entrypoint; diffs contain only intended edits.

### Step 8 — Verify routing with real providers before deployment

Write a temporary script under `$evidenceDir`; run it with the API interpreter from the API directory, with `AWS_PROFILE=default`, observability disabled locally, and the local-only manifest override from step 4. Initialize/close the real Jev client using the existing lifecycle functions. Capture provider metadata through an observability spy rather than exposing user data.

Required classification matrix:

| Input | Expected intent |
| --- | --- |
| `Hello!` | `simple` |
| `Thanks for finding restaurants!` | `simple` |
| `What kinds of restaurants can you help me find?` | `simple` |
| `Write a Python sorting function.` | `off_topic` |
| `What's the weather tomorrow?` | `off_topic` |
| `Find vegan Thai restaurants in Austin.` | `restaurant_search` |
| `What do you remember about my dietary restrictions?` | `restaurant_search` |
| `Which cuisine, dietary restriction, and meal budget do you remember for my restaurant recommendations?` | `restaurant_search` |
| `What preferences have I told you before?` | `restaurant_search` |
| `Remind me which restaurants you recommended earlier.` | `restaurant_search` |
| Prior dining conversation + `What do you remember?` | `restaurant_search` |

Run all 11 matrix cases with real Jev. For the contextual case, construct a previous user/assistant exchange about restaurant preferences and make `What do you remember?` the latest user message; the classifier check needs no AWS memory write. Reuse earlier results only as historical context, not as proof of the changed prompts. Run three live Bedrock fallback calls: the failing memory wording, a greeting, and the unrelated coding request. Patch `nodes.classify_with_jev` to raise `TimeoutError` in that temporary process; keep the Bedrock chain real. Add live cases only when failures or changed instructions justify them.

For each call record input case name, expected/actual intent, actual provider, model, fallback reason, and pass/fail. Fail a normal Jev check if it silently falls back. Do not benchmark or extrapolate latency/cost. Before continuing, resolve failures inside the approved scope or explicitly report the blocker.

### Step 9 — Synchronize prompts and build the ARM64 image

This step makes authorized prompt writes. Remove the local-only manifest override; require and regenerate the real manifest:

```powershell
Set-Location -LiteralPath (Join-Path $repoRoot 'restaurant-finder-api')
Remove-Item Env:PROMPT_MANIFEST_PATH -ErrorAction SilentlyContinue
Remove-Item Env:PROMPT_SYNC_MODE -ErrorAction SilentlyContinue
$env:REQUIRE_PROMPT_MANIFEST = 'true'
.\.venv\Scripts\python.exe -m src.deployment.sync_prompts --profile default --region us-east-2
.\.venv\Scripts\python.exe -m src.deployment.validate_prompts
```

The sync command sets its own sync mode in its child process and reuses matching immutable versions. Expect new versions for the changed router/search prompt definitions; other matching prompts should be reused. Inspect the generated manifest for account, region, hashes, and immutable versions. Never delete versions or edit version metadata manually.

Choose a fresh version tag that includes the source revision and a timestamp; record it before deployment:

```powershell
Set-Location -LiteralPath $repoRoot
$sourceRevision = (git rev-parse --short HEAD).Trim()
$imageTag = 'memory-ui-tracing-' + $sourceRevision + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-arm64'
$imageUri = $ecrUri + ':' + $imageTag
docker info --format '{{.ServerVersion}}'
docker build --platform linux/arm64 --tag $imageUri .\restaurant-finder-api
docker image inspect $imageUri --format '{{.Os}}/{{.Architecture}}'
docker run --rm --platform linux/arm64 --env REQUIRE_PROMPT_MANIFEST=true $imageUri python -m src.deployment.validate_prompts
```

The source revision may still be the baseline while approved edits are uncommitted; the timestamp makes the tag unique. Record the exact diff/source commit in the final evidence so the deployed contents are identifiable. Prefer a local implementation commit before building when convenient; do not push until the approved publication step.

Exit condition: successful build, `linux/arm64`, packaged validation success, recorded new tag. Do not infer architecture from the tag alone.

### Step 10 — Push the new image without changing `latest`

Try ordinary ECR login first:

```powershell
aws ecr get-login-password --profile default --region us-east-2 | docker login --username AWS --password-stdin 447393541969.dkr.ecr.us-east-2.amazonaws.com
docker push $imageUri
aws ecr describe-images --profile default --region us-east-2 --repository-name restaurantfinder-agent --image-ids imageTag=$imageTag --query 'imageDetails[0].{digest:imageDigest,tags:imageTags,size:imageSizeInBytes}' --output json
```

Do not print or save the login password. Verify ECR contains the intended new tag/digest; do not tag/push `latest`.

Known Windows blocker: the normal credential helper previously failed with `The stub received bad data`. If it recurs, use the proven isolated workaround:

1. Resolve full executable paths with `Get-Command aws.exe` and `Get-Command docker.exe`.
2. Create a uniquely named temporary directory under the system temp directory containing `config.json` with `{"auths":{},"credsStore":""}`.
3. In a `try/finally` block, save this process's PATH and remove the directory containing Docker's executables/helpers from that process's PATH. Docker otherwise auto-selects the Windows helper even with a temporary config.
4. Invoke Docker by its full path with `--config <temporary-directory> --host npipe:////./pipe/dockerDesktopLinuxEngine` for login and push. Invoke AWS by its full path and pipe its password to `--password-stdin`.
5. Restore PATH in `finally`. Verify the temporary credential directory resolves beneath the intended system temp parent, then remove only that generated directory with `Remove-Item -LiteralPath` and `-Recurse`.
6. Re-run ECR `describe-images` to prove the push. The regular Docker configuration must not be changed.

Do not treat a successful login as evidence that the push succeeded.

### Step 11 — Enable the regional trace destination after approval

Re-read the snapshots immediately before this step. If the destination is already `CloudWatchLogs/ACTIVE`, do not switch it again. If other changes occurred, reconcile them with the owner before changing account settings.

1. If `aws/spans` is absent, create it and apply 30-day retention. If present, preserve its current class/retention.
2. Check whether existing resource policies grant `xray.amazonaws.com` the required `logs:PutLogEvents` access. Preserve existing policies and statements.
3. If additional access is needed, use a dedicated policy named `restaurantFinder-TransactionSearchAccess` with the scoped document below. Do not overwrite a preexisting policy with that name without inspecting and reconciling it.
4. Change only the regional trace destination to `CloudWatchLogs`.
5. Re-read destination/status and indexing. Preserve the preflight Default rule (currently 0%). Do not enable Application Signals discovery or change sampling/indexing to make a sparse check easier.

Conditional new group commands:

```powershell
aws logs create-log-group --profile default --region us-east-2 --log-group-name aws/spans
aws logs put-retention-policy --profile default --region us-east-2 --log-group-name aws/spans --retention-in-days 30
```

Conditional policy document, saved with a structured JSON serializer to an ignored UTF-8 file:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "TransactionSearchXRayAccess",
    "Effect": "Allow",
    "Principal": {"Service": "xray.amazonaws.com"},
    "Action": "logs:PutLogEvents",
    "Resource": [
      "arn:aws:logs:us-east-2:447393541969:log-group:aws/spans:*",
      "arn:aws:logs:us-east-2:447393541969:log-group:/aws/application-signals/data:*"
    ],
    "Condition": {
      "ArnLike": {"aws:SourceArn": "arn:aws:xray:us-east-2:447393541969:*"},
      "StringEquals": {"aws:SourceAccount": "447393541969"}
    }
  }]
}
```

The second resource follows AWS's documented ingestion policy; its inclusion does not authorize enabling other Application Signals features. Adding a scoped policy does not narrow any older broader policy; do not claim it does.

```powershell
# Run only if the policy is needed and the document was reviewed.
aws logs put-resource-policy --profile default --region us-east-2 --policy-name restaurantFinder-TransactionSearchAccess --policy-document file://<ABSOLUTE_POLICY_FILE>

aws xray update-trace-segment-destination --profile default --region us-east-2 --destination CloudWatchLogs
aws xray get-trace-segment-destination --profile default --region us-east-2
aws xray get-indexing-rules --profile default --region us-east-2
```

AWS says searchable spans can take up to 10 minutes to appear after enablement. Wait in intervals no longer than 60 seconds, keep the owner informed, and use log arrival as evidence. `ACTIVE` alone is not delivery proof. Do not make additional policy or instrumentation changes blindly after a failed check.

### Step 12 — Prepare and inspect the AgentCore-only deployment

From the infra directory, synthesize with the exact new image. If infra source was changed, run `npm run build` first.

```powershell
Set-Location -LiteralPath (Join-Path $repoRoot 'restaurant-finder-infra')
npx cdk synth restaurantFinder-AgentCoreStack --quiet -c "imageUri=$imageUri"
```

Compare `cdk.out/restaurantFinder-AgentCoreStack.template.json` directly with the preflight deployed template. Expected functional difference: Runtime image URI. New prompt versions are packaged in the image; they are not CloudFormation resources. Investigate any IAM, unrelated environment, resource creation/deletion, or replacement differences before deployment. CDK metadata differences may be nonfunctional, but still record them.

Only after reviewing the expected template, prepare the change set. This command publishes CDK assets and creates a CloudFormation change set, so it is an authorized external write, not a read-only diff:

```powershell
$changeSetName = 'restaurant-finder-' + (Get-Date -Format 'yyyyMMddHHmmss')
npx cdk deploy restaurantFinder-AgentCoreStack --exclusively --method prepare-change-set --change-set-name $changeSetName --require-approval never -c "imageUri=$imageUri"
aws cloudformation describe-change-set --profile default --region us-east-2 --stack-name $stackName --change-set-name $changeSetName --output json
```

Confirm the installed CLI supports `prepare-change-set` and `--exclusively`; both were inspected while drafting. Confirm no ECR dependency deployment occurred. Require the change set to be available and every resource replacement/delete to be absent. Expected Runtime change has `Replacement: False`. If the diff is broader, stop and resolve scope before executing.

Execute the reviewed change set:

```powershell
aws cloudformation execute-change-set --profile default --region us-east-2 --stack-name $stackName --change-set-name $changeSetName
```

Poll stack and Runtime statuses at spaced intervals (for example 15–30 seconds) while continuing independent work. Do not block commentary with a long CLI waiter. Fail on terminal failure status. Success requires a stable stack and Runtime `READY` on `$imageUri`, not merely an accepted update response. Recheck EcrStack and its resource events to confirm it was not redeployed.

### Step 13 — Prove deployed memory recall and isolation

Use an ignored temporary Python script with `boto3.Session(profile_name='default', region_name='us-east-2')`. Configure a reasonable Runtime read timeout (for example 240 seconds) and disable automatic request retries for these tests to avoid ambiguous repeated invocations.

1. Generate actor A as `codex-handoff-<uuid>` and session A1 as a unique ID at least 33 characters long. Use only valid identifier characters.
2. Invoke the Runtime with JSON bytes and `contentType='application/json'`, `accept='text/event-stream'`, and `runtimeSessionId=sessionA1`. Payload fields: `prompt`, `customer_name='Verification'`, `actor_id=actorA`, `conversation_id=sessionA1`.
3. Seed: `Hello! Please remember my dining preferences: I am vegan, I prefer Thai cuisine, and my meal budget is under 25 dollars.`
4. Consume the full response stream. Parse both direct SSE JSON and nested JSON strings; capture `chunk`, `done`, `error`, and `blocked` explicitly. HTTP 200 with no content, a block event, or an error event is not a successful answer.
5. Poll `retrieve_memory_records` for namespace `/users/{actorA}/preferences`, query `dietary preferences cuisine budget`, topK 5, until all three synthetic facts appear. Allow up to five minutes in spaced polls; do not reseed repeatedly. If extraction is still absent, report the gap.
6. Create a different session A2 for the same actor. Send the exact previously failing memory-only wording from section 3. Do not include vegan, Thai, or $25 in this input.
7. Assert the answer reports all three facts. Inspect fresh spans/logs or a safe graph-event check to prove `restaurant_search`, a `memory_retrieval_tool` invocation, and successful returned records.
8. Generate actor B and new session B1. Directly query actor B's preference namespace and require no actor A records. Run a UI/API recall check if needed; do not infer memory isolation only from the model declining to answer.
9. Distinguish tool errors from successful empty results. Never pass if the model fabricates a correct-looking answer despite a retrieval failure.

Keep the isolated synthetic memory records; deletion is outside this scope. Record test actor/session IDs only in ignored evidence, not telemetry dimensions or public documentation. No authenticated production identity claims are warranted by this test.

### Step 14 — Verify the UI and trace/log/metric delivery

UI:

1. Determine whether the existing port-8000 process is this project's Chainlit server before stopping anything. Inspect its command line; do not kill unrelated processes.
2. Restart only the verified project server if needed for edited code. Use the saved `.env` from the UI directory and bind `127.0.0.1`:

```powershell
Set-Location -LiteralPath (Join-Path $repoRoot 'restaurant-finder-ui')
uv run --no-sync chainlit run app.py --host 127.0.0.1 --port 8000
```

3. Use the Playwright skill or the approved in-app browser controls for a greeting and a memory recall flow. If applying a skill, read it and follow its browser-session rules. Do not run two browser controllers against the same test session.
4. Show blocked-message behavior using deterministic direct/nested SSE fixtures. A real block check can replay the previously blocked benign instruction-style prompt; AWS blocking is not deterministic, so do not count an unblocked result as proof of blocked rendering. Use a temporary local fixture transport/browser server if necessary, keep it bound to localhost, and restore normal UI settings afterward.
5. Confirm block text survives `done`, no blank result is shown, and normal replies still stream. Report browser errors/warnings honestly; prior checks had warnings.

Tracing:

1. Record a fresh request window using UTC timestamps from the request script.
2. Read `aws/spans` events in that window. Inspect actual span documents; adapt the query to the returned structure rather than assuming a field layout.
3. Identify `workflow.execution`, `router.classify`, and `router.jev` in one trace. Correlate through trace IDs and the synthetic session/workflow context. Verify provider/intent attributes on the router span.
4. The 0% indexing baseline may yield no X-Ray trace summaries; inspect stored span logs. Do not increase indexing just to make `get-trace-summaries` show a result.
5. Inspect fresh Runtime and telemetry logs for trace exporter 400/403 errors after the destination becomes active. Do not confuse historical errors with current failures.

Logs and metrics:

1. Verify fresh sanitized `memory.save` and `memory.retrieve` log records and their status attributes.
2. Query OTLP metrics through the signed CloudWatch PromQL endpoint. Classic `cloudwatch list-metrics` returned empty in the previous check even though these OTLP metrics existed.
3. Use SigV4 service `monitoring`, region `us-east-2`, credentials from the default session, and URL `https://monitoring.us-east-2.amazonaws.com/api/v1/query`.
4. URL-encode and query `last_over_time({__name__="agentcore.memory.save.count"}[1h])`, then `agentcore.memory.retrieve.count` and `agentcore.memory.operation.duration`. Inspect returned timestamps to ensure the evidence is relevant to this deployment; old samples alone do not satisfy the check.
5. Expect status `success` with nonempty counters/histograms. Do not label cumulative metric values as request totals without accounting for Runtime instances and resets.

Exit condition: all relevant criteria in section 4 have inspected evidence. If trace delivery still fails, retain error type/status and endpoint/config facts, investigate narrowly using primary documentation, and report the remaining blocker without claiming monitoring is complete.

### Step 15 — Save the result and hand it back

1. Update README's dated checkpoint and known gaps from actual results. Keep startup instructions accurate and document that Transaction Search is regional account configuration outside the application stack.
2. Create a concise evidence summary: source commit, image tag/digest, prompt version changes, stack/Runtime status, tracing before/after, indexing setting, tests, real provider results, memory recall/isolation, UI outcomes, and unmet criteria.
3. Scan candidate Git files for the configured TypeSafe key and credential patterns without printing their values. Ensure `.env`, credential directories, generated prompt manifests, and live-check artifacts remain ignored. A pattern scan is not a guarantee that all possible secrets are absent.
4. Review `git diff --check`, `git diff`, and staged paths. Commit only intended changes and this handoff document if still uncommitted. Preserve unrelated/user files.
5. Push `feat/jev-router` after approved validation. Reinspect workflow triggers before pushing; current deployment workflows auto-run on `main`, not this branch. Do not merge to `main` or dispatch workflows.
6. Keep a sanitized persistent validation summary in README or the requested project notes. Remove generated scripts, temporary credentials, screenshots/logs, and temporary fixture servers after extracting needed evidence. Retain user files. Remove only verified generated paths; Windows recursive cleanup must use checked absolute targets and `Remove-Item -LiteralPath`.
7. Keep the normal UI available for the owner if requested; report whether it is running and how to restart it.
8. Final response: commit link, local UI URL/status, deployment image, checks that passed, remaining gaps, any account-level changes, and rollback information. Do not claim reduced cost or improved latency without a separate benchmark.

## 7. Failure handling and rollback

| Failure | Required response |
| --- | --- |
| Wrong AWS account/region | Stop cloud writes; report the mismatch. |
| Local tests fail | Fix within approved scope; do not build/push/deploy a failed implementation. |
| Jev live case falls back | Report it as a Jev check failure, not a classification success; inspect availability and refine only when justified. |
| Prompt manifest mismatch | Regenerate using the sync command after approval; never falsify hashes/versions. |
| ECR helper failure | Use isolated temporary config workaround; preserve regular Docker credentials. |
| Unexpected CloudFormation replacements/deletes/IAM changes | Do not execute; reconcile with scope first. |
| AgentCore update fails | Inspect stack events; allow CloudFormation rollback to complete; never delete/recreate the stack as a shortcut. |
| Deployed code regression | Deploy `$previousImageUri` through an AgentCore-only reviewed change set using the same `--exclusively` procedure. Restore UI source by targeted revert, preserving `.env` and other changes. |
| Trace delivery fails after account change | Keep evidence; investigate scoped causes. A destination rollback affects all regional tracing users, so explain impact and obtain explicit rollback approval before switching it back. |
| Memory extraction delayed | Wait bounded intervals; distinguish delay/empty/errors; do not invent remembered facts or repeatedly write seed events. |

Rolling back the image restores the previous packaged prompt manifest; new immutable prompt versions and ECR images can remain for audit. Do not delete them. If approved to reverse the destination, use the preflight snapshot; its current baseline command would be:

```powershell
aws xray update-trace-segment-destination --profile default --region us-east-2 --destination XRay
```

Reverting the destination does not undo ingested spans or charges and makes this Runtime's OTLP trace path fail again. Do not delete shared log groups/policies as rollback cleanup. If new shared tracing consumers appeared, pause and reassess before rollback.

## 8. Decisions, remaining questions, and source requirements

Decisions already specified: keep Jev/Haiku versions; use the existing tool-capable route for memory; handle blocked events in the UI; preserve 0% indexing; use a versioned ARM64 image; deploy AgentCore only; publish on the feature branch; no performance benchmark or production identity redesign.

Questions that actually require the owner: approval of this PRD, materially broader account changes, unexpected resource replacements/deletions, and an account-level rollback affecting other tracing consumers. Ordinary implementation details and safely discoverable resource IDs do not require another question.

Primary references, retrieved while drafting:

- [AWS ADOT setup](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-OTLP-UsingADOT.html): Transaction Search prerequisite for the X-Ray OTLP endpoint.
- [Enable Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-TransactionSearch.html): regional account tracing change, resource policy, destination, indexing, and propagation delay.
- [GetTraceSegmentDestination](https://docs.aws.amazon.com/xray/latest/api/API_GetTraceSegmentDestination.html): destination/status readback.
- [CloudWatch QueryMetrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-PromQL-API-QueryMetrics.html): signed PromQL query path and permissions.
- [Docker login credential handling](https://docs.docker.com/reference/cli/docker/login/): Windows helper behavior and temporary configuration considerations.

The deployment flags `--exclusively` and `--method prepare-change-set` were confirmed in the installed local CDK CLI help. Recheck if the CLI changes. Use primary documentation for uncertain API behavior; never invent success evidence.
