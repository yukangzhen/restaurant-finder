# Public repository readiness and verified setup instructions

Status: local implementation and offline validation completed on 2026-10-22. The owner subsequently approved section 10 publication and merge after CI passes; execution is authorized. Final publication evidence belongs to PR #1 and its exact-head GitHub checks.

## 1. Outcome and audience

Prepare `yukangzhen/restaurant-finder` for readers arriving from the accepted LinkedIn demonstration. A new reader should understand the author's contributions, find the code shown in the demonstration, reproduce credential-free checks, and follow an accurate, explicitly paid AWS setup path in their own account.

This is a portfolio demonstration, not an operated production service. Preserve upstream attribution, the accepted final video, application behavior, existing local environment files, and unrelated working-tree changes.

## 2. Inspected baseline

Read-only review on 2026-10-22 established:

- The GitHub repository is already public. Its default branch is `main`, at `ecd3cc53274d59d215235f7e2ab08e274777de68` (the initial commit).
- The local/demo branch is `feat/document-multipart-rollout`, at `3b116a0133d1e0f5318f1add2d8ed0d2e4daa44f`.
- Draft PR #1 targets `feat/jev-router`, not `main`. It therefore does not currently bring the demonstrated implementation to the public default branch.
- GitHub runs 39541597336 and 39541595559 completed successfully for the demo head on 2026-10-21. These are existing CI results, not tests run during this review.
- All four listed GitHub workflows are active. The image and infrastructure workflows currently have push-to-main deployment triggers. Configured secret values/names, branch protection and repository settings requiring authentication remain unverified because no usable noninteractive Git credential was available.
- The root README has an incorrect clone-directory example, bare Python/CLI commands after `uv sync`, invalid sequential sibling-directory changes, duplicated setup paths, stale Runtime status claims, and incomplete current RAG/source-viewer configuration.
- CDK constructs three stacks (ECR, RAG, AgentCore). Runtime RAG is enabled by CDK, while multipart, follow-ups and real-source support default off; hybrid defaults to vector. The README does not provide a complete corpus activation path or explain this difference from the recorded demo.
- The infrastructure README still describes generated Cognito/placeholder-tool directories absent from the actual implementation. The API README describes only the synthetic RAG version. UI packaging declares a README that is not tracked.
- The current Docker ignore list excludes selected generated directories but leaves other private `.generated` working directories eligible for `COPY . .`. The pinned prompt manifest is the generated build asset that must remain available.
- Root Git ignore rules do not cover every `.env.*` variant. No non-example environment file is tracked at the inspected head.
- A bounded redacted scan of 190 tracked files found no matches for the checked credential patterns. A high-confidence-pattern scan of 44 locally reachable commits also found no matches. This does not establish the absence of all secrets or inspect inaccessible remote-only history.
- Neither this repository nor upstream currently exposes a GitHub-detected license; upstream's license endpoint returns 404. Do not add an invented license or imply permission to relicense inherited work.
- Real restaurant originals used in the recording are privately prepared artifacts, not a complete reproducible corpus committed to Git. Fictional fixtures are committed. Discovery can return restaurants outside the document catalog.
- The previously recorded early Source 2 viewer mismatch remains an unresolved product issue; the accepted video correction was editorial. Do not describe that edit as an application repair.

Evidence: GitHub repository/commit/PR/workflow/run API responses; tracked source, configuration, Dockerfile, ignore files, dependency manifests, deployment CLIs and documentation. No AWS calls, application requests, builds or test executions were made for this review.

## 3. Definition of done

1. The README accurately explains what the demonstration does and what this fork adds, with credit and a small architecture diagram.
2. The documented clone URL, paths, CLI arguments, environment names, stack outputs, region, ports and feature defaults agree with inspected code.
3. There are clearly separate instructions for offline inspection/checks, a local UI connected to AWS Runtime, and an optional locally running API that still uses AWS services.
4. A single detailed setup guide explains the complete first-deployment sequence, prompt manifest, secrets, corpus activation and source viewing without relying on the author's account or ignored/private files.
5. Fictional fixtures provide the reproducible document path. The real-restaurant recording is labeled as a separately prepared corpus; no promise that unrestricted discovery always has PDF coverage.
6. Paid/mutating commands are labeled and are not executed during this task. Destruction instructions explain retained resources and potential continuing charges.
7. Normal Docker build context excludes private generated material while allowing only the required generated prompt manifest. Git ignores local environment variants while retaining examples.
8. Deployment cannot start merely because the public release is merged: proposed local workflow edits make image/infra deployment manual-only. No workflow is dispatched.
9. Documentation links and command contracts pass local checks. Existing offline tests/evaluations and infrastructure checks are run only under the local approval below, with cloud calls disabled. Report actual results and any limitation.
10. Publication remains a separate gate. The final release must put the demonstrated implementation and reviewed docs on the public default branch; local preparation alone is not public completion.

