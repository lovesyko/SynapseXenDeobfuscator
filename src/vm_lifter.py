from typing import List, Dict, Any, Optional
from .decoder import RawPrototype, RawInstruction
from .ir import IRModule, IRFunction, IRInstruction, IROpcode, Operand, OperandType

class VMLifter:
    def __init__(self, root_proto: RawPrototype):
        self.root_proto = root_proto

    def lift(self) -> IRModule:
        module = IRModule()
        module.main_function = self._lift_proto(self.root_proto, func_id=0, name="main")
        return module

    def _lift_proto(self, proto: RawPrototype, func_id: int, name: str) -> IRFunction:
        ir_func = IRFunction(func_id=func_id, name=name)
        ir_func.num_params = proto.num_params

        constants = proto.constants

        for idx, inst in enumerate(proto.instructions):
            ir_inst = self._lift_instruction(inst, constants, proto.child_prototypes)
            ir_func.instructions.append(ir_inst)

        for c_idx, child in enumerate(proto.child_prototypes):
            child_ir = self._lift_proto(child, func_id=c_idx + 1, name=f"closure_{func_id}_{c_idx}")
            ir_func.child_functions.append(child_ir)

        return ir_func

    def _lift_instruction(self, inst: RawInstruction, constants: List[Any], child_protos: List[RawPrototype]) -> IRInstruction:
        tag = inst.op_tag
        A = inst.opA
        B = inst.opB
        C = inst.opC
        const_val = inst.const_val

        regA = Operand(OperandType.REGISTER, A)
        regB = Operand(OperandType.REGISTER, B)
        regC = Operand(OperandType.REGISTER, C)

        KNOWN_GLOBALS = {
            "game", "workspace", "script", "Instance", "getrenv", "getgenv",
            "Vector3", "CFrame", "Color3", "UDim2", "math", "table", "string",
            "task", "pairs", "ipairs", "pcall", "require", "print", "warn",
            "error", "loadstring", "HttpGet", "_G", "shared"
        }

        def get_op(val: int) -> Operand:
            if 0 <= val < len(constants):
                return Operand(OperandType.CONSTANT, constants[val])
            return Operand(OperandType.REGISTER, val)

        opB = get_op(B)
        opC = get_op(C)

        if opB.op_type == OperandType.CONSTANT:
            c_val = opB.value
            if isinstance(c_val, str) and c_val in KNOWN_GLOBALS:
                return IRInstruction(IROpcode.GETGLOBAL, dest=regA, args=[opB])
            return IRInstruction(IROpcode.LOADK, dest=regA, args=[opB])

        if isinstance(const_val, str) and const_val in KNOWN_GLOBALS:
            return IRInstruction(IROpcode.GETGLOBAL, dest=regA, args=[Operand(OperandType.CONSTANT, const_val)])

        if B != 0 and isinstance(const_val, str) and const_val.isidentifier():
            return IRInstruction(IROpcode.GETTABLE, dest=regA, args=[regB, Operand(OperandType.CONSTANT, const_val)])

        if B != 0 and C != 0:
            return IRInstruction(IROpcode.CALL, dest=regA, args=[regB, regC])

        if B != 0 and C == 0:
            return IRInstruction(IROpcode.MOVE, dest=regA, args=[regB])

        if const_val is not None:
            return IRInstruction(IROpcode.LOADK, dest=regA, args=[Operand(OperandType.CONSTANT, const_val)])

        return IRInstruction(IROpcode.NOP)
