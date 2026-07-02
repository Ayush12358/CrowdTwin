FROM python:3.12-slim

# Install system dependencies for OpenCV/YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy main pipeline code
COPY main.py .

EXPOSE 8000

ENTRYPOINT ["python", "main.py"]
CMD ["--camera_link", "0", "--host", "0.0.0.0", "--port", "8000"]
