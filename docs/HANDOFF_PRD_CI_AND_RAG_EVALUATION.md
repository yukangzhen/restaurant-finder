# Handoff PRD: Automated checks and document RAG evaluation

**Status:** Approved by the owner's explicit `proceed`; implementation and verification in progress.
**Prepared:** 2026-10-08.
**Branch:** `feat/jev-router`, inspected at `0a428d026572b5d83cda53bc634ac7eea91efdfd` with a clean worktree.

## 1. Deliverable and purpose

Implement the owner's requested next steps:

1. Automatically check the API, UI and infrastructure on GitHub pushes and pull requests.
2. Add a reusable document-question dataset, deterministic evaluation checks and a readable RAG report.

The audience is the owner's AI engineering portfolio/demo viewers and future contributors. A successful result provides repeatable evidence that changes preserve routing, retrieval contracts, citations and failure behavior. It also makes explicit what has been checked with simulated dependencies and what has actually been observed from an AI response.

Keep the working local demo and deployed AWS Runtime intact. This task needs no new AWS/TypeSafe/model calls, paid embeddings, deployment, ingestion or corpus publication. GitHub-hosted CI uses runner resources under the account's existing Actions terms; do not claim those minutes are free without checking the account.

## 2. Inspected starting point

- The API's last verified offline suite passed 105 tests; the UI passed 26 tests. Do not reuse those counts as new execution results.
- `.github/workflows` contains image deployment, infrastructure deployment and infrastructure destruction workflows. There is no dedicated offline CI workflow.
- Image deployment currently runs on `main` changes or manual dispatch. Its AWS credentials and deployment path must not be used by the new checks.
- API and UI use committed `uv.lock` files. The UI pins Chainlit 2.12.0. Both applications use Python 3.11; the API requires at least 3.11.9.
- Infrastructure uses a committed `package-lock.json`, TypeScript build, Jest and CDK. The inspected Jest configuration selects `.test.ts` files; the RAG infrastructure file defines three tests.
- Existing RAG tests exercise actual parsing, generation preparation, query scope, retrieval validation, exact-quote rendering, moderation gating and SSE with in-memory stores and simulated embeddings/model responses.
- Existing `src/evaluation/test_cases.py` covers restaurant search, memory, safety and other agent scenarios. It does not define a document-RAG dataset with machine-checkable expected source IDs/versions/quotes.
- The existing AgentCore evaluation runner invokes the live Runtime and AgentCore evaluators. It is unsuitable for automatic offline CI.
- `src/evaluation/__init__.py` eagerly imports that AWS evaluation stack. A new offline evaluation entry point needs an import boundary that does not initialize those integrations. Preserve the existing public exports.
- `sample_documents/corpus-v2.json` references six fictional documents. Harbor menu v2 is RM32; retained v1 is RM28. Sakura mushroom pasta is RM36; Spice chickpea curry is RM22. Cancellation fees in the inspected policies are Harbor RM20, Sakura RM15 and Spice RM10.
- Source references already pin the generation, source hash, document version and page or line range. The current Runtime is version 11, and the working local demo is at port 8010.

## 3. Scope and authorization gate

The user requested both capabilities. The user's `AGENTS.md` additionally requires a PRD and sign-off before implementation. This document makes the proposed changes and observable completion criteria reviewable. Request one explicit **proceed** for the scope below.

### Included after sign-off

- Add the offline workflow, evaluation dataset, scorer, offline harness, unit/regression tests and documentation.
- Make a narrow lazy-import adjustment to the evaluation package if needed, preserving existing import names and live evaluation behavior.
- Run local API/UI/evaluation/infrastructure checks and controlled failure tests.
- Commit and push to the existing feature branch, causing the new push workflow to run; inspect its actual results and repair failures within this scope.
- Use GitHub read access through existing authentication to inspect jobs/artifacts. Do not print tokens or add credentials to CI.

### Boundaries

- No live agent/evaluator/model/embedding invocations, AWS changes, prompt synchronization, corpus mutation, Docker publication or Runtime update.
- No change to models, router, RAG retrieval algorithm, production prompts, browser tools, dining memory or citation UX.
- No deployment/destruction workflow dispatch, main push/merge, PR creation, branch-protection setting change or new GitHub secret/access grant.
- No leaderboard, latency/cost benchmark, broad retrieval-accuracy claim or model-based grading service.
- No public/private authentication redesign or source uploads.
- Preserve unrelated user changes and running UI processes. Do not restart the demo for a CI/evaluation-only change.

