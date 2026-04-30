const API_BASE = (window.API_BASE_URL || 'http://localhost:8000') + '/api/v1';

const AppState = {
    collections: [],
    selectedCollection: '',
    chunkSize: 1000,
    documents: [],
    previewDocId: null,
    isUploading: false
};

// DOM 元素
const els = {
    collectionSelect: document.getElementById('collectionSelect'),
    docCollectionSelect: document.getElementById('docCollectionSelect'),
    newCollectionName: document.getElementById('newCollectionName'),
    createCollectionBtn: document.getElementById('createCollectionBtn'),
    chunkSize: document.getElementById('chunkSize'),
    uploadBtn: document.getElementById('uploadBtn'),
    fileInput: document.getElementById('fileInput'),
    dropZone: document.getElementById('dropZone'),
    uploadStatus: document.getElementById('uploadStatus'),
    uploadStatusText: document.getElementById('uploadStatusText'),
    documentList: document.getElementById('documentList'),
    docCount: document.getElementById('docCount'),
    previewPanel: document.getElementById('previewPanel'),
    previewHeader: document.getElementById('previewHeader'),
    previewContent: document.getElementById('previewContent'),
    closePreview: document.getElementById('closePreview'),
    connStatus: document.getElementById('connStatus'),
    segments: document.querySelectorAll('.segment'),
};

// API 请求辅助函数
async function api(url, options = {}) {
    const res = await fetch(`${API_BASE}${url}`, options);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(err.detail || '请求失败');
    }
    return res.json();
}

// 更新连接状态
function setConnectionStatus(status, text) {
    if (!els.connStatus) return;
    els.connStatus.className = 'status-badge ' + status;
    els.connStatus.textContent = text;
}

// 加载集合列表
async function loadCollections() {
    try {
        const data = await api('/collections');
        AppState.collections = data.collections || [];
        setConnectionStatus('connected', '已连接');
        renderCollectionSelects();
    } catch (e) {
        console.error('加载集合失败:', e);
        setConnectionStatus('error', '连接失败');
    }
}

// 渲染集合下拉框
function renderCollectionSelects() {
    const options = ['<option value="">请选择集合</option>'];
    AppState.collections.forEach(c => {
        options.push(`<option value="${c.name}">${c.name} (${c.count})</option>`);
    });

    const html = options.join('');
    els.collectionSelect.innerHTML = html;
    els.docCollectionSelect.innerHTML = html;

    if (AppState.selectedCollection) {
        els.collectionSelect.value = AppState.selectedCollection;
        els.docCollectionSelect.value = AppState.selectedCollection;
    }
}

// 创建集合
async function createCollection() {
    const name = els.newCollectionName.value.trim();
    if (!name) {
        alert('请输入集合名称');
        return;
    }
    try {
        await api('/collections', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        els.newCollectionName.value = '';
        await loadCollections();
        AppState.selectedCollection = name;
        renderCollectionSelects();
        await loadDocuments();
    } catch (e) {
        alert('创建集合失败: ' + e.message);
    }
}

// 加载文档列表
async function loadDocuments() {
    const collection = els.docCollectionSelect.value;
    if (!collection) {
        renderEmptyState('选择集合并上传文件');
        els.docCount.textContent = '';
        return;
    }

    try {
        const data = await api(`/collections/${encodeURIComponent(collection)}/documents`);
        AppState.documents = data.documents || [];
        renderDocuments();
    } catch (e) {
        console.error('加载文档失败:', e);
        renderEmptyState('加载失败，请重试');
    }
}

function renderEmptyState(hint) {
    els.documentList.innerHTML = `
        <div class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="40" height="40">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
            </svg>
            <p>暂无文档</p>
            <span>${hint}</span>
        </div>
    `;
}

// 渲染文档列表
function renderDocuments() {
    if (AppState.documents.length === 0) {
        renderEmptyState('选择集合并上传文件');
        els.docCount.textContent = '';
        return;
    }

    const html = AppState.documents.map(doc => `
        <div class="doc-item ${doc.id === AppState.previewDocId ? 'active' : ''}" data-id="${doc.id}">
            <div class="doc-name">${escapeHtml(doc.source)}</div>
            <div class="doc-meta">${doc.chunk_count} 个分块 · ${formatDate(doc.created_at)}</div>
            <div class="doc-actions">
                <button class="view-btn" data-id="${doc.id}">查看内容</button>
                <button class="delete-btn" data-id="${doc.id}">删除</button>
            </div>
        </div>
    `).join('');

    els.documentList.innerHTML = html;
    els.docCount.textContent = `共 ${AppState.documents.length} 个文档`;

    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            loadDocumentChunks(btn.dataset.id);
        });
    });
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteDocument(btn.dataset.id);
        });
    });
    document.querySelectorAll('.doc-item').forEach(item => {
        item.addEventListener('click', () => {
            loadDocumentChunks(item.dataset.id);
        });
    });
}

