from fastapi import APIRouter

from utils.response import success_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():

    return success_response(
        data={"service": "agentic-rag", "status": "running"},
        message="service is healthy",
    )