## 4. Definition of done

| ID | Observable completion criterion |
| --- | --- |
| Q1 | GitHub runs the new checks on a pushed feature commit; its recorded head SHA matches the implemented commit. |
| Q2 | API and UI regression suites pass locally and in the clean CI environment; report actual test counts. |
| Q3 | Infrastructure TypeScript build, Jest tests and CDK synthesis pass with dummy account/context and no AWS lookup/deploy. |
| Q4 | A named aggregate status fails if any required job fails or is unexpectedly skipped; the workflow has no AWS secrets/OIDC/deployment step. |
| E1 | A versioned dataset has at least 14 uniquely identified document scenarios, explicit expectations and source-grounded gold answers. |
| E2 | The offline harness invokes the real document workflow/validation/rendering with explicitly simulated dependencies; report labels identify this as offline regression. |
| E3 | Scoring catches wrong relevant facts, wrong restaurant/document/version/generation/location, missing/extra citations, unsupported answers and incorrect abstention/clarification. |
| E4 | Intentional wrong-answer and wrong-citation observations cause failing results and a nonzero CLI exit; healthy offline cases pass. |
| E5 | Reports distinguish simulated results from imported observations and state completeness/coverage. Missing cases, duplicate/unknown IDs and malformed input do not produce a green complete-suite result. |
| E6 | Report JSON and readable case summary are produced locally and in CI; safe artifacts are available for inspection. |
| E7 | Import/CLI/offline checks construct zero real cloud/model clients; existing evaluation imports remain compatible. |
| D1 | Documentation describes exact commands, source-version assumptions, scoring limits and actual CI/test evidence; the pushed commit and worktree status are recorded. |

CI supplies pass/fail status. Enforced merge/deployment blocking would require a separately approved repository/deployment policy change; do not claim this task configures that enforcement.

## 5. Evaluation design

### 5.1 Dataset and expectations

Add a focused versioned JSON dataset under `src/evaluation/datasets/`, with strict parsing. Each case contains:

- Unique ID/category, question and optional prior approved restaurant scope.
- Explicit local corpus fixture (`corpus.json` or `corpus-v2.json`), so v1/v2 expectations never depend on a live active pointer.
- Expected outcome status and restaurant/document type where applicable.
- Accepted exact source quote(s) and expected document ID/version/location for answered cases.
- Forbidden facts/claims where relevant, plus expected citation count and call/rewrite constraints for offline regression.
- A separately defined offline input scenario/selector response. Keep expected results independent of actual observed output; do not construct observations by copying the expectation object.

Compile pinned manifests/chunks from the existing sample corpus using the real local preparation code. Verify each gold quote is actually present in its expected source and source location. Derive hashes/generation/chunk IDs from those fixtures rather than typing fake hashes. Do not modify the documents to satisfy a failing expectation.

Minimum cases:

| Case | Expected result |
| --- | --- |
| Harbor menu v2 price | Answer RM32 from `harbor-menu` v2, PDF page 1. |
| Harbor menu v1 price | Answer RM28 from the explicitly selected retained local v1 fixture. |
| Sakura menu price | Answer RM36 from `sakura-menu`; no Harbor citation. |
| Spice menu price | Answer RM22 for chickpea curry from `spice-menu`. |
| Harbor cancellation fee | Answer RM20 from `harbor-policy`, correct section/lines. |
| Sakura cancellation fee | Answer RM15 from `sakura-policy`. |
| Spice cancellation fee | Answer RM10 from `spice-policy`. |
| Harbor valet parking | Insufficient evidence; no invented availability claim/citation. |
| Restaurant unspecified | Clarification; no embedding/retrieval/answer selection. |
| Unknown restaurant | Clarification, preserving scope rules. |
| Harbor/Sakura comparison | Clarification under the current single-restaurant scope. |
| Harbor policy follow-up | Reuse supplied approved Harbor scope; one simulated rewrite. |
| Explicit Sakura after Harbor | Explicit Sakura scope overrides prior Harbor scope. |
| Forged/changed selector quote | Invalid-answer outcome with no approved citation. |

Additional adversarial scorer fixtures must include a valid quote about the wrong dish from the right source. Provenance alone would pass that quote; the question-specific gold expectation must fail it. Keep these negative observations separate from the healthy dataset's expected results.

### 5.2 Offline execution and imported observations

Provide a focused CLI, for example `python -m src.evaluation.rag`:

