# Travel Chat

一款結合 AI 旅行規劃與即時通訊的旅行規劃產品。

---

## 這個專案是什麼

Travel Chat 讓使用者**一邊跟 AI 對談規劃行程，一邊跟朋友討論，最後把行程存成可共同編輯的行程表**。

三個核心功能：

1. **即時通訊** — 一對一與群組聊天室，走 WebSocket，含已讀狀態與未讀數。
2. **AI 旅遊顧問** — 與 Google Gemini 對話並以串流回覆，帶旅遊規劃的 system prompt。
3. **行程規劃** — 建立行程 -> 每日排程（day）-> 當日活動（activity）-> 可關聯景點（attraction），並可分享給其他使用者，以 owner / editor / viewer 三種角色控制權限。

### 目前完成度

| 範圍 | 狀態 |
|---|---|
| 後端：會員系統（註冊、登入、JWT、Email 驗證、密碼重設、軟刪除） | 完成 |
| 後端：即時聊天（一對一、群組、已讀／未讀） | 完成 |
| 後端：AI 聊天（Gemini 串流、對話歷史） | 完成 |
| 後端：行程規劃與分享（trips / days / activities / attractions / members） | 完成 |
| 前端：登入註冊、聊天 UI、行程規劃 UI | 完成 |
| 前端：AI 聊天 UI（串流打字機渲染） | 未完成 |
| AI 產生的行程「一鍵存入行程表」整合 | 未完成 |
| RWD 設計 | 未完成 |

詳細的階段規劃見 [ROADMAP.md](ROADMAP.md)。

---

## 系統架構

```
瀏覽器（React SPA，:5173）
    │
    ├─ HTTP / REST（:8000）
    │     ├─ /api/auth/      註冊、登入、JWT、Email 驗證、密碼重設
    │     ├─ /api/members/    個人資料、使用者搜尋
    │     ├─ /api/admin/      管理功能（staff only）
    │     ├─ /api/chats/      聊天室、訊息歷史、AI 對話歷史
    │     └─ /api/trips/      行程、每日排程、活動、景點、成員
    │
    └─ WebSocket（:8000，Daphne ASGI）
          ├─ ws/chat/<room_id>/         好友／群組聊天
          └─ ws/ai/<conversation_id>/   AI 串流對話
                                            │
                        Redis（:6379）──────┘  Channel Layer（跨連線廣播）
                        PostgreSQL（:5432）    資料持久化
```

---

## 技術棧

| 層 | 技術 |
|---|---|
| 後端 | Python 3.12、Django 6、Django REST Framework |
| WebSocket | Django Channels、Daphne（ASGI） |
| Message Broker | Redis 7（Channel Layer） |
| 認證 | JWT（SimpleJWT，含 rotation + blacklist）、BCrypt 密碼雜湊 |
| AI | Google Gemini（`google-genai`），未設 API key 時自動走 stub 假串流 |
| 資料庫 | PostgreSQL 16 |
| 前端 | React 19、TypeScript、Vite、react-router-dom v7、react-bootstrap |
| 前端測試 | Vitest + @testing-library |
| 後端測試 | pytest + pytest-django |
| DevOps | Docker Compose、uv（Python 套件管理）、npm |

---

## 專案結構

```
django_channel/
├── .env                    <- 後端讀取的環境變數（需自行建立，見下方步驟）
├── .env.example            <- 後端環境變數範本
├── docker-compose.yml      <- 四個服務：frontend / backend / db / redis
├── ROADMAP.md              <- 開發階段與進度
├── backend/
│   ├── core/               Django settings、ASGI/WSGI、root URL
│   ├── members/            會員（認證、個人資料、軟刪除）
│   ├── chats/              聊天（一對一、群組、AI），consumers + routing
│   │   └── ai/             AI provider 抽象層（gemini / stub）
│   ├── trips/              行程規劃（Trip / TripDay / Activity / Attraction / TripMember）
│   ├── tests/              pytest 測試（依 app 分子目錄）
│   └── pyproject.toml
├── frontend/
│   ├── .env                <- 前端環境變數（需自行建立）
│   ├── .env.example
│   ├── src/
│   │   ├── auth/           AuthContext、ProtectedRoute
│   │   ├── components/     可重用元件（modal、表單、badge）
│   │   ├── layouts/        AppShell（導覽列 + Outlet）
│   │   ├── lib/            api client（apiFetch）、chatApi、tripApi、型別
│   │   ├── pages/          各頁面
│   │   ├── styles/         design tokens + Bootstrap 主題
│   │   └── router.tsx
│   ├── tests/              Vitest 測試（對應 src 結構）
│   └── STYLE_SPEC.md       UI 風格規範（實作新畫面前必讀）
└── openspec/               規格驅動開發的規格與變更提案
```

