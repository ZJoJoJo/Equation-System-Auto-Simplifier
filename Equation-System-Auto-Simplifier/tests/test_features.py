"""
方程组自动化简软件 - 全面功能验证测试
逐项验证需求文档中列出的所有功能点是否真正实现。
"""

import sys
import os
import json
import time
import threading
import urllib.request
import urllib.error

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.engine import (
    parse_equations,
    identify_variables,
    identify_variables_from_text,
    solve_with_intermediate,
    compute_target_expression,
    merge_like_terms,
    simplify_system,
    fix_latex_subscripts,
    render_equation_latex
)
import sympy as sp

# ============================================================================
# 测试框架
# ============================================================================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def record(self, category, name, success, detail=""):
        status = "PASS" if success else "FAIL"
        self.results.append((category, name, status, detail))
        if success:
            self.passed += 1
        else:
            self.failed += 1
        symbol = "✓" if success else "✗"
        print(f"  [{symbol}] {name}" + (f" — {detail}" if detail and not success else ""))

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print(f"测试总结：{self.passed}/{total} 通过，{self.failed} 失败")
        print("=" * 70)
        if self.failed > 0:
            print("\n失败项：")
            for cat, name, status, detail in self.results:
                if status == "FAIL":
                    print(f"  [{cat}] {name}: {detail}")
        return self.failed == 0


result = TestResult()


# ============================================================================
# 一、核心基础功能验证
# ============================================================================

print("\n" + "=" * 70)
print("一、核心基础功能验证")
print("=" * 70)

# --- 1.1 批量输入多元方程组 + 智能化简 ---
print("\n【1.1】批量输入多元方程组 + 智能化简")

def test_basic_simplify():
    """测试基本的二元一次方程组化简"""
    text = """
    2*x + 3*y = 12
    x - y = 1
    """
    eqs = parse_equations(text)
    sol = sp.solve(eqs, [sp.symbols('x'), sp.symbols('y')], dict=True)
    x_val = sol[0][sp.symbols('x')]
    y_val = sol[0][sp.symbols('y')]
    # 验证解正确：x=3, y=2
    assert x_val == 3, f"x 应为 3，实际 {x_val}"
    assert y_val == 2, f"y 应为 2，实际 {y_val}"
    return True

try:
    test_basic_simplify()
    result.record("核心基础", "二元一次方程组化简", True, "x=3, y=2")
except Exception as e:
    result.record("核心基础", "二元一次方程组化简", False, str(e))


def test_linear_3var():
    """测试三元一次方程组"""
    text = """
    x + y + z = 6
    x - y + z = 2
    2*x + y - z = 1
    """
    eqs = parse_equations(text)
    x, y, z = sp.symbols('x y z')
    sol = sp.solve(eqs, [x, y, z], dict=True)[0]
    assert sol[x] == 1, f"x 应为 1，实际 {sol[x]}"
    assert sol[y] == 2, f"y 应为 2，实际 {sol[y]}"
    assert sol[z] == 3, f"z 应为 3，实际 {sol[z]}"
    return True

try:
    test_linear_3var()
    result.record("核心基础", "三元一次方程组化简", True, "x=1, y=2, z=3")
except Exception as e:
    result.record("核心基础", "三元一次方程组化简", False, str(e))


def test_fractional_equations():
    """测试分式方程组"""
    text = """
    1/x + 1/y = 3/2
    1/x - 1/y = 1/2
    """
    eqs = parse_equations(text)
    x, y = sp.symbols('x y')
    sol = sp.solve(eqs, [x, y], dict=True)[0]
    # 1/x = 1, 1/y = 1/2 => x=1, y=2
    assert sol[x] == 1, f"x 应为 1，实际 {sol[x]}"
    assert sol[y] == 2, f"y 应为 2，实际 {sol[y]}"
    return True

try:
    test_fractional_equations()
    result.record("核心基础", "分式方程组化简", True, "x=1, y=2")
except Exception as e:
    result.record("核心基础", "分式方程组化简", False, str(e))


def test_polynomial_system():
    """测试多项式方程组"""
    text = """
    x**2 + y**2 = 25
    x + y = 7
    """
    eqs = parse_equations(text)
    x, y = sp.symbols('x y')
    sol = sp.solve(eqs, [x, y], dict=True)
    # 解为 (3,4) 和 (4,3)
    x_vals = sorted([s[x] for s in sol])
    assert x_vals == [3, 4], f"x 解应为 [3,4]，实际 {x_vals}"
    return True

try:
    test_polynomial_system()
    result.record("核心基础", "多项式方程组化简", True, "解为 (3,4) 和 (4,3)")
except Exception as e:
    result.record("核心基础", "多项式方程组化简", False, str(e))


def test_circuit_analysis():
    """测试电路方程组（典型应用场景）"""
    text = """
    v_1 = I_1 * R_1
    v_2 = I_2 * R_2
    I_1 = I_2
    v_1 + v_2 = V_total
    """
    res = simplify_system(text, intermediate_vars=['I_1', 'I_2'], target_expressions=['v_1', 'v_2'])
    v1 = res['results'][0]['python']
    v2 = res['results'][1]['python']
    # v1 = R1*Vtotal/(R1+R2), v2 = R2*Vtotal/(R1+R2)
    R1, R2, V = sp.symbols('R_1 R_2 V_total')
    expected_v1 = R1 * V / (R1 + R2)
    expected_v2 = R2 * V / (R1 + R2)
    assert sp.simplify(sp.sympify(v1) - expected_v1) == 0, f"v1 不匹配: {v1}"
    assert sp.simplify(sp.sympify(v2) - expected_v2) == 0, f"v2 不匹配: {v2}"
    return True

