import { api, cachedApi } from '../api.js';
import { state, setState } from '../state.js';
import { escapeHtml, formatDate, showToast, customPrompt } from '../utils.js';

export function render() {
    return `
        <div class="grid grid-cols-[280px_1fr] gap-6 min-h-[calc(100vh-112px)]">
            <aside class="bg-white rounded-2xl border border-surface-200/80 shadow-card flex flex-col overflow-hidden">
                <div class="p-4 border-b border-surface-100 flex items-center justify-between">
                    <h4 class="text-sm font-semibold text-surface-800">💬 会话列表</h4>
                    <button id="newConvBtn" class="w-8 h-8 rounded-lg border border-surface-200 flex items-center justify-center text-surface-500 hover:text-brand-500 hover:border-brand-300 hover:bg-brand-50 transition-all">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    </button>
                </div>
                <div id="conversationList" class="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
                    <div class="text-sm text-surface-400 text-center py-8">加载中...</div>
                </div>
            </aside>
            <section class="flex flex-col gap-5">
                <div class="flex gap-3 items-center">
                    <div class="flex-1 relative">
                        <svg class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                        <input type="text" id="qaSearchInput" placeholder="搜索问答记录..." class="w-full pl-10 pr-4 py-2.5 rounded-xl border border-surface-200 bg-white text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all">
                    </div>
                    <button id="qaSearchBtn" class="px-4 py-2.5 rounded-xl border border-surface-200 bg-white text-sm font-medium text-surface-600 hover:border-brand-300 hover:text-brand-600 hover:bg-brand-50 transition-all">搜索</button>
                    <button id="qaSemanticSearchBtn" class="px-4 py-2.5 rounded-xl border border-surface-200 bg-white text-sm font-medium text-surface-600 hover:border-brand-300 hover:text-brand-600 hover:bg-brand-50 transition-all">语义搜索</button>
                    <button id="newQABtn" class="px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">+ 新建问答</button>
                </div>
                <div id="qaRecordList" class="space-y-4">
                    <div class="text-sm text-surface-400 text-center py-12">选择会话或搜索问答记录</div>
                </div>
            </section>
        </div>
    `;
}

export async function init() {
    if (!state.token) {
        document.getElementById('qaRecordList').innerHTML = `
            <div class="text-center py-16">
                <div class="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-surface-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <p class="text-surface-500 mb-3">请先登录后查看问答记录</p>
                <button id="qaLoginBtn" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all">去登录</button>
            </div>`;
        document.getElementById('qaLoginBtn')?.addEventListener('click', () => {
            document.getElementById('loginBtn').click();
        });
        return;
    }
    await loadConversations();
    await loadQARecords();

    document.getElementById('newConvBtn')?.addEventListener('click', async () => {
        const title = await customPrompt('输入会话标题');
        if (!title) return;
        await api('/conversations', { method: 'POST', body: { title } });
        await loadConversations();
    });

    document.getElementById('newQABtn')?.addEventListener('click', async () => {
        const question = await customPrompt('输入问题');
        if (!question) return;
        const answer = await customPrompt('输入回答');
        if (!answer) return;
        api('/qa/records', {
            method: 'POST',
            body: { question, answer, conversation_id: state.selectedConversation || undefined },
        }).then(() => loadQARecords());
    });

    document.getElementById('qaSearchBtn')?.addEventListener('click', async () => {
        const keyword = document.getElementById('qaSearchInput').value;
        await loadQARecords(keyword);
    });

    document.getElementById('qaSemanticSearchBtn')?.addEventListener('click', async () => {
        const query = document.getElementById('qaSearchInput').value;
        if (!query) return;
        try {
            const data = await api('/qa/search', { method: 'POST', body: { query, top_k: 10 } });
            renderQASearchResults(data.results);
        } catch (e) {
            showToast('语义搜索失败: ' + e.message, 'error');
        }
    });
}

async function loadConversations() {
    try {
        const data = await cachedApi('/conversations');
        setState('conversations', data);
        const list = document.getElementById('conversationList');
        if (!data.length) {
            list.innerHTML = '<div class="text-sm text-surface-400 text-center py-8">暂无会话</div>';
            return;
        }
        list.innerHTML = data.map(c => `
            <div class="p-3 rounded-xl ${state.selectedConversation === c.id ? 'bg-brand-50 border border-brand-200/60' : 'hover:bg-surface-50 cursor-pointer'} transition-all" data-id="${c.id}">
                <div class="font-medium text-sm ${state.selectedConversation === c.id ? 'text-brand-700' : 'text-surface-800'}">${escapeHtml(c.title || '未命名会话')}</div>
                <div class="text-xs text-surface-400 mt-1">${formatDate(c.updated_at)}</div>
            </div>
        `).join('');
        list.querySelectorAll('[data-id]').forEach(item => {
            item.addEventListener('click', () => {
                setState('selectedConversation', parseInt(item.dataset.id));
                loadConversations();
                loadQARecords();
            });
        });
    } catch (e) {
        console.error('加载会话失败:', e);
    }
}