// 加载文档分块
async function loadDocumentChunks(docId) {
    AppState.previewDocId = docId;
    renderDocuments();

    try {
        const data = await api(`/documents/${docId}/chunks`);
        els.previewPanel.style.display = 'block';
        els.previewHeader.textContent = `${data.document_name} · 共 ${data.chunks.length} 个分块`;
        els.previewContent.innerHTML = data.chunks.map(chunk => `
            <div class="chunk-item">
                <div class="chunk-index">分块 ${chunk.index + 1}</div>
                <div class="chunk-text">${escapeHtml(chunk.content)}</div>
            </div>
        `).join('');
        els.previewPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
        alert('加载文档内容失败: ' + e.message);
    }
}

// 关闭预览
function closePreviewPanel() {
    AppState.previewDocId = null;
    els.previewPanel.style.display = 'none';
    renderDocuments();
}

// 删除文档
async function deleteDocument(docId) {
    if (!confirm('确定要删除该文档吗？')) return;

    try {
        await api(`/documents/${docId}`, { method: 'DELETE' });
        if (AppState.previewDocId === docId) {
            closePreviewPanel();
        }
        await Promise.all([loadDocuments(), loadCollections()]);
    } catch (e) {
        alert('删除失败: ' + e.message);
    }
}

// 上传文件
async function uploadFiles(files) {
    const collection = els.collectionSelect.value;
    if (!collection) {
        alert('请先选择目标集合');
        return;
    }

    if (AppState.isUploading) return;
    AppState.isUploading = true;
    els.uploadStatus.style.display = 'flex';
    els.dropZone.querySelector('.upload-placeholder').style.display = 'none';

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        els.uploadStatusText.textContent = `正在处理 ${file.name} (${i + 1}/${files.length})...`;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('collection_name', collection);
        formData.append('chunk_size', els.chunkSize.value);

        try {
            await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            }).then(async res => {
                if (!res.ok) {
                    const err = await res.json().catch(() => ({ detail: '上传失败' }));
                    throw new Error(err.detail);
                }
                return res.json();
            });
            successCount++;
        } catch (e) {
            failCount++;
            console.error(`上传 ${file.name} 失败:`, e.message);
        }
    }

    els.uploadStatus.style.display = 'none';
    els.dropZone.querySelector('.upload-placeholder').style.display = 'flex';
    AppState.isUploading = false;
    els.fileInput.value = '';

    if (failCount > 0) {
        alert(`上传完成: ${successCount} 个成功, ${failCount} 个失败`);
    }

    await Promise.all([loadDocuments(), loadCollections()]);

    if (els.docCollectionSelect.value !== collection) {
        els.docCollectionSelect.value = collection;
        AppState.selectedCollection = collection;
        await loadDocuments();
    }
}

// 工具函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// 事件绑定
els.createCollectionBtn.addEventListener('click', createCollection);

els.newCollectionName.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') createCollection();
});

els.collectionSelect.addEventListener('change', (e) => {
    AppState.selectedCollection = e.target.value;
    els.docCollectionSelect.value = e.target.value;
    loadDocuments();
});

els.docCollectionSelect.addEventListener('change', (e) => {
    AppState.selectedCollection = e.target.value;
    els.collectionSelect.value = e.target.value;
    loadDocuments();
});

// 分段控制器
els.segments.forEach(seg => {
    seg.addEventListener('click', () => {
        els.segments.forEach(s => s.classList.remove('active'));
        seg.classList.add('active');
        els.chunkSize.value = seg.dataset.value;
    });
});

els.uploadBtn.addEventListener('click', () => {
    els.fileInput.click();
});

els.fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadFiles(Array.from(e.target.files));
    }
});

els.closePreview.addEventListener('click', closePreviewPanel);

// 拖拽上传
els.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    els.dropZone.classList.add('dragover');
});

els.dropZone.addEventListener('dragleave', () => {
    els.dropZone.classList.remove('dragover');
});

els.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    els.dropZone.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files).filter(f => {
        const ext = f.name.slice(f.name.lastIndexOf('.')).toLowerCase();
        return ext === '.pdf' || ext === '.docx';
    });
    if (files.length > 0) {
        uploadFiles(files);
    } else {
        alert('仅支持 PDF 和 DOCX 文件');
    }
});

// 初始化
loadCollections();
