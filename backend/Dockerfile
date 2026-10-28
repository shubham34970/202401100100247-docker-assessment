FROM python:3.13.18-slim-bookworm

ARG APP_VERSION=dev
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DISABLE_PIP_VERSION_CHECK=1 \
	APP_VERSION=${APP_VERSION}

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip==26.2.2 \
	&& python -m pip install --no-cache-dir -r requirements.txt \
	&& groupadd --system app \
	&& useradd --system --gid app --home-dir /app app

COPY --chown=app:app app.py .

USER app

EXPOSE 5000

CMD ["python", "app.py"]
