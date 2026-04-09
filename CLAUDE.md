# Project Commands

All commands run from `backend/` directory.

## Install
```bash
uv sync --group dev
```

## Run Server
```bash
docker-compose up                  # Use docker (recommended)
uv run python manage.py runserver  # Without docker
```

## Migrate
```bash
docker-compose exec backend uv run python manage.py makemigrations
docker-compose exec backend uv run python manage.py migrate
docker-compose exec backend uv run python manage.py showmigrations
```

## Tests
```bash
uv run pytest -q                # all tests
uv run pytest tests/xxx/xxx.py  # single file
```

## Lint & Format
```bash
uv run ruff check .
uv run ruff format .
```
