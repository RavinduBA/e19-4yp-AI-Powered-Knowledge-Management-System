import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from utils.get_embedding_function import get_embedding_function
from langchain_chroma import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = "data"

def load_documents():
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document]):
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )
    
    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)
    
    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")
    
    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)
    
    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        print("✅ Documents added and persisted automatically")
        return len(new_chunks)
    else:
        print("✅ No new documents to add")
        return 0

def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index
    
    last_page_id = None
    current_chunk_index = 0
    
    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"
        
        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
        
        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id
        
        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id
    
    return chunks

def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

def populate_database(reset=False):
    """
    Main function to populate the database
    """
    try:
        if reset:
            print("✨ Clearing Database")
            clear_database()
        
        # Check if DATA_PATH exists
        if not os.path.exists(DATA_PATH):
            return {
                "success": False,
                "message": f"Data directory '{DATA_PATH}' not found. Please create it and add PDF files."
            }
        
        # Load and process documents
        documents = load_documents()
        
        if not documents:
            return {
                "success": False,
                "message": f"No PDF documents found in '{DATA_PATH}' directory."
            }
        
        chunks = split_documents(documents)
        new_docs_added = add_to_chroma(chunks)
        
        if new_docs_added > 0:
            message = "Database populated successfully"
        else:
            message = "No new documents were added. All documents already exist in the database."

        return {
            "success": True,
            "message": message,
            "documents_processed": len(documents),
            "chunks_created": len(chunks),
            "new_documents_added": new_docs_added
        }

        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error populating database: {str(e)}"
        }