FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update     && apt-get install -y --no-install-recommends docker.io     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip     && python -m pip install -r requirements.txt

COPY . .

RUN mkdir -p /data /runtime/proposals /runtime     && python -m py_compile agent.py model.py config.py tools/*.py

CMD ["python", "agent.py"]
