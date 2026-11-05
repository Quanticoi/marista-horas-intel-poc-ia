"""Explicit handoff from a completed journey, never a latest-model lookup."""
import json
from pathlib import Path
from uuid import UUID

from src.workbench.operations_sdk import call, write_report_file

CURRENT = Path('/workspace/reports/journey-current.json')
LEGACY = Path('/reports/journey-latest.json')


def save_context(summary, cycle, path=CURRENT):
    if not summary.get('stages') or any(s['status'] != 'PASS' for s in summary['stages']):
        raise ValueError('A jornada precisa concluir todas as etapas antes de continuar.')
    document = dict(summary, cycle_code=cycle)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_report_file(path, json.dumps(document, ensure_ascii=False, indent=2))


def resolve_proposal(cfg, explicit=None, current=CURRENT, legacy=LEGACY):
    if explicit:
        return str(UUID(str(explicit))), {'selection_source': 'explicit'}
    path = current if current.exists() else legacy
    if not path.exists():
        raise ValueError('Nenhuma jornada concluída registrada. Execute o notebook 01 até o fim ou selecione proposal_id na célula 1.1.')
    try:
        context = json.loads(path.read_text(encoding='utf-8'))
        proposal_id = str(UUID(context['proposal_id']))
        if proposal_id != context['execution_id'] or not context['stages']:
            raise ValueError('invalid execution')
        if any(s['status'] != 'PASS' for s in context['stages']):
            raise ValueError('unfinished execution')
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError('Contexto da jornada inválido; execute 01 até o fim ou selecione uma proposta explicitamente.') from error
    header = call(cfg, 'GET', f'/v1/proposals/{proposal_id}')
    view = call(cfg, 'GET', f'/v1/proposals/{proposal_id}/application-view?limit=1')
    if view['academic_cycle']['cycle_code'] != cfg.cycle:
        raise ValueError('A jornada registrada pertence a outro ciclo; selecione uma proposta explicitamente.')
    for key in ('execution_id', 'run_id', 'model_name', 'model_version', 'snapshot_id'):
        if not context.get(key) or str(header.get(key)) != str(context[key]):
            raise ValueError(f'Contexto da jornada diverge da proposta persistida: {key}. Selecione uma proposta explicitamente.')
    return proposal_id, dict(selection_source=str(path), proposal_id=proposal_id,
                             run_id=context['run_id'], model_name=context['model_name'],
                             model_version=context['model_version'], snapshot_id=context['snapshot_id'])
