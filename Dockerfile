# 📦 Base image
FROM python:3.13-alpine

# 🔧 Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 📁 Workdir
WORKDIR /app

# 📦 Install deps
COPY requirement.txt /app/requirement.txt
RUN pip install --no-cache-dir -r /app/requirement.txt

# 📥 Copy source
COPY . /app

# 👤 Non-root
RUN adduser -D appuser && chown -R appuser:appuser /app
USER appuser

# 🚀 Run
CMD ["python", "Main.py"]