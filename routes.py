from fastapi import APIRouter, HTTPException
from backend.schemas import DocumentRequest, DocumentResponse
from backend.services.generator import GeminiDocumentGenerator

router = APIRouter(tags=["documents"])


@router.post("/generate", response_model=DocumentResponse)
def generate_document(request: DocumentRequest) -> DocumentResponse:
    try:
        generator = GeminiDocumentGenerator()
        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
        )
        return DocumentResponse(document_type=request.document_type, content=content)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Document generation failed: {exc}") from exc
