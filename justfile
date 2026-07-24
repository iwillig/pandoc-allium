# Run absolutely everything: every linter and every test suite.
check: lint test

# Run everything: Python + JS test suites (JS includes the cucumber features).
test: test-py test-js

# Run the Python test suite (pytest via pipenv).
test-py:
    pipenv run pytest

# Run the JS test suite: unit tests, then the cucumber features.
test-js:
    cd js && yarn test

# Run the cucumber-js feature suite on its own (js/features).
test-features:
    cd js && yarn test:features

# Run everything: Python + JS linters.
lint: lint-py lint-js

# Lint Python sources with ruff.
lint-py:
    pipenv run ruff check .

# Lint JS sources with eslint.
lint-js:
    cd js && yarn lint

# Chat with unsloth/Qwen3.6-27B-MLX-8bit via mlx_vlm's chat CLI.
chat-qwen:
    pipenv run python -m mlx_vlm.chat --model unsloth/Qwen3.6-27B-MLX-8bit

# Serve unsloth/Qwen3.6-27B-MLX-8bit at http://localhost:8080/v1 (OpenAI-compatible) for pi agent. Leave running in its own terminal.
serve-qwen:
    pipenv run python -m mlx_vlm.server --host 127.0.0.1 --port 8080 --model unsloth/Qwen3.6-27B-MLX-8bit
