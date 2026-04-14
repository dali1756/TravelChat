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

## 環境變數

所有 env 變數皆需於 `.env` 提供（可參考 `.env.example`）。

| 變數 | 用途 | 預設 | 備註 |
|---|---|---|---|
| `SECRET_KEY` | Django SECRET_KEY | **必填**（缺值會 `KeyError`） | 生產環境請用長亂數 |
| `DJANGO_DEBUG` | Debug 模式 | `False` | 僅 `"True"` / `"1"` / `"true"` 才開啟 |
| `ALLOWED_HOSTS` | 允許的 Host（逗號分隔） | `localhost,127.0.0.1` | Prod 必須指定 |
| `FRONTEND_URL` | 前端 base URL（用於 email 連結） | `http://localhost:5173` | |
| `EMAIL_BACKEND` | Email 後端 | `console`（印到 stdout） | Prod 請設為 SMTP |
| `DEFAULT_FROM_EMAIL` | 寄件者 | `noreply@localhost` | |
| `LOGIN_THROTTLE_RATE` | 登入速率限制 | `5/min` | DRF 格式，例如 `10/min` |
| `REDIS_HOST` | Redis host | `redis` | |
| `DB_*` | PostgreSQL 連線 | 參考 `.env.example` | |

## API 總覽

### 認證相關（`/api/auth/`）
| Method | Path | 說明 |
|---|---|---|
| POST | `/register/` | 註冊（建立 inactive user 並寄驗證信） |
| POST | `/login/` | 登入（需 `is_active=True`）；預設速率 5/min |
| POST | `/logout/` | 登出（作廢 refresh token；需驗擁有者） |
| POST | `/token/refresh/` | 換發 access token（啟用 rotation + blacklist） |
| GET  | `/verify-email/?uid=&token=` | Email 驗證，通過後啟用並回 JWT |
| POST | `/verify-email/resend/` | 重寄驗證信（需 email + password） |
| POST | `/password-reset/request/` | 忘記密碼請求（無論 email 是否存在皆回 200） |
| POST | `/password-reset/confirm/` | 用 uid + token 重設密碼，成功後作廢所有 session |

### 使用者自身（`/api/members/`）
| Method | Path | 說明 |
|---|---|---|
| GET/PUT/PATCH | `/me/` | 讀取／更新 profile（email 唯讀） |
| PUT | `/me/password/` | 修改密碼（需舊密碼；成功後作廢所有 session） |

### Staff only（`/api/admin/`）
| Method | Path | 說明 |
|---|---|---|
| PATCH | `/members/<id>/active/` | 切換指定使用者 `is_active`；停用時順帶作廢其 refresh token |
