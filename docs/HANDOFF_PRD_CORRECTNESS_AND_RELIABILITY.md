# Handoff PRD: Correctness and Reliability Repairs

## Outcome

Repair the correctness and reliability issues found during the Restaurant Finder review, verify them locally, and deploy the validated code to the existing AWS development stack. The work should make a single user turn predictable: tool use is bounded per turn, browser sessions are isolated, results are normalized accurately, and no response is shown or saved until the output guardrail has approved it.

## Audience and reason

This document is the execution brief for the project owner and the implementing agent. It records the approved scope, acceptance criteria, deployment boundaries, and evidence needed to decide whether this work is complete.

## Definition of done

- All eight repair areas below are implemented with regression coverage.
- Existing API and UI checks pass, plus focused new checks for each repaired behavior.
- Importing supported modules in a fresh Python process does not create AWS clients or fail through package import cycles.
- The repository's prompt manifest is synchronized from the actual prompt sources before the runtime image is built; the image contains a validated manifest.
- A unique ARM64 image is published and its digest and manifest are verified.
- The existing development CloudFormation change set contains only the intended Lambda code asset and AgentCore Runtime image updates. No replacement, deletion, IAM, memory, or tracing change is allowed.
- Bounded live Runtime checks pass, including turn-scoped tool budgets, same-session follow-up, memory isolation checks, browser operation concurrency, and guardrail behavior where live configuration permits.
- README and this execution record describe the resulting code, checks, prompt versions, image digest, deployment facts, and any validation gaps.
- Changes are committed and pushed on `feat/jev-router`. No merge to `main` and no GitHub workflow dispatch.

## Approved scope: eight repair areas

1. **Per-turn tool budget.** Initialize tool count for every new user turn, permit the fourth configured call to execute, never leave an unmatched tool call in conversation state, and produce a valid final answer when the budget is exhausted. The budget is a per-turn limit, not a cumulative conversation limit.
2. **Output guardrail before display and memory.** Buffer the complete answer, check it before sending any text or saving memory, use approved anonymized output, let a block take precedence, and fail closed with a readable service error if an enabled guardrail is missing or errors. Preserve the existing guardrail policy and disabled-mode behavior.
3. **Single graph execution.** If streaming fails, do not invoke the graph again to recover. Return a safe failure result without replaying tools, memory hooks, or other side effects.
4. **Isolated browser operations.** Create one BrowserToolkit per browser operation; use a unique operation thread ID; pass its tools and config explicitly; close only that operation's toolkit in `finally`, including error and cancellation paths. Keep the user's conversation/session identity unchanged for tracing and memory.
5. **Normalize and validate restaurant results.** Handle direct dictionaries, JSON strings, and MCP TextContent lists through one normalizer; unwrap supported Lambda envelopes consistently (maximum four layers); validate `statusCode`, error values, and final restaurant-list shape; raise typed, sanitized errors; do not log raw response bodies. Unknown fields remain unknown: ratings/review counts/prices are nullable when absent; `price_description` retains values such as `$10–20`; review counts are nonnegative numbers or null; booleans parse true/false/null rather than Python truthiness; preserve zero; do not present requested filters as restaurant facts; count only valid restaurants; result status is `success`, `empty`, or `error` with an error code; generic web articles are not restaurant records; preserve the actual data source. Reuse the normalization rules for MCP and browser extraction.
6. **Consistent requested result counts.** Default to at most five results; honor an explicit requested count from 1 through 10; return fewer when evidence supports fewer; invoke browser fallback only when valid results are fewer than `min(4, requested_count)` and the request remains unmet. Do not browser-search if the user asked for two and received two. Bind only tools that are available and preserve the difference between discovery and single-restaurant research.
7. **Safe package imports.** Keep package `__init__.py` files lightweight. Direct model, prompt, state, node, and API imports must work in isolated fresh Python processes without eager application/workflow imports or AWS client creation, while preserving supported app entrypoints.
8. **Fresh-ECR deployment consistency.** In the deployment workflow's empty-ECR path, set up Python 3.11 and the pinned `uv`, synchronize the lock with `--extra local-aws`, synchronize and validate prompts before image build, and add offline manifest validation to the Docker build. Distinguish ECR lookup failures from an empty repository. Preserve workflow triggers and ARM64 behavior. Validate branch logic with fixtures/static checks; do not dispatch the workflow or use another AWS account.

