export const state = {
    token: localStorage.getItem('qa_token') || null,
    user: null,
    currentPage: 'qa',
    collections: [],
    selectedCollection: '',
    chunkSize: 1000,
    documents: [],
    previewDocId: null,
    isUploading: false,
    qaRecords: [],
    conversations: [],
    selectedConversation: null,
    preferences: null,
    presetTags: [],
};

export function setState(key, value) {
    state[key] = value;
}
