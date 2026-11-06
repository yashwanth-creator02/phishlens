FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-postgres.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-postgres.txt
COPY app ./app
COPY training ./training
COPY data ./data
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh && mkdir -p /app/models /app/storage /app/reports
# Bake the synthetic demo model into the image: a host that opens the port only after training
# would miss its health check on every cold start.
RUN python -m training.train --source synthetic --n 2400 --out /app/models --reports /app/reports
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
