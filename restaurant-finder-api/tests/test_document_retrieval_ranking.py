import math
import unittest
from dataclasses import FrozenInstanceError

from src.application.document_rag.ranking import keyword_rank, reciprocal_rank_fusion, tokenize


class RankingTests(unittest.TestCase):
    def test_tokenizer_has_one_declared_unicode_rule(self):
        self.assertEqual(tokenize("  CAFÉ\tCafe\u0301_32.50! "), ["café", "café", "32", "50"])
        self.assertEqual(tokenize("!!!___"), [])

    def test_bm25_matches_independent_hand_calculation(self):
        # N=2, df(apple)=2, lengths 3 and 2, average=2.5.
        actual = keyword_rank("apple apple", [("a", "apple apple pear"), ("b", "apple plum")])
        idf = math.log(1.2)
        expected = {"a": idf * 2 * 2.2 / (2 + 1.2 * (.25 + .75 * 3 / 2.5)),
                    "b": idf * 2.2 / (1 + 1.2 * (.25 + .75 * 2 / 2.5))}
        self.assertEqual([c.key for c in actual], ["a", "b"])
        for c in actual:
            self.assertAlmostEqual(c.score, expected[c.key], places=14)
        self.assertEqual(actual, keyword_rank("apple", [("a", "apple apple pear"), ("b", "apple plum")]))

    def test_keyword_ties_use_key_not_input_order(self):
        self.assertEqual(keyword_rank("pasta", [("z", "pasta"), ("a", "pasta")]),
                         keyword_rank("pasta", [("a", "pasta"), ("z", "pasta")]))
        self.assertEqual([c.key for c in keyword_rank("pasta", [("z", "pasta"), ("a", "pasta")])], ["a", "z"])

    def test_empty_pool_tokens_and_nonmatching_terms(self):
        for q, pool in [("x", []), ("!!!", [("a", "pasta")]), ("x", [("a", "!!!")]), ("unknown", [("a", "pasta")])]:
            self.assertEqual(keyword_rank(q, pool), ())

    def test_scoped_statistics_are_local_and_bounded(self):
        local = keyword_rank("apple", [("a", "apple"), ("b", "pear")])
        other = keyword_rank("apple", [("a", "apple"), ("b", "pear"), ("c", "apple")])
        self.assertNotEqual(local[0].score, other[0].score)
        with self.assertRaises(ValueError):
            keyword_rank("x", [(str(i), "x") for i in range(49)])

    def test_fusion_matches_the_prd_numerical_example(self):
        actual = reciprocal_rank_fusion(["a", "b"], ["b", "c"])
        self.assertEqual([c.key for c in actual], ["b", "a", "c"])
        self.assertAlmostEqual(actual[0].score, 1/62 + 1/61, places=15)
        self.assertEqual((actual[0].vector_rank, actual[0].keyword_rank), (2, 1))
        self.assertEqual(actual[2].vector_rank, None)

    def test_fusion_empty_ties_and_disjoint_union(self):
        self.assertEqual(reciprocal_rank_fusion([], []), ())
        self.assertEqual([c.key for c in reciprocal_rank_fusion(["z"], ["a"])], ["a", "z"])
        self.assertEqual(len(reciprocal_rank_fusion(list("abcde"), list("fghij"))), 10)

    def test_invalid_bounds_and_duplicate_lists_are_rejected(self):
        for value in (True, False, 0, 6, 1.0, "5", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): keyword_rank("x", [], top_k=value)
                with self.assertRaises(ValueError): reciprocal_rank_fusion([], [], top_k=value)
        for v, k in [(["a", "a"], []), ([], ["a", "a"]), ([""], []), ([1], []), (list("abcdef"), [])]:
            with self.assertRaises(ValueError): reciprocal_rank_fusion(v, k)
        with self.assertRaises(ValueError): keyword_rank("x", [("a", "x"), ("a", "x")])

    def test_results_are_immutable_and_guards_are_honored(self):
        result = keyword_rank("pasta", [("a", "pasta")])[0]
        with self.assertRaises(FrozenInstanceError): result.score = 0
        def stopped(): raise TimeoutError("stopped")
        with self.assertRaises(TimeoutError): keyword_rank("x", [("a", "x")], guard=stopped)
        with self.assertRaises(TimeoutError): reciprocal_rank_fusion(["a"], [], guard=stopped)
