from typing import Dict, List
from .ir import IRFunction, BasicBlock, IRInstruction, IROpcode

class CFGBuilder:
    def __init__(self, ir_func: IRFunction):
        self.ir_func = ir_func

    def build_cfg(self):
        if not self.ir_func.instructions:
            return

        bb0 = BasicBlock(block_id=0)
        self.ir_func.basic_blocks[0] = bb0

        current_bb = bb0
        for idx, inst in enumerate(self.ir_func.instructions):
            current_bb.instructions.append(inst)

            if inst.opcode in (IROpcode.RETURN, IROpcode.JUMP, IROpcode.JUMP_IF_FALSE, IROpcode.JUMP_IF_TRUE):
                if idx + 1 < len(self.ir_func.instructions):
                    next_bb_id = len(self.ir_func.basic_blocks)
                    next_bb = BasicBlock(block_id=next_bb_id)
                    self.ir_func.basic_blocks[next_bb_id] = next_bb
                    current_bb.successors.append(next_bb)
                    next_bb.predecessors.append(current_bb)
                    current_bb = next_bb

        for child in self.ir_func.child_functions:
            child_builder = CFGBuilder(child)
            child_builder.build_cfg()
