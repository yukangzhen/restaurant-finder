import json
import uuid
import os

import aiohttp
import chainlit as cl
from chainlit.input_widget import TextInput


# --- Connection mode configuration ---
# Set AGENT_CONNECTION_MODE to "aws" to invoke the deployed AgentCore Runtime on AWS.
# Set to "local" (or leave unset) to call the local API server.
AGENT_CONNECTION_MODE = os.environ.get("AGENT_CONNECTION_MODE", "local").lower()

# Local mode settings
AGENTCORE_API_URL = os.environ.get("AGENTCORE_API_URL", "http://localhost:8080/invocations")

# AWS mode settings
AGENT_RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")
# Optional single-user identity for local development. In production, actor IDs
# must come from authenticated server-side identity, not a client-controlled value.
MEMORY_ACTOR_ID = os.environ.get("MEMORY_ACTOR_ID", "").strip()

# Lazily initialized boto3 client for AWS mode
_agentcore_client = None


def _get_agentcore_client():
    """Get or create the boto3 bedrock-agentcore client (lazy init)."""
    global _agentcore_client
    if _agentcore_client is None:
        import boto3
        from botocore.config import Config

        runtime_config = Config(
            connect_timeout=10,
            read_timeout=300,
            retries={"total_max_attempts": 1},
        )
        _agentcore_client = boto3.client(
            "bedrock-agentcore",
            region_name=AWS_REGION,
            config=runtime_config,
        )
    return _agentcore_client


def _next_stream_item(iterator, sentinel):
    """Read one blocking SDK stream item without leaking StopIteration."""
    try:
        return next(iterator)
    except StopIteration:
        return sentinel


@cl.on_settings_update
async def settings_update(settings):
    """Handle settings updates."""
    cl.user_session.set("customer_name", settings.get("customer_name", "Guest"))

    await cl.Message(
        content=f"Settings updated! Welcome, {settings.get('customer_name', 'Guest')}! Ready to find your perfect restaurant."
    ).send()


@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session with settings."""
    settings = await cl.ChatSettings(
        [
            TextInput(
                id="customer_name",
                label="Your Name",
                placeholder="Enter your name",
                initial="Guest"
            ),
        ]
    ).send()

    cl.user_session.set("customer_name", settings.get("customer_name", "Guest"))

    conversation_id = str(uuid.uuid4())
    cl.user_session.set("conversation_id", conversation_id)

    customer_name = settings.get("customer_name", "Guest")
    await cl.Message(
        content=f"Welcome, {customer_name}! I'm your restaurant finder assistant. What kind of dining experience are you looking for today?\n\n*Tip: Click the settings icon to update your profile.*"
    ).send()


async def _local_sse_lines(payload):
    """Yield SSE lines from the local HTTP API."""
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            AGENTCORE_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            line_buffer = ""
            async for chunk_bytes in response.content.iter_any():
                line_buffer += chunk_bytes.decode("utf-8", errors="replace")
                while "\n" in line_buffer:
                    line, line_buffer = line_buffer.split("\n", 1)
                    yield line.strip()


async def _aws_sse_lines(payload, conversation_id):
    """Yield SSE lines from the AWS Bedrock AgentCore Runtime."""
    import asyncio

    client = _get_agentcore_client()
    deadline = asyncio.get_running_loop().time() + 300
    response = await asyncio.wait_for(
        asyncio.to_thread(
            client.invoke_agent_runtime,
            agentRuntimeArn=AGENT_RUNTIME_ARN,
            qualifier="DEFAULT",
            runtimeSessionId=conversation_id,
            payload=json.dumps(payload),
        ),
        timeout=300,
    )
    body = response.get("response")
    sentinel = object()
    try:
        if "text/event-stream" in response.get("contentType", ""):
            iterator = await asyncio.to_thread(body.iter_lines, chunk_size=1)
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError("AgentCore response exceeded 300 seconds")
                line = await asyncio.wait_for(
                    asyncio.to_thread(_next_stream_item, iterator, sentinel),
                    timeout=remaining,
                )
                if line is sentinel:
                    break
                if line:
                    yield line.decode("utf-8", errors="replace") if isinstance(line, bytes) else str(line)
        elif body is not None:
            iterator = await asyncio.to_thread(iter, body)
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError("AgentCore response exceeded 300 seconds")
                item = await asyncio.wait_for(
                    asyncio.to_thread(_next_stream_item, iterator, sentinel),
                    timeout=remaining,
                )
                if item is sentinel:
                    break
                chunk = item.decode("utf-8") if isinstance(item, bytes) else str(item)
                yield f'data: {json.dumps({"chunk": chunk})}'
    finally:
        close = getattr(body, "close", None)
        if callable(close):
            await asyncio.to_thread(close)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages by calling the AgentCore API (local or AWS)."""
    customer_name = cl.user_session.get("customer_name", "Guest")
    conversation_id = cl.user_session.get("conversation_id")

    msg = cl.Message(content="Working on your request…")
    await msg.send()

    await _invoke_agent(msg, message.content, customer_name, conversation_id)


async def _invoke_agent(
    msg: cl.Message,
    user_input: str,
    customer_name: str,
    conversation_id: str,
):
    """Invoke the agent via local API or AWS AgentCore Runtime based on config."""
    if AGENT_CONNECTION_MODE == "aws" and not AGENT_RUNTIME_ARN:
        msg.content = "Configuration Error: AGENT_RUNTIME_ARN is required when AGENT_CONNECTION_MODE=aws."
        await msg.update()
        return

    payload = {
        "prompt": user_input,
        "customer_name": customer_name,
        "conversation_id": conversation_id,
    }
    if MEMORY_ACTOR_ID:
        payload["actor_id"] = MEMORY_ACTOR_ID

    full_response = ""
    streamed_content = False

    try:
        if AGENT_CONNECTION_MODE == "aws":
            lines = _aws_sse_lines(payload, conversation_id)
        else:
            lines = _local_sse_lines(payload)

        async for line in lines:
            if not line or not line.startswith("data: "):
                continue

            json_str = line[6:]
            try:
                data = json.loads(json_str)

                # Handle nested SSE format
                if isinstance(data, str) and data.startswith("data: "):
                    data = json.loads(data[6:].strip())

                if isinstance(data, dict):
                    if data.get("blocked") is True:
                        blocked_message = data.get("message")
                        if not isinstance(blocked_message, str) or not blocked_message.strip():
                            blocked_message = "I couldn't process that request. Please try a restaurant-related question."
                        msg.content = blocked_message
                        await msg.update()
                        return

                    if "chunk" in data:
                        chunk = data["chunk"]
                        if not isinstance(chunk, str):
                            chunk = str(chunk)
                        if not streamed_content:
                            msg.content = ""
                            streamed_content = True
                        await msg.stream_token(chunk)
                        full_response += chunk

                    elif "error" in data:
                        msg.content = f"Error: {data['error']}"
                        await msg.update()
                        return

            except json.JSONDecodeError:
                continue

        msg.content = full_response if full_response else "No response received."
        await msg.update()

    except aiohttp.ClientResponseError as e:
        msg.content = f"API Error: {e.status}"
        await msg.update()
    except aiohttp.ClientError:
        msg.content = "Connection Error: Could not connect to the local API. Please ensure the API server is running."
        await msg.update()
    except Exception as e:
        if AGENT_CONNECTION_MODE == "aws":
            error_name = type(e).__name__
            msg.content = f"AWS Runtime Error ({error_name}). Please try again later."
        else:
            msg.content = "An unexpected error occurred. Please try again."
        await msg.update()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
