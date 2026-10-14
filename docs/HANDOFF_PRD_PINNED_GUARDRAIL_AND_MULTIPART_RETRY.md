# Handoff PRD: Pin the validated guardrail and retry multipart acceptance

**Status:** Gate A COMPLETE. Gate B execution explicitly approved by the owner on 2026-10-14; publication/image/rollout/live acceptance are in progress. Their outcome remains unmeasured until receipts establish it.

**Outcome:** Bind the Restaurant Finder to the validated immutable guardrail, preserving safe failure, masking and citation release; then complete bounded multipart acceptance before any demo walkthrough.

**Audience/purpose:** The project owner and execution agent preparing an AI engineering demonstration. Success requires correct configuration, reproducible release bytes and verifiable document sources. No benchmark, production launch or LinkedIn publication is included.

## 1. Verified starting point

| Item | Current evidence |
| --- | --- |
| Workspace | `C:/Users/kinoc/Documents/Codex/2026-09-28/i-x20/work/agentic-ai-langgraph-and-aws-agentcore`. |
| Git | `feat/document-multipart-rollout`, HEAD `0845b8bb4c1fa74e933470274d7272dc1561c5f0`. Three approved telemetry/test paths remain modified locally, unpublished. |
| Review | Draft [PR #1](https://github.com/yukangzhen/restaurant-finder/pull/1), base `feat/jev-router`; origin owned by yukangzhen. Never push upstream or merge. |
| Application baseline | Runtime `restaurantFinder_Agent-Ha58oX5Psu` / DEFAULT READY 15; multipart key absent; restored `comparison-be5c35d-20261012093655-arm64` image. Recapture before rollout. |
| Original guardrail | `sfiq3neb2co5`, DRAFT, unchanged; rejects first-party citation provenance. |
| Validated candidate | `ih5xpt3qi946`, version `1`, READY, region `us-east-2`, name `restaurant-finder-doc-sources-20261013`. Ten controls passed on DRAFT; numbered configuration matches. |
| Configuration digest | `8e69ed2c156b0977e41c36e6edce06f7c72fa80244021d4e3ffcf258782bf390`; numbered policy fingerprint `cbf24512ff86fcd0187d95424e868d0f4b5ee1199515bdd4b06363ccdfad176d`. |
| Integration defect | Manager resolves by name; startup overwrites ID/version settings. An environment version alone cannot select the immutable candidate. |
| Infrastructure | No pinned guardrail environment pair is currently emitted. Source IAM already permits GetGuardrail/ApplyGuardrail for account/region guardrails; verify the deployed role. No IAM change is planned. |
| Corpus/prompts | Generation `29a3a897b651c3d9fe153ce5c819f3acfe29e2ab786ac56d82e998821598267a`, six originals. Retained nine-prompt manifest SHA `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9`; keep older eight-prompt worktree manifest unchanged. |
| Historical tests | 209 API tests; complete 17/20/40 offline cases, 374/260/609 checks. No fresh suite ran during candidate creation. |

The [repair PRD](HANDOFF_PRD_MULTIPART_GUARDRAIL_REPAIR.md) records actual outcomes/limitations. Historical unrun cases and the already used rollback do not transfer here.

## 2. Deliverables and completion gates

**Gate A — local implementation/tests:** explicit immutable binding, safe startup, accepted default definition, generic CDK pair configuration, regressions/full local reports, and a reviewed release/deployment proposal. Completion means code/tests pass and Gate B is concrete; it does not mean deployment or live acceptance.

**Gate B — separately approved publication/rollout:** reviewed source publication with passing inspected CI; one audited unique ARM64 image; minimal Runtime update; verified immutable binding/readiness; six fresh user requests and original-source inspection/downloads; retain/conditional rollback and safe closeout. Stop before demonstration.

## 3. Authorization and preservation

| Action | Boundary |
| --- | --- |
| Safe inspection and this PRD | Included in completed candidate plan. |
| Gate A source/docs/test map below | New explicit implementation/test sign-off. |
| Commit/push/update draft PR, image build/push, Runtime update | Gate B sign-off on concrete reviewed release/configuration. No merge. |
| Owned UI restart, six Runtime sends, four original downloads, one conditional rollback | Must be explicitly included in Gate B's fresh allowance. |
| Guardrail create/update/version/delete or extra standalone probes | Not included; candidate already exists. |
| Docker restart/recovery | Separate approval if needed; earlier one-use restart permissions are spent. |

Preserve real `.env`, credentials, locks, owner warning work, corpus/vector index/pointer/originals, prompts, gateway/memory/resources, models/Jev and unrelated changes. No new dependencies, IAM expansion, benchmark/demo, moderation disablement, citation exemption, blocked-answer retry/replan or worker/provider payload exposure.

## 4. Gate A implementation map

| Repository path | Change |
| --- | --- |
| `restaurant-finder-api/src/infrastructure/guardrails.py` | Resolve explicit ID/numbered version with GetGuardrail, verify READY/matching identity, cache it; no configured-failure name/create/update/version fallback. Mirror only the accepted competitor definition. Preserve existing decisions and telemetry. |
| `restaurant-finder-api/src/infrastructure/startup.py` | Preserve validated pair; enabled pinned initialization failure raises a sanitized unavailable error and leaves startup incomplete. |
| `restaurant-finder-api/src/config.py` | Reuse existing fields; clarify complete-pair/numbered-version semantics without new service/secret fields. |
| `restaurant-finder-api/tests/test_correctness_repairs.py` | Add mocked binding/setup/cache/startup failures while retaining privacy/finalization regressions. |
| `restaurant-finder-infra/bin/cdk.ts` | Strict optional paired `guardrailId` / `guardrailVersion` contexts; reject partial/invalid/DRAFT binding. |
| `restaurant-finder-infra/lib/stacks/agentcore-stack.ts` | Paired optional props; emit both environment keys together, otherwise omit both. Preserve multipart default-off/IAM/resources. |
| `restaurant-finder-infra/test/document-rag.test.ts` | Omitted/valid/partial/malformed/DRAFT pair tests, including normalized-template invariants. |
| `restaurant-finder-infra/README.md` | Pair configuration, deliberate setup, immutable identity and four-field reviewed update/rollback semantics. |
| This PRD and repair PRD | Append actual results. |

`api.py` already awaits initialization without swallowing its exception. Inspect/test that behavior before adding another source path. UI/contracts/prompts/CI/locks initially need no changes; show evidence and scope before expanding.

## 5. Binding contract

- Empty ID/default DRAFT preserves deliberate unconfigured create/get setup. Auto-resolved cached settings must not be mistaken for a new external strict pair on repeated initialization.
- Explicit ID with valid positive numbered version: GetGuardrail exactly that pair, require matching returned ID/version and READY. Deployment target is `ih5xpt3qi946:1`; do not hardcode it as a generic default.
- Explicit ID with missing/DRAFT/invalid version, or numbered version without ID: fail before accepting requests; reject partial CDK contexts/props too.
- Not found, denied, timeout, malformed/mismatched response or non-READY: sanitized failure, startup incomplete, no List/Create/Update/CreateVersion fallback.
- Cache only a successful pair, with bounded initialization client settings. Metadata lookup is not per-turn moderation; preserve client-free imports.
- Intentional disabled local setup still makes no guardrail call. Gate B remains enabled.
- Keep one final complete-answer moderation operation. Mask/block/unavailability suppress document citations/coverage; only approved text follows existing memory gates.

Required tests: exact lookup/pair propagation into input/output checks; no fallback mutation; invalid-pair failures; compatible default setup/cache behavior; seeded error privacy; startup/lifespan failure; CDK omitted/valid/invalid serialization and unchanged non-binding properties. Reset test singleton/startup state explicitly; never edit real configuration.

## 6. Gate A execution and verification

1. Capture branch/HEAD/status and starting hashes. Extend the three existing telemetry changes; do not reset them or include owner warning work.
2. Fresh read-only candidate version/configuration, original Runtime/guardrail, corpus pointer and intended identity checks. Stop dependent work on material drift.
3. Implement the approved map; inspect decision/source/memory invariants and safe errors. Preserve nine-prompt artifact and old worktree manifest; no prompt sync.
4. Run full API discovery and three offline evaluators with isolated metadata/prompt/export/live-evaluation-off variables and an absent manifest sentinel. Use new ignored reports; commands are in repair PRD section 8. Verify complete 17/20/40 cases.
5. Run locked UI regression suite; infrastructure build/Jest and dummy-account no-lookup synth with omitted/valid/invalid binding contexts. Use installed locked dependencies; no update/provider lookup. Record actual fresh counts.
6. Review diff/privacy/provider-call prohibitions, original datasets/manifest hashes and all preserved owner assets. Existing guardrail decisions must remain unchanged.
7. Prepare exact commit/PR file list and safe description, release/image/manifest/template/budget/rollback package for Gate B. Exclude `.generated`, secrets/configuration and `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`. Stop before publication/mutation.

## 7. Gate B rollout — not yet authorized

Reuse the [prior rollout's procedures](HANDOFF_PRD_MULTIPART_PUBLICATION_AND_ROLLOUT.md) for image/prompt provenance, readiness, change-set review, traces, source inspection and cleanup. This gate needs fresh authorization; prior two-field/budget/rollback authority is spent.

Exactly four intended Runtime leaves:

```text
AgentRuntimeArtifact.ContainerConfiguration.ContainerUri = fresh audited release image
EnvironmentVariables.DOCUMENT_MULTIPART_ENABLED = "true"
EnvironmentVariables.BEDROCK_GUARDRAIL_ID = "ih5xpt3qi946"
EnvironmentVariables.BEDROCK_GUARDRAIL_VERSION = "1"
```

Capture fresh original template/Runtime/endpoint and image/UI rollback evidence. Build the minimal four-leaf patch, preserving all other properties/env values/key presence/resources/outputs. Require a reviewed change set modifying only the existing Runtime, without replacement. Full synthesis is source evidence, not permission to apply unrelated drift.

Verify deployed role GetGuardrail/ApplyGuardrail permission and immutable configuration without broadening IAM. Once publication is approved, push reviewed release to origin/update draft PR and inspect exact-SHA CI artifacts. Reuse validated nine prompts; no sync/new version by default. Prove baseline ECR digest fetchable/retained, build/audit one unique ARM64 tag from exact source/manifest, push once and record actual runnable registry digest. Do not invent it during planning.

Docker failure requires separate recovery approval. Execute approved reviewed change set once; verify stable stack/Runtime/DEFAULT, image/pair/flag and unchanged resources/corpus. Readiness contains no warm-up/model request. If needed, stage the approved release UI on loopback 8010 after identifying/capturing current owned process/source/interpreter/configuration; restart only that owned UI under Gate B approval.

### Fresh six-attempt allowance

Explicit Gate B approval grants six new Runtime attempted sends, reserved before delivery. Errors/timeouts/uncertainty consume slots; no free retry, greeting, smoke probe, live evaluator or additional standalone guardrail call. Stop on wrong routing/evidence/arithmetic, refusal/provider failure, unexpected tool/replan or source association failure.

| Slot | Exact input and conversation | Expected |
| --- | --- | --- |
| L1 / fresh A | `Compare mushroom pasta prices at Harbor and Sakura, and explain both restaurants' cancellation policies. Show the sources.` | Answered 4/4, RM32/RM36 and RM4 difference, complete policies, four original sources. |
| L2 / same A | `For Harbor, what is the mushroom pasta price and cancellation policy?` | Answered 2/2, two sources/no two-venue arithmetic, scope cleared; retained L1 controls still target L1. |
| L3 / same A | `And what about its cancellation fee?` | Restaurant clarification, no cited answer/retrieval/selection/rewrite. |
| L4 / fresh B | `Compare mushroom pasta prices at Harbor and Spice, and explain both restaurants' cancellation policies.` | Partial 3/4, missing Spice dish explicit/no difference, full supported records, three sources. |
| L5 / fresh C | `Compare mushroom pasta prices at Harbor and Sakura, and explain both restaurants' cancellation policies and parking rules.` | Whole-request clarification; no planner/pin/embedding/vector/selector/source. |
| L6 / fresh D | `Compare mushroom pasta prices at Harbor and Sakura.` | Existing comparison 2/2, full qualifiers, RM4 difference, two sources/no multipart planner. |

Keep A's actor/session for L1-L3 with no restart; use synthetic separate actors for others. Preserve prior bounded expectations: three multipart planners, at most 12 logical worker retrievals, no web/repair/replan. Verify actual traces; these are expectations, not measured counts.

Inspect each L1 source in the actual UI, PDF page 1 and Markdown section/line context. Download all four exact originals, verify bytes/hash/generation/document/version/location against fresh references, and after L2 re-open a retained L1 control to verify answer association. Document inspections are not extra agent sends. No surrogate file/public bucket URL; keep bodies/signed URLs/credentials private.

### Newly approved rollback

Include at most one conditional rollback to the fresh baseline on rollout/acceptance failure. Restore image and exact prior presence/value of the three environment keys (multipart/ID/version), and verified prior UI source/configuration. Require stable new Runtime/DEFAULT version and unchanged pointer/resources; numeric version need not return to 15. No post-rollback model request beyond the six-send ledger.

Retain candidate/version/image/prompts and receipts. Rollback cannot erase publication, charges, telemetry or stored events; deletion is not approved. Additional recovery/mutation/probes need reviewed scope. Record actual acceptance/rollback and stop before demo regardless of outcome.

## 8. Acceptance and open gates

| ID | Observable requirement |
| --- | --- |
| P01 | Owner/source/dataset/manifest/lock identities preserved; approved paths only. |
| P02 | Exact numbered binding with no fallback; wrong/unavailable configuration prevents startup. |
| P03 | CDK pair parsing/emission/default/invalid cases and non-binding invariants verified. |
| P04 | Full approved local suites/offline cases pass; privacy/moderation/source/memory contracts intact. |
| P05 | Reviewed release/CI/artifacts/nine prompts/audited ARM64 registry digest align. |
| P06 | Four-leaf Runtime update and immutable binding read-back match; other state preserved. |
| P07 | Six scenarios and four original-source downloads pass within allowance. |
| P08 | Retain/rollback, budgets, safe cleanup/closeout recorded; no demo starts. |

Use PASS/FAIL/BLOCKED/UNMEASURED. Gate A can pass with P05-P08 unmeasured. Policy validation is not application binding; readiness is not functional acceptance. Never redefine completion after a stopped case.

**Next sign-off:** Gate B review package in sections 7 and 10: reviewed publication, one audited ARM64 image, minimal four-leaf Runtime update, six fresh attempted sends, original-source inspections/downloads, owned UI restart if needed and one conditional rollback. Gate A is complete. Final commit/image digest/Runtime version are future measured values and must be verified before deployment.

**Stopping point:** candidate `ih5xpt3qi946:1` remains unbound in AWS. Gate A local source/tests and fresh read-only AWS verification pass. Publication/rollout has not been executed.


## 9. Gate A execution record - 2026-10-13

The owner's "Proceed" approved Gate A local implementation/tests. Eight mapped source/test/documentation paths changed; the prior telemetry changes were retained. `api.py` needed no change: the lifespan failure regression proves it never yields or initializes Jev after a guardrail initialization failure.

Implemented exact configured ID/positive numbered version GetGuardrail validation, matching READY read-back, success-only cached identity and fixed sanitized errors. Invalid/partial/DRAFT pairs fail before client creation; provider/not-found/denied/timeout/malformed/non-READY failures have no automatic fallback. Metadata client timeouts are 5s connect/15s read with one total SDK attempt. Configured managers cannot publish a replacement version. Automatic empty-ID/DRAFT setup remains compatible within the initialized manager; enabled initialization failures now stop startup for both deliberate setup and pinned binding. Disabled local setup skips validation/clients. Only the reviewed 170-character competitor definition changed among default policies.

CDK accepts a complete optional string pair and emits both keys or neither. Both CLI contexts and stack props reject invalid values, including trailing newlines and versions outside the positive eight-digit format. Full normalized-template and CLI synthesis comparisons preserve all other environment, IAM, resources and outputs.

| Verification | Actual result |
| --- | --- |
| API unittest discovery | PASS: 226 tests, including 17 new binding/startup tests. |
| UI unittest discovery | PASS: 31 tests; no UI source/configuration change or restart. |
| Infrastructure compilation | PASS using installed locked dependencies. |
| Infrastructure Jest | PASS: 48 tests, including 42 new binding tests. |
| Document RAG offline | PASS: complete 17/17 cases, 374 measured checks. |
| Document comparison offline | PASS: complete 20/20 cases, 260 measured checks. |
| Document multipart offline | PASS: complete 40/40 cases, 609 measured checks. |
| CLI synthesis | PASS: omitted and valid pairs synthesize; ID-only, version-only, DRAFT and malformed cases reject. Dummy account, no lookups. |
| Source/preservation | PASS: 24 non-edited captured identities; graph nodes byte-identical to Gate A start; moderation/telemetry helper ASTs unchanged; other default-policy ASTs unchanged; HEAD unchanged. |
| Fresh AWS metadata/identity/role/corpus | PENDING_LOGIN: initial STS identity check returned `LoginRefreshRequired`; dependent release verification is not complete. |
| Publication, image build/push, Runtime change, live moderation/model calls | Not executed. |

The initial Jest/cache and CDK attempts hit Windows EPERM in the system temporary directory. Those logs are retained. Scoped workspace cache/temp settings resolved the environment restriction; all final checks passed with no dependency or machine-wide configuration change. Test logs include expected synthetic error-path messages. Offline simulations do not establish live provider quality.

Private receipts: `restaurant-finder-api/.generated/pinned-guardrail-20261013145909/`. Real configuration/locks/datasets/originals/manifests/owner warnings are preserved; tests used absent-manifest and export/live-evaluation-off process settings. P01-P04 local requirements pass; the required fresh cloud prerequisite remains pending, and P05-P08 are UNMEASURED. Do not label Gate A fully complete before closing that prerequisite.

To resume: restore `aws login --profile default`, then use the prepared read-only inspection to verify the exact numbered policy/messages, original DRAFT policy/time, Runtime/DEFAULT/image/pair/flag, active pointer and existing role permissions. No standalone ApplyGuardrail/model send is needed or authorized. Record actual results or stop on drift; do not edit real `.env` or apply a rollout while authentication is unresolved.

## 10. Prepared Gate B review package - publication not authorized

Proposed commit: `Fix immutable guardrail binding and preserve citation moderation` on `feat/document-multipart-rollout`, based on `0845b8bb4c1fa74e933470274d7272dc1561c5f0`. Review all 11 paths together, including the previously approved telemetry changes:

```text
restaurant-finder-api/src/application/orchestrator/workflow/nodes.py
restaurant-finder-api/src/config.py
restaurant-finder-api/src/infrastructure/guardrails.py
restaurant-finder-api/src/infrastructure/startup.py
restaurant-finder-api/tests/test_correctness_repairs.py
restaurant-finder-infra/README.md
restaurant-finder-infra/bin/cdk.ts
restaurant-finder-infra/lib/stacks/agentcore-stack.ts
restaurant-finder-infra/test/document-rag.test.ts
docs/HANDOFF_PRD_MULTIPART_GUARDRAIL_REPAIR.md
docs/HANDOFF_PRD_PINNED_GUARDRAIL_AND_MULTIPART_RETRY.md
```

Exclude owner `docs/HANDOFF_PRD_RUNTIME_WARNINGS.md`, every `.generated` artifact, credentials/real configuration and locks. Update the existing draft PR #1 on origin only; retain its base `feat/jev-router`, never merge or push upstream. Exact commit/CI identity remains a future measurement after publication approval.

Proposed safe PR summary: exact immutable guardrail validation and fail-closed startup; bounded content-free moderation diagnostics; accepted provenance-aware competitor definition; paired CDK configuration and regressions. Verification: 226 API/31 UI/48 infrastructure tests, 17/20/40 complete offline cases and six context synth checks. Limitations: fresh AWS preflight pending, no live application acceptance/deployment, offline results are simulated.

Release inputs: the exact reviewed source commit plus retained immutable nine-prompt manifest SHA `68e9d44e8e073d301d63fd00619ce0aefc867d66df235da9bfe809a2a25f82d9`. Do not use or rewrite the older eight-prompt worktree manifest. No prompt sync or new prompt versions by default. The Gate B image tag must be unique (`pinned-guardrail-<exact-short-commit>-<approved-UTC>-arm64`); image audit/build/push and actual ARM64 runnable registry digest occur only after approval, with baseline digest retention verified first.

The four-leaf Runtime patch and six exact acceptance inputs are defined in section 7. Build that patch from the freshly verified deployed template; do not deploy full synthesis. The target pair is `ih5xpt3qi946:1`, multipart true, plus the audited new image URI. Verify existing GetGuardrail/ApplyGuardrail permissions without widening IAM. Readiness uses metadata only; no extra warm-up requests. Trace checks retain the three-planner/12-logical-retrieval bound and source/coverage/memory gates.

Gate B review must include source publication and exact-SHA CI inspection, one audited ARM64 image build/push, one minimal reviewed Runtime update, six fresh attempted sends, four original document downloads/inspection, an owned UI restart if required, and at most one conditional rollback to the fresh image/env/UI baseline. Prior budgets/restart/rollback approvals are spent. Additional Docker recovery requires a separate concrete decision; stop before demo. Candidate/version/resources are retained.

**Current decision:** fresh read-only preflight is complete, as recorded in section 12. The Gate B review package is ready for explicit approval under AGENTS.md. No publication, image build, Runtime mutation or live send has been performed.


## 11. Read-only resume attempt

The owner's subsequent "proceed" resumed the remaining Gate A metadata verification. The 11 reviewed release hashes, 24 protected identities and HEAD were rechecked and remain unchanged. The prepared read-only inspection again stopped at STS credential resolution with `LoginRefreshRequired`, before candidate/original policy, Runtime/endpoint, corpus or role verification could run.

Local test reports remain valid on unchanged source bytes; no suite was rerun. Fresh cloud prerequisite remains PENDING_LOGIN, Gate A is not fully closed, and Gate B remains unapproved/UNMEASURED. The owner must complete `aws login --profile default` and report completion before another read-only retry. No model/moderation request, AWS resource mutation, publication, image build, deployment or UI/Docker action occurred. Original and retry authentication-error receipts are retained privately.


## 12. Gate A completion - 2026-10-14

After the owner confirmed browser sign-in was complete, the prepared read-only inspection succeeded at `2026-10-14T00:52:10.355252+00:00`. This completion record supersedes sections 9 and 11's pending-login status; their original failure receipts remain retained.

- Intended AWS account/default profile and us-east-2 verified.
- Candidate `ih5xpt3qi946:1` READY; every reviewed configured policy field and both blocked messages match the frozen request. No ApplyGuardrail or application request was sent.
- Original `sfiq3neb2co5` DRAFT READY, original policy/messages match and update time unchanged (`2026-10-06 07:33:21.865712+00:00`).
- Runtime/DEFAULT READY 15, restored image verified, multipart and pinned-pair environment keys absent. The new source has not been deployed.
- Active corpus pointer ETag remains `"d3705246c1cc2a4fd7f694bc91553e95"`; canonical pointer SHA `a157c8fd84c626672a7bb967402f12d13318ba3c72e2ff4b2c8d9485fb563d44`.
- The deployed Runtime role's `RuntimeAccessPolicy` contains regional/account guardrail wildcard Allow permissions for GetGuardrail and ApplyGuardrail. Policy digest: `6ff2a7301b03e26308a4a8c10a12716c57205775e7f0472c168818a527c80eaa`. This inspects inline permission configuration, not effective authorization from a running Runtime; live application acceptance remains unmeasured.
- All 11 release-file hashes and 24 protected identities reverified before metadata reads; HEAD unchanged. Local test counts remain 226 API, 31 UI, 48 infrastructure, 77 complete offline scenarios and six context checks on unchanged source bytes. No suite rerun or new application change was necessary.

P01-P04 and the required fresh cloud prerequisite PASS; Gate A is COMPLETE. P05-P08 remain UNMEASURED. The application still uses its original deployed guardrail/configuration. No AWS mutation, billable moderation/model/embedding call, publication, image build/push, deployment, UI/Docker action or resource deletion occurred.

Private `aws-preflight.json`, completion/preservation and cleanup receipts are retained. Remove the owned read-only helper after verification; retain source backups, test logs, synthesis assemblies, prompt artifacts, cloud resources and all prior receipts. Source publication/deployment requires Gate B approval of the prepared review package; stop before demo.


## 13. Gate B execution approval - 2026-10-14

The owner answered **"Proceed with Gate B"** to the concrete request covering publication of the 11 listed paths to the existing draft PR, one audited ARM64 image build/push, the four Runtime leaves (`image`, multipart true, guardrail `ih5xpt3qi946:1`), at most six fresh attempted acceptance requests, four original-source inspections/downloads, owned UI restart if required, and at most one conditional rollback. Stop before the demo walkthrough. Matching approved actions need no repeated generic confirmation.

The normal Docker Desktop start was accepted, but its Linux engine remained unavailable and a status check timed out. When asked about one supported restart, the owner chose **"I'll restore Docker manually"**. No restart/reset/WSL action is authorized or performed; independent publication and read-only rollback preparation can continue.

Private operation receipts are under `.generated/guardrail-rollout-20261014005846/`. Reserve each live ledger slot before sending. Previous allowances and used rollbacks do not transfer. Preserve owner warning work, credentials/configuration, locks, corpus, immutable prompts, candidate/version and historical receipts. Source/image/CI and the actual minimal change set must match before mutation; stop on drift/failure and follow the new conditional rollback rule.
