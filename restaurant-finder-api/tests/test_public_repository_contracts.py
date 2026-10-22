"""Offline contracts for public setup safety; never build or invoke AWS."""
from pathlib import Path
import fnmatch
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PublicRepositoryContracts(unittest.TestCase):
    def test_generated_docker_allowlist(self):
        rules = [line.strip() for line in (ROOT / "restaurant-finder-api/.dockerignore").read_text().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        self.assertIn(".generated/**", rules)
        self.assertIn("!.generated/prompt-manifest.json", rules)
        self.assertNotIn(".generated", rules)
        self.assertNotIn(".generated/", rules)
        self.assertLess(rules.index(".generated/**"), rules.index("!.generated/prompt-manifest.json"))
        self.assertEqual([r for r in rules if r.startswith("!.generated")], ["!.generated/prompt-manifest.json"])

        # Exercise the simple generated-path allowlist, not a complete Docker
        # pattern matcher. No Docker engine or private filesystem is consulted.
        def included(path):
            result = True
            for rule in rules:
                negated = rule.startswith("!")
                pattern = rule[1:] if negated else rule
                if fnmatch.fnmatchcase(path, pattern) or path.startswith(pattern.rstrip("/") + "/"):
                    result = negated
            return result

        self.assertTrue(included(".generated/prompt-manifest.json"))
        for path in [".generated/private.txt", ".generated/discovered-coverage-r29/receipt.json",
                     ".generated/policy-pdf-demo-r18/policy.pdf", ".generated/nested/prompt-manifest.json",
                     ".generated/real-restaurants-demo/source.pdf", ".generated/prompt-manifest.json.old"]:
            with self.subTest(path=path):
                self.assertFalse(included(path))

    def test_deployment_is_manual_and_ci_remains_automatic(self):
        for filename in ("deploy-image.yml", "deploy-infra.yml"):
            text = (ROOT / ".github/workflows" / filename).read_text()
            trigger = text.split("\non:\n", 1)[1].split("\nenv:\n", 1)[0]
            self.assertIn("  workflow_dispatch:", trigger)
            self.assertNotIn("  push:", trigger)
            self.assertNotIn("  pull_request:", trigger)
        ci = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertIn("  push:", ci)
        self.assertIn("  pull_request:", ci)

    @unittest.skipUnless(shutil.which("git"), "Git required to verify ignore semantics")
    def test_environment_variants_ignored_but_examples_available(self):
        with tempfile.TemporaryDirectory(prefix="public-repository-ignore-") as temporary:
            folder = Path(temporary)
            subprocess.run(["git", "-c", "init.templateDir=", "init", "--quiet", str(folder)], check=True,
                           capture_output=True)
            for name in (".gitignore", "restaurant-finder-api/.gitignore"):
                target = folder / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text((ROOT / name).read_text())
            for prefix in ("", "restaurant-finder-api/", "restaurant-finder-ui/"):
                for suffix in (".env", ".env.production", ".env.staging", ".env.local"):
                    result = subprocess.run(["git", "-C", str(folder), "check-ignore", "--no-index", "-q", prefix + suffix])
                    self.assertEqual(result.returncode, 0, prefix + suffix)
                result = subprocess.run(["git", "-C", str(folder), "check-ignore", "--no-index", "-q", prefix + ".env.example"])
                self.assertEqual(result.returncode, 1, prefix + ".env.example")

    def test_documented_entry_points_and_readmes_exist(self):
        for name in ("README.md", "docs/SETUP.md", "restaurant-finder-ui/README.md",
                     "restaurant-finder-api/src/main.py", "restaurant-finder-api/src/deployment/ingest_documents.py"):
            self.assertTrue((ROOT / name).is_file(), name)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("git clone https://github.com/yukangzhen/restaurant-finder.git", readme)
        self.assertNotIn("git clone <repository-url>", readme)


if __name__ == "__main__":
    unittest.main()
