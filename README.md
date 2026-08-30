<!--
  Equation System Auto-Simplifier
  Bilingual README (English / 中文)
-->

<div align="center">

# Equation System Auto-Simplifier
# 方程组自动化简软件

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green)](https://flask.palletsprojects.com/)
[![SymPy](https://img.shields.io/badge/SymPy-1.12%2B-orange)](https://www.sympy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

A minimalist desktop application for automatic equation system simplification, powered by symbolic computation.

一款基于符号计算的极简风格桌面方程组自动化简软件。

[English](#english) | [中文](#中文)

</div>

---

<a id="english"></a>
## English

### Features

#### Core Functionality
- **Multi-equation input**: Simplify, eliminate, and merge polynomial, rational, and multi-variable equation systems
- **Custom subscripts**: `v_1`, `R_123`, `a_xy` — all characters after underscore are treated as subscript
- **Greek letter variables**: Prefix with `/` to use as a variable — `/beta` → β, `/gamma` → γ. Typing `beta` directly keeps it as SymPy's built-in beta function
- **Auto variable detection**: Scans all equations and identifies every independent variable
- **Implicit multiplication**: `2x` is automatically parsed as `2*x`

#### Advanced Customization
- **Intermediate variable masking**: Variables marked as intermediate participate in computation but are removed from final output
- **Target expression**: Specify output form — single variable (`v_1`), ratio (`v_1/v_2`), or combination (`v_1 + v_2`)
- **Like-term merging**: Group and merge terms containing specified variables

#### Rendering
- **LaTeX / KaTeX rendering**: Real-time rendering of all inputs and results
- **Multi-character subscript fix**: `v_12` renders as `v_{12}`, not `v_1 2`
- **Offline KaTeX**: No internet connection required for formula rendering

#### Interface
- Minimalist design with four functional zones
- Collapsible "Input Help" panel at the bottom
- Desktop window mode (pywebview) or browser mode

---

### Quick Start

#### Prerequisites
- Windows 10 / 11
- Python 3.8 or higher (check "Add Python to PATH" during installation)
- Internet connection required for first run (auto-installs dependencies)

#### Installation & Run

**Option 1: One-click launcher (recommended)**
1. Clone or download this repository
2. Double-click `方程组自动化简.exe`
3. On first run, it automatically creates a `.venv` virtual environment and installs dependencies (~1-2 minutes)
4. Subsequent launches start instantly

**Option 2: Command line**
```bash
# Desktop window mode
python app.py

# Browser mode
python app.py --web
```

---

### Input Guide

#### Greek Letter Variables
Prefix with `/` to use as a variable:

| Input | Symbol | Input | Symbol |
|-------|--------|-------|--------|
| `/alpha` | α | `/mu` | μ |
| `/beta` | β | `/nu` | ν |
| `/gamma` | γ | `/xi` | ξ |
| `/delta` | δ | `/pi` | π |
| `/epsilon` | ε | `/rho` | ρ |
| `/zeta` | ζ | `/sigma` | σ |
| `/eta` | η | `/tau` | τ |
| `/theta` | θ | `/phi` | φ |
| `/iota` | ι | `/chi` | χ |
| `/kappa` | κ | `/psi` | ψ |
| `/lambda` | λ | `/omega` | ω |

With subscripts: `/beta_1` → β₁

> Typing `beta`, `gamma`, etc. directly keeps them as SymPy built-in math functions.

#### Basic Operations
| Input | Meaning |
|-------|---------|
| `+ - * /` | Arithmetic |
| `x^2` or `x**2` | Power |
| `2x` | Implicit multiplication (2 × x) |
| `(x+1)(x-1)` | Implicit multiplication between groups |

#### Common Functions
| Input | Meaning |
|-------|---------|
| `sqrt(x)` | Square root √x |
| `sin(x) cos(x) tan(x)` | Trigonometric |
| `exp(x)` | Exponential eˣ |
| `log(x)` | Natural logarithm ln x |
| `abs(x)` | Absolute value \|x\| |

#### Equation Format
- One equation per line, separated by `=`
- Lines starting with `#` are comments
- Blank lines are ignored

#### Custom Parameters
- **Intermediate variables**: Comma-separated, e.g. `V_1, V_2` — participate in computation, removed from output
- **Target expressions**: Desired output form, e.g. `V_o/V_i`
- **Merge variables**: Group like-terms by specified variables
- **Ctrl+Enter**: Quick simplify shortcut

---

### Example

#### Circuit Transfer Function (with Greek letters)
```
V_1 = (g_m*/beta*r_0*V_i + s*C*r_0*V_o) / (1 + s*C*r_0)
s*C*V_1 = (g_m4 + s*C + 1/r_o4)*V_o - g_m4*V_2
g_m4*V_o = g_m3*V_1 + (g_m4 + 1/r_o3 + 1/r_o4)*V_2
```
- Intermediate variables: `V_1, V_2`
- Target: `V_o/V_i`

Output: Complete s-domain transfer function with β rendered as Greek letter.

---

### Project Structure

```
TEST/
├── 方程组自动化简.exe      # Desktop launcher (auto environment setup)
├── launcher.cs             # Launcher C# source
├── app.py                  # Flask backend + pywebview entry
├── requirements.txt        # Python dependencies
├── run.bat / run_web.bat  # Backup launch scripts
├── core/
│   ├── __init__.py
│   └── engine.py           # Core simplification engine
├── templates/
│   └── index.html          # Frontend page
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── vendor/katex/       # Offline KaTeX resources
├── tests/
│   └── test_features.py    # 64 functional tests
└── .venv/                  # Auto-created virtual environment
```

---

### Running Tests

```bash
python tests/test_features.py
```

64 tests across 8 categories:
- Core functionality (simplification, subscripts, variable detection, implicit multiplication)
- Advanced customization (intermediate masking, target expressions, term merging)
- Rendering rules (LaTeX output, multi-character subscripts)
- Interface & file integrity
- Flask API integration
- Supplementary constraints
- Desktop packaging
- Greek letter variables

---

### Tech Stack

- **Backend**: Python 3 + Flask + SymPy (symbolic computation)
- **Frontend**: HTML + CSS + JavaScript + KaTeX
- **Desktop**: pywebview + waitress (production WSGI server)
- **Launcher**: C# compiled native exe (auto environment detection)

---

### License

This project is licensed under the MIT License.

---

<a id="中文"></a>
## 中文

### 功能特性

#### 核心基础功能
- **批量输入多元方程组**：支持整式、分式、多项式、多元联立方程组的逐级化简、消元、合并运算
- **下划线自定义下标**：`v_1`、`R_123`、`a_xy`，下划线后所有字符统一识别为完整下标
- **希腊字母变量**：在名称前加 `/` 即识别为变量——`/beta` → β、`/gamma` → γ。直接输入 `beta` 保持为 SymPy 内置贝塔函数
- **智能变量识别**：自动扫描所有方程，精准识别全部独立变量
- **隐式乘法支持**：`2x` 自动识别为 `2*x`

#### 自定义进阶功能
- **中间变量屏蔽**：标记的中间变量全程参与运算，但最终输出中自动剔除
- **目标结果指定**：支持单一变量（`v_1`）、变量分式（`v_1/v_2`）、多变量组合（`v_1 + v_2`）
- **同类项合并**：指定特征变量，自动归类合并所有包含该变量的项

#### 公式渲染
- **LaTeX / KaTeX 双兼容**：所有输入、结果实时渲染
- **多字符下标修复**：`v_12` 完整渲染为 `v_{12}`
- **离线 KaTeX**：公式渲染无需联网

#### 界面风格
- 极简简约风格，四大功能分区
- 底部可折叠「输入帮助」面板
- 桌面窗口模式（pywebview）或浏览器模式

---

### 快速开始

#### 系统要求
- Windows 10 / 11
- Python 3.8 或更高版本（安装时勾选 "Add Python to PATH"）
- 首次运行需联网（自动安装依赖）

#### 安装与运行

**方式一：一键启动器（推荐）**
1. 克隆或下载本仓库
2. 双击 `方程组自动化简.exe`
3. 首次运行自动创建 `.venv` 虚拟环境并安装依赖（约 1-2 分钟）
4. 后续启动秒级响应

**方式二：命令行启动**
```bash
# 桌面窗口模式
python app.py

# 浏览器模式
python app.py --web
```

---

### 输入指南

#### 希腊字母变量
在名称前加 `/` 即识别为变量：

| 输入 | 符号 | 输入 | 符号 |
|------|------|------|------|
| `/alpha` | α | `/mu` | μ |
| `/beta` | β | `/nu` | ν |
| `/gamma` | γ | `/xi` | ξ |
| `/delta` | δ | `/pi` | π |
| `/epsilon` | ε | `/rho` | ρ |
| `/zeta` | ζ | `/sigma` | σ |
| `/eta` | η | `/tau` | τ |
| `/theta` | θ | `/phi` | φ |
| `/iota` | ι | `/chi` | χ |
| `/kappa` | κ | `/psi` | ψ |
| `/lambda` | λ | `/omega` | ω |

支持带下标：`/beta_1` → β₁

> 直接输入 `beta`、`gamma` 等保持为 SymPy 内置数学函数。

#### 基本运算
| 输入 | 含义 |
|------|------|
| `+ - * /` | 加减乘除 |
| `x^2` 或 `x**2` | 幂运算 |
| `2x` | 隐式乘法（2 × x） |
| `(x+1)(x-1)` | 括号间隐式乘法 |

#### 常用函数
| 输入 | 含义 |
|------|------|
| `sqrt(x)` | 平方根 √x |
| `sin(x) cos(x) tan(x)` | 三角函数 |
| `exp(x)` | 指数 eˣ |
| `log(x)` | 自然对数 ln x |
| `abs(x)` | 绝对值 \|x\| |

#### 方程组格式
- 每行一个方程，用 `=` 分隔
- 以 `#` 开头的行为注释
- 空行自动忽略

#### 自定义参数
- **中间变量**：逗号分隔，如 `V_1, V_2`——参与运算但结果中屏蔽
- **目标结果**：指定输出形式，如 `V_o/V_i`
- **合并变量**：按指定变量合并同类项
- **Ctrl+Enter**：快捷执行化简

---

### 示例
<img width="1263" height="1019" alt="image" src="https://github.com/user-attachments/assets/5f56743c-3b40-45de-9198-aa824eda3516" />

#### 电路传输函数（含希腊字母）
```
V_1 = (g_m*/beta*r_0*V_i + s*C*r_0*V_o) / (1 + s*C*r_0)
s*C*V_1 = (g_m4 + s*C + 1/r_o4)*V_o - g_m4*V_2
g_m4*V_o = g_m3*V_1 + (g_m4 + 1/r_o3 + 1/r_o4)*V_2
```
- 中间变量：`V_1, V_2`
- 目标结果：`V_o/V_i`

输出：完整 s 域传输函数，β 正确渲染为希腊字母。

---

### 项目结构

```
TEST/
├── 方程组自动化简.exe      # 桌面启动器（自动环境设置）
├── launcher.cs             # 启动器 C# 源码
├── app.py                  # Flask 后端 + pywebview 入口
├── requirements.txt        # Python 依赖清单
├── run.bat / run_web.bat  # 备用启动脚本
├── core/
│   ├── __init__.py
│   └── engine.py           # 核心化简引擎
├── templates/
│   └── index.html          # 前端主页面
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── vendor/katex/       # 离线 KaTeX 资源
├── tests/
│   └── test_features.py    # 64 项功能测试
└── .venv/                  # 自动创建的虚拟环境
```

---

### 运行测试

```bash
python tests/test_features.py
```

覆盖 8 大类 64 项测试：
- 核心基础功能（化简、下标、变量识别、隐式乘法）
- 自定义进阶功能（中间变量屏蔽、目标结果、同类项合并）
- 公式渲染规则（LaTeX 输出、多字符下标）
- 界面与文件完整性
- Flask API 集成
- 补充约束
- 桌面应用包装
- 希腊字母变量

---

### 技术栈

- **后端**：Python 3 + Flask + SymPy（符号计算）
- **前端**：HTML + CSS + JavaScript + KaTeX
- **桌面包装**：pywebview + waitress（生产级 WSGI 服务器）
- **启动器**：C# 编译的原生 exe（自动环境检测与设置）

---

### 许可证

本项目采用 MIT 许可证。
