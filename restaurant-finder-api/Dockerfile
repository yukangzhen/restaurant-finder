FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    PATH="/app/.venv/bin:$PATH"

# Resolve only from the checked-in lockfile. The source tree is copied after
# dependencies so normal code changes do not invalidate the dependency layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Run the agent as an unprivileged user.
RUN useradd --create-home --uid 1000 bedrock_agentcore
COPY . .
RUN chown -R bedrock_agentcore:bedrock_agentcore /app
USER bedrock_agentcore

EXPOSE 9000 8000 8080

CMD ["opentelemetry-instrument", "python", "-m", "src.main"]
