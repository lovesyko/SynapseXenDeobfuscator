from enum import Enum, auto
from typing import List, Dict, Any, Optional

class IROpcode(Enum):
    NOP = auto()
    LOADK = auto()
    LOADNIL = auto()
    LOADBOOL = auto()
    MOVE = auto()
    GETGLOBAL = auto()
    SETGLOBAL = auto()
    GETTABLE = auto()
    SETTABLE = auto()
    CALL = auto()
    RETURN = auto()
    CLOSURE = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    POW = auto()
    CONCAT = auto()
    EQ = auto()
    LT = auto()
    LE = auto()
    NOT = auto()
    VARARG = auto()

class OperandType(Enum):
    REGISTER = auto()
    CONSTANT = auto()
    UPVALUE = auto()
    LABEL = auto()
    GLOBAL = auto()

class Operand:
    def __init__(self, op_type: OperandType, value: Any):
        self.op_type = op_type
        self.value = value

    def __repr__(self):
        if self.op_type == OperandType.REGISTER:
            return f"R{self.value}"
        elif self.op_type == OperandType.CONSTANT:
            return f"K({repr(self.value)})"
        elif self.op_type == OperandType.GLOBAL:
            return f"G({self.value})"
        elif self.op_type == OperandType.LABEL:
            return f"L{self.value}"
        return str(self.value)

class IRInstruction:
    def __init__(self, opcode: IROpcode, dest: Optional[Operand] = None, args: List[Operand] = None, line_info: int = 0):
        self.opcode = opcode
        self.dest = dest
        self.args = args or []
        self.line_info = line_info

    def __repr__(self):
        args_str = ", ".join(str(a) for a in self.args)
        if self.dest:
            return f"{self.dest} = {self.opcode.name} {args_str}".strip()
        return f"{self.opcode.name} {args_str}".strip()

class BasicBlock:
    def __init__(self, block_id: int):
        self.block_id = block_id
        self.instructions: List[IRInstruction] = []
        self.predecessors: List['BasicBlock'] = []
        self.successors: List['BasicBlock'] = []

    def __repr__(self):
        return f"<BB{self.block_id} Insts={len(self.instructions)} Preds={len(self.predecessors)} Succs={len(self.successors)}>"

class IRFunction:
    def __init__(self, func_id: int, name: str = "main"):
        self.func_id = func_id
        self.name = name
        self.num_params: int = 0
        self.instructions: List[IRInstruction] = []
        self.basic_blocks: Dict[int, BasicBlock] = {}
        self.child_functions: List['IRFunction'] = []

    def __repr__(self):
        return f"<IRFunction {self.name} (ID={self.func_id}) Insts={len(self.instructions)} Blocks={len(self.basic_blocks)} Children={len(self.child_functions)}>"

class IRModule:
    def __init__(self):
        self.main_function: Optional[IRFunction] = None

    def __repr__(self):
        return f"<IRModule Main={self.main_function}>"
