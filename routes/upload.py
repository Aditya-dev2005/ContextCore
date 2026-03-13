from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_processor import extract_text_from_pdf, chunk_text
from services.vector_store import create_vectorstore, save_vectorstore
from models.schemas import UploadResponse
import tempfile
import os
import shutil

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name
    
    try:
        # Process PDF
        text = extract_text_from_pdf(tmp_path)
        chunks = chunk_text(text)
        
        # Create and save vector store
        metadata = {"source": file.filename}
        from services.vector_store import add_to_vectorstore
        add_to_vectorstore(chunks, file.filename)
        
        return UploadResponse(
            message="PDF processed successfully",
            chunks=len(chunks),
            filename=file.filename
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)