FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy project files
COPY . .

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]