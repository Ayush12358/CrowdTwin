FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator API and the dashboard files
COPY api.py .
COPY web/ ./web/

EXPOSE 8001

ENTRYPOINT ["python", "api.py"]
CMD ["--host", "0.0.0.0", "--port", "8001"]
