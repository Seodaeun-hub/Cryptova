FROM python:3.11-slim

# AI 전처리 스크립트가 repository root를 작업 경로로 사용한다.
WORKDIR /workspace/cryptova-ai

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