- `--offline --output <report.json>`: run actual RAG orchestration using in-memory storage/vector records, simulated embeddings and explicitly scripted model responses. The fake vector ranking is deterministic; it is not an evaluation of Titan's semantic retrieval accuracy.
- `--observations <file.json> --output <report.json>`: score explicitly supplied normalized observations without making agent/model calls. Validate their case IDs, declared origin, outcome, text, citations and any provided retrieval evidence. Record provenance as imported/unverified unless supported capture metadata is supplied; never relabel hand-authored data as observed AI output.
- `--list-cases`: list the dataset without initializing SDKs or running evaluations.

Treat simulated selector successes as workflow regression evidence. Do not report them as real model correctness, hallucination rate or end-to-end RAG accuracy. A future real-model dataset run needs separately authorized invocation counts/budget; this task prepares the scorer for it but does not run it.

### 5.3 Deterministic checks and honest coverage

Use machine-checkable expectations appropriate to the extractive answer contract:

- Outcome status/restaurant scope matches the case.
- Required accepted source quote is present as an exact quote, allowing only the renderer's known canonicalization/escaping; a substring like `RM32` alone is insufficient.
- All attached citations match expected source records from the pinned manifest: document/version/hash/generation/chunk and PDF page or Markdown section/line range. Check extras as well as missing references.
- Insufficient-evidence/clarification/invalid outcomes have no answered claim or clickable citations. Do not infer a negative factual answer from absent evidence.
- Offline call counters enforce expected zero/single rewrite/retrieval/selector behavior. Imported observations without counters mark these checks unmeasured.
- Retrieval evidence, when provided, supports reference/evidence inclusion checks. When absent, retrieval coverage is unmeasured; never invent recall/precision or use vector distances as confidence.

Return per-check pass/fail/unmeasured plus per-case verdict, expected/observed source summary, execution mode and totals. Aggregate only checks with documented denominators. The complete offline suite must pass all required checks and cover all cases. An incomplete imported file must be clearly incomplete and return a nonzero completeness result rather than a misleading 100% success claim.

Reject empty datasets, duplicate/unknown case IDs, contradictory expectations, extra schema fields and oversize observation files. Bound JSON input, number of cases and response/evidence lengths to reasonable documented limits. Errors should show safe types/case IDs, not credentials or arbitrary provider exception bodies. Reports contain only the fictional corpus/questions and safe checks; omit session URLs, actor identifiers, raw headers and local `.env` values.

## 6. Planned files

| File | Responsibility |
| --- | --- |
| `.github/workflows/ci.yml` | API/RAG, UI, infrastructure jobs and aggregate result. |
| `restaurant-finder-api/src/evaluation/datasets/document_rag.json` | Versioned question cases and source-grounded expectations. |
| `restaurant-finder-api/src/evaluation/rag.py` | Strict dataset/observation contracts, deterministic scoring and CLI/reporting. Split a small offline helper if needed for clarity. |
| `restaurant-finder-api/src/evaluation/rag_offline.py` | In-memory corpus execution and explicitly simulated model dependencies, if separation is useful. |
| `restaurant-finder-api/src/evaluation/__init__.py` | Lazy compatibility exports so the offline module does not eagerly import live AWS evaluators. |
| `restaurant-finder-api/tests/test_rag_evaluation.py` | Dataset grounding, scorer failures, coverage, offline behavior, import isolation and CLI exit tests. |
| `docs/CI_AND_RAG_EVALUATION.md` | User-facing commands, report examples, scopes and honest interpretation. |
| Root README / `docs/DOCUMENT_RAG.md` | Concise links to checks/evaluation instructions. |
| This PRD | Actual execution evidence and acceptance status. |

Use existing dependencies and `unittest` where possible. Do not add an evaluation platform or new grader dependency merely to produce reports. Do not make runtime code depend on the evaluation harness. Reuse existing fake design without importing top-level test modules into a shipped CLI; either define small evaluation adapters or share a narrowly scoped utility safely.

## 7. Execution steps after approval

### Step 1 — Reconfirm scope and clean baseline

Read status, branch and recent commit. Inspect any new local instructions. Preserve user edits. Record the last baseline and relevant tool/lock versions. Do not call AWS to establish a baseline for an offline-only change.

### Step 2 — Make evaluation imports safe

Inspect the package's eager exports and SDK side effects. Use lazy exports or another minimal compatible approach. Verify importing the new CLI/listing cases does not load the AWS AgentCore evaluation SDK or construct cloud clients. Verify existing exported names still resolve when explicitly requested, using mocks where needed.

