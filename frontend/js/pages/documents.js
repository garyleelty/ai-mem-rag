import { api, apiForm, invalidateCache } from '../api.js';
import { state, setState } from '../state.js';
import { escapeHtml, formatDate, setConnectionStatus, showToast, customConfirm } from '../utils.js';

export function render() {
    return `
        <div class="grid grid-cols-[260px_1fr_300px] gap-0 min-h-[calc(100vh-112px)] bg-white rounded-2xl border border-surface-200/80 shadow-card overflow-hidden">
            <aside class="bg-surface-50 border-r border-surface-200/60 p-5 flex flex-col gap-6">
                <div class="space-y-3">
                    <h4 class="text-xs font-semibold text-surface-500 uppercase tracking-wider">📁 集合管理</h4>
                    <div class="space-y-1.5">
                        <label class="text-xs font-medium text-surface-500">目标集合</label>
                        <select id="collectionSelect" class="w-full px-3 py-2 rounded-lg border border-surface-200 bg-white text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all">
                            <option value="">请选择集合</option>
                        </select>
                    </div>
                    <div class="space-y-1.5">
                        <label class="text-xs font-medium text-surface-500">新建集合</label>
                        <div class="flex gap-2">
                            <input type="text" id="newCollectionName" placeholder="输入名称..." class="flex-1 px-3 py-2 rounded-lg border border-surface-200 bg-white text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all">
                            <button id="createCollectionBtn" class="w-9 h-9 rounded-lg border border-surface-200 flex items-center justify-center text-surface-500 hover:text-brand-500 hover:border-brand-300 hover:bg-brand-50 transition-all">
                                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="h-px bg-surface-200"></div>
                <div class="space-y-3">
                    <h4 class="text-xs font-semibold text-surface-500 uppercase tracking-wider">📤 上传配置</h4>
                    <div class="space-y-1.5">
                        <label class="text-xs font-medium text-surface-500">分块大小</label>
                        <div class="flex bg-surface-100 rounded-lg p-1 gap-1">
                            <button class="chunk-seg flex-1 py-1.5 rounded-md text-xs font-medium text-surface-500 hover:text-surface-800 transition-all" data-value="500">500</button>
                            <button class="chunk-seg flex-1 py-1.5 rounded-md text-xs font-medium bg-white text-brand-600 shadow-sm" data-value="1000">1000</button>
                            <button class="chunk-seg flex-1 py-1.5 rounded-md text-xs font-medium text-surface-500 hover:text-surface-800 transition-all" data-value="2000">2000</button>
                        </div>
                        <input type="hidden" id="chunkSize" value="1000">
                    </div>
                    <button id="uploadBtn" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        上传文件
                    </button>
                    <input type="file" id="fileInput" multiple accept=".pdf,.docx" class="hidden">
                </div>
            </aside>
            <section class="p-6 flex flex-col gap-5">
                <div id="dropZone" class="border-2 border-dashed border-surface-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center hover:border-brand-400 hover:bg-brand-50/30 transition-all duration-200 cursor-pointer min-h-[260px]">
                    <div id="uploadPlaceholder" class="flex flex-col items-center gap-3">
                        <div class="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center">
                            <svg class="w-8 h-8 text-brand-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        </div>
                        <h3 class="text-base font-semibold text-surface-800">拖拽文件到此处上传</h3>
                        <p class="text-sm text-surface-400">支持 PDF、DOCX 格式 · 单文件最大 20MB</p>
                        <button class="px-5 py-2 rounded-xl border border-surface-200 bg-white text-sm font-medium text-surface-600 hover:border-brand-300 hover:text-brand-600 hover:bg-brand-50 transition-all" onclick="document.getElementById('fileInput').click()">选择文件</button>
                    </div>
                    <div id="uploadStatus" class="hidden flex-col items-center gap-3">
                        <div class="w-12 h-12 rounded-full border-4 border-brand-100 border-t-brand-500 animate-spin"></div>
                        <span id="uploadStatusText" class="text-sm text-surface-600">正在处理...</span>
                    </div>
                </div>
                <div id="previewPanel" class="hidden bg-white rounded-2xl border border-surface-200/80 overflow-hidden">
                    <div class="flex items-center justify-between px-5 py-3 bg-surface-50 border-b border-surface-200/60">
                        <h4 id="previewHeader" class="text-sm font-semibold text-surface-800">文档预览</h4>
                        <button id="closePreview" class="w-8 h-8 rounded-lg hover:bg-surface-100 flex items-center justify-center text-surface-400 hover:text-surface-600 transition-all">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                    <div id="previewContent" class="p-4 space-y-3 max-h-[500px] overflow-y-auto scrollbar-thin"></div>
                </div>
            </section>
            <aside class="bg-surface-50 border-l border-surface-200/60 flex flex-col">
                <div class="p-5 border-b border-surface-200/60">
                    <h4 class="text-sm font-semibold text-surface-800 mb-3">📚 文档列表</h4>
                    <select id="docCollectionSelect" class="w-full px-3 py-2 rounded-lg border border-surface-200 bg-white text-sm focus:outline-none focus:border-brand-400 transition-all">
                        <option value="">选择集合</option>
                    </select>
                </div>
                <div id="documentList" class="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-2">
                    <div class="text-center py-12">
                        <svg class="w-10 h-10 text-surface-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        <p class="text-sm text-surface-400">暂无文档</p>
                        <span class="text-xs text-surface-300">选择集合并上传文件</span>
                    </div>
                </div>
                <div id="docCount" class="px-5 py-3 border-t border-surface-200/60 text-xs text-surface-400 text-center"></div>
            </aside>
        </div>
    `;
}

