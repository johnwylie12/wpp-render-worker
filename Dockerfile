FROM python:3.12-slim

# WeasyPrint 69 runtime libraries + Liberation (last-resort fallback only).
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

# Install the committed brand fonts (Trebuchet + Paralucent) so the CIR,
# snapshot, and cover render in real brand type on Railway (not Liberation).
RUN mkdir -p /usr/share/fonts/brand \
    && cp fonts/*.ttf fonts/*.otf /usr/share/fonts/brand/ 2>/dev/null || true \
    && fc-cache -f >/dev/null 2>&1

# fonts.conf maps Arial Nova/Arial -> Trebuchet and lets Trebuchet/Paralucent
# resolve to the installed brand fonts (Liberation only as last-resort fallback).
ENV FONTCONFIG_FILE=/app/cir/build/fonts.conf
ENV POLL_SECONDS=60
ENV STORAGE_BUCKET=collateral
ENV SUPPORTED_DOC_TYPES=vertical_deepdive,note_card,package,cover_page,opportunity_snapshot,sector_benchmark,case_study,closing_page,mailer,exec_brief,wave
# SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected by the host at runtime.

CMD ["python", "worker.py"]
