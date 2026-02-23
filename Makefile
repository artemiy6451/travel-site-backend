SRC := app/
TESTS := tests/

install:
	poetry install

black:
	poetry run black $(SRC) $(TESTS)
	@echo "Black done!"

ruff:
	poetry run ruff check $(SRC) $(TESTS)
	@echo "Ruff done!"

mypy:
	poetry run mypy --config mypy.ini $(SRC)
	@echo "Mypy done!"

test:
	poetry run pytest $(SRC) $(TESTS)
	@echo "Pytest done!"

check: black ruff mypy test
	@echo "All check passed!"

run:
	poetry run python $(SRC)main.py

dev:
	poetry run fastapi dev $(SRC)main.py

migrate:
	PYTHONPATH=. poetry run alembic upgrade head

migrate-create:
	PYTHONPATH=. poetry run alembic revision --autogenerate -m "$(m)"

migrate-down:
	PYTHONPATH=. poetry run alembic downgrade -1

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
