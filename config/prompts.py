#!/usr/bin/env python3
"""
Multilingual Prompt Management
中英双语Prompt配置管理
"""

from typing import Dict, Any
from enum import Enum
from config.settings import Language

class PromptTemplate:
    """Prompt模板类"""
    
    def __init__(self, zh: str, en: str):
        self.zh = zh
        self.en = en
    
    def get(self, language: Language = Language.CHINESE) -> str:
        """根据语言获取对应的prompt"""
        return self.zh if language == Language.CHINESE else self.en
    
    def format(self, language: Language = Language.CHINESE, **kwargs) -> str:
        """格式化prompt"""
        template = self.get(language)
        return template.format(**kwargs)

# 系统默认Prompt
DEFAULT_SYSTEM_PROMPT = PromptTemplate(
    zh="""你是UK Biobank数据字典的专家助手。你可以使用提供的工具来帮助用户：

🔍 **可用工具**：
1. **explain_field_by_id** - 根据field_id查询字段详细信息
2. **search_fields_by_keyword** - 关键字搜索相关字段
3. **get_category_fields** - 浏览特定分类的字段
4. **get_encoding_values** - 查看编码值含义
5. **recommend_related_fields** - 推荐相关字段
6. **get_all_categories** - 获取所有数据分类
7. **get_recommended_fields** - 查看推荐使用的字段

📋 **搜索关键词建议**：
- 心理健康: 使用 "mental", "depression", "anxiety", "mood", "psychiatric"
- 心血管: 使用 "heart", "cardiac", "blood", "pressure"  
- 糖尿病: 使用 "diabetes", "glucose", "insulin"
- 癌症: 使用 "cancer", "tumour", "malignant"
- 脑部: 使用 "brain", "mri", "cognitive"

📋 **使用指南**：
- 当用户询问特定字段时，使用explain_field_by_id
- 当用户搜索某个主题时，使用search_fields_by_keyword，选择最佳的英文关键词
- 当用户想了解某个分类时，使用get_category_fields
- 主动推荐相关的测量指标和数据字段
- 用中文清晰地解释查询结果
- 搜索时使用单个英文关键词效果最好

请耐心详细地回答问题，充分利用这些工具为用户提供准确有用的信息。""",

    en="""You are an expert assistant for the UK Biobank data dictionary. You can use the provided tools to help users:

🔍 **Available Tools**:
1. **explain_field_by_id** - Query detailed field information by field_id
2. **search_fields_by_keyword** - Search related fields by keywords
3. **get_category_fields** - Browse fields in specific categories
4. **get_encoding_values** - View encoding value meanings
5. **recommend_related_fields** - Recommend related fields
6. **get_all_categories** - Get all data categories
7. **get_recommended_fields** - View recommended fields

📋 **Search Keyword Suggestions**:
- Mental health: use "mental", "depression", "anxiety", "mood", "psychiatric"
- Cardiovascular: use "heart", "cardiac", "blood", "pressure"
- Diabetes: use "diabetes", "glucose", "insulin"
- Cancer: use "cancer", "tumour", "malignant"
- Brain: use "brain", "mri", "cognitive"

📋 **Usage Guide**:
- When users ask about specific fields, use explain_field_by_id
- When users search for topics, use search_fields_by_keyword with optimal English keywords
- When users want to explore categories, use get_category_fields
- Proactively recommend related measurements and data fields
- Provide clear explanations in English
- Single English keywords work best for searches

Please answer questions patiently and thoroughly, making full use of these tools to provide accurate and useful information."""
)

# 错误消息模板
ERROR_MESSAGES = {
    "field_not_found": PromptTemplate(
        zh="字段 {field_id} 不存在，请检查字段ID是否正确。",
        en="Field {field_id} not found. Please check if the field ID is correct."
    ),
    "search_no_results": PromptTemplate(
        zh="没有找到包含关键词 '{keyword}' 的字段。请尝试其他关键词。",
        en="No fields found containing keyword '{keyword}'. Please try other keywords."
    ),
    "category_not_found": PromptTemplate(
        zh="分类 '{category}' 不存在。请使用 get_all_categories 查看可用分类。",
        en="Category '{category}' not found. Please use get_all_categories to view available categories."
    ),
    "encoding_not_found": PromptTemplate(
        zh="编码 {encoding_id} 不存在，请检查编码ID是否正确。",
        en="Encoding {encoding_id} not found. Please check if the encoding ID is correct."
    ),
    "api_error": PromptTemplate(
        zh="API调用失败：{error}。请稍后重试。",
        en="API call failed: {error}. Please try again later."
    ),
    "rate_limit_exceeded": PromptTemplate(
        zh="请求频率过高，请稍后再试。",
        en="Rate limit exceeded. Please try again later."
    )
}

# 成功消息模板
SUCCESS_MESSAGES = {
    "search_completed": PromptTemplate(
        zh="搜索完成，找到 {count} 个相关字段。",
        en="Search completed. Found {count} related fields."
    ),
    "field_explained": PromptTemplate(
        zh="字段 {field_id} 的详细信息已获取。",
        en="Detailed information for field {field_id} has been retrieved."
    ),
    "recommendations_found": PromptTemplate(
        zh="为字段 {field_id} 找到 {count} 个相关推荐。",
        en="Found {count} related recommendations for field {field_id}."
    )
}

