"""
方程组自动化简核心引擎
支持：方程组解析、变量识别、消元化简、中间变量屏蔽、目标结果指定、同类项合并

希腊字母变量：用户输入 /beta, /gamma 等，识别为希腊字母变量 β, γ
（直接输入 beta 则为 SymPy 的贝塔函数，不改变 SymPy 默认行为）
"""

import re
import keyword
from typing import List, Dict, Tuple, Optional
import sympy as sp
from sympy import symbols, Eq, solve, simplify, collect, latex, sympify, Symbol, fraction


# ---------------------------------------------------------------------------
# 1. 希腊字母映射
# ---------------------------------------------------------------------------

# 希腊字母名称 → LaTeX 命令
_GREEK_LETTERS = {
    'alpha': '\\alpha',
    'beta': '\\beta',
    'gamma': '\\gamma',
    'delta': '\\delta',
    'epsilon': '\\epsilon',
    'zeta': '\\zeta',
    'eta': '\\eta',
    'theta': '\\theta',
    'iota': '\\iota',
    'kappa': '\\kappa',
    'lambda': '\\lambda',
    'mu': '\\mu',
    'nu': '\\nu',
    'xi': '\\xi',
    'pi': '\\pi',
    'rho': '\\rho',
    'sigma': '\\sigma',
    'tau': '\\tau',
    'upsilon': '\\upsilon',
    'phi': '\\phi',
    'chi': '\\chi',
    'psi': '\\psi',
    'omega': '\\omega',
}

# 内部变量名前缀（用于区分希腊字母变量与 SymPy 函数）
_GREEK_PREFIX = 'grk_'

# 希腊字母正则：匹配 /alpha, /beta 等，后面不跟字母（避免 /betaa 误匹配）
_GREEK_PATTERN = re.compile(
    r'/(' + '|'.join(sorted(_GREEK_LETTERS.keys(), key=len, reverse=True)) + r')(?![a-zA-Z])'
)


def _replace_greek_input(text: str) -> str:
    """将用户输入中的 /beta, /gamma 替换为内部变量名 grk_beta, grk_gamma"""
    def replacer(m):
        return _GREEK_PREFIX + m.group(1)
    return _GREEK_PATTERN.sub(replacer, text)


def _to_display_name(name: str) -> str:
    """内部变量名 → 用户可见名称（grk_beta → beta）"""
    if name.startswith(_GREEK_PREFIX):
        return name[len(_GREEK_PREFIX):]
    return name


def _to_display_expr_str(s: str) -> str:
    """将表达式字符串中的内部变量名替换为显示名（grk_beta → beta）"""
    for greek_name in _GREEK_LETTERS:
        s = s.replace(_GREEK_PREFIX + greek_name, greek_name)
    return s


def _get_symbol_names() -> Dict[Symbol, str]:
    """生成希腊字母符号的 LaTeX 名称映射，用于 latex() 的 symbol_names 参数"""
    result = {}
    for greek_name, latex_cmd in _GREEK_LETTERS.items():
        internal_name = _GREEK_PREFIX + greek_name
        result[Symbol(internal_name)] = latex_cmd
    return result


# 预计算的 symbol_names 映射（全局复用，仅处理无下标的希腊字母）
_SYMBOL_NAMES = _get_symbol_names()


def _build_symbol_names(expr) -> Dict[Symbol, str]:
    """动态构建 symbol_names 映射，包含表达式中所有希腊字母符号（含带下标）。"""
    symbol_names = dict(_SYMBOL_NAMES)
    for sym in expr.free_symbols:
        name = str(sym)
        if name.startswith(_GREEK_PREFIX):
            rest = name[len(_GREEK_PREFIX):]  # e.g. beta_1
            match = re.match(r'([a-zA-Z]+)(?:_(\w+))?', rest)
            if match:
                greek_name = match.group(1)
                subscript = match.group(2)
                if greek_name in _GREEK_LETTERS:
                    latex_cmd = _GREEK_LETTERS[greek_name]
                    if subscript:
                        symbol_names[sym] = latex_cmd + '_{' + subscript + '}'
                    else:
                        symbol_names[sym] = latex_cmd
    return symbol_names


def _safe_latex(expr) -> str:
    """生成 LaTeX，自动应用希腊字母符号名称映射（含带下标处理）"""
    return latex(expr, symbol_names=_build_symbol_names(expr))


# ---------------------------------------------------------------------------
# 2. 变量名提取与安全解析
# ---------------------------------------------------------------------------

