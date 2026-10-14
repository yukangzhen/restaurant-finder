import asyncio
import hashlib
import json
import threading
import time
import unittest
from pathlib import Path
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
    def multipart_sources(self):
        root = Path(__file__).resolve().parents[2]/"restaurant-finder-api"/"sample_documents"
        contents = [(root/name).read_bytes() for name in ("harbor-menu-v2.pdf", "harbor-policy.md", "sakura-menu.md", "sakura-policy.md")]
        values = [reference(contents[0],format="pdf",filename="harbor-menu-v2.pdf",document_id="harbor-menu",version="v2",
                            page=1,section=None,line_start=None,line_end=None)]
        for i, (content, stem, kind) in enumerate(zip(contents[1:], ("harbor", "sakura", "sakura"), ("policy", "menu", "policy")), 2):
            values.append(reference(content,label=f"Source {i}",document_id=f"{stem}-{kind}",filename=f"{stem}-{kind}.md",
                                    chunk_id=str(i)*64,section="Main dishes" if kind=="menu" else "Reservations and cancellation",
                                    line_start=5,line_end=11 if kind=="menu" else 8))
        answer="Answered 4 of 4 requested parts.\n"+"\n".join(f"Source: Source {i} — verified original" for i in range(1,5))
        return values, contents, answer

    def test_four_sources_verify_original_bytes_locations_and_answer_identity(self):
        values, contents, answer = self.multipart_sources()
        keys = {sources.Citation.model_validate(value).source_key: content for value,content in zip(values,contents)}
        bodies = []
        def get_object(**kwargs):
            body=Body(keys[kwargs["Key"]]); bodies.append(body)
            return {"Body":body,"ContentLength":len(body.content)}
        client=SimpleNamespace(get_object=get_object)
        with patch.object(sources,"_get_s3_client",return_value=client),\
             patch.object(sources.cl,"Pdf",side_effect=lambda **kwargs:SimpleNamespace(**kwargs)),\
             patch.object(sources.cl,"Text",side_effect=lambda **kwargs:SimpleNamespace(**kwargs)),\
             patch.object(sources.cl,"File",side_effect=lambda **kwargs:SimpleNamespace(**kwargs)):
            elements,notice,links=asyncio.run(sources.prepare_source_elements(values,answer,"bucket","us-east-2",answer_number=1))
            later,_,later_links=asyncio.run(sources.prepare_source_elements(values,answer,"bucket","us-east-2",answer_number=2))
        self.assertEqual(notice,"")
        self.assertEqual(len(elements),8)
        self.assertEqual(len(links),4)
        self.assertTrue(all(body.closed for body in bodies))
        self.assertEqual([elements[i].content for i in (1,3,5,7)],contents)
        self.assertEqual(elements[0].page,1)
        self.assertIn("lines 5–8",elements[2].content)
        self.assertIn("lines 5–11",elements[4].content)
        self.assertTrue(all(links[k]!=later_links[k] for k in links))
        self.assertEqual(len(later),8)

    def test_fourth_source_failure_preserves_first_three_without_agent_retry(self):
        values,contents,answer=self.multipart_sources()
        keys={sources.Citation.model_validate(value).source_key:content for value,content in zip(values,contents)}
        reads=[]
        def get_object(**kwargs):
            reads.append(kwargs["Key"])
            if kwargs["Key"].endswith("sakura-policy.md"):
                raise RuntimeError("unavailable")
            body=Body(keys[kwargs["Key"]])
            return {"Body":body,"ContentLength":len(body.content)}
        with patch.object(sources,"_get_s3_client",return_value=SimpleNamespace(get_object=get_object)),\
             patch.object(sources.cl,"Pdf",side_effect=lambda **kwargs:SimpleNamespace(**kwargs)),\
             patch.object(sources.cl,"Text",side_effect=lambda **kwargs:SimpleNamespace(**kwargs)),\
             patch.object(sources.cl,"File",side_effect=lambda **kwargs:SimpleNamespace(**kwargs)):
            elements,notice,links=self.prepare(values,answer)
        self.assertEqual(len(elements),6)
        self.assertEqual(notice,sources.SOURCE_UNAVAILABLE)
        self.assertEqual(set(links),{"Source 1","Source 2","Source 3"})
        self.assertEqual(len(reads),4)
        self.assertEqual(len(set(reads)),4)

    def test_fifth_source_and_corrupted_four_source_metadata_fail_before_io(self):
        values,_,answer=self.multipart_sources()
        for bad in (values+[reference(label="Source 5")],values[:3]+[{**values[3],"generation_id":"f"*64}],
                    values[:3]+[{**values[3],"label":"Source 3"}],values[:3]+[{**values[3],"url":"https://fake"}]):
            with self.assertRaises(ValueError):
                sources.validate_citations(bad,answer)

    def test_comparison_opens_two_distinct_originals_with_one_generation(self):
        root = Path(__file__).resolve().parents[2] / "restaurant-finder-api" / "sample_documents"
        pdf, md = (root/"harbor-menu-v2.pdf").read_bytes(), (root/"sakura-menu.md").read_bytes()
        values = [reference(pdf,format="pdf",filename="harbor-menu-v2.pdf",document_id="harbor-menu",version="v2",
                            page=1,section=None,line_start=None,line_end=None),
                  reference(md,label="Source 2",filename="sakura-menu.md",document_id="sakura-menu",section="Main dishes",
                            line_start=5,line_end=11,chunk_id="c"*64)]
        answer = "| Harbor | RM32 per serving | Source 1 |\n| Sakura | RM36 per serving | Source 2 |\n" + ANSWER + "\nSource: Source 2 — sakura menu"
        def element(**kwargs):
            return SimpleNamespace(**kwargs)
        with patch.object(sources,"load_original",side_effect=[pdf,md]) as load,\
             patch.object(sources.cl,"Pdf",side_effect=element),patch.object(sources.cl,"Text",side_effect=element),\
             patch.object(sources.cl,"File",side_effect=element):
            elements,notice,links = self.prepare(values,answer)
        self.assertEqual(load.call_count,2)
        self.assertEqual(notice,"")
        self.assertEqual(len(elements),4)
        self.assertEqual((elements[0].content,elements[0].page),(pdf,1))
        self.assertIn("RM36",elements[2].content)
        self.assertEqual(elements[3].content,md)
        self.assertEqual(set(links),{"Source 1","Source 2"})
        with self.assertRaises(ValueError):
            sources.validate_citations([values[0],{**values[1],"generation_id":"f"*64}],answer)

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
        with patch.object(sources,"load_original",side_effect=loader) as load, patch.object(sources,"make_elements",side_effect=lambda c,b,n:[c.label,b]):
            elements,notice,links=asyncio.run(run())
        self.assertEqual(len(elements),4)
        self.assertEqual(notice,"")
        load.assert_called_once()
        self.assertNotEqual(event_thread[0],worker_thread[0])

    def test_duplicate_failures_are_not_retried_and_errors_are_safe(self):
        with patch.object(sources,"load_original",side_effect=RuntimeError("SECRET_PROVIDER_BODY")) as load:
            elements,notice,links=self.prepare([reference(),reference(label="Source 2")],ANSWER+"\nSource: Source 2 — same menu")
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
            elements,notice,links=self.prepare([reference(),reference(label="Source 2",document_id="other")],ANSWER+"\nSource: Source 2 — other")
        load.assert_called_once()
        self.assertEqual(elements,[])
        self.assertEqual(notice,sources.SOURCE_UNAVAILABLE)

    def test_native_elements_receive_original_bytes_page_and_safe_text(self):
        def element(**kwargs):
            return SimpleNamespace(**kwargs)
        with patch.object(sources.cl,"Pdf",side_effect=element),patch.object(sources.cl,"Text",side_effect=element),patch.object(sources.cl,"File",side_effect=element):
            pdf,download=sources.make_elements(sources.Citation.model_validate(reference()),PDF)
            self.assertEqual((pdf.name,pdf.page,pdf.content),("Source 1 (answer 1)",1,PDF))
            self.assertEqual(download.content,PDF)
            text,download=sources.make_elements(sources.Citation.model_validate(reference(MD)),MD)
            self.assertIn("   3 | Fee RM20.",text.content)
            self.assertEqual(download.content,MD)
            self.assertEqual(download.mime,"application/octet-stream")

    def test_native_viewer_names_are_distinct_across_answers(self):
        citation=sources.Citation.model_validate(reference())
        self.assertNotEqual(sources.viewer_name(citation,1),sources.viewer_name(citation,2))
        for number in [True,0,-1,1000001,"2"]:
            with self.subTest(number=number),self.assertRaises(ValueError):
                sources.viewer_name(citation,number)

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
    def test_followup_keeps_earlier_menu_and_new_policy_controls_bound_to_their_answers(self):
        root=Path(__file__).resolve().parents[2]/"restaurant-finder-api/sample_documents"
        pdf=(root/"harbor-menu-v2.pdf").read_bytes();policy=(root/"harbor-policy.md").read_bytes()
        menu=reference(pdf,format="pdf",filename="harbor-menu-v2.pdf",document_id="harbor-menu",version="v2",
                       page=1,section=None,line_start=None,line_end=None)
        later=reference(policy,format="md",filename="harbor-policy.md",document_id="harbor-policy",version="v1",
                        page=None,section="Reservations and cancellation",line_start=5,line_end=8,chunk_id="c"*64)
        prepared=[]
        async def prepare(values,answer,bucket,region,number):
            prepared.append((number,values[0]["document_id"],values[0]["source_hash"]))
            return await sources.prepare_source_elements(values,answer,bucket,region,number)
        client=SimpleNamespace(get_object=lambda **kwargs:{"Body":Body(pdf if kwargs["Key"].endswith(".pdf") else policy),
                                                          "ContentLength":len(pdf if kwargs["Key"].endswith(".pdf") else policy)})
        messages=[_Message(),_Message()]
        async def execute():
            for number,value in enumerate((menu,later),1):
                events=["data: "+json.dumps({"chunk":ANSWER,"citations":[value]}),'data: {"done":true}']
                with patch.object(app,"_aws_sse_lines",return_value=_async_lines(events)):
                    await app._invoke_agent(messages[number-1],"seed" if number==1 else "And what about its cancellation fee?",
                                            "Guest","offline",answer_number=number)
        with patch.object(app,"AGENT_CONNECTION_MODE","aws"),patch.object(app,"AGENT_RUNTIME_ARN","runtime"),\
             patch.object(app,"DOCUMENT_SOURCE_VIEWER_ENABLED",True),patch.object(app,"RAG_DOCUMENT_BUCKET","bucket"),\
             patch.object(app,"prepare_source_elements",side_effect=prepare),patch.object(sources,"_get_s3_client",return_value=client),\
             patch.object(sources.cl,"Pdf",side_effect=lambda **kw:SimpleNamespace(**kw)),\
             patch.object(sources.cl,"Text",side_effect=lambda **kw:SimpleNamespace(**kw)),\
             patch.object(sources.cl,"File",side_effect=lambda **kw:SimpleNamespace(**kw)):
            asyncio.run(execute())
        self.assertEqual(messages[0].elements[0].content,pdf)
        self.assertEqual(messages[0].elements[0].page,1)
        self.assertEqual(messages[1].elements[1].content,policy)
        self.assertIn("lines 5–8",messages[1].elements[0].content)
        self.assertNotEqual(messages[0].elements[0].name,messages[1].elements[0].name)
        self.assertEqual(prepared,[(1,"harbor-menu",menu["source_hash"]),(2,"harbor-policy",later["source_hash"])])
        self.assertIn(messages[0].elements[0].name,messages[0].content)
        self.assertIn(messages[1].elements[0].name,messages[1].content)

    def test_comparison_and_partial_source_lines_remain_clickable(self):
        for values, answer in [([reference(),reference(MD,label="Source 2")],ANSWER+"\nSource: Source 2 — second venue"),
                               ([reference()],"Partial comparison: other restaurant retrieval unavailable.\n"+ANSWER)]:
            mapping = {value["label"]:value["label"]+" (answer 1)" for value in values}
            prepare = AsyncMock(return_value=(["viewers"],"",mapping))
            events = ["data: "+json.dumps({"chunk":answer,"citations":values}),'data: {"done":true}']
            message = self.invoke(events,prepare)
            self.assertEqual(message.elements,["viewers"])
            for label, viewer in mapping.items():
                self.assertIn(f"Source: {viewer} — ",message.content)
                self.assertNotIn(f"Source: {label} — ",message.content)
            prepare.assert_awaited_once()

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
            prepare=AsyncMock(return_value=(["viewer","download"],"",{"Source 1":"Source 1 (answer 1)"}))
            message=self.invoke([value,'data: {"done":true}'],prepare)
            self.assertEqual(message.content,ANSWER.replace("Source: Source 1 — ","Source: Source 1 (answer 1) — "))
            self.assertEqual(message.elements,["viewer","download"])
            prepare.assert_awaited_once_with([reference()],ANSWER,"bucket",app.AWS_REGION,1)

    def test_block_errors_incomplete_and_mismatched_envelopes_never_attach(self):
        event="data: "+json.dumps({"chunk":ANSWER,"citations":[reference()]})
        for events in [[event],[event,'data: {"blocked":true,"message":"Blocked"}'],
                       [event,'data: {"error":"failed"}'],[event,'data: {"chunk":"extra"}','data: {"done":true}']]:
            prepare=AsyncMock()
            message=self.invoke(events,prepare)
            prepare.assert_not_awaited()
            self.assertEqual(message.elements,[])

    def test_source_failure_keeps_approved_answer_and_provenance(self):
        prepare=AsyncMock(return_value=([],sources.SOURCE_UNAVAILABLE,{}))
        event="data: "+json.dumps({"chunk":ANSWER,"citations":[reference()]})
        message=self.invoke([event,'data: {"done":true}'],prepare)
        self.assertEqual(message.content,ANSWER+"\n\n"+sources.SOURCE_UNAVAILABLE)
        self.assertEqual(message.elements,[])


if __name__ == "__main__":
    unittest.main()
