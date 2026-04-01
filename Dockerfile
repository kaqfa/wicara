# Gunakan image Python ringan sebagai base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV HOST=0.0.0.0
ENV PORT=5555

# Set working directory
WORKDIR /app

# Install system dependencies (opsional, jika diperlukan library C nantinya)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy semua file project ke dalam container
COPY . /app/

# Buat direktori yang dibutuhkan untuk data persisten dan pastikan permissions
RUN mkdir -p /app/static/images/uploads /app/sites /app/exports /app/logs /app/app/plugins/installed
RUN chmod -R 777 /app/static/images/uploads /app/sites /app/exports /app/logs /app/app/plugins/installed
RUN touch /app/config.json && chmod 666 /app/config.json

# Expose port yang digunakan
EXPOSE 5555

# Jalankan aplikasi menggunakan Gunicorn untuk production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5555", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