### Step 3 — Ground and validate the question dataset

Create at least the 14 cases above. Parse the two existing local corpus fixtures and bind accepted quotes to actual chunks/source records. Use separate expected-data and observation paths. Add tests that fail on a quote/version/location typo in the dataset itself.

### Step 4 — Implement the scorer and report contracts

Implement strict dataset/observation validation, expected outcome/quote/provenance checks, unmeasured checks and full coverage accounting. Use safe bounded parsing and documented exit codes: success only for a complete passing run; nonzero for failure, incomplete observations or invalid input. Reports must retain the execution mode and origin.

### Step 5 — Implement the offline workflow harness

Use real local generation preparation, query scope, `DocumentRetriever`, document workflow and citation rendering with in-memory adapters. Feed scripted selector/rewrite inputs that are independent of the score function. Measure fake call counters. Prevent actual S3/Bedrock/TypeSafe/AgentCore client construction, and fail immediately if an unintended live path is used. Avoid global persistent settings changes; confine temporary overrides to the run and restore them.

### Step 6 — Prove the checks catch failures

Run healthy cases and deliberately corrupted observations: wrong dish/price, wrong restaurant/source version, wrong generation/hash/page/lines, fabricated citation, unexpected extra citation, false parking claim, wrong status, missing/duplicate/unknown case. Verify failed checks and nonzero CLI exits. Run fixtures without changing deployed data or tracked corpus contents.

### Step 7 — Add the credential-free GitHub workflow

Use three independent jobs and one aggregate check:

1. **API and RAG:** Python 3.11 (satisfying >=3.11.9), verified pinned uv tool version, locked API dependency sync, `unittest discover`, dataset validation and complete offline evaluation/report.
2. **UI:** matching Python/uv, locked UI dependency sync and `unittest discover`.
3. **Infrastructure:** Node 22, `npm ci`, `npm run build`, `npm test -- --runInBand`, and `npx cdk synth --all --no-lookups` with dummy `CDK_DEFAULT_ACCOUNT=123456789012`, region `us-east-2` and explicit dummy image context. Never deploy or fetch real account context.
4. **Quality checks:** use `always()` and inspect all required job results; fail on failure/cancellation/unexpected skip, pass only when all succeeded.

Trigger on ordinary `push` and `pull_request`, with sensible branch coverage and no secret-bearing `pull_request_target`. Set `permissions: contents: read`, job timeouts and concurrency cancellation of superseded runs. Do not add an OIDC token permission. Validate official action/tool versions, pin third-party actions to inspected full commit SHAs and label the release in a comment. Set checkout `persist-credentials: false`.

Use per-project dependency caches keyed by the relevant lockfile; exclude `.env`, AWS credentials, `.files`, CDK output and local generated snapshots. Start with the verified uv release already used by the project only if its official release can be confirmed; otherwise choose and document a supported pinned version without changing dependency resolutions.

CI must use a sanitized environment, no project `.env` or production prompt manifest. Set `PROMPT_SYNC_MODE=false`, `REQUIRE_PROMPT_MANIFEST=false`, an absent explicit prompt-manifest path, `AWS_EC2_METADATA_DISABLED=true`, and disable cloud telemetry/live evaluation by their real settings. Inject RAG test/harness dependencies explicitly. Do not use invented setting names as protection. A configuration flag alone is not proof of zero live calls; import/client guards and tests supply that evidence.

Write a readable summary to `GITHUB_STEP_SUMMARY`, preserving real exit codes. Upload only the bounded fictional RAG report and concise test logs using a short retention period; do not upload broad working directories or originals/private state. Do not use `continue-on-error` to turn failing tests green.

### Step 8 — Reproduce CI locally

Run the exact relevant commands with sanitized environment values and existing locked environments. The approved task authorizes regression/scorer/CLI checks. Dependency downloads may need network access; they must not consume AWS calls. CDK synth may write ignored local build output. If it requests a lookup, stop that command and fix the offline context rather than supplying AWS credentials.

Record actual API/UI/evaluation test counts, dataset case counts, infrastructure test counts and commands. Check lazy-import compatibility and controlled-failure exit codes. Review generated TypeScript output so it does not become an unrelated tracked change.

### Step 9 — Publish and inspect the real GitHub run

Review the diff and ignored artifacts; commit/push only scoped changes to `origin/feat/jev-router`. The existing main-only deployment push triggers should not run for this branch. Do not dispatch them.

