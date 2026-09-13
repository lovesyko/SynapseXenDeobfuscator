from typing import List, Dict, Any, Optional

class RawInstruction:
    def __init__(self, op_code: int, op_tag: int, opA: int, opB: int, opC: int = 0, const_val: Any = None):
        self.op_code = op_code
        self.op_tag = op_tag
        self.opA = opA
        self.opB = opB
        self.opC = opC
        self.const_val = const_val

    def __repr__(self):
        return f"<RawInst op={self.op_code} tag={self.op_tag} A={self.opA} B={self.opB} C={self.opC} K={repr(self.const_val)}>"

class RawPrototype:
    def __init__(self, proto_id: int):
        self.proto_id = proto_id
        self.constants: List[Any] = []
        self.instructions: List[RawInstruction] = []
        self.child_prototypes: List['RawPrototype'] = []
        self.num_params: int = 0
        self.upvalues: int = 0

    def __repr__(self):
        return f"<RawPrototype ID={self.proto_id} Consts={len(self.constants)} Insts={len(self.instructions)} Children={len(self.child_prototypes)}>"

class BytecodeDecoder:
    def __init__(self, runtime_data: Dict[str, Any]):
        self.runtime_data = runtime_data or {}

    def decode(self) -> RawPrototype:
        return self._build_proto(self.runtime_data, proto_id=0)

    def _build_proto(self, data: Dict[str, Any], proto_id: int) -> RawPrototype:
        proto = RawPrototype(proto_id=proto_id)
        proto.constants = data.get("consts", [])
        proto.num_params = data.get("num_params", 0)
        proto.upvalues = data.get("upvalues", 0)

        raw_insts = data.get("insts", [])
        if raw_insts:
            key_stats = {}
            for inst in raw_insts:
                if isinstance(inst, dict):
                    for k, v in inst.items():
                        if isinstance(v, (int, float)):
                            if k not in key_stats: key_stats[k] = []
                            key_stats[k].append(int(v))

            op_code_key = None
            const_key = None
            op_tag_key = None
            opA_key = None
            opB_key = None
            opC_key = None

            for k, vals in key_stats.items():
                max_v = max(vals)
                min_v = min(vals)
                if max_v > 100000000:
                    op_code_key = k
                elif 10000 <= min_v and max_v <= 500000:
                    const_key = k
                elif max_v <= 64 and min_v >= 0 and op_tag_key is None:
                    op_tag_key = k

            remaining = [k for k in key_stats if k not in (op_code_key, const_key, op_tag_key)]
            remaining.sort(key=lambda k: max(key_stats[k]))

            if remaining: opA_key = remaining[0]
            if len(remaining) > 1: opB_key = remaining[1]
            if len(remaining) > 2: opC_key = remaining[2]

            for i_data in raw_insts:
                if isinstance(i_data, dict):
                    op_code = int(i_data.get(op_code_key, 0)) if op_code_key else 0
                    op_tag = int(i_data.get(op_tag_key, 0)) if op_tag_key else 0
                    opA = int(i_data.get(opA_key, 0)) if opA_key else 0
                    opB = int(i_data.get(opB_key, 0)) if opB_key else 0
                    opC = int(i_data.get(opC_key, 0)) if opC_key else 0

                    const_val = None
                    if const_key and const_key in i_data:
                        raw_c_val = int(i_data[const_key])
                        c_idx = raw_c_val // 16384
                        if 0 <= c_idx < len(proto.constants):
                            const_val = proto.constants[c_idx]

                    proto.instructions.append(RawInstruction(
                        op_code=op_code, op_tag=op_tag, opA=opA, opB=opB, opC=opC, const_val=const_val
                    ))

        children_data = data.get("children", [])
        for c_idx, c_data in enumerate(children_data):
            child_proto = self._build_proto(c_data, proto_id=c_idx + 1)
            proto.child_prototypes.append(child_proto)

        return proto
