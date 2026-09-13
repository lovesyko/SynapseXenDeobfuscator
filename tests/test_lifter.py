import unittest
from src.decoder import RawPrototype, RawInstruction
from src.vm_lifter import VMLifter
from src.ir import IROpcode

class TestVMLifter(unittest.TestCase):
    def test_lifting(self):
        proto = RawPrototype(proto_id=0)
        proto.constants = ["print", "Hello World"]
        proto.instructions = [
            RawInstruction(op_code=1, op_tag=1, opA=0, opB=0),
            RawInstruction(op_code=2, op_tag=2, opA=1, opB=1),
            RawInstruction(op_code=4, op_tag=4, opA=0, opB=1)
        ]

        lifter = VMLifter(proto)
        module = lifter.lift()
        self.assertIsNotNone(module.main_function)
        self.assertEqual(len(module.main_function.instructions), 3)
        self.assertEqual(module.main_function.instructions[0].opcode, IROpcode.GETGLOBAL)
        self.assertEqual(module.main_function.instructions[1].opcode, IROpcode.LOADK)

if __name__ == "__main__":
    unittest.main()
