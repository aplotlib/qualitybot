import streamlit as st
import os
import hashlib
from datetime import datetime
import requests
import json
import io
import tempfile
from pathlib import Path

# Document processing libraries
import PyPDF2
import docx
import pandas as pd
from docx import Document
from docx.shared import Pt

# --- API KEY HANDLING ---
# Try to get API key from Streamlit secrets
try:
    api_key = st.secrets["openai_api_key"]
except (FileNotFoundError, KeyError):
    # If not found in secrets, use environment variable if available
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If not found anywhere, show error
    if not api_key:
        st.error("No API key found. Please set up your OpenAI API key in Streamlit secrets or as an environment variable.")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="质量控制助手 | Quality Control Assistant",
    page_icon="🔍",
    layout="wide"
)

# --- SESSION STATE INITIALIZATION ---
# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'language' not in st.session_state:
    st.session_state.language = "zh"  # Default to Mandarin
    
# Password hash (for "MPFvive8955@#@")
CORRECT_PASSWORD_HASH = "67f49a115b64c1a8affbc851384932f5e3e32a4bcc3a1bf3dd7933a48e4a11c3"

def verify_password(password):
    """Verify the password by comparing hashes"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == CORRECT_PASSWORD_HASH

# Translations dictionary
translations = {
    "app_title": {
        "zh": "质量控制助手",
        "en": "Quality Control Assistant"
    },
    "login": {
        "zh": "登录",
        "en": "Login"
    },
    "password": {
        "zh": "密码",
        "en": "Password"
    },
    "enter_password": {
        "zh": "请输入密码访问系统",
        "en": "Please enter password to access the system"
    },
    "incorrect_password": {
        "zh": "密码不正确，请重试",
        "en": "Incorrect password, please try again"
    },
    "login_button": {
        "zh": "登录系统",
        "en": "Login to System"
    },
    "logout": {
        "zh": "退出登录",
        "en": "Logout"
    },
    "welcome": {
        "zh": "欢迎使用宁海威斐质量控制系统",
        "en": "Welcome to Ninghai Vive Quality Control System"
    },
    "settings": {
        "zh": "设置",
        "en": "Settings"
    },
    "language": {
        "zh": "语言",
        "en": "Language"
    },
    "chinese": {
        "zh": "中文",
        "en": "Chinese"
    },
    "english": {
        "zh": "英文",
        "en": "English"
    },
    "api_key_configured": {
        "zh": "API密钥已配置 ✅",
        "en": "API Key configured ✅"
    },
    "api_key_not_configured": {
        "zh": "API密钥未配置 ⚠️",
        "en": "API Key not configured ⚠️"
    },
    "choose_model": {
        "zh": "选择模型",
        "en": "Choose a model"
    },
    "temperature": {
        "zh": "温度",
        "en": "Temperature"
    },
    "temperature_help": {
        "zh": "较高的值使输出更随机，较低的值使输出更确定",
        "en": "Higher values make output more random, lower values more deterministic"
    },
    "max_response_length": {
        "zh": "最大响应长度",
        "en": "Maximum response length"
    },
    "max_response_length_help": {
        "zh": "响应中的最大标记数",
        "en": "Maximum number of tokens in the response"
    },
    "new_conversation": {
        "zh": "新对话",
        "en": "New Conversation"
    },
    "download_conversation": {
        "zh": "下载对话",
        "en": "Download Conversation"
    },
    "chat_bot": {
        "zh": "聊天机器人 🤖",
        "en": "Chat Bot 🤖"
    },
    "document_translator": {
        "zh": "文档翻译 🔄",
        "en": "Document Translator 🔄"
    },
    "quality_assistant": {
        "zh": "您的质量相关问题和任务的AI助手。",
        "en": "Your AI assistant for quality-related questions and tasks."
    },
    "sop_library": {
        "zh": "SOP标准库 📚",
        "en": "SOP Library 📚"
    },
    "faq": {
        "zh": "常见问题 ❓",
        "en": "FAQ ❓"
    },
    "your_message": {
        "zh": "您的消息：",
        "en": "Your message:"
    },
    "send": {
        "zh": "发送",
        "en": "Send"
    },
    "thinking": {
        "zh": "思考中...",
        "en": "Thinking..."
    },
    "greeting": {
        "zh": "👋 您好！请尝试向我询问有关质量控制的问题：",
        "en": "👋 Hello! Please try asking me questions about quality control:"
    },
    "sample_question1": {
        "zh": "如何测试转移吊带？",
        "en": "How do I test transfer slings?"
    },
    "sample_question2": {
        "zh": "抽样检验水平是什么？",
        "en": "What is the sampling inspection level?"
    },
    "sample_question3": {
        "zh": "发现缺陷时应该怎么做？",
        "en": "What should I do when I find defects?"
    },
    "sample_question4": {
        "zh": "我们的AQL标准是什么？",
        "en": "What are our AQL standards?"
    },
    "contact_alex": {
        "zh": "如有不确定，请联系质量经理Alex: alexander.popoff@vivehealth.com",
        "en": "When in doubt, contact Quality Manager Alex: alexander.popoff@vivehealth.com"
    },
    "supported_file_formats": {
        "zh": "支持的文件格式：",
        "en": "Supported file formats:"
    },
    "choose_document": {
        "zh": "选择要翻译的文档",
        "en": "Choose a document to translate"
    },
    "source_language": {
        "zh": "源语言",
        "en": "Source Language"
    },
    "target_language": {
        "zh": "目标语言",
        "en": "Target Language"
    },
    "output_format": {
        "zh": "输出格式",
        "en": "Output Format"
    },
    "process_translate": {
        "zh": "处理并翻译",
        "en": "Process and Translate"
    },
    "auto_detect": {
        "zh": "自动检测",
        "en": "Auto-detect"
    },
    "text": {
        "zh": "文本",
        "en": "Text"
    },
    "docx": {
        "zh": "DOCX",
        "en": "DOCX"
    },
    "processing_document": {
        "zh": "正在处理文档...",
        "en": "Processing document..."
    },
    "select_sop": {
        "zh": "选择SOP标准",
        "en": "Select SOP Standard"
    },
    "all_sops": {
        "zh": "所有SOP",
        "en": "All SOPs"
    },
    "search_sops": {
        "zh": "搜索SOP",
        "en": "Search SOPs"
    },
    "no_results": {
        "zh": "没有找到结果",
        "en": "No results found"
    },
    "faq_search": {
        "zh": "搜索常见问题",
        "en": "Search FAQs"
    },
    "section": {
        "zh": "章节",
        "en": "Section"
    },
    "show_all": {
        "zh": "显示全部",
        "en": "Show All"
    },
    "testing": {
        "zh": "测试",
        "en": "Testing"
    },
    "inspection": {
        "zh": "检验",
        "en": "Inspection"
    },
    "materials": {
        "zh": "材料",
        "en": "Materials"
    },
    "by_vive": {
        "zh": "宁海威斐质量控制系统",
        "en": "Ninghai Vive Quality Control System"
    },
    "tooltips": {
        "aql": {
            "zh": "可接受质量限（AQL）是指在抽样检验中被认为可接受的最大缺陷率。对于安全关键产品，我们的AQL为0.1%，这意味着批次中几乎不允许有缺陷。",
            "en": "Acceptable Quality Limit (AQL) is the maximum defect rate considered acceptable in a sampling inspection. For safety-critical products, our AQL is 0.1%, meaning virtually no defects are allowed in a batch."
        },
        "inspection_level": {
            "zh": "检验水平决定了要检验的样品数量。S-1是基本水平，S-2是中等水平，S-3是最严格的水平，用于最关键的安全产品。",
            "en": "Inspection level determines the number of samples to inspect. S-1 is basic level, S-2 is intermediate, and S-3 is the most rigorous level used for the most critical safety products."
        },
        "load_test": {
            "zh": "负载测试通过施加产品最大额定重量的特定百分比来测试产品的强度和耐久性。例如，120%负载测试意味着测试产品承受其额定最大重量的120%。",
            "en": "Load testing examines product strength and durability by applying a specific percentage of the product's maximum rated weight. For example, 120% load test means testing the product at 120% of its rated maximum weight."
        }
    }
}

# Helper function to get translated text
def t(key):
    if key in translations:
        return translations[key][st.session_state.language]
    return key

# --- SOP KNOWLEDGE BASE ---
sop_knowledge_base = {
    "groups": {
        "en": [
            {
                "name": "GROUP 1: HIGH LOAD TRANSFER PRODUCTS",
                "description": "S-3 Level, 408kg load, 20 min test, 0.1% AQL",
                "products": [
                    "Transfer Sling (MI487/LVA2056BLK)",
                    "Transfer Blanket Small (MI621/MOB1022WHTLS)",
                    "Transfer Blanket with Handles (MI624/LVA2000)",
                    "Lift Sling with Opening (MI645/LVA2057BLU)",
                    "Wooden Transfer Board (RHB1037WOOD/L)",
                    "Core Hydraulic Patient Lift (MOB1120)",
                    "Hydraulic Patient Lift Systems (MOB1068PMP, MOB1068SLG)",
                    "Transfer Blanket Large (MI621-L/MOB1022WHTL)"
                ]
            },
            {
                "name": "GROUP 2: SUPPORT DEVICES",
                "description": "S-2 Level, 0.1% AQL, 5 min test",
                "products": [
                    "Car Assist Handle (MI474/LVA2098) - 137kg",
                    "Portable Stand Assist (MI524-LVA3016BLK) - 115kg"
                ]
            },
            {
                "name": "GROUP 3: PERSONAL SUPPORT ITEM",
                "description": "S-1 Level, 0.1% AQL",
                "products": [
                    "Transfer Harness (MI471/RHB1054) - 181kg, 5 min - 4 handles each test, switch handles",
                    "All Transfer Belts, including: leg transfer, easy clean transfer, heavy duty transfer with leg straps - 225kg, 5 min"
                ]
            }
        ],
        "zh": [
            {
                "name": "第一组：高负载转移产品",
                "description": "S-3级别, 408kg负载, 20分钟测试, 0.1% AQL",
                "products": [
                    "转移吊带 (MI487/LVA2056BLK)",
                    "小号转移床单 (MI621/MOB1022WHTLS)",
                    "带把手转移床单 (MI624/LVA2000)",
                    "开孔提升吊带 (MI645/LVA2057BLU)",
                    "木质转移板 (RHB1037WOOD/L)",
                    "核心液压病人升降机 (MOB1120)",
                    "液压病人升降系统 (MOB1068PMP, MOB1068SLG)",
                    "大号转移床单 (MI621-L/MOB1022WHTL)"
                ]
            },
            {
                "name": "第二组：支撑设备",
                "description": "S-2级别, 0.1% AQL, 5分钟测试",
                "products": [
                    "汽车辅助拉手 (MI474/LVA2098) - 137kg",
                    "便携式站立辅助器 (MI524-LVA3016BLK) - 115kg"
                ]
            },
            {
                "name": "第三组：个人支撑物品",
                "description": "S-1级别, 0.1% AQL",
                "products": [
                    "转移背带 (MI471/RHB1054) - 181kg, 5分钟 - 每次测试4个把手，轮换把手",
                    "所有转移带，包括：腿部转移带，易清洁转移带，重型转移带带腿带 - 225kg, 5分钟"
                ]
            }
        ]
    },
    "materials": {
        "en": [
            {
                "material": "Straps/Webbing",
                "test_method": "Visual + 120% load test",
                "sample_size": "Per product inspection level",
                "acceptance": "No tears/deformation"
            },
            {
                "material": "Hardware",
                "test_method": "Visual + 120% load test",
                "sample_size": "Per product inspection level",
                "acceptance": "No breakage"
            },
            {
                "material": "Fabric/Mesh",
                "test_method": "Visual + 100% load test",
                "sample_size": "Per product inspection level",
                "acceptance": "No tears"
            }
        ],
        "zh": [
            {
                "material": "织带/带子",
                "test_method": "目视 + 120%负载测试",
                "sample_size": "按产品检验级别",
                "acceptance": "无撕裂/变形"
            },
            {
                "material": "硬件",
                "test_method": "目视 + 120%负载测试",
                "sample_size": "按产品检验级别",
                "acceptance": "无断裂"
            },
            {
                "material": "面料/网布",
                "test_method": "目视 + 100%负载测试",
                "sample_size": "按产品检验级别",
                "acceptance": "无撕裂"
            }
        ]
    },
    "products": {
        "en": [
            {"product": "Transfer Sling", "item_number": "MI487/LVA2056BLK", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Car Assist Handle", "item_number": "MI474/LVA2098", "test_load": "137 kg", "test_method": "Pull test", "aql": "0.1%", "inspection_level": "Special Level S-2", "test_time": "5 min"},
            {"product": "Transfer Blanket Small", "item_number": "MI621/MOB1022WHTLS", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Transfer Blanket with Handles", "item_number": "MI624/LVA2000", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Lift Sling with Opening", "item_number": "MI645/LVA2057BLU", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Transfer Blanket Large", "item_number": "MI621-L/MOB1022WHTL", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Transfer Harness", "item_number": "MI471/RHB1054", "test_load": "181 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-1", "test_time": "5 min"},
            {"product": "Portable Stand Assist", "item_number": "MI524-LVA3016BLK", "test_load": "115 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-2", "test_time": "5 min"},
            {"product": "Wooden Transfer Board", "item_number": "RHB1037WOOD/L", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Core Hydraulic Patient Lift", "item_number": "MOB1120", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Hydraulic Patient Lift Pump", "item_number": "MOB1068PMP", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"},
            {"product": "Hydraulic Patient Lift With Sling", "item_number": "MOB1068SLG", "test_load": "408 kg", "test_method": "Static load", "aql": "0.1%", "inspection_level": "Special Level S-3", "test_time": "20 min"}
        ],
        "zh": [
            {"product": "转移吊带", "item_number": "MI487/LVA2056BLK", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "汽车辅助拉手", "item_number": "MI474/LVA2098", "test_load": "137 kg", "test_method": "拉力测试", "aql": "0.1%", "inspection_level": "特殊等级 S-2", "test_time": "5 分钟"},
            {"product": "小号转移床单", "item_number": "MI621/MOB1022WHTLS", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "带把手转移床单", "item_number": "MI624/LVA2000", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "开孔提升吊带", "item_number": "MI645/LVA2057BLU", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "大号转移床单", "item_number": "MI621-L/MOB1022WHTL", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "转移背带", "item_number": "MI471/RHB1054", "test_load": "181 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-1", "test_time": "5 分钟"},
            {"product": "便携式站立辅助器", "item_number": "MI524-LVA3016BLK", "test_load": "115 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-2", "test_time": "5 分钟"},
            {"product": "木质转移板", "item_number": "RHB1037WOOD/L", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "核心液压病人升降机", "item_number": "MOB1120", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "液压病人升降泵", "item_number": "MOB1068PMP", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"},
            {"product": "带吊带的液压病人升降机", "item_number": "MOB1068SLG", "test_load": "408 kg", "test_method": "静态负载", "aql": "0.1%", "inspection_level": "特殊等级 S-3", "test_time": "20 分钟"}
        ]
    },
    "defect_handling": {
        "en": {
            "title": "Defect Handling Procedures",
            "steps": [
                "1. Reinspect the lot at next higher inspection level. E.g., S-2 becomes S-3 if defects exceed AQL, and 0.1% AQL essentially means zero defects for normal batch sizes.",
                "2. Contact material vendors if defects are traced to incoming raw materials rather than MPF workmanship.",
                "3. Adjust inspection for small orders to maintain inventory, with safeguards.",
                "4. For raw materials: Check +10 samples per 1000 units. Cosmetic flaws acceptable; safety defects reject batch."
            ],
            "risk_adjustments": [
                "No relaxation for most critical products (e.g., patient lift slings).",
                "Acceptable for lower-risk products (e.g., transfer belts) if defects are isolated and safe units can be confirmed."
            ]
        },
        "zh": {
            "title": "缺陷处理程序",
            "steps": [
                "1. 使用更高检验水平重新检验批次。例如，如果缺陷超过AQL，S-2变为S-3，0.1%的AQL实际上意味着对于正常批量大小的零缺陷。",
                "2. 如果发现问题源于原材料而非MPF工艺，将联系材料供应商。",
                "3. 针对小批量订单，为保证库存，可以根据产品风险调整检验。",
                "4. 对于原材料：每1000单位增加检查10个样品。外观瑕疵可接受；安全缺陷拒收批次。"
            ],
            "risk_adjustments": [
                "高风险产品（例如病人移位吊带）不放宽要求。",
                "低风险产品（例如转移腰带），若能在重新检验中隔离出安全产品，可适当放宽。"
            ]
        }
    }
}

# --- FAQ DATA ---
faq_data = {
    "en": [
        {
            "question": "What load testing is required for transfer slings?",
            "answer": "Transfer slings (MI487/LVA2056BLK) require S-3 level inspection with a 408kg static load test for 20 minutes. The AQL is 0.1%, which essentially means zero defects for normal batch sizes.",
            "category": "Testing"
        },
        {
            "question": "What does '120% load test' mean for material testing?",
            "answer": "The 120% load test refers to testing materials at 120% of the advertised maximum weight for the product. For example, if a product's advertised maximum weight is 200kg, the materials should be tested at 240kg.",
            "category": "Testing"
        },
        {
            "question": "How long should I test Group 1 products?",
            "answer": "All Group 1 (High Load Transfer Products) should be tested for 20 minutes under static load conditions at 408kg.",
            "category": "Testing"
        },
        {
            "question": "What's the AQL standard for our safety products?",
            "answer": "All critical safety products use an AQL of 0.1%, which essentially means zero defects are allowed for normal batch sizes. This strict standard applies to all products across Groups 1, 2, and 3.",
            "category": "Inspection"
        },
        {
            "question": "What inspection level should I use for Car Assist Handles?",
            "answer": "Car Assist Handles (MI474/LVA2098) should use Special Level S-2 inspection at 0.1% AQL with a 137kg pull test for 5 minutes.",
            "category": "Inspection"
        },
        {
            "question": "What should I do if I find a defect during inspection?",
            "answer": "If a defect is found: 1) Reinspect the lot at the next higher inspection level (e.g., S-2 becomes S-3). 2) Contact material vendors if defects are traced to incoming materials. 3) For high-risk products like patient lift slings, no relaxation of standards is allowed. 4) For lower-risk products, if defects are isolated and safe units can be confirmed, some adjustments may be acceptable. Always inform Quality Manager Alex if you're uncertain.",
            "category": "Inspection"
        },
        {
            "question": "How should I test transfer harnesses?",
            "answer": "Transfer Harnesses (MI471/RHB1054) require Special Level S-1 inspection at 0.1% AQL. Use a 181kg static load test for 5 minutes. Test 4 handles each time and switch handles during the test.",
            "category": "Testing"
        },
        {
            "question": "What are the material testing requirements before production?",
            "answer": "Before production, test critical components using the same sampling level as the final product: 1) Straps/Webbing: Visual + 120% load test with no tears/deformation allowed. 2) Hardware: Visual + 120% load test with no breakage allowed. 3) Fabric/Mesh: Visual + 100% load test with no tears allowed.",
            "category": "Materials"
        },
        {
            "question": "Can I adjust inspection standards for small orders?",
            "answer": "For small orders, adjustments can be made to maintain inventory, but with safeguards: 1) No relaxation for high-risk products like patient lift slings. 2) For lower-risk products like transfer belts, relaxation may be acceptable if defects are isolated and safe units can be confirmed through reinspection. Always prioritize safety over inventory concerns.",
            "category": "Inspection"
        },
        {
            "question": "What should I do with products after destructive testing?",
            "answer": "All safety device load testing is considered destructive. Products that undergo load testing should not be sold after testing, as the structural integrity may be compromised even if no visible damage is present.",
            "category": "Testing"
        },
        {
            "question": "How do I handle material defects versus workmanship defects?",
            "answer": "If defects are traced to incoming raw materials rather than MPF workmanship, contact the material vendors immediately. For raw materials, check +10 samples per 1000 units if defects are found. Cosmetic flaws in materials may be acceptable, but safety defects require rejecting the entire batch.",
            "category": "Materials"
        },
        {
            "question": "What sampling plan should I use for critical safety products?",
            "answer": "For critical safety products with a 0.1% AQL, use the Special Inspection Level corresponding to the product group: S-3 for Group 1 products, S-2 for Group 2 products, and S-1 for Group 3 products. Refer to the AQL sampling chart to determine the exact sample size based on lot size. With a 0.1% AQL, essentially zero defects are allowed for normal batch sizes.",
            "category": "Inspection"
        }
    ],
    "zh": [
        {
            "question": "转移吊带需要什么负载测试？",
            "answer": "转移吊带（MI487/LVA2056BLK）需要S-3级别检验，进行408kg静态负载测试，持续20分钟。AQL为0.1%，这对于正常批量大小实际上意味着零缺陷。",
            "category": "Testing"
        },
        {
            "question": "材料测试中的'120%负载测试'是什么意思？",
            "answer": "120%负载测试是指在产品宣传的最大承重的120%下测试材料。例如，如果产品宣传的最大承重是200kg，则材料应在240kg下测试。",
            "category": "Testing"
        },
        {
            "question": "第一组产品应该测试多长时间？",
            "answer": "所有第一组（高负载转移产品）应在408kg静态负载条件下测试20分钟。",
            "category": "Testing"
        },
        {
            "question": "我们安全产品的AQL标准是什么？",
            "answer": "所有关键安全产品使用0.1%的AQL，这实际上意味着对于正常批量大小不允许有缺陷。这一严格标准适用于第1、2、3组的所有产品。",
            "category": "Inspection"
        },
        {
            "question": "汽车辅助拉手应该使用什么检验水平？",
            "answer": "汽车辅助拉手（MI474/LVA2098）应使用特殊等级S-2检验，AQL为0.1%，进行137kg拉力测试，持续5分钟。",
            "category": "Inspection"
        },
        {
            "question": "如果在检验过程中发现缺陷，我应该怎么做？",
            "answer": "如果发现缺陷：1）使用更高检验水平重新检验批次（例如，S-2变为S-3）。2）如果发现问题源于原材料，联系材料供应商。3）对于高风险产品如病人升降吊带，不允许放宽标准。4）对于较低风险产品，如果缺陷是孤立的且能确认安全单元，可能接受一些调整。如有不确定，请务必通知质量经理Alex。",
            "category": "Inspection"
        },
        {
            "question": "我应该如何测试转移背带？",
            "answer": "转移背带（MI471/RHB1054）需要特殊等级S-1检验，AQL为0.1%。使用181kg静态负载测试，持续5分钟。每次测试4个把手，并在测试过程中轮换把手。",
            "category": "Testing"
        },
        {
            "question": "生产前的材料测试要求是什么？",
            "answer": "生产前，使用与最终产品相同的抽样水平测试关键组件：1）织带/带子：目视+120%负载测试，不允许有撕裂/变形。2）硬件：目视+120%负载测试，不允许有断裂。3）面料/网布：目视+100%负载测试，不允许有撕裂。",
            "category": "Materials"
        },
        {
            "question": "我可以为小订单调整检验标准吗？",
            "answer": "对于小订单，可以进行调整以维持库存，但需要安全措施：1）高风险产品如病人升降吊带不允许放宽要求。2）对于较低风险产品如转移腰带，如果缺陷是孤立的且能通过重新检验确认安全单元，可以接受适当放宽。始终将安全置于库存考虑之上。",
            "category": "Inspection"
        },
        {
            "question": "破坏性测试后的产品应该如何处理？",
            "answer": "所有安全设备负载测试被视为破坏性测试。经过负载测试的产品不应在测试后销售，因为即使没有可见损坏，其结构完整性也可能已经受损。",
            "category": "Testing"
        },
        {
            "question": "如何处理材料缺陷与工艺缺陷？",
            "answer": "如果发现缺陷源于原材料而非MPF工艺，立即联系材料供应商。对于原材料，如果发现缺陷，每1000单位增加检查10个样品。材料的外观瑕疵可能可以接受，但安全缺陷需要拒收整批。",
            "category": "Materials"
        },
        {
            "question": "关键安全产品应该使用什么抽样计划？",
            "answer": "对于AQL为0.1%的关键安全产品，使用与产品组对应的特殊检验水平：第1组产品使用S-3，第2组产品使用S-2，第3组产品使用S-1。参考AQL抽样表，根据批量大小确定准确的样本大小。对于0.1%的AQL，正常批量大小实际上不允许有缺陷。",
            "category": "Inspection"
        }
    ]
}

# --- STYLES ---
st.markdown("""
<style>
    /* Login styles */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .login-title {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        color: #0d47a1;
    }
    .login-button {
        background-color: #4285F4;
        color: white;
        padding: 0.6rem 1.2rem;
        border-radius: 4px;
        border: none;
        font-size: 1rem;
        cursor: pointer;
        margin-top: 1rem;
    }
    .login-error {
        color: #d32f2f;
        margin-top: 1rem;
    }
    
    /* Chat styles */
    .chat-message {
        padding: 1.5rem; 
        border-radius: 0.5rem; 
        margin-bottom: 1rem; 
        display: flex;
        flex-direction: row;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #f0f2f6;
    }
    .chat-message.assistant {
        background-color: #e3f2fd;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        margin-right: 1rem;
        border-radius: 50%;
        object-fit: cover;
    }
    .chat-message .message {
        flex: 1;
    }
    .stTextInput input {
        padding: 0.5rem !important;
        font-size: 1rem !important;
    }
    .floating-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    .sidebar .block-container {
        padding-top: 2rem;
    }
    .main-tabs .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .main-tabs .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding: 10px 16px;
        margin-right: 4px;
    }
    .main-tabs .stTabs [aria-selected="true"] {
        background-color: #e3f2fd;
        border-bottom: 2px solid #4285F4;
    }
    .progress-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 20px;
    }
    .faq-item {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    .faq-question {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .faq-answer {
        font-size: 1rem;
    }
    .faq-category {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .category-Testing {
        background-color: #e3f2fd;
        color: #0d47a1;
    }
    .category-Inspection {
        background-color: #e8f5e9;
        color: #1b5e20;
    }
    .category-Materials {
        background-color: #fff3e0;
        color: #e65100;
    }
    .contact-alex {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffebee;
        color: #c62828;
        font-weight: bold;
    }
    .critical-product {
        font-weight: bold;
        color: #c62828;
    }
    .search-box {
        margin-bottom: 1rem;
    }
    .sop-table {
        width: 100%;
        border-collapse: collapse;
    }
    .sop-table th, .sop-table td {
        padding: 0.5rem;
        text-align: left;
        border: 1px solid #e0e0e0;
    }
    .sop-table th {
        background-color: #f0f2f6;
    }
    .language-toggle {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- DIRECT API CALL FUNCTION ---
def call_openai_api(messages, model, temperature, max_tokens, api_key):
    """Call OpenAI API directly using requests to avoid client issues"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        error_message = f"API Error: {response.status_code} - {response.text}"
        raise Exception(error_message)

# --- DOCUMENT PROCESSING FUNCTIONS ---
def extract_text_from_pdf(file):
    """Extract text from a PDF file"""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    num_pages = len(pdf_reader.pages)
    
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() + "\n\n"
    
    return text, num_pages

def extract_text_from_docx(file):
    """Extract text from a DOCX file"""
    doc = docx.Document(file)
    full_text = []
    
    for para in doc.paragraphs:
        full_text.append(para.text)
    
    return "\n".join(full_text), len(doc.paragraphs)

def extract_text_from_txt(file):
    """Extract text from a TXT file"""
    text = file.getvalue().decode("utf-8")
    lines = text.split("\n")
    return text, len(lines)

def extract_text_from_csv(file):
    """Extract text from a CSV file"""
    df = pd.read_csv(file)
    csv_text = df.to_csv(index=False)
    return csv_text, len(df)

def extract_text_from_xlsx(file):
    """Extract text from an Excel file"""
    df = pd.read_excel(file)
    excel_text = df.to_csv(index=False)
    return excel_text, len(df)

def process_document(uploaded_file):
    """Process the uploaded document and extract text"""
    file_extension = Path(uploaded_file.name).suffix.lower()
    
    if file_extension == ".pdf":
        text, pages = extract_text_from_pdf(uploaded_file)
    elif file_extension == ".docx":
        text, pages = extract_text_from_docx(uploaded_file)
    elif file_extension == ".txt":
        text, pages = extract_text_from_txt(uploaded_file)
    elif file_extension == ".csv":
        text, pages = extract_text_from_csv(uploaded_file)
    elif file_extension in [".xlsx", ".xls"]:
        text, pages = extract_text_from_xlsx(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")
    
    return text, pages

def translate_text(text, source_lang, target_lang, model, temperature, api_key, progress_bar=None, status_text=None):
    """Translate text using OpenAI API"""
    
    # Split the text into chunks (approx 4000 tokens per chunk)
    chunk_size = 4000  # Adjust based on token limits
    chunks = []
    words = text.split()
    current_chunk = []
    current_chunk_size = 0
    
    for word in words:
        current_chunk_size += len(word) + 1  # +1 for space
        if current_chunk_size > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_chunk_size = len(word) + 1
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    translated_chunks = []
    total_chunks = len(chunks)
    
    if progress_bar is not None:
        progress_bar.empty()
        progress_bar.progress(0)
    
    for i, chunk in enumerate(chunks):
        if status_text is not None:
            status_text.text(f"Translating chunk {i+1}/{total_chunks}...")
        
        messages = [
            {"role": "system", "content": f"You are a professional translator. Translate the following text from {source_lang} to {target_lang}. Maintain the original formatting as much as possible."},
            {"role": "user", "content": chunk}
        ]
        
        translated_chunk = call_openai_api(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=4096,  # Maximum allowed by API
            api_key=api_key
        )
        
        translated_chunks.append(translated_chunk)
        
        if progress_bar is not None:
            progress_bar.progress((i + 1) / total_chunks)
    
    if status_text is not None:
        status_text.text("Translation completed!")
    
    return "\n".join(translated_chunks)

def create_docx_from_text(text, filename):
    """Create a DOCX file from text"""
    doc = Document()
    
    # Add styles
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Split text by paragraphs and add to document
    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.strip():  # Skip empty paragraphs
            doc.add_paragraph(para)
    
    # Save to a BytesIO object
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    return doc_io

# --- SIDEBAR ---
if st.session_state.authenticated:
    with st.sidebar:
        st.title(t("settings"))
        
        # Language selector
        st.markdown('<div class="language-toggle">', unsafe_allow_html=True)
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇨🇳 " + t("chinese"), use_container_width=True):
                st.session_state.language = "zh"
                st.rerun()
        with lang_col2:
            if st.button("🇺🇸 " + t("english"), use_container_width=True):
                st.session_state.language = "en"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Logout button
        if st.button(t("logout"), type="primary"):
            st.session_state.authenticated = False
            st.rerun()
    
    # API Key Status
    if api_key:
        st.success(t("api_key_configured"))
    else:
        st.warning(t("api_key_not_configured"))
    
    # Model Selection
    model = st.selectbox(
        t("choose_model"),
        ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"],
        index=1  # Default to gpt-4o for better quality
    )
    
    # Temperature Slider
    temperature = st.slider(
        t("temperature"),
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help=t("temperature_help")
    )
    
    # Maximum Length
    max_tokens = st.slider(
        t("max_response_length"),
        min_value=256,
        max_value=4096,
        value=1024,
        step=256,
        help=t("max_response_length_help")
    )
    
    # Reset Conversation
    if st.button(t("new_conversation")):
        if "messages" in st.session_state:
            st.session_state.messages = []
        st.rerun()
    
    # Download Conversation
    if "messages" in st.session_state and st.session_state.messages:
        if st.button(t("download_conversation")):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.txt"
            
            content = ""
            for msg in st.session_state.messages:
                content += f"{msg['role'].title()}: {msg['content']}\n\n"
            
            st.download_button(
                label=t("download_conversation"),
                data=content,
                file_name=filename,
                mime="text/plain"
            )

    st.markdown("---")
    st.markdown(t("by_vive"))

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create system message with SOP information
sop_system_message = f"""You are a Quality Control Assistant for Vive Health. Your primary role is to help the quality team in the Ninghai, China facility with questions about quality control procedures, especially regarding critical safety products.

Use this information from our SOPs:

PRODUCT GROUPS:
Group 1 (S-3 Level, 408kg load, 20 min test): Transfer Sling, Transfer Blanket Small, Transfer Blanket with Handles, Lift Sling with Opening, Wooden Transfer Board, Core Hydraulic Patient Lift, Hydraulic Patient Lift Systems, Transfer Blanket Large
Group 2 (S-2 Level, 5 min test): Car Assist Handle (137kg), Portable Stand Assist (115kg)
Group 3 (S-1 Level): Transfer Harness (181kg, 5 min, 4 handles each test, switch handles), All Transfer Belts (225kg, 5 min)

MATERIAL TESTING:
- Straps/Webbing: Visual + 120% load test, no tears/deformation allowed
- Hardware: Visual + 120% load test, no breakage allowed
- Fabric/Mesh: Visual + 100% load test, no tears allowed

DEFECT HANDLING:
1. Reinspect at higher level (S-2 becomes S-3)
2. Contact vendors for material defects
3. For small orders, adjust based on risk (no relaxation for critical products)
4. For raw materials: Check +10 samples per 1000 units

All safety products use 0.1% AQL (zero defects for normal batches).
Load tested products should not be sold after testing.

IMPORTANT NOTES:
- If asked about defects, remind users they must ALWAYS contact Alex if they find safety-critical defects.
- For high-risk products (patient lift slings, transfer boards), NO relaxation of standards is allowed under any circumstances.
- 120% load test means testing at 120% of the advertised maximum weight for the product.
- Always provide clear, simple explanations suitable for non-native English speakers.
- If you're unsure about any detail, ALWAYS recommend contacting Quality Manager Alex (alexander.popoff@vivehealth.com).

Respond in the same language the user uses (Chinese or English). For Mandarin responses, use simple, clear language appropriate for manufacturing staff in Ninghai, China.
"""

# --- LOGIN SCREEN ---
# Display login screen if not authenticated
if not st.session_state.authenticated:
    st.markdown(f"""
    <div class="login-container">
        <div class="login-title">{t("welcome")}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input(
            t("password"), 
            type="password", 
            placeholder=t("enter_password"),
            help="请输入管理员提供的访问密码 | Please enter the access password provided by your administrator"
        )
        
        if st.button(t("login_button"), use_container_width=True):
            if verify_password(password_input):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error(t("incorrect_password"))
                
        st.image("https://api.dicebear.com/7.x/bottts/svg?seed=gpt", width=150)

# --- MAIN CONTENT WITH TABS ---
if st.session_state.authenticated:
    st.markdown('<div class="main-tabs">', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs([t("chat_bot"), t("document_translator"), t("sop_library"), t("faq")])
    st.markdown('</div>', unsafe_allow_html=True)

with tab1:
    # Only show content if authenticated
    if st.session_state.authenticated:
        # --- HEADER ---
        st.header(t("app_title") + " 🤖")
        st.markdown(t("quality_assistant"))
    
    # --- DISPLAY CHAT MESSAGES ---
    for message in st.session_state.messages:
        with st.container():
            st.markdown(f"""
            <div class="chat-message {message['role']}">
                <img class="avatar" src="{'https://api.dicebear.com/7.x/bottts/svg?seed=gpt' if message['role'] == 'assistant' else 'https://api.dicebear.com/7.x/personas/svg?seed=user'}" />
                <div class="message">
                    <p>{message['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # --- INPUT AREA ---
    with st.container():
        input_container = st.container()
        
        with input_container:
            user_input = st.text_area(t("your_message"), key="user_input", height=100)
            col1, col2 = st.columns([6, 1])
            
            with col2:
                submit_button = st.button(t("send"))
    
    # --- PROCESS INPUT ---
    if submit_button and user_input:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Check if API key is available
        if not api_key:
            st.error("API Key not configured. Please set up secrets for this application.")
        else:
            # Call OpenAI API directly without using the client library
            try:
                with st.spinner(t("thinking")):
                    # Create messages array for API
                    messages = [
                        {"role": "system", "content": sop_system_message}
                    ]
                    
                    # Add previous messages
                    for m in st.session_state.messages:
                        messages.append({"role": m["role"], "content": m["content"]})
                    
                    # Direct API call
                    assistant_response = call_openai_api(
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        api_key=api_key
                    )
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                    
                    # Rerun to update UI
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Add sample questions or suggestions
    if len(st.session_state.messages) == 0:
        st.info(t("greeting"))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("- " + t("sample_question1"))
            st.markdown("- " + t("sample_question2"))
        with col2:
            st.markdown("- " + t("sample_question3"))
            st.markdown("- " + t("sample_question4"))
        
        st.markdown(f'<div class="contact-alex">{t("contact_alex")}</div>', unsafe_allow_html=True)

with tab2:
    # Only show content if authenticated
    if st.session_state.authenticated:
        st.header(t("document_translator") + " 🔄")
        st.markdown("上传大型文档（最多100多页）并将其翻译成任何语言。 | Upload large documents (up to 100+ pages) and translate them to any language.")
    
    # File upload
    uploaded_file = st.file_uploader(t("choose_document"), 
                                     type=["pdf", "docx", "txt", "csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / (1024*1024):.2f} MB"
        }
        st.write(file_details)
        
        # Translation settings
        col1, col2 = st.columns(2)
        with col1:
            source_language = st.selectbox(
                t("source_language"),
                [t("auto_detect"), "English", "Spanish", "French", "German", "Chinese", 
                 "Japanese", "Korean", "Russian", "Arabic", "Portuguese", "Italian"]
            )
        with col2:
            target_language = st.selectbox(
                t("target_language"),
                ["English", "Spanish", "French", "German", "Chinese", 
                 "Japanese", "Korean", "Russian", "Arabic", "Portuguese", "Italian"]
            )
        
        # Output format
        output_format = st.radio(
            t("output_format"),
            [t("text"), t("docx")],
            horizontal=True
        )
        
        # Process and translate button
        if st.button(t("process_translate")):
            if not api_key:
                st.error("API Key not configured. Please set up secrets for this application.")
            else:
                try:
                    # Create progress indicators
                    progress_container = st.container()
                    with progress_container:
                        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                        status_text = st.empty()
                        progress_bar = st.empty()
                        status_text.text(t("processing_document"))
                        progress_bar.progress(0)
                        
                        # Process document
                        text, size_info = process_document(uploaded_file)
                        
                        # Calculate and display stats
                        word_count = len(text.split())
                        char_count = len(text)
                        estimated_tokens = word_count * 1.3  # Rough estimate
                        
                        status_text.text("Document processed! Preparing for translation...")
                        file_type = Path(uploaded_file.name).suffix
                        
                        if file_type == ".pdf":
                            size_desc = f"{size_info} pages"
                        elif file_type == ".docx":
                            size_desc = f"{size_info} paragraphs"
                        elif file_type in [".csv", ".xlsx", ".xls"]:
                            size_desc = f"{size_info} rows"
                        else:
                            size_desc = f"{size_info} lines"
                        
                        st.markdown(f"""
                        **Document Stats:**
                        - {size_desc}
                        - {word_count:,} words
                        - {char_count:,} characters
                        - ~{estimated_tokens:,.0f} estimated tokens
                        """)
                        
                        # Calculate cost and time estimates
                        if model == "gpt-3.5-turbo":
                            cost_estimate = estimated_tokens / 1000 * 0.0010  # $0.0010 per 1K input tokens
                            time_estimate = (estimated_tokens / 4000) * 5  # ~5 seconds per 4K tokens
                        else:  # gpt-4 models
                            cost_estimate = estimated_tokens / 1000 * 0.01  # $0.01 per 1K input tokens
                            time_estimate = (estimated_tokens / 4000) * 10  # ~10 seconds per 4K tokens
                        
                        st.markdown(f"""
                        **Estimated Processing:**
                        - Cost: ~${cost_estimate:.2f}
                        - Time: ~{int(time_estimate)} seconds
                        """)
                        
                        # Translate text
                        status_text.text("Translating document...")
                        translated_text = translate_text(
                            text=text,
                            source_lang=source_language if source_language != t("auto_detect") else "",
                            target_lang=target_language,
                            model=model,
                            temperature=temperature,
                            api_key=api_key,
                            progress_bar=progress_bar,
                            status_text=status_text
                        )
                        
                        status_text.text("Translation completed! Preparing download...")
                        
                        # Prepare download
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        base_filename = f"{Path(uploaded_file.name).stem}_translated_{target_language}_{timestamp}"
                        
                        if output_format == t("text"):
                            st.download_button(
                                label="Download Translated Text",
                                data=translated_text,
                                file_name=f"{base_filename}.txt",
                                mime="text/plain"
                            )
                        else:  # DOCX
                            docx_file = create_docx_from_text(translated_text, base_filename)
                            st.download_button(
                                label="Download Translated DOCX",
                                data=docx_file,
                                file_name=f"{base_filename}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        
                        status_text.text("✅ Translation completed! Download available.")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Show preview
                        with st.expander("Preview Translation"):
                            preview_length = min(2000, len(translated_text))
                            st.text_area(
                                "Translation Preview (first 2000 chars)",
                                translated_text[:preview_length] + ("..." if len(translated_text) > preview_length else ""),
                                height=300
                            )
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    else:
        # Show supported formats when no file is uploaded
        st.info(f"""
        **{t("supported_file_formats")}**
        - PDF (.pdf) - Handles large multi-page documents
        - Word (.docx) - Preserves basic formatting in translation
        - Text (.txt) - Fast processing for plain text
        - Spreadsheets (.csv, .xlsx, .xls) - Translates tabular data
        
        Upload files up to 100+ pages. For best results with very large documents, use GPT-4o.
        """)

with tab3:
    # Only show content if authenticated
    if st.session_state.authenticated:
        st.header(t("sop_library") + " 📚")
    
    # Select SOP category
    sop_category = st.selectbox(
        t("select_sop"),
        [t("all_sops"), t("testing"), t("inspection"), t("materials")]
    )
    
    # Search functionality
    search_query = st.text_input(t("search_sops"), "")
    
    # Display product groups
    st.subheader(t("groups"))
    
    for group in sop_knowledge_base["groups"][st.session_state.language]:
        if (search_query.lower() in group["name"].lower() or 
            search_query.lower() in group["description"].lower() or 
            any(search_query.lower() in product.lower() for product in group["products"]) or
            sop_category == t("all_sops") or 
            (sop_category == t("testing") and "test" in group["description"].lower())):
            
            with st.expander(group["name"], expanded=True):
                st.markdown(f"**{group['description']}**")
                
                # Add tooltip for AQL
                if "AQL" in group["description"]:
                    st.info(translations["tooltips"]["aql"][st.session_state.language])
                
                # Add tooltip for inspection level
                if "S-1" in group["description"] or "S-2" in group["description"] or "S-3" in group["description"]:
                    st.info(translations["tooltips"]["inspection_level"][st.session_state.language])
                
                # Display products with more emphasis on safety-critical items
                for product in group["products"]:
                    if any(critical_item in product for critical_item in ["Patient Lift", "Sling", "Transfer Board"]):
                        st.markdown(f"- <span class='critical-product'>{product}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- {product}")
    
    # Display material testing requirements
    if sop_category == t("all_sops") or sop_category == t("materials") or "material" in search_query.lower():
        st.subheader(t("materials") + " " + t("testing"))
        
        materials_data = sop_knowledge_base["materials"][st.session_state.language]
        
        # Create a DataFrame for better display
        df_materials = pd.DataFrame(materials_data)
        st.table(df_materials)
    
    # Display product testing requirements
    if sop_category == t("all_sops") or sop_category == t("testing") or "test" in search_query.lower():
        st.subheader(t("testing") + " " + t("testing"))
        
        products_data = sop_knowledge_base["products"][st.session_state.language]
        filtered_products = [p for p in products_data if search_query.lower() in p["product"].lower() or not search_query]
        
        if filtered_products:
            # Create a DataFrame for better display
            df_products = pd.DataFrame(filtered_products)
            st.table(df_products)
        else:
            st.info(t("no_results"))
    
    # Display defect handling procedures
    if sop_category == t("all_sops") or sop_category == t("inspection") or "defect" in search_query.lower():
        st.subheader(sop_knowledge_base["defect_handling"][st.session_state.language]["title"])
        
        defect_data = sop_knowledge_base["defect_handling"][st.session_state.language]
        
        for step in defect_data["steps"]:
            st.markdown(f"- {step}")
        
        st.markdown("**Risk-Based Adjustments:**")
        for adj in defect_data["risk_adjustments"]:
            st.markdown(f"- {adj}")

with tab4:
    # Only show content if authenticated
    if st.session_state.authenticated:
        st.header(t("faq") + " ❓")
    
    # Search functionality
    faq_search = st.text_input(t("faq_search"), "")
    
    # Filter by category
    faq_category = st.radio(
        t("section"),
        [t("show_all"), t("testing"), t("inspection"), t("materials")],
        horizontal=True
    )
    
    # Display FAQs
    faqs = faq_data[st.session_state.language]
    
    for faq in faqs:
        # Filter by search query and category
        if ((faq_search.lower() in faq["question"].lower() or 
             faq_search.lower() in faq["answer"].lower()) and
            (faq_category == t("show_all") or 
             faq_category == t(faq["category"]))):
            
            st.markdown(f"""
            <div class="faq-item">
                <div class="faq-question">{faq["question"]}</div>
                <div class="faq-answer">{faq["answer"]}</div>
                <div class="faq-category category-{faq["category"]}">{t(faq["category"])}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Add contact information
    st.markdown(f'<div class="contact-alex">{t("contact_alex")}</div>', unsafe_allow_html=True)

# Add floating help button if authenticated
if st.session_state.authenticated:
    st.markdown("""
    <div class="floating-button">
        <a href="mailto:alexander.popoff@vivehealth.com" target="_blank" style="text-decoration:none;">
            <button style="background-color:#4285F4; color:white; border:none; padding:10px 15px; border-radius:50%; font-size:16px;">
                ?
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
