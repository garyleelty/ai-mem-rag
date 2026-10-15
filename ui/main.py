import streamlit as st
import requests
import json
from datetime import datetime
from typing import List

st.set_page_config(
    page_title="AI Memory RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://localhost:8000"


def get_api(path: str) -> dict:
    try:
        response = requests.get(f"{API_BASE_URL}{path}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return {}


def post_api(path: str, data: dict) -> dict:
    try:
        response = requests.post(f"{API_BASE_URL}{path}", json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return {}


def put_api(path: str, data: dict) -> dict:
    try:
        response = requests.put(f"{API_BASE_URL}{path}", json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return {}


def delete_api(path: str) -> bool:
    try:
        response = requests.delete(f"{API_BASE_URL}{path}")
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"API 请求失败: {e}")
        return False


def format_datetime(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str


def main():
    st.title("🧠 AI Memory RAG")
    st.markdown("---")

    st.sidebar.title("导航")
    page = st.sidebar.radio(
        "选择页面",
        ["首页", "记忆管理", "语义搜索", "知识图谱"]
    )

    if page == "首页":
        show_home()
    elif page == "记忆管理":
        show_memory_management()
    elif page == "语义搜索":
        show_search()
    elif page == "知识图谱":
        show_graph()


def show_home():
    st.header("欢迎来到 AI Memory RAG")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            memories = get_api("/api/memories")
            st.metric("总记忆数", len(memories) if memories else 0)
        except:
            st.metric("总记忆数", 0)
    
    with col2:
        st.metric("API 状态", "✅ 正常")
    
    with col3:
        st.metric("向量数据库", "ChromaDB")
    
    st.markdown("---")
    st.subheader("快速开始")
    st.markdown("📝 **记忆管理 - 创建、编辑、删除你的记忆")
    st.markdown("🔍 **语义搜索 - 使用自然语言搜索记忆")
    st.markdown("🌐 **知识图谱 - 查看记忆之间的关系")


def show_memory_management():
    st.header("记忆管理")
    
    tab1, tab2 = st.tabs(["创建记忆", "查看记忆列表"])
    
    with tab1:
        st.subheader("创建新记忆")
        content = st.text_area("记忆内容", height=200, placeholder="请输入记忆内容...")
        tags_input = st.text_input("标签 (用逗号分隔)", placeholder="例如: 学习, 笔记")
        
        metadata_str = st.text_area("元数据 (JSON 格式)", placeholder='{"source": "manual"}', height=100)
        
        if st.button("创建记忆", type="primary"):
            if not content:
                st.error("请输入记忆内容")
            else:
                try:
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
                    metadata = json.loads(metadata_str) if metadata_str.strip() else {}
                    
                    result = post_api("/api/memories", {
                        "content": content,
                        "tags": tags,
                        "metadata": metadata
                    })
                    
                    if result:
                        st.success("记忆创建成功!")
                        st.json(result)
                except json.JSONDecodeError:
                    st.error("元数据格式错误，请输入有效的 JSON")
                except Exception as e:
                    st.error(f"创建失败: {e}")
    
    with tab2:
        st.subheader("记忆列表")
        memories = get_api("/api/memories")
        
        if not memories:
            st.info("暂无记忆，请先创建记忆")
        else:
            for memory in memories:
                with st.expander(f"记忆: {memory['id'][:8]}..."):
                    st.write(f"**内容**: {memory['content']}")
                    st.write(f"**标签**: {', '.join(memory.get('tags', []))}")
                    st.write(f"**版本**: {memory['version']}")
                    st.write(f"**创建时间**: {format_datetime(memory['created_at'])}")
                    st.write(f"**更新时间**: {format_datetime(memory['updated_at'])}")
                    
                    if st.button(f"删除", key=f"delete_{memory['id']}"):
                        if delete_api(f"/api/memories/{memory['id']}"):
                            st.success("删除成功!")
                            st.rerun()


def show_search():
    st.header("语义搜索")
    
    query = st.text_input("搜索查询", placeholder="请输入搜索内容...")
    limit = st.slider("返回结果数量", 1, 50, 10)
    threshold = st.slider("相似度阈值", 0.0, 1.0, 0.0, 0.1)
    
    if st.button("搜索", type="primary") and query:
        results = post_api("/api/memories/search", {
            "query": query,
            "limit": limit,
            "threshold": threshold if threshold > 0 else None
        })
        
        if not results:
            st.info("未找到相关记忆")
        else:
            st.subheader(f"找到 {len(results)} 个相关结果")
            for idx, result in enumerate(results, 1):
                memory = result['memory']
                score = result['score']
                
                with st.expander(f"结果 {idx} (相似度: {score:.4f})"):
                    st.write(f"**内容**: {memory['content']}")
                    st.write(f"**标签**: {', '.join(memory.get('tags', []))}")
                    st.write(f"**创建时间**: {format_datetime(memory['created_at'])}")
                    st.progress(score)


def show_graph():
    st.header("知识图谱")
    st.info("知识图谱功能开发中...")
    
    st.markdown("此页面将显示记忆之间的关系可视化")
    
    memories = get_api("/api/memories")
    
    if memories:
        st.write(f"当前有 {len(memories)} 个记忆")
        for memory in memories:
            st.markdown(f"- {memory['id'][:8]}: {memory['content'][:50]}...")


if __name__ == "__main__":
    main()
