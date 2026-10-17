FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir prometheus-client
COPY delivery_metrics.py .
# Without this, Python buffers print() and `docker logs` shows nothing
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "delivery_metrics.py"]