async function loadQARecords(keyword = '') {
    try {
        let url = '/qa/records?page=1&page_size=50';
        if (state.selectedConversation) url += `&conversation_id=${state.selectedConversation}`;
        if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
        const data = await api(url);
        setState('qaRecords', data.items);
        renderQARecords(data.items);
    } catch (e) {
        console.error('加载问答记录失败:', e);
    }
}

function renderQARecords(records) {
    const list = document.getElementById('qaRecordList');
    if (!records || !records.length) {
        list.innerHTML = `
            <div class="text-center py-16">
                <div class="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-surface-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                </div>
                <p class="text-surface-500">暂无问答记录</p>
            </div>`;
        return;
    }
    list.innerHTML = records.map(r => `
        <div class="group bg-white rounded-2xl border border-surface-200/80 shadow-card hover:shadow-float hover:-translate-y-0.5 transition-all duration-200 overflow-hidden cursor-pointer" data-id="${r.id}">
            <div class="flex">
                <div class="w-1 bg-gradient-to-b from-brand-400 to-brand-600 rounded-l-2xl"></div>
                <div class="flex-1 p-5">
                    <div class="flex items-start justify-between gap-4">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-brand-50 text-brand-600 text-xs font-semibold">Q</span>
                                <h3 class="font-semibold text-surface-800">${escapeHtml(r.question)}</h3>
                            </div>
                            <div class="flex items-start gap-2">
                                <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 text-xs font-semibold shrink-0">A</span>
                                <p class="text-sm text-surface-500 leading-relaxed line-clamp-2">${escapeHtml(r.answer.substring(0, 200))}${r.answer.length > 200 ? '...' : ''}</p>
                            </div>
                        </div>
                        <div class="flex flex-col items-end gap-2 shrink-0">
                            ${r.model_name ? `<span class="px-2.5 py-1 rounded-lg bg-surface-50 text-xs font-medium text-surface-500">🤖 ${r.model_name}</span>` : ''}
                            <span class="text-xs text-surface-400">${formatDate(r.created_at)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    list.querySelectorAll('[data-id]').forEach(card => {
        card.addEventListener('click', () => showQADetail(parseInt(card.dataset.id)));
    });
}

function renderQASearchResults(results) {
    const list = document.getElementById('qaRecordList');
    if (!results || !results.length) {
        list.innerHTML = '<div class="text-center py-16 text-surface-400">未找到相似记录</div>';
        return;
    }
    list.innerHTML = results.map(r => `
        <div class="group bg-white rounded-2xl border border-brand-200 shadow-card hover:shadow-float hover:-translate-y-0.5 transition-all duration-200 overflow-hidden cursor-pointer" data-id="${r.qa_record_id}">
            <div class="flex">
                <div class="w-1 bg-gradient-to-b from-violet-400 to-purple-600 rounded-l-2xl"></div>
                <div class="flex-1 p-5">
                    <div class="flex items-center gap-2 mb-3">
                        <span class="px-2.5 py-1 rounded-full bg-brand-50 text-brand-600 text-xs font-bold">语义匹配 ${(r.similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="flex items-center gap-2 mb-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-brand-50 text-brand-600 text-xs font-semibold">Q</span>
                        <h3 class="font-semibold text-surface-800">${escapeHtml(r.question)}</h3>
                    </div>
                    <div class="flex items-start gap-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-600 text-xs font-semibold shrink-0">A</span>
                        <p class="text-sm text-surface-500 leading-relaxed line-clamp-2">${escapeHtml(r.answer.substring(0, 200))}${r.answer.length > 200 ? '...' : ''}</p>
                    </div>
                    <div class="text-xs text-surface-400 mt-2">${formatDate(r.created_at)}</div>
                </div>
            </div>
        </div>
    `).join('');
    list.querySelectorAll('[data-id]').forEach(card => {
        card.addEventListener('click', () => showQADetail(parseInt(card.dataset.id)));
    });
}

async function showQADetail(qaId) {
    try {
        const record = await api(`/qa/records/${qaId}`);
        const feedback = await api(`/qa/records/${qaId}/feedback`).catch(() => null);
        const modal = document.getElementById('qaDetailModal');
        const content = document.getElementById('qaDetailContent');

        content.innerHTML = `
            <div class="space-y-5">
                <div>
                    <div class="text-xs font-semibold text-brand-600 uppercase tracking-wider mb-2">问题</div>
                    <p class="text-surface-800 leading-relaxed">${escapeHtml(record.question)}</p>
                </div>
                <div>
                    <div class="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-2">回答</div>
                    <p class="text-surface-600 leading-relaxed whitespace-pre-wrap">${escapeHtml(record.answer)}</p>
                </div>
                <div class="flex gap-4 text-xs text-surface-400 py-3 border-t border-b border-surface-100">
                    ${record.model_name ? `<span>🤖 ${record.model_name}</span>` : ''}
                    <span>${formatDate(record.created_at)}</span>
                    ${record.temperature ? `<span>🌡️ ${record.temperature}</span>` : ''}
                    ${record.tokens_used ? `<span>📊 ${record.tokens_used} tokens</span>` : ''}
                </div>
                <div>
                    <div class="text-sm font-semibold text-surface-800 mb-3">反馈</div>
                    <div class="flex gap-2 mb-4">
                        <button class="feedback-btn px-4 py-2 rounded-xl border ${feedback?.feedback_type === 'thumbs_up' ? 'border-brand-300 bg-brand-50 shadow-sm' : 'border-surface-200 bg-white hover:border-brand-300 hover:bg-brand-50'} text-lg transition-all" data-type="thumbs_up">👍</button>
                        <button class="feedback-btn px-4 py-2 rounded-xl border ${feedback?.feedback_type === 'thumbs_down' ? 'border-brand-300 bg-brand-50 shadow-sm' : 'border-surface-200 bg-white hover:border-brand-300 hover:bg-brand-50'} text-lg transition-all" data-type="thumbs_down">👎</button>
                        <button class="feedback-btn px-4 py-2 rounded-xl border ${feedback?.feedback_type === 'modified' ? 'border-brand-300 bg-brand-50 shadow-sm' : 'border-surface-200 bg-white hover:border-brand-300 hover:bg-brand-50'} text-lg transition-all" data-type="modified">✏️</button>
                    </div>
                    <div class="flex flex-wrap gap-2 mb-4">
                        ${state.presetTags.map(t => `
                            <label class="cursor-pointer">
                                <input type="checkbox" value="${t.name}" class="sr-only peer" ${feedback?.preset_tags?.includes(t.name) ? 'checked' : ''}>
                                <span class="inline-block px-3 py-1 rounded-full text-xs font-medium border transition-all peer-checked:ring-2" style="background:${t.color}15;color:${t.color};border-color:${t.color}40;--tw-ring-color:${t.color}">${t.label}</span>
                            </label>
                        `).join('')}
                    </div>
                    <textarea id="feedbackComment" placeholder="备注..." class="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all resize-y mb-3" rows="2">${feedback?.comment || ''}</textarea>
                    <button id="submitFeedbackBtn" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all">提交反馈</button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
        modal.classList.add('flex');

        document.getElementById('submitFeedbackBtn')?.addEventListener('click', async () => {
            const feedbackType = content.querySelector('.feedback-btn.border-brand-300')?.dataset.type;
            const presetTags = Array.from(content.querySelectorAll('input[type=checkbox]:checked')).map(cb => cb.value);
            const comment = document.getElementById('feedbackComment').value;
            try {
                if (feedback) {
                    await api(`/qa/records/${qaId}/feedback`, { method: 'PUT', body: { feedback_type: feedbackType, preset_tags, comment } });
                } else {
                    await api(`/qa/records/${qaId}/feedback`, { method: 'POST', body: { feedback_type: feedbackType || 'thumbs_up', preset_tags, comment } });
                }
                showToast('反馈已提交', 'success');
                closeQADetailModal();
                loadQARecords();
            } catch (e) {
                showToast('提交失败: ' + e.message, 'error');
            }
        });

        content.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                content.querySelectorAll('.feedback-btn').forEach(b => {
                    b.classList.remove('border-brand-300', 'bg-brand-50', 'shadow-sm');
                    b.classList.add('border-surface-200', 'bg-white');
                });
                btn.classList.remove('border-surface-200', 'bg-white');
                btn.classList.add('border-brand-300', 'bg-brand-50', 'shadow-sm');
            });
        });
    } catch (e) {
        showToast('加载详情失败: ' + e.message, 'error');
    }
}

function closeQADetailModal() {
    const m = document.getElementById('qaDetailModal');
    m.classList.add('hidden');
    m.classList.remove('flex');
}

export function setupQADetailClose() {
    document.getElementById('closeQADetail')?.addEventListener('click', closeQADetailModal);
    document.getElementById('qaDetailBackdrop')?.addEventListener('click', closeQADetailModal);
}
