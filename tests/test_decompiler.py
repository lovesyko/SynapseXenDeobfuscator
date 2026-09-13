import unittest
from src.ir import IRModule, IRFunction, IRInstruction, IROpcode, Operand, OperandType
from src.decompiler import Decompiler, AssignmentStatement, ConstantExpr, ReturnStatement
from src.codegen import CodeGenerator

class TestDecompiler(unittest.TestCase):
    def test_decompilation(self):
        mod = IRModule()
        fn = IRFunction(func_id=0, name="main")
        fn.instructions = [
            IRInstruction(IROpcode.GETGLOBAL, dest=Operand(OperandType.REGISTER, 0), args=[Operand(OperandType.CONSTANT, "print")]),
            IRInstruction(IROpcode.LOADK, dest=Operand(OperandType.REGISTER, 1), args=[Operand(OperandType.CONSTANT, "Hello World")]),
            IRInstruction(IROpcode.CALL, dest=Operand(OperandType.REGISTER, 0), args=[Operand(OperandType.REGISTER, 1)])
        ]
        mod.main_function = fn

        decomp = Decompiler(mod)
        ast = decomp.decompile()
        cg = CodeGenerator()
        code = cg.generate(ast)
        self.assertIn("print('Hello World')", code)

    def test_boolean_codegen(self):
        code = CodeGenerator().generate([
            AssignmentStatement("enabled", ConstantExpr(True)),
            AssignmentStatement("disabled", ConstantExpr(False)),
            ReturnStatement(ConstantExpr(True))
        ])
        self.assertIn("enabled = true", code)
        self.assertIn("disabled = false", code)
        self.assertIn("return true", code)

if __name__ == "__main__":
    unittest.main()
