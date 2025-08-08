from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import BASE_DIR
import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from src.aws_session import bedrock_client
from langchain_aws import BedrockEmbeddings

load_dotenv()

nest_asyncio.apply()

embeddings = BedrockEmbeddings(client = bedrock_client)
db_path = os.path.join(BASE_DIR, "vector_store/chroma_db")

def get_db_collection(collection_name: str) -> Chroma:
        """
        Factory function to get a Chroma client for a specific collection.
        Loads the persistent database from disk.
        """

        try:
            # Ensure an event loop is running before sensitive initializations
            asyncio.get_running_loop()
        except RuntimeError:  # 'There is no current event loop...'
            # If no loop is running in the current thread, set a new one.
            asyncio.set_event_loop(asyncio.new_event_loop())

        return Chroma(
            collection_name=collection_name,
            persist_directory=db_path,
            embedding_function=embeddings
        )