export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleString('zh-CN');
}

export function setConnectionStatus(status, text) {
    const el = document.getElementById('connStatus');
    if (!el) return;
    const dot = el.querySelector('span');
    if (status === 'connected') {
        el.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-600';
        if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-slow';
    } else if (status === 'error') {
        el.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-red-50 text-red-600';
        if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-red-500';
    } else {
        el.className = 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-surface-100 text-surface-500';
        if (dot) dot.className = 'w-1.5 h-1.5 rounded-full bg-surface-300';
    }
    el.innerHTML = (dot ? dot.outerHTML : '') + text;
}

let _toastContainer = null;

function getToastContainer() {
    if (!_toastContainer) {
        _toastContainer = document.createElement('div');
        _toastContainer.id = 'toastContainer';
        _toastContainer.className = 'fixed top-20 right-6 z-[200] flex flex-col gap-2';
        document.body.appendChild(_toastContainer);
    }
    return _toastContainer;
}

export function showToast(message, type = 'info') {
    const container = getToastContainer();
    const colors = {
        info: 'bg-brand-50 text-brand-700 border-brand-200',
        success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        error: 'bg-red-50 text-red-700 border-red-200',
        warning: 'bg-amber-50 text-amber-700 border-amber-200',
    };
    const toast = document.createElement('div');
    toast.className = `px-4 py-3 rounded-xl border shadow-md text-sm font-medium animate-slide-up ${colors[type] || colors.info}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

export function customPrompt(title, placeholder = '') {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 z-[200] flex items-center justify-center';
        overlay.innerHTML = `
            <div class="absolute inset-0 bg-surface-900/40 backdrop-blur-sm"></div>
            <div class="relative bg-white rounded-2xl shadow-2xl w-[90vw] max-w-[400px] overflow-hidden animate-slide-up">
                <div class="px-6 py-4 border-b border-surface-100">
                    <h3 class="font-semibold text-surface-800">${title}</h3>
                </div>
                <div class="px-6 py-4">
                    <input type="text" id="customPromptInput" placeholder="${placeholder}" class="w-full px-4 py-2.5 rounded-xl border border-surface-200 bg-surface-50 text-sm focus:outline-none focus:border-brand-400 focus:shadow-glow transition-all" autofocus>
                </div>
                <div class="px-6 py-4 flex gap-3 justify-end border-t border-surface-100">
                    <button id="customPromptCancel" class="px-4 py-2 rounded-xl border border-surface-200 text-sm font-medium text-surface-600 hover:border-brand-300 transition-all">取消</button>
                    <button id="customPromptOk" class="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all">确定</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        const input = overlay.querySelector('#customPromptInput');
        input.focus();

        const close = (value) => {
            overlay.remove();
            resolve(value);
        };

        overlay.querySelector('#customPromptCancel').addEventListener('click', () => close(null));
        overlay.querySelector('#customPromptOk').addEventListener('click', () => close(input.value || null));
        overlay.querySelector('.absolute').addEventListener('click', () => close(null));
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') close(input.value || null);
            if (e.key === 'Escape') close(null);
        });
    });
}

export function customConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 z-[200] flex items-center justify-center';
        overlay.innerHTML = `
            <div class="absolute inset-0 bg-surface-900/40 backdrop-blur-sm"></div>
            <div class="relative bg-white rounded-2xl shadow-2xl w-[90vw] max-w-[400px] overflow-hidden animate-slide-up">
                <div class="px-6 py-6">
                    <p class="text-surface-800 text-sm">${message}</p>
                </div>
                <div class="px-6 py-4 flex gap-3 justify-end border-t border-surface-100">
                    <button id="customConfirmCancel" class="px-4 py-2 rounded-xl border border-surface-200 text-sm font-medium text-surface-600 hover:border-brand-300 transition-all">取消</button>
                    <button id="customConfirmOk" class="px-4 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 text-white text-sm font-semibold shadow-md hover:shadow-lg transition-all">确定</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        const close = (value) => {
            overlay.remove();
            resolve(value);
        };

        overlay.querySelector('#customConfirmCancel').addEventListener('click', () => close(false));
        overlay.querySelector('#customConfirmOk').addEventListener('click', () => close(true));
        overlay.querySelector('.absolute').addEventListener('click', () => close(false));
    });
}
