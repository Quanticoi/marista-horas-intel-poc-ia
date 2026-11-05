"""Strict provisional v2 contract; no institutional identifiers are invented."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)


class Selector(Strict):
    model_name:str=Field(pattern=r'^hi\.demo\.v4\.c[0-9]+\.components$')
    model_version:str=Field(pattern=r'^[1-9][0-9]*$')


class Generation(Strict):
    schema_version:Literal['poc-planilha-turmas-v2']='poc-planilha-turmas-v2'
    snapshot_id:UUID
    cycle_code:str=Field(pattern=r'^20[0-9]{2}-[12]$')
    proposal_revision:int=Field(default=1,ge=1)
    model_selectors:list[Selector]=Field(min_length=1,max_length=20)
    requested_by:str=Field(min_length=1,max_length=120)


class Academic(Strict):
    establishment:str|None
    school:str|None
    course_code:str
    course_name:str
    curriculum_code:str
    curriculum_version:str|None
    class_label:str|None
    period:int=Field(ge=1)
    shift:str
    discipline_code:str
    discipline_name:str
    offer_type:str
    cohort_id:UUID|None
    cohort_ingress:str|None
    prime_ids:None
    mapping_status:Literal['UNMAPPED','SYNTHETIC_ONLY']


class Component(Strict):
    value:int|None=Field(ge=0)
    raw_prediction:float|None
    data_class:Literal['AI_ESTIMATE','NOT_AVAILABLE']
    source_ref:UUID|None


class Demand(Strict):
    regular:Component
    dependency:Component
    elective:Component
    estimated_total:int|None=Field(ge=0)
    uncertainty:None
    reference_planned_students:int|None=Field(ge=0)
    composition_rule:Literal['CEIL_NONNEGATIVE_DISJOINT_DEMO_CATEGORIES']
    categories_disjoint:Literal['DEMO_ASSUMPTION']


class Activity(Strict):
    source_row_id:UUID
    source_file_sha256:str=Field(pattern='^[a-f0-9]{64}$')
    source_sheet:str
    source_row_number:int
    kind:Literal['THEORY','PRACTICE','OTHER']
    division:str|None
    reference_planned_students:int|None
    reference_seats:int|None
    capacity:None
    capacity_status:Literal['OFFICIAL_RULE_NOT_AVAILABLE']
    proposed_groups:list[dict]
    proposal_status:Literal['PENDING_OFFICIAL_CAPACITY']


class Offer(Strict):
    offer_id:UUID
    academic:Academic
    activities:list[Activity]
    status:Literal['QUARANTINED','REFERENCE_ONLY','DRAFT_PENDING_COORDINATOR']
    elective_eligibility:Literal['ELIGIBLE','INELIGIBLE','UNKNOWN']
    unification:dict
    modulation:dict
    demand:Demand
    lineage:dict
    warnings:list[str]


class ApplicationView(Strict):
    schema_version:Literal['poc-planilha-turmas-v2']
    contract_status:Literal['PROVISORIO_PENDENTE_HOMOLOGACAO']
    proposal_id:UUID
    correlation_id:str
    execution_id:UUID
    snapshot_id:UUID
    dataset_sha256:str
    cycle_code:str
    proposal_revision:int
    phase:Literal['REGULAR_MATRIX_DRAFT']
    source_type:Literal['SEMI_SYNTHETIC_POC']
    status:Literal['DRAFT_PENDING_COORDINATOR']
    generated_at:str
    offers:list[Offer]
    total_rows:int
    limit:int
    offset:int
    filters:dict
    payload_sha256:str
    proposal_sha256:str
