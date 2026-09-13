from typing import Dict, Any
from .ir import IRFunction, IROpcode, Operand, OperandType

class DataFlowAnalyzer:
    def __init__(self, ir_func: IRFunction):
        self.ir_func = ir_func
        self.constants_map: Dict[str, Any] = {}

    def analyze(self):
        cleaned_instructions = []
        for inst in self.ir_func.instructions:
            if inst.opcode == IROpcode.LOADK and inst.dest:
                if inst.args and inst.args[0].op_type == OperandType.CONSTANT:
                    self.constants_map[str(inst.dest)] = inst.args[0].value
            
            cleaned_instructions.append(inst)

        self.ir_func.instructions = cleaned_instructions

        for child in self.ir_func.child_functions:
            analyzer = DataFlowAnalyzer(child)
            analyzer.analyze()
