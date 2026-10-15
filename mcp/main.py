#!/usr/bin/env python3
"""AI Memory RAG MCP Server"""

import asyncio
import os
import sys
from typing import Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from api.models.memory import MemoryUnitCreate, SearchQuery
from core.memory_engine import MemoryEngine
from adapters.factory import get_vector_store, get_relational_store
from config.settings import settings


# 初始化记忆引擎
def get_memory_engine() -> MemoryEngine:
    """获取或创建记忆引擎实例"""
    vector_store = get_vector_store()
    relational_store = get_relational_store()
    return MemoryEngine(vector_store, relational_store)


# 创建MCP服务器
server = Server("ai-memory-rag")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="add_memory",
            description="添加一条新的记忆到记忆系统中",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "记忆内容",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "记忆标签，可选",
                        "default": [],
                    },
                    "metadata": {
                        "type": "object",
                        "description": "记忆元数据，可选",
                        "default": {},
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="search_memory",
            description="搜索记忆系统中相关的记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询内容",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量，默认10条",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "threshold": {
                        "type": "number",
                        "description": "相似度阈值，0-1之间，可选",
                        "default": None,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="list_memories",
            description="列出所有记忆（最新的N条",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量，默认50条",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="delete_memory",
            description="删除一条记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "要删除的记忆ID",
                    },
                },
                "required": ["memory_id"],
            },
        ),
        Tool(
            name="get_memory_versions",
            description="获取一条记忆的版本历史",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "记忆ID",
                    },
                },
                "required": ["memory_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """调用工具"""
    engine = get_memory_engine()
    
    if name == "add_memory":
        content = arguments.get("content")
        tags = arguments.get("tags", [])
        metadata = arguments.get("metadata", {})
        
        memory_create = MemoryUnitCreate(
            content=content,
            tags=tags,
            metadata=metadata,
        )
        
        memory = engine.create_memory(memory_create)
        
        result = (
            f"✅ 记忆添加成功！\n"
            f"ID: {memory.id}\n"
            f"内容: {memory.content}\n"
            f"标签: {', '.join(memory.tags) if memory.tags else '无'}\n"
            f"创建时间: {memory.created_at}\n"
        )
        
        return [TextContent(type="text", text=result)]
    
    elif name == "search_memory":
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        threshold = arguments.get("threshold")
        
        search_query = SearchQuery(
            query=query,
            limit=limit,
            threshold=threshold,
        )
        
        results = engine.search(search_query)
        
        if not results:
            return [TextContent(type="text", text="❌ 没有找到相关的记忆")]
        
        result_text = f"🔍 找到 {len(results)} 条相关记忆：\n\n"
        for i, result in enumerate(results, 1):
            result_text += (
                f"{i}. 相似度: {result.score:.4f}\n"
                f"   内容: {result.memory.content}\n"
                f"   标签: {', '.join(result.memory.tags) if result.memory.tags else '无'}\n"
                f"   创建时间: {result.memory.created_at}\n"
                f"   ID: {result.memory.id}\n\n"
            )
        
        return [TextContent(type="text", text=result_text)]
    
    elif name == "list_memories":
        limit = arguments.get("limit", 50)
        memories = engine.list_memories(limit=limit)
        
        if not memories:
            return [TextContent(type="text", text="📭 还没有任何记忆")]
        
        result_text = f"📝 共有 {len(memories)} 条记忆：\n\n"
        for memory in memories:
            result_text += (
                f"ID: {memory.id}\n"
                f"内容: {memory.content}\n"
                f"标签: {', '.join(memory.tags) if memory.tags else '无'}\n"
                f"版本: {memory.version}\n"
                f"创建时间: {memory.created_at}\n\n"
            )
        
        return [TextContent(type="text", text=result_text)]
    
    elif name == "delete_memory":
        memory_id = arguments.get("memory_id")
        success = engine.delete_memory(memory_id)
        
        if success:
            return [TextContent(type="text", text=f"✅ 记忆 {memory_id} 删除成功！")]
        else:
            return [TextContent(type="text", text=f"❌ 删除失败，记忆 {memory_id} 不存在")]
    
    elif name == "get_memory_versions":
        memory_id = arguments.get("memory_id")
        versions = engine.relational_store.get_memory_versions(memory_id)
        
        if not versions:
            return [TextContent(type="text", text=f"❌ 记忆 {memory_id} 不存在或没有版本历史")]
        
        result_text = f"📜 记忆 {memory_id} 的版本历史：\n\n"
        for version in versions:
            result_text += (
                f"版本 {version['version']}\n"
                f"内容: {version['content']}\n"
                f"时间: {version['created_at']}\n\n"
            )
        
        return [TextContent(type="text", text=result_text)]
    
    else:
        return [TextContent(type="text", text=f"❌ 未知工具: {name}")]


async def main():
    """主函数"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
