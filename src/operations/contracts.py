from typing import Literal
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field,model_validator
from src.persistence.journey import RULE

class Strict(BaseModel):
    model_config=ConfigDict(extra="forbid")

class Selector(Strict):
    model_name:str=Field(pattern=r"^(planilha-turmas-demo|hi\.demo\.[A-Za-z0-9_.-]+)$",max_length=160)
    model_version:str=Field(pattern=r"^[1-9][0-9]*$",max_length=12)

class Generation(Strict):
    schema_version:Literal["poc-generation-v2"]="poc-generation-v2"
    mode:Literal["DEMO","APPROVED"]="DEMO"
    cycle_code:str=Field(pattern=r"^[0-9]{4}-[12]$")
    snapshot_id:UUID
    model_selectors:list[Selector]=Field(min_length=1,max_length=30)
    ruleset_version:Literal[RULE]=RULE
    capacity:int=Field(default=40,ge=1,le=500)
    requested_by:str=Field(min_length=1,max_length=120)
    confirm_demo:Literal[True]

    @model_validator(mode="after")
    def unique(self):
        if len({(m.model_name,m.model_version) for m in self.model_selectors})!=len(self.model_selectors):
            raise ValueError("Duplicate model selection")
        return self

class Campaign(Strict):
    schema_version:Literal["poc-training-campaign-v2"]="poc-training-campaign-v2"
    snapshot_id:UUID
    cycle_code:str=Field(pattern=r"^[0-9]{4}-[12]$")
    model_keys:list[str]=Field(min_length=1,max_length=600)
    algorithm:Literal["ridge","dummy"]="ridge"
    alpha:float=Field(default=1.0,gt=0,le=1000)
    max_parallel_jobs:int=Field(default=2,ge=1,le=2)
    max_attempts:int=Field(default=3,ge=1,le=4)
    requested_by:str=Field(min_length=1,max_length=120)
    confirm_training:Literal[True]

    @model_validator(mode="after")
    def keys(self):
        import re
        if len(set(self.model_keys))!=len(self.model_keys) or any(not re.fullmatch(r"hi\.demo\.[A-Za-z0-9_.-]{1,140}",k) for k in self.model_keys):
            raise ValueError("Select unique hi.demo.* synthetic experiment identities")
        return self
