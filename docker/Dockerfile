FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/docker/scripts/*.sh

ENTRYPOINT ["/bin/sh", "/app/docker/scripts/entrypoint.sh"]
CMD ["api"]