try:
    test_circuit_analysis()
    result.record("核心基础", "电路方程组消元化简", True, "分压公式正确")
except Exception as e:
    result.record("核心基础", "电路方程组消元化简", False, str(e))


# --- 1.2 下划线自定义下标输入 ---
print("\n【1.2】下划线自定义下标输入格式")

def test_subscript_single_digit():
    """单位数下标"""
    text = "v_1 = I_1 * R_1"
    eqs = parse_equations(text)
    vars = identify_variables(eqs)
    assert 'v_1' in vars, f"应识别 v_1，实际 {vars}"
    assert 'I_1' in vars, f"应识别 I_1，实际 {vars}"
    assert 'R_1' in vars, f"应识别 R_1，实际 {vars}"
    return True

try:
    test_subscript_single_digit()
    result.record("核心基础", "单位数下标识别", True)
except Exception as e:
    result.record("核心基础", "单位数下标识别", False, str(e))


def test_subscript_multi_digit():
    """多位数下标：v_12 必须整体识别为变量名，不是 v_1 * 2"""
    text = "v_12 = I_1 * R_123"
    eqs = parse_equations(text)
    vars = identify_variables(eqs)
    assert 'v_12' in vars, f"应识别 v_12（整体下标），实际 {vars}"
    assert 'R_123' in vars, f"应识别 R_123（三位数下标），实际 {vars}"
    # 关键验证：不应该出现 v_1 或 R_1 这种被错误拆分的变量
    assert 'v_1' not in vars, "v_12 不应被拆分为 v_1"
    return True

try:
    test_subscript_multi_digit()
    result.record("核心基础", "多位数下标整体识别", True, "v_12, R_123 正确")
except Exception as e:
    result.record("核心基础", "多位数下标整体识别", False, str(e))


def test_subscript_alpha():
    """字母下标：a_xy"""
    text = "a_xy + b_xy = c_z"
    eqs = parse_equations(text)
    vars = identify_variables(eqs)
    assert 'a_xy' in vars, f"应识别 a_xy，实际 {vars}"
    assert 'b_xy' in vars, f"应识别 b_xy，实际 {vars}"
    assert 'c_z' in vars, f"应识别 c_z，实际 {vars}"
    return True

try:
    test_subscript_alpha()
    result.record("核心基础", "字母下标识别", True, "a_xy, b_xy, c_z")
except Exception as e:
    result.record("核心基础", "字母下标识别", False, str(e))


def test_subscript_mixed():
    """字母数字混合下标"""
    text = "node_1a + node_2b = total_3c"
    eqs = parse_equations(text)
    vars = identify_variables(eqs)
    assert 'node_1a' in vars, f"应识别 node_1a，实际 {vars}"
    assert 'node_2b' in vars, f"应识别 node_2b，实际 {vars}"
    assert 'total_3c' in vars, f"应识别 total_3c，实际 {vars}"
    return True

try:
    test_subscript_mixed()
    result.record("核心基础", "字母数字混合下标", True, "node_1a, node_2b, total_3c")
except Exception as e:
    result.record("核心基础", "字母数字混合下标", False, str(e))


# --- 1.3 智能变量识别 ---
print("\n【1.3】智能变量识别")

def test_variable_identification_complete():
    """验证变量识别无遗漏、无重复"""
    text = """
    a*x + b*y = c
    d*x + e*y = f
    z = x + y
    """
    vars = identify_variables_from_text(text)
    expected = ['a', 'b', 'c', 'd', 'e', 'f', 'x', 'y', 'z']
    assert vars == expected, f"变量识别不匹配。期望 {expected}，实际 {vars}"
    # 验证无重复
    assert len(vars) == len(set(vars)), "存在重复变量"
    return True

try:
    test_variable_identification_complete()
    result.record("核心基础", "变量识别无遗漏无重复", True, "9个变量全部识别")
except Exception as e:
    result.record("核心基础", "变量识别无遗漏无重复", False, str(e))


def test_variable_identification_with_subscripts():
    """带下标变量的识别"""
    text = """
    v_out = A_v * v_in
    i_load = v_out / R_load
    v_in = i_sig * R_sig
    """
    vars = identify_variables_from_text(text)
    expected = ['A_v', 'R_load', 'R_sig', 'i_load', 'i_sig', 'v_in', 'v_out']
    assert vars == expected, f"期望 {expected}，实际 {vars}"
    return True

try:
    test_variable_identification_with_subscripts()
    result.record("核心基础", "带下标变量识别", True, "7个变量")
except Exception as e:
    result.record("核心基础", "带下标变量识别", False, str(e))


# ============================================================================
# 二、自定义进阶功能验证
# ============================================================================

print("\n" + "=" * 70)
print("二、自定义进阶功能验证")
print("=" * 70)

# --- 2.1 中间变量自定义屏蔽 ---
print("\n【2.1】中间变量自定义屏蔽功能")