## 4. Scope and exclusions

Local implementation approval covers these paths:

- `README.md` — replace historical rollout narration with the current portfolio overview, accurate features/limits, quick setup entry points and verified evidence links.
- `docs/SETUP.md` (new) — canonical setup guide with explicitly labeled PowerShell commands, working-directory boundaries and paid AWS operations.
- `docs/DOCUMENT_RAG.md` — reconcile current source types/flags, limits and ingestion instructions; label historical records rather than implying old Runtime versions remain current.
- `docs/CI_AND_RAG_EVALUATION.md` — list all five offline evaluations and current workflow behavior; distinguish recorded CI from fresh checks.
- `restaurant-finder-api/README.md` — current API entry point, AWS dependencies and links to the canonical guide.
- `restaurant-finder-ui/README.md` (new) — local/AWS connection modes, ports, credentials, source bucket/read permissions and identity limits.
- `restaurant-finder-infra/README.md` and `restaurant-finder-infra/README` — replace obsolete scaffolding with accurate stack/configuration descriptions and a pointer to the canonical instructions.
- `.gitignore` and `restaurant-finder-api/.dockerignore` — environment/build-context boundaries described above; preserve the currently asserted real-source exclusion.
- `.github/workflows/deploy-image.yml` and `.github/workflows/deploy-infra.yml` — remove automatic push triggers only; keep manual dispatch and existing deployment behavior. Explicitly document that the infrastructure workflow does not reproduce all recorded demo opt-ins; recommend reviewed manual CDK deployment for those settings.
- `restaurant-finder-api/.env.example` and `restaurant-finder-ui/.env.example` — comments/placeholders only where needed to make the guide and current settings agree; no real account identifiers or credentials.
- `restaurant-finder-api/tests/test_public_repository_contracts.py` (new) — bounded offline assertions for the generated-file Docker boundary, environment-example exceptions and manual-only deployment triggers. Adapt an existing relevant assertion only if the approved ignore change requires it, and record the exact path first.
- This PRD — execution evidence and remaining decisions.

No feature work, dependency upgrades, benchmark, license invention, source redistribution, broad IAM/CDK changes, source-viewer product repair, deletion/history rewrite, AWS deployment/query/inference, Docker action, video edit or LinkedIn posting. Preserve existing PRDs and unrelated changes. Do not delete historical runbooks as a cosmetic cleanup.

## 5. Execution plan after local approval

### A. Establish reproducible instructions

1. Record the starting branch, head and working-tree status. Work on the existing branch unless isolation is necessary to preserve unrelated changes; do not reset or stage unrelated paths.
2. Build a command checklist from actual source: `src/config.py`, UI environment reads, CDK context validators/outputs, dependency locks, prompt sync/validation and ingestion argument parsers.
3. Use `git clone https://github.com/yukangzhen/restaurant-finder.git` and directory `restaurant-finder`. Until publication, explicitly identify the feature branch needed for the demo implementation; remove that temporary note only after default-branch verification.
4. Provide an offline path requiring no AWS credentials: locked dependency installation, tests and all five simulated evaluations. Explain that dependency downloads need network access even though the checks do not need cloud services.
5. Write one first-deployment path: check AWS identity/region/model access; install locked infra/API dependencies; bootstrap only if required; deploy ECR; sync and validate nine prompt versions using the project environment; build/push a unique ARM64 image with a clean context; review/deploy RAG/AgentCore with explicit feature contexts; record outputs; populate SearchAPI/Jev secrets; explicitly prepare and activate the fictional corpus; configure/start the UI.
6. Check the exact Jev secret format against its loader. Explain that prompt sync writes AWS resources; it is separate from startup. Explain guardrail automatic setup versus an explicit immutable ID/version pair, without copying the author's pair.
7. Make RAG prerequisites concrete: runtime bucket/index/active key; Titan V2 access; local flags versus CDK flags; dry-run versus paid publish; UI bucket and `s3:GetObject`/version access; current source-format and corpus bounds. Do not instruct readers to prepare the recorded private real-source corpus from files absent from Git.
8. Use `uv sync --locked --extra local-aws` and environment-qualified execution consistently for AWS-assisted local use. Use separate terminal/working-directory blocks for API and UI. Verify the supported local entry point from locked installed package metadata before documenting its port; do not launch the real AWS-backed application during this review.
9. Describe the local UI as a client of the cloud-hosted backend, not evidence that the UI itself is cloud hosted. Note credentials, identity/authorization and trace privacy limits for a shared public service.
10. Correct cleanup: CDK teardown does not remove retained ECR/S3/vector/log data and is not a guarantee of zero charges. Avoid presenting a destructive command as an ordinary verification step.

