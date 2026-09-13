import unittest
import os
import argparse
from cli import deobfuscate_file

class TestCorpusBatch(unittest.TestCase):
    def test_all_synapse_xen_samples(self):
        sample_dir = r'C:\Users\raff\.gemini\antigravity\brain\88f5cbb5-b081-444e-8083-bf854935d315\scratch\obfuscator-samples\SynapseXen\v1.1.2'
        self.assertTrue(os.path.exists(sample_dir), "Sample directory must exist")

        files = [f for f in os.listdir(sample_dir) if f.endswith('.lua')]
        self.assertGreater(len(files), 0, "Must find sample files")

        dummy_opts = argparse.Namespace(
            inspect=False, decode=False, dump_ir=False, dump_cfg=False, batch=True, force=False
        )

        passed = 0
        failed = 0
        for f in files:
            full_path = os.path.join(sample_dir, f)
            try:
                out = deobfuscate_file(full_path, dummy_opts)
                self.assertTrue(isinstance(out, str) and len(out) > 0)
                passed += 1
            except Exception as e:
                failed += 1

        print(f"\nCorpus Batch Results: {passed} / {len(files)} passed ({failed} failed)")
        self.assertEqual(failed, 0, f"Expected 0 failures across corpus, got {failed}")

if __name__ == "__main__":
    unittest.main()
