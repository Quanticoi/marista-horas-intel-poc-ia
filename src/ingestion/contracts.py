from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.data.synthetic import validate


class Enrollment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    model_key: str = Field(pattern=r"^C[1-9][0-9]*-CR[1-9][0-9]*-P([1-9]|1[0-9]|20)$", max_length=60)
    campus_id: str
    course_id: str
    period_id: str
    reference_year: int = Field(ge=2000, le=2200)
    reference_semester: int = Field(ge=1, le=2)
    regular_students: int = Field(ge=0, le=1000000)
    dependency_students: int = Field(ge=0, le=1000000)
    elective_students: int = Field(ge=0, le=1000000)


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9_.-]+$")
    as_of_date: date
    target_year: int = Field(ge=2000, le=2200, strict=True)
    target_semester: int = Field(ge=1, le=2, strict=True)
    records: list[Enrollment] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def valid_history(self):
        records = [r.model_dump() for r in self.records]
        validate(records, self.as_of_date)
        if len({r.model_key for r in self.records}) > 30:
            raise ValueError("Maximum 30 series per dataset")
        from collections import Counter
        if min(Counter(r.model_key for r in self.records).values()) < 3:
            raise ValueError("At least three observations per series are required for temporal validation")
        if self.as_of_date >= date(self.target_year, 1 if self.target_semester == 1 else 7, 1):
            raise ValueError("Snapshot must precede target semester")
        return self


class TrainingStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    snapshot_id: UUID
    model_key: str = Field(min_length=1, max_length=160)
    algorithm: Literal["seasonal", "ridge", "forest"]
    code_version: str = Field(min_length=1, max_length=80)
    config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    run_id: str = Field(pattern=r"^[0-9a-f]{32}$")
