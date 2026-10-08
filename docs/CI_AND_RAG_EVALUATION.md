# Automated checks and document RAG evaluation

## What runs on GitHub

The `Offline quality checks` workflow runs on pushes and pull requests:

| Job | Checks |
| --- | --- |
| API and document RAG | Locked dependencies, API unit/regression suite, complete offline RAG dataset. |
| UI | Locked dependencies and UI regression suite. |
| Infrastructure | Locked npm dependencies, TypeScript compilation, Jest and CDK synthesis with dummy context/no lookups. |
| Quality checks | Passes only when all three jobs succeed; failure, cancellation and skipped jobs do not pass. |

The workflow needs no AWS/TypeSafe credentials, model calls, prompt synchronization or deployments. It has read-only repository permission, pinned action commits, job timeouts and per-project dependency caches. It publishes the RAG case table in the job summary and keeps only the fictional evaluation report and concise test logs as artifacts for seven days. Original documents, `.env`, private session files and AWS state are not uploaded.

Logged test commands explicitly enable Bash `pipefail`, so piping output through `tee` preserves test failures. Regression tests verify this behavior for all three jobs as well as the aggregate check. Corpus source paths must be relative on Windows and Linux; the parser rejects drive-qualified, rooted and out-of-directory paths before reading source files.

This supplies a status check. Enforcing merge/deployment ordering through protected branches or deployment gates is separate repository policy, not configured here. The existing main-only deployment workflows remain separate.

The owner approved enabling previously disabled Actions for this repository. Its selected-action allowlist permits the pinned CI action commits and the references already used by existing workflows. When changing an action reference, update that allowlist deliberately; a new SHA/tag is not automatically permitted.

## Run the document evaluation locally

From `restaurant-finder-api`, use the locked environment. Dependency installation is `uv sync --locked`; an existing local AWS development environment may retain its `local-aws` extra. The evaluation itself requires no AWS login.

PowerShell:

```powershell
$env:PROMPT_SYNC_MODE='false'
$env:PROMPT_MANIFEST_PATH='.generated/offline-no-manifest.json'
$env:REQUIRE_PROMPT_MANIFEST='false'
$env:AWS_EC2_METADATA_DISABLED='true'
$env:AGENT_OBSERVABILITY_ENABLED='false'
$env:EVALUATION_ENABLED='false'
$env:LOGURU_LEVEL='ERROR'
uv run --no-sync python -m src.evaluation.rag --list-cases
uv run --no-sync python -m src.evaluation.rag --offline --output .generated/evaluation/document-rag.json
```

The CLI writes JSON and a same-name `.md` case table. Generated local reports are ignored by Git. Exit codes:

- **0:** every dataset case is present and all required measured checks pass.
- **1:** a check fails or the observations do not cover the full dataset.
- **2:** malformed/unsupported/oversize input or an execution error.

Use the exit code from the current invocation. Invalid input does not create a new report; a report from an earlier invocation is not evidence of success for the failed command.

Run API regressions with `uv run --no-sync python -m unittest discover -s tests -q`. From `restaurant-finder-ui`, run the same command for UI tests. From `restaurant-finder-infra`, run `npm ci`, `npm run build`, `npm test -- --runInBand`, and CDK synth with dummy account `123456789012`, region `us-east-2`, `--no-lookups` and the explicit dummy image context shown in `.github/workflows/ci.yml`. Do not substitute an authenticated deployment command for this check.

## What the 16 cases check

The versioned dataset is `restaurant-finder-api/src/evaluation/datasets/document_rag.json`.

- Harbor v1/v2 menu prices (RM28/RM32), Sakura mushroom pasta (RM36) and Spice chickpea curry (RM22).
- The three restaurant cancellation fees (RM20/RM15/RM10).
- Missing parking evidence, unspecified/unknown/multiple restaurants, follow-up scope and explicit scope override.
- Forged chunk selection and changed source quotation.
- Full-name and short-alias Harbor policy queries.

Human-written gold quotes are checked against real local source chunks, versions and page/line locations. Gold and simulated selector inputs occupy separate dataset fields. The offline harness calls the real document workflow, query resolver, `DocumentRetriever`, provenance validator and renderer. Its store, vector results, embeddings and model answers are explicitly simulated; it does not copy an expected result into an observation.