# 受保护的常见数学函数名（不加入 locals，保留为 SymPy 函数）
# 包括 beta, gamma 等——用户直接输入 beta 时使用 SymPy 函数
_PROTECTED_FUNCTIONS = {
    'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2',
    'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh',
    'exp', 'log', 'ln', 'sqrt', 'abs', 'sign',
    'floor', 'ceil', 'round', 'frac',
    'min', 'max', 'sum', 'prod',
    'gamma', 'beta', 'factorial', 'binomial',
    'pi', 'E', 'I', 'oo', 'zoo', 'nan',
    're', 'im', 'arg', 'conjugate',
    'root', 'cbrt',
    'zeta', 'digamma', 'trigamma',
}


def _extract_variable_names(text: str) -> List[str]:
    """
    从文本中提取所有可能的用户变量名。
    先将 /beta 等替换为内部变量名 grk_beta，再提取。
    只排除 Python 关键字、内置函数和受保护的数学函数。
    """
    # 先替换希腊字母输入
    text = _replace_greek_input(text)

    pattern = r'[a-zA-Z][a-zA-Z0-9_]*'
    raw_names = re.findall(pattern, text)

    builtin_names = set(dir(__builtins__)) if isinstance(__builtins__, dict) else set(dir(builtins))
    keyword_names = set(keyword.kwlist)

    result = []
    seen = set()
    for name in raw_names:
        if (name not in seen
                and name not in keyword_names
                and name not in builtin_names
                and name not in _PROTECTED_FUNCTIONS):
            seen.add(name)
            result.append(name)
    return result


def _build_locals(var_names: List[str]) -> Dict[str, Symbol]:
    """为变量名列表构建符号字典，用于 sympify 的 locals 参数。
    受保护的常见数学函数（sin, cos, beta 等）不加入，保留为 SymPy 函数。"""
    return {name: symbols(name) for name in var_names if name not in _PROTECTED_FUNCTIONS}


def _safe_sympify(expr_str: str, known_vars: List[str] = None) -> sp.Expr:
    """
    安全解析表达式。
    通过 locals 参数传入已知变量符号。
    常见数学函数（sin, cos, exp, sqrt, beta 等）保留为 SymPy 函数。
    希腊字母变量（grk_beta 等）通过 locals 识别为用户变量。
    """
    locals_dict = {}
    if known_vars:
        locals_dict = _build_locals(known_vars)
    return sympify(expr_str, locals=locals_dict)


# ---------------------------------------------------------------------------
# 3. 表达式规范化
# ---------------------------------------------------------------------------

def _normalize_expression(expr_str: str) -> str:
    """
    将用户输入的表达式规范化为 SymPy 可解析的格式。
    1. 将 /beta 等替换为内部变量名 grk_beta
    2. 将 ^ 替换为 **
    3. 隐式乘法（数字不属于变量名时才添加）
    """
    s = expr_str.strip()
    # 替换希腊字母输入
    s = _replace_greek_input(s)
    # 将 ^ 替换为 **
    s = s.replace('^', '**')
    # 隐式乘法：数字后面紧跟字母/下划线/左括号，
    # 但要求数字前面不是字母/下划线/数字（即数字不是变量名的一部分）
    s = re.sub(r'(?<![a-zA-Z_0-9])(\d+)([a-zA-Z_\(])', r'\1*\2', s)
    # 右括号后紧跟字母/数字/左括号
    s = re.sub(r'\)([a-zA-Z_\d\(])', r')*\1', s)
    return s


# ---------------------------------------------------------------------------
# 4. 方程组解析器
# ---------------------------------------------------------------------------

def parse_equations(text: str) -> List[Eq]:
    """
    解析多行方程组文本。
    每行格式：左表达式 = 右表达式
    支持下划线自定义下标（如 v_1, R_12, a_xy）
    支持希腊字母变量（如 /beta, /gamma）
    """
    all_var_names = _extract_variable_names(text)

    equations = []
    lines = text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError(f"方程缺少等号: {line}")
        left_str, right_str = line.split('=', 1)
        left = _safe_sympify(_normalize_expression(left_str), all_var_names)
        right = _safe_sympify(_normalize_expression(right_str), all_var_names)
        equations.append(Eq(left, right))
    return equations


# ---------------------------------------------------------------------------
# 5. 变量识别
# ---------------------------------------------------------------------------

def identify_variables(equations: List[Eq]) -> List[str]:
    """
    扫描所有方程，识别全部独立变量（符号），无遗漏、无重复。
    返回按名称排序的变量显示名列表（grk_beta → beta）。
    """
    var_set = set()
    for eq in equations:
        var_set.update(eq.free_symbols)
    return sorted([_to_display_name(str(v)) for v in var_set])


def identify_variables_from_text(text: str) -> List[str]:
    """从文本直接识别变量（便捷接口）。"""
    eqs = parse_equations(text)
    return identify_variables(eqs)


# ---------------------------------------------------------------------------
# 6. 中间变量屏蔽 + 消元求解
# ---------------------------------------------------------------------------