export async function init() {
    await loadCollections();
    initDocumentEvents();
}

async function loadCollections() {
    try {
        const data = await api('/collections');
        setState('collections', data.collections || []);
        setConnectionStatus('connected', '已连接');
        renderCollectionSelects();
    } catch (e) {
        console.error('加载集合失败:', e);
        setConnectionStatus('error', '连接失败');
    }
}

function renderCollectionSelects() {
    const options = ['<option value="">请选择集合</option>'];
    state.collections.forEach(c => {
        options.push(`<option value="${c.name}">${c.name} (${c.count})</option>`);
    });
    const html = options.join('');
    const c1 = document.getElementById('collectionSelect');
    const c2 = document.getElementById('docCollectionSelect');
    if (c1) c1.innerHTML = html;
    if (c2) c2.innerHTML = html;
    if (state.selectedCollection) {
        if (c1) c1.value = state.selectedCollection;
        if (c2) c2.value = state.selectedCollection;
    }
}

function initDocumentEvents() {
    document.getElementById('createCollectionBtn')?.addEventListener('click', async () => {
        const name = document.getElementById('newCollectionName').value.trim();
        if (!name) { showToast('请输入集合名称', 'warning'); return; }
        try {
            await api('/collections', { method: 'POST', body: { name } });
            document.getElementById('newCollectionName').value = '';
            invalidateCache('/collections');
            await loadCollections();
        } catch (e) { showToast('创建失败: ' + e.message, 'error'); }
    });

    document.getElementById('uploadBtn')?.addEventListener('click', () => {
        document.getElementById('fileInput')?.click();
    });

    document.getElementById('fileInput')?.addEventListener('change', (e) => {
        if (e.target.files?.length) uploadFiles(e.target.files);
    });

    document.getElementById('docCollectionSelect')?.addEventListener('change', () => {
        setState('selectedCollection', document.getElementById('docCollectionSelect').value);
        loadDocuments();
    });

    document.getElementById('closePreview')?.addEventListener('click', closePreviewPanel);

    document.querySelectorAll('.chunk-seg').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chunk-seg').forEach(b => {
                b.classList.remove('bg-white', 'text-brand-600', 'shadow-sm');
                b.classList.add('text-surface-500');
            });
            btn.classList.remove('text-surface-500');
            btn.classList.add('bg-white', 'text-brand-600', 'shadow-sm');
            document.getElementById('chunkSize').value = btn.dataset.value;
        });
    });

    const dropZone = document.getElementById('dropZone');
    dropZone?.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('border-brand-400', 'bg-brand-50/30'); });
    dropZone?.addEventListener('dragleave', () => { dropZone.classList.remove('border-brand-400', 'bg-brand-50/30'); });
    dropZone?.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-brand-400', 'bg-brand-50/30');
        const files = Array.from(e.dataTransfer.files).filter(f => {
            const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
            return ext === '.pdf' || ext === '.docx';
        });
        if (files.length) uploadFiles(files);
        else showToast('仅支持 PDF 和 DOCX 文件', 'warning');
    });
}

async function loadDocuments() {
    const collection = document.getElementById('docCollectionSelect')?.value;
    if (!collection) {
        renderEmptyDocuments('选择集合并上传文件');
        return;
    }
    try {
        const data = await api(`/collections/${encodeURIComponent(collection)}/documents`);
        setState('documents', data.documents || []);
        renderDocuments();
    } catch (e) {
        renderEmptyDocuments('加载失败，请重试');
    }
}

