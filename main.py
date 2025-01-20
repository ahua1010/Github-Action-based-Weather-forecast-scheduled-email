from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

import logging
import os
import requests
from datetime import datetime

# 設定日誌
logging.basicConfig(level=logging.INFO)  # 設置日誌級別為INFO

# 用戶設定
user_settings = {}

email_sender = "shuaiahua@gmail.com" #os.environ.get("EMAIL_ADDRESS")
email_password = "zria hsmd prtp lkmz" #os.environ.get("EMAIL_PASSWORD")
api_key = "CWA-022D9A1D-57B9-4938-B42F-74BEEF7EEAAB" #os.environ.get("CWA_API_KEY")
smtp_server = "smtp.gmail.com"  # Adjust based on your email provider
smtp_port = 587  # Standard TLS port

# Replace send_reply and send_weather_info functions with email versions
def send_email(user_email, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = user_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)
        
        logging.info(f"Successfully sent email to {user_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {user_email}: {e}")

### 執行邏輯函式----------------------------------------------------------
# 獲取天氣資訊的函數
def get_weather(user_email, location):
    api_url_1 = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-089?Authorization={api_key}&locationName={location}"
    response_1 = requests.get(api_url_1)
    
    if response_1.status_code != 200:
        return "無法獲取天氣資訊，請檢查地點名稱或授權碼。"

    try:
        weather_data = response_1.json()
        data = weather_data['records']['Locations'][0]["Location"][0]
    except IndexError:
        logging.error(f"index超出json格式 location:{location}")
        return "無法解析天氣資料，請稍後再試。"

    # 計算最高溫和最低溫
    temps = []
    for time_data in data["WeatherElement"][0]["Time"]:
        temp = int(time_data["ElementValue"][0]["Temperature"])
        temps.append(temp)

    max_temp = max(temps)
    min_temp = min(temps)

    # 尋找當前溫度
    current_time = datetime.now()
    current_temp = None
    
    for time_data in data["WeatherElement"][0]["Time"]:
        start_time = datetime.strptime(time_data["DataTime"].replace('T', ' ').split('+')[0], "%Y-%m-%d %H:%M:%S")
        if current_time <= start_time:
            current_temp = int(time_data["ElementValue"][0]["Temperature"])
            break 
    
    if current_temp is None:
        logging.error("無法找到當前氣溫")
        current_temp = temps[0]  # 使用第一個可用溫度作為備選

    # 下雨預測
    threshold = 50
    rain_alert_message = ""
    if user_settings[user_email]['rain_alert']:
        for forecast in data['WeatherElement'][7]['Time']:
            start_time = datetime.strptime(forecast['StartTime'].replace('T', ' ').split('+')[0], '%Y-%m-%d %H:%M:%S')
            rain_probability = int(forecast['ElementValue'][0]['ProbabilityOfPrecipitation'])

            if start_time > current_time and rain_probability > threshold:
                time_difference = (start_time - current_time).total_seconds() / 3600
                rain_alert_message = f"{int(time_difference)}小時後高機率下雨"
                break
        else:
            rain_alert_message = "未來12小時無降雨風險"
        
    # 紫外線資訊
    station_id = get_uv_station_by_city(location)
    uv_alert_message = ""
    
    if station_id and user_settings[user_email]['uv_alert']:
        api_url_2 = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0005-001?Authorization={api_key}&StationID={station_id}"
        response_2 = requests.get(api_url_2)
        
        if response_2.status_code == 200:
            try:
                uv_level = response_2.json()['records']['weatherElement']['location'][0]['UVIndex']
                uv_alert_message = get_uv_warning(uv_level)
            except (KeyError, IndexError) as e:
                logging.error(f"解析紫外線數據時出錯: {e}")
                uv_alert_message = "無法獲取紫外線資訊"
        else:
            uv_alert_message = "無法獲取紫外線資訊"

    return (f"當前溫度: {current_temp}°C。 {rain_alert_message}"
            f"\n{location}最高/最低溫度:{max_temp}°C / {min_temp}°C。"
            f"\n{uv_alert_message}")

def get_uv_warning(uv_index):
    """
    根據紫外線指數回傳等級及建議訊息
    """
    if uv_index <= 2:
        level = "低量級"
        advice = "紫外線弱，建議適度戶外活動，但仍需注意防曬。"
    elif 3 <= uv_index <= 5:
        level = "中量級"
        advice = "紫外線中等，建議戴帽子、太陽眼鏡，並塗抹防曬乳。"
    elif 6 <= uv_index <= 7:
        level = "高量級"
        advice = "紫外線高，避免長時間曝曬，建議撐傘或尋找遮蔽處。"
    elif 8 <= uv_index <= 10:
        level = "過量級"
        advice = "紫外線非常強烈，建議減少戶外活動，並全方位做好防曬措施。"
    else:  # uv_index >= 11
        level = "危險級"
        advice = "紫外線極危險，避免任何直接曝曬，務必留在室內或做好防護。"

    return f"目前紫外線指數：{uv_index} {level}\n建議：{advice}"

def get_uv_station_by_city(user_city):
    uv_stations = [
        {"station_id": "466850", "city": "新北市"},
        {"station_id": "466910", "city": "臺北市"},
        {"station_id": "466940", "city": "基隆市"},
        {"station_id": "466990", "city": "花蓮縣"},
        {"station_id": "467050", "city": "桃園市"},
        {"station_id": "467080", "city": "宜蘭縣"},
        {"station_id": "467110", "city": "金門縣"},
        {"station_id": "467270", "city": "彰化縣"},
        {"station_id": "467280", "city": "苗栗縣"},
        {"station_id": "467290", "city": "雲林縣"},
        {"station_id": "467300", "city": "澎湖縣"},
        {"station_id": "467410", "city": "臺南市"},
        {"station_id": "467441", "city": "高雄市"},
        {"station_id": "467480", "city": "嘉義市"},
        {"station_id": "467490", "city": "臺中市"},
        {"station_id": "467530", "city": "嘉義縣"},
        {"station_id": "467540", "city": "臺東縣"},
        {"station_id": "467550", "city": "南投縣"},
        {"station_id": "467571", "city": "新竹縣"},
        {"station_id": "467590", "city": "屏東縣"},
        {"station_id": "467990", "city": "連江縣"},
        {"station_id": "C0D660", "city": "新竹市"},
        {"station_id": "G2AI50",  "city":"台北市"}
    ]
    matched_stations = [station["station_id"] for station in uv_stations if station["city"] == user_city]
    if matched_stations:
        return matched_stations[0]
    else:
        return None

if __name__ == "__main__":
    # 測試用戶設定
    test_user = "shuaiahua@gmail.com"
    user_settings[test_user] = {
        "location": "臺北市",
        "send_time": "08:00",
        "rain_alert": True,
        "uv_alert": True
    }
    
    # 測試發送天氣信息
    try:
        weather_info = get_weather(test_user, user_settings[test_user]['location'])
        send_email(
            test_user,
            "Daily Weather",
            weather_info
        )
        logging.info("Weather info sent successfully in test mode")
    except Exception as e:
        logging.error(f"Test failed: {e}")
