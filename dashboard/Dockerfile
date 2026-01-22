FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all dashboard files
COPY . .

# Expose the default Hugging Face Spaces port
EXPOSE 7860

# Run the ASGI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
