"""Validate generated Bedrock prompt metadata without making AWS calls."""

import json

from src.infrastructure.prompt_metadata import validate_prompt_manifest


if __name__ == "__main__":
    print(json.dumps(validate_prompt_manifest(), indent=2, sort_keys=True))
