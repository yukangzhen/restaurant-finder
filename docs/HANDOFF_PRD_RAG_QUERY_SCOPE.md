# Handoff PRD: Restaurant names must not change document-question intent

**Status:** Complete for the approved local/code scope. Implementation, local checks, published feature commit, GitHub CI and artifact inspection passed on 2026-10-08. AWS Runtime rollout/live validation remain separate work.
**Prepared:** 2026-10-08 (Asia/Kuala_Lumpur).
**Baseline:** `feat/jev-router`, `d4c8784ef5e269670ae289692342c1511e865283`; clean worktree before creating this PRD.

## 1. Outcome and purpose

Fix document-type inference so a restaurant name containing an intent keyword does not affect whether RAG searches menus, policies or both. The owner is preparing an AI engineering demonstration; the result should provide an explainable resolver improvement and reproducible regression evidence.

For example, “According to Harbor Pasta Lab policy, what is the cancellation fee?” should search only that restaurant's policy documents. “According to Harbor Pasta Lab menu, how much is mushroom pasta?” should still search menus. A question explicitly asking about both a menu and a policy must retain access to both.

Deliverables: a narrow resolver change, regression tests, updated source-grounded evaluation expectations, one genuine mixed-document evaluation case, current usage documentation and verified feature-branch CI results.

## 2. Inspected code and cause

- `restaurant-finder-api/src/application/document_rag/retrieval.py`, `resolve_query`: canonicalizes and bounds the question to 1,000 characters, detects catalog names/aliases, resolves restaurant scope, then scans the whole question for menu/policy keywords.
- Menu keywords include `pasta`, `price` and `cost`; policy keywords include `policy`, `cancellation`, `fee` and `parking`. Both groups matching produces `document_type=None`, meaning no document-type restriction.
- The manifest identifies Harbor as `Harbor Pasta Lab (fictional demo)`, with aliases `Harbor Pasta Lab`, `Harbor Pasta`, and `Harbor`. Full-name policy questions therefore match both `pasta` and policy words.
- `workflow.py` resolves scope/type before an optional follow-up rewrite. The rewrite changes embedding query text but cannot change the resolved filters. Preserve that boundary.
- The 16-case dataset currently explicitly expects the full-name Harbor policy question to have no type filter. Its short-name alias case expects `policy`. `test_rag_evaluation.py` also asserts this difference. These expectations must change deliberately with the fix.
- Previous verified baseline: 125 API tests, 26 UI tests, 3 infrastructure tests, and 16 offline RAG cases. These are historical counts; record newly executed results after implementation.

## 3. Scope and approval

The owner's “okay go ahead” authorized preparing the proposed fix. Their `AGENTS.md` additionally required a reviewable PRD and sign-off before implementation. The owner subsequently approved this document with explicit **proceed**, authorizing the local edits, offline checks, feature-branch commit/push and automatic CI verification listed below.

Included:

- Resolver implementation and focused tests.
- Intentional dataset expectation changes and a mixed-document case.
- Documentation and actual execution evidence.
- Offline local API/RAG checks; inspect the existing GitHub workflow's automatically triggered API/UI/infrastructure/aggregate results and safe artifacts.
- Commit and push scoped changes to `origin/feat/jev-router` after local validation, repairing failures within this scope.

Boundaries:

- No live AWS/TypeSafe/model/embedding calls, credentials/settings changes, corpus ingestion, prompt synchronization or paid evaluation.
- No image publication, Runtime update, deployment/destruction workflow dispatch, main merge or PR creation.
- No retriever ranking, keyword vocabulary, router, model, prompt, citation, UI, memory or infrastructure redesign.
- Preserve running demo processes, existing source documents and dependency locks.

Local/GitHub completion does not deploy this runtime code. A reviewed rollout and live functional validation remain subsequent tasks.

## 4. Intended behavior

Use case-insensitive, escaped, whole-name/alias matching with the resolver's existing `(?<!\w)` / `(?!\w)` boundaries. Determine restaurant scope from the original bounded question. Obtain all matched name/alias spans from that same original question, accounting for repeated and overlapping matches. Mask the union of those spans with spaces **only in a temporary text used for document-type inference**. Do not delete all occurrences of words such as `pasta`, hardcode Harbor, or remove the venue from the embedding/answer query.

