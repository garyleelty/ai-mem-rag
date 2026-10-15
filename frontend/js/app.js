import { api } from './api.js';
import { state, setState } from './state.js';
import { checkAuth, handleLogin, handleRegister, handleLogout, openAuthModal, closeAuthModal } from './auth.js';
import { setupQADetailClose } from './pages/qa.js';
import * as qaPage from './pages/qa.js';
import * as docsPage from './pages/documents.js';
import * as prefsPage from './pages/preferences.js';

const pages = { qa: qaPage, documents: docsPage, preferences: prefsPage };

async function loadPage(page) {
    setState('currentPage', page);
    const main = document.getElementById('mainContent');
    document.querySelectorAll('.nav-tab').forEach(t => {
        if (t.dataset.page === page) {
            t.classList.add('bg-white', 'text-brand-600', 'shadow-card');
            t.classList.remove('text-surface-500');
        } else {
            t.classList.remove('bg-white', 'text-brand-600', 'shadow-card');
            t.classList.add('text-surface-500');
        }
    });
    main.innerHTML = pages[page].render();
    await pages[page].init();
}

async function loadPresetTags() {
    if (!state.token) return;
    try {
        const data = await api('/tags/preset');
        setState('presetTags', data);
    } catch (e) {
        console.error('加载标签失败:', e);
    }
}

async function init() {
    await checkAuth();
    await loadPresetTags();
    setupQADetailClose();

    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => loadPage(tab.dataset.page));
    });

    document.getElementById('loginBtn')?.addEventListener('click', openAuthModal);
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        handleLogout();
        loadPage('qa');
    });

    document.getElementById('authBackdrop')?.addEventListener('click', closeAuthModal);

    const authForm = document.getElementById('authForm');
    const authTitle = document.getElementById('authTitle');
    const authSubmitBtn = document.getElementById('authSubmitBtn');
    const authSwitchBtn = document.getElementById('authSwitchBtn');
    let isLogin = true;

    authSwitchBtn?.addEventListener('click', () => {
        isLogin = !isLogin;
        authTitle.textContent = isLogin ? '欢迎回来' : '创建账号';
        authSubmitBtn.textContent = isLogin ? '登录' : '注册';
        authSwitchBtn.textContent = isLogin ? '去注册' : '去登录';
    });

    authForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('authUsername').value;
        const password = document.getElementById('authPassword').value;
        try {
            if (isLogin) await handleLogin(username, password);
            else await handleRegister(username, password);
            await loadPresetTags();
            loadPage(state.currentPage);
        } catch (err) { alert(err.message); }
    });

    loadPage('qa');
}

init();
