"""应用配置：从环境变量读取，区分开发/生产。"""
import os
from dotenv import load_dotenv

# 加载项目根目录的 .env
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # 数据库：默认 SQLite，切 MySQL 只需改 DATABASE_URL
    _db_url = os.getenv("DATABASE_URL", "sqlite:///juben.db")
    if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
        # 相对路径 SQLite 落到项目根目录，避免受工作目录影响
        _name = _db_url.replace("sqlite:///", "")
        _db_url = "sqlite:///" + os.path.join(_BASE_DIR, _name)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 大模型
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

    # 联网搜索
    TENCENT_SEARCH_SID = os.getenv("TENCENT_SEARCH_SID", "")
    TENCENT_SEARCH_SKEY = os.getenv("TENCENT_SEARCH_SKEY", "")

    # COS
    COS_SECRET_ID = os.getenv("COS_SECRET_ID", "")
    COS_SECRET_KEY = os.getenv("COS_SECRET_KEY", "")
    COS_REGION = os.getenv("COS_REGION", "ap-guangzhou")
    COS_BUCKET = os.getenv("COS_BUCKET", "")
    COS_DOMAIN = os.getenv("COS_DOMAIN", "")

    BASE_DIR = _BASE_DIR
