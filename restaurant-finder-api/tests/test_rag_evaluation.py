import copy
import importlib
import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import shutil
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from src.evaluation import rag
from src.evaluation.rag_offline import cloud_clients_forbidden, run_offline


class RagEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = rag.load_dataset()
        cls.grounded = rag.compile_dataset(cls.dataset)
        cls.observations = run_offline(cls.dataset, cls.grounded)

    def changed(self, case_id="harbor_price_v2", **changes):
        observations = copy.deepcopy(self.observations)
        observation = next(o for o in observations if o.case_id == case_id)
        for key, value in changes.items():
            setattr(observation, key, value)
        return observations

    def score(self, observations, mode="offline_regression"):
        return rag.evaluate(self.dataset, observations, mode=mode, grounded=self.grounded)

    def test_all_cases_grounded_and_complete_offline_passes(self):
        report = self.score(self.observations)
        self.assertGreaterEqual(report["dataset_cases"], 14)
        self.assertTrue(report["complete"])
        self.assertTrue(report["passed"])
        self.assertEqual(report["unmeasured_checks"], 0)
        self.assertEqual(report["origin_verification"], "simulated_dependencies")

    def test_versions_are_explicit_and_different(self):
        versions = {o.case_id: o for o in self.observations}
        self.assertIn("RM32", versions["harbor_price_v2"].text)
        self.assertIn("RM28", versions["harbor_price_v1"].text)
        self.assertNotEqual(versions["harbor_price_v1"].generation_id, versions["harbor_price_v2"].generation_id)

    def test_wrong_dish_from_right_source_is_not_a_correct_answer(self):
        from src.application.document_rag.workflow import render_document_answer
        from src.domain.document_rag import RagAnswerDraft
        original = next(o for o in self.observations if o.case_id == "harbor_price_v2")
        manifest, _ = self.grounded[original.case_id]
        draft = RagAnswerDraft(status="answered", selections=[{"chunk_id": original.citations[0].chunk_id,
                              "quote": "Tomato pasta - RM24 per serving."}])
        text, citations = render_document_answer(draft, original.evidence, manifest)
        report = self.score(self.changed(text=text, citations=citations))
        row = next(row for row in report["cases"] if row["case_id"] == original.case_id)
        self.assertEqual(row["checks"]["citation_chunk_id"], "pass")
        self.assertEqual(row["checks"]["answer_text"], "fail")
        self.assertFalse(report["passed"])

    def test_wrong_prices_extra_claims_and_false_abstention_fail(self):
        original = self.observations[0]
        for changes in [{"text": original.text.replace("RM32", "RM99")},
                        {"text": original.text + "\nIt offers valet parking."},
                        {"status": "insufficient_evidence", "citations": [], "text": "Not enough evidence."}]:
            with self.subTest(changes=changes):
                self.assertFalse(self.score(self.changed(**changes))["passed"])
        self.assertFalse(self.score(self.changed("missing_parking", text="Harbor does not offer valet parking."))["passed"])

    def test_every_citation_field_is_checked(self):
        citation = self.observations[0].citations[0]
        mutations = {"label": "Source 2", "generation_id": "0" * 64, "document_id": "sakura-menu",
                     "chunk_id": "0" * 64, "source_hash": "0" * 64, "filename": "other.pdf",
                     "version": "v1", "page": 2}
        for field, value in mutations.items():
            with self.subTest(field=field):
                observed = citation.model_copy(update={field: value})
                report = self.score(self.changed(citations=[observed]))
                self.assertFalse(report["passed"])
                self.assertEqual(report["cases"][0]["checks"]["citation_" + field], "fail")
        policy = next(o for o in self.observations if o.case_id == "harbor_fee_alias")
        for field, value in {"section": "Other section", "line_start": 6, "line_end": 9}.items():
            with self.subTest(field=field):
                self.assertFalse(self.score(self.changed(policy.case_id, citations=[policy.citations[0].model_copy(update={field:value})]))["passed"])

    def test_missing_and_extra_citations_and_wrong_restaurant_fail(self):
        citation = self.observations[0].citations[0]
        for changes in [{"citations": []}, {"citations": [citation, citation.model_copy(update={"label":"Source 2"})]},
                        {"restaurant_id": "demo-sakura-table"}, {"generation_id": "0" * 64}]:
            with self.subTest(changes=changes):
                self.assertFalse(self.score(self.changed(**changes))["passed"])

    def test_missing_evidence_and_counters_are_unmeasured_only_for_imports(self):
        values = copy.deepcopy(self.observations)
        for value in values:
            value.evidence = None
            value.calls = None
            value.origin = "recorded"
        imported = self.score(values, mode="imported_observations")
        self.assertTrue(imported["passed"])
        self.assertGreater(imported["unmeasured_checks"], 0)
        self.assertEqual(imported["origin_verification"], "imported_unverified")
        values[0].origin = "manual"
        with self.assertRaises(ValueError):
            self.score(values)
        for value in values:
            value.origin = "offline_simulated"
        self.assertFalse(self.score(values)["passed"])

    def test_scope_calls_and_evidence_integrity_are_checked(self):
        original = self.observations[0]
        corrupt = original.evidence[0].model_copy(update={"text":"CORRUPTED_FIXTURE"})
        for changes in [{"calls": rag.Calls(embedding=2,retrieval=1,selector=1,rewrite=0)},
                        {"query_document_type":"policy"}, {"evidence":[]}, {"evidence":[corrupt]},
                        {"evidence":[*original.evidence, original.evidence[0]]}]:
            with self.subTest(changes=changes):
                self.assertFalse(self.score(self.changed(**changes))["passed"])
        clarified = next(o for o in self.observations if o.case_id == "missing_restaurant")
        self.assertEqual(clarified.calls, rag.Calls(embedding=0,retrieval=0,selector=0,rewrite=0))
        full_name = next(o for o in self.observations if o.case_id == "harbor_fee")
        short_name = next(o for o in self.observations if o.case_id == "harbor_fee_alias")
        self.assertIsNone(full_name.query_document_type)
        self.assertEqual(short_name.query_document_type,"policy")

    def test_missing_duplicate_unknown_cases_do_not_pass(self):
        report = self.score(self.observations[:-1])
        self.assertFalse(report["complete"])
        self.assertFalse(report["passed"])
        for values in [self.observations + [self.observations[0]],
                       [self.observations[0].model_copy(update={"case_id":"unknown"})]]:
            with self.assertRaises(ValueError):
                self.score(values)

    def test_bad_dataset_quote_version_location_and_exclusions_rejected(self):
        for changes in [{"quote":"Mushroom pasta - RM999."}, {"version":"v9"}, {"page":2}]:
            data = self.dataset.model_dump()
            data["cases"][0]["expected"]["quotes"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                rag.compile_dataset(rag.Dataset.model_validate(data))
        data = self.dataset.model_dump()
        data["cases"][0]["expected"]["forbidden_phrases"] = ["RM32"]
        with self.assertRaises(ValueError):
            rag.compile_dataset(rag.Dataset.model_validate(data))

    def test_strict_schemas_empty_duplicate_and_oversize_inputs(self):
        dataset = self.dataset.model_dump()
        for change in [{**dataset,"extra":"untrusted"}, {**dataset,"cases":[]},
                       {**dataset,"cases":[*dataset["cases"],dataset["cases"][0]]}]:
            with self.assertRaises(ValidationError):
                rag.Dataset.model_validate(change)
        observation = self.observations[0].model_dump()
        for change in [{**observation,"extra":1}, {**observation,"text":"x"*15001},
                       {**observation,"status":"invented"}, {**observation,"case_id":"bad|markdown"}]:
            with self.assertRaises(ValidationError):
                rag.Observation.model_validate(change)
        with TemporaryDirectory() as directory:
            path=Path(directory)/"oversize.json"
            path.write_bytes(b" "*(rag.MAX_INPUT_BYTES+1))
            with self.assertRaises(ValueError):
                rag.read_json(path)

    def test_cli_healthy_failure_incomplete_invalid_and_safe_reports(self):
        with TemporaryDirectory() as directory:
            output=Path(directory)/"result.json"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(rag.main(["--offline","--output",str(output)]),0)
            self.assertTrue(json.loads(output.read_text())["passed"])
            self.assertTrue(output.with_suffix(".md").exists())
            for observations in [self.changed(text="SECRET_INPUT_BODY"),self.observations[:-1]]:
                path=Path(directory)/"observations.json"
                path.write_text(json.dumps({"schema_version":1,"observations":[o.model_dump() for o in observations]}))
                with redirect_stdout(io.StringIO()) as captured:
                    self.assertEqual(rag.main(["--observations",str(path),"--output",str(output)]),1)
                self.assertNotIn("SECRET_INPUT_BODY",captured.getvalue()+output.read_text())
            path.write_text('{"SECRET_INPUT_BODY":true}')
            with redirect_stdout(io.StringIO()) as captured:
                self.assertEqual(rag.main(["--observations",str(path),"--output",str(output)]),2)
            self.assertNotIn("SECRET_INPUT_BODY",captured.getvalue())

    def test_cli_wrong_citation_has_nonzero_exit(self):
        values=self.changed(citations=[])
        with TemporaryDirectory() as directory:
            path=Path(directory)/"observations.json"
            path.write_text(json.dumps({"schema_version":1,"observations":[o.model_dump() for o in values]}))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(rag.main(["--observations",str(path),"--output",str(Path(directory)/"report.json")]),1)

    def test_offline_guard_detects_clients_even_when_exception_caught(self):
        import boto3
        with self.assertRaises(AssertionError), cloud_clients_forbidden():
            try:
                boto3.client("bedrock")
            except AssertionError:
                pass

    def test_fresh_offline_imports_and_execution_do_not_load_live_evaluation_sdk(self):
        script = '''
import sys, boto3
from unittest.mock import patch
with patch("boto3.client",side_effect=AssertionError), patch("boto3.Session",side_effect=AssertionError):
    from src.evaluation import rag
    assert rag.main(["--list-cases"]) == 0
    dataset=rag.load_dataset()
    from src.evaluation.rag_offline import run_offline
    assert rag.evaluate(dataset,run_offline(dataset,rag.compile_dataset(dataset)),mode="offline_regression")["passed"]
assert "src.evaluation.client" not in sys.modules
assert "bedrock_agentcore_starter_toolkit" not in sys.modules
'''
        env={**os.environ,"PROMPT_MANIFEST_PATH":str(rag.API_ROOT/".generated"/"offline-no-manifest.json"),
             "REQUIRE_PROMPT_MANIFEST":"false","AWS_EC2_METADATA_DISABLED":"true"}
        result=subprocess.run([sys.executable,"-c",script],cwd=rag.API_ROOT,env=env,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_legacy_exports_resolve_lazily_and_unknown_names_fail(self):
        evaluation=importlib.import_module("src.evaluation")
        self.assertIn("EvaluationRunner",dir(evaluation))
        for name,module in evaluation._EXPORTS.items():
            sentinel=object()
            with patch.object(evaluation,"import_module",return_value=SimpleNamespace(**{name:sentinel})) as load:
                self.assertIs(getattr(evaluation,name),sentinel)
                load.assert_called_once_with("src.evaluation."+module)
        with self.assertRaises(AttributeError):
            getattr(evaluation,"unrecognized_export")

    def test_partial_price_gold_and_nonfinite_json_rejected(self):
        with self.assertRaises(ValidationError):
            rag.GoldQuote(document_id="harbor-menu",version="v2",quote="RM32",page=1)
        with TemporaryDirectory() as directory:
            path=Path(directory)/"nonfinite.json"
            path.write_text('{"value":NaN}')
            with self.assertRaises(ValueError):
                rag.read_json(path)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        import yaml
        path=rag.API_ROOT.parent/".github"/"workflows"/"ci.yml"
        self.workflow=yaml.load(path.read_text(),Loader=yaml.BaseLoader)

    def test_workflow_is_offline_read_only_and_actions_are_pinned(self):
        self.assertEqual(set(self.workflow["on"]),{"push","pull_request"})
        self.assertEqual(self.workflow["permissions"],{"contents":"read"})
        self.assertEqual(self.workflow["jobs"]["quality"]["if"],"always()")
        self.assertEqual(set(self.workflow["jobs"]["quality"]["needs"]),{"api","ui","infrastructure"})
        for job in self.workflow["jobs"].values():
            for step in job["steps"]:
                if "uses" in step:
                    self.assertRegex(step["uses"],r"^[a-zA-Z0-9-]+/[a-zA-Z0-9-]+@[a-f0-9]{40}$")
                self.assertNotIn("continue-on-error",step)
                self.assertNotIn("secrets.",json.dumps(step))
                self.assertNotIn("deploy",step.get("run",""))

    def test_aggregate_shell_rejects_failed_cancelled_and_skipped_jobs(self):
        bash=shutil.which("bash")
        if sys.platform=="win32":
            bash="C:/Program Files/Git/bin/bash.exe"
        if not bash or not Path(bash).exists():
            self.skipTest("Bash unavailable for local workflow verification")
        script=self.workflow["jobs"]["quality"]["steps"][0]["run"]
        with TemporaryDirectory() as directory:
            for variable in ["API_RESULT","UI_RESULT","INFRA_RESULT"]:
                for status in ["success","failure","cancelled","skipped"]:
                    values={"API_RESULT":"success","UI_RESULT":"success","INFRA_RESULT":"success",variable:status,
                            "GITHUB_STEP_SUMMARY":(Path(directory)/"summary.md").as_posix()}
                    result=subprocess.run([bash,"--noprofile","--norc","-e","-o","pipefail","-c",script],
                                          env={**os.environ,**values},capture_output=True,text=True,timeout=10)
                    with self.subTest(variable=variable,status=status):
                        self.assertEqual(result.returncode==0,status=="success",result.stderr)

    def test_logged_test_steps_preserve_a_failed_command_exit(self):
        bash=shutil.which("bash")
        if sys.platform=="win32":
            bash="C:/Program Files/Git/bin/bash.exe"
        if not bash or not Path(bash).exists():
            self.skipTest("Bash unavailable for local workflow verification")
        with TemporaryDirectory() as directory:
            for job_name in ["api","ui","infrastructure"]:
                job=self.workflow["jobs"][job_name]
                self.assertEqual(job["defaults"]["run"]["shell"],"bash")
                steps=[step for step in job["steps"] if "| tee" in step.get("run","")]
                self.assertEqual(len(steps),1)
                script=steps[0]["run"]
                command=next(line for line in script.splitlines() if "| tee" in line).split("| tee",1)[0]
                for replacement in ["true ","false "]:
                    # Execute the actual step's flags; do not supply pipefail from the test.
                    result=subprocess.run([bash,"--noprofile","--norc","-c",script.replace(command,replacement,1)],
                                          cwd=directory,env=os.environ.copy(),capture_output=True,text=True,timeout=10)
                    with self.subTest(job=job_name,command=replacement.strip()):
                        self.assertEqual(result.returncode==0,replacement.strip()=="true",result.stderr)


if __name__ == "__main__":
    unittest.main()
