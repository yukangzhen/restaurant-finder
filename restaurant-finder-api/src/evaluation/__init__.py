"""
AgentCore Evaluations module for the Restaurant Finder Agent.

This module provides comprehensive evaluation capabilities using AWS Bedrock AgentCore
Evaluations, including:
- Built-in evaluators (Correctness, GoalSuccessRate, ToolSelectionAccuracy, etc.)
- Custom evaluators for restaurant-specific metrics
- On-demand evaluation for development and testing
- Online evaluation for production monitoring

Usage:
    from src.evaluation import EvaluationClient, run_on_demand_evaluation

    # Run on-demand evaluation
    results = await run_on_demand_evaluation(session_id="your-session-id")

    # Setup online evaluation for production
    from src.evaluation import setup_online_evaluation
    config = await setup_online_evaluation()

    # Run comprehensive evaluation with test cases
    from src.evaluation import EvaluationRunner
    runner = EvaluationRunner(agent_id="my-agent", agent_arn="arn:...")
    results = await runner.run_full_evaluation()
"""

from importlib import import_module

# Importing the package or offline CLI must not load the live evaluation SDK.
_EXPORTS = {
    "EvaluationClient": "client",
    "EvaluationRunner": "runner",
    "run_on_demand_evaluation": "on_demand",
    "evaluate_session": "on_demand",
    "setup_online_evaluation": "online",
    "OnlineEvaluationManager": "online",
    "RESTAURANT_EVAL_CASES": "test_cases",
    "EvalTestCase": "test_cases",
    "TestCategory": "test_cases",
}


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(f"{__name__}.{_EXPORTS[name]}"), name)


def __dir__():
    return sorted(set(globals()) | set(_EXPORTS))

__all__ = [
    "EvaluationClient",
    "EvaluationRunner",
    "run_on_demand_evaluation",
    "evaluate_session",
    "setup_online_evaluation",
    "OnlineEvaluationManager",
    "RESTAURANT_EVAL_CASES",
    "EvalTestCase",
    "TestCategory",
]
