FROM mambaorg/micromamba:2.0.5
ARG CODE_VERSION=uncommitted
ENV CODE_VERSION=${CODE_VERSION}
COPY --chown=$MAMBA_USER:$MAMBA_USER config/environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY --chown=$MAMBA_USER:$MAMBA_USER pyproject.toml ./
COPY --chown=$MAMBA_USER:$MAMBA_USER config/requirements.lock ./requirements.lock
RUN --mount=type=cache,target=/home/mambauser/.cache/pip,uid=57439 pip install -r requirements.lock
COPY --chown=$MAMBA_USER:$MAMBA_USER src ./src
RUN pip install --no-deps . && pip check && python -m ipykernel install --sys-prefix --name pucpr --display-name 'PUCPR Python 3.12'
COPY --chown=$MAMBA_USER:$MAMBA_USER config ./config
COPY --chown=$MAMBA_USER:$MAMBA_USER notebooks ./notebooks
COPY --chown=$MAMBA_USER:$MAMBA_USER sql ./sql
COPY --chown=$MAMBA_USER:$MAMBA_USER tests ./tests
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
CMD ["python", "-m", "src.common.launch", "jupyter"]