---

## Setup

這條路線**不需要**在本機安裝 Python、Node、PostgreSQL、Redis，只要有 Docker 就好。

### 你需要先安裝

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（含 Docker Compose）
- Git

### 步驟 1：取得程式碼

```bash
git clone https://github.com/dali1756/TravelChat.git
cd django_channel
```

### 步驟 2：建立兩個環境變數檔

這個專案有**兩份** `.env`。根目錄那份是**必要的**（缺少會導致後端無法啟動）；`frontend/.env` 是選用的（程式碼內建的預設值與範本相同，但仍建議建立，日後改埠號或部署時才有地方調整）：

```bash
# 後端（在專案根目錄，注意不是 backend/）— 必要
cp .env.example .env

# 前端 — 選用
cp frontend/.env.example frontend/.env
```

接著編輯根目錄的 `.env`，**填入 `SECRET_KEY`**：

```bash
# 產生一組隨機字串貼進 SECRET_KEY=
openssl rand -base64 48
```

其餘變數的預設值已經是 Docker 環境可直接運作的設定（`DB_HOST=db`、`REDIS_HOST=redis` 是 Docker 內部的服務名稱），不用改。

> `GEMINI_API_KEY` 留空即可。留空時 AI 聊天會走 stub 假串流，整套流程仍可完整操作；之後申請到金鑰再填入就會自動切換成真的 Gemini，不需要改任何程式碼。

### 步驟 3：啟動所有服務

```bash
docker-compose up
```

這會一次啟動**四個**服務：frontend（:5173）、backend（:8000）、PostgreSQL（:5432）、Redis（:6379）。

> **改程式碼後要不要重啟？**
> - **前端**：`frontend/` 以 volume 掛載進 container，Vite dev server 提供 HMR，存檔後瀏覽器自動更新，不需重啟。
> - **後端**：container 以 `daphne` 啟動（見 `backend/Dockerfile`），**不會自動重載**。改完 `backend/` 的程式碼要執行 `docker-compose restart backend` 才會生效。
> - 或是不想 `restart` 也可以 `docker-compose down` -> `docker-compose up`。
> - 新增／移除套件（`pyproject.toml`、`package.json`）：需要 `docker-compose up --build` 重建 image。

### 步驟 4：建立資料庫表

```bash
docker-compose exec backend uv run python manage.py migrate
```

### 步驟 5：建立管理員帳號

```bash
docker-compose exec backend uv run python manage.py createsuperuser
```

會依序詢問 **Email**、Username、密碼。
注意本專案的登入帳號是 **email 而非 username**。

管理員帳號建立後即為啟用狀態（`is_active=True`），可以直接登入。

### 步驟 6：確認一切正常

| 打開這個網址 | 應該看到 |
|---|---|
| http://localhost:5173 | 前端登入頁 |
| http://localhost:8000/admin/ | Django 管理後台登入頁 |
| http://localhost:8000/api/trips/ | `{"detail":"Authentication credentials were not provided."}` <- 這是正確的，代表 API 活著且權限生效 |

用步驟 5 建立的管理員 email / 密碼登入 http://localhost:5173 ，就會進入對話列表頁。

### 步驟 7：建立可以互相聊天／分享行程的測試帳號

這一步有兩個容易卡住的地方，先說明原因再給做法：

1. 透過前端註冊的帳號預設 `is_active=False`，**必須完成 email 驗證才能登入**。
2. 開發環境的 `EMAIL_BACKEND` 是 console，信件不會真的寄出，而是**印在 backend 的 log 裡**。而且信中的驗證連結指向 `http://localhost:5173/verify-email?...`，但前端目前**還沒有這個頁面**（屬未完成範圍），直接點會是空白頁。
3. 管理員帳號雖然能登入，但為了避免帳號枚舉，後端的使用者搜尋 API 會**排除 superuser 與 username 為 admin 的帳號**。所以管理員帳號搜尋不到，無法用來測試聊天或行程分享。

因此請建立**兩個一般帳號**，並用以下任一方式啟用：

**方式 A：透過 Django 管理後台啟用（最簡單）**

1. 在 http://localhost:5173/register 註冊兩個帳號（例如 `alice@test.com`、`bob@test.com`）。
2. 用管理員登入 http://localhost:8000/admin/ 。
3. 進入 **Users**，點開帳號，勾選 **Active**，儲存。
4. 回前端即可登入。

**方式 B：使用 log 裡的驗證連結**

