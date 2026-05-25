# 📅 智能 LINE 互動會議提醒系統

這是一個使用 **Python + Flask** 開發的互動式會議與行程管理提醒系統。
使用者可以直接透過 LINE 機器人以「自然語言」告知行程的**主題、日期、時間、地點**，系統將透過 **Gemini API** 智慧解析，並自動執行以下任務：
1. **Google 行事曆同步**：自動在 Google Calendar 中建立行程活動。
2. **Gmail SMTP 確認信**：建立成功後立即寄送 HTML 格式的通知信。
3. **對話狀態補齊**：若使用者少提供了時間或地點等欄位，機器人會智慧對話引導補齊。
4. **雙重管道行前提醒**：在行程開始前 **1.5 小時（90 分鐘）**，自動同時發送 **LINE 推播訊息**與 **Gmail 提醒信**。

---

## 🛠️ 功能特色

- **對話引導機制**：自動暫存會話狀態，缺少「主題、日期、時間、地點」任一項時，主動詢問補齊。
- **Gemini 智慧解析**：支援中文自然語言輸入（例如：「明天下午3:00在延平817討論專案」），自動轉換相對日期。
- **防止重複通知**：使用 SQLite 資料庫持久化紀錄，每項行程提醒僅發送一次。
- **時區鎖定**：鎖定 `Asia/Taipei`（台北時間），避免因部署伺服器時區不同導致排程錯亂。
- **高相容部署**：提供 Webhook 與健康檢查，可完美運行於 Render、Railway、Ubuntu VPS 或本地。
- **容錯與重試**：發送 LINE 與 Email 具有指數型倒退重試機制。

---

## 📂 專案目錄結構

```
aaa/
├── app.py                  # 網頁伺服器主入口 (處理 Webhook & 啟動背景排程器)
├── config.py               # 環境變數與日誌設定
├── database.py             # SQLite 資料庫操作 (對話狀態 session & 行程 reminder 儲存)
├── authorize_google.py     # 本地一次性 Google OAuth 授權工具
├── requirements.txt        # 依賴套件清單
├── .env.example            # 環境變數範本
└── services/
    ├── gemini_service.py   # Gemini 自然語言解析服務
    ├── calendar_service.py # Google Calendar API 服務
    ├── email_service.py    # Gmail SMTP 信件服務
    └── line_service.py     # LINE Message API (Reply/Push) 服務
```

---

## 🚀 準備工作與設定步驟

