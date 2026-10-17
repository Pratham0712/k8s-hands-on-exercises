FROM python:3.12-slim

WORKDIR /app

# Copy only the app, not the venv or the evidence files
COPY app.py /app/

RUN pip install --no-cache-dir "flask>=3,<4"

EXPOSE 5000

CMD ["python", "app.py"]
