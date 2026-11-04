"""Provisional application representation, independent of notebook/UI."""
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid5, NAMESPACE_URL
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from src.common.lineage import CONTRACT, sha256


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Students(Strict):
    regular: int | None = None
    dependency: int | None = None
    elective: int | None = None
    total: int = Field(ge=0)
    origins: list[dict] | None = None


class Modulation(Strict):
    rule_version: str
    capacity: int = Field(gt=0)
    proposed_groups: int = Field(ge=0)
    groups: list[dict] | None = None
    provisional: Literal[True] = True


class Offer(Strict):
    offer_id: UUID
    campus_id: UUID
    course_id: UUID
    period_id: UUID
    discipline_id: UUID
    cohort: str | None = None
    shift: str | None = None
    offer_type: str | None = None
    status: Literal["SUGERIDA"] = "SUGERIDA"
    forecast_raw: float
    students: Students
    modulation: Modulation
    teacher_suggestion: None = None
    human_adjustment: int | None = None
    source_model_keys: list[str]
    warnings: list[str]


class RuleResult(Strict):
    rule_id: str
    status: Literal["PASS", "FAIL", "NOT_EVALUATED"]
    reason: str
    evidence: str


class ApplicationView(Strict):
    schema_version: Literal["poc-planilha-turmas-v1"] = CONTRACT
    contract_status: Literal["PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO"] = "PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO"
    proposal_id: UUID
    execution_id: UUID
    proposal_revision: Literal[1] = 1
    academic_cycle: dict
    status: str
    source_type: Literal["DEMO"] = "DEMO"
    generated_at_utc: datetime
    lineage: dict
    offers: list[Offer]
    validation: list[RuleResult]
    total_rows: int
    limit: int
    offset: int
    payload_sha256: str


def rules(header, offers):
    result = [RuleResult(rule_id="POC-DRAFT", status="PASS" if header["status"] == "DRAFT" else "FAIL",
        reason="Proposta demonstrativa sem aprovação automática", evidence="proposal_generations.status"),
        RuleResult(rule_id="RF008-partial", status="PASS" if all(o.teacher_suggestion is None for o in offers) else "FAIL",
        reason="Sem docente/horário/sala na representação inicial; matriz institucional não homologada", evidence="offers.teacher_suggestion")]
    for rule, why in {
        "RGN001/US027":"Decisão humana e prevalência de edições não exercitadas pelo DEMO",
        "RGN002/RF010":"Integração institucional entre todos os cursos não demonstrada",
        "RGN003/RF021–025/US029–030":"Alvo agregado; composição regular/dependência/eletiva da previsão desconhecida",
        "RGN023/US028":"Gate de validação da matriz depende da aplicação",
        "RF009/RF020/US026":"Turno, coorte de ingresso e matriz homologada indisponíveis",
        "RF040–047/US033–034":"Capacidade DEMO não é regra institucional; unificação não validada",
        "RF117–125":"Sem elegibilidade PRIME/Escola/turno ou aprovação GQA",
        "RF155–159/US005–006":"SQL sintético e temporal; nenhuma integração institucional validada",
        "RF195–199/US016":"Auditoria técnica parcial; perfis institucionais/exportação não demonstrados",
        "RF204–206/US017":"Original preservado; revisão humana e feedback validado ainda indisponíveis",
        "US022":"Responsabilidade funcional não demonstrada por este ensaio",
    }.items():
        result.append(RuleResult(rule_id=rule,status="NOT_EVALUATED",reason=why,evidence="DEMO scope"))
    return result


def build_view(con, proposal_id, limit=100, offset=0):
    header = con.execute(text("""SELECT g.*,c.cycle_code,s.sha256 AS snapshot_sha256
        FROM planning.proposal_generations g JOIN planning.academic_cycles c ON c.id=g.cycle_id
        JOIN planning.dataset_snapshots s ON s.id=g.snapshot_id WHERE execution_id=:id"""),
        {"id":proposal_id}).mappings().first()
    if not header:
        raise LookupError("Proposal not found")
    usages = [dict(r) for r in con.execute(text("""SELECT * FROM planning.proposal_model_usage
        WHERE proposal_id=:id ORDER BY model_key,registered_model_name,model_version,run_id"""), {"id":proposal_id}).mappings()]
    lines = con.execute(text("""SELECT l.*,c.campus_id FROM planning.proposal_lines l
        JOIN planning.courses c ON c.id=l.course_id WHERE execution_id=:id
        ORDER BY course_id,period_id,discipline_id LIMIT :limit OFFSET :offset"""),
        dict(id=proposal_id,limit=limit,offset=offset)).mappings()
    offers = []
    for row in lines:
        key = "/".join(str(row[k]) for k in ("course_id","period_id","discipline_id"))
        sources = [u["model_key"] for u in usages if u["line_keys"] and key in u["line_keys"]]
        offers.append(Offer(offer_id=uuid5(NAMESPACE_URL, f"{proposal_id}/{key}"),
            **{k: row[k] for k in ("campus_id","course_id","period_id","discipline_id","forecast_raw","human_adjustment")},
            students=Students(total=row["proposed_students"]),
            modulation=Modulation(rule_version=header["rule_version"],capacity=header["capacity"],proposed_groups=row["proposed_groups"]),
            source_model_keys=sorted(set(sources)),warnings=["Composição de estudantes/coorte/turno desconhecida", "Modulação provisória DEMO"] + ([] if sources else ["Origem por linha não documentada no legado"])))
    view = ApplicationView(proposal_id=header["execution_id"],execution_id=header["execution_id"],
        academic_cycle={"academic_cycle_id":str(header["cycle_id"]),"cycle_code":header["cycle_code"]},
        status=header["status"],generated_at_utc=header["generated_at"],
        lineage=dict(snapshot_id=str(header["snapshot_id"]),snapshot_sha256=header["snapshot_sha256"],
            dataset_sha256=header["dataset_sha256"],training_campaign_id=None,ruleset_version=header["rule_version"],
            model_usages=[{k:str(v) if isinstance(v,(UUID,datetime)) else v for k,v in u.items()} for u in usages]),
        offers=offers,validation=rules(header,offers),total_rows=header["row_count"],limit=limit,offset=offset,payload_sha256="")
    body = view.model_dump(mode="json")
    body.pop("payload_sha256")
    view.payload_sha256 = sha256(body)
    return view


if __name__=="__main__":
    import json
    from pathlib import Path
    Path("/reports/planilha-turmas-poc-v1.schema.json").write_text(
        json.dumps(ApplicationView.model_json_schema(),ensure_ascii=False,indent=2),encoding="utf-8")