### B. Apply the small repository fixes

1. Tighten Docker exclusions with a tested `.generated` allowlist that retains the prompt manifest and excludes private working receipts/originals. Retain root secret exclusions and existing real-source pattern.
2. Ignore all local `.env.*` variants except deliberately tracked examples. Check Git ignore behavior with synthetic names; never read or modify real `.env` values.
3. Make image and infra deployment manual-only locally, preventing publication-triggered deployment. Keep offline CI on push/PR and the existing destruction workflow unchanged.
4. Align component READMEs and root navigation with the canonical setup guide. Avoid undocumented Makefile lint commands that require missing Ruff dependencies; use working locked checks instead of adding a dependency upgrade.

### C. Verify locally

1. Check every local Markdown link/path, setup module and argument against tracked files. Validate shell syntax and directory transitions; label placeholders that readers must replace. Cross-check defaults and stack output names programmatically where practical.
2. Run the bounded repository contract tests, API/UI suites, five offline document evaluations, TypeScript compilation/Jest and a no-lookups CDK synth with dummy account/image context. Use an isolated environment without the real `.env`, prompt manifest or AWS credentials; do not import/start the live app as a command check. If locked dependencies are unavailable, report the exact gap rather than install different versions silently.
3. Inspect a context inventory/ignore check using harmless temporary fixtures instead of Docker. Require the manifest to be eligible and private generated examples to be excluded. This is not proof of a newly built image; report it accurately.
4. Re-run redacted credential-pattern and tracked-file checks plus `git diff --check`. Inspect the final diff for real credentials, private original bytes, account-specific instructions and unrelated changes.
5. Produce a command verification ledger: statically checked, executed offline, or requires separately approved AWS validation. Do not claim that a fresh-account end-to-end deployment has been executed.

## 6. Separate publication gate

After local completion, show the exact changed paths and verification results. Prepare a concrete publication packet that:

1. Explains the existing PR's feature-branch base and proposes one reviewed route to `main`, without silently merging/retargeting the draft.
2. Includes manual-only deploy workflow changes before any public default-branch update.
3. Requests authentication only if publication still lacks a usable credential; do not expose tokens or store them in repo files.
4. Lists the exact push, PR/base/title changes, merge strategy and optional repository-description update for approval. No AWS secrets or Actions credentials will be added.
5. Observes resulting offline CI, checks the final default-branch SHA and anonymously reads the rendered public README/source links after publication.

No publication, merge, branch-settings change or workflow dispatch is authorized by approval of local preparation alone.

## 7. Open issues and truthful limits

- Upstream licensing/redistribution permissions are not established by public visibility. Preserve attribution and do not add a license covering inherited work without appropriate authority. No legal conclusion is being made by this audit.
- The known early source-viewer mismatch is outside this documentation/configuration scope; record it as an unresolved limitation rather than claim that editing the video fixed it. A product repair requires a separate scoped plan.
- Branch protection, configured Actions secrets and authenticated repository policies cannot yet be verified. Public API checks establish repository visibility, default SHA, open PR and observed CI only.
- Fresh-account setup, currently deployed Runtime state, third-party model availability and live source viewing will not be certified by static/offline checks. A separate bounded AWS validation approval would be required.
- Do not claim a measured Jev latency/cost improvement or general RAG accuracy from simulated regression checks.