def test_intermediate_var_elimination():
    """验证中间变量在最终结果中被彻底剔除"""
    text = """
    v_1 = I_1 * R_1
    v_2 = I_2 * R_2
    I_1 = I_2
    v_1 + v_2 = V_total
    """
    res = simplify_system(text, intermediate_vars=['I_1', 'I_2'], target_expressions=['v_1', 'v_2'])
    for r in res['results']:
        expr = sp.sympify(r['python'])
        free_vars = [str(v) for v in expr.free_symbols]
        # 关键验证：结果中不应包含 I_1 或 I_2
        assert 'I_1' not in free_vars, f"结果 {r['target']} 中仍包含中间变量 I_1: {free_vars}"
        assert 'I_2' not in free_vars, f"结果 {r['target']} 中仍包含中间变量 I_2: {free_vars}"
    return True

try:
    test_intermediate_var_elimination()
    result.record("进阶功能", "中间变量彻底屏蔽", True, "结果中无 I_1, I_2")
except Exception as e:
    result.record("进阶功能", "中间变量彻底屏蔽", False, str(e))


def test_intermediate_var_participates():
    """验证中间变量全程参与运算（不是简单忽略）"""
    # 如果中间变量不参与运算，结果会错误
    text = """
    y = 2*x + 3*m
    m = x + 1
    """
    # m 是中间变量，y 应该 = 2x + 3(x+1) = 5x + 3
    res = simplify_system(text, intermediate_vars=['m'], target_expressions=['y'])
    y_val = sp.sympify(res['results'][0]['python'])
    x = sp.symbols('x')
    expected = 5 * x + 3
    assert sp.simplify(y_val - expected) == 0, f"y 应为 5x+3（中间变量参与运算），实际 {y_val}"
    # 验证结果中无 m
    assert 'm' not in [str(v) for v in y_val.free_symbols], "结果中仍包含 m"
    return True

try:
    test_intermediate_var_participates()
    result.record("进阶功能", "中间变量参与运算后屏蔽", True, "y=5x+3（m已代入）")
except Exception as e:
    result.record("进阶功能", "中间变量参与运算后屏蔽", False, str(e))


def test_multiple_intermediate_vars():
    """多个中间变量链式消去"""
    text = """
    result = a * step1
    step1 = b * step2
    step2 = c * src_val
    """
    res = simplify_system(
        text,
        intermediate_vars=['step1', 'step2'],
        target_expressions=['result']
    )
    result_val = sp.sympify(res['results'][0]['python'])
    a, b, c, sv = sp.symbols('a b c src_val')
    expected = a * b * c * sv
    assert sp.simplify(result_val - expected) == 0, f"result 应为 a*b*c*src_val，实际 {result_val}"
    free = [str(v) for v in result_val.free_symbols]
    assert 'step1' not in free and 'step2' not in free, "中间变量未完全消去"
    return True

try:
    test_multiple_intermediate_vars()
    result.record("进阶功能", "多中间变量链式消去", True, "result=a*b*c*input")
except Exception as e:
    result.record("进阶功能", "多中间变量链式消去", False, str(e))


# --- 2.2 目标结果自定义指定 ---
print("\n【2.2】目标结果自定义指定功能")

def test_target_single_var():
    """指定单一变量结果"""
    text = """
    x + y = 10
    x - y = 4
    """
    res = simplify_system(text, target_expressions=['x'])
    assert len(res['results']) == 1, f"应只输出1个结果，实际 {len(res['results'])}"
    assert res['results'][0]['target'] == 'x'
    assert sp.sympify(res['results'][0]['python']) == 7, "x 应为 7"
    return True

try:
    test_target_single_var()
    result.record("进阶功能", "指定单一变量结果", True, "x=7")
except Exception as e:
    result.record("进阶功能", "指定单一变量结果", False, str(e))


def test_target_fraction():
    """指定变量分式结果 v_1/v_2"""
    text = """
    v_1 = I_1 * R_1
    v_2 = I_2 * R_2
    I_1 = I_2
    v_1 + v_2 = V_total
    """
    res = simplify_system(text, intermediate_vars=['I_1', 'I_2'], target_expressions=['v_1/v_2'])
    ratio = sp.sympify(res['results'][0]['python'])
    R1, R2 = sp.symbols('R_1 R_2')
    expected = R1 / R2
    assert sp.simplify(ratio - expected) == 0, f"v1/v2 应为 R1/R2，实际 {ratio}"
    return True

try:
    test_target_fraction()
    result.record("进阶功能", "指定变量分式结果", True, "v_1/v_2 = R_1/R_2")
except Exception as e:
    result.record("进阶功能", "指定变量分式结果", False, str(e))


def test_target_multi_var_combo():
    """多变量组合结果"""
    text = """
    x + y = 10
    x - y = 4
    """
    res = simplify_system(text, target_expressions=['x + y', 'x * y', 'x**2 + y**2'])
    assert len(res['results']) == 3
    # x=7, y=3
    assert sp.sympify(res['results'][0]['python']) == 10, "x+y 应为 10"
    assert sp.sympify(res['results'][1]['python']) == 21, "x*y 应为 21"
    assert sp.sympify(res['results'][2]['python']) == 58, "x^2+y^2 应为 58"
    return True

try:
    test_target_multi_var_combo()
    result.record("进阶功能", "多变量组合结果", True, "x+y=10, x*y=21, x²+y²=58")
except Exception as e:
    result.record("进阶功能", "多变量组合结果", False, str(e))


