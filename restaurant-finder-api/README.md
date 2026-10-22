# Restaurant Finder API

Python/LangGraph backend for restaurant discovery, conversational memory and bounded document RAG. Entry point: `src.main`; HTTP handler: `src.infrastructure.api`. It runs locally or as an ARM64 AgentCore Runtime container.

Use the [canonical setup guide](../docs/SETUP.md) for commands. From this directory, `uv sync --locked --extra local-aws --python 3.11` installs the AWS-assisted local environment. A local API still needs AWS services and credentials. `uv run --no-sync python -m src.main` starts the SDK server on port 8080 and can initialize AWS guardrails; it is not an offline check.

`src/config.py` and [.env.example](.env.example) define local settings. CDK supplies deployed settings separately. Prompt synchronization explicitly writes Bedrock prompt versions; Docker requires the resulting `.generated/prompt-manifest.json`. Runtime startup does not synchronize prompts.

Document ingestion is a separate owner action, never a side effect of a chat request. The committed `sample_documents/` corpus is fictional. Real-source preparation requires reviewed original bytes, provenance and catalog compatibility; those private originals are not committed or included in the image. See [document RAG](../docs/DOCUMENT_RAG.md).

For credential-free checks, run the isolated instructions in [Setup](../docs/SETUP.md#2-offline-checks). All five document evaluations simulate cloud/model dependencies. The separate `src.evaluation.runner`, `on_demand` and `online` modules are live AWS evaluation tools and may incur charges; they are not part of the offline quick start. Makefile formatting targets require Ruff, which is not in the current dependency manifest.
