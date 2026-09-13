from typing import List, Any, Optional, Dict
from .ir import IRModule, IRFunction, IROpcode, Operand, OperandType

class ASTNode:
    pass

class StatementNode(ASTNode):
    pass

class ExpressionNode(ASTNode):
    pass

class CallStatement(StatementNode):
    def __init__(self, fn_expr: ExpressionNode, args: List[ExpressionNode]):
        self.fn_expr = fn_expr
        self.args = args

class MethodCallExpr(ExpressionNode):
    def __init__(self, obj: ExpressionNode, method: str, args: List[ExpressionNode]):
        self.obj = obj
        self.method = method
        self.args = args

class AssignmentStatement(StatementNode):
    def __init__(self, var_name: str, value_expr: ExpressionNode):
        self.var_name = var_name
        self.value_expr = value_expr

class ReturnStatement(StatementNode):
    def __init__(self, value_expr: Optional[ExpressionNode] = None):
        self.value_expr = value_expr

class VariableExpr(ExpressionNode):
    def __init__(self, name: str):
        self.name = name

class ConstantExpr(ExpressionNode):
    def __init__(self, value: Any):
        self.value = value

class IndexExpr(ExpressionNode):
    def __init__(self, obj: ExpressionNode, key: ExpressionNode):
        self.obj = obj
        self.key = key

class FunctionDecl(StatementNode):
    def __init__(self, name: str, params: List[str], body: List[StatementNode]):
        self.name = name
        self.params = params
        self.body = body

