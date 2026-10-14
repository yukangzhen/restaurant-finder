import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.evaluation import document_followups as evaluation


class FollowupEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=evaluation.load_dataset()
        cls.gold=evaluation.compile_dataset(cls.dataset)
        cls.observations=evaluation.run_offline(cls.dataset,cls.gold)

    def test_all_24_cases_all_variants_and_executed_turns_pass(self):
        report=evaluation.evaluate(self.dataset,self.observations,self.gold)
        self.assertTrue(report["passed"])
        self.assertEqual(report["observed_cases"],24)
        self.assertEqual(sum(len(v["turns"]) for c in self.observations for v in c["variants"]),63)

    def test_missing_duplicate_unknown_variant_or_turn_cannot_pass(self):
        self.assertFalse(evaluation.evaluate(self.dataset,self.observations[:-1],self.gold)["passed"])
        for values in (self.observations+[self.observations[0]],[{"case_id":"unknown","variants":[]}]):
            with self.assertRaises(ValueError): evaluation.evaluate(self.dataset,values,self.gold)
        for mutate in (lambda value:value[0]["variants"].clear(),lambda value:value[0]["variants"][0]["turns"].pop(),
                       lambda value:value[0]["variants"].append(value[0]["variants"][0])):
            values=copy.deepcopy(self.observations);mutate(values)
            self.assertFalse(evaluation.evaluate(self.dataset,values,self.gold)["passed"])

    def test_observation_scope_item_approval_source_qualifiers_counts_and_order_mutations_fail(self):
        mutations=[("scope",lambda t:t.update(context_targets=["demo-sakura-table"])),
                   ("item",lambda t:t.update(effective_item="tomato pasta")),
                   ("approval",lambda t:t.update(response_status="blocked")),
                   ("source",lambda t:t["citations"][0].update(generation_id="f"*64)),
                   ("qualifiers",lambda t:t.update(text=t["text"].replace("24 hours","48 hours"))),
                   ("calls",lambda t:t["calls"].update(rewrite=1))]
        for name,mutate in mutations:
            with self.subTest(name=name):
                values=copy.deepcopy(self.observations);mutate(values[0]["variants"][0]["turns"][-1])
                self.assertFalse(evaluation.evaluate(self.dataset,values,self.gold)["passed"])
        values=copy.deepcopy(self.observations)
        actual=values[2]["variants"][0]["turns"][-1]
        self.assertIn("RM4",actual["text"])
        actual["text"]=actual["text"].replace("RM4", "RM999")
        self.assertFalse(evaluation.evaluate(self.dataset,values,self.gold)["passed"])
        values=copy.deepcopy(self.observations);values[0]["variants"][0]["turns"].reverse()
        self.assertFalse(evaluation.evaluate(self.dataset,values,self.gold)["passed"])

    def test_provider_execution_is_independent_of_expected_context(self):
        from types import SimpleNamespace
        altered=copy.deepcopy(self.dataset.cases[0])
        altered.variants[0].turns[-1].expected.context_targets=["demo-sakura-table"]
        subset=SimpleNamespace(cases=[altered]);gold=evaluation.compile_dataset(subset)
        actual=evaluation.run_offline(subset,gold)
        self.assertEqual(actual[0]["variants"][0]["turns"][-1]["context_targets"],["demo-harbor-pasta"])

    def test_invalid_dataset_and_nonfinite_json_return_two_without_new_report(self):
        with TemporaryDirectory() as directory:
            bad=Path(directory)/"bad.json";report=Path(directory)/"report.json"
            bad.write_text('{"schema_version":NaN}',encoding="utf-8")
            with redirect_stdout(io.StringIO()): code=evaluation.main(["--offline","--dataset",str(bad),"--output",str(report)])
            self.assertEqual(code,2);self.assertFalse(report.exists())
            data=self.dataset.model_dump();data["cases"].pop()
            bad.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaises(ValueError): evaluation.load_dataset(bad)

    def test_reports_exclude_questions_quotes_context_owners_and_provider_bodies(self):
        report=evaluation.evaluate(self.dataset,self.observations,self.gold)
        with TemporaryDirectory() as directory:
            path=Path(directory)/"report.json";evaluation.write_report(report,path)
            text=path.read_text()+path.with_suffix(".md").read_text()
        for forbidden in ("And what about its cancellation fee?","Reservations at Harbor", "actor_digest","payload_digest","SIMULATED_PRIVATE"):
            self.assertNotIn(forbidden,text)
