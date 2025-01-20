# Github-Action-based-Weather-forecast-scheduled-email

這是一個基於 GitHub Actions 的自動化天氣預報郵件系統，每天早上 8 點會自動發送天氣預報信息。

## 功能特點

- 自動發送每日天氣預報郵件
- 支援溫度資訊（當前溫度、最高溫、最低溫）
- 降雨預報提醒
- 紫外線指數警示
- 支援台灣各縣市天氣查詢

## 使用技術

- Python
- GitHub Actions（自動化排程）
- 中央氣象署開放資料平台 API
- Gmail SMTP 服務

## 環境設置

1. 複製專案到本地
2. 在 GitHub Secrets 中設置以下環境變數：
   - `EMAIL_ADDRESS`: 發送郵件的 Gmail 帳號
   - `EMAIL_PASSWORD`: Gmail 應用程式密碼
   - `CWA_API_KEY`: 中央氣象署 API 金鑰

## 配置說明

1. 在 `main.py` 中設置用戶資訊：
   ```python
   user_settings[email] = {
       "location": "臺北市",  # 想要獲取天氣資訊的城市
       "send_time": "08:00",  # 發送時間
       "rain_alert": True,    # 是否開啟降雨提醒
       "uv_alert": True       # 是否開啟紫外線提醒
   }
   ```

2. GitHub Actions 設置為每天早上 8 點（UTC+8）自動執行

## 注意事項

- 需要有中央氣象署的 API 授權碼
- 發送郵件的 Gmail 帳號需要開啟「安全性較低的應用程式存取權」或使用應用程式密碼
- 確保 GitHub Actions 有足夠的執行額度

## 授權

MIT License
