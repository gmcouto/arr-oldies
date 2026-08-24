# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Create isolated virtualenv for arr-oldies installation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy project manifest first to maximize layer caching of dependencies
COPY pyproject.toml README.md ./

# Install third-party dependencies using standard library tomllib before copying source code
RUN python3 -c "import tomllib; data=tomllib.load(open('pyproject.toml','rb')); print('\n'.join(data['project']['dependencies']))" > /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy application source code and install arr-oldies package
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

# Stage 2: Runner stage
FROM python:3.11-slim AS runner

# OCI Image Labels
LABEL org.opencontainers.image.title="arr-oldies" \
      org.opencontainers.image.description="CLI tool and auditing engine to inventory and clean stale media across Radarr and Sonarr instances" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/gmcouto/arr-oldies"

# Runtime environment settings
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create unprivileged non-root user and group
RUN groupadd -g 1000 arrgroup && \
    useradd -u 1000 -g arrgroup -m -d /app arruser && \
    mkdir -p /config && \
    chown -R arruser:arrgroup /app /config

# Copy virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy and configure entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Run as unprivileged user
USER arruser
WORKDIR /app

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["--help"]
