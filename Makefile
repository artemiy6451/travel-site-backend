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
	poetry run mypy --config mypy.ini $(SRC) $(TESTS)
	@echo "Mypy done!"

pytest:
	poetry run pytest $(SRC) $(TESTS)
	@echo "Pytest done!"

check: black ruff mypy pytest
	@echo "All check passed!"

run:
	poetry run python $(SRC)main.py

dev:
	poetry run fastapi dev $(SRC)main.py --host 0.0.0.0 --port 8000

migrate:
	PYTHONPATH=. poetry run alembic upgrade head

migrate-create:
	PYTHONPATH=. poetry run alembic revision --autogenerate -m "$(m)"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
