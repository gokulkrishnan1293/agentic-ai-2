import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

COMMON_LLM_MODEL_NAME = os.getenv("COMMON_LLM_MODEL_NAME", "mistral")

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME","gemini-2.5-pro")

#AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

#DYNAMODB_STATE_TABLE = os.getenv("DYNAMODB_STATE_TABLE", "claim_agent_state_dev")

TOOLING_SERVICE_URL = os.getenv("TOOLING_SERVICE_URL", "http://localhost:8001/api/v1/tools/execute")

PROMPTS_DIR = os.getenv("PROMPTS_DIR", str(BASE_DIR / "prompts"))