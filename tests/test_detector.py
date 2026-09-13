import unittest
from src.detector import detect_synapse_xen

class TestDetector(unittest.TestCase):
    def test_detection_positive(self):
        sample = """
        --[[
            Synapse Xen v1.1.2 by Synapse GP
            VM Hash: e2603e44edf60ea98289a5483eaf9176c940b5f0239a03232623795bab4431cc
        ]]
        local SynapseXen_test = 1
        """
        det = detect_synapse_xen(sample)
        self.assertTrue(det.is_synapse_xen)
        self.assertEqual(det.version, "v1.1.2")
        self.assertGreaterEqual(det.confidence, 0.5)

    def test_detection_negative(self):
        sample = "print('Hello World')"
        det = detect_synapse_xen(sample)
        self.assertFalse(det.is_synapse_xen)

if __name__ == "__main__":
    unittest.main()
