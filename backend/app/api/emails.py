from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_database
from app.schemas.email import EmailResponse, EmailStatsResponse, EmailSyncResult
from app.schemas.user import UserResponse
from app.services.email_service import EmailService, email_doc_to_response

router = APIRouter(prefix="/api/emails", tags=["emails"])


def get_email_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> EmailService:
    return EmailService(db)


@router.post("/sync", response_model=EmailSyncResult)
async def sync_emails(
    max_per_account: int = Query(default=20, ge=1, le=50),
    current_user: UserResponse = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
) -> EmailSyncResult:
    """Trigger ingestion and deduplication of unread emails across all connected accounts."""
    return await email_service.sync_user_inboxes(
        user_id=current_user.id,
        max_per_account=max_per_account,
    )


@router.get("", response_model=list[EmailResponse])
async def list_emails(
    only_important: bool = Query(default=False, description="Filter only potentially important emails"),
    only_unread: bool = Query(default=False, description="Filter only unread emails"),
    q: str | None = Query(default=None, description="Search keyword in subject, sender, or content"),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
) -> list[EmailResponse]:
    """List normalized ingested emails for the authenticated user."""
    docs = await email_service.list_emails(
        user_id=current_user.id,
        only_important=only_important,
        only_unread=only_unread,
        search_query=q,
        limit=limit,
        skip=skip,
    )
    return [email_doc_to_response(doc) for doc in docs]


@router.get("/stats/summary", response_model=EmailStatsResponse)
async def get_email_stats(
    current_user: UserResponse = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
) -> EmailStatsResponse:
    """Retrieve inbox ingestion counts and signal metrics for the authenticated user."""
    return await email_service.get_email_stats(current_user.id)


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(
    email_id: str,
    current_user: UserResponse = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
) -> EmailResponse:
    """Fetch single email details by ID ensuring user isolation."""
    doc = await email_service.get_email_by_id(email_id, current_user.id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found or unauthorized.",
        )
    return email_doc_to_response(doc)
