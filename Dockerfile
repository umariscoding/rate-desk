# One image: build the React app, then serve it and the API from a single Python server.
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir -e .
COPY backend/templates ./templates
COPY --from=web /web/dist /app/frontend
ENV FRONTEND_DIR=/app/frontend DATA_DIR=/app/data PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