def solve_with_intermediate(
    equations: List[Eq],
    intermediate_vars: List[str],
    target_vars: List[str]
) -> Dict[str, sp.Expr]:
    """
    求解方程组，同时屏蔽中间变量。
    中间变量和目标变量一起作为求解变量，SymPy solve 自动消去。
    超定处理：方程数多于待求解变量数时，自动补充其他变量。
    """
    # 用户输入的中间变量可能是显示名（如 beta），需要转换为内部名
    intermediate_vars = [_display_to_internal(v) for v in intermediate_vars]
    target_vars = [_display_to_internal(v) for v in target_vars]

    solve_vars = list(dict.fromkeys(intermediate_vars + target_vars))

    if not solve_vars:
        return {}

    # 收集方程中所有变量
    all_eq_vars = set()
    for eq in equations:
        all_eq_vars.update(eq.free_symbols)
    all_eq_var_names = sorted([str(v) for v in all_eq_vars])

    # 超定处理
    if len(equations) > len(solve_vars):
        for v in all_eq_var_names:
            if v not in solve_vars and len(solve_vars) < len(equations):
                solve_vars.append(v)

    # 检查方程数
    core_count = len(set(intermediate_vars + target_vars))
    if len(equations) < core_count:
        raise ValueError(
            f"方程数量不足：有 {core_count} 个待求解变量"
            f"（中间变量 {len(intermediate_vars)} 个 + 目标变量 {len(target_vars)} 个），"
            f"但只有 {len(equations)} 个方程。"
        )

    symbols_map = {name: symbols(name) for name in solve_vars}
    solve_symbols = [symbols_map[name] for name in solve_vars]
    result = solve(equations, solve_symbols, dict=True)

    if not result:
        raise ValueError("方程组无解，请检查输入是否正确。")

    sol = result[0]
    output = {}
    for name in target_vars:
        sym = symbols_map[name]
        if sym in sol:
            output[name] = simplify(sol[sym])
        else:
            output[name] = sym
    return output


def _display_to_internal(name: str) -> str:
    """显示名 → 内部名（beta → grk_beta，如果是希腊字母的话）"""
    if name in _GREEK_LETTERS:
        return _GREEK_PREFIX + name
    return name


# ---------------------------------------------------------------------------
# 7. 目标结果计算
# ---------------------------------------------------------------------------

def compute_target_expression(
    expr_str: str,
    solutions: Dict[str, sp.Expr],
    known_vars: List[str] = None
) -> sp.Expr:
    """
    根据已求得的变量解，计算用户指定的目标结果表达式。
    支持单一变量、变量分式、多变量组合。
    """
    expr = _safe_sympify(_normalize_expression(expr_str), known_vars)
    subs_dict = {symbols(name): val for name, val in solutions.items()}
    result = expr.subs(subs_dict)
    return simplify(result)


# ---------------------------------------------------------------------------
# 8. 同类项合并
# ---------------------------------------------------------------------------

def merge_like_terms(
    expr: sp.Expr,
    merge_vars: List[str]
) -> sp.Expr:
    """按用户指定的特征变量合并同类项，支持多组批量合并。"""
    if not merge_vars:
        return expr
    internal_names = [_display_to_internal(v) for v in merge_vars]
    syms = [symbols(v) for v in internal_names]
    return collect(expr, syms, evaluate=True)


# ---------------------------------------------------------------------------
# 9. 主入口：完整化简流程
# ---------------------------------------------------------------------------

