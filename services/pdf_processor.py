from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config
from typing import List
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file"""
    text = ""
    try:
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            if page.extract_text():
                text += page.extract_text()
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")
    return text

def chunk_text(text: str) -> List[str]:
    """Split text into chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.MAX_CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    chunks = splitter.split_text(text)
    return chunks