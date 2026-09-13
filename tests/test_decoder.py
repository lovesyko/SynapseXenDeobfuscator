import unittest
from src.decoder import BytecodeDecoder

class TestDecoder(unittest.TestCase):
    def test_bytecode_decode(self):
        mock_runtime = {
            "consts": ["game", "Workspace", "Part"],
            "num_params": 1,
            "upvalues": 0,
            "insts": [
                {"1717075632": 1, "1531021873": 1, "463306503": 0, "1869495129": 0},
                {"1717075632": 2, "1531021873": 5, "463306503": 1, "1869495129": 0, "2139216807": 1}
            ],
            "children": []
        }

        decoder = BytecodeDecoder(runtime_data=mock_runtime)
        proto = decoder.decode()
        self.assertEqual(len(proto.constants), 3)
        self.assertEqual(len(proto.instructions), 2)
        self.assertEqual(proto.num_params, 1)

if __name__ == "__main__":
    unittest.main()