## 8. Approval requested

Approve local documentation/configuration corrections and the offline validation in sections 4–5. This permits no GitHub publication, AWS calls, Docker build/restart, paid inference or video changes. A separate concrete publication decision follows the reviewed local result.

## 9. Local execution and verification - 2026-10-22

The owner approved local cleanup and offline checks. Implementation is complete in the 16 paths listed below; existing changes to the connected-demo PRD and the two unrelated untracked PRDs were preserved and are excluded from this publication packet.

### Changes completed

- Replaced the root README's stale rollout narration with current architecture, contributions/attribution, feature defaults, branch status, reproducible setup links and explicit known limitations.
- Added the canonical PowerShell setup guide, with correct clone/directory commands, environment-qualified execution, separate terminals, all three stacks, nine-prompt synchronization, ARM64 image flow, correct provider-secret formats, explicit sample-corpus activation, source-viewer permissions, local/cloud distinction and retained-resource cleanup.
- Reconciled API/UI/infrastructure guides, document engineering and all five offline evaluator instructions. Added the previously missing UI README declared by its package metadata.
- Broadened Git environment exclusions while retaining examples. Docker now excludes all generated working files except the required prompt manifest; the parent remains traversable for the explicit inclusion.
- Removed push triggers from image/infra deployment workflows only. Manual dispatch bodies, offline CI and destruction workflow are unchanged. These edits are local, not yet applied to GitHub.
- Added four bounded offline repository contract tests. No application behavior, dependency version, video or cloud resource changed.

### Verification ledger

| Check | Observed result |
| --- | --- |
| API unit/regression suite | 349 tests, all passed; includes the four new repository contracts. Expected failure-path diagnostic messages appeared within passing negative tests. |
| UI unit/regression suite | 52 tests, all passed. |
| Infrastructure TypeScript compilation | Passed. |
| Infrastructure Jest suite | 57 tests, all passed. |
| CDK synthesis | All three stacks synthesized using dummy account/image, no lookups; passed. |
| Single-document evaluation | 17/17 cases; passed; 374 measured checks. |
| Comparison evaluation | 20/20 cases; passed; 260 measured checks. |
| Multipart evaluation | 40/40 cases; passed; 609 measured checks. |
| Follow-up evaluation | 24/24 conversations; passed; 1,147 measured checks. |
| Retrieval evaluation | 24/24 cases, 57 variants; passed; 1,070 measured checks. |
| Sample-corpus dry-run | Six documents, 14 chunks; reported zero AWS calls. |
| Current public-guide local links | 48 targets/anchors checked; no missing targets/anchors. |
| PowerShell syntax | 17 blocks parsed with the native PowerShell AST parser; no syntax errors. This did not execute AWS commands. |
| Documented Python command modules | All nine module paths exist. CLI flags, settings, stack output names, secret formats and server port checked against source/installed SDK. |
| Installed Python dependencies | 175 API and 144 UI distributions compared with their respective lockfiles; no version mismatches after standard package-name normalization. |
| Installed infrastructure dependencies | 335 installed package versions matched package-lock; no required lock entries missing. |
| Ignore contracts | Generated-file allowlist and synthetic environment variants/examples passed. No Docker build was run; this is a bounded ignore-pattern/structure check, not a newly built-image audit. |
| Redacted scan | No checked high-confidence AWS/GitHub/private-key patterns found in tracked files plus the four new public paths. Not a universal secret absence guarantee. |
| Whitespace check | `git diff --check` passed. Git's local LF/CRLF notices are not test failures. |

### Isolation and limitations

API/UI checks ran against a disposable source copy without real `.env` or generated prompt metadata, with non-secret dummy credentials, nonexistent credential/config paths, disabled telemetry/evaluation and external Python sockets/DNS blocked. Node infrastructure checks used dummy context with external connection/DNS blocking and CLI telemetry/version checks disabled. No application server, live inference, AWS query or Docker command was run.

