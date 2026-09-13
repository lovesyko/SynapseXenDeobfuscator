from typing import List
from .decompiler import (
    StatementNode, ExpressionNode, CallStatement, AssignmentStatement,
    ReturnStatement, VariableExpr, ConstantExpr, IndexExpr, FunctionDecl, MethodCallExpr
)

class CodeGenerator:
    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size

    def generate(self, statements: List[StatementNode]) -> str:
        lines = []
        for stmt in statements:
            lines.extend(self._emit_stmt(stmt, indent_level=0))
        return "\n".join(lines)

    def _emit_stmt(self, stmt: StatementNode, indent_level: int) -> List[str]:
        indent = " " * (indent_level * self.indent_size)
        if isinstance(stmt, AssignmentStatement):
            val_code = self._emit_expr(stmt.value_expr)
            return [f"{indent}{stmt.var_name} = {val_code}"]

        elif isinstance(stmt, CallStatement):
            if isinstance(stmt.fn_expr, ConstantExpr):
                fn_code = f"v{stmt.fn_expr.value}" if isinstance(stmt.fn_expr.value, int) else "v0"
            else:
                fn_code = self._emit_expr(stmt.fn_expr)
            args_code = ", ".join(self._emit_expr(a) for a in stmt.args)
            if args_code:
                return [f"{indent}{fn_code}({args_code})"]
            return [f"{indent}{fn_code}()"]

        elif isinstance(stmt, ReturnStatement):
            if stmt.value_expr:
                return [f"{indent}return {self._emit_expr(stmt.value_expr)}"]
            return [f"{indent}return"]

        elif isinstance(stmt, FunctionDecl):
            params_str = ", ".join(stmt.params)
            lines = [f"{indent}function {stmt.name}({params_str})"]
            for s in stmt.body:
                lines.extend(self._emit_stmt(s, indent_level + 1))
            lines.append(f"{indent}end")
            return lines

        return []

    def _emit_expr(self, expr: ExpressionNode) -> str:
        if isinstance(expr, VariableExpr):
            return expr.name
        elif isinstance(expr, ConstantExpr):
            if expr.value is None:
                return "nil"
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            if isinstance(expr.value, str):
                return repr(expr.value)
            return str(expr.value)
        elif isinstance(expr, IndexExpr):
            obj_str = self._emit_expr(expr.obj)
            key_str = self._emit_expr(expr.key)
            if isinstance(expr.key, ConstantExpr) and isinstance(expr.key.value, str) and expr.key.value.isidentifier():
                return f"{obj_str}.{expr.key.value}"
            return f"{obj_str}[{key_str}]"
        elif isinstance(expr, MethodCallExpr):
            obj_str = self._emit_expr(expr.obj)
            args_str = ", ".join(self._emit_expr(a) for a in expr.args)
            sep = ":" if expr.method in ("GetService", "FindFirstChild", "WaitForChild", "FireServer", "InvokeServer", "Connect") else "."
            return f"{obj_str}{sep}{expr.method}({args_str})"
        return "nil"
