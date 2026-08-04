# Frontend

Travel Chat 前端使用 React 19 + TypeScript + Vite。

> 第一次 setup 整個專案（含後端、資料庫、Redis）請看根目錄的 [README.md](../README.md)。
> 本文件只涵蓋前端本身。前端需要後端在 `http://localhost:8000` 運作才能登入。

## 開發指令

```bash
npm install          # 安裝套件
npm run dev          # 啟動 dev server（http://localhost:5173）
npm run build        # 型別檢查（tsc）+ production build
npm run lint         # ESLint
npm test             # Vitest（單次執行）
npm run test:watch   # Vitest watch 模式
```

## 環境變數

複製 `.env.example` 為 `.env`，依需要調整：

| 變數 | 預設 | 說明 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | 後端 REST API 起始位址；瀏覽器於 dev 時直接打 host port |
| `VITE_WS_BASE_URL` | `ws://localhost:8000` | 後端 WebSocket 起始位址（聊天用） |

## UI 風格規範

前端畫面風格請以深色系、科技感、偏產品化介面為主，詳細規範見：

- [STYLE_SPEC.md](STYLE_SPEC.md)

實作新頁面前，先對照這份 spec，再決定版型、色彩、字體與元件樣式。
