# Dockerfile for Revenue Recovery AI Agent (Python backend)

# ---------- Build stage ----------
FROM python:3.11-slim AS builder
WORKDIR /app

# Install uv (Python package manager)
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY expense_agent/ ./expense_agent/

# Install dependencies without dev packages
RUN uv sync --frozen --no-dev

# ---------- Runtime stage ----------
FROM python:3.11-slim AS runner
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

# Copy application code
COPY --from=builder /app/expense_agent ./expense_agent

# Expose the FastAPI service port
EXPOSE 8080

# Run the FastAPI application via uv
CMD ["uv", "run", "python", "expense_agent/fast_api_app.py"]
