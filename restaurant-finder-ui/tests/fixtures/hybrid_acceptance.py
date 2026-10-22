"""Local-only SSE/S3 fixture for the unchanged Chainlit UI; never live RAG evidence."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import socket
import sys
import threading

UI_ROOT=Path(__file__).resolve().parents[2]
if str(UI_ROOT) not in sys.path:
    sys.path.insert(0,str(UI_ROOT))
from acceptance import QUESTIONS, redact, write_json

GENERATION=hashlib.sha256(b"local-hybrid-acceptance-fixture-only").hexdigest()
MENU_H="Mushroom pasta - RM32 per serving. Contains wheat and milk."
MENU_S="Mushroom pasta - RM36 per serving. Contains wheat and milk. Available at dinner only."
POLICY_H=("Reservations at Harbor Pasta Lab can be cancelled without a fee at least 24 hours before the booking. "
          "Cancellations less than 24 hours before the booking incur a RM20 fee per booking.")
POLICY_S=("Reservations at Sakura Table Lab can be cancelled without a fee at least 12 hours before the booking. "
          "Later cancellations incur a RM15 fee per booking.")
SOURCES={
 "harbor-menu":("harbor-menu-v2.pdf","v2",MENU_H,"menu",None),
 "harbor-policy":("harbor-policy.md","v1",POLICY_H,"policy","Reservations and cancellation"),
 "sakura-menu":("sakura-menu.md","v1",MENU_S,"menu","Main dishes"),
 "sakura-policy":("sakura-policy.md","v1",POLICY_S,"policy","Reservations and cancellation"),
}
SELECTIONS=(("harbor-menu",),("harbor-policy",),("harbor-policy",),(),
            ("harbor-menu","sakura-menu"),("harbor-menu","sakura-menu"),
            ("harbor-menu","harbor-policy","sakura-menu","sakura-policy"))


def original_data(samples):
    return {key:(Path(samples)/values[0]).read_bytes() for key,values in SOURCES.items()}


def answer(index,samples):
    blobs=original_data(samples)
    if index==3:
        return {"chunk":"LOCAL FIXTURE — simulated services.\n\nThe supplied documents do not provide evidence about valet parking."}
    text="LOCAL FIXTURE — simulated services.\n\n";citations=[]
    for number,key in enumerate(SELECTIONS[index],1):
        name,version,quote,_,section=SOURCES[key];fmt="pdf" if name.endswith(".pdf") else "md"
        text+=f'> "{quote}"\n\nSource: Source {number} — {key}; version {version}; '+("page 1" if fmt=="pdf" else section)+"\n\n"
        citations.append(dict(label=f"Source {number}",generation_id=GENERATION,document_id=key,
            chunk_id=hashlib.sha256((key+quote).encode()).hexdigest(),source_hash=hashlib.sha256(blobs[key]).hexdigest(),
            format=fmt,filename=name,version=version,page=1 if fmt=="pdf" else None,
            section=section,line_start=5 if fmt=="md" else None,
            line_end=(11 if key=="sakura-menu" else 8) if fmt=="md" else None))
    if index>=4:text+="Harbor Pasta Lab is cheaper by RM4 per serving."
    return {"chunk":text,"citations":citations}


def install_boundary(receipt):
    """Fail before an external socket/client can be created; record any attempt."""
    import boto3
    state={"blocked_external":0,"blocked_aws":0,"source_reads":0}
    lock=threading.Lock()
    def save():
        with lock:write_json(Path(receipt),state)
    def forbid_client(*args,**kwargs):
        state["blocked_aws"]+=1;save()
        raise RuntimeError("AWS is forbidden in the local fixture")
    boto3.client=forbid_client
    boto3.session.Session.client=forbid_client
    original_connect=socket.socket.connect
    original_connect_ex=socket.socket.connect_ex
    original_resolve=socket.getaddrinfo
    def allowed(address):
        return not isinstance(address,tuple) or address[0] in ("127.0.0.1","::1")
    def connect(sock,address):
        if not allowed(address):
            state["blocked_external"]+=1;save()
            raise RuntimeError("External socket forbidden in fixture")
        return original_connect(sock,address)
    def connect_ex(sock,address):
        if not allowed(address):
            state["blocked_external"]+=1;save()
            raise RuntimeError("External socket forbidden in fixture")
        return original_connect_ex(sock,address)
    def resolve(host,*args,**kwargs):
        if host not in (None,"127.0.0.1","::1","localhost"):
            state["blocked_external"]+=1;save()
            raise RuntimeError("External DNS forbidden in fixture")
        return original_resolve(host,*args,**kwargs)
    socket.socket.connect=connect;socket.socket.connect_ex=connect_ex;socket.getaddrinfo=resolve
    save()
    return state,save


def configure_ui():
    if os.environ.get("AGENT_CONNECTION_MODE")!="local" or os.environ.get("AGENT_RUNTIME_ARN"):
        raise RuntimeError("Fixture requires explicit local mode without a Runtime ARN")
    class PrivateURLFilter(logging.Filter):
        def filter(self,record):
            if isinstance(record.msg,str):record.msg=redact(record.msg)
            if isinstance(record.args,tuple):record.args=tuple(redact(v) for v in record.args)
            return True
    logging.getLogger('uvicorn.access').addFilter(PrivateURLFilter())
    samples=Path(os.environ["HYBRID_FIXTURE_SAMPLES"]);blobs=original_data(samples)
    state,save=install_boundary(os.environ["HYBRID_FIXTURE_GUARD"])
    import source_documents
    class MemoryS3:
        def get_object(self,*,Bucket,Key):
            if Bucket!="offline-fixture":raise ValueError("Unexpected fixture bucket")
            key=Key.removeprefix(f"rag/generations/{GENERATION}/sources/").rsplit(".",1)[0]
            if Key!=f"rag/generations/{GENERATION}/sources/{key}."+("pdf" if key=="harbor-menu" else "md"):
                raise ValueError("Unexpected fixture source")
            data=blobs[key];state["source_reads"]+=1;save()
            return {"ContentLength":len(data),"Body":io.BytesIO(data)}
    source_documents._get_s3_client=lambda _region:MemoryS3()
    import app
    async def forbidden_runtime(*args,**kwargs):
        raise RuntimeError("Real Runtime forbidden in fixture")
        yield
    app._aws_sse_lines=forbidden_runtime


def serve_stub(port,samples,receipt):
    from aiohttp import web
    state={"mode":"local_fixture","requests":[]}
    async def health(_request):
        return web.json_response({"ready":True,"mode":"local_fixture"})
    async def invoke(request):
        payload=await request.json();index=len(state["requests"])
        if index>=7 or payload.get("prompt")!=QUESTIONS[index]:
            return web.json_response({"error":"Unexpected fixture request"},status=409)
        identity=hashlib.sha256(str(payload.get("conversation_id","")).encode()).hexdigest()
        if not payload.get("conversation_id"):
            return web.json_response({"error":"Missing fixture conversation"},status=409)
        if index in (1,2,3) and identity!=state["requests"][0]["conversation_hash"]:
            return web.json_response({"error":"Conversation A mismatch"},status=409)
        if index==4 and identity==state["requests"][0]["conversation_hash"]:
            return web.json_response({"error":"Conversation B must be fresh"},status=409)
        if index in (5,6) and identity!=state["requests"][4]["conversation_hash"]:
            return web.json_response({"error":"Conversation B mismatch"},status=409)
        state["requests"].append({"slot":f"L{index+1}","conversation_hash":identity})
        write_json(Path(receipt),state)
        response=web.StreamResponse(headers={"Content-Type":"text/event-stream"})
        await response.prepare(request)
        for event in [answer(index,samples),{"done":True}]:
            await response.write(("data: "+json.dumps(event)+"\n\n").encode())
        await response.write_eof()
        return response
    app=web.Application();app.router.add_get("/health",health);app.router.add_post("/invocations",invoke)
    write_json(Path(receipt),state)
    web.run_app(app,host="127.0.0.1",port=port,print=None)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,required=True)
    parser.add_argument("--samples",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    if not 1024<=args.port<=65535 or args.port==8010:raise SystemExit("Invalid fixture port")
    serve_stub(args.port,args.samples,args.receipt)
