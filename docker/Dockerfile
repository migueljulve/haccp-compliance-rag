FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /code

# Dependencies first, in their own layer: editing application code below must not
# invalidate this layer, since reinstalling torch takes minutes.
# --frozen installs the exact versions from uv.lock instead of re-resolving.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY app/ app/
COPY src/ src/

EXPOSE 8501

CMD ["uv", "run", "--no-dev", "streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]