class Decompiler:
    def __init__(self, ir_module: IRModule):
        self.ir_module = ir_module

    def decompile(self) -> List[StatementNode]:
        if not self.ir_module.main_function:
            return []

        raw_stmts = self._decompile_function(self.ir_module.main_function)
        return self._optimize_dead_assignments(raw_stmts)

    def _optimize_dead_assignments(self, stmts: List[StatementNode]) -> List[StatementNode]:
        def get_read_vars(expr: ExpressionNode) -> set:
            vars_found = set()
            if isinstance(expr, VariableExpr):
                vars_found.add(expr.name)
            elif isinstance(expr, IndexExpr):
                vars_found.update(get_read_vars(expr.obj))
                vars_found.update(get_read_vars(expr.key))
            elif isinstance(expr, MethodCallExpr):
                vars_found.update(get_read_vars(expr.obj))
                for a in expr.args:
                    vars_found.update(get_read_vars(a))
            return vars_found

        live_vars = set()
        kept_stmts = []

        for stmt in reversed(stmts):
            if isinstance(stmt, AssignmentStatement):
                is_live = (stmt.var_name in live_vars) or isinstance(stmt.value_expr, MethodCallExpr)
                if is_live:
                    kept_stmts.append(stmt)
                    live_vars.discard(stmt.var_name)
                    live_vars.update(get_read_vars(stmt.value_expr))
            elif isinstance(stmt, CallStatement):
                kept_stmts.append(stmt)
                live_vars.update(get_read_vars(stmt.fn_expr))
                for a in stmt.args:
                    live_vars.update(get_read_vars(a))
            elif isinstance(stmt, ReturnStatement):
                kept_stmts.append(stmt)
                if stmt.value_expr:
                    live_vars.update(get_read_vars(stmt.value_expr))
            elif isinstance(stmt, FunctionDecl):
                clean_body = self._optimize_dead_assignments(stmt.body)
                kept_stmts.append(FunctionDecl(name=stmt.name, params=stmt.params, body=clean_body))
            else:
                kept_stmts.append(stmt)

        if not kept_stmts and stmts:
            kept_stmts.append(stmts[-1])

        return list(reversed(kept_stmts))

    def _decompile_function(self, ir_func: IRFunction) -> List[StatementNode]:
        statements: List[StatementNode] = []
        reg_names: Dict[str, str] = {}
        reg_exprs: Dict[str, ExpressionNode] = {}

        def get_reg_name(reg_str: str) -> str:
            if reg_str in reg_names:
                return reg_names[reg_str]
            if reg_str.startswith("R"):
                try:
                    num = int(reg_str[1:])
                    if num >= 0:
                        name = f"v{num}"
                    else:
                        name = f"v{abs(num) + 1000}"
                    reg_names[reg_str] = name
                    return name
                except ValueError:
                    pass
            return reg_str

        def get_expr(reg_str: str) -> ExpressionNode:
            if reg_str in reg_exprs:
                return reg_exprs[reg_str]
            return VariableExpr(get_reg_name(reg_str))

        for inst in ir_func.instructions:
            if inst.opcode == IROpcode.GETGLOBAL and inst.dest:
                g_name = str(inst.args[0].value) if inst.args else "global"
                dest_str = str(inst.dest)
                val_expr = VariableExpr(g_name)
                reg_exprs[dest_str] = val_expr
                statements.append(AssignmentStatement(var_name=get_reg_name(dest_str), value_expr=val_expr))

            elif inst.opcode == IROpcode.LOADK and inst.dest:
                dest_str = str(inst.dest)
                k_val = inst.args[0].value if inst.args else None
                val_expr = ConstantExpr(k_val)
                reg_exprs[dest_str] = val_expr
                statements.append(AssignmentStatement(var_name=get_reg_name(dest_str), value_expr=val_expr))

            elif inst.opcode == IROpcode.SETGLOBAL:
                g_name = str(inst.args[0].value) if inst.args else "global"
                val_expr = get_expr(str(inst.args[1])) if len(inst.args) > 1 else ConstantExpr(None)
                statements.append(AssignmentStatement(var_name=g_name, value_expr=val_expr))

            elif inst.opcode == IROpcode.GETTABLE and inst.dest:
                dest_str = str(inst.dest)
                obj_reg = str(inst.args[0]) if inst.args else "tbl"
                obj_expr = get_expr(obj_reg)
                key_expr = ConstantExpr(inst.args[1].value) if len(inst.args) > 1 and inst.args[1].op_type == OperandType.CONSTANT else get_expr(str(inst.args[1]))
                
                idx_expr = IndexExpr(obj_expr, key_expr)
                reg_exprs[dest_str] = idx_expr
                statements.append(AssignmentStatement(var_name=get_reg_name(dest_str), value_expr=idx_expr))

            elif inst.opcode == IROpcode.CALL:
                dest_str = str(inst.dest) if inst.dest else None
                fn_reg = str(inst.dest) if inst.dest else "func"
                fn_expr = get_expr(fn_reg)
                if isinstance(fn_expr, ConstantExpr):
                    fn_expr = VariableExpr(get_reg_name(fn_reg))

                call_args = [get_expr(str(a)) for a in inst.args]

                if isinstance(fn_expr, IndexExpr) and isinstance(fn_expr.key, ConstantExpr) and isinstance(fn_expr.key.value, str):
                    method_name = fn_expr.key.value
                    if method_name in ("GetService", "FindFirstChild", "WaitForChild", "FireServer", "InvokeServer", "Connect", "new", "HttpGet"):
                        m_expr = MethodCallExpr(fn_expr.obj, method_name, call_args)
                        if dest_str:
                            reg_exprs[dest_str] = m_expr
                            statements.append(AssignmentStatement(var_name=get_reg_name(dest_str), value_expr=m_expr))
                        else:
                            statements.append(CallStatement(fn_expr=m_expr, args=[]))
                    else:
                        c_stmt = CallStatement(fn_expr=fn_expr, args=call_args)
                        if dest_str:
                            reg_exprs[dest_str] = VariableExpr(get_reg_name(dest_str))
                        statements.append(c_stmt)
                else:
                    c_stmt = CallStatement(fn_expr=fn_expr, args=call_args)
                    if dest_str:
                        reg_exprs[dest_str] = VariableExpr(get_reg_name(dest_str))
                    statements.append(c_stmt)

            elif inst.opcode == IROpcode.RETURN:
                ret_val = get_expr(str(inst.args[0])) if inst.args else None
                statements.append(ReturnStatement(value_expr=ret_val))

        for child in ir_func.child_functions:
            child_body = self._decompile_function(child)
            statements.append(FunctionDecl(name=child.name, params=[f"v{i+1}" for i in range(child.num_params)], body=child_body))

        return statements