function renderDocuments() {
    const list = document.getElementById('documentList');
    const count = document.getElementById('docCount');
    if (!state.documents.length) {
        renderEmptyDocuments('选择集合并上传文件');
        if (count) count.textContent = '';
        return;
    }
    list.innerHTML = state.documents.map(doc => `
        <div class="p-3 rounded-xl bg-white border ${doc.id === state.previewDocId ? 'border-brand-200 shadow-sm' : 'border-surface-200 hover:border-brand-300'} cursor-pointer transition-all" data-id="${doc.id}">
            <div class="font-medium text-sm text-surface-800 word-break-all">${escapeHtml(doc.source)}</div>
            <div class="text-xs text-surface-400 mt-1">${doc.chunk_count} 分块 · ${formatDate(doc.created_at)}</div>
            <div class="flex gap-2 mt-2 pt-2 border-t border-surface-100">
                <button class="view-btn px-2.5 py-1 rounded-md text-xs font-medium text-brand-600 bg-brand-50 hover:bg-brand-100 transition-all" data-id="${doc.id}">查看</button>
                <button class="delete-btn px-2.5 py-1 rounded-md text-xs font-medium text-red-500 bg-red-50 hover:bg-red-100 transition-all" data-id="${doc.id}">删除</button>
            </div>
        </div>
    `).join('');
    if (count) count.textContent = `共 ${state.documents.length} 个文档`;
    list.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); loadDocumentChunks(btn.dataset.id); });
    });
    list.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); deleteDocument(btn.dataset.id); });
    });
}

function renderEmptyDocuments(hint) {
    const list = document.getElementById('documentList');
    if (!list) return;
    list.innerHTML = `
        <div class="text-center py-12">
            <svg class="w-10 h-10 text-surface-300 mx-auto mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <p class="text-sm text-surface-400">暂无文档</p>
            <span class="text-xs text-surface-300">${hint}</span>
        </div>`;
}

async function loadDocumentChunks(docId) {
    setState('previewDocId', docId);
    renderDocuments();
    try {
        const data = await api(`/documents/${docId}/chunks`);
        const panel = document.getElementById('previewPanel');
        const header = document.getElementById('previewHeader');
        const content = document.getElementById('previewContent');
        if (panel) panel.classList.remove('hidden');
        if (header) header.textContent = `${data.document_name} · 共 ${data.chunks.length} 个分块`;
        if (content) content.innerHTML = data.chunks.map(chunk => `
            <div class="p-4 rounded-xl bg-surface-50 border-l-[3px] border-l-brand-500">
                <div class="text-xs font-semibold text-brand-600 mb-2">分块 ${chunk.index + 1}</div>
                <div class="text-sm text-surface-600 leading-relaxed whitespace-pre-wrap">${escapeHtml(chunk.content)}</div>
            </div>
        `).join('');
        panel?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) { showToast('加载文档内容失败: ' + e.message, 'error'); }
}

function closePreviewPanel() {
    setState('previewDocId', null);
    const panel = document.getElementById('previewPanel');
    if (panel) panel.classList.add('hidden');
    renderDocuments();
}

async function deleteDocument(docId) {
    if (!await customConfirm('确定要删除该文档吗？')) return;
    try {
        await api(`/documents/${docId}`, { method: 'DELETE' });
        if (state.previewDocId === docId) closePreviewPanel();
        invalidateCache('/collections');
        await Promise.all([loadDocuments(), loadCollections()]);
    } catch (e) { showToast('删除失败: ' + e.message, 'error'); }
}

async function uploadFiles(files) {
    const collection = document.getElementById('collectionSelect')?.value;
    if (!collection) { showToast('请先选择目标集合', 'warning'); return; }
    if (state.isUploading) return;
    setState('isUploading', true);
    const status = document.getElementById('uploadStatus');
    const statusText = document.getElementById('uploadStatusText');
    const placeholder = document.getElementById('uploadPlaceholder');
    if (status) { status.classList.remove('hidden'); status.classList.add('flex'); }
    if (placeholder) { placeholder.classList.add('hidden'); }

    let successCount = 0, failCount = 0;
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (statusText) statusText.textContent = `正在处理 ${file.name} (${i + 1}/${files.length})...`;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('collection_name', collection);
        formData.append('chunk_size', document.getElementById('chunkSize')?.value || 1000);
        try {
            const result = await apiForm('/upload', formData);
            if (result.task_id) {
                await pollUploadStatus(result.task_id);
                successCount++;
            } else {
                successCount++;
            }
        } catch (e) { failCount++; }
    }
    if (status) { status.classList.add('hidden'); status.classList.remove('flex'); }
    if (placeholder) { placeholder.classList.remove('hidden'); }
    setState('isUploading', false);
    document.getElementById('fileInput').value = '';
    if (failCount > 0) showToast(`上传完成: ${successCount} 个成功, ${failCount} 个失败`, 'warning');
    else if (successCount > 0) showToast(`上传完成: ${successCount} 个文件已成功上传`, 'success');
    invalidateCache('/collections');
    await Promise.all([loadDocuments(), loadCollections()]);
}

async function pollUploadStatus(taskId) {
    const maxAttempts = 60;
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(r => setTimeout(r, 1000));
        try {
            const result = await api(`/upload/status/${taskId}`);
            if (result.status === 'completed') return result;
            if (result.status === 'failed') throw new Error(result.error || '处理失败');
        } catch (e) {
            if (e.message !== '请求失败') throw e;
        }
    }
    throw new Error('处理超时');
}
