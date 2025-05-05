FROM ghcr.io/dataresearchcenter/ftmq:latest

COPY ftm_assets /app/ftm_assets
COPY setup.py /app/setup.py
COPY pyproject.toml /app/pyproject.toml
COPY VERSION /app/VERSION
COPY README.md /app/README.md

WORKDIR /app
RUN pip install gunicorn uvicorn
RUN pip install .

USER 1000
ENTRYPOINT ["gunicorn", "ftm_assets.api:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker"]
