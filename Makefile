.PHONY: \
	settings \
	webhook \
	llm \
	gemini \
	embeddings \
	qdrant \
	sql \
	mpesa \
	test \
	clean

settings:
	python -m src.configs.settings

webhook:
	uvicorn src.messages.webhook:app --reload

llm:
	python -m tests.test_llm

gemini:
	python -m src.services.gemini

embeddings:
	python -m tests.embeddings

qdrant:
	python -m tests.qdrant

sql:
	python -m src.services.sql

mpesa:
	python -m src.MPESA.access_token

test:
	python -m pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete