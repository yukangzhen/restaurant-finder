"""S3 Vectors adapter. Filters are composed by server code, never by an LLM."""
from __future__ import annotations

from src.domain.document_rag import validate_vector
from src.infrastructure.document_store import CLIENT_CONFIG


class VectorStore:
    def __init__(self, index_arn: str, region: str, client=None, session=None):
        self.index_arn, self.region, self._client, self._session = index_arn, region, client, session
        self.put_attempts = 0

    @property
    def client(self):
        if self._client is None:
            import boto3
            self._client = (self._session or boto3).client("s3vectors", region_name=self.region, config=CLIENT_CONFIG)
        return self._client

    def validate_index(self):
        index = self.client.get_index(indexArn=self.index_arn)["index"]
        if index["dimension"] != 512 or index["dataType"] != "float32" or index["distanceMetric"] != "cosine":
            raise ValueError("Vector index is incompatible with Titan V2 512/cosine")

    def put(self, records: list[dict]):
        if not 1 <= len(records) <= 100:
            raise ValueError("Vector batch must contain 1 to 100 records")
        for record in records:
            validate_vector(record["data"]["float32"])
        self.put_attempts += 1
        return self.client.put_vectors(indexArn=self.index_arn, vectors=records)

    def get(self, keys: list[str]):
        return self.client.get_vectors(indexArn=self.index_arn, keys=keys, returnData=True, returnMetadata=True)["vectors"]

    def query(self, vector: list[float], generation_id: str, restaurant_id: str, document_type: str | None = None, top_k: int = 5):
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be 1 to 10")
        clauses = [{"generation_id": {"$eq": generation_id}}, {"restaurant_id": {"$eq": restaurant_id}}]
        if document_type:
            if document_type not in {"menu", "policy"}:
                raise ValueError("Unknown document type")
            clauses.append({"document_type": {"$eq": document_type}})
        request = {"indexArn": self.index_arn, "queryVector": {"float32": validate_vector(vector)}, "topK": top_k,
                   "filter": {"$and": clauses}, "returnDistance": True, "returnMetadata": True}
        response = self.client.query_vectors(**request)
        results = list(response["vectors"])
        # Handle pagination only if the installed service model supports it.
        members = self.client.meta.service_model.operation_model("QueryVectors").input_shape.members
        pages = 1
        while response.get("nextToken"):
            if "nextToken" not in members or pages >= 10:
                raise ValueError("Unsupported or excessive query pagination")
            response = self.client.query_vectors(**request, nextToken=response["nextToken"])
            results.extend(response["vectors"])
            pages += 1
        return results[:top_k]
