FROM python:3.13.7-slim

# set environment variables
# prevents python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE=1
# non-empty value ensures python output (stdout, stderr) is sent to the terminal without buffering
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# set container working directory
WORKDIR /app

# copy requirements file first to working directory (helps cache layer)
COPY requirements.txt .

# install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy project files to working directory
COPY . .

# collect static files
RUN python manage.py collectstatic --noinput

# create custom non-root user
RUN useradd --system --create-home --shell /usr/sbin/nologin appuser

# chown -R changes ownership of the app directory to the non-root user (prevents permission issues)
# chmod +x changes file mode of the run script to executable
RUN chown -R appuser:appuser ./ && chmod +x ./scripts/run.sh

USER appuser

EXPOSE 8000

CMD ["./scripts/run.sh"]
