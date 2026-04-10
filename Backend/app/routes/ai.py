from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_ai_service, get_alert_service, get_current_user
from app.models.user import User
from app.schemas.ai import (
    AnalyzeAlertRequest,
    AnalyzeAlertResponse,
    AlertAnalysisResult,
    ChatRequest,
    ChatResponse,
)
from app.services.ai_service import AIService
from app.services.alert_service import AlertService

router = APIRouter(tags=["AI"])


@router.post("/analyze-alert", response_model=AnalyzeAlertResponse)
def analyze_alert(
    payload: AnalyzeAlertRequest,
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service),
    ai_service: AIService = Depends(get_ai_service),
):
    try:
        if payload.alert_id is not None:
            alert_data = alert_service.get_alert_by_id_for_user(
                user=current_user,
                alert_id=payload.alert_id,
            )
            if not alert_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Alert not found",
                )
        else:
            alert_data = payload.alert.model_dump() if payload.alert else None

        if not alert_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert payload is required when alert_id is not provided",
            )

        analysis = ai_service.analyze_alert(alert_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AnalyzeAlertResponse(
        alert_id=payload.alert_id,
        analysis=AlertAnalysisResult(**analysis),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    _: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    try:
        response = ai_service.chat(payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ChatResponse(response=response)
