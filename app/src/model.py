import boto3
from langchain_aws.chat_models import ChatBedrockConverse
from src.aws_session import bedrock_client
from dotenv import load_dotenv

load_dotenv()




LLM_MODEL = ChatBedrockConverse(
    model= "arn:aws:bedrock:us-east-1:967255022802:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0",
    provider="bedrock_converse",
    temperature=1,
    max_tokens=None,
    client=bedrock_client
)