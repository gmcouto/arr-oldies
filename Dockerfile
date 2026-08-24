# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Create isolated virtualenv for arr-oldies installation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package metadata and source code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install build dependencies and the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

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