Keeping the original question means the returned `DocumentQuery.query` remains its existing canonicalized, bounded value. The temporary masking must not change clarification text, prior approved scope, explicit restaurant override or follow-up behavior. Retain the current keywords and rule: menu only -> `menu`; policy only -> `policy`; both/neither -> `None`.

| Question/context | Expected restaurant/type |
| --- | --- |
| Full Harbor name + cancellation policy | Harbor / `policy` |
| Short Harbor alias + cancellation policy | Harbor / `policy` |
| Full Harbor name + mushroom pasta price/menu | Harbor / `menu` |
| Full Harbor name + menu price and cancellation policy | Harbor / `None` |
| Full Harbor name + a neutral documents question with no intent keywords outside the name | Harbor / `None` |
| Same questions in mixed case, with possessives/punctuation or repeated venue mentions | Same scope/type as their plain forms |
| Synthetic catalog name `Policy Kitchen` + an explicit menu question | Synthetic restaurant / `menu` |
| Synthetic catalog name `Price Cafe` + an explicit policy question | Synthetic restaurant / `policy` |
| No venue, no approved scope | Clarification; no embeddings/retrieval/selector calls |
| Follow-up cancellation question with approved scope | Prior restaurant / `policy`; existing single rewrite behavior |
| Explicit Sakura question after approved Harbor scope | Sakura overrides Harbor |
| Multiple venues or an explicit unknown venue | Existing clarification behavior |
| An unrelated word containing a short alias, e.g. `Harborview` | Do not match `Harbor` as a substring |

Synthetic names belong only to in-memory test fixtures; do not modify the published catalog/corpus.

## 5. Observable completion criteria

| ID | Criterion |
| --- | --- |
| S1 | Full-name and alias policy questions resolve to `policy`; menu questions resolve to `menu`. |
| S2 | Genuine mixed intent and neutral intent return `None`; meaningful food words outside name spans remain visible to intent inference. |
| S3 | Matching handles case/possessives/repetition/overlap and non-Harbor keyword-bearing names; original canonical query text remains unchanged. |
| S4 | Missing/unknown/multiple-venue clarification, approved follow-up scope, explicit override and rewrite filter preservation retain their existing behavior. |
| S5 | A workflow test records a full-name policy vector query with `policy` and confirms no menu evidence reaches the selector. |
| S6 | The updated dataset has 17 complete passing offline cases: the original 16 with corrected full-name policy expectation plus one mixed menu/policy answer with two trusted quotations/citations. Gold prices, fees, hashes, versions and locations remain grounded in existing fixtures. |
| S7 | Scoring still rejects the full-name policy observation if its recorded filter is changed back to `None`; genuine mixed retrieval must not be forced to one type. |
| S8 | Local API/RAG checks and all four GitHub jobs pass for the actual pushed SHA. Downloaded logs/reports substantiate counts and match local RAG results. |
| S9 | Scoped docs describe current behavior, limitations, commands, exact counts/run URL and deployment status. Worktree is clean and remote commit matches. |

No benchmark or general semantic-intent-accuracy claim is required. The keyword resolver remains a small heuristic; masking catalog names does not solve every contextual ambiguity (for example `cost` alongside a policy keyword).

## 6. Files to edit

| File | Change |
| --- | --- |
| `restaurant-finder-api/src/application/document_rag/retrieval.py` | Collect/mask matched catalog-name spans for type inference while preserving scope/query behavior. |
| `restaurant-finder-api/tests/test_document_rag_retrieval.py` | Focused resolver and workflow filter/evidence regression coverage. Avoid unintentionally multiplying tests through existing `AnswerTests(RetrievalTests)` inheritance; a separate resolver test class is suitable. |
| `restaurant-finder-api/src/evaluation/datasets/document_rag.json` | Change `harbor_fee.expected.document_type` to `policy`; add one two-source mixed-intent case with separate gold/simulation fields. |
| `restaurant-finder-api/tests/test_rag_evaluation.py` | Require both full/short policy filters; add wrong-filter and mixed-case assertions. |
| `docs/CI_AND_RAG_EVALUATION.md`, `docs/DOCUMENT_RAG.md` | Explain corrected behavior and the 17-case evaluation; record new inspected results. |
| Root `README.md` | Keep the introductory dataset count and guide link current. |
| `docs/HANDOFF_PRD_CI_AND_RAG_EVALUATION.md` | Add a brief superseding link for its historical scope quirk; preserve its historical counts/run record. |
| This PRD | Record approval, actual commands/evidence and S1-S9 results. |

