"""SQL snapshot persistence. Running this module never trains or serves a model."""
import argparse
import json
from pathlib import Path
from sqlalchemy import text
from src.persistence.db import engine
from src.academic.importer import import_sources
from src.simulation.academic import simulate,digest


def save(snapshot):
    expected=dict(snapshot)
    expected.pop('snapshot_id')
    expected.pop('dataset_sha256')
    if digest(expected)!=snapshot['dataset_sha256']:
        raise ValueError('Snapshot hash mismatch')
    with engine().begin() as con:
        con.execute(text("""INSERT INTO planning.academic_simulation_snapshots
            (snapshot_id,dataset_sha256,cycle_code,seed,scenario_id,manifest)
            VALUES (:snapshot_id,:dataset_sha256,:target,:seed,:scenario_id,CAST(:manifest AS jsonb))
            ON CONFLICT DO NOTHING"""),dict(snapshot,manifest=json.dumps(snapshot,ensure_ascii=False)))
        saved=con.execute(text('SELECT manifest FROM planning.academic_simulation_snapshots WHERE snapshot_id=:id'),
                          {'id':snapshot['snapshot_id']}).scalar_one()
        if saved!=snapshot:
            raise ValueError('Immutable snapshot differs')
        for row in snapshot['observations']:
            con.execute(text("""INSERT INTO planning.model_training_observations
                (snapshot_id,offer_id,cycle_code,cohort_id,regular,dependency,elective,split,data_class,payload)
                VALUES (:snapshot,:offer_id,:cycle_code,:cohort_id,:regular,:dependency,:elective,:split,:data_class,CAST(:payload AS jsonb))
                ON CONFLICT DO NOTHING"""),dict(row,snapshot=snapshot['snapshot_id'],payload=json.dumps(row,ensure_ascii=False)))
    return snapshot['snapshot_id']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path('/reference'))
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--profile',default='baseline')
    parser.add_argument('--output',type=Path,default=Path('/reports/v4/scenario-manifest.json'))
    args=parser.parse_args()
    snapshot=simulate(import_sources(args.source),seed=args.seed,profile=args.profile)
    save(snapshot)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(snapshot_id=snapshot['snapshot_id'],dataset_sha256=snapshot['dataset_sha256'],
                         observations=len(snapshot['observations']),offers=len(snapshot['offers']),excluded=len(snapshot['excluded']))))

if __name__=='__main__':
    main()