## API and UI behavior

- Replace the internal streaming generator contract with a typed `run_orchestrator_turn` result containing the complete safe text and whether the response was blocked. Preserve the request JSON and existing SSE event shape. A successful answer is emitted as one complete chunk followed by `done`; blocked and error paths also end cleanly. Never retry or replay a graph turn.
- Read the AgentCore streaming HTTP body in a worker thread, with 10-second connect and 300-second total/read bounds, close the response, and disable automatic AWS Runtime retries. Avoid blocking the async event loop. Show `Working on your request…` while the UI waits. Preserve direct and nested UI block parsing.
- Graph order: input guardrail → initialize per-turn state → router → search/tool loop → final output guardrail → memory hook only if approved → END → UI sends approved complete text.
- The finalizer updates the same AIMessage ID with approved masked text or a safe blocked message. A blocked or unavailable guardrail result creates no memory event. An approved turn saves exactly the final approved text. Keep the existing checkpointer limitation documented; do not broaden this scope into a persistence redesign.

## Constraints and deployment boundaries

- Do not change the Jev router or Haiku fallback model selection.
- Do not run benchmarks.
- Do not modify regional AgentCore tracing settings, memory retention/index configuration, or broad IAM policy.
- Do not delete or replace existing resources, images, prompt versions, or memories.
- Do not merge to `main`, dispatch workflows, or deploy to a different account.
- Build an ARM64 image with unique tag `correctness-<source-short-sha>-<UTC timestamp>-arm64`; do not overwrite `latest` in the manual path.
- Prompt sync is an AWS write. Perform it only after confirming the intended AWS identity and region. Only prompts whose source hashes changed should receive new immutable versions.
- Before deployment, record the current stack template, Runtime image URI/READY status, Lambda identity/hash/asset, and source commit. Prepare and inspect a change set before executing it.
- The expected change set may update only the Lambda code asset and AgentCore Runtime image. Stop if any resource replacement, deletion, IAM, memory, tracing, or other unexpected change appears.
- Live Runtime verification is bounded to at most 12 invocations, two deliberately concurrent browser operations, and ten bounded extraction polls. Use synthetic actors; do not delete retained memories or claim production actor-identity guarantees.
- Roll back Runtime image and Lambda asset together from the recorded deployed template/source if needed. Keep images, prompts, and memory data.

## Verification plan

1. Run focused regression tests for the eight repair areas and existing API/UI test suites; use deterministic fixtures for guardrail, MCP, browser, and workflow error paths.
2. Use subprocess import checks for each required public module and verify that imports make no AWS calls.
3. Run repository checks (`git diff --check`, Python compile/import checks, UI test/build checks, infrastructure synthesis/static assertions) without dispatching CI.
4. Scan the proposed diff for secrets and verify no ignored `.env` or generated prompt manifest is staged.
5. Revalidate AWS caller identity and region. Synchronize changed prompts and validate the generated manifest.
6. Build and publish the unique ARM64 image; inspect the manifest and confirm its image digest.
7. Back up deployment facts, prepare the exclusive stack change set, and inspect every resource action before execution.
8. Execute only if the change set matches the boundaries above. Verify Runtime readiness and run the bounded live checks.
9. Update the execution record and README, commit and push the branch, and report verified results and any blocked criteria.

## Baseline findings to verify during implementation

The review reproduced these issues using source inspection and local fixtures: tool-call count can persist in graph state across user turns and the limit check can skip execution at the boundary; output guardrail checks occur after stream chunks have already been yielded and fail open when configuration is missing; stream failure can trigger a second graph execution; browser cleanup closes all shared browser sessions; supported MCP response encodings are handled inconsistently; requested count, prompt instructions, and fallback threshold disagree; eager package imports create a circular dependency; and the fresh-ECR image path does not generate the prompt manifest. These are review findings, not live AWS test results.

