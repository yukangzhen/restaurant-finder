# Restaurant Finder UI

Local Chainlit client for the Restaurant Finder backend. It calls an AWS AgentCore Runtime (`AGENT_CONNECTION_MODE=aws`) or a local API (`local`). The UI is not deployed to cloud hosting by the CDK stacks.

Follow [Setup](../docs/SETUP.md#4-connect-the-local-ui-to-aws). From this directory, create `.env` only if it does not already exist:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edit .env before starting.
uv sync --locked --extra local-aws --python 3.11
uv run --no-sync chainlit run app.py --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Chainlit reads `.env` from this directory. AWS mode needs `AGENT_RUNTIME_ARN`, `AWS_REGION` and a valid credential profile. Local mode uses `AGENTCORE_API_URL=http://localhost:8080/invocations`.

Source viewing additionally requires `DOCUMENT_SOURCE_VIEWER_ENABLED=true` and `RAG_DOCUMENT_BUCKET` matching the backend corpus bucket. The UI identity needs `s3:GetObject` on that bucket's `rag/generations/*/sources/*` objects. Reads use immutable generation keys and verify content hashes; they do not make the bucket public or provide document-level authorization for a shared service.

Leave `MEMORY_ACTOR_ID` empty to isolate anonymous memory per conversation. A stable value is for local single-user demonstrations. Shared public use needs authenticated identities assigned by the server. See the root [known issues](../README.md#limits-and-known-issues), including the unresolved early source-viewer mismatch.

Offline UI regressions: `uv run --no-sync python -m unittest discover -s tests -q`, from a clean checkout/environment without real `.env` credentials as described in [Setup](../docs/SETUP.md#2-offline-checks).
