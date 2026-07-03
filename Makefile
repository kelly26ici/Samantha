.PHONY: llm settings qdrant embeddings

settings:
	python -m src.configs.settings

llm:
	python -m tests.test_llm

embeddings:
	python -m tests.embeddings

qdrant:
	python -m tests.qdrant