Use existing dependencies and `unittest`. Keep implementation small; no new classification service or generic abstraction is needed.

## 7. Execution steps after sign-off

1. **Recheck baseline.** Inspect status/branch/instructions. Preserve new user edits. Record current HEAD; do not initialize cloud clients.
2. **Add regression coverage.** Cover the behavior table, original query preservation and real workflow policy-only evidence using existing local corpus/fakes. Capture the expected current failure before applying the fix.
3. **Implement span masking.** Reuse catalog matching and existing regex boundaries. Resolve venues against original text, mask all matched spans in temporary intent text, then apply unchanged keyword/type rules. Add no model call or fallback.
4. **Update evaluation deliberately.** Correct only the obsolete full-name type expectation. Build the mixed case from the existing Harbor v2 menu price (RM32) and policy cancellation fee (RM20), requiring both exact source quotations/citations. Validate both gold quotes against their pinned versions/locations. Keep simulated selections distinct from expectations.
5. **Check failure detection.** Change a valid policy observation's `query_document_type` to `None` and require scoring failure. Verify the mixed case reports no type filter and includes both expected sources. Retain all existing malformed input, provenance and abstention checks.
6. **Run offline validation.** From the API with `UV_PYTHON=3.11`, workspace `UV_CACHE_DIR`, `PROMPT_SYNC_MODE=false`, an absent `PROMPT_MANIFEST_PATH`, `REQUIRE_PROMPT_MANIFEST=false`, `AWS_EC2_METADATA_DISABLED=true`, `AGENT_OBSERVABILITY_ENABLED=false`, `EVALUATION_ENABLED=false`, and `LOGURU_LEVEL=ERROR`, execute:

   ```powershell
   uv run --no-sync python -m unittest discover -s tests -q
   uv run --no-sync python -m src.evaluation.rag --offline --output .generated/evaluation/document-rag.json
   ```

   Record actual exit codes/counts, complete 17-case JSON/Markdown and zero failed/unmeasured checks. Maintain client-construction guards. Do not turn a test failure into a pass by weakening the expected behavior.
7. **Update docs and review diff.** Describe masked name spans with simple examples, preserve the historical CI record, and record what is locally verified. Inspect `git diff --check`; exclude ignored reports, secrets, generated infrastructure files and source documents from staging.
8. **Publish and verify CI.** Commit/push only the approved changes to `feat/jev-router`. Read the new automatic `Offline quality checks` run for the exact SHA. Require API/UI/infrastructure/aggregate success. Download bounded report/log artifacts, inspect terminal test results, and compare the RAG JSON to the local report. The existing Bash/pipefail safeguards must remain effective.
9. **Close out.** Record S1-S9 evidence, run URL, hashes, counts and any gap. Publish the final record; verify clean worktree and matching remote. Clearly state that deployed Runtime has not been updated by this offline change.

## 8. Risks and rollback

- Overly broad name removal could erase real intent. Mask only whole matched catalog-name spans and test food words outside them.
- Removing a short alias before its overlapping full name could leave `Pasta` behind. Collect matches on original text and mask the full union rather than repeatedly mutating text.
- Always preferring policy when both keywords appear would lose genuine menu-plus-policy questions. Keep the existing both/neither rule and require the mixed-case regression.
- Existing keyword limitations remain; this is a focused correction, not a general intent classifier.
- Rollback is a scoped Git revert of this fix. No corpus/index migration or cloud rollback is part of the approved work.

## 9. Open questions and next phase

Owner PRD sign-off was received and no material design question remains for this local fix.

After completion, prepare a separately reviewable Runtime rollout and bounded live functional-validation plan, including intended requests and cost boundary, before consuming model/embedding calls or changing the deployed application. Merging into `main` is also a separate action because existing deployment workflows can trigger there.

## 10. Verified execution evidence — 2026-10-08

The owner approved with explicit `proceed` on 2026-10-08. The new standalone `QueryScopeTests` class contains eight test methods so the existing retrieval/answer inheritance does not duplicate new cases. Before the resolver change, the focused run returned exit 1: eight tests with 23 failed assertions/subtests, reproducing name-induced type errors and unfiltered workflow evidence.

The resolver now collects whole-name/alias matches against the original bounded question, masks their span union in a separate character buffer, and applies the original intent keywords to that buffer. No model call was added. Scope resolution, canonical query text and rewrite filter preservation retain their existing contracts.

