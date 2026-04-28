# Travel Chat - Development Roadmap
這是一個結合 AI 旅行規劃和即時通訊的旅行規劃產品，使用者可以與 AI 對談規劃行程、與朋友討論，並將 AI 產生的行程儲存到個人行程表中。

---

## 架構
```bash
User (Frontend)
    |
    +-- HTTP (REST API)
    |     +-- /api/auth/        --> 註冊、登入、Token、驗證、密碼相關
    |     +-- /api/members/     --> 個人資料
    |     +-- /api/trips/       --> 行程 CRUD、景點
    |     +-- /api/chats/       --> 聊天室、訊息歷史記錄
    |
    +-- WebSocket
          +-- ws/chat/<room>/   --> 好友/群組聊天
          +-- ws/ai/<conv>/     --> AI（Gemini Streaming）
                                    |
                                    v AI 產生行程
                                    --> 儲存到行程表
```

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Django 6, Django REST Framework      |
| WebSocket      | Django Channels, Daphne (ASGI)       |
| Message Broker | Redis (Channel Layer)                |
| Auth           | JWT (SimpleJWT)                      |
| AI             | Google Gemini API                    |
| Database       | SQLite (dev) -> PostgreSQL (prod)    |
| Frontend       | TBD (React / Vue / Next.js)          |
| DevOps         | Docker Compose, uv                   |

## Backend App Structure

```bash
backend/
+-- core/       # Django settings, ASGI/WSGI, root URL config
+-- members/    # User management (auth, profile, friends)
+-- chats/      # Messaging (person-to-person, group, AI chat)
+-- trips/      # Trip planning (itineraries, attractions, schedules)
```

---

## Development Phases

### Phase 1: User System (members)

**Goal:** Users can register, log in, and get JWT tokens.

- [x] Custom User model (extend AbstractUser, soft delete, BCrypt)
- [x] Registration API (POST /api/auth/register/) - is_active=False until email verified
- [x] Login API (POST /api/auth/login/) - returns JWT, rate limited
- [x] Logout API (POST /api/auth/logout/) - blacklist refresh token
- [x] Token refresh API (POST /api/auth/token/refresh/) - rotation + blacklist
- [x] User profile API (GET/PUT/PATCH /api/members/me/)
- [x] Change password API (PUT /api/members/me/password/)
- [x] Email verification (send, verify, resend)
- [x] Password reset (request, confirm)
- [x] Admin set user active (PATCH /api/admin/members/<id>/active/)
- [x] Deployment config (SECRET_KEY, DEBUG, ALLOWED_HOSTS from env)
- [x] Database migration
- [x] Tests (101 passing)

### Phase 2: Real-time Chat - Direct Message MVP (chats)

**Goal:** Users can create 1-to-1 chat rooms and send real-time messages to each other.

- [x] Chat models (Room, Message)
- [x] ChatConsumer (WebSocket connect/disconnect/receive)
- [x] WebSocket routing (ws/chat/<room_id>/)
- [x] REST API to create/get direct chat room
- [x] REST API for chat room list (GET /api/chats/rooms/)
- [x] REST API for message history (GET /api/chats/rooms/<id>/messages/)
- [x] WebSocket JWT authentication
- [x] Tests

### Phase 2.5: Chat Enhancements - Group Chat and Read State (chats)

**Goal:** Extend direct chat foundation to support group conversations and basic read-state features.

- [ ] Group chat support (multiple users in one room)
- [ ] Group member management
- [x] Read receipt support
- [x] Unread count support
- [ ] Tests

### Phase 3: AI Chat - Gemini Integration (chats)

**Goal:** Users can chat with AI to discuss travel plans, with streaming responses.

- [ ] Install google-genai package
- [ ] AIConsumer (WebSocket connect/disconnect/receive)
- [ ] WebSocket routing (ws/ai/<conversation_id>/)
- [ ] Gemini Streaming API integration (typewriter effect)
- [ ] AI conversation history storage
- [ ] System prompt for travel planning context
- [ ] Tests

### Phase 4: Trip Planning (trips)

**Goal:** Users can create and manage trip itineraries.

- [ ] Create trips app
- [ ] Trip models (Trip, Day, Activity, Attraction)
- [ ] Trip CRUD API (POST/GET/PUT/DELETE /api/trips/)
- [ ] Day schedule management
- [ ] Share trip with other users
- [ ] Tests

### Phase 5: AI + Trip Integration

**Goal:** AI-generated travel plans can be saved directly to user's itinerary.

- [ ] AI response parsing (extract structured trip data)
- [ ] "Save to itinerary" action from AI chat
- [ ] AI refinement (user feedback -> adjusted plan)
- [ ] Attraction recommendations based on preferences
- [ ] Tests

### Phase 6: Frontend

**Goal:** Build the user interface.

- [ ] Choose framework (React / Vue / Next.js)
- [ ] Project setup in frontend/
- [ ] Auth pages (register, login)
- [ ] Chat UI (message list, input, room list)
- [ ] AI chat UI (streaming response display)
- [ ] Trip planner UI (calendar view, drag & drop)
- [ ] Responsive design (mobile support)

---

## Future Considerations

- **Database:** Migrate from SQLite to PostgreSQL before production
- **File Storage:** User avatars, trip photos (S3 or similar)
- **Notifications:** Push notifications for new messages
- **Map Integration:** Google Maps API for attraction visualization
- **Multi-language:** i18n support
- **Deployment:** CI/CD pipeline, cloud hosting