1. 註冊後，在跑 `docker-compose up` 的終端機找到印出的驗證信內容，複製其中的 `uid` 與 `token`。
2. 把網址改成打後端 API（把 `5173/verify-email?` 換成 `8000/api/auth/verify-email/?`）並在瀏覽器開啟：

   ```
   http://localhost:8000/api/auth/verify-email/?uid=<貼上 uid>&token=<貼上 token>
   ```

3. 回傳 JWT 即代表啟用成功。

兩個帳號都啟用後，就能用其中一個帳號搜尋另一個，開始聊天或分享行程。

---

## 本機開發（不使用 Docker）

適合想直接在本機跑、用 IDE debug 的情境。

### 你需要先安裝

- Python 3.12（本專案以 `.python-version` 指定）
- [uv](https://docs.astral.sh/uv/)（Python 套件與虛擬環境管理）
- Node.js 22 + npm
- PostgreSQL 16（需自行建立資料庫）
- Redis 7（WebSocket 的 Channel Layer 必需，未啟動則聊天功能無法連線）

### 重要：先改 `.env` 的兩個 host

`.env.example` 的預設值是給 Docker 用的服務名稱。本機直跑時必須改成 localhost，否則會出現 `could not translate host name "db"` 之類的錯誤：

```diff
- DB_HOST=db
+ DB_HOST=127.0.0.1
- REDIS_HOST=redis
+ REDIS_HOST=127.0.0.1
```

並確認 PostgreSQL 內已存在 `DB_NAME` 指定的資料庫（預設 `django_channel`）：

```bash
createdb django_channel
```

### 啟動後端

```bash
cd backend
uv sync --group dev                      # 安裝套件（自動建立 .venv）
uv run python manage.py migrate          # 建立資料表
uv run python manage.py createsuperuser  # 建立管理員（帳號為 email）
uv run python manage.py runserver        # 啟動於 http://localhost:8000
```

> 因為 `daphne` 已列在 `INSTALLED_APPS` 的第一位，`runserver` 會以 ASGI 模式啟動，WebSocket 一併可用，不需要另外跑 daphne。

### 啟動前端（另開一個終端機）

```bash
cd frontend
npm install
npm run dev        # 啟動於 http://localhost:5173
```

前端的 `.env` 預設指向 `http://localhost:8000`，與上面的後端一致，不需修改。

---

## 服務與埠號

| 服務 | 埠號 | 用途 |
|---|---|---|
| frontend | 5173 | Vite dev server（React SPA） |
| backend | 8000 | REST API + WebSocket（Daphne ASGI） |
| db | 5432 | PostgreSQL |
| redis | 6379 | Channels 的 Channel Layer |

後端已設定 CORS 允許 `http://localhost:5173` 與 `http://127.0.0.1:5173`。
若你改了前端埠號，需同步調整 `backend/core/settings.py` 的 `CORS_ALLOWED_ORIGINS`。

---

## 環境變數

### 後端：專案根目錄的 `.env`

由 `backend/core/settings.py` 以 `load_dotenv` 從**專案根目錄**讀取（不是 `backend/.env`）。

| 變數 | 用途 | 預設 | 備註 |
|---|---|---|---|
| `SECRET_KEY` | Django SECRET_KEY | **必填** | 留空或缺少會導致啟動失敗 |
| `DJANGO_DEBUG` | Debug 模式 | `False` | 僅 `"True"` / `"1"` / `"true"` 會開啟 |
| `ALLOWED_HOSTS` | 允許的 Host | `localhost,127.0.0.1` | 生產環境必須指定 |
| `FRONTEND_URL` | 前端 base URL | `http://localhost:5173` | 用於 email 內的驗證／重設密碼連結 |
| `EMAIL_BACKEND` | Email 後端 | console（印到 stdout） | 生產環境請改為 SMTP |
| `DEFAULT_FROM_EMAIL` | 寄件者 | `noreply@localhost` | |
| `LOGIN_THROTTLE_RATE` | 登入速率限制 | `5/min` | DRF 格式，例如 `10/min` |
| `REDIS_HOST` | Redis host | `127.0.0.1` | Docker 環境用 `redis` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | PostgreSQL 連線 | 見 `.env.example` | Docker 環境 `DB_HOST=db` |
| `GEMINI_API_KEY` | Gemini API 金鑰 | 空（走 stub 假串流） | 填入後自動切換真 Gemini，無需改 code |
| `GEMINI_MODEL` | Gemini 模型 | `gemini-2.0-flash` | |

### 前端：`frontend/.env`

| 變數 | 用途 | 預設 |
|---|---|---|
| `VITE_API_BASE_URL` | 後端 REST API 起始位址 | `http://localhost:8000` |
| `VITE_WS_BASE_URL` | 後端 WebSocket 起始位址 | `ws://localhost:8000` |

> 新增任何環境變數時，請同步更新對應的 `.env.example`（含註解說明）。

---

## 常用命令

### 服務控制

```bash
docker-compose up                    # 啟動所有服務（frontend / backend / db / redis）
docker-compose up --build            # 新增或移除套件後需 rebuild
docker-compose down                  # 停止所有服務
docker-compose restart backend       # 改完後端程式碼後套用變更（daphne 不會自動重載）
docker-compose logs -f backend       # 只看後端 log（找驗證信連結時很有用）
docker-compose exec backend bash     # 進入後端 container
```

### 資料庫

```bash
docker-compose exec backend uv run python manage.py showmigrations   # 檢視 migration 狀態
docker-compose exec backend uv run python manage.py makemigrations   # 產生 migration
docker-compose exec backend uv run python manage.py migrate          # 套用 migration
docker-compose exec db psql -U postgres -d django_channel            # 連進 PostgreSQL
```

### 後端測試與程式碼檢查（在 `backend/` 執行）

```bash
cd backend
uv run pytest -q                  # 執行所有測試
uv run pytest tests/trips/        # 只跑某個 app 的測試
uv run pytest tests/xxx/xxx.py    # 執行單一測試檔
uv run ruff check .               # 檢查 Python 程式碼規範
uv run ruff format .              # 自動格式化
```

> 後端測試使用 `tests/settings.py`：資料庫為 sqlite in-memory、Channel Layer 為 InMemory、Email 為 locmem。**因此跑測試不需要啟動 Docker、PostgreSQL 或 Redis。**

### 前端測試與程式碼檢查（在 `frontend/` 執行）

```bash
cd frontend
npm test                          # 執行所有測試
npm test -- tests/pages/          # 只跑某個目錄
npm run test:watch                # Watch 模式（改檔案自動重跑）
npm run lint                      # ESLint
npm run build                     # 型別檢查（tsc）+ production build
```

---

## API 總覽

所有需要認證的端點皆使用 `Authorization: Bearer <access_token>`。前端的 `apiFetch` 已內建 401 自動 refresh。

### 認證（`/api/auth/`）

| Method | Path | 說明 |
|---|---|---|
| POST | `/register/` | 註冊（建立 `is_active=False` 的帳號並寄驗證信） |
| POST | `/login/` | 登入（帶 **email** + password；需 `is_active=True`）；預設速率 5/min |
| POST | `/logout/` | 登出（作廢 refresh token） |
| POST | `/token/refresh/` | 換發 access token（rotation + blacklist） |
| GET | `/verify-email/?uid=&token=` | Email 驗證，通過後啟用帳號並回傳 JWT |
| POST | `/verify-email/resend/` | 重寄驗證信（需 email + password） |
| POST | `/password-reset/request/` | 忘記密碼請求（無論 email 是否存在皆回 200，避免帳號枚舉） |
| POST | `/password-reset/confirm/` | 以 uid + token 重設密碼，成功後作廢所有 session |

### 使用者自身（`/api/members/`）

| Method | Path | 說明 |
|---|---|---|
| GET / PUT / PATCH | `/me/` | 讀取／更新個人資料（email 唯讀） |
| PUT | `/me/password/` | 修改密碼（需舊密碼；成功後作廢所有 session） |
| GET | `/search/?q=` | 搜尋使用者（用於發起聊天、分享行程）。以 **username 前綴**比對，只回傳 `is_active=True` 的帳號，最多 20 筆，並排除自己、superuser 與 username 為 `admin` 的帳號 |

### 聊天（`/api/chats/`）

| Method | Path | 說明 |
|---|---|---|
| GET | `/rooms/` | 我的聊天室列表（含最後訊息與未讀數） |
| POST | `/rooms/direct/` | 建立／取得一對一聊天室 |
| POST | `/rooms/group/` | 建立群組聊天室 |
| GET | `/rooms/<id>/messages/` | 訊息歷史 |
| POST | `/rooms/<id>/read/` | 標記已讀 |
| GET / POST | `/rooms/<id>/members/` | 群組成員列表／新增 |
| DELETE | `/rooms/<id>/members/<user_id>/` | 移除群組成員 |
| GET / POST | `/ai/conversations/` | AI 對話列表／建立 |
| GET | `/ai/conversations/<id>/messages/` | AI 對話歷史 |

### 行程（`/api/trips/`）

| Method | Path | 說明 |
|---|---|---|
| GET / POST | `/` | 我參與的行程列表／建立行程 |
| GET / PUT / PATCH / DELETE | `/<id>/` | 行程明細（含巢狀 days 與 activities）／修改（owner、editor）／刪除（僅 owner） |
| GET / POST | `/<id>/days/` | 每日排程列表／新增（日期需落在行程起訖範圍且不重複） |
| GET / PUT / PATCH / DELETE | `/<id>/days/<day_id>/` | 單日讀取／修改／刪除 |
| GET / POST | `/<id>/days/<day_id>/activities/` | 當日活動列表／新增 |
| GET / PUT / PATCH / DELETE | `/<id>/days/<day_id>/activities/<activity_id>/` | 活動讀取／修改（含以 `order` 調序）／刪除 |
| GET / POST | `/attractions/` | 景點列表／建立（任何登入使用者皆可建立） |
| GET | `/attractions/<id>/` | 景點明細 |
| GET / POST | `/<id>/members/` | 行程成員列表／分享（僅 owner，指派 editor 或 viewer） |
| DELETE | `/<id>/members/<user_id>/` | 移除成員（owner）／自行退出行程（成員本人） |

權限規則：非參與者一律回 **404**（不洩漏行程是否存在）；參與者但角色不足則回 **403**。

### WebSocket

| Path | 說明 |
|---|---|
| `ws/chat/<room_id>/` | 好友／群組聊天，需在連線時帶 JWT |
| `ws/ai/<conversation_id>/` | AI 串流對話 |

---

## 疑難排解

| 症狀 | 原因 | 解法 |
|---|---|---|
| 後端啟動即 `KeyError: 'SECRET_KEY'` 或 `SECRET_KEY setting must not be empty` | 根目錄 `.env` 不存在或 `SECRET_KEY` 留空 | `cp .env.example .env` 並填入 `openssl rand -base64 48` 產生的值 |
| `could not translate host name "db"` | 未使用 Docker 卻沿用 Docker 的 host 設定 | 把 `.env` 的 `DB_HOST` 改為 `127.0.0.1` |
| 聊天室連不上、WebSocket 一直斷線 | Redis 沒啟動，或 `REDIS_HOST` 設錯 | 啟動 Redis；本機直跑時 `REDIS_HOST=127.0.0.1` |
| 登入回「帳號或密碼錯誤」但密碼確實正確 | 帳號 `is_active=False`（尚未完成 email 驗證） | 見上方「步驟 7」用管理後台勾選 Active，或走驗證連結 |
| 登入時填 username 一直失敗 | 本專案的登入帳號是 **email** | 改填 email |
| 點驗證信連結是空白頁 | 前端尚未實作 `/verify-email` 頁面 | 改打後端 API：`http://localhost:8000/api/auth/verify-email/?uid=...&token=...` |
| 使用者搜尋找不到某個帳號 | 搜尋是 **username 前綴**比對（不是包含比對），且只回傳已啟用帳號，並排除自己、superuser 與 `admin` | 用 username 的**開頭**幾個字搜尋；確認對方 `is_active=True`；改用一般帳號而非管理員帳號測試 |
| 前端 API 請求被 CORS 擋 | 前端不是跑在 5173 | 調整 `backend/core/settings.py` 的 `CORS_ALLOWED_ORIGINS` |
| 改了後端程式碼但行為沒變 | container 以 `daphne` 啟動，不會自動重載 | `docker-compose restart backend` |
| 新增了 Python／npm 套件但容器內沒生效 | image 未重建 | `docker-compose up --build` |
| `relation "..." does not exist` / API 回 500 | 沒跑過 migration | `docker-compose exec backend uv run python manage.py migrate` |
| AI 回覆內容看起來像假的 | `GEMINI_API_KEY` 未設定，走 stub provider | 填入金鑰後重啟後端 |

---

## 開發規範

動手改程式前請先看這幾份文件：

| 文件 | 內容 |
|---|---|
| [ROADMAP.md](ROADMAP.md) | 開發階段、各階段完成狀態 |
| [CLAUDE.md](CLAUDE.md) | 常用指令速查 |
| [.claude/rules/api.md](.claude/rules/api.md) | API 設計規範（RESTful 命名、回應格式、安全性要求） |
| [frontend/STYLE_SPEC.md](frontend/STYLE_SPEC.md) | UI 風格規範（深色科技風、design tokens），實作新畫面前必讀 |
| `openspec/` | 規格驅動開發（SDD）的規格與變更提案 |

開發流程採 **SDD + TDD**：先寫規格 -> 寫一個會失敗的測試 -> 最小實作讓它通過 -> 視需要重構。
