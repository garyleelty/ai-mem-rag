import { api } from '../api.js';
import { state } from '../state.js';
import { showToast } from '../utils.js';

export function render() {
    return `
        <div class="max-w-2xl mx-auto">
            <h2 class="text-2xl font-bold text-surface-800 mb-6">⭐ 偏好设置</h2>
            <form id="preferenceForm" class="bg-white rounded-2xl border border-surface-200/80 shadow-card p-8 space-y-6">
                <div class="space-y-1.5">
                    <label class="text-sm font-medium text-surface-800">回答风格</label>
                    <select id="prefStyle" class="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all">
                        <option value="balanced">平衡</option>
                        <option value="concise">简洁</option>
                        <option value="detailed">详细</option>
                        <option value="technical">技术</option>
                    </select>
                </div>
                <div class="space-y-1.5">
                    <label class="text-sm font-medium text-surface-800">首选语言</label>
                    <input type="text" id="prefLanguage" value="zh" placeholder="如: zh, en" class="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all">
                </div>
                <div class="space-y-1.5">
                    <label class="text-sm font-medium text-surface-800">兴趣领域</label>
                    <input type="text" id="prefDomains" placeholder="如: 编程, 设计, 数据库（逗号分隔）" class="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all">
                </div>
                <div class="space-y-1.5">
                    <label class="text-sm font-medium text-surface-800">自定义系统提示词</label>
                    <textarea id="prefPrompt" rows="4" placeholder="输入自定义提示词..." class="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all resize-y"></textarea>
                </div>
                <div class="flex items-center gap-3">
                    <div class="relative">
                        <input type="checkbox" id="prefAutoSummary" class="sr-only peer">
                        <label for="prefAutoSummary" class="w-11 h-6 bg-surface-200 rounded-full peer-checked:bg-brand-500 cursor-pointer transition-all after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-5 after:h-5 after:bg-white after:rounded-full after:shadow-sm after:transition-all peer-checked:after:translate-x-5"></label>
                    </div>
                    <span class="text-sm font-medium text-surface-800">自动总结</span>
                </div>
                <div class="pt-2">
                    <button type="submit" class="w-full py-3 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">保存偏好</button>
                </div>
            </form>
        </div>
    `;
}

export async function init() {
    if (!state.token) {
        document.querySelector('.max-w-2xl').innerHTML = `
            <div class="text-center py-16">
                <div class="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-surface-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <p class="text-surface-500 mb-3">请先登录后设置偏好</p>
                <button id="prefLoginBtn" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all">去登录</button>
            </div>`;
        document.getElementById('prefLoginBtn')?.addEventListener('click', () => {
            document.getElementById('loginBtn').click();
        });
        return;
    }
    try {
        const data = await api('/preferences');
        document.getElementById('prefStyle').value = data.preferred_style || 'balanced';
        document.getElementById('prefLanguage').value = data.preferred_language || 'zh';
        if (data.domain_interests) {
            try {
                const domains = JSON.parse(data.domain_interests);
                document.getElementById('prefDomains').value = domains.join(', ');
            } catch (e) {}
        }
        document.getElementById('prefPrompt').value = data.custom_prompt || '';
        document.getElementById('prefAutoSummary').checked = data.auto_summary || false;
    } catch (e) {
        console.error('加载偏好失败:', e);
    }

    document.getElementById('preferenceForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const body = {
            preferred_style: document.getElementById('prefStyle').value,
            preferred_language: document.getElementById('prefLanguage').value,
            domain_interests: document.getElementById('prefDomains').value.split(',').map(s => s.trim()).filter(Boolean),
            custom_prompt: document.getElementById('prefPrompt').value,
            auto_summary: document.getElementById('prefAutoSummary').checked,
        };
        try {
            await api('/preferences', { method: 'PUT', body });
            alert('偏好已保存');
        } catch (e) { alert('保存失败: ' + e.message); }
    });
}
