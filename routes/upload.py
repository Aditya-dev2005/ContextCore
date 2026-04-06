from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from services.pdf_processor import extract_text_from_pdf, chunk_text
from services.vector_store import add_to_vectorstore
from models.schemas import UploadResponse
from routes.auth import verify_token
import tempfile
import os
import shutil
from typing import Optional

router = APIRouter()

def get_user_from_token(authorization: Optional[str]) -> str:
    """Extract username from Bearer token, fallback to default."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        username = verify_token(token)
        if username:
            return username
    return "__default__"

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    user = get_user_from_token(authorization)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        text = extract_text_from_pdf(tmp_path)
        chunks = chunk_text(text)
        add_to_vectorstore(chunks, file.filename, user=user)

        return UploadResponse(
            message="PDF processed successfully",
            chunks=len(chunks),
            filename=file.filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)