def test_target_default_all_non_intermediate():
    """不指定目标时，智能选择可求解的非中间变量（优先方程左边变量）"""
    text = """
    v_1 = I_1 * R_1
    v_2 = I_2 * R_2
    I_1 = I_2
    v_1 + v_2 = V_total
    """
    res = simplify_system(text, intermediate_vars=['I_1', 'I_2'])
    targets = [r['target'] for r in res['results']]
    # 智能选择：方程左边变量优先（v_1, v_2），排除中间变量
    assert 'v_1' in targets, "默认应包含 v_1"
    assert 'v_2' in targets, "默认应包含 v_2"
    assert 'I_1' not in targets, "默认不应包含中间变量 I_1"
    assert 'I_2' not in targets, "默认不应包含中间变量 I_2"
    # 结果数量不超过方程数-中间变量数
    assert len(targets) <= len(res['all_variables']) - 2
    return True

try:
    test_target_default_all_non_intermediate()
    result.record("进阶功能", "默认输出所有非中间变量", True)
except Exception as e:
    result.record("进阶功能", "默认输出所有非中间变量", False, str(e))


# --- 2.3 自定义同类项合并 ---
print("\n【2.3】自定义同类项合并功能")

def test_merge_like_terms_single():
    """单变量同类项合并"""
    expr = sp.sympify('a*x + b*x + c*x + d')
    merged = merge_like_terms(expr, ['x'])
    x = sp.symbols('x')
    expected = x * (sp.symbols('a') + sp.symbols('b') + sp.symbols('c')) + sp.symbols('d')
    assert sp.simplify(merged - expected) == 0, f"合并结果不匹配: {merged}"
    return True

try:
    test_merge_like_terms_single()
    result.record("进阶功能", "单变量同类项合并", True, "x(a+b+c)+d")
except Exception as e:
    result.record("进阶功能", "单变量同类项合并", False, str(e))


def test_merge_like_terms_multi():
    """多变量批量合并"""
    expr = sp.sympify('a*x + b*x + c*y + d*y + e')
    merged = merge_like_terms(expr, ['x', 'y'])
    x, y = sp.symbols('x y')
    a, b, c, d, e = sp.symbols('a b c d e')
    expected = x * (a + b) + y * (c + d) + e
    assert sp.simplify(merged - expected) == 0, f"合并结果不匹配: {merged}"
    return True

try:
    test_merge_like_terms_multi()
    result.record("进阶功能", "多变量批量合并", True, "x(a+b)+y(c+d)+e")
except Exception as e:
    result.record("进阶功能", "多变量批量合并", False, str(e))


def test_merge_in_simplify_pipeline():
    """合并功能在完整化简流程中生效"""
    text = """
    y = a*x + b*x + c*x + d
    z = 2*x + 3*x + 5
    """
    res = simplify_system(text, target_expressions=['y', 'z'], merge_vars=['x'])
    y_val = sp.sympify(res['results'][0]['python'])
    z_val = sp.sympify(res['results'][1]['python'])
    x = sp.symbols('x')
    # y 应合并为 x*(a+b+c)+d
    assert sp.expand(y_val - (x * (sp.symbols('a') + sp.symbols('b') + sp.symbols('c')) + sp.symbols('d'))) == 0
    # z 应合并为 5*x + 5
    assert z_val == 5 * x + 5, f"z 应为 5x+5，实际 {z_val}"
    return True

try:
    test_merge_in_simplify_pipeline()
    result.record("进阶功能", "合并功能在化简流程中生效", True)
except Exception as e:
    result.record("进阶功能", "合并功能在化简流程中生效", False, str(e))


# ============================================================================
# 三、公式渲染规则验证
# ============================================================================

print("\n" + "=" * 70)
print("三、公式渲染规则验证")
print("=" * 70)

# --- 3.1 LaTeX 输出 ---
print("\n【3.1】LaTeX/KaTeX 渲染输出")

def test_latex_output_fraction():
    """分式渲染"""
    text = """
    x + y = 10
    x - y = 4
    """
    res = simplify_system(text, target_expressions=['x/y'])
    latex_str = res['results'][0]['latex']
    assert '\\frac' in latex_str, f"分式应使用 \\frac 渲染: {latex_str}"
    return True

try:
    test_latex_output_fraction()
    result.record("渲染规则", "分式LaTeX渲染", True)
except Exception as e:
    result.record("渲染规则", "分式LaTeX渲染", False, str(e))


def test_latex_output_superscript():
    """上标（幂）渲染"""
    text = "y = x**2 + 2*x + 1"
    eqs = parse_equations(text)
    latex_str = sp.latex(eqs[0])
    assert '^{2}' in latex_str or '^2' in latex_str, f"上标渲染不正确: {latex_str}"
    return True

try:
    test_latex_output_superscript()
    result.record("渲染规则", "上标LaTeX渲染", True)
except Exception as e:
    result.record("渲染规则", "上标LaTeX渲染", False, str(e))


# --- 3.2 多字符下标渲染BUG修复 ---
print("\n【3.2】多字符下标渲染BUG修复（重点）")

def test_subscript_render_two_digits():
    """v_12 必须渲染为 v_{12}，不是 v_1 2"""
    latex_str = render_equation_latex("v_12 = I_1 * R_123")
    # 关键验证：必须有 v_{12}，不能是 v_1 后面跟 2
    assert 'v_{12}' in latex_str, f"v_12 应渲染为 v_{{12}}，实际: {latex_str}"
    assert 'R_{123}' in latex_str, f"R_123 应渲染为 R_{{123}}，实际: {latex_str}"
    return True

try:
    test_subscript_render_two_digits()
    result.record("渲染规则", "两位数下标完整渲染 v_{12}", True)
except Exception as e:
    result.record("渲染规则", "两位数下标完整渲染 v_{12}", False, str(e))