The scorer independently checks the complete extractive answer text, expected status/scope/generation, every citation field, evidence integrity, source inclusion and supplied call counters. A valid quote about tomato pasta still fails the mushroom-pasta question, even if its source hash and page are correct. Exact prices alone are not an accepted gold quote.

### A documented scope quirk

The existing keyword resolver treats `pasta` as a menu keyword even when it appears inside the venue name `Harbor Pasta Lab`. A full-name policy question therefore resolves to no document-type filter; it can retrieve menu and policy passages. Its evaluation still requires the correct policy quote/citation. The short-name `Harbor policy` case explicitly requires policy-only filtering. This task documents and covers the current behavior; it does not change the retrieval algorithm.

## How to interpret the report

An offline report is labeled `offline_regression` and `simulated_dependencies`. It establishes reproducible workflow/contract behavior. It does **not** measure current Jev routing accuracy, Haiku answer selection, Titan vector ranking, live hallucination rate, latency or cost.

Checks have `pass`, `fail` or `unmeasured` states. The report records the expected and observed case counts, missing IDs, failed cases, measured-check count and unmeasured-check count. A partial set cannot receive complete-suite success. Source provenance establishes where a quote came from; question relevance is checked against this small curated dataset, not a universal semantic judge.

Inputs are bounded to 2 MiB, 50 cases, 15,000 answer characters, three citations and ten evidence records per observation. The dataset requires at least 14 cases; this version has 16. IDs/schemas are strict, unknown and duplicate case IDs fail, and nonfinite JSON values are rejected. Reports omit raw answer/evidence bodies, provider payloads, sessions, headers and credentials.

## Score recorded or hand-authored observations

The scorer can inspect normalized observations without generating responses:

```powershell
uv run --no-sync python -m src.evaluation.rag --observations .generated/evaluation/observations.json --output .generated/evaluation/recorded-report.json
```

Input shape:

```json
{
  "schema_version": 1,
  "observations": [
    {
      "case_id": "harbor_price_v2",
      "origin": "recorded",
      "status": "answered",
      "text": "<complete raw API answer, without the UI answer-number decoration>",
      "restaurant_id": "demo-harbor-pasta",
      "generation_id": "<actual full generation hash>",
      "citations": ["<actual structured citation objects>"],
      "calls": null,
      "evidence": null
    }
  ]
}
```

This illustration contains placeholders and is not valid executable input. Use real structured citation objects from the response and the correct dataset fixture generation. Other fields include optional `query_document_type`; full schemas are in `src/evaluation/rag.py`. Valid origins are `manual`, `recorded` or `offline_simulated`.

Imported observations always retain `imported_unverified` origin verification: a caller declaring `recorded` is not proof of a real model capture. Missing counters/evidence are reported as unmeasured. Scoring all required cases can pass answer/provenance checks without measuring retrieval internals; the report makes that distinction explicit. A live generation prepared with a different parser/config cannot silently count as the pinned local fixture's generation.

A real end-to-end model evaluation requires a separately authorized collection run and budget. This CLI deliberately contains no live-invocation option. The existing AgentCore live evaluation runner remains available through its original imports, loaded lazily only when requested.

## Evidence

The [verified GitHub run](https://github.com/yukangzhen/restaurant-finder/actions/runs/37750760123) checks implementation commit `3aba7881ad9de422fbf2db77d4198b8368f33714`. Its downloaded artifacts confirm **125 API tests**, **26 UI tests**, **3 infrastructure tests**, and **16/16 offline RAG cases** with 352 measured checks and no failures. TypeScript compilation and CDK synthesis also succeeded. Local RAG JSON matches the GitHub report exactly.

The [approved execution PRD](HANDOFF_PRD_CI_AND_RAG_EVALUATION.md) records commands, controlled-failure checks, the first run's masked test failure and its repair, and all acceptance results. Inspect both the run's commit SHA and test artifacts before claiming success; a status badge alone is insufficient. These results describe offline regression with simulated dependencies, not live model accuracy.
