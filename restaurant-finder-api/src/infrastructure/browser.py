"""Factories for isolated AgentCore Browser operations."""

from __future__ import annotations

import asyncio
import uuid

from langchain_aws.tools import create_browser_toolkit
from langchain_aws.tools.browser_toolkit import BrowserToolkit
from langchain_core.tools import BaseTool
from loguru import logger

from src.config import settings


def create_browser_operation(parent_config: dict | None = None) -> tuple[BrowserToolkit, dict[str, BaseTool], dict]:
    """Create a toolkit, tools, and unique session config owned by one operation."""
    operation_id = f"browser-{uuid.uuid4().hex}"
    toolkit, _ = create_browser_toolkit(region=settings.AWS_REGION)
    tools = toolkit.get_tools_by_name()
    config = dict(parent_config or {})
    configurable = dict(config.get("configurable", {}))
    conversation_id = configurable.get("thread_id")
    configurable["thread_id"] = operation_id
    if conversation_id:
        configurable["conversation_id"] = conversation_id
    config["configurable"] = configurable
    logger.info("Created isolated browser operation {}", operation_id)
    return toolkit, tools, config


async def close_browser_operation(toolkit: BrowserToolkit) -> None:
    """Close only the toolkit owned by the completed browser operation."""
    cleanup_task = asyncio.create_task(toolkit.cleanup())
    try:
        await asyncio.shield(cleanup_task)
    except asyncio.CancelledError:
        # Let the operation's own toolkit finish closing before propagating
        # cancellation to the caller.
        try:
            await asyncio.shield(cleanup_task)
        finally:
            raise
    except Exception as error:
        logger.warning("Browser operation cleanup failed (error_type={})", type(error).__name__)
