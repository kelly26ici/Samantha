.PHONY: llm settings

settings:
	python -m src.configs.settings

llm:
	python -m tests.test_llm