def simplify_system(
    equations_text: str,
    intermediate_vars: Optional[List[str]] = None,
    target_expressions: Optional[List[str]] = None,
    merge_vars: Optional[List[str]] = None
) -> Dict:
    """完整化简流程。"""
    intermediate_vars = intermediate_vars or []
    target_expressions = target_expressions or []
    merge_vars = merge_vars or []

    all_var_names = _extract_variable_names(equations_text)

    # 步骤1：解析方程组
    equations = parse_equations(equations_text)
    all_vars = identify_variables(equations)

    # 收集方程左边变量（用于分式目标智能判断）
    left_var_names = set()
    for eq in equations:
        for s in eq.lhs.free_symbols:
            left_var_names.add(str(s))

    # 步骤2：确定目标变量
    target_vars = []
    if target_expressions:
        for texpr in target_expressions:
            expr = _safe_sympify(_normalize_expression(texpr), all_var_names)
            numerator, denominator = sp.fraction(expr)
            if denominator != 1:
                # 分式目标：分子变量一定求解；分母变量出现在方程左边才求解
                for s in numerator.free_symbols:
                    name = str(s)
                    if name not in target_vars:
                        target_vars.append(name)
                for s in denominator.free_symbols:
                    name = str(s)
                    if name in left_var_names and name not in target_vars:
                        target_vars.append(name)
            else:
                for s in expr.free_symbols:
                    name = str(s)
                    if name not in target_vars:
                        target_vars.append(name)

    # 默认目标变量
    if not target_expressions:
        target_vars_internal = _select_default_targets(
            equations, [_display_to_internal(v) for v in all_vars],
            [_display_to_internal(v) for v in intermediate_vars]
        )
        target_vars = target_vars_internal
        target_expressions = [_to_display_name(v) for v in target_vars]

    # 步骤3：求解
    solutions = solve_with_intermediate(equations, intermediate_vars, target_vars)

    # 步骤4：计算每个目标表达式
    results = []
    for texpr in target_expressions:
        value = compute_target_expression(texpr, solutions, all_var_names)
        if merge_vars:
            value = merge_like_terms(value, merge_vars)
        results.append({
            'target': texpr,
            'latex': fix_latex_subscripts(_safe_latex(value)),
            'python': _to_display_expr_str(str(value))
        })

    # 步骤5：生成化简步骤
    steps = _generate_steps(
        equations, all_vars, intermediate_vars,
        [_to_display_name(v) for v in target_vars],
        target_expressions, merge_vars, solutions
    )

    return {
        'equations_latex': [fix_latex_subscripts(_safe_latex(eq)) for eq in equations],
        'all_variables': all_vars,
        'intermediate_vars': intermediate_vars,
        'target_expressions': target_expressions,
        'merge_vars': merge_vars,
        'results': results,
        'steps': steps
    }


def _select_default_targets(
    equations: List[Eq],
    all_vars: List[str],
    intermediate_vars: List[str]
) -> List[str]:
    """智能选择默认目标变量（内部名）。"""
    max_targets = len(equations) - len(intermediate_vars)
    if max_targets <= 0:
        raise ValueError("方程数量不足，无法求解任何目标变量。")

    left_vars = []
    for eq in equations:
        for s in eq.lhs.free_symbols:
            name = str(s)
            if name not in intermediate_vars and name not in left_vars:
                left_vars.append(name)

    all_non_intermediate = [v for v in all_vars if v not in intermediate_vars]

    target_vars = []
    for v in left_vars:
        if v in all_non_intermediate and len(target_vars) < max_targets:
            target_vars.append(v)
    for v in all_non_intermediate:
        if v not in target_vars and len(target_vars) < max_targets:
            target_vars.append(v)

    return target_vars


def _generate_steps(
    equations, all_vars, intermediate_vars,
    target_vars, target_expressions, merge_vars, solutions
) -> List[str]:
    """生成化简步骤的文字说明。"""
    steps = []
    steps.append(f"识别到 {len(equations)} 个方程，共 {len(all_vars)} 个独立变量：{', '.join(all_vars)}")
    if intermediate_vars:
        steps.append(f"标记中间变量（最终输出屏蔽）：{', '.join(intermediate_vars)}")
    steps.append(f"待求解变量（中间变量 + 目标变量）：{', '.join(intermediate_vars + target_vars)}")
    steps.append("执行符号消元求解，自动消去所有待求解变量...")
    if solutions:
        steps.append("求解完成，中间变量已从目标结果中彻底剔除。")
    if merge_vars:
        steps.append(f"按特征变量合并同类项：{', '.join(merge_vars)}")
    steps.append(f"输出 {len(target_expressions)} 个目标结果。")
    return steps


# ---------------------------------------------------------------------------
# 10. LaTeX 渲染辅助
# ---------------------------------------------------------------------------

def fix_latex_subscripts(latex_str: str) -> str:
    """确保 LaTeX 中下标格式正确（兜底函数）。"""
    result = []
    i = 0
    while i < len(latex_str):
        if latex_str[i] == '_' and i + 1 < len(latex_str) and latex_str[i + 1] != '{':
            j = i + 1
            while j < len(latex_str) and latex_str[j].isalnum():
                j += 1
            sub = latex_str[i + 1:j]
            if sub:
                result.append('_{' + sub + '}')
            else:
                result.append('_')
            i = j
        else:
            result.append(latex_str[i])
            i += 1
    return ''.join(result)


def render_equation_latex(equation_text: str) -> str:
    """将单个方程文本渲染为 LaTeX（用于实时预览）。"""
    all_var_names = _extract_variable_names(equation_text)
    if '=' in equation_text:
        left_str, right_str = equation_text.split('=', 1)
        left = _safe_sympify(_normalize_expression(left_str), all_var_names)
        right = _safe_sympify(_normalize_expression(right_str), all_var_names)
        return fix_latex_subscripts(_safe_latex(Eq(left, right)))
    else:
        expr = _safe_sympify(_normalize_expression(equation_text), all_var_names)
        return fix_latex_subscripts(_safe_latex(expr))