# 工具描述（多语言）
TOOL_DESCRIPTIONS = {
    "explain_field_by_id": PromptTemplate(
        zh="根据字段ID获取字段的完整解释信息，包括描述、单位、参与者数量、编码值等。",
        en="Get complete field information by field ID, including description, units, participant count, encoding values, etc."
    ),
    "search_fields_by_keyword": PromptTemplate(
        zh="使用关键词搜索相关字段，支持模糊匹配标题和描述。",
        en="Search related fields using keywords, supporting fuzzy matching of titles and descriptions."
    ),
    "get_category_fields": PromptTemplate(
        zh="获取指定分类下的所有字段，用于浏览特定医学领域的数据。",
        en="Get all fields under a specified category for browsing data in specific medical domains."
    ),
    "get_encoding_values": PromptTemplate(
        zh="查看字段编码值的具体含义，了解数据如何编码。",
        en="View the specific meanings of field encoding values to understand how data is encoded."
    ),
    "recommend_related_fields": PromptTemplate(
        zh="基于指定字段推荐相关字段，帮助发现相关的测量指标。",
        en="Recommend related fields based on a specified field to help discover related measurements."
    ),
    "get_all_categories": PromptTemplate(
        zh="获取所有可用的数据分类列表。",
        en="Get a list of all available data categories."
    ),
    "get_recommended_fields": PromptTemplate(
        zh="获取推荐使用的字段列表，这些是常用的重要字段。",
        en="Get a list of recommended fields that are commonly used and important."
    )
}

# 帮助信息
HELP_MESSAGES = {
    "usage_guide": PromptTemplate(
        zh="""
## 使用指南

### 基本搜索
- 直接输入疾病或生理指标名称，如："depression"、"blood pressure"
- 系统会自动搜索相关字段并提供详细解释

### 高级查询
- 使用字段ID查询：`字段 31 的详细信息`
- 浏览分类：`心血管相关的所有字段`
- 查看编码：`编码 100291 的含义`

### 推荐功能
- 获取相关字段：`与字段 31 相关的其他字段`
- 查看推荐字段：`推荐的心理健康字段`

### 搜索技巧
- 使用英文关键词效果更好
- 尝试不同的关键词组合
- 可以询问具体的医学术语或测量方法
        """,
        en="""
## Usage Guide

### Basic Search
- Enter disease or physiological indicator names directly, e.g., "depression", "blood pressure"
- The system will automatically search related fields and provide detailed explanations

### Advanced Queries
- Query by field ID: `Details for field 31`
- Browse categories: `All cardiovascular-related fields`
- View encodings: `Meaning of encoding 100291`

### Recommendation Features
- Get related fields: `Other fields related to field 31`
- View recommended fields: `Recommended mental health fields`

### Search Tips
- English keywords work better
- Try different keyword combinations
- You can ask about specific medical terms or measurement methods
        """
    )
}

def get_prompt(template_name: str, language: Language = Language.CHINESE, **kwargs) -> str:
    """获取格式化的prompt"""
    if template_name == "default_system":
        return DEFAULT_SYSTEM_PROMPT.get(language)
    
    # 查找对应的模板
    for template_dict in [ERROR_MESSAGES, SUCCESS_MESSAGES, TOOL_DESCRIPTIONS, HELP_MESSAGES]:
        if template_name in template_dict:
            return template_dict[template_name].format(language, **kwargs)
    
    raise ValueError(f"Prompt template '{template_name}' not found")

def get_error_message(error_type: str, language: Language = Language.CHINESE, **kwargs) -> str:
    """获取错误消息"""
    if error_type in ERROR_MESSAGES:
        return ERROR_MESSAGES[error_type].format(language, **kwargs)
    return ERROR_MESSAGES["api_error"].format(language, error=f"Unknown error: {error_type}")

def get_success_message(success_type: str, language: Language = Language.CHINESE, **kwargs) -> str:
    """获取成功消息"""
    if success_type in SUCCESS_MESSAGES:
        return SUCCESS_MESSAGES[success_type].format(language, **kwargs)
    return f"Operation completed successfully."

# 语言检测
def detect_language(text: str) -> Language:
    """简单的语言检测"""
    # 统计中文字符
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    total_chars = len(text.replace(' ', ''))
    
    if total_chars == 0:
        return Language.CHINESE
    
    chinese_ratio = chinese_chars / total_chars
    
    # 如果中文字符占比超过30%，认为是中文
    return Language.CHINESE if chinese_ratio > 0.3 else Language.ENGLISH

if __name__ == "__main__":
    # 测试prompt系统
    print("=== Testing Prompt System ===")
    
    # 测试默认系统prompt
    zh_prompt = DEFAULT_SYSTEM_PROMPT.get(Language.CHINESE)
    en_prompt = DEFAULT_SYSTEM_PROMPT.get(Language.ENGLISH)
    print(f"Chinese prompt length: {len(zh_prompt)}")
    print(f"English prompt length: {len(en_prompt)}")
    
    # 测试错误消息
    error_msg = get_error_message("field_not_found", Language.CHINESE, field_id=123)
    print(f"Error message: {error_msg}")
    
    # 测试语言检测
    test_texts = [
        "depression相关的字段",
        "What is field 31?",
        "血压测量方法",
        "cardiovascular disease"
    ]
    
    for text in test_texts:
        lang = detect_language(text)
        print(f"'{text}' -> {lang}")