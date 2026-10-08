import asyncio
import hashlib
import json
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import app
import source_documents as sources
from test_sse_responses import _Message, _async_lines

PDF = b"%PDF-1.4\noriginal fixture"
MD = b"# Policy\nCancel 24 hours before booking.\nFee RM20.\n"


def reference(content=PDF, **changes):
    data={"label":"Source 1","generation_id":"a"*64,"document_id":"harbor-menu","chunk_id":"b"*64,
          "source_hash":hashlib.sha256(content).hexdigest(),"format":"pdf","filename":"harbor-menu.pdf",
          "version":"v1","page":1,"section":None,"line_start":None,"line_end":None}
    if content != PDF:
        data.update(format="md",filename="harbor-policy.md",document_id="harbor-policy",page=None,section="Policy",line_start=2,line_end=3)
    return {**data,**changes}


ANSWER = 'According to the fictional demo documents:\n\n> "quote"\n\nSource: Source 1 — harbor; version v1'


class Body:
    def __init__(self, content):
        self.content=content
        self.closed=False
        self.thread=None
    def read(self, bound):
        self.thread=threading.get_ident()
        self.bound=bound
        return self.content[:bound]
    def close(self):
        self.closed=True


class SourceTests(unittest.TestCase):
    def load(self, content, data=None, length=None):
        body=Body(content)
        client=SimpleNamespace(get_object=lambda **kw:{"Body":body,"ContentLength":len(content) if length is None else length})
        with patch.object(sources,"_get_s3_client",return_value=client):
            result=sources.load_original(sources.Citation.model_validate(data or reference(content)),"private-bucket","us-east-2")
        return result, body

    def test_original_bytes_and_body_close(self):
        for content in [PDF,MD]:
            result,body=self.load(content)
            self.assertEqual(result,content)
            self.assertTrue(body.closed)
            self.assertEqual(body.bound,sources.MAX_SOURCE_BYTES+1)

    def test_hash_signature_encoding_size_and_incomplete_body_fail_closed(self):
        cases=[(PDF,reference(source_hash="c"*64),len(PDF)),(b"not a PDF",reference(b"not a PDF",format="pdf",filename="menu.pdf",page=1,section=None,line_start=None,line_end=None),9),
               (b"\xff",reference(b"\xff",line_start=1,line_end=1),1),(PDF,reference(),sources.MAX_SOURCE_BYTES+1),
               (PDF,reference(),len(PDF)+1),(b"",reference(),0),(PDF,reference(),True)]
        for content,data,length in cases:
            body=Body(content)
            client=SimpleNamespace(get_object=lambda **kw:{"Body":body,"ContentLength":length})
            with self.subTest(data=data,length=length), patch.object(sources,"_get_s3_client",return_value=client):
                with self.assertRaises((ValueError,UnicodeDecodeError)):
                    sources.load_original(sources.Citation.model_validate(data),"private-bucket","us-east-2")
            self.assertTrue(body.closed)

    def test_actual_oversized_bytes_are_rejected(self):
        content=b"x"*(sources.MAX_SOURCE_BYTES+1)
        with self.assertRaises(ValueError):
            self.load(content,reference(),length=sources.MAX_SOURCE_BYTES)

    def test_unsafe_or_malformed_references_rejected_before_io(self):
        for changes in [{"document_id":"../../secret"},{"generation_id":"bad"},{"filename":"../menu.pdf"},
                        {"page":True},{"page":11},{"url":"https://fake"},{"format":"html"},{"line_start":1}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                sources.validate_citations([reference(**changes)],ANSWER)
        for values in [None,{},[],[reference()]*4,[reference(label="Source 2")]]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                sources.validate_citations(values,ANSWER)
        with self.assertRaises(ValueError):
            sources.validate_citations([reference()],"Unrelated answer")

    def test_generation_key_is_pinned_and_never_resolves_active_pointer(self):
        citation=sources.Citation.model_validate(reference())
        client=SimpleNamespace(get_object=lambda **kw:{"Body":Body(PDF),"ContentLength":len(PDF)})
        from unittest.mock import Mock
        client.get_object=Mock(wraps=client.get_object)
        with patch.object(sources,"_get_s3_client",return_value=client):
            self.assertEqual(sources.load_original(citation,"bucket","us-east-2"),PDF)
            fake_active_generation="f"*64
            self.assertEqual(sources.load_original(citation,"bucket","us-east-2"),PDF)
        self.assertNotEqual(citation.generation_id,fake_active_generation)
        self.assertTrue(all(c.kwargs["Key"]==f"rag/generations/{'a'*64}/sources/harbor-menu.pdf" for c in client.get_object.call_args_list))

    def test_full_markdown_is_literal_and_has_original_line_numbers(self):
        content=MD+b'<script>alert(1)</script>\n![remote](https://example.test/image)\n```\n[link](javascript:alert(1))\n'
        citation=sources.Citation.model_validate(reference(content))
        view=sources.markdown_view(citation,content)
        self.assertIn("lines 2–3",view)
        self.assertIn("   1 | # Policy",view)
        self.assertIn("   7 | [link]",view)
        self.assertIn("````text\n",view)
        self.assertTrue(view.endswith("````"))
        self.assertIn("<script>",view)  # Inside the literal block, never active HTML.
        with self.assertRaises(ValueError):
            sources.markdown_view(citation.model_copy(update={"line_end":100}),content)

    def prepare(self, values, answer=ANSWER, bucket="bucket"):
        return asyncio.run(sources.prepare_source_elements(values,answer,bucket,"us-east-2"))

    def test_duplicate_sources_read_once_and_work_off_event_loop(self):
        event_thread=[]
        worker_thread=[]
        def loader(*_):
            worker_thread.append(threading.get_ident())
            return PDF
        async def run():
            event_thread.append(threading.get_ident())
            return await sources.prepare_source_elements([reference(),reference(label="Source 2")],ANSWER+"\nSource: Source 2 — same menu","bucket","us-east-2")
        with patch.object(sources,"load_original",side_effect=loader) as load, patch.object(sources,"make_elements",side_effect=lambda c,b:[c.label,b]):
            elements,notice=asyncio.run(run())
        self.assertEqual(len(elements),4)
        self.assertEqual(notice,"")
        load.assert_called_once()
        self.assertNotEqual(event_thread[0],worker_thread[0])

    def test_duplicate_failures_are_not_retried_and_errors_are_safe(self):
        with patch.object(sources,"load_original",side_effect=RuntimeError("SECRET_PROVIDER_BODY")) as load:
            elements,notice=self.prepare([reference(),reference(label="Source 2")],ANSWER+"\nSource: Source 2 — same menu")
        load.assert_called_once()
        self.assertEqual(elements,[])
        self.assertEqual(notice,sources.SOURCE_UNAVAILABLE)
        self.assertNotIn("SECRET",notice)

    def test_conflicting_duplicate_metadata_and_missing_bucket_have_no_reads(self):
        with patch.object(sources,"load_original") as load:
            self.assertEqual(self.prepare([reference()],bucket="")[0],[])
            self.assertEqual(self.prepare([reference(),reference(label="Source 2",source_hash="c"*64)],ANSWER+"\nSource: Source 2 — same")[0],[])
        load.assert_not_called()

    def test_timeout_does_not_start_another_source_or_retry(self):
        def slow(*_):
            time.sleep(.03)
            return PDF
        with patch.object(sources,"SOURCE_TIMEOUT_SECONDS",.001),patch.object(sources,"load_original",side_effect=slow) as load:
            elements,notice=self.prepare([reference(),reference(label="Source 2",document_id="other")],ANSWER+"\nSource: Source 2 — other")
        load.assert_called_once()
        self.assertEqual(elements,[])
        self.assertEqual(notice,sources.SOURCE_UNAVAILABLE)

    def test_native_elements_receive_original_bytes_page_and_safe_text(self):
        def element(**kwargs):
            return SimpleNamespace(**kwargs)
        with patch.object(sources.cl,"Pdf",side_effect=element),patch.object(sources.cl,"Text",side_effect=element),patch.object(sources.cl,"File",side_effect=element):
            pdf,download=sources.make_elements(sources.Citation.model_validate(reference()),PDF)
            self.assertEqual((pdf.name,pdf.page,pdf.content),("Source 1",1,PDF))
            self.assertEqual(download.content,PDF)
            text,download=sources.make_elements(sources.Citation.model_validate(reference(MD)),MD)
            self.assertIn("   3 | Fee RM20.",text.content)
            self.assertEqual(download.content,MD)
            self.assertEqual(download.mime,"application/octet-stream")

    def test_sdk_timeouts_and_attempt_bound(self):
        import boto3
        previous=sources._s3_client
        sources._s3_client=None
        try:
            with patch.object(boto3,"client",return_value=object()) as create:
                sources._get_s3_client("us-east-2")
            config=create.call_args.kwargs["config"]
            self.assertEqual((config.connect_timeout,config.read_timeout,config.retries["total_max_attempts"]),(3,10,1))
        finally:
            sources._s3_client=previous


class CitationStreamTests(unittest.TestCase):
    def invoke(self, events, prepare):
        message=_Message()
        with patch.object(app,"AGENT_CONNECTION_MODE","aws"),patch.object(app,"AGENT_RUNTIME_ARN","runtime"),\
             patch.object(app,"DOCUMENT_SOURCE_VIEWER_ENABLED",True),patch.object(app,"RAG_DOCUMENT_BUCKET","bucket"),\
             patch.object(app,"_aws_sse_lines",return_value=_async_lines(events)),patch.object(app,"prepare_source_elements",prepare):
            asyncio.run(app._invoke_agent(message,"menu?","Guest","offline"))
        return message

    def test_direct_and_nested_approved_metadata_attaches_to_complete_answer(self):
        event="data: "+json.dumps({"chunk":ANSWER,"citations":[reference()]})
        for value in [event,"data: "+json.dumps(event)]:
            prepare=AsyncMock(return_value=(["viewer","download"],""))
            message=self.invoke([value,'data: {"done":true}'],prepare)
            self.assertEqual(message.content,ANSWER)
            self.assertEqual(message.elements,["viewer","download"])
            prepare.assert_awaited_once_with([reference()],ANSWER,"bucket",app.AWS_REGION)

    def test_block_errors_incomplete_and_mismatched_envelopes_never_attach(self):
        event="data: "+json.dumps({"chunk":ANSWER,"citations":[reference()]})
        for events in [[event],[event,'data: {"blocked":true,"message":"Blocked"}'],
                       [event,'data: {"error":"failed"}'],[event,'data: {"chunk":"extra"}','data: {"done":true}']]:
            prepare=AsyncMock()
            message=self.invoke(events,prepare)
            prepare.assert_not_awaited()
            self.assertEqual(message.elements,[])

    def test_source_failure_keeps_approved_answer_and_provenance(self):
        prepare=AsyncMock(return_value=([],sources.SOURCE_UNAVAILABLE))
        event="data: "+json.dumps({"chunk":ANSWER,"citations":[reference()]})
        message=self.invoke([event,'data: {"done":true}'],prepare)
        self.assertEqual(message.content,ANSWER+"\n\n"+sources.SOURCE_UNAVAILABLE)
        self.assertEqual(message.elements,[])


if __name__ == "__main__":
    unittest.main()
