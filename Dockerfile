FROM python:3.12-slim

# WeasyPrint 69 runtime libraries + Liberation fonts (the locked CIR was
# rendered against Liberation via fonts.conf, so these guarantee pixel parity).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi8 \
        shared-mime-info \
        fontconfig \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Trebuchet/Arial Nova -> Liberation Sans mapping (CIR parity) for BOTH the
# CIR engine and the cover letter.
ENV FONTCONFIG_FILE=/app/cir/build/fonts.conf
ENV POLL_SECONDS=60
ENV STORAGE_BUCKET=collateral
ENV SUPPORTED_DOC_TYPES=vertical_deepdive
# SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected by the host at runtime.

CMD ["python", "worker.py"]
