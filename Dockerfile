# Use official lightweight Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port (if applicable, e.g., for FastAPI/Flask)
EXPOSE 8000

# Command to run the application (update for your web server)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app"]
