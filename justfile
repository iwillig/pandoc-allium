# Run everything: Python + JS test suites.
test: test-py test-js

# Run the Python test suite (pytest via pipenv).
test-py:
    pipenv run pytest

# Run the JS test suite (yarn/node).
test-js:
    cd js && yarn test

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
