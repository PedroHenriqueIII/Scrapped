from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.core.database import get_db_sync
from app.core.deps import get_current_user
from app.core.security import UserResponse
from app.models.models import Search, DecisionMaker, SearchStatus, SearchType
from app.schemas.schemas import (
    SearchCreate,
    SearchBatchCreate,
    SearchResponse,
    SearchStatusResponse,
    SearchListResponse,
)
from app.tasks.scraper import process_search_task

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_search(
    search_data: SearchCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    search_type = classify_query(search_data.query)
    
    search = Search(
        user_id=UUID(current_user.id),
        query=search_data.query,
        target_role=search_data.target_role,
        status=SearchStatus.PENDING,
        search_type=SearchType(search_type)
    )
    db.add(search)
    db.commit()
    db.refresh(search)

    background_tasks.add_task(process_search_task, str(search.id))

    return SearchStatusResponse(
        id=search.id,
        status=search.status.value,
        search_type=search_type,
        created_at=search.created_at,
        completed_at=search.completed_at
    )


@router.post("/batch", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def create_batch_search(
    batch_data: SearchBatchCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    searches = []
    for query in batch_data.queries:
        search = Search(
            user_id=UUID(current_user.id),
            query=query,
            target_role=batch_data.target_role,
            status=SearchStatus.PENDING,
            search_type=SearchType.COMPANY
        )
        db.add(search)
        searches.append(search)
    
    db.commit()
    for search in searches:
        background_tasks.add_task(process_search_task, str(search.id))

    return {"message": f"{len(searches)} searches created", "count": len(searches)}


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search(
    search_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    search = db.query(Search).filter(Search.id == UUID(search_id)).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    
    if str(search.user_id) != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    results = db.query(DecisionMaker).filter(DecisionMaker.search_id == UUID(search_id)).all()
    
    return SearchResponse(
        id=search.id,
        user_id=search.user_id,
        query=search.query,
        target_role=search.target_role,
        status=search.status.value,
        search_type=search.search_type.value if search.search_type else None,
        results=[r for r in results],
        created_at=search.created_at,
        completed_at=search.completed_at
    )


@router.get("", response_model=SearchListResponse)
async def list_searches(
    skip: int = 0,
    limit: int = 20,
    current_user: UserResponse = Depends(get_current_user),
    db = Depends(get_db_sync)
):
    query = db.query(Search).filter(Search.user_id == UUID(current_user.id))
    total = query.count()
    searches = query.order_by(Search.created_at.desc()).offset(skip).limit(limit).all()

    return SearchListResponse(
        searches=[
            SearchStatusResponse(
                id=s.id,
                status=s.status.value,
                search_type=s.search_type.value if s.search_type else None,
                created_at=s.created_at,
                completed_at=s.completed_at
            )
            for s in searches
        ],
        total=total
    )


def classify_query(query: str) -> str:
    from app.services.classifier import classify_query as classify
    return classify(query)