Inspect the automatically triggered CI run for the exact pushed SHA with existing authenticated GitHub tooling. Read job results and the safe report artifact. Prefer bounded waits and useful work between checks. Fix workflow/platform failures in scope and inspect the resulting new run. Do not claim GitHub CI passed from local test success alone. If GitHub Actions is unavailable/disabled or account limits block execution, record that specific gap and request only the needed user action; complete unaffected local work first.

### Step 10 — Close out with evidence

Update the docs and this PRD with exact commands, counts, test/failure evidence, run URL, implementation SHA, remote verification and Q1–D1 results. Explicitly distinguish offline regression success from measured live model quality. Verify clean scoped worktree and matching remote commit. No Runtime image publication is necessary for an offline evaluation/CI change.

## 8. Risks, limits and rollback

- Offline fixtures can catch contract/orchestration regressions but cannot measure current Jev/Haiku/Titan behavior. Report this limitation prominently, even if every fixture passes.
- Exact gold answers fit this extractive fictional demo. They are not a universal semantic grader for paraphrases or arbitrary documents.
- Current corpus fixtures determine expected versions; changing that corpus later requires intentional review of the dataset, rather than silently refreshing expectations from a new live pointer.
- Lazy export changes must preserve existing live evaluation imports; unit tests cover compatibility without invoking those services.
- Existing workflow completion status does not enforce protected-branch merging or coordinate deployment ordering.
- Rollback is a normal scoped Git revert of the new CI/evaluation commits. This feature changes no AWS resource or live corpus to roll back.

## 9. References and open questions

Inspected official guidance: [GitHub Python build/test workflows](https://docs.github.com/en/actions/tutorials/build-and-test-code/python), [uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/), and [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use). Inspect action release identities during implementation rather than guessing SHAs.

The owner supplied the explicit `proceed` required by `AGENTS.md`. No implementation code, workflow, cloud resource or test execution was changed/performed while preparing the original proposal.

## 10. Implementation findings

The initial dataset run found the existing keyword resolver considers `Pasta` in the full venue name `Harbor Pasta Lab` a menu keyword. Its full-name policy question consequently has no type filter, although the selected answer correctly cites policy. The full-name case remains in the dataset and expects that current query behavior while requiring the correct policy quote. A separate short-alias `Harbor policy` case requires policy-only filtering. This preserves the approved retrieval-algorithm boundary and documents the efficiency quirk instead of claiming policy filtering worked for both forms.

The dataset contains 16 cases, including separate forged-ID and changed-quote cases. Execution results, GitHub evidence and final acceptance status will be recorded after verification.

### Repairs discovered by inspecting CI artifacts

The first Actions run, `37749612011` at `13a5a769447675140127feb6f6d9359da5731133`, reported successful jobs. Downloading its test artifact revealed the API suite actually had one error. That run is **not accepted as successful verification**: the test pipeline ended in `tee`, masking the failing command's exit code. Each project job now explicitly selects Bash and each logged test step sets `set -euo pipefail`. A regression test executes the actual three step scripts with successful/failing substitutes, without injecting shell flags from the test, and requires correct exit propagation.

The underlying test error was platform-specific path validation: Linux's `Path` treated the prohibited Windows path `C:/outside.pdf` as relative and attempted to read it. A narrow parser repair now rejects Windows drive/root-qualified paths on either platform before accessing source bytes. Existing traversal tests now also cover drive-relative, backslash, UNC and POSIX absolute forms. This is an offline parser/platform repair under execution step 9; source contents, retrieval algorithms and deployed resources are unchanged.

### Owner-approved Actions setting change

The first implementation push could not trigger CI: an authenticated read of the repository's Actions permissions returned `enabled: false`. Local work and publication were completed before requesting the additional setting authorization. The owner explicitly answered **Enable Actions and verify CI**.

Actions was enabled with `allowed_actions: selected`. The verified allowlist has 15 exact action references: the five pinned official action commits used by this CI plus the references already present in the existing deployment/destruction workflows. Broad GitHub-owned/verified-action allowances remain false; existing SHA-enforcement settings were not changed. This preserves the existing workflows' permitted references without dispatching them or modifying secrets. Ignored before/after settings records are under `.generated/evaluation/`. Future action-reference updates require updating that allowlist.

The API's `.python-version` hints at the older exact patch 3.11.9, while the tested local interpreter is 3.11.16 (UI: 3.11.15). Both meet project requirements. CI sets `UV_PYTHON=3.11` so uv uses the selected supported minor runtime rather than fetching the older exact patch. Locked dependencies are unchanged.
