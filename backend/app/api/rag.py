from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_database
from app.schemas.rag import RAGIndexStatusResponse, RAGQueryRequest, RAGQueryResponse
from app.schemas.user import UserResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/rag", tags=["rag"])


def get_rag_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> RAGService:
    return RAGService(db)


@router.post("/query", response_model=RAGQueryResponse)
async def query_email_knowledge(
    payload: RAGQueryRequest,
    current_user: UserResponse = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGQueryResponse:
    """Execute natural language RAG Q&A over the user's historical emails."""
    return await rag_service.query_and_answer(
        user_id=current_user.id,
        query=payload.query,
        top_k=payload.top_k,
    )


@router.post("/reindex", response_model=RAGIndexStatusResponse)
async def reindex_user_emails(
    current_user: UserResponse = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGIndexStatusResponse:
    """Rebuild the ChromaDB vector embeddings index for the authenticated user."""
    return await rag_service.reindex_all_user_emails(user_id=current_user.id)
