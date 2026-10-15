import requests

BASE = "http://localhost:8000/api/v1"

# 使用已有账号登录
print("=== 1. Login ===")
r = requests.post(f"{BASE}/auth/login", json={"username": "testuser10", "password": "testpass123"})
if r.status_code != 200:
    print("Login failed, trying register...")
    r = requests.post(f"{BASE}/auth/register", json={"username": "testuser11", "password": "testpass123"})
print(r.status_code, r.json())
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n=== 2. Me ===")
r = requests.get(f"{BASE}/auth/me", headers=headers)
print(r.status_code, r.json())

print("\n=== 3. Create Conversation ===")
r = requests.post(f"{BASE}/conversations", headers=headers, json={"title": "测试会话"})
print(r.status_code, r.json())
conv_id = r.json()["id"]

print("\n=== 4. Create QA Record ===")
r = requests.post(f"{BASE}/qa/records", headers=headers, json={
    "question": "什么是RAG？",
    "answer": "RAG是检索增强生成技术。",
    "model_name": "gpt-4",
    "conversation_id": conv_id
})
print(r.status_code, r.json())
qa_id = r.json()["id"]

print("\n=== 5. List QA Records ===")
r = requests.get(f"{BASE}/qa/records", headers=headers)
print(r.status_code, r.json())

print("\n=== 6. Search ===")
r = requests.post(f"{BASE}/qa/search", headers=headers, json={"query": "检索增强", "top_k": 3})
print(r.status_code, r.text)

print("\n=== 7. Preferences ===")
r = requests.get(f"{BASE}/preferences", headers=headers)
print(r.status_code, r.json())

print("\n=== 8. Tags ===")
r = requests.get(f"{BASE}/tags/preset", headers=headers)
print(r.status_code, r.json())

print("\n=== 9. Feedback ===")
r = requests.post(f"{BASE}/qa/records/{qa_id}/feedback", headers=headers, json={
    "feedback_type": "thumbs_up",
    "preset_tags": ["accurate"],
    "comment": "很好"
})
print(r.status_code, r.json())

print("\n=== ALL TESTS COMPLETED ===")