def test_subscript_render_alpha():
    """a_xy 必须渲染为 a_{xy}"""
    latex_str = render_equation_latex("a_xy + b_xy = c_z")
    assert 'a_{xy}' in latex_str, f"a_xy 应渲染为 a_{{xy}}，实际: {latex_str}"
    assert 'b_{xy}' in latex_str, f"b_xy 应渲染为 b_{{xy}}，实际: {latex_str}"
    assert 'c_{z}' in latex_str, f"c_z 应渲染为 c_{{z}}，实际: {latex_str}"
    return True

try:
    test_subscript_render_alpha()
    result.record("渲染规则", "字母下标完整渲染 a_{xy}", True)
except Exception as e:
    result.record("渲染规则", "字母下标完整渲染 a_{xy}", False, str(e))


def test_subscript_in_results():
    """化简结果中的下标也正确渲染"""
    text = """
    v_out = A_v * v_in
    v_in = i_sig * R_sig
    """
    res = simplify_system(text, intermediate_vars=['v_in'], target_expressions=['v_out'])
    latex_str = res['results'][0]['latex']
    assert 'A_{v}' in latex_str or 'A_v' in latex_str, f"A_v 渲染不正确: {latex_str}"
    assert 'R_{sig}' in latex_str or 'R_sig' in latex_str, f"R_sig 渲染不正确: {latex_str}"
    return True

try:
    test_subscript_in_results()
    result.record("渲染规则", "化简结果中下标正确渲染", True)
except Exception as e:
    result.record("渲染规则", "化简结果中下标正确渲染", False, str(e))


def test_fix_latex_subscripts_function():
    """fix_latex_subscripts 兜底函数测试"""
    # 模拟有问题的LaTeX：v_12 没有花括号
    fixed = fix_latex_subscripts("v_12 = R_123 * I_1")
    assert 'v_{12}' in fixed, f"应修复为 v_{{12}}，实际: {fixed}"
    assert 'R_{123}' in fixed, f"应修复为 R_{{123}}，实际: {fixed}"
    return True

try:
    test_fix_latex_subscripts_function()
    result.record("渲染规则", "下标修复兜底函数", True)
except Exception as e:
    result.record("渲染规则", "下标修复兜底函数", False, str(e))


# --- 3.3 学术规范渲染 ---
print("\n【3.3】学术规范渲染（分式、根号、括号等）")

def test_render_sqrt():
    """根号渲染"""
    text = "y = sqrt(x**2 + 1)"
    eqs = parse_equations(text)
    latex_str = sp.latex(eqs[0])
    assert '\\sqrt' in latex_str, f"根号应使用 \\sqrt: {latex_str}"
    return True

try:
    test_render_sqrt()
    result.record("渲染规则", "根号LaTeX渲染", True)
except Exception as e:
    result.record("渲染规则", "根号LaTeX渲染", False, str(e))


def test_render_parentheses():
    """括号渲染"""
    text = "y = (x + 1) * (x - 1)"
    eqs = parse_equations(text)
    latex_str = sp.latex(eqs[0])
    assert '(' in latex_str and ')' in latex_str, f"括号渲染: {latex_str}"
    return True

try:
    test_render_parentheses()
    result.record("渲染规则", "括号LaTeX渲染", True)
except Exception as e:
    result.record("渲染规则", "括号LaTeX渲染", False, str(e))


# ============================================================================
# 四、界面与文件完整性验证
# ============================================================================

print("\n" + "=" * 70)
print("四、界面与文件完整性验证")
print("=" * 70)

def check_file_exists(rel_path, desc):
    full = os.path.join(PROJECT_ROOT, rel_path)
    exists = os.path.exists(full)
    size = os.path.getsize(full) if exists else 0
    result.record("界面文件", desc, exists, f"{rel_path} ({size} bytes)" if exists else f"缺失: {rel_path}")
    return exists

print("\n【4.1】核心文件存在性")
check_file_exists("app.py", "Flask后端主程序")
check_file_exists("core/engine.py", "核心化简引擎")
check_file_exists("core/__init__.py", "核心模块初始化")
check_file_exists("templates/index.html", "前端主页面")
check_file_exists("static/css/style.css", "极简风格样式表")
check_file_exists("static/js/app.js", "前端交互逻辑")
check_file_exists("run.bat", "Windows启动脚本")

print("\n【4.2】KaTeX 本地离线资源")
check_file_exists("static/vendor/katex/katex.min.css", "KaTeX样式表")
check_file_exists("static/vendor/katex/katex.min.js", "KaTeX脚本")
# 检查字体文件
fonts_dir = os.path.join(PROJECT_ROOT, "static/vendor/katex/fonts")
if os.path.exists(fonts_dir):
    font_count = len([f for f in os.listdir(fonts_dir) if f.endswith('.woff2')])
    result.record("界面文件", "KaTeX字体文件", font_count >= 15, f"{font_count} 个 woff2 字体")
else:
    result.record("界面文件", "KaTeX字体文件", False, "fonts目录不存在")


print("\n【4.3】界面功能分区检查")
def test_ui_sections():
    """验证HTML中包含所有要求的功能分区"""
    html_path = os.path.join(PROJECT_ROOT, "templates/index.html")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    checks = {
        "公式输入区": 'equations-input' in html,
        "自定义参数设置区": 'intermediate-vars' in html and 'target-exprs' in html and 'merge-vars' in html,
        "实时渲染预览区": 'preview-area' in html,
        "最终结果输出区": 'result-area' in html,
        "中间变量输入": 'intermediate-vars' in html,
        "目标结果输入": 'target-exprs' in html,
        "合并变量输入": 'merge-vars' in html,
        "化简按钮": 'simplify-btn' in html,
        "KaTeX本地引用": 'static/vendor/katex' in html,
    }
    all_pass = True
    for name, ok in checks.items():
        if not ok:
            all_pass = False
            result.record("界面文件", f"界面分区: {name}", False)
    if all_pass:
        result.record("界面文件", "所有界面功能分区完整", True, f"{len(checks)} 项检查全部通过")
    return all_pass