## Execution record

### Local implementation and verification — October 7, 2026

- Implemented the eight approved repair areas and the API/UI boundary changes
  above on `feat/jev-router`. Added focused regression coverage in
  `restaurant-finder-api/tests/test_correctness_repairs.py` and
  `restaurant-finder-ui/tests/test_sse_responses.py`.
- API verification: 47 tests passed with
  `python -m unittest discover -s tests -v` from `restaurant-finder-api`.
  The local test run disabled prompt sync and pointed the manifest path at a
  missing temporary file so it would not make AWS calls or rely on a stale,
  ignored generated manifest.
- UI verification: 8 tests passed with
  `python -m unittest discover -s tests -v` from `restaurant-finder-ui`, using a
  separate temporary test environment because the existing UI environment was
  in use.
- `python -m compileall` passed for the API source/tests, Lambda handler, and UI
  source/tests. `git diff --check` passed. `npx --no-install cdk synth` passed
  from `restaurant-finder-infra` and synthesized both stacks locally.
- The checked-in prompt sources changed, but prompt synchronization and
  manifest validation against Bedrock have not run. No prompt version, ECR
  image, or AWS resource was changed by this local work.

### AWS deployment and live verification — October 8, 2026

- AWS identity was verified as account `447393541969`, ARN
  `arn:aws:iam::447393541969:user/kangzhen`. The profile's configured region is
  `us-east-1`; every AWS operation for this task explicitly targeted
  `us-east-2`, and the profile was not changed.
- Prompt synchronization completed in `us-east-2`. New immutable versions
  were created for `SEARCH_AGENT_PROMPT` v3, `RESTAURANT_EXPLORER_PROMPT` v2,
  and `RESTAURANT_EXTRACTION_PROMPT` v2. Existing versions were reused for
  `ROUTER_PROMPT` v2, `SIMPLE_RESPONSE_PROMPT` v1, and
  `RESEARCH_EXTRACTION_PROMPT` v1. The generated prompt manifest validated.
- Built and pushed the unique ARM64 image
  `447393541969.dkr.ecr.us-east-2.amazonaws.com/restaurantfinder-agent:correctness-f9dcf56-20261007135110-arm64`.
  Its verified ECR/Buildx digest is
  `sha256:0614966b8424edbeba937ca6f4014d492ccc624d347ecc2ec4f14c35fbcc23c2`.
- Before preparing the change set, the stack was `UPDATE_COMPLETE`; Runtime
  `restaurantFinder_Agent-Ha58oX5Psu` was `READY` on
  `memory-ui-tracing-8685344-20261007-143849-arm64`. The existing Lambda was
  `restaurantFinder-AgentCor-restaurantFinderMcpLambd-eMGGBXrDjYVB` with code
  hash `RBhOldQ6xJ3iY04OVUnxqtOsK2Yh6peEjsooYse9wHg=`. The source commit was
  `f9dcf56`. The pre-deployment CloudFormation template was backed up with
  SHA-256 `2BF1F056AFB0E24E164E96EE16CC5FDC49EE6D23608C5458CBAF4E0377EBFA09`.
- Prepared change set
  `arn:aws:cloudformation:us-east-2:447393541969:changeSet/correctness-20261007135110/d26ae023-1cee-4f86-bda7-52b8efa5a3ca`.
  The standard preview included the intended Lambda code and Runtime image
  updates plus dynamic `Modify` predictions for
  `AWS::BedrockAgentCore::GatewayTarget`
  (`restaurantFinderAgentCoreGatewayLambdaTarget`) and `AWS::IAM::Policy`
  (`restaurantFinderAgentCoreGatewayRoleDefaultPolicy7B703173`) caused by
  `restaurantFinderMcpLambda7367777D.Arn`. The enhanced preview with property
  values showed exactly two resource changes: the Runtime image URI and the
  Lambda code S3 asset. The GatewayTarget `TargetConfiguration` and IAM
  `PolicyDocument` values matched the deployed template, and the resource
  identities and replacement flags were unchanged. This met the approved gate.
