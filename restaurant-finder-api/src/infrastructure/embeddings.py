"""Titan V2 adapter: fixed dimensions, normalization and no hidden retries."""
from __future__ import annotations
import json

from src.domain.document_rag import RagConfig, canonical_text, validate_vector
from src.infrastructure.document_store import CLIENT_CONFIG


class TitanEmbeddings:
    def __init__(self, region: str, client=None, session=None, max_attempts: int = 128):
        self.region, self._client, self._session = region, client, session
        self.attempts, self.tokens, self.max_attempts = 0, 0, max_attempts
        self.config = RagConfig()

    def embed(self, text: str) -> list[float]:
        if self.attempts >= self.max_attempts:
            raise RuntimeError("Embedding attempt budget exhausted")
        text = canonical_text(text)
        if not text or len(text) > 50000:
            raise ValueError("Invalid embedding text")
        if self._client is None:
            import boto3
            self._client = (self._session or boto3).client("bedrock-runtime", region_name=self.region, config=CLIENT_CONFIG)
        self.attempts += 1
        response = self._client.invoke_model(modelId=self.config.model_id, contentType="application/json", accept="application/json",
                                            body=json.dumps({"inputText": text, "dimensions": 512, "normalize": True, "embeddingTypes": ["float"]}))
        body = response["body"]
        try:
            result = json.loads(body.read())
        finally:
            body.close()
        self.tokens += result.get("inputTextTokenCount", 0)
        return validate_vector(result["embedding"])
