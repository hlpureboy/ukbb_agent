#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ukbb-phes",
# ]
#
# [tool.uv.sources]
# ukbb-phes = { path = "." }
# ///
"""
MCP Server for UK Biobank Data Dictionary Tools
Exposes UK Biobank database functionality through Model Context Protocol
"""

import json
import sys
from typing import Any, Dict, List, Optional
import logging

from mcp.server.fastmcp import FastMCP

from ukb_tools import UKBTools
from core.logger import setup_logger
from config.settings import settings

# Setup logging
logger = setup_logger("mcp_server")

# Initialize UK Biobank tools
ukb_tools = UKBTools()

# Create FastMCP server instance
mcp = FastMCP("ukb-datadict-server")

@mcp.resource("ukb://categories")
async def get_categories():
    """Get all available data categories in UK Biobank"""
    categories = ukb_tools.get_all_categories()
    return json.dumps(categories, ensure_ascii=False, indent=2)

@mcp.resource("ukb://recommended")
async def get_recommended():
    """Get curated list of recommended UK Biobank fields"""
    recommended = ukb_tools.get_recommended_fields(limit=50)
    return json.dumps(recommended, ensure_ascii=False, indent=2)

@mcp.resource("ukb://database-info")
async def get_database_info():
    """Get information about the UK Biobank database structure"""
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

@mcp.tool()
async def explain_field(field_id: int) -> str:
    """Get detailed information about a UK Biobank field by ID"""
    try:
        result = ukb_tools.explain_field_by_id(field_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error explaining field {field_id}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def search_fields(keyword: str, limit: int = 20) -> str:
    """Search UK Biobank fields by keyword"""
    try:
        result = ukb_tools.search_fields_by_keyword(keyword, limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error searching fields with keyword '{keyword}': {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def get_category_fields(category_name: str, limit: int = 50) -> str:
    """Get all fields in a specific category"""
    try:
        result = ukb_tools.get_category_fields(category_name, limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error getting fields for category '{category_name}': {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def get_encoding_values(encoding_id: int, limit: int = 50) -> str:
    """Get the meaning of encoded values for a specific encoding ID"""
    try:
        result = ukb_tools.get_encoding_values(encoding_id, limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error getting encoding values for ID {encoding_id}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def recommend_related_fields(field_id: int, limit: int = 10) -> str:
    """Find fields related to a given field ID"""
    try:
        result = ukb_tools.recommend_related_fields(field_id, limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error finding related fields for {field_id}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def get_all_categories() -> str:
    """Get all available data categories in UK Biobank"""
    try:
        result = ukb_tools.get_all_categories()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error getting all categories: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
async def get_recommended_fields(category_name: Optional[str] = None, limit: int = 20) -> str:
    """Get curated recommended fields, optionally filtered by category"""
    try:
        result = ukb_tools.get_recommended_fields(category_name, limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error getting recommended fields: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    # Test database connection
    try:
        test_result = ukb_tools.get_all_categories()
        logger.info(f"Database connection successful, found {len(test_result)} categories")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)
    
    logger.info("Starting UK Biobank MCP Server")
    mcp.run()