The workflow fixture's ingestion preparation performs six readiness queries; per-question query-count assertions correctly measure the delta after that setup, just as embedding assertions do. Selector payloads contain chunk IDs/text, so policy-only evidence is checked against the pinned manifest's actual chunk records rather than invented payload fields.

After implementation, `uv run --no-sync python -m unittest discover -s tests -q` passed **135 tests** locally. The approved offline CLI returned exit **0** with **17/17 cases**, **374 measured checks**, zero failed/missing/unmeasured checks, and JSON/Markdown reports. The new evaluator regressions reject the obsolete full-name unrestricted filter, single-type mixed filters and a missing second mixed citation. Cloud-client/import guards and existing aggregate/pipeline failure checks passed in the same suite.

The focused command `uv run --no-sync python -m unittest discover -s tests -p test_document_rag_retrieval.py -k QueryScopeTests -q` subsequently passed **all eight tests** with exit **0**. No test was skipped. Local checks used the sanitized environment in step 6 and the existing locked environment; no dependency/source-document changes were required.

### Publication and actual CI evidence

- Implementation SHA: **`ae354b09055d9a911a0567d99cf2f821ea42686d`**, message `fix: exclude restaurant names from document intent inference`, pushed to `origin/feat/jev-router`.
- Accepted run: [Offline quality checks — 37760052664](https://github.com/yukangzhen/restaurant-finder/actions/runs/37760052664), automatically triggered by `push` for that exact SHA. **API and document RAG**, **UI**, **Infrastructure**, and **Quality checks** all completed with `success`.
- Downloaded all three bounded artifacts: `offline-rag-and-api`, `offline-ui`, `offline-infrastructure`. Inspected actual terminal results: **135 API tests, OK**; **26 UI tests, OK**; **3 infrastructure tests passed**. TypeScript compilation and no-lookup dummy-context CDK synthesis steps also succeeded.
- The CI RAG JSON is identical to the local JSON: **17/17**, **374 measured checks**, zero failed/missing/unmeasured checks. Its case records independently report passing expected-type checks for full-name policy, short-alias policy and mixed-document questions; its Markdown table confirms complete success.
- `git ls-remote --heads origin feat/jev-router` matched the implementation SHA. The worktree was clean before this final documentation update. The final documentation commit is published and its remote/CI matching checked separately; a commit hash cannot be embedded in its own contents.
- Scoped diff review confirmed no changes to the original corpus/documents, prompts, dependency locks, UI/infrastructure code or workflow configuration. No deployment, corpus publication, paid model/embedding call or demo restart was performed.
- Ignored evidence lives under `restaurant-finder-api/.generated/evaluation/`: `query-scope-before.log`, `query-scope-after.log`, `query-scope-api-tests.log`, the JSON/Markdown evaluation reports, run metadata, downloaded artifacts and `query-scope-implementation-verification.json`. GitHub artifact retention is seven days; this document preserves the inspected results.

### Acceptance results

| ID | Result | Inspected evidence |
| --- | --- | --- |
| S1 | PASS | Case/alias/possessive resolver tests; both dataset policy cases require `policy`; menu cases retain `menu`. |
| S2 | PASS | Neutral and mixed resolver tests plus the mixed 17th dataset case; genuine dish/price words outside names remain effective. |
| S3 | PASS | Repeated/overlapping/reordered aliases, escaped synthetic names, case, query canonicalization/length and substring boundaries tested. |
| S4 | PASS | Clarification/unknown/multiple-venue, approved follow-up, explicit override and model rewrite filter tests passed. |
| S5 | PASS | Real workflow/fake retriever query uses Harbor/policy; each supplied selector chunk is verified as a Harbor policy chunk; one per-question embedding/query. |
| S6 | PASS | 17 complete offline cases; mixed answer has Harbor menu v2 RM32/page 1 and policy v1 RM20/lines 5-8, with two trusted citations. |
| S7 | PASS | Old `None` policy filter fails scoring; either single-type mixed filter and a missing mixed citation fail scoring. |
| S8 | PASS | Local API/focused/CLI success and exact-SHA GitHub four-job success; actual artifacts inspected and report JSON equality asserted. |
| S9 | PASS | Updated README/guides/historical link and this record; implementation pushed with clean worktree/remote match. Final documentation publication is verified separately. |

All approved local/code criteria passed. No live model-quality claim is made. The deployed Runtime still needs a separately reviewed image rollout; the working localhost demonstration has not been restarted or changed to run this fix.
