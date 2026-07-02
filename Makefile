install:
	uv pip install -e .

run:
	uv run uvicorn app.fastapi_server:app --host 0.0.0.0 --port 8080

demo:
	uv run python -m app.agent
