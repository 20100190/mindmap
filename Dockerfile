FROM python:3.11-slim

# 1. Create a non-root user (Standard for HF Spaces)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# 2. Key Change: Copy files as the 'user', not root
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

# 3. HF Spaces expects port 7860 by default
ENV PORT=7860

# 4. Bind to the HF port
CMD ["sh", "-c", "gunicorn -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT} main:app"]