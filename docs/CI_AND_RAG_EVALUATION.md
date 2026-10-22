# Automated checks and document evaluation

## What runs on GitHub

The [offline workflow](../.github/workflows/ci.yml) runs on pushes and pull requests:

| Job | Checks |
| --- | --- |
| API and document RAG | Locked dependencies, API regression suite and all five offline document evaluators. |
| UI | Locked dependencies and UI regression suite. |
| Infrastructure | Locked npm dependencies, TypeScript compilation, Jest and dummy-account CDK synthesis with no lookups. |
| Quality checks | Requires success from all three jobs; failed, skipped or cancelled jobs do not pass. |

Actions are pinned to commit SHAs; jobs have timeouts and read-only repository permissions. The workflow needs no AWS/TypeSafe credentials, prompt synchronization, deployments or model calls. Reports/logs are allowlisted artifacts with seven-day retention; private originals, environment files and cloud state are not uploaded. Bash `pipefail` preserves failures when logging through `tee`.

Image/infra deployments are separate **manual-only** workflows in this revision. Offline CI success is not a deployment gate enforced by branch protection; authenticated repository policy must be reviewed separately. Repository Actions allowlists may need an owner update when an action SHA is changed.

## Reproduce locally

Use the exact fresh-checkout/environment instructions in [Setup: offline checks](SETUP.md#2-offline-checks), not an AWS-configured working directory. Install with `uv sync --locked --python 3.11`. Each project has its own environment. API/UI suite command, from the respective directory:

```powershell
uv run --no-sync python -m unittest discover -s tests -q
```

From the API directory, with the offline environment established:

```powershell
uv run --no-sync python -m src.evaluation.rag --offline --output .generated/evaluation/document-rag.json
uv run --no-sync python -m src.evaluation.document_comparison --offline --output .generated/evaluation/document-comparison.json
uv run --no-sync python -m src.evaluation.document_multipart --offline --output .generated/evaluation/document-multipart.json
uv run --no-sync python -m src.evaluation.document_followups --offline --output .generated/evaluation/document-followups.json
uv run --no-sync python -m src.evaluation.document_retrieval --offline --output .generated/evaluation/document-retrieval.json
```

Infrastructure commands are `npm ci`, `npm run build`, `npm test -- --runInBand` and the explicit dummy-image `cdk synth --all --no-lookups` in Setup. Do not substitute an authenticated deploy/diff for offline synthesis.

## Dataset scope

| Evaluator | Frozen scope | What real code is exercised |
| --- | --- | --- |
| `rag` | 17 single-document cases | Scope resolution, retrieval contracts, quotations, provenance, rendering and safe failure. |
| `document_comparison` | 20 cases | Two-venue workers, evidence contracts, fixed-point price arithmetic and source order. |
| `document_multipart` | 40 cases | Structured-plan validation, task coverage, bounded workers and complete menu/policy records. |
| `document_followups` | 24 conversations, 28 variants, 63 turns | Parent graph, approved context, deterministic continuations, clarification and fresh evidence. |
| `document_retrieval` | 24 cases, 57 variants | BM25/RRF ranking, candidate verification, provenance and retrieval budgets. |

The fixtures are fictional and separate from real-restaurant demonstration documents. Models, embeddings, semantic vector results, AWS storage, moderation and durable memory are simulated. Expected answers/provider scripts are separate fields; real workflow/validation code executes rather than copying gold into output.

This establishes deterministic functional regression for the curated dataset. It does **not** measure live routing/selector accuracy, semantic recall, hallucination rate, general restaurant coverage, authentication, throughput, latency or savings.

## Reports and failure interpretation

Each evaluator writes JSON plus a same-name Markdown summary. Exit codes are **0** (complete pass), **1** (failed/missing checks) or **2** (invalid input/execution failure). Check the current exit status and report timestamp/path; an old file is not evidence for a failed new invocation.

Reports distinguish `offline_regression` / `simulated_dependencies`, case completeness and measured/unmeasured checks. They omit raw questions, quotations, provider bodies, identities and credentials. Missing, duplicate or unknown cases cannot count as complete success. GitHub status without the matching SHA/report is not evidence for a different revision.

The RAG scorer also supports normalized imported observations via `--observations`. Declaring `origin=recorded` does not authenticate their origin: imported observations remain `imported_unverified`. The offline CLI deliberately has no live invocation option. Existing AgentCore live evaluators (`runner`, `on_demand`, `online`) are separate, potentially billable tools.

## Existing evidence

Demo head `3b116a0133d1e0f5318f1add2d8ed0d2e4daa44f` passed [push CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39541595559) and [PR CI](https://github.com/yukangzhen/restaurant-finder/actions/runs/39541597336) on 2026-10-21. Those existing runs predate the local README/configuration cleanup; do not label them as its fresh CI.

Earlier [CI implementation](HANDOFF_PRD_CI_AND_RAG_EVALUATION.md), [follow-up](HANDOFF_PRD_DOCUMENT_CONVERSATION_FOLLOWUPS.md), [hybrid retrieval](HANDOFF_PRD_HYBRID_DOCUMENT_RETRIEVAL.md) and [complete-record acceptance](HANDOFF_PRD_SINGLE_RECORD_PUBLICATION_AND_ROLLOUT.md) records retain historical results. The current [readiness record](HANDOFF_PRD_PUBLIC_REPOSITORY_READINESS.md) reports the cleanup's actual local validation and gaps.
