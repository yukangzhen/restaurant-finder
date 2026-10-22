import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from acceptance import (
    AcceptanceError, Controller, Ledger, QUESTIONS, TEXTBOX,
    child_path, cli_result, function, redact, validate_function_shape, validate_origin,
)


class FakeCLI:
    def __init__(self, root):
        self.root = Path(root)
        self.calls = []
        self.error_at = None
        self.read = {"value":QUESTIONS[0], "boxes":1, "sends":1, "enabled":True, "pending":False}

    def snapshot(self):
        self.calls.append("snapshot")
        return TEXTBOX + " Source 1 (answer 1)"

    def run(self, code):
        self.calls.append(code)
        if self.error_at == "fill" and ".fill(" in code:
            raise AcceptanceError("CLI process failed")
        if ".fill(" in code:
            return {"filled":True}
        if "inputValue()" in code:
            return self.read
        return {"count":1}

    def prepare(self, code):
        validate_function_shape(code)
        self.calls.append("compile:" + code)
        if self.error_at == "compile":
            raise AcceptanceError("Compilation failed")
        path = self.root / "prepared.js"
        path.write_text(code)
        return path

    def execute(self, path):
        self.calls.append("dispatch")
        path.unlink(missing_ok=True)
        if self.error_at == "dispatch":
            raise subprocess.TimeoutExpired("node",45)
        return {"dispatched":True,"opened":True,"downloaded":True}


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = Ledger(self.root / "attempts.json")
        self.cli = FakeCLI(self.root)
        self.controller = Controller(self.cli,self.ledger,"http://127.0.0.1:8011","#observed-submit")
        self.controller.set_chat("A")

    def test_top_level_await_is_rejected_before_dispatch(self):
        with self.assertRaises(AcceptanceError):
            self.cli.prepare("await page.click('button')")
        validate_function_shape(function("return {};"))
        self.assertEqual(self.ledger.load()["attempts"],0)

    def test_failed_fill_cannot_fall_through(self):
        self.cli.error_at="fill"
        with self.assertRaises(AcceptanceError):
            self.controller.submit("L1")
        self.assertNotIn("dispatch",self.cli.calls)
        self.assertEqual(self.ledger.load()["slots"]["L1"],"UNUSED")

    def test_cli_semantic_error_with_zero_exit_is_failure(self):
        for output in ('{"isError":true}', '{"result":{"error":"bad"}}',
                       '{"result":"### Error\\nSyntaxError"}'):
            with self.assertRaises(AcceptanceError):
                cli_result(SimpleNamespace(returncode=0,stdout=output))
        with self.assertRaises(AcceptanceError):
            cli_result(SimpleNamespace(returncode=1,stdout="{}"))

    def test_wrong_or_empty_readback_cannot_reserve(self):
        for value in ("", "wrong"):
            self.cli.read["value"]=value
            with self.assertRaises(AcceptanceError):
                self.controller.submit("L1")
        self.assertEqual(self.ledger.load()["attempts"],0)

    def test_ambiguous_or_missing_controls_cannot_submit(self):
        for field in ("boxes","sends"):
            for value in (0,2):
                self.cli.read[field]=value
                with self.assertRaises(AcceptanceError):
                    self.controller.submit("L1")
            self.cli.read[field]=1
        self.assertNotIn("dispatch",self.cli.calls)

    def test_exact_fill_reserves_and_dispatches_once(self):
        self.controller.submit("L1")
        self.assertEqual(self.cli.calls.count("dispatch"),1)
        self.assertEqual(self.ledger.load()["attempts"],1)
        self.assertEqual(self.ledger.data["slots"]["L1"],"SUBMITTED")

    def test_dispatch_timeout_consumes_and_cannot_resend(self):
        self.cli.error_at="dispatch"
        with self.assertRaises(subprocess.TimeoutExpired):
            self.controller.submit("L1")
        self.assertEqual(self.ledger.load()["slots"]["L1"],"UNCERTAIN")
        with self.assertRaises(AcceptanceError):
            self.controller.submit("L1")
        self.assertEqual(self.cli.calls.count("dispatch"),1)

    def test_restarted_controller_cannot_repeat_a_slot(self):
        self.controller.submit("L1")
        other=Controller(self.cli,Ledger(self.ledger.path),"http://127.0.0.1:8011","#observed-submit")
        with self.assertRaises(AcceptanceError):
            other.submit("L1")
        self.assertEqual(other.ledger.load()["attempts"],1)

    def test_failed_seed_and_wrong_conversation_prevent_followups(self):
        with self.assertRaises(AcceptanceError):
            self.controller.submit("L2")
        with self.assertRaises(AcceptanceError):
            self.controller.set_chat("B")
        self.controller.submit("L1")
        self.ledger.state("L1","FAIL")
        with self.assertRaises(AcceptanceError):
            self.controller.submit("L2")

    def test_source_and_download_limits_are_separate(self):
        for _ in range(18):
            self.controller.source_action("button","Source 1 (answer 1)")
        with self.assertRaises(AcceptanceError):
            self.controller.source_action("button","Source 1 (answer 1)")
        for index in range(4):
            self.controller.source_action("button","Source 1 (answer 1)",f"source-{index}.md")
        with self.assertRaises(AcceptanceError):
            self.controller.source_action("button","Source 1 (answer 1)","fifth.md")
        self.assertEqual(self.ledger.load()["attempts"],0)

    def test_serialized_data_and_origin_path_validation(self):
        data='"; $(whoami)\\n`quote`'
        code=function("const value="+json.dumps(data)+";return value;")
        self.assertIn(json.dumps(data),code)
        validate_function_shape(code)
        for url in ("https://example.com","http://localhost:8011","http://127.0.0.1:8010",
                    "http://127.0.0.1:8011/path","http://x@127.0.0.1:8011"):
            with self.assertRaises(AcceptanceError):
                validate_origin(url,"local")
        for name in ("../secret","a/b","..","/root","a\\b"):
            with self.assertRaises(AcceptanceError):
                child_path(self.root,name)
        with self.assertRaises(AcceptanceError):
            self.ledger.check("L8")

    def test_tokens_are_redacted_from_nested_artifacts(self):
        raw={"result":[{"text":"Source 1 (answer 1) http://127.0.0.1:8011/project/file/x?session_id=synthetic-secret"}],
             "other":"/project/file/x?token=another-secret", "query":"sessionId=third-secret"}
        output=json.dumps(redact(raw))
        for secret in ("synthetic-secret","another-secret","third-secret"):
            self.assertNotIn(secret,output)
        self.assertIn("Source 1",output)

    def test_compiler_failure_before_reservation(self):
        self.cli.error_at="compile"
        with self.assertRaises(AcceptanceError):
            self.controller.submit("L1")
        self.assertEqual(self.ledger.load()["attempts"],0)

    def test_pending_message_cannot_submit(self):
        self.cli.read["pending"]=True
        with self.assertRaises(AcceptanceError):
            self.controller.submit("L1")
        self.assertEqual(self.ledger.load()["attempts"],0)

    def test_live_mode_requires_explicit_verified_frozen_ledger(self):
        with self.assertRaises(AcceptanceError):
            Ledger(self.root/"live.json","live")
        with self.assertRaises(AcceptanceError):
            Ledger(self.ledger.path,"live")

    def test_only_submitted_slots_can_pass(self):
        with self.assertRaises(AcceptanceError):
            self.ledger.state("L1","PASS")
        self.controller.submit("L1")
        self.ledger.state("L1","PASS")
        self.assertEqual(self.ledger.load()["slots"]["L1"],"PASS")

    def test_source_read_waits_without_click_or_submission(self):
        self.controller.read_source("Source 1 (answer 1)", ["Harbor", "RM32"])
        code=self.cli.calls[-1]
        self.assertIn("required.every",code)
        self.assertIn("deadline",code)
        self.assertNotIn(".click(",code)
        self.assertNotIn(".press(",code)
        self.assertEqual(self.ledger.load()["source_opens"],0)
        self.assertEqual(self.ledger.data["attempts"],0)
        with self.assertRaises(AcceptanceError):
            self.controller.read_source("Source 1 (answer 1)", [])

    def test_new_chat_confirms_observed_dialog_before_marking_fresh(self):
        for slot in ("L1","L2","L3","L4"):
            self.ledger.data['slots'][slot]='PASS'
        self.ledger.save()
        self.controller.inspect=lambda: {'buttons':[{'id':'new-chat-button'}],
                                         'text':'Create New Chat'}
        self.cli.snapshot=lambda:'Create New Chat Confirm'
        original=self.cli.run
        self.cli.run=lambda code: ({'fresh':True} if 'const deadline' in code else original(code))
        self.controller.new_chat('B')
        self.assertEqual(self.ledger.load()['chat'],'B')
        self.assertTrue(any("name:'Confirm'" in c for c in self.cli.calls))
        self.assertFalse(any('.press(' in c for c in self.cli.calls))
        self.assertEqual(self.ledger.data['attempts'],0)


if __name__ == "__main__":
    unittest.main()
