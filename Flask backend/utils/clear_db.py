import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from utils.get_embedding_function import get_embedding_function
from langchain_chroma import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = "data"

def clear_chroma_database():
    # Load the existing Chroma DB
    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embedding_function()
    )

    # Get all existing document IDs
    existing_items = db.get(include=[])
    existing_ids = existing_items.get("ids", [])
    deleted_count = len(existing_ids)

    if deleted_count > 0:
        db.delete(ids=existing_ids)
        message = f"🗑️ Deleted {deleted_count} documents from Chroma database."
    else:
        message = "📂 No documents to delete in the Chroma database."

    return {
        "success": True,
        "message": message,
        "chunks_deleted": deleted_count
    }
