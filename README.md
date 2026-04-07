# Travel Chat
一款結合 AI 的旅行規劃和即時通訊功能的旅行規劃產品。

## 技術棧
- **Backend:** Django 6, Django REST Framework, Django Channels
- **WebSocket:** Daphne (ASGI), Redis (Channel Layer)
- **Auth:** JWT (SimpleJWT)
- **Database:** PostgreSQL
- **DevOps:** Docker Compose, uv

## Getting Started
### Prerequisites
- [Docker](https://www.docker.com/)
- [uv](https://docs.astral.sh/uv/)

### Setup
```bash
git clone <repo-url>
cd django_channel
cp .env.example .env                                         # 複製 .env.example -> .env 並填入值
cd backend
uv sync --group dev                                          # 安裝套件（自動建立 .venv 檔案）
cd ..
docker-compose up                                            # 啟動所有服務（Backend + Databases + Redis）
docker-compose exec backend uv run python manage.py migrate  # 第一次啟動需執行
```

### Access

- **Backend:** http://localhost:8000
- **Admin:** http://localhost:8000/admin/

### 虛擬環境
如果沒有使用 Docker
```bash
cd backend
source .venv/bin/activate
uv run python manage.py runserver
```

## 常用命令
### Server
```bash
docker-compose up                 # 啟動所有服物
docker-compose up --build         # Rebuild after adding packages
docker-compose down               # 停止所有服務
```

### Database
```bash
# Check migration status
docker-compose exec backend uv run python manage.py showmigrations

# Run migrations
docker-compose exec backend uv run python manage.py makemigrations
docker-compose exec backend uv run python manage.py migrate

# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d django_channel
```

### Tests & Linting
```bash
uv run pytest                     # Run all tests
uv run pytest tests/xxx/xxx.py    # Run single file
uv run ruff check .               # Lint check
uv run ruff format .              # Auto format
```
