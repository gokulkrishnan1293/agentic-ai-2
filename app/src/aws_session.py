import boto3
from botocore.config import Config

def get_bedrock_client():
    """
    Creates and returns a Boto3 client for Bedrock with a robust
    adaptive retry strategy to handle ThrottlingExceptions.
    """
    # Configure the retry strategy.
    retry_config = Config(
        retries={
            'max_attempts': 10, # Try up to 3 times
            'mode': 'adaptive'  # Use smart, exponential backoff
        }
    )
    
    print("--- Initializing Boto3 Bedrock client with adaptive retries ---")
    
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name='us-east-1',
        config=retry_config
    )
    return client

# Create a single, shared client instance for the entire application.
bedrock_client = get_bedrock_client()