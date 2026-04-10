from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AlertPayload(BaseModel):
    device_id: int
    type: str
    severity: str
    description: str
    created_at: datetime | None = None


class AnalyzeAlertRequest(BaseModel):
    alert_id: int | None = Field(default=None, ge=1)
    alert: AlertPayload | None = None

    @model_validator(mode="after")
    def validate_input(self):
        if self.alert_id is None and self.alert is None:
            raise ValueError("Provide either alert_id or alert payload")
        return self


class AlertAnalysisResult(BaseModel):
    explanation: str
    why_it_happened: str
    risk_level_reasoning: str
    mitigation_steps: list[str]


class AnalyzeAlertResponse(BaseModel):
    alert_id: int | None = None
    analysis: AlertAnalysisResult


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    response: str


class AlertForAI(BaseModel):
    id: int | None = None
    device_id: int
    type: str
    severity: str
    description: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
