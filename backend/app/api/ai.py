from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_database
from app.schemas.ai import EmailTriageResponse
from app.schemas.user import UserResponse
from app.services.ai_pipeline import AIPipelineService

router = APIRouter(prefix="/api/ai", tags=["ai"])


def get_ai_pipeline_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AIPipelineService:
    return AIPipelineService(db)


@router.post("/triage/{email_id}", response_model=EmailTriageResponse)
async def triage_single_email(
    email_id: str,
    current_user: UserResponse = Depends(get_current_user),
    ai_pipeline: AIPipelineService = Depends(get_ai_pipeline_service),
) -> EmailTriageResponse:
    """Run deep Groq AI triage, summary, deadline & action extraction on an email."""
    result = await ai_pipeline.triage_email(email_id=email_id, user_id=current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found or unauthorized.",
        )
    return result


@router.post("/batch-triage", response_model=list[EmailTriageResponse])
async def batch_triage_emails(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    ai_pipeline: AIPipelineService = Depends(get_ai_pipeline_service),
) -> list[EmailTriageResponse]:
    """Run Groq AI triage on all pending potentially important emails."""
    return await ai_pipeline.batch_triage_user_emails(
        user_id=current_user.id,
        limit=limit,
    )