### 1. LINE Developers 設定
1. 登入 [LINE Developers Console](https://developers.line.biz/)。
2. 建立一個 **Provider**（若無）。
3. 建立一個 **Messaging API Channel**。
4. 在 **Messaging API settings** 頁面：
   - 啟用 Messaging API。
   - 產生 **Channel Access Token**（設定至環境變數 `LINE_CHANNEL_ACCESS_TOKEN`）。
   - 設定 Webhook URL：例如 `https://your-app-domain.com/webhook` (需為 HTTPS)。
   - 開啟 **Use webhook**。
   - **停用** LINE 官方帳號的自動回覆訊息與歡迎訊息（在 LINE Official Account Manager 中設定）。
5. 在 **Basic settings** 頁面：
   - 取得 **Channel Secret**（設定至環境變數 `LINE_CHANNEL_SECRET`）。
   - 取得您的 **Your user ID**（設定至環境變數 `LINE_USER_ID`，用於發送 1.5 小時前的 Push 訊息）。

### 2. Gmail SMTP 設定
因為系統採用 SMTP 連線，您需要使用 Gmail 帳號發送郵件：
1. 進入您的 Google 帳戶管理網頁。
2. 啟用「**兩步驟驗證**」（必要前提）。
3. 在搜尋欄搜尋「**應用程式密碼** (App Passwords)」。
4. 建立一個新密碼（例如命名為 "Reminder System"），產生一組 16 字元的密碼。
5. 將此密碼設定至環境變數 `SMTP_PASSWORD`，將您的 Gmail 設定至 `SMTP_USER`。

### 3. Google Calendar API 設定
本系統需要與您的 Google 行事曆連動：
1. 進入 [Google Cloud Console](https://console.cloud.google.com/)。
2. 建立新專案，並在 API 庫中搜尋並啟用 **Google Calendar API**。
3. 進入「**OAuth 同意畫面**」：
   - 選擇 **External**，填寫必要的 App Name 和 Email。
   - 測試使用者 (Test users) 中加入您自己的 Google 帳號。
4. 進入「**憑證** (Credentials)」：
   - 點擊「建立憑證」 -> 「**OAuth 2.0 用戶端識別碼**」。
   - 應用程式類型選擇「**傳統版應用程式** (Desktop App)」。
   - 建立後下載 JSON 檔案，並將檔案重新命名為 **`credentials.json`**，放置於專案根目錄下。
5. **本地授權取得 Token**：
   - 在本地終端機執行 `python authorize_google.py`。
   - 系統會開啟瀏覽器請您登入 Google 帳號並授權日曆權限。
   - 授權完成後，專案根目錄下會自動生成 **`token.json`**。
   - 終端機亦會印出單行 JSON 字串，請複製並保存，這在雲端部署時非常重要。

---

## 💻 本地運行與測試

### 1. 安裝套件
請確保您的電腦已安裝 Python 3.8+，並執行以下命令安裝依賴：
```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
將 `.env.example` 複製為 `.env` 並填入各項參數：
```bash
cp .env.example .env
```
*(在 Windows 上可手動複製並重新命名為 `.env`)*

### 3. 啟動伺服器
```bash
python app.py
```

### 4. 設定本地 Webhook 測試環境
由於 LINE 需要 HTTPS Webhook 才能運作，您可以使用 `ngrok` 來進行對外穿透：
```bash
# 安裝並執行 ngrok 將本地 5000 端口映射出去
ngrok http 5000
```
複製 ngrok 產生的 `https://xxxx.ngrok-free.app` 網址，並將 `https://xxxx.ngrok-free.app/webhook` 貼回 LINE Developers Console 的 Webhook URL 欄位中，點擊 **Verify** 確認回傳 `Success`。

### 5. 測試流程
- **完整輸入測試**：在 LINE 對話框發送 `明天下午3:00在延平817討論專案`。機器人應回覆成功排定並同步 Google 日曆，您也應收到 Gmail 確認信。
- **對話引導測試**：發送 `討論專案`。機器人會回覆已記錄主題，但提示缺少日期、時間與地點。接著依序發送 `5月26日`、`下午三點`、`地點在延平817`。欄位補齊後，行程同樣建立成功！
- **取消與清空**：如果輸入過程中想要重新開始，發送 `取消` 即可清空暫存對話。
- **1.5小時提醒測試**：
  - 您可以故意新增一個起迄時間為 **現在時間起的 80 分鐘後** 的行程。
  - 因為該時間小於 90 分鐘且大於 -30 分鐘，背景排程器（每分鐘執行一次）將在 1 分鐘內捕捉到該行程，並自動向您發送 LINE 提醒推播與 Gmail 提醒信！

---

## ☁️ 雲端平台部署指引

### A. 部署至 Render 或 Railway (推薦)
1. **建立 Web Service**：
   - 連結您的 GitHub 儲存庫。
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py` (注意：請直接使用 `python app.py` 啟動以確保背景排程執行緒正常運作，不建議使用多 Worker 的 Gunicorn 以防重複啟動排程器)。
2. **設定環境變數 (Environment Variables)**：
   - 設定 `PORT`, `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, `LINE_USER_ID`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`, `GEMINI_API_KEY`。
   - 設定 **`GOOGLE_CREDENTIALS_JSON`**：將本地 `credentials.json` 的整段 JSON 內容複製貼上。
   - 設定 **`GOOGLE_TOKEN_JSON`**：將本地 `token.json` 的整段 JSON 內容複製貼上。

### B. 部署至 Ubuntu Server / VPS
1. 將專案檔案上傳至伺服器。
2. 建立並啟用 Python 虛擬環境，安裝相依套件：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. 建立 systemd 服務檔以維持背景守護運行：
   ```bash
   sudo nano /etc/systemd/system/reminder-bot.service
   ```
   寫入以下內容：
   ```ini
   [Unit]
   Description=LINE Meeting Reminder Bot Service
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/aaa
   ExecStart=/home/ubuntu/aaa/venv/bin/python app.py
   Restart=always
   EnvironmentFile=/home/ubuntu/aaa/.env

   [Install]
   WantedBy=multi-user.target
   ```
4. 啟動並啟用服務：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start reminder-bot.service
   sudo systemctl enable reminder-bot.service
   ```
5. 查看日誌確認運行：
   ```bash
   sudo journalctl -u reminder-bot.service -f
   ```