The original API virtual environment points to a temporary Python base that cannot load its standard library. It was left unchanged. Validation used the working UI Python 3.11.15 interpreter with the installed API dependency directory first on the import path; those distribution versions were individually checked against the API lockfile. UI validation used that interpreter's own locked packages. A fresh `uv sync --locked --offline` attempt in the disposable copy failed before installation because the default uv cache path was inaccessible; no cache permissions or local environment were changed. Therefore fresh dependency installation, `npm ci`, and a fresh-account AWS deployment are not newly certified here.

Temporary source copies, generated reports, guards and parse scripts are removed after the evidence above is captured. Existing user environments and unrelated generated data are retained.

The broader historical-document scan found an old machine-local, line-suffixed link in `HANDOFF_PRD_COMPARISON_PUBLICATION_AND_ROLLOUT.md`. That historical file was outside the approved edit scope and remains unchanged. All links in the seven current public guides resolved. Upstream licensing, the early viewer mismatch and authenticated repository settings remain the limitations described in section 7.

## 10. Publication packet - owner approved on 2026-10-22

### Exact paths (16)

1. `README.md`
2. `docs/SETUP.md`
3. `docs/DOCUMENT_RAG.md`
4. `docs/CI_AND_RAG_EVALUATION.md`
5. `restaurant-finder-api/README.md`
6. `restaurant-finder-ui/README.md`
7. `restaurant-finder-infra/README.md`
8. `restaurant-finder-infra/README`
9. `.gitignore`
10. `restaurant-finder-api/.dockerignore`
11. `.github/workflows/deploy-image.yml`
12. `.github/workflows/deploy-infra.yml`
13. `restaurant-finder-api/.env.example`
14. `restaurant-finder-ui/.env.example`
15. `restaurant-finder-api/tests/test_public_repository_contracts.py`
16. `docs/HANDOFF_PRD_PUBLIC_REPOSITORY_READINESS.md`

### Proposed route to the public default branch

1. Recheck the remote head and PR state, resolve authentication if necessary, and inspect the full feature-to-main diff (including earlier Jev/RAG implementation) before any mutation. Stop for an unexpected remote divergence or unrelated content. Do not force-push or rewrite history.
2. Prepare the public-release version of the branch-status text and clone instructions in the reviewed README/setup guide: use `main` once merged, and do not leave a statement that `main` is still the initial version in the merged release. This is the only additional documentation adjustment proposed for publication.
3. Commit only the 16 listed paths on `feat/document-multipart-rollout`, excluding all pre-existing unrelated PRD changes; push that branch.
4. Retarget existing draft PR #1 from `feat/jev-router` to `main`, with title `Restaurant Finder: Jev routing, document RAG and AWS demo`. Update its description to explain attribution, the complete feature scope, manual-only deployment, verification results and known gaps. The PR's scope therefore includes earlier feature commits, not only this cleanup.
5. Observe the automatic offline CI runs for the exact updated head. Verify all three jobs, aggregate status and all five reports; do not dispatch any deployment/destruction workflow. If CI fails, inspect/report the failure before proposing any out-of-scope fix.
6. Once reviewed and green, mark the PR ready and squash-merge it into `main`, keeping the feature branch. Verify the resulting default-branch SHA and anonymously inspect the public README/source/setup links. The merged workflows must remain manual-only; no AWS credentials will be added or changed.
7. Record final public links and actual CI results. No repository-description change, branch protection change, license addition, video upload, AWS action or LinkedIn post is included.

The owner separately approved this exact packet after reviewing the local result: commit/push the 16 paths, retarget PR #1 to main, verify offline CI, and squash-merge once green. That authorization excludes AWS operations, workflow dispatch, credential changes, video changes and LinkedIn posting. The local-only approval was not used as publication authorization.

### Execution baseline

Before mutation, the authenticated GitHub identity was verified as `yukangzhen`; no credentials were printed or stored in repository files. Remote main remained `ecd3cc53274d59d215235f7e2ab08e274777de68` and the feature branch remained `3b116a0133d1e0f5318f1add2d8ed0d2e4daa44f`. GitHub reported the feature branch 43 commits ahead and zero behind main, with 160 changed files, matching the accumulated Jev/RAG release. Draft PR #1 remained open with its original feature base. There was no unexpected remote divergence.

The release version removes temporary feature-branch instructions from the README/setup guide. Publication is conditional on successful exact-head CI; final run/merge links and results are recorded in PR #1 and the execution response rather than implied by this pre-publication checkpoint.
