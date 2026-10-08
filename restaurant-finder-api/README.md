# Controlled document RAG

The API includes a fourth `document_qa` route for synthetic menus and policies. It pins a versioned S3 generation, retrieves Titan V2/S3 Vectors evidence by restaurant, and renders validated exact-quote citations through the existing output guardrail and SSE path. RAG is disabled locally by default.

See [the engineering guide](../docs/DOCUMENT_RAG.md) for configuration, offline/publish commands, limitations and rollback. Six sample sources and a Harbor price-update fixture are under `sample_documents/`; source PDFs are excluded from the runtime image.