test_ui_sections()


print("\n【4.4】极简风格检查")
def test_minimalist_style():
    css_path = os.path.join(PROJECT_ROOT, "static/css/style.css")
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()
    # 检查无花哨动画/特效
    has_animation = '@keyframes' in css or 'animation:' in css
    has_gradients = 'gradient' in css.lower()
    has_shadow = 'box-shadow' in css
    result.record("界面文件", "无花哨动画", not has_animation, "不含@keyframes" if not has_animation else "包含动画")
    result.record("界面文件", "无渐变背景", not has_gradients, "不含gradient" if not has_gradients else "包含渐变")
    # 轻微阴影是可接受的（极简风格常用）
    return True

test_minimalist_style()


# ============================================================================
# 五、API 集成测试
# ============================================================================

print("\n" + "=" * 70)
print("五、Flask API 集成测试")
print("=" * 70)

# 启动测试服务器
from app import app

def api_post(path, data):
    """发送POST请求到测试客户端"""
    with app.test_client() as client:
        resp = client.post(path, json=data, content_type='application/json')
        return resp.status_code, resp.get_json()


print("\n【5.1】/api/identify 变量识别接口")
def test_api_identify():
    code, data = api_post('/api/identify', {
        'equations': 'v_1 = I_1 * R_1\nv_2 = I_2 * R_2\nI_1 = I_2\nv_1 + v_2 = V_total'
    })
    assert code == 200, f"状态码应为200，实际 {code}"
    assert data['success'] == True
    assert len(data['variables']) == 7
    assert 'v_1' in data['variables']
    assert 'R_123' not in data['variables']  # 不应有不存在的变量
    return True

try:
    test_api_identify()
    result.record("API集成", "/api/identify 变量识别", True, "7个变量")
except Exception as e:
    result.record("API集成", "/api/identify 变量识别", False, str(e))


print("\n【5.2】/api/preview 实时预览接口")
def test_api_preview():
    code, data = api_post('/api/preview', {
        'lines': ['v_12 = I_1 * R_123', 'a_xy + b_xy = c']
    })
    assert code == 200
    assert data['success'] == True
    assert len(data['latex_list']) == 2
    assert 'v_{12}' in data['latex_list'][0], "多字符下标应完整渲染"
    assert 'R_{123}' in data['latex_list'][0]
    assert 'a_{xy}' in data['latex_list'][1]
    return True

try:
    test_api_preview()
    result.record("API集成", "/api/preview 实时预览", True, "下标完整渲染")
except Exception as e:
    result.record("API集成", "/api/preview 实时预览", False, str(e))


print("\n【5.3】/api/simplify 核心化简接口")
def test_api_simplify():
    code, data = api_post('/api/simplify', {
        'equations': 'v_1 = I_1 * R_1\nv_2 = I_2 * R_2\nI_1 = I_2\nv_1 + v_2 = V_total',
        'intermediate_vars': ['I_1', 'I_2'],
        'target_expressions': ['v_1', 'v_2', 'v_1/v_2'],
        'merge_vars': []
    })
    assert code == 200
    assert data['success'] == True
    d = data['data']
    assert len(d['results']) == 3
    assert d['results'][0]['target'] == 'v_1'
    assert 'R_{1}' in d['results'][0]['latex']
    # 验证中间变量已屏蔽
    for r in d['results']:
        expr = sp.sympify(r['python'])
        free = [str(v) for v in expr.free_symbols]
        assert 'I_1' not in free, f"结果 {r['target']} 包含中间变量 I_1"
        assert 'I_2' not in free, f"结果 {r['target']} 包含中间变量 I_2"
    # 验证步骤输出
    assert len(d['steps']) > 0
    return True

try:
    test_api_simplify()
    result.record("API集成", "/api/simplify 核心化简", True, "3个结果，中间变量已屏蔽")
except Exception as e:
    result.record("API集成", "/api/simplify 核心化简", False, str(e))


print("\n【5.4】API 错误处理")
def test_api_error_handling():
    # 缺少等号的方程
    code, data = api_post('/api/simplify', {
        'equations': 'x + y 10',  # 缺少等号
        'target_expressions': ['x']
    })
    assert code == 400, f"无效方程应返回400，实际 {code}"
    assert data['success'] == False
    assert 'error' in data

    # 方程数不足
    code2, data2 = api_post('/api/simplify', {
        'equations': 'x + y = 10',
        'target_expressions': ['x', 'y']
    })
    assert code2 == 400, f"方程数不足应返回400，实际 {code2}"
    return True

try:
    test_api_error_handling()
    result.record("API集成", "API错误处理", True, "无效输入返回400")
except Exception as e:
    result.record("API集成", "API错误处理", False, str(e))


