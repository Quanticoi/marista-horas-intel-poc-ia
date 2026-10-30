from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_id: UUID
    snapshot_id: UUID
    model_key: str = Field(min_length=1, max_length=160)
    target_year: int = Field(ge=2000, le=2200)
    target_semester: int = Field(ge=1, le=2)


class InferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_id: UUID
    snapshot_id: UUID
    model_key: str
    registered_version: str
    forecast_raw: float = Field(ge=0, allow_inf_nan=False)
    is_fallback: bool
    mlflow_run_id: str = ""
    code_version: str = ""
    dataset_sha256: str = ""
