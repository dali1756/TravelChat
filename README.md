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

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
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
docker-compose up                 # 啟動所有服務
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

### Docker Shell
```bash
# 進入 backend container shell
docker-compose exec backend bash

# 進入 db container shell
docker-compose exec db bash
```

### Backend Tests & Linting (在 backend/ 目錄下執行)
```bash
cd backend
uv run pytest -q                  # 執行所有測試
uv run pytest tests/xxx/xxx.py    # 執行單一測試檔案
uv run ruff check .               # 檢查 Python 程式碼規範
uv run ruff format .              # 自動格式化 Python 程式碼
```

### Frontend Tests & Linting (在 frontend/ 目錄下執行)
```bash
cd frontend
npm test                          # 執行所有測試
npm test -- tests/xxx/xxx.test.ts # 執行單一測試檔案
npm run test:watch                # Watch 模式（改檔案自動重跑）
npm run lint                      # 檢查程式碼規範
```