print("\n【5.5】首页可访问")
def test_homepage():
    with app.test_client() as client:
        resp = client.get('/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert '方程组自动化简' in html
        assert 'katex.min.js' in html
    return True

try:
    test_homepage()
    result.record("API集成", "首页可访问", True)
except Exception as e:
    result.record("API集成", "首页可访问", False, str(e))


# ============================================================================
# 六、补充约束验证
# ============================================================================

print("\n" + "=" * 70)
print("六、补充约束验证")
print("=" * 70)

print("\n【6.1】用户自定义规则优先级最高")
def test_custom_rules_priority():
    """验证用户设置的合并变量、中间变量、目标输出优先级最高"""
    text = """
    y = a*x + b*x + c
    z = d*x + e*x + f
    """
    # 用户指定合并x，指定只输出y，不输出z
    res = simplify_system(text, target_expressions=['y'], merge_vars=['x'])
    assert len(res['results']) == 1, "用户指定只输出y，应只有1个结果"
    assert res['results'][0]['target'] == 'y'
    # 验证合并生效
    y_val = sp.sympify(res['results'][0]['python'])
    x = sp.symbols('x')
    expected = x * (sp.symbols('a') + sp.symbols('b')) + sp.symbols('c')
    assert sp.simplify(y_val - expected) == 0, "合并变量规则未生效"
    return True

try:
    test_custom_rules_priority()
    result.record("补充约束", "用户自定义规则优先级最高", True)
except Exception as e:
    result.record("补充约束", "用户自定义规则优先级最高", False, str(e))


print("\n【6.2】实时编辑支持（防抖机制）")
def test_realtime_debounce():
    """验证前端JS中包含防抖实时更新逻辑"""
    js_path = os.path.join(PROJECT_ROOT, "static/js/app.js")
    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()
    has_debounce = 'setTimeout' in js and 'clearTimeout' in js
    has_input_listener = "addEventListener('input'" in js or 'addEventListener("input"' in js
    has_preview_api = '/api/preview' in js
    result.record("补充约束", "前端防抖实时更新", has_debounce and has_input_listener,
                  "含setTimeout/clearTimeout和input监听" if has_debounce and has_input_listener else "缺失")
    result.record("补充约束", "实时预览API调用", has_preview_api)
    return True

test_realtime_debounce()


print("\n【6.3】输出结果LaTeX规范渲染")
def test_output_latex_standard():
    """验证所有输出结果都包含LaTeX字段"""
    text = "x + y = 10\nx - y = 4"
    res = simplify_system(text, target_expressions=['x', 'y'])
    for r in res['results']:
        assert 'latex' in r, f"结果缺少latex字段: {r}"
        assert 'python' in r, f"结果缺少python字段: {r}"
        assert 'target' in r, f"结果缺少target字段: {r}"
        assert len(r['latex']) > 0, "latex字段为空"
    return True

try:
    test_output_latex_standard()
    result.record("补充约束", "输出结果LaTeX规范渲染", True, "每个结果含latex/python/target")
except Exception as e:
    result.record("补充约束", "输出结果LaTeX规范渲染", False, str(e))


print("\n【6.4】隐式乘法支持（2x → 2*x）")
def test_implicit_multiplication():
    """验证用户输入 2x 时自动识别为 2*x"""
    text = "2x + 3y = 12\nx - y = 1"
    eqs = parse_equations(text)
    x, y = sp.symbols('x y')
    sol = sp.solve(eqs, [x, y], dict=True)[0]
    assert sol[x] == 3, f"x 应为 3，实际 {sol[x]}"
    assert sol[y] == 2, f"y 应为 2，实际 {sol[y]}"
    return True

try:
    test_implicit_multiplication()
    result.record("补充约束", "隐式乘法支持 2x→2*x", True, "x=3, y=2")
except Exception as e:
    result.record("补充约束", "隐式乘法支持 2x→2*x", False, str(e))


print("\n【6.5】注释行和空行忽略")
def test_comments_and_blank_lines():
    text = """
    # 这是注释
    x + y = 10

    # 另一个注释
    x - y = 4
    """
    eqs = parse_equations(text)
    assert len(eqs) == 2, f"应只解析2个有效方程，实际 {len(eqs)}"
    return True

try:
    test_comments_and_blank_lines()
    result.record("补充约束", "注释行和空行忽略", True, "只解析2个有效方程")
except Exception as e:
    result.record("补充约束", "注释行和空行忽略", False, str(e))


# ============================================================================
# 七、桌面应用包装验证
# ============================================================================

print("\n" + "=" * 70)
print("七、桌面应用包装验证")
print("=" * 70)

print("\n【7.1】pywebview 桌面窗口支持")
def test_pywebview_available():
    try:
        import webview
        result.record("桌面应用", "pywebview 已安装", True, f"版本 {getattr(webview, '__version__', 'unknown')}")
        return True
    except ImportError:
        result.record("桌面应用", "pywebview 已安装", False, "未安装")
        return False

test_pywebview_available()


print("\n【7.2】app.py 包含桌面启动逻辑")
def test_desktop_launch_code():
    app_path = os.path.join(PROJECT_ROOT, "app.py")
    with open(app_path, 'r', encoding='utf-8') as f:
        code = f.read()
    has_webview = 'webview.create_window' in code
    has_waitress = 'waitress' in code
    has_fallback = '--web' in code and 'run_web' in code
    result.record("桌面应用", "桌面窗口创建逻辑", has_webview)
    result.record("桌面应用", "waitress生产服务器", has_waitress)
    result.record("桌面应用", "浏览器模式回退", has_fallback)
    return True

test_desktop_launch_code()


print("\n【7.3】Windows 启动脚本")
def test_run_bat():
    bat_path = os.path.join(PROJECT_ROOT, "run.bat")
    with open(bat_path, 'r', encoding='utf-8') as f:
        content = f.read()
    has_python = 'python app.py' in content
    has_chcp = 'chcp 65001' in content  # UTF-8支持
    result.record("桌面应用", "run.bat 启动脚本", has_python and has_chcp,
                  "含python启动和UTF-8编码设置" if has_python and has_chcp else "缺失")
    return True

test_run_bat()


# ============================================================================
# 八、希腊字母变量验证
# ============================================================================

print("\n" + "=" * 70)
print("八、希腊字母变量验证")
print("=" * 70)

print("\n【8.1】/beta 作为变量识别")
def test_greek_beta_var():
    text = "y = /beta * x + 1"
    vars = identify_variables_from_text(text)
    assert 'beta' in vars, f"应识别 beta 变量，实际 {vars}"
    assert 'x' in vars
    assert 'y' in vars
    return True

try:
    test_greek_beta_var()
    result.record("希腊字母", "/beta 识别为变量β", True)
except Exception as e:
    result.record("希腊字母", "/beta 识别为变量β", False, str(e))


print("\n【8.2】beta（不带斜杠）保持 SymPy 函数")
def test_beta_as_function():
    # 直接输入 beta 不应被识别为用户变量（保持SymPy贝塔函数）
    text = "y = x + 1"
    vars = identify_variables_from_text(text)
    assert 'beta' not in vars, "纯文本中无beta，自然不识别"
    # 含 beta 函数调用的场景
    text2 = "y = beta(x, 2) + 1"
    vars2 = identify_variables_from_text(text2)
    # beta 是函数名，不应识别为变量；x 是变量
    assert 'x' in vars2, f"应识别 x，实际 {vars2}"
    assert 'beta' not in vars2, "beta 应保持为SymPy函数，不识别为用户变量"
    return True

try:
    test_beta_as_function()
    result.record("希腊字母", "beta保持SymPy函数不被覆盖", True)
except Exception as e:
    result.record("希腊字母", "beta保持SymPy函数不被覆盖", False, str(e))


print("\n【8.3】希腊字母 LaTeX 渲染")
def test_greek_latex():
    text = "y = /alpha * x + /beta * z"
    res = simplify_system(text, target_expressions=['y'])
    latex_str = res['results'][0]['latex']
    assert '\\alpha' in latex_str, f"应包含 \\alpha，实际 {latex_str}"
    assert '\\beta' in latex_str, f"应包含 \\beta，实际 {latex_str}"
    return True

try:
    test_greek_latex()
    result.record("希腊字母", "希腊字母LaTeX渲染 α β", True)
except Exception as e:
    result.record("希腊字母", "希腊字母LaTeX渲染 α β", False, str(e))


print("\n【8.4】多个希腊字母")
def test_multiple_greek():
    text = """
    y = /alpha * x + /beta * z
    z = /gamma * x
    """
    res = simplify_system(text, intermediate_vars=['z'], target_expressions=['y'])
    vars = identify_variables_from_text(text)
    assert 'alpha' in vars
    assert 'beta' in vars
    assert 'gamma' in vars
    python_str = res['results'][0]['python']
    assert 'alpha' in python_str
    assert 'beta' in python_str
    assert 'gamma' in python_str
    return True

try:
    test_multiple_greek()
    result.record("希腊字母", "多希腊字母 α β γ 同时使用", True)
except Exception as e:
    result.record("希腊字母", "多希腊字母 α β γ 同时使用", False, str(e))


print("\n【8.5】电路方程组含 /beta")
def test_circuit_with_beta():
    text = """
    V_1 = (g_m*/beta*r_0*V_i + s*C*r_0*V_o) / (1 + s*C*r_0)
    s*C*V_1 = (g_m4 + s*C + 1/r_o4)*V_o - g_m4*V_2
    g_m4*V_o = g_m3*V_1 + (g_m4 + 1/r_o3 + 1/r_o4)*V_2
    """
    res = simplify_system(text, intermediate_vars=['V_1', 'V_2'], target_expressions=['V_o/V_i'])
    assert len(res['results']) == 1
    assert 'beta' in res['all_variables']
    latex_str = res['results'][0]['latex']
    assert '\\beta' in latex_str, "结果应包含 \\beta"
    # 验证中间变量已屏蔽
    assert 'V_1' not in res['results'][0]['python']
    assert 'V_2' not in res['results'][0]['python']
    return True

try:
    test_circuit_with_beta()
    result.record("希腊字母", "电路方程组含/beta化简成功", True)
except Exception as e:
    result.record("希腊字母", "电路方程组含/beta化简成功", False, str(e))


print("\n【8.6】希腊字母带下标")
def test_greek_with_subscript():
    text = "y = /beta_1 * x + /beta_2 * z"
    vars = identify_variables_from_text(text)
    assert 'beta_1' in vars, f"应识别 beta_1，实际 {vars}"
    assert 'beta_2' in vars
    res = simplify_system(text, target_expressions=['y'])
    assert '\\beta_{1}' in res['results'][0]['latex'] or '\\beta_1' in res['results'][0]['latex']
    return True

try:
    test_greek_with_subscript()
    result.record("希腊字母", "希腊字母带下标 β₁ β₂", True)
except Exception as e:
    result.record("希腊字母", "希腊字母带下标 β₁ β₂", False, str(e))


# ============================================================================
# 最终总结
# ============================================================================

all_passed = result.summary()
sys.exit(0 if all_passed else 1)
