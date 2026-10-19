import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.evaluation import document_retrieval as e


class RetrievalEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=e.load_dataset()
        cls.observations=e.run_offline(cls.dataset)

    def test_complete_actual_execution_passes(self):
        report=e.evaluate(self.dataset,self.observations)
        self.assertTrue(report["passed"])
        self.assertTrue(report["complete"])
        self.assertEqual(report["observed_cases"],24)
        self.assertEqual(report["observed_variants"],57)
        self.assertGreater(report["measured_checks"],1000)

    def changed(self,case=0,variant=0):
        obs=copy.deepcopy(self.observations)
        return obs,obs[case]["variants"][variant]["result"]

    def assert_rejected(self,obs):
        self.assertFalse(e.evaluate(self.dataset,obs)["passed"])

    def test_missing_duplicate_unknown_and_reordered_observations_fail(self):
        self.assert_rejected(self.observations[:-1])
        for obs in (self.observations+[self.observations[0]],
                    [{"case_id":"R99","variants":[]}]):
            with self.assertRaises(ValueError): e.evaluate(self.dataset,obs)
        obs=copy.deepcopy(self.observations)
        obs[5]["variants"].reverse()
        self.assert_rejected(obs)
        obs=copy.deepcopy(self.observations)
        obs[5]["variants"].pop()
        self.assert_rejected(obs)

    def test_dataset_requires_every_frozen_variant(self):
        raw=self.dataset.model_dump()
        raw["cases"][14]["variants"].pop()
        with self.assertRaises(ValueError): e.Dataset.model_validate(raw)
        raw=self.dataset.model_dump();raw["cases"].reverse()
        with self.assertRaises(ValueError): e.Dataset.model_validate(raw)

    def test_forged_counts_scope_generation_and_integrity_fail(self):
        for field,value in (("embedding",0),("retrieval",0),("pin",0),("selector",0)):
            obs,result=self.changed();result[field]=value
            self.assert_rejected(obs)
        obs,result=self.changed()
        result["scopes"][0]["restaurant_id"]=e.S
        self.assert_rejected(obs)
        obs,result=self.changed()
        result["scopes"][0]["document_type"]="policy"
        self.assert_rejected(obs)
        for changes in ({"generation_id":"f"*64},{"source_hash":"f"*64},{"text":"forged"}):
            obs,result=self.changed()
            result["evidence"][0]=result["evidence"][0].model_copy(update=changes)
            self.assert_rejected(obs)

    def test_fabricated_vector_distance_fails_even_if_diagnostic_is_also_changed(self):
        obs,result=self.changed(2)
        result["evidence"][0]=result["evidence"][0].model_copy(update={"distance":.9})
        result["diagnostics"][0]=replace(result["diagnostics"][0],vector_distances=(.9,))
        self.assert_rejected(obs)

    def test_fusion_and_keyword_rank_mutations_fail(self):
        obs,result=self.changed(3)
        diag=result["diagnostics"][0]
        result["diagnostics"][0]=replace(diag,fused=tuple(reversed(diag.fused)))
        self.assert_rejected(obs)
        obs,result=self.changed(3);diag=result["diagnostics"][0]
        result["diagnostics"][0]=replace(diag,fused=(replace(diag.fused[0],score=0.0),*diag.fused[1:]))
        self.assert_rejected(obs)
        obs,result=self.changed(18);diag=result["diagnostics"][0]
        result["diagnostics"][0]=replace(diag,keyword=tuple(reversed(diag.keyword)))
        self.assert_rejected(obs)

    def test_forged_reads_and_missing_diagnostic_fail(self):
        obs,result=self.changed()
        result["reads"]=[]
        self.assert_rejected(obs)
        obs,result=self.changed()
        result["diagnostics"]=[]
        self.assert_rejected(obs)

    def test_stripped_qualifiers_and_forged_originals_fail(self):
        obs,result=self.changed()
        result["outcome"]=result["outcome"].model_copy(update={"text":result["outcome"].text.replace("milk","water")})
        self.assert_rejected(obs)
        obs,result=self.changed()
        source=result["outcome"].citations[0].model_copy(update={"source_hash":"f"*64})
        result["outcome"]=result["outcome"].model_copy(update={"citations":[source]})
        self.assert_rejected(obs)
        obs,result=self.changed(22)
        turns=result["conversations"][0]["variants"][0]["turns"]
        turns[-1]["text"]=turns[-1]["text"].replace("dinner","breakfast")
        self.assert_rejected(obs)

    def test_conversation_calls_context_or_sources_cannot_be_fabricated(self):
        for field,value in (("calls",{}),("context_targets",[e.S]),("citations",[])):
            obs,result=self.changed(23)
            turn=result["conversations"][0]["variants"][0]["turns"][-1]
            if field=="calls":
                turn[field]["retrieval"]=0
            else:
                turn[field]=value
            self.assert_rejected(obs)

    def test_reports_are_safe_and_cli_exits_are_meaningful(self):
        report=e.evaluate(self.dataset,self.observations)
        with TemporaryDirectory(prefix="retrieval-report-") as temp:
            path=Path(temp)/"report.json"
            e.write_report(report,path)
            body=path.read_text()+path.with_suffix(".md").read_text()
            for private in ("Mushroom pasta", "PRIVATE_SIMULATED_PROVIDER_BODY", "actor_digest", "http://", "https://"):
                self.assertNotIn(private,body)
            self.assertEqual(json.loads(path.read_text())["observed_variants"],57)
            with patch.object(e,"run_offline",return_value=self.observations):
                self.assertEqual(e.main(["--offline","--output",str(path)]),0)
            with patch.object(e,"run_offline",return_value=self.observations[:-1]):
                self.assertEqual(e.main(["--offline","--output",str(path)]),1)
            with patch.object(e,"run_offline",side_effect=ValueError("private")):
                self.assertEqual(e.main(["--offline","--output",str(path)]),2)
