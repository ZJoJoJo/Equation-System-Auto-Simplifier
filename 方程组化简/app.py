"""
方程组自动化简软件 - Flask 后端 + pywebview 桌面入口
运行方式：
  python app.py          # 启动桌面窗口（默认）
  python app.py --web    # 仅在浏览器中运行（http://127.0.0.1:5000）
"""

import sys
import os
import threading
import webbrowser

from flask import Flask, render_template, request, jsonify

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.engine import (
    simplify_system,
    identify_variables_from_text,
    render_equation_latex,
    fix_latex_subscripts
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_AS_ASCII'] = False


# ---------------------------------------------------------------------------
# 页面路由
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


# ---------------------------------------------------------------------------
# API 路由
# ---------------------------------------------------------------------------

@app.route('/api/identify', methods=['POST'])
def api_identify():
    """识别方程组中的所有变量。"""
    data = request.get_json(force=True)
    text = data.get('equations', '')
    try:
        variables = identify_variables_from_text(text)
        return jsonify({
            'success': True,
            'variables': variables
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/preview', methods=['POST'])
def api_preview():
    """实时渲染单个方程/表达式的 LaTeX（用于输入区实时预览）。"""
    data = request.get_json(force=True)
    lines = data.get('lines', [])
    try:
        rendered = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                rendered.append('')
                continue
            latex_str = render_equation_latex(line)
            rendered.append(latex_str)
        return jsonify({
            'success': True,
            'latex_list': rendered
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/simplify', methods=['POST'])
def api_simplify():
    """核心化简接口。"""
    data = request.get_json(force=True)
    equations_text = data.get('equations', '')
    intermediate_vars = data.get('intermediate_vars', []) or []
    target_expressions = data.get('target_expressions', []) or []
    merge_vars = data.get('merge_vars', []) or []

    # 清理空字符串
    intermediate_vars = [v.strip() for v in intermediate_vars if v.strip()]
    target_expressions = [t.strip() for t in target_expressions if t.strip()]
    merge_vars = [v.strip() for v in merge_vars if v.strip()]

    try:
        result = simplify_system(
            equations_text=equations_text,
            intermediate_vars=intermediate_vars,
            target_expressions=target_expressions,
            merge_vars=merge_vars
        )
        # 修复结果中的下标渲染
        for r in result['results']:
            r['latex'] = fix_latex_subscripts(r['latex'])
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ---------------------------------------------------------------------------
# 启动逻辑
# ---------------------------------------------------------------------------

def run_web():
    """在浏览器中运行（开发/备用模式）。"""
    port = 5000
    url = f'http://127.0.0.1:{port}'
    print(f'方程组自动化简软件已启动: {url}')
    print('按 Ctrl+C 停止服务')
    webbrowser.open(url)
    app.run(host='127.0.0.1', port=port, debug=False)


def run_desktop():
    """以桌面窗口模式运行（pywebview）。"""
    import time
    import urllib.request

    print('[1/4] 正在导入桌面窗口组件...')
    try:
        import webview
    except Exception as e:
        print(f'  失败：pywebview 导入失败 - {e}')
        raise

    port = 5000
    url = f'http://127.0.0.1:{port}'

    print('[2/4] 正在启动本地服务器...')

    # 在后台线程启动 Flask
    server_error = []

    def start_server():
        try:
            from waitress import serve
            serve(app, host='127.0.0.1', port=port, threads=8)
        except Exception as e:
            server_error.append(str(e))

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪（最多等5秒）
    server_ready = False
    for i in range(50):
        if server_error:
            print(f'  失败：服务器启动错误 - {server_error[0]}')
            raise RuntimeError(f'服务器启动失败: {server_error[0]}')
        try:
            req = urllib.request.Request(url, method='HEAD')
            urllib.request.urlopen(req, timeout=1)
            server_ready = True
            break
        except Exception:
            time.sleep(0.1)

    if not server_ready:
        print('  失败：服务器在5秒内未响应')
        raise RuntimeError('本地服务器启动超时')

    print('  服务器已就绪')

    print('[3/4] 正在创建桌面窗口...')
    try:
        window = webview.create_window(
            '方程组自动化简软件',
            url,
            width=1280,
            height=800,
            min_size=(900, 600),
            resizable=True,
            text_select=True
        )
    except Exception as e:
        print(f'  失败：窗口创建失败 - {e}')
        raise

    print('[4/4] 窗口已启动，正在加载界面...')
    print('  （关闭窗口即可退出程序）')
    print()

    try:
        webview.start(debug=False)
    except Exception as e:
        print(f'窗口运行错误: {e}')
        raise


if __name__ == '__main__':
    if '--web' in sys.argv:
        run_web()
    else:
        print('=' * 50)
        print('  方程组自动化简软件 - 桌面模式')
        print('=' * 50)
        print()
        try:
            run_desktop()
        except Exception as e:
            print()
            print('!' * 50)
            print(f'  桌面模式启动失败: {e}')
            print('  正在自动回退到浏览器模式...')
            print('!' * 50)
            print()
            try:
                run_web()
            except Exception as e2:
                print(f'浏览器模式也失败了: {e2}')
                print()
                input('按回车键退出...')
