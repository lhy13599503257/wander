# Project Wander 🌍✈️

**Slogan:** Not just a trip, it's *your* journey.
**Goal:** An AI-powered travel planning assistant that personalizes every step, from visa prep to daily itineraries.

## 核心理念 (Core Philosophy)
- **Hyper-Personalized:** 基于用户详细画像（居住地、护照、风格、购物偏好）的定制化。
- **End-to-End Anxiety Relief:** 解决旅行前的焦虑（签证、机票提醒），而不只是旅行中的玩乐。
- **Start Small, Dream Big:** 从最小可行性产品 (MVP) 开始，逐步迭代。

## 🌟 功能列表 (Features)

### 1. 深度用户画像 (The Traveler Profile) 👤
- **基础信息:** 居住地、护照国籍、签证持有情况（如美签、申根签）。
- **旅行风格:**
  - 节奏: 特种兵 (Fast) vs. 慢节奏/度假 (Slow)
  - 类型: Citywalk, 运动/户外, 购物, 美食, 历史/文化
- **交通偏好:**
  - 城市间: 直飞 vs. 转机 (价格敏感度)
  - 城市内: Public Transit, Uber/Taxi, 包车, Citywalk
- **住宿偏好:** 酒店等级 (星级), 预算范围, 位置偏好 (市中心 vs. 安静郊区)
- **购物偏好:** 具体的品牌/品类 (e.g., Supreme, Vintage, 奢侈品, 当地手工艺)

### 2. 智能行程规划 (AI Itinerary Generator) 🗺️
- **Input:** 目的地 + 天数 + 用户画像
- **Output:**
  - 每日行程安排 (Morning/Afternoon/Evening)
  - 路线规划 (串联景点和购物点)
  - 购物点插入 (基于偏好自动匹配附近的店)

### 3. 智能提醒与准备 (The Smart Pre-Travel Checklist) ⏰
- **签证助手:**
  - 根据护照+目的地，自动判断是否需要签证。
  - 提供官方签证申请链接 (DIY Friendly)。
  - **提醒功能:** "你还有 2 个月出发，现在必须办签证了！"
- **机票助手:**
  - 价格趋势预测（未来功能）。
  - **提醒功能:** "建议提前 3 个月买票，现在价格合适。"

## 🛠️ 技术栈 (Tech Stack - Tentative)
- **Frontend:** Flutter / React Native (跨平台 App) 或微信小程序 (MVP)
- **Backend:** Python (FastAPI) / Node.js
- **AI Core:** GPT-4o / Gemini (处理规划逻辑)
- **Database:** PostgreSQL / Firebase (存储用户画像)

## 📅 开发计划 (Roadmap)
- [ ] **Phase 1 (MVP):** 核心画像录入 + 基础文本行程生成 + 签证链接库
- [ ] **Phase 2:** 地图集成 + 实时机票/酒店价格
- [ ] **Phase 3:** 社区分享 + 商业化 (广告/返利)
