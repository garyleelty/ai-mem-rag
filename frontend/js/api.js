import { state } from './state.js';

const BASE = (window.API_BASE_URL || 'http://localhost:8000') + '/api/v1';

const _cache = new Map();
const CACHE_TTL = 30_000;

export async function api(url, options = {}) {
    const opts = {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    };
    if (state.token) {
        opts.headers['Authorization'] = `Bearer ${state.token}`;
    }
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(`${BASE}${url}`, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(err.detail || '请求失败');
    }
    return res.json();
}

export async function apiForm(url, formData) {
    const opts = { method: 'POST', body: formData, headers: {} };
    if (state.token) {
        opts.headers['Authorization'] = `Bearer ${state.token}`;
    }
    const res = await fetch(`${BASE}${url}`, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(err.detail || '请求失败');
    }
    return res.json();
}

export async function cachedApi(url, options = {}) {
    const cacheKey = url + JSON.stringify(options);
    const cached = _cache.get(cacheKey);
    if (cached && Date.now() - cached.time < CACHE_TTL) {
        return cached.data;
    }
    const data = await api(url, options);
    _cache.set(cacheKey, { data, time: Date.now() });
    return data;
}

export function invalidateCache(prefix = '') {
    for (const key of _cache.keys()) {
        if (!prefix || key.startsWith(prefix)) _cache.delete(key);
    }
}
