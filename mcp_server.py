#!/usr/bin/env python3
"""
MCP Server for UK Biobank Data Dictionary Tools
Exposes UK Biobank database functionality through Model Context Protocol
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence
import logging

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource, LoggingLevel
)

from ukb_tools import UKBTools
from core.logger import setup_logger
from config.settings import settings

# Setup logging
logger = setup_logger("mcp_server")

# Initialize UK Biobank tools
ukb_tools = UKBTools()

# Create MCP server instance
server = Server("ukb-datadict-server")

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="ukb://categories",
            name="UK Biobank Categories",
            description="All available data categories in UK Biobank",
            mimeType="application/json"
        ),
        Resource(
            uri="ukb://recommended",
            name="Recommended Fields",
            description="Curated list of recommended UK Biobank fields",
            mimeType="application/json"
        ),
        Resource(
            uri="ukb://database-info",
            name="Database Information",
            description="Information about the UK Biobank database structure",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific resource"""
    try:
        if uri == "ukb://categories":
            categories = ukb_tools.get_all_categories()
            return json.dumps(categories, ensure_ascii=False, indent=2)
        
        elif uri == "ukb://recommended":
            recommended = ukb_tools.get_recommended_fields(limit=50)
            return json.dumps(recommended, ensure_ascii=False, indent=2)
        
        elif uri == "ukb://database-info":
            info = {
                "database_path": ukb_tools.db_path,
                "description": "UK Biobank data dictionary SQLite database",
                "tables": [
                    "field - Main data fields",
                    "category - Data categories", 
                    "encoding - Value encodings",
                    "esimpint - Integer encodings",
                    "esimpstring - String encodings",
                    "recommended - Recommended fields",
                    "insvalue - Instance values"
                ]
            }
            return json.dumps(info, ensure_ascii=False, indent=2)
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
            
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="explain_field",
            description="Get detailed information about a UK Biobank field by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "field_id": {
                        "type": "integer",
                        "description": "The UK Biobank field ID to explain"
                    }
                },
                "required": ["field_id"]
            }
        ),
        Tool(
            name="search_fields",
            description="Search UK Biobank fields by keyword",
            inputSchema={
                "type": "object", 
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to search for in field titles and descriptions"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 20
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_category_fields",
            description="Get all fields in a specific category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_name": {
                        "type": "string", 
                        "description": "Name of the category to search (supports partial matching)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 50
                    }
                },
                "required": ["category_name"]
            }
        ),
        Tool(
            name="get_encoding_values",
            description="Get the meaning of encoded values for a specific encoding ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "encoding_id": {
                        "type": "integer",
                        "description": "The encoding ID to look up"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Maximum number of encoding values to return",
                        "default": 50
                    }
                },
                "required": ["encoding_id"]
            }
        ),
        Tool(
            name="recommend_related_fields", 
            description="Find fields related to a given field ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "field_id": {
                        "type": "integer",
                        "description": "The reference field ID to find related fields for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of related fields to return", 
                        "default": 10
                    }
                },
                "required": ["field_id"]
            }
        ),
        Tool(
            name="get_all_categories",
            description="Get all available data categories in UK Biobank",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_recommended_fields",
            description="Get curated recommended fields, optionally filtered by category",
            inputSchema={
                "type": "object",
                "properties": {
                    "category_name": {
                        "type": "string",
                        "description": "Optional category name to filter recommendations"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recommended fields to return",
                        "default": 20
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "explain_field":
            field_id = arguments.get("field_id")
            if not field_id:
                raise ValueError("field_id is required")
            
            result = ukb_tools.explain_field_by_id(field_id)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "search_fields":
            keyword = arguments.get("keyword")
            limit = arguments.get("limit", 20)
            if not keyword:
                raise ValueError("keyword is required")
            
            result = ukb_tools.search_fields_by_keyword(keyword, limit)
            return [TextContent(
                type="text", 
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_category_fields":
            category_name = arguments.get("category_name")
            limit = arguments.get("limit", 50)
            if not category_name:
                raise ValueError("category_name is required")
            
            result = ukb_tools.get_category_fields(category_name, limit)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_encoding_values":
            encoding_id = arguments.get("encoding_id")
            limit = arguments.get("limit", 50)
            if encoding_id is None:
                raise ValueError("encoding_id is required")
            
            result = ukb_tools.get_encoding_values(encoding_id, limit)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "recommend_related_fields":
            field_id = arguments.get("field_id")
            limit = arguments.get("limit", 10)
            if not field_id:
                raise ValueError("field_id is required")
            
            result = ukb_tools.recommend_related_fields(field_id, limit)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_all_categories":
            result = ukb_tools.get_all_categories()
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        elif name == "get_recommended_fields":
            category_name = arguments.get("category_name")
            limit = arguments.get("limit", 20)
            
            result = ukb_tools.get_recommended_fields(category_name, limit)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, ensure_ascii=False)
        )]

async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting UK Biobank MCP Server")
    
    # Test database connection
    try:
        test_result = ukb_tools.get_all_categories()
        logger.info(f"Database connection successful, found {len(test_result)} categories")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ukb-datadict-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(
                        resources_changed=False,
                        tools_changed=False,
                        prompts_changed=False
                    ),
                    experimental_capabilities={}
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())