- Executed the change set. CloudFormation reached `UPDATE_COMPLETE`; Runtime
  `restaurantFinder_Agent-Ha58oX5Psu` reached `READY`, version 9, on
  `correctness-f9dcf56-20261007135110-arm64`. The latest stack events show only
  the Lambda function and Runtime updated, followed by stack `UPDATE_COMPLETE`;
  no rollback occurred in this change set. The Lambda retained its physical
  identity and is `Active` with `LastUpdateStatus=Successful`. Its deployed
  `CodeSha256` is `XvwOFiXGSO8vUE/WrHckfd22jGCKZ/x2q6OJkj/7rJc=`.
- The ECR image remains the verified ARM64 digest
  `sha256:0614966b8424edbeba937ca6f4014d492ccc624d347ecc2ec4f14c35fbcc23c2`.
  The image contents were checked against the worktree before deployment, and
  a fresh CDK synth produced the expected Lambda asset and image tag.
- Post-deployment read-only checks confirmed Runtime version 9 is `READY` on the
  expected image, the GatewayTarget is `READY` and still points to the existing
  Lambda ARN, and the gateway role policy still permits only
  `lambda:InvokeFunction` on that function and its qualified ARN.
- Ten Runtime responses completed successfully: five earlier direct requests
  covering greetings, restaurant search, and same-session follow-up; one
  Chainlit greeting; then synthetic memory save, same-actor recall in a new
  session, a different-actor isolation request, and an illegal-activity request
  that returned `blocked=true` with no text. One additional request was rejected
  before reaching the Runtime because the AWS session had expired. The total is
  11 Runtime API attempts out of the 12-request cap, with no SDK retries.
- Memory verification passed: the synthetic vegan/Thai/Penang/under-RM100
  preference appeared in the preference namespace on poll 5, the same actor
  recalled it in a new session, and a different synthetic actor received no
  saved preferences. Synthetic records were retained; none were deleted.
- Output PII verification passed using `test@example.com`: `ApplyGuardrail`
  returned an `EMAIL / ANONYMIZED` assessment and the original address was
  absent from the returned output. A first synthetic address under `.invalid`
  was instead blocked by the denied-topic classifier; the standard test address
  verified masking. Guardrail policy was not modified.
- Exactly two Browser operations were created concurrently and received distinct
  operation IDs. Both navigations completed without exceptions. After closing
  the first toolkit, the second toolkit returned extracted page text, and both
  toolkits were cleaned up. The final diagnostic print then failed because the
  Windows CP1252 console could not encode a Unicode character in the extracted
  page text, so the expected page-marker value was not captured. The Browser
  operations were not repeated because the approved cap was two.
- CloudWatch was inspected read-only. The Runtime log group had 113 events in
  the six-hour query window, no traceback or `error` text, and no events later
  than `2026-10-07T19:29:39Z`. The GenAI telemetry group likewise had no events
  later than `2026-10-07T19:29:42Z`; therefore it contains no fresh trace/log
  evidence for the October 8 Runtime checks. The telemetry query had no `403`
  mentions; 15 lines contained the literal string `400`, but their meaning was
  not established from the bounded summary. No tracing setting was changed.
- `git diff --check` and the tracked-diff credential-pattern scan passed; no
  `.env` or generated prompt manifest appears in Git status. Earlier local
  verification remains 47 API tests and 8 UI tests, compile checks, and CDK
  synthesis. These suites were not rerun after documentation-only edits.
- No resource replacement or deletion occurred, and no prompt, memory, IAM, or
  tracing configuration was changed by the deployment. The remaining evidence
  gaps are the absent fresh telemetry and the Browser test's uncaptured page
  marker; the operation-isolation behavior itself completed. The branch is
  ready for the planned commit and push, with these limitations recorded.
