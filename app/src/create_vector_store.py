import os
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from src.config import BASE_DIR,COMMON_LLM_MODEL_NAME,OLLAMA_BASE_URL
import chromadb
import json
from dotenv import load_dotenv
from src.aws_session import bedrock_client
from langchain_aws import BedrockEmbeddings
load_dotenv()


KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
CHROMA_PERSIST_PATH = os.path.join(BASE_DIR, "vector_store/chroma_db")


#print("Initializing embeddings with Google's 'text-embedding-004' model...")


#embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=os.environ.get("GOOGLE_API_KEY"),)

embeddings = BedrockEmbeddings(client = bedrock_client)

client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
#Initialize the ChromaDB client, telling it where to save the data.
#vectorstore = Chroma(embedding_function=embeddings, persist_directory=CHROMA_PERSIST_PATH)
print(f"ChromaDB client initialized. Data will be saved to: {CHROMA_PERSIST_PATH}")

def process_excel_files(directory: str) -> list[Document]:
            """
            Loads Excel files, creates a searchable text block for the page_content,
            and stores the full, structured row data in the metadata.
            """
            documents = []
            for filename in os.listdir(directory):
                if filename.endswith(".xlsx"):
                    file_path = os.path.join(directory, filename)
                    df = pd.read_excel(file_path).fillna('')
                    print(f"  - Loading and processing Excel file: {filename}")

                    for index, row in df.iterrows():
                    # --- THIS IS THE KEY CHANGE ---
                    # 1. Create a concise text block for semantic search from key fields.
                        # This is what the vector embedding will be based on.
                        searchable_content = (
                            f"Intent: {row.get('PrimaryIntent', '')}. "
                            f"Keywords: {row.get('Keywords', '')}. "
                            f"Summary: {row.get('Summary', '')}"
                        )
                        
                        # 2. Convert the entire row to a dictionary, then to a JSON string.
                        # This preserves the full structure.
                        full_row_data_dict = row.to_dict()
                        
                        # 3. Create the metadata object.
                        doc_metadata = {
                            "source": filename,
                            "row": index,
                            # Store the full structured data here.
                            "full_row_json": json.dumps(full_row_data_dict) 
                        }

                        # Create the LangChain Document.
                        doc = Document(
                            page_content=searchable_content, # Use the clean text for search
                            metadata=doc_metadata            # Store the rich data in metadata
                        )
                        documents.append(doc)
            
            return documents

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

def process_text_files(directory: str) -> list[Document]:
        """Loads all .md and .pdf files in a directory."""
        print(f"  - Loading text/pdf files from: {directory}")
        loader = DirectoryLoader(
        directory,
        glob="**/*[.md,.pdf]",
        loader_cls=UnstructuredMarkdownLoader,
        loader_kwargs={"autodetect_encoding": True},
        show_progress=True
        )
        return loader.load()


data_sources = {
"sop": {"processor": process_excel_files, "collection_name": "sops_store"},
"error_code": {"processor": process_excel_files, "collection_name": "errors_store"},
"api_catalog": {"processor": process_excel_files, "collection_name": "apis_store"},
}

for dir_name, source_info in data_sources.items():
    source_path = os.path.join(KNOWLEDGE_BASE_DIR, dir_name)
    collection_name = source_info["collection_name"]
    if os.path.exists(source_path):
        print(f"\nProcessing directory: '{dir_name}' for collection '{collection_name}'...")
        
        # Get or create the collection from the persistent client
        # This is a more explicit and reliable way to work with collections.
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=None # We will handle embeddings manually
        )
        
        documents = source_info["processor"](source_path)
        
        if not documents:
            print(f"  No documents found in '{dir_name}'. Skipping.")
            continue
            
        docs = text_splitter.split_documents(documents)
        print(f"  Split into {len(docs)} chunks.")

        # --- THIS IS THE KEY CHANGE ---
        # We now add to the collection manually, which is more robust.
        
        # Prepare the data for Chroma's `add` method
        contents_to_embed = [doc.page_content for doc in docs]
        metadatas_to_add = [doc.metadata for doc in docs]
        # Create a unique ID for each chunk
        ids_to_add = [f"{collection_name}_{i}" for i in range(len(docs))]

        # Generate embeddings for the content
        print(f"  Generating {len(contents_to_embed)} embeddings...")
        embedded_vectors = embeddings.embed_documents(contents_to_embed)
        
        # Add everything to the collection
        collection.add(
            embeddings=embedded_vectors,
            documents=contents_to_embed,
            metadatas=metadatas_to_add,
            ids=ids_to_add
        )
        
        print(f"  Successfully added {collection.count()} items to collection '{collection_name}'.")
print("\n--- Vector store creation process complete. ---")
print(f"Total collections in database: {len(client.list_collections())}")