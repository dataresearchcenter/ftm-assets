export DEBUG := 1
export FTM_ASSETS_PUBLIC_CDN_PREFIX := http://localhost:5000/api/static
export FTM_ASSETS_MIRROR := 1
export FTM_ASSETS_THUMBNAILS := 1


all: clean install test

install:
	poetry install --with dev --all-extras

lint:
	poetry run flake8 ftm_assets --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 ftm_assets --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

pre-commit:
	poetry run pre-commit install
	poetry run pre-commit run -a

typecheck:
	poetry run mypy --strict ftm_assets

test:
	rm -rf .test-store
	mkdir -p static
	poetry run pytest -v --capture=sys --cov=ftm_assets --cov-report lcov
	rm -rf .test-store

build:
	poetry run build

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

api:
	uvicorn ftm_assets.api:app --reload --port 5000
