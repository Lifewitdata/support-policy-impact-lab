"""Full-refresh models, built in a fresh database before replacing the prior output."""
import os
import tempfile
import duckdb
import polars as pl
from .common import ROOT, config


def execute_models(con, followup_hours, observation_end):
    for path in sorted((ROOT/'sql').glob('*.sql')):
        sql = path.read_text().replace('{{followup_hours}}',str(int(followup_hours))).replace('{{observation_end}}',observation_end)
        con.execute(sql)


def build():
    cfg, plan = config('simulation'), config('analysis_plan')
    target=ROOT/'data/processed/support_policy.duckdb'
    # Everything is reproducible from raw Parquet. Do not depend on a previous
    # database or its WAL for a full-refresh run. Parallel writers are unsupported.
    with tempfile.TemporaryDirectory(prefix='build-',dir=target.parent) as directory:
        fresh=os.path.join(directory,'support_policy.duckdb')
        con=duckdb.connect(fresh,config={'threads':4})
        try:
            for p in sorted((ROOT/'data/raw').glob('*.parquet')):
                frame = pl.read_parquet(p)
                con.register('incoming',frame.to_arrow())
                con.execute(f'CREATE OR REPLACE TABLE raw_{p.stem} AS SELECT * FROM incoming')
            execute_models(con,plan['followup_hours'],cfg['observation_end'])
            exports={name:con.execute(f'SELECT * FROM {name} ORDER BY 1').pl()
                     for name in ['experiment_mart','policy_summary','daily_enrolment']}
            con.execute('CHECKPOINT')
        finally:
            con.close()
        # The old database is derived output. Remove a stale journal only after
        # the new database has completed and closed successfully.
        target.with_name(target.name+'.wal').unlink(missing_ok=True)
        os.replace(fresh,target)
        for name,result in exports.items():
            result.write_parquet(ROOT/'data/marts'/f'{name}.parquet')
            if name != 'experiment_mart':
                result.write_csv(ROOT/'outputs/tables'/f'{name}.csv')
