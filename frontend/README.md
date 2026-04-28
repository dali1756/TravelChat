# Frontend

Travel Chat 前端使用 React + TypeScript + Vite。

## 開發指令

```bash
npm install
npm run dev
npm run build
npm run lint
npm test
```

## 環境變數

複製 `.env.example` 為 `.env`，依需要調整：

| 變數 | 預設 | 說明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | 後端 REST API 起始位址；瀏覽器於 dev 時直接打 host port |

## UI 風格規範

前端畫面風格請以深色系、科技感、偏產品化介面為主，詳細規範見：

- [STYLE_SPEC.md](/Users/jeter/jobs/django_channel/frontend/STYLE_SPEC.md)

實作新頁面前，先對照這份 spec，再決定版型、色彩、字體與元件樣式。
