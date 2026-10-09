build:
    uv run build.py

serve: build
    python3 -m http.server 8000 -d site
