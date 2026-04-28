# Frontend Style Spec

## 目標

Travel Chat 前端畫面以「深色系 + 科技風 + 高可信度產品感」為主軸。

介面應該給人以下感受：

- 穩定、冷靜、專業
- 有即時通訊與 AI 工具產品的科技感
- 不走花俏霓虹夜店風，也不做廉價 Cyberpunk style
- 優先做出清晰層次與高資訊可讀性

## 實作方式

- 樣式實作以 `Bootstrap` 為主
- 不以手刻 component CSS 為主要策略
- 允許保留少量全域樣式，用於字體載入、design tokens、background、動畫 keyframes 與 third-party override
- 新元件優先透過 Bootstrap component、Bootstrap utility classes、共用 wrapper component 來完成
- 不直接使用預設 Bootstrap 外觀上線，必須做主題化調整成符合本 spec 的深色科技風

## 視覺方向

- 主色調以深藍黑、石墨黑、冷灰、水泥灰等為基底
- 點綴色使用冷色系高亮 accent，例如 cyan、teal、electric blue
- 避免大面積純黑；改用有層次的深色背景
- 避免高飽和紫色作為主要品牌色
- 重要操作區塊要有微弱發光或邊框高光，但不能過度

## 色彩系統

建議優先定義 design tokens，並映射到 Bootstrap theme 與全域 CSS variables，後續所有頁面共用。

```css
:root {
  --bg-app: #07111f;
  --bg-surface: #0d1726;
  --bg-surface-alt: #132033;
  --bg-elevated: #18283f;
  --border-subtle: rgba(148, 163, 184, 0.18);
  --border-strong: rgba(96, 165, 250, 0.34);
  --text-primary: #e6eef8;
  --text-secondary: #9fb2c8;
  --text-muted: #6f839a;
  --accent-primary: #3ecbff;
  --accent-secondary: #19b8a6;
  --accent-danger: #ff6b81;
  --success: #2dd4bf;
  --warning: #fbbf24;
  --shadow-soft: 0 18px 48px rgba(3, 8, 20, 0.38);
  --glow-accent: 0 0 0 1px rgba(62, 203, 255, 0.16), 0 0 24px rgba(62, 203, 255, 0.12);
}
```

## 背景規則

- App 最外層背景不要只用單色，應搭配漸層或低對比光暈
- 可使用 radial gradient 製造科技感，但透明度要低
- 面板、卡片、聊天室清單、訊息區塊要靠明暗層次分出深度
- 背景重點是「有空氣感」，不是花紋堆滿

建議方向：

- 主背景：深藍黑漸層
- 局部光源：左上或右上淡 cyan glow
- 區塊底色：比主背景亮一階

## 字體規則

- 避免預設系統字或單純 `Arial` / `Roboto`
- 中文介面建議使用 `Noto Sans TC`、`IBM Plex Sans TC`
- 英文標題可搭配 `Space Grotesk` 或 `Sora`
- 數字、時間、代碼、狀態值可用 `JetBrains Mono`
- 標題字重明確，內文保持乾淨，不做過度誇張字效

## 排版規則

- 採用寬鬆但有節奏的 spacing，不要把元件擠滿
- 區塊之間用間距與層級分隔，不依賴粗重邊框
- 標題、說明、控制區、內容區要有明確視覺節奏
- 手機版要優先維持可讀性與點擊區大小，不可只縮小桌面版

## 元件風格

### Card / Panel

- 使用深色面板搭配細邊框
- 圓角偏中等，不做過圓膨脹感
- Hover 可有輕微上浮、亮度提升或 border accent

### Button

- Primary button 使用冷色亮面 accent
- Secondary button 走深底 + 細框
- Danger button 用偏粉紅紅或 coral red，避免飽和純紅
- 禁止使用過於亮白的按鈕底色

### Input / Form

- 深色底、淺色字、清楚 focus ring
- Focus 狀態優先用 accent border 或外層 glow
- Placeholder 顏色要弱，但仍需可辨識
- 錯誤訊息用簡潔文字加 danger 色，不要只靠顏色表達

### Chat UI

- 房間列表與訊息區要有明確切面感
- 自己的訊息與對方訊息用底色與對齊區分
- 未讀狀態用小而明確的 badge，不做過大紅點
- 已讀標記、時間戳、系統提示應弱化，但仍可快速掃讀

### AI / Planner 區塊

- AI 回應區可增加淡發光邊框或品牌色左側線條
- 行程規劃卡片強調結構與資訊層次，不靠誇張插畫
- 有資料流感，但不能讓畫面太硬或太工程化

## 動效規則

- 動效要有目的，主要用在載入、切換、hover、訊息進場
- 時間以 160ms 到 280ms 為主，避免拖沓
- 可使用 fade + translateY 的輕量進場
- 發光、blur、scale 效果都要克制
- 不要全頁面到處做浮動動畫

## Icon 與插圖

- Icon 風格保持簡潔、線性、現代
- 避免過度可愛或擬物化圖示
- 插圖若使用，應偏 abstract / product / map / signal 類型
- 裝飾素材只做襯托，不可搶主資訊

## 頁面實作原則

- 優先建立全域 design tokens，再做頁面
- 每個新頁面至少先確認：背景、主卡片、文字階層、按鈕層級、狀態色
- 同類元件要共享樣式，不要每頁各自長不一樣
- 以 Bootstrap 為主要樣式語言，避免頁面同時混用多套 UI framework 視覺規則
- 可將常用樣式抽成共用 wrapper component 或語意化 class，但不要退回大規模手寫 CSS

## Do

- 使用深色分層背景建立空間感
- 用亮色 accent 聚焦互動點
- 讓聊天、AI、行程規劃都保持一致的產品語言
- 重視桌機與手機版的閱讀節奏

## Don't

- 不要做成大面積純黑加純藍發光的廉價科技風
- 不要把大量樣式散落成不可維護的手刻 CSS 檔
- 不要用預設 Bootstrap 樣式直接上線
- 不要混入多套不一致的 accent 色
- 不要只追求酷炫，忽略表單與資訊的清楚程度

## Bootstrap 實作備註

- 色彩、陰影、圓角、字級、spacing 收斂到 Bootstrap theme token 與全域變數
- 重複出現的卡片、按鈕、badge、input 樣式應抽成共用 pattern
- 可搭配 Bootstrap utility classes，但不要讓頁面被零散 class 堆到不可維護
- 若同一組樣式規則在三個以上地方重複，應考慮抽 wrapper component 或共用 class

## 交付標準

前端畫面完成時，至少應符合以下條件：

- 一眼看得出是深色科技風，而不是預設模板頁
- 所有主要元件在同一套色彩與層級邏輯下運作
- 文字對比足夠，表單與聊天資訊易讀
- 手機版與桌面版都能正常使用
- 新畫面與既有畫面並排時，不會像不同產品
