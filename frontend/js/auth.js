import { api } from './api.js';
import { state, setState } from './state.js';

export function updateUserUI() {
    const userMenu = document.getElementById('userMenu');
    const loginBtn = document.getElementById('loginBtn');
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');
    if (state.user) {
        userMenu.classList.remove('hidden');
        userMenu.classList.add('flex');
        loginBtn.classList.add('hidden');
        userName.textContent = state.user.username;
        if (userAvatar) userAvatar.textContent = state.user.username.charAt(0).toUpperCase();
    } else {
        userMenu.classList.add('hidden');
        userMenu.classList.remove('flex');
        loginBtn.classList.remove('hidden');
    }
}

export async function checkAuth() {
    if (!state.token) return false;
    try {
        const user = await api('/auth/me');
        setState('user', user);
        updateUserUI();
        return true;
    } catch (e) {
        setState('token', null);
        localStorage.removeItem('qa_token');
        updateUserUI();
        return false;
    }
}

export async function handleLogin(username, password) {
    const data = await api('/auth/login', { method: 'POST', body: { username, password } });
    setState('token', data.access_token);
    setState('user', data.user);
    localStorage.setItem('qa_token', data.access_token);
    updateUserUI();
    closeAuthModal();
}

export async function handleRegister(username, password) {
    const data = await api('/auth/register', { method: 'POST', body: { username, password } });
    setState('token', data.access_token);
    setState('user', data.user);
    localStorage.setItem('qa_token', data.access_token);
    updateUserUI();
    closeAuthModal();
}

export function handleLogout() {
    setState('token', null);
    setState('user', null);
    localStorage.removeItem('qa_token');
    updateUserUI();
}

export function openAuthModal() {
    const m = document.getElementById('authModal');
    m.classList.remove('hidden');
    m.classList.add('flex');
}

export function closeAuthModal() {
    const m = document.getElementById('authModal');
    m.classList.add('hidden');
    m.classList.remove('flex');
}
