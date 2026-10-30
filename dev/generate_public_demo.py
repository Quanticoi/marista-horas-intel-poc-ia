"""Generate a readable public-data notebook using only stdlib on the host."""
import json
from pathlib import Path
from textwrap import dedent

cells = []


def cell(kind, source):
    value = dict(cell_type=kind, id=f"public-{len(cells):02d}", metadata={},
                 source=dedent(source).strip().splitlines(keepends=True))
    if kind == "code":
        value.update(execution_count=None, outputs=[])
    cells.append(value)


cell("markdown", """
# Laboratório completo: séries temporais com dados públicos

Execute **Run → Run All Cells** no kernel **PUCPR Python 3.12**.
Este notebook treina e registra candidatos no MLflow; cada execução cria novos runs.
Não altera o catálogo acadêmico nem promove modelos para produção.

## Pergunta e origem
Conseguimos prever o próximo trimestre de PIB real, consumo real e desemprego?
Usamos 203 trimestres (1959Q1–2009Q3) da base `macrodata`, distribuída com
statsmodels 0.14.4. Dados históricos públicos FRED/BLS, compilados por Skipper Seabold.
[Fonte, dicionário e declaração de domínio público](https://github.com/statsmodels/statsmodels/blob/v0.14.4/statsmodels/datasets/macrodata/data.py).
PIB/consumo estão em bilhões de dólares de 2005; desemprego em percentual.
É um benchmark técnico: não representa alunos, matrículas ou previsão econômica atual.
Usa dados revisados disponíveis na base, não vintages de publicação em tempo real.
""")
cell("code", """
from pathlib import Path
import hashlib, json, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from statsmodels.datasets import macrodata
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

OUTPUT = Path('/workspace/public-demo')
OUTPUT.mkdir(parents=True, exist_ok=True)
EXPERIMENT = 'public-macrodata-timeseries'
mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
experiment = mlflow.set_experiment(EXPERIMENT)
print('Experimento:', EXPERIMENT, '| ID:', experiment.experiment_id)
""")
cell("markdown", """
## 1. Carregar, validar e preservar a base
O CSV já está instalado no pacote; não há download nem dados inventados.
Salvamos uma cópia com SHA-256 para rastrear exatamente a entrada de cada execução.
""")
cell("code", """
raw = macrodata.load_pandas().data.copy()
periods = pd.PeriodIndex(raw.year.astype(int).astype(str) + 'Q' + raw.quarter.astype(int).astype(str), freq='Q')
raw.index = periods.to_timestamp(how='start')
raw.index.name = 'date'
assert len(raw) == 203 and raw.index.is_unique and raw.index.is_monotonic_increasing
assert not raw.isna().any().any()
assert np.all(np.diff(periods.asi8) == 1), 'Lacuna temporal'
csv_path = OUTPUT / 'macrodata.csv'
raw.to_csv(csv_path, float_format='%.10g')
checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()
provenance = dict(dataset='statsmodels.macrodata', version='0.14.4', sha256=checksum,
    source='https://github.com/statsmodels/statsmodels/blob/v0.14.4/statsmodels/datasets/macrodata/data.py',
    license='Public domain (dataset declaration)', rows=len(raw), frequency='quarterly')
(OUTPUT / 'provenance.json').write_text(json.dumps(provenance, indent=2))
print('Linhas:', len(raw), '| Período:', periods[0], 'até', periods[-1], '| SHA256:', checksum)
display(raw.head())
display(raw[['realgdp', 'realcons', 'unemp']].describe())
""")
cell("markdown", """
## 2. Explorar tendências e variações
Cada variável tem escala própria. Não comparamos MAE de dólares com MAE em pontos percentuais.
Observe a tendência de PIB/consumo e os ciclos de desemprego.
""")
cell("code", """
SERIES = ['realgdp', 'realcons', 'unemp']
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
for name, ax in zip(SERIES, axes):
    raw[name].plot(ax=ax, title=name, grid=True)
fig.tight_layout()
fig.savefig(OUTPUT / 'historical-series.png', dpi=140)
plt.show()
""")
cell("markdown", """
## 3. Features e protocolo temporal
Para prever y(t), usamos apenas y(t-1), y(t-2), y(t-4), média dos quatro trimestres
anteriores e mudança anterior. Nenhum valor contemporâneo de outra série entra no modelo.
Os últimos 20 trimestres são teste; os 20 anteriores são validação.
Escolhemos o método por MAE de validação e só depois observamos o teste.
A avaliação é de **um passo à frente**: valores reais de trimestres já encerrados
ficam disponíveis no próximo passo. Não equivale a prever 20 trimestres de uma vez.
""")
cell("code", """
FEATURES = ['lag1', 'lag2', 'lag4', 'mean4', 'previous_change']
def supervised(series):
    frame = pd.DataFrame({'y': series})
    for lag in (1, 2, 4):
        frame[f'lag{lag}'] = series.shift(lag)
    frame['mean4'] = series.shift(1).rolling(4).mean()
    frame['previous_change'] = series.shift(1).diff()
    return frame.dropna()

def estimator(name):
    if name == 'ridge':
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    return RandomForestRegressor(n_estimators=100, max_depth=6, min_samples_leaf=3,
                                 random_state=42, n_jobs=1)

def metrics(actual, predicted):
    return {'mae': float(mean_absolute_error(actual, predicted)),
            'rmse': float(np.sqrt(mean_squared_error(actual, predicted)))}

sample = supervised(raw.realgdp)
display(sample.head())
print('Treino:', len(sample)-40, '| Validação: 20 | Teste: 20')
assert sample.index[-41] < sample.index[-40] < sample.index[-20]
assert sample.lag1.iloc[0] == raw.realgdp.iloc[3]
""")
cell("markdown", """
## 4. Treinar e comparar nove execuções
Baseline de persistência: próximo valor = último valor observado.
Ridge aplica padronização ajustada somente no treino; Random Forest usa semente fixa.
Após validação, cada estimador é reajustado em treino+validação para medir o teste.
Registramos métricas, parâmetros, dados, gráficos, previsões e seis modelos sklearn
no experimento público. Baseline não precisa de artefato treinado.
""")
cell("code", """
records, all_predictions, run_links = [], {}, []
for series_name in SERIES:
    frame = supervised(raw[series_name])
    train, valid, test = frame.iloc[:-40], frame.iloc[-40:-20], frame.iloc[-20:]
    candidates = {}
    for algorithm in ('persistence', 'ridge', 'random_forest'):
        model = None if algorithm == 'persistence' else estimator(algorithm)
        if model is None:
            val_prediction = valid.lag1.to_numpy()
        else:
            model.fit(train[FEATURES], train.y)
            val_prediction = model.predict(valid[FEATURES])
        candidates[algorithm] = metrics(valid.y, val_prediction)
    selected = min(candidates, key=lambda name: candidates[name]['mae'])
    predictions = pd.DataFrame({'actual': test.y})
    for algorithm, validation_metrics in candidates.items():
        with mlflow.start_run(run_name=f'{series_name}-{algorithm}', tags={
            'dataset': 'public-macrodata', 'synthetic': 'false', 'purpose': 'demonstration',
            'selected_on_validation': str(algorithm == selected).lower(), 'dataset_sha256': checksum}) as run:
            mlflow.log_params(dict(series=series_name, algorithm=algorithm, horizon=1,
                train_rows=len(train), validation_rows=20, test_rows=20,
                split='chronological', selection_metric='validation_mae', seed=42,
                features=','.join(FEATURES)))
            model = None if algorithm == 'persistence' else estimator(algorithm)
            if model is None:
                predicted = test.lag1.to_numpy()
            else:
                fit = frame.iloc[:-20]
                model.fit(fit[FEATURES], fit.y)
                predicted = model.predict(test[FEATURES])
                mlflow.log_params({f'model_{k}': str(v) for k, v in model.get_params().items()})
                mlflow.sklearn.log_model(model, name='model',
                    signature=infer_signature(test[FEATURES], predicted),
                    input_example=test[FEATURES].head(2),
                    registered_model_name=f'public-macrodata-{series_name}-{algorithm}')
            test_metrics = metrics(test.y, predicted)
            mlflow.log_metrics({f'validation_{k}': v for k,v in validation_metrics.items()})
            mlflow.log_metrics({f'test_{k}': v for k,v in test_metrics.items()})
            mlflow.log_artifact(str(csv_path), 'dataset')
            mlflow.log_artifact(str(OUTPUT / 'provenance.json'), 'dataset')
            mlflow.log_artifact(str(OUTPUT / 'historical-series.png'), 'plots')
            detail = pd.DataFrame({'actual': test.y, 'predicted': predicted})
            detail['residual'] = detail.actual - detail.predicted
            prediction_path = OUTPUT / f'{series_name}-{algorithm}-predictions.csv'
            detail.to_csv(prediction_path)
            mlflow.log_artifact(str(prediction_path), 'evaluation')
            fig, ax = plt.subplots(figsize=(10, 3))
            detail[['actual', 'predicted']].plot(ax=ax, title=f'{series_name}: {algorithm}', grid=True)
            fig.tight_layout()
            mlflow.log_figure(fig, 'plots/test-predictions.png')
            plt.close(fig)
            predictions[algorithm] = predicted
            records.append(dict(series=series_name, algorithm=algorithm,
                validation_mae=validation_metrics['mae'], test_mae=test_metrics['mae'],
                test_rmse=test_metrics['rmse'], selected=algorithm == selected, run_id=run.info.run_id))
            run_links.append(f'http://127.0.0.1:5000/#/experiments/{experiment.experiment_id}/runs/{run.info.run_id}')
    all_predictions[series_name] = predictions
results = pd.DataFrame(records)
results.to_csv(OUTPUT / 'comparison.csv', index=False)
display(results.drop(columns='run_id').round(3))
assert len(results) == 9 and np.isfinite(results[['validation_mae','test_mae','test_rmse']]).all().all()
""")
cell("markdown", """
## 5. Interpretar o teste e consultar o Registry
O melhor na validação pode perder no teste; mantenha a seleção original para evitar
escolher retrospectivamente pelo teste. A base pequena e as mudanças econômicas
limitam a generalização. Random Forest não extrapola tendências tão bem quanto modelos lineares.
Os registros `public-macrodata-*` são candidatos de demonstração, sem alias champion.
""")
cell("code", """
fig, axes = plt.subplots(3, 1, figsize=(12, 10))
for (name, prediction), ax in zip(all_predictions.items(), axes):
    prediction.plot(ax=ax, title=f'{name} — teste de um passo à frente', grid=True)
fig.tight_layout()
fig.savefig(OUTPUT / 'comparison.png', dpi=140)
plt.show()
display(results[results.selected].drop(columns='run_id').round(3))
display(Markdown(f'[Abrir experimento público](http://127.0.0.1:5000/#/experiments/{experiment.experiment_id})'))
print('9 runs finalizados; 6 modelos registrados; sem promoção automática.')
print('CSV, proveniência, previsões e figuras em', OUTPUT)
""")
cell("markdown", """
## Próximos exercícios
1. Compare janela expansiva com janela móvel, mantendo o teste final intocado.
2. Experimente prever diferenças e reconstruir os níveis; compare contra persistência.
3. Adicione horizontes maiores com estratégia recursiva e métricas por horizonte.
4. Para o caso Marista, obtenha séries históricas institucionais autorizadas; este
benchmark demonstra o fluxo de trabalho, não valida desempenho em matrículas.

Os experimentos acadêmicos existentes estão em
[pucpr-synthetic](http://127.0.0.1:5000/#/experiments/1).
""")

notebook = dict(nbformat=4, nbformat_minor=5, metadata={"kernelspec": {
    "name": "pucpr", "display_name": "PUCPR Python 3.12", "language": "python"}}, cells=cells)
target = Path(__file__).resolve().parents[1] / 'notebooks/08_public_timeseries_lab.ipynb'
target.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(target)
