import os
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from uuid import UUID
from src.common.tagging import MODEL_PATTERN

class Parameters(BaseModel):
    model_config=ConfigDict(extra="forbid")
    mode:Literal["READ_EXISTING","GENERATE_AND_VALIDATE"]="READ_EXISTING"
    proposal_id:UUID|None=None
    snapshot_id:UUID|None=None
    model_name:str=Field(default="planilha-turmas-demo",pattern=MODEL_PATTERN,max_length=160)
    model_version:str=Field(default="",pattern=r"^([1-9][0-9]*)?$")
    registry_prefix:str=Field(default="",pattern=r"^[A-Za-z0-9_.-]{0,160}$")
    registry_page_token:str=Field(default="",max_length=2048)
    campaign_id:UUID|None=None
    approval_id:UUID|None=None
    execute_write:bool=False
    confirmation:str=""
    request_key:str=Field(default="",max_length=160)
    requester:str=Field(default="scientist-demo",min_length=1,max_length=120)
    algorithm:Literal["ridge","dummy"]="ridge"
    alpha:float=Field(default=1,gt=0,le=1000)
    capacity:int=Field(default=40,ge=1,le=500)
    model_count:int=Field(default=3,ge=1,le=500)
    campaign_display_name:str=Field(default="POC DEMO • Validação manual",min_length=1,max_length=160)
    parallel_jobs:int=Field(default=2,ge=1,le=2)
    campaign_action:Literal["create","observe","pause","resume","cancel","retry-failed"]="observe"
    governance_action:Literal["read","request","approve","reject"]="read"
    review_action:Literal["APPROVE","REVOKE","ROLLBACK"]="APPROVE"
    reason:str=""
    lineage_kind:Literal["proposal","run","model","snapshot","campaign"]="proposal"
    external_id:str=""
    reset_mode:Literal["preview","reset-data","factory-reset"]="preview"
    reinitialize:Literal["empty","demo-ready"]="demo-ready"
    reset_plan_id:UUID|None=None

    @classmethod
    def load(cls):
        values={key:os.environ["V2_"+key.upper()] for key in cls.model_fields if os.getenv("V2_"+key.upper())}
        for key,env in (("proposal_id","PROPOSAL_ID"),("reset_plan_id","RESET_PLAN_ID")):
            if key not in values and os.getenv(env):
                values[key]=os.environ[env]
        return cls.model_validate(values)

    def authorize(self):
        if not self.execute_write or self.confirmation!="EXECUTE_DEMO" or not self.request_key:
            raise ValueError("Writing requires execute_write=True, confirmation=EXECUTE_DEMO and a stable request_key")
