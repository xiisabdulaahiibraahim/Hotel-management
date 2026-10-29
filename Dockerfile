FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for reportlab & mysqlclient if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libfreetype6-dev \
    liblcms2-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
