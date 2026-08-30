/* ============================================
   方程组自动化简软件 - 前端逻辑
   ============================================ */

(function () {
    'use strict';

    // ---------- DOM 元素 ----------
    const equationsInput = document.getElementById('equations-input');
    const intermediateVarsInput = document.getElementById('intermediate-vars');
    const targetExprsInput = document.getElementById('target-exprs');
    const mergeVarsInput = document.getElementById('merge-vars');
    const simplifyBtn = document.getElementById('simplify-btn');
    const clearBtn = document.getElementById('clear-btn');
    const exampleBtn = document.getElementById('example-btn');
    const previewArea = document.getElementById('preview-area');
    const resultArea = document.getElementById('result-area');
    const stepsPanel = document.getElementById('steps-panel');
    const stepsArea = document.getElementById('steps-area');
    const statusText = document.getElementById('status-text');
    const varCount = document.getElementById('var-count');
    const eqCount = document.getElementById('eq-count');

    // ---------- 状态 ----------
    let previewTimer = null;
    let identifyTimer = null;

    // ---------- 工具函数 ----------

    /** 用 KaTeX 渲染 LaTeX 字符串为 HTML */
    function renderLatex(latexStr, displayMode) {
        try {
            return katex.renderToString(latexStr, {
                throwOnError: false,
                displayMode: displayMode || false,
                strict: false
            });
        } catch (e) {
            return '<span style="color:red;">渲染错误: ' + escapeHtml(latexStr) + '</span>';
        }
    }

    /** HTML 转义 */
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /** 解析逗号分隔的输入为数组 */
    function parseCsvInput(str) {
        if (!str || !str.trim()) return [];
        return str.split(/[,，]/).map(s => s.trim()).filter(s => s.length > 0);
    }

    /** 设置状态栏文本 */
    function setStatus(text, isError) {
        statusText.textContent = text;
        statusText.style.color = isError ? 'var(--error)' : 'var(--text-hint)';
    }

    /** 显示错误信息 */
    function showError(container, message) {
        container.innerHTML = '<div class="error-message">' + escapeHtml(message) + '</div>';
    }

    // ---------- 实时预览 ----------

    function updatePreview() {
        const text = equationsInput.value;
        const lines = text.split('\n').filter(l => l.trim());

        if (lines.length === 0) {
            previewArea.innerHTML = '<p class="placeholder-text">输入公式后此处实时渲染</p>';
            eqCount.textContent = '方程：0';
            return;
        }

        eqCount.textContent = '方程：' + lines.length;

        // 调用后端预览接口（通过 SymPy 解析生成正确 LaTeX，确保下标完整）
        fetch('/api/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lines: lines })
        })
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    // 解析错误时显示原始文本
                    previewArea.innerHTML = lines.map((l, i) =>
                        '<div class="preview-line"><code>' + escapeHtml(l) + '</code></div>'
                    ).join('');
                    return;
                }
                previewArea.innerHTML = data.latex_list.map((latex, i) => {
                    if (!latex) return '';
                    return '<div class="preview-line">' +
                        renderLatex(latex, true) + '</div>';
                }).join('');
            })
            .catch(() => {
                // 网络错误时显示原始文本
                previewArea.innerHTML = lines.map(l =>
                    '<div class="preview-line"><code>' + escapeHtml(l) + '</code></div>'
                ).join('');
            });
    }

    // ---------- 变量识别 ----------

    function updateVariables() {
        const text = equationsInput.value.trim();
        if (!text) {
            varCount.textContent = '变量：-';
            return;
        }

        fetch('/api/identify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ equations: text })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    varCount.textContent = '变量：' + data.variables.length + ' 个';
                    varCount.title = data.variables.join(', ');
                } else {
                    varCount.textContent = '变量：-';
                }
            })
            .catch(() => {
                varCount.textContent = '变量：-';
            });
    }

    // ---------- 核心化简 ----------

    function doSimplify() {
        const equations = equationsInput.value.trim();
        if (!equations) {
            setStatus('请先输入方程组', true);
            showError(resultArea, '请先在左侧输入方程组。');
            return;
        }

        const intermediateVars = parseCsvInput(intermediateVarsInput.value);
        const targetExprs = parseCsvInput(targetExprsInput.value);
        const mergeVars = parseCsvInput(mergeVarsInput.value);

        setStatus('正在化简...');
        simplifyBtn.disabled = true;
        resultArea.innerHTML = '<p class="placeholder-text">正在计算，请稍候...</p>';

        fetch('/api/simplify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                equations: equations,
                intermediate_vars: intermediateVars,
                target_expressions: targetExprs,
                merge_vars: mergeVars
            })
        })
            .then(res => res.json())
            .then(data => {
                simplifyBtn.disabled = false;
                if (!data.success) {
                    setStatus('化简失败', true);
                    showError(resultArea, data.error || '未知错误');
                    stepsPanel.style.display = 'none';
                    return;
                }
                setStatus('化简完成');
                renderResult(data.data);
            })
            .catch(err => {
                simplifyBtn.disabled = false;
                setStatus('网络错误', true);
                showError(resultArea, '请求失败：' + err.message);
            });
    }

    // ---------- 渲染结果 ----------

    function renderResult(data) {
        // 变量标签
        let varTagsHtml = '';
        if (data.all_variables && data.all_variables.length > 0) {
            varTagsHtml = '<div class="var-tags">';
            data.all_variables.forEach(v => {
                let cls = 'var-tag';
                if (data.intermediate_vars.includes(v)) cls += ' intermediate';
                varTagsHtml += '<span class="' + cls + '">' + escapeHtml(v) + '</span>';
            });
            varTagsHtml += '</div>';
        }

        // 结果项
        let resultsHtml = '';
        if (data.results && data.results.length > 0) {
            data.results.forEach(r => {
                resultsHtml += '<div class="result-item">';
                resultsHtml += '<div class="result-target">' + escapeHtml(r.target) + ' =</div>';
                resultsHtml += '<div class="result-expr">' + renderLatex(r.latex, true) + '</div>';
                resultsHtml += '</div>';
            });
        } else {
            resultsHtml = '<p class="placeholder-text">无结果输出</p>';
        }

        resultArea.innerHTML = varTagsHtml + resultsHtml;

        // 化简步骤
        if (data.steps && data.steps.length > 0) {
            stepsPanel.style.display = 'block';
            stepsArea.innerHTML = data.steps.map(s =>
                '<div class="step-item">' + escapeHtml(s) + '</div>'
            ).join('');
        } else {
            stepsPanel.style.display = 'none';
        }
    }

    // ---------- 清空 ----------

    function doClear() {
        equationsInput.value = '';
        intermediateVarsInput.value = '';
        targetExprsInput.value = '';
        mergeVarsInput.value = '';
        previewArea.innerHTML = '<p class="placeholder-text">输入公式后此处实时渲染</p>';
        resultArea.innerHTML = '<p class="placeholder-text">点击「化简」按钮查看结果</p>';
        stepsPanel.style.display = 'none';
        varCount.textContent = '变量：-';
        eqCount.textContent = '方程：0';
        setStatus('已清空');
    }

    // ---------- 加载示例 ----------

    function loadExample() {
        equationsInput.value =
            'v_1 = I_1 * R_1\n' +
            'v_2 = I_2 * R_2\n' +
            'I_1 = I_2\n' +
            'v_1 + v_2 = V_total';
        intermediateVarsInput.value = 'I_1, I_2';
        targetExprsInput.value = 'v_1, v_2, v_1/v_2';
        mergeVarsInput.value = '';
        setStatus('已加载示例，点击「化简」查看结果');
        // 触发预览和变量识别
        triggerDebouncedUpdate();
    }

    // ---------- 防抖更新 ----------

    function triggerDebouncedUpdate() {
        if (previewTimer) clearTimeout(previewTimer);
        if (identifyTimer) clearTimeout(identifyTimer);
        previewTimer = setTimeout(updatePreview, 300);
        identifyTimer = setTimeout(updateVariables, 300);
    }

    // ---------- 事件绑定 ----------

    equationsInput.addEventListener('input', triggerDebouncedUpdate);
    simplifyBtn.addEventListener('click', doSimplify);
    clearBtn.addEventListener('click', doClear);
    exampleBtn.addEventListener('click', loadExample);

    // 支持 Ctrl+Enter 快捷化简
    equationsInput.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            doSimplify();
        }
    });

    // 输入帮助面板折叠/展开
    const helpToggle = document.getElementById('help-toggle');
    const helpContent = document.getElementById('help-content');
    if (helpToggle && helpContent) {
        helpToggle.addEventListener('click', function () {
            if (helpContent.style.display === 'none') {
                helpContent.style.display = 'block';
                helpToggle.textContent = '输入帮助 ▴';
            } else {
                helpContent.style.display = 'none';
                helpToggle.textContent = '输入帮助 ▾';
            }
        });
    }

    // ---------- 初始化 ----------
    setStatus('就绪